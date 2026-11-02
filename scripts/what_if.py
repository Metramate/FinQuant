"""What happens if I add X% of the book in a new ticker?

    python scripts/what_if.py --ticker HOOD --pcts 2 5 10
    python scripts/what_if.py --ticker HOOD --pcts 5 --fund cash

Funding modes (percent = share of the WHOLE book):
  prorata (default): sell all existing risky holdings proportionally, cash unchanged
  cash             : pay from the cash line (limited to the cash you hold)

Everything is in-sample, current weights held constant, history since --start (same caveats as
portfolio_manager.py). Cash is assumed to earn ``--rf``. Writes reports/latest/what_if_<TICKER>.{md,png}.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from load_my_portfolio import load_holdings  # noqa: E402
from my_prices import fetch_prices  # noqa: E402
from portfolio_manager import ANN, build_book, md_table  # noqa: E402


def scenario_stats(w: pd.Series, cash_w: float, rets: pd.DataFrame, rf: float, bench: pd.Series) -> dict:
    pr = rets.values @ w.values + cash_w * rf / ANN
    cum = np.cumprod(1 + pr)
    dd = cum / np.maximum.accumulate(cum) - 1
    ann = cum[-1] ** (ANN / len(pr)) - 1
    vol = pr.std(ddof=1) * np.sqrt(ANN)
    cov = rets.cov().values * ANN
    rc = w.values * (cov @ w.values) / (w.values @ cov @ w.values)
    worst20 = pd.Series(pr).rolling(20).apply(lambda x: np.prod(1 + x) - 1).min()
    return {
        "ann_return": ann, "vol": vol, "sharpe": (ann - rf) / vol, "max_dd": dd.min(),
        "worst_20d": worst20, "beta_QQQM": np.cov(pr, bench)[0, 1] / bench.var(),
        "rc": pd.Series(rc, index=w.index),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ticker", default="HOOD")
    ap.add_argument("--pcts", type=float, nargs="+", default=[2, 5, 10])
    ap.add_argument("--fund", choices=["prorata", "cash"], default="prorata")
    ap.add_argument("--start", default="2024-01-01")
    ap.add_argument("--rf", type=float, default=0.04)
    ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parent.parent / "reports" / "latest"))
    a = ap.parse_args()
    tkr = a.ticker.upper()

    df = load_holdings()
    new = {"ticker": tkr, "yahoo_ticker": tkr, "asset_class": "stock", "quantity": 0.0, "avg_price_usd": 1.0,
           "cost_usd": 0.0, "weight_pct": 0.0, "theme": "NEW"}
    df2 = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
    risky, cash, book, px = build_book(df2, fetch_prices(df2, a.start))
    rets = px.pct_change().dropna()
    cash_w = cash / book
    base = risky["w_book"].copy()
    others = [t for t in base.index if t != tkr]
    bench = pd.Series(rets["QQQM"].values)

    rows, rcs, labels = {}, {}, {}
    for pct in [0.0] + list(a.pcts):
        x = pct / 100
        w = base.copy()
        cw = cash_w
        if a.fund == "prorata":
            w[others] = base[others] * (1 - cash_w - x) / (1 - cash_w)
        else:
            if x > cash_w:
                print(f"[skip] {pct}% exceeds cash ({100*cash_w:.1f}%) in --fund cash")
                continue
            cw = cash_w - x
        w[tkr] = x
        s = scenario_stats(w, cw, rets, a.rf, bench)
        lab = "now" if pct == 0 else f"+{pct:g}%"
        rcs[lab] = s.pop("rc")
        rows[lab] = s
        labels[lab] = (w, cw)

    t = pd.DataFrame(rows).T
    t["hood_risk_share"] = [100 * rcs[k][tkr] for k in t.index]
    t["crypto_risk_share"] = [100 * rcs[k][[i for i in others if risky.loc[i, "theme"] == "Crypto"]].sum() for k in t.index]
    t["ai_semis_risk_share"] = [100 * rcs[k][[i for i in others if risky.loc[i, "theme"] in ("Semis / AI", "Broad tech")]].sum() for k in t.index]
    for c in ("ann_return", "vol", "max_dd", "worst_20d"):
        t[c] *= 100
    t.index.name = "Scenario"

    h = rets[tkr]
    corr = rets.corr()[tkr].drop(tkr).sort_values(ascending=False)
    sleeve = pd.Series(rets[others].values @ (base[others] / base[others].sum()).values, index=rets.index)
    own_vol, own_dd = h.std() * np.sqrt(ANN), (px[tkr].iloc[-1] / px[tkr].iloc[-ANN:].max() - 1)
    shock = {f"+{p:g}%": 100 * (p / 100) * -0.40 for p in a.pcts}

    # chart
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1, 3, figsize=(14, 4.6))
    xs = list(t.index)
    ax[0].plot(xs, t["vol"], "o-", color="#4c78a8")
    ax[0].set_title("Volatility % (annualised)")
    ax[1].plot(xs, t["max_dd"], "o-", color="#d1495b")
    ax[1].set_title("Worst drawdown % (in-sample)")
    ax[2].bar(xs, t["hood_risk_share"], color="#f2a900")
    ax[2].set_title(f"{tkr}: share of portfolio risk %")
    for a_ in ax:
        a_.set_xlabel(f"{tkr} as % of whole book")
    fig.suptitle(f"What if you add {tkr}? (funding: {a.fund}; Sharpe " + ", ".join(f"{k} {v:.2f}" for k, v in t["sharpe"].items()) + ")", fontsize=10)
    fig.tight_layout()
    fig.savefig(out / f"07_what_if_{tkr}.png", dpi=130)
    plt.close(fig)

    md = [
        f"# What if: add {tkr} ({a.fund}-funded)",
        f"{tkr}: {100*own_vol:.0f}% annualised vol, {100*own_dd:.0f}% from 1-year high, "
        f"correlation to your AI/semis names avg {corr[[i for i in others if risky.loc[i,'theme'] in ('Semis / AI','Broad tech')]].mean():.2f}, "
        f"to crypto avg {corr[[i for i in others if risky.loc[i,'theme']=='Crypto']].mean():.2f}, "
        f"to your existing risky sleeve {np.corrcoef(h.values, sleeve.values)[0,1]:.2f}.",
        "",
        md_table(t[["ann_return", "vol", "sharpe", "max_dd", "worst_20d", "beta_QQQM", "hood_risk_share", "crypto_risk_share", "ai_semis_risk_share"]],
                 {"ann_return": "{:.1f}%", "vol": "{:.1f}%", "sharpe": "{:.2f}", "max_dd": "{:.1f}%", "worst_20d": "{:.1f}%",
                  "beta_QQQM": "{:.2f}", "hood_risk_share": "{:.1f}%", "crypto_risk_share": "{:.1f}%", "ai_semis_risk_share": "{:.1f}%"}),
        "",
        "Mechanical hit if the new position falls 40% (book impact): " + ", ".join(f"{k}: {v:.1f}%" for k, v in shock.items()),
        "",
        "In-sample, current weights constant; history includes a strong bull run; not advice.",
    ]
    (out / f"what_if_{tkr}.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"\nCorrelation of {tkr} with each holding:\n{corr.round(2).to_string()}")


if __name__ == "__main__":
    main()
