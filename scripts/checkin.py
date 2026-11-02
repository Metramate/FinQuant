"""Weekly check-in: dated snapshot, what changed since last time, and rule-based alerts.

    python scripts/checkin.py          # writes reports/history/<date>.json and reports/latest/checkin.md

Alerts use ``data/pm_rules.json``:
  * a holding above its max weight (e.g. HOOD > 5%)
  * a holding drifted from the plan in the CSV's ``weight_pct`` column (relative AND absolute thresholds)
  * a theme carrying too large a share of portfolio risk
  * big 5-day moves, oversold names (RSI), book volatility above a ceiling
Rules for tickers you do not hold yet are ignored until you add them to the CSV.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from load_my_portfolio import load_holdings  # noqa: E402
from my_prices import fetch_prices  # noqa: E402
from portfolio_manager import ANN, build_book, risk_contrib, stats  # noqa: E402
from signals import rsi  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", default="2024-01-01")
    ap.add_argument("--rf", type=float, default=0.04)
    ap.add_argument("--rules", default=str(ROOT / "data" / "pm_rules.json"))
    ap.add_argument("--history", default=str(ROOT / "reports" / "history"))
    ap.add_argument("--out", default=str(ROOT / "reports" / "latest"))
    a = ap.parse_args()
    rules = json.loads(pathlib.Path(a.rules).read_text())
    hist, out = pathlib.Path(a.history), pathlib.Path(a.out)
    hist.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)

    df = load_holdings()
    risky, cash, book, px = build_book(df, fetch_prices(df, a.start))
    rets = px.pct_change().dropna()
    cov = rets.cov().values * ANN
    w = risky["w_sleeve"].values
    rc = pd.Series(risk_contrib(w, cov), index=risky.index)
    st = stats(w, rets, a.rf)
    plan = df.set_index("ticker")["weight_pct"]

    snap = {
        "date": str(px.index[-1].date()), "book_usd": round(book, 2), "cash_usd": round(cash, 2),
        "vol": round(float(st["vol"]), 4), "sharpe": round(float(st["sharpe"]), 3), "max_dd": round(float(st["max_dd"]), 4),
        "weights_pct": {t: round(100 * float(v), 2) for t, v in risky["w_book"].items()},
        "risk_share_pct": {t: round(100 * float(v), 2) for t, v in rc.items()},
        "values_usd": {t: round(float(v), 2) for t, v in risky["value"].items()},
    }
    prev_files = sorted(p for p in hist.glob("*.json") if p.stem < snap["date"])
    prev = json.loads(prev_files[-1].read_text()) if prev_files else None
    (hist / f"{snap['date']}.json").write_text(json.dumps(snap, indent=1))

    alerts = []
    # 1. max weight
    mw = rules.get("max_weight_pct", {})
    for t, wt in snap["weights_pct"].items():
        cap = mw.get(t, mw.get("default"))
        if cap is not None and wt > cap:
            alerts.append(f"**{t} is {wt:.1f}% of the book, above its {cap:g}% limit**")
    # 2. drift vs plan
    dr = rules.get("drift_vs_plan", {})
    for t, wt in snap["weights_pct"].items():
        if t in plan.index and plan[t] > 0:
            d = wt - plan[t]
            if abs(d) >= dr.get("min_abs_pct_points", 1.0) and abs(d) / plan[t] >= dr.get("relative", 0.25):
                alerts.append(f"{t} drifted {d:+.1f}pt from the plan ({plan[t]:.1f}% → {wt:.1f}%)")
    # 3. theme risk shares
    for th, lim in rules.get("theme_max_risk_share_pct", {}).items():
        share = sum(v for t, v in snap["risk_share_pct"].items() if risky.loc[t, "theme"] == th)
        if share > lim:
            alerts.append(f"{th} carries {share:.0f}% of portfolio risk (limit {lim:g}%)")
    # 4. moves / oversold / vol
    mv = rules.get("move_alerts", {})
    chg5 = 100 * (px.iloc[-1] / px.iloc[-6] - 1)
    for t, v in chg5.items():
        if v <= mv.get("drop_5d_pct", -10):
            alerts.append(f"{t} fell {v:.0f}% in 5 days")
        if v >= mv.get("rise_5d_pct", 15):
            alerts.append(f"{t} rose {v:.0f}% in 5 days")
    over = [t for t in px if rsi(px[t]).iloc[-1] < rules.get("oversold_rsi", 30)]
    if over:
        alerts.append(f"Oversold (RSI<{rules.get('oversold_rsi', 30)}): {', '.join(over)}: where new cash would go if the thesis holds")
    if 100 * st["vol"] > rules.get("book_vol_max_pct", 1e9):
        alerts.append(f"Sleeve volatility {100*st['vol']:.0f}% above your {rules['book_vol_max_pct']}% ceiling")

    md = [f"# Check-in {snap['date']}", f"Book **${book:,.0f}** (cash ${cash:,.0f}) · vol {100*st['vol']:.1f}% · Sharpe {st['sharpe']:.2f} · max drawdown {100*st['max_dd']:.0f}%", "",
          "## Alerts", *(["- " + x for x in alerts] or ["- none"]), ""]
    if prev:
        dv = snap["book_usd"] - prev["book_usd"]
        md += [f"## Since {prev['date']}", f"- Book {dv:+,.0f} USD ({100*dv/prev['book_usd']:+.1f}%) (includes any cash you added/removed)",
               f"- Volatility {100*prev['vol']:.1f}% → {100*snap['vol']:.1f}%"]
        moves = {t: snap["weights_pct"][t] - prev["weights_pct"].get(t, 0) for t in snap["weights_pct"]}
        big = sorted(moves.items(), key=lambda kv: -abs(kv[1]))[:5]
        md += ["- Biggest weight changes: " + ", ".join(f"{t} {v:+.1f}pt" for t, v in big)]
        new = set(snap["weights_pct"]) - set(prev["weights_pct"])
        gone = set(prev["weights_pct"]) - set(snap["weights_pct"])
        if new: md += [f"- New positions: {', '.join(sorted(new))}"]
        if gone: md += [f"- Removed positions: {', '.join(sorted(gone))}"]
    else:
        md += ["## Since last time", "- First snapshot saved; the next run will show changes."]
    (out / "checkin.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
