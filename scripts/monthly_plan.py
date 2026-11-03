"""Monthly buy plan: put new money where the book is most UNDER its target weight. Never sells.

    python scripts/monthly_plan.py --monthly-eur 1000                # this month's buy list
    python scripts/monthly_plan.py --monthly-eur 1500 --apply        # same, and write the buys into data/my-portfolio.csv (backup kept)
    python scripts/monthly_plan.py --monthly-eur 1000 --simulate 36  # how the book changes over 36 months vs 'everything into the 14'
    python scripts/monthly_plan.py --report                          # risk of each stage's target mix vs your book today

Targets live in data/targets.json by book size (stage A < EUR 20k, B 20-30k, C > 30k). The greedy rule: each month spread the money over
the (at most --max-buys) positions with the biggest gap to target, in proportion to the gap, skipping buys under --min-buy-eur. Positions
above target just get diluted as the book grows. --apply assumes you filled at the latest close: adjust the CSV by hand if prices differ.

Assumptions (mine): thresholds are in EUR (converted with the live EURUSD), cash target 5% and the cash line is never touched, simulation
uses constant prices (shows the effect of new money only, not of returns). Not advice.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yfinance as yf  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from load_my_portfolio import HOLDINGS, load_holdings  # noqa: E402
from my_prices import fetch_prices  # noqa: E402
from portfolio_manager import ANN, md_table, risk_contrib, stats  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGETS = ROOT / "data" / "targets_optimised.json"  # from scripts/construct.py; the hand-set file is data/targets.json (use --targets)
SLEEVE_COLORS = ["#f2a900", "#7b4fd3", "#4c78a8", "#2a9d8f", "#264653", "#c7d2de"]


def eurusd() -> float:
    h = yf.Ticker("EURUSD=X").history(period="10d")["Close"].dropna()
    return float(h.iloc[-1])


def stage_for(book_eur: float, stages: list[dict]) -> dict:
    return [s for s in stages if book_eur >= s["from_eur"]][-1]


def allocate(values: dict, weights: dict, money: float, max_buys: int, min_buy: float) -> dict:
    """Spread `money` over the positions furthest below target (targets rescaled to the invested money, cash excluded), in proportion to their gaps.
    `max_buys` is a hard cap, so a position can land a bit above target; later months dilute it."""
    wn = {t: w for t, w in weights.items() if t != "CASH"}  # dry powder is separate: weights are shares of the INVESTED money
    wsum = sum(wn.values())
    total_after = sum(values.values()) + money
    gap = {t: max(w / wsum * total_after - values.get(t, 0.0), 0.0) for t, w in wn.items()}
    order = [t for t, g in sorted(gap.items(), key=lambda kv: -kv[1]) if g > 0]
    while order:
        chosen = order[:max_buys]  # hard cap on purchases per month; small overshoots self-correct in later months
        S = sum(gap[t] for t in chosen)
        alloc = {t: money * gap[t] / S for t in chosen}  # proportional to the gap; may slightly overshoot a target after small buys are dropped
        small = [t for t, a_ in alloc.items() if a_ < min_buy]
        if not small:
            break
        order = [t for t in order if t not in small]
    else:
        return {}
    return {t: a_ for t, a_ in alloc.items() if a_ > 0}


def extended_holdings(df: pd.DataFrame, targets: dict) -> pd.DataFrame:
    rows = []
    for t, m in targets["new_positions"].items():
        if t not in set(df["ticker"]):
            rows.append({"ticker": t, "yahoo_ticker": m["yahoo"], "asset_class": m["asset_class"], "quantity": 0.0, "avg_price_usd": 1.0, "cost_usd": 0.0,
                         "weight_pct": 0.0, "theme": m["theme"], "history_proxy": np.nan})
    return pd.concat([df, pd.DataFrame(rows)], ignore_index=True) if rows else df


def current_state(df_ext: pd.DataFrame, start="2024-01-01"):
    px = fetch_prices(df_ext, start)
    last = px.ffill().iloc[-1]
    held = df_ext[df_ext["asset_class"] != "cash"]
    values = {r.ticker: float(r.quantity * last[r.yahoo_ticker]) for r in held.itertuples()}
    price = {r.ticker: float(last[r.yahoo_ticker]) for r in held.itertuples()}
    cash = float(df_ext.loc[df_ext["asset_class"] == "cash", "quantity"].sum())
    return values, price, cash, px


def sleeve_shares(values: dict, cash: float, groups: dict) -> dict:
    tot = sum(values.values()) + cash
    out = {}
    for g, ts in groups.items():
        out[g] = (cash if ts == ["CASH"] else sum(values.get(t, 0.0) for t in ts)) / tot
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--monthly-eur", type=float, default=1000.0)
    ap.add_argument("--max-buys", type=int, default=5)
    ap.add_argument("--min-buy-eur", type=float, default=60.0)
    ap.add_argument("--targets", default=str(TARGETS), help="targets JSON (default: optimised by construct.py)")
    ap.add_argument("--holdings", default=str(HOLDINGS), help="holdings CSV to read (and to write with --apply)")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--simulate", type=int, default=0, help="months to simulate")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "reports" / "latest"))
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    targets = json.loads(pathlib.Path(a.targets).read_text())
    df = load_holdings(pathlib.Path(a.holdings))
    df_ext = extended_holdings(df, targets)
    fx = eurusd()
    values, price, cash, px = current_state(df_ext)
    book_usd = sum(values.values()) + cash
    book_eur = book_usd / fx
    stage = stage_for(book_eur, targets["stages"])
    W = stage["weights"]
    md = [f"# Monthly plan (EURUSD {fx:.3f})", f"Book ${book_usd:,.0f} = EUR {book_eur:,.0f} -> stage **{stage['name']}**. Money this month: EUR {a.monthly_eur:,.0f} = ${a.monthly_eur*fx:,.0f}.", ""]

    # ------------------------------------------------ this month's buys
    money = a.monthly_eur * fx
    buys = allocate(values, W, money, a.max_buys, a.min_buy_eur * fx)
    total_after = book_usd + money
    rows = []
    for t, usd in sorted(buys.items(), key=lambda kv: -kv[1]):
        now = values.get(t, 0.0)
        rows.append({"Ticker": t, "buy EUR": usd / fx, "buy USD": usd, "shares": usd / price[t], "weight now %": 100 * now / book_usd,
                     "weight after %": 100 * (now + usd) / total_after, "target %": W[t], "new?": "NEW" if now == 0 else ""})
    bt = pd.DataFrame(rows).set_index("Ticker") if rows else pd.DataFrame()
    md += ["## This month's buys (most under-target first)",
           md_table(bt, {"buy EUR": "{:,.0f}", "buy USD": "{:,.0f}", "shares": "{:.4f}", "weight now %": "{:.1f}", "weight after %": "{:.1f}", "target %": "{:.1f}"}) if len(bt) else "Nothing to buy: every position is at or above target.", ""]
    over = {t: 100 * values[t] / book_usd - W.get(t, 0) for t in values if 100 * values[t] / book_usd - W.get(t, 0) > 1.0}
    if over:
        md += ["Above target (no selling needed, they get diluted): " + ", ".join(f"{t} +{v:.1f}pt" for t, v in sorted(over.items(), key=lambda kv: -kv[1])), ""]
    md += ["Positions still at zero in this stage (planned later): " + (", ".join(sorted(set(targets["new_positions"]) - set(W))) or "none"), ""]

    if a.apply and buys:
        shutil.copy(a.holdings, a.holdings + ".bak")
        d = df_ext.copy()
        for t, usd in buys.items():
            i = d.index[d["ticker"] == t][0]
            d.loc[i, "quantity"] += usd / price[t]
            d.loc[i, "cost_usd"] += usd
            d.loc[i, "avg_price_usd"] = d.loc[i, "cost_usd"] / d.loc[i, "quantity"]
        d["weight_pct"] = d.apply(lambda r: W.get(r["ticker"], r["weight_pct"]), axis=1)
        d = d[(d["asset_class"] == "cash") | (d["quantity"] > 0)]
        d.to_csv(a.holdings, index=False)
        md += [f"APPLIED to {pathlib.Path(a.holdings).name} (backup: {pathlib.Path(a.holdings).name}.bak). Assumes fills at the latest close.", ""]

    # ------------------------------------------------ simulation: rule vs everything into the 14
    if a.simulate:
        groups = targets["groups"]
        v_rule, v_base, c = dict(values), dict(values), cash
        v_rule = {t: v for t, v in v_rule.items()}
        hist = []
        stage_months = {}
        calendar = []
        for m in range(a.simulate + 1):
            s_rule = sleeve_shares(v_rule, c, groups)
            s_base = sleeve_shares(v_base, c, groups)
            hist.append((m, s_rule, s_base, sum(1 for v in v_rule.values() if v > 0.5 * 1), sum(1 for v in v_base.values() if v > 0)))
            if m == a.simulate:
                break
            tot_eur = (sum(v_rule.values()) + c) / fx
            st = stage_for(tot_eur, targets["stages"])
            stage_months.setdefault(st["name"], m)
            al = allocate(v_rule, st["weights"], money, a.max_buys, a.min_buy_eur * fx)
            calendar.append((m + 1, st["name"].split()[0], al))
            for t, usd in al.items():
                v_rule[t] = v_rule.get(t, 0.0) + usd
            core = {t: v for t, v in v_base.items() if v > 0}
            ssum = sum(core.values())
            for t, v in core.items():
                v_base[t] = v + money * v / ssum
        sim = pd.DataFrame([{"month": m, **{k: 100 * v for k, v in sr.items()}, "# positions": n} for m, sr, sb, n, nb in hist]).set_index("month")
        base = pd.DataFrame([{"month": m, **{k: 100 * v for k, v in sb.items()}, "# positions": nb} for m, sr, sb, n, nb in hist]).set_index("month")
        pick = [m for m in (0, 6, 12, 18, 24, 36, a.simulate) if m <= a.simulate]
        keep = ["Crypto", "AI / semis / tech", list(groups)[2], "Steady compounders", "World fund", "Cash"]
        keep = [k for k in keep if k in sim.columns]
        show = sim.loc[sorted(set(pick)), keep + ["# positions"]].copy()
        show.index = [f"month {m}" for m in show.index]
        show.index.name = "With the plan"
        b2 = base.loc[sorted(set(pick)), ["Crypto", "AI / semis / tech", "Cash"]].copy()
        b2.index = [f"month {m}" for m in b2.index]
        b2.index.name = "All new money into the 14 (pro rata)"
        cal_rows = {f"month {m}": {"stage": stg, "buys (EUR)": ", ".join(f"{t} {u/fx:,.0f}" for t, u in sorted(al.items(), key=lambda kv: -kv[1]))} for m, stg, al in calendar[:12]}
        cal = pd.DataFrame(cal_rows).T
        cal.index.name = "Buy calendar (first 12 months)"
        base_final = {t: 100 * v / (sum(v_base.values()) + c) for t, v in v_base.items() if v > 0}
        md += [md_table(cal), ""]
        md += [f"## {a.simulate}-month path at EUR {a.monthly_eur:,.0f}/mo (constant prices: shows only what new money does)",
               "Stage changes: " + ", ".join(f"stage {k.split()[0]} from month {v}" for k, v in stage_months.items()), "",
               md_table(show, {c_: "{:.1f}" for c_ in keep} | {"# positions": "{:.0f}"}), "",
               md_table(b2, {c_: "{:.1f}" for c_ in b2.columns}), ""]
        fig, ax = plt.subplots(1, 2, figsize=(15, 5), sharey=True)
        names = list(groups)
        for axis, data, ttl in ((ax[0], sim, "With the plan"), (ax[1], base, "Everything into the 14 you hold (pro rata)")):
            axis.stackplot(data.index, *[data[g] for g in names if g in data.columns], colors=SLEEVE_COLORS[:len(names)], labels=[n[:42] for n in names if n in data.columns])
            axis.set_title(ttl, fontsize=11); axis.set_xlabel("months from now"); axis.set_ylim(0, 100)
        ax[0].set_ylabel("% of the book"); ax[0].legend(frameon=False, fontsize=7, loc="lower left")
        fig.suptitle(f"How the mix changes with EUR {a.monthly_eur:,.0f} a month (prices held constant)", fontsize=12)
        fig.tight_layout(); fig.savefig(out / "13_plan_paths.png", dpi=130); plt.close(fig)

    # ------------------------------------------------ risk of each stage's target mix
    if a.report:
        hold_tickers = {r.ticker: r.yahoo_ticker for r in df_ext.itertuples() if r.asset_class != "cash"}
        R = px.rename(columns={v: k for k, v in hold_tickers.items()}).pct_change().dropna(how="all")
        mixes = {"Your book today": {t: 100 * v / book_usd for t, v in values.items() if v > 0}}
        if a.simulate:
            mixes[f"All new money into the 14 (month {a.simulate} mix)"] = {t: w for t, w in base_final.items() if t in R.columns}
        for s in targets["stages"]:
            mixes[f"Stage {s['name'].split()[0]} target"] = {t: w for t, w in s["weights"].items() if t != "CASH"}
        cols = sorted({t for m in mixes.values() for t in m})
        Rw = R[cols].dropna()
        rep = {}
        crypto = set(targets["groups"]["Crypto"]); ai = set(targets["groups"]["AI / semis / tech"])
        for name, m in mixes.items():
            w = np.array([m.get(t, 0.0) for t in cols]); w = w / w.sum()
            st = stats(w, Rw, 0.04)
            rc = pd.Series(risk_contrib(w, Rw.cov().values * ANN), index=cols)
            rep[name] = {"vol %": 100 * st["vol"], "worst drawdown %": 100 * st["max_dd"], "worst 20d loss %": 0.0,
                         "crypto share of risk %": 100 * rc[[c_ for c_ in cols if c_ in crypto]].sum(), "AI/semis share of risk %": 100 * rc[[c_ for c_ in cols if c_ in ai]].sum(),
                         "# positions": int((w > 0).sum())}
            pr = pd.Series(Rw.values @ w, index=Rw.index)
            rep[name]["worst 20d loss %"] = 100 * float(((1 + pr).rolling(20).apply(np.prod, raw=True) - 1).min())
        rp = pd.DataFrame(rep).T
        rp.index.name = "Mix"
        md += [f"## Risk of each target mix over {Rw.index[0].date()} to {Rw.index[-1].date()} (risky part only, history of these names, hindsight)",
               md_table(rp, {c_: "{:.1f}" for c_ in rp.columns if c_ != "# positions"} | {"# positions": "{:.0f}"}), ""]

    (out / "plan.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
