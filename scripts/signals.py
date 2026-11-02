"""Trend / stretch signals for every holding, using FinQuant's own moving-average functions.

    python scripts/signals.py

Outputs reports/latest/signals.md and 10_signals.png (price + 20d Bollinger band + 50d/200d SMA per holding).

These are DESCRIPTIVE tools: where is each position relative to its own trend and recent range? The script also
backtests one blunt rule ("hold an asset only while it closes above its 200-day SMA, else cash") on today's
holdings, so you can see whether following trend would have helped or hurt your aggressive mix, net of costs.
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
from finquant.moving_average import sma, sma_std  # noqa: E402
from load_my_portfolio import load_holdings  # noqa: E402
from my_prices import fetch_prices  # noqa: E402
from portfolio_manager import ANN, build_book, md_table  # noqa: E402


def rsi(p: pd.Series, n: int = 14) -> pd.Series:
    d = p.diff()
    up, dn = d.clip(lower=0).rolling(n).mean(), (-d.clip(upper=0)).rolling(n).mean()
    return 100 - 100 / (1 + up / dn)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", default="2024-01-01")
    ap.add_argument("--rf", type=float, default=0.04)
    ap.add_argument("--cost-bps", type=float, default=10.0)
    ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parent.parent / "reports" / "latest"))
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    df = load_holdings()
    risky, cash, book, px = build_book(df, fetch_prices(df, a.start))
    ma20, sd20, ma50, ma200 = sma(px, 20), sma_std(px, 20), sma(px, 50), sma(px, 200)  # FinQuant functions
    upper, lower = ma20 + 2 * sd20, ma20 - 2 * sd20

    last = px.iloc[-1]
    tbl = pd.DataFrame({
        "w_book": 100 * risky["w_book"],
        "vs_SMA50": 100 * (last / ma50.iloc[-1] - 1),
        "vs_SMA200": 100 * (last / ma200.iloc[-1] - 1),
        "pctB": (last - lower.iloc[-1]) / (upper.iloc[-1] - lower.iloc[-1]),
        "RSI14": pd.Series({t: rsi(px[t]).iloc[-1] for t in px}),
    })

    def trend(r):
        return "above both" if r.vs_SMA50 > 0 and r.vs_SMA200 > 0 else "below both" if r.vs_SMA50 < 0 and r.vs_SMA200 < 0 else "mixed"

    def flag(r):
        f = []
        if r.pctB > 1: f.append("above upper band")
        if r.pctB < 0: f.append("below lower band")
        if r.RSI14 > 70: f.append("overbought")
        if r.RSI14 < 30: f.append("oversold")
        return ", ".join(f) or "-"

    tbl["trend"] = tbl.apply(trend, axis=1)
    tbl["stretch"] = tbl.apply(flag, axis=1)
    tbl = tbl.sort_values("w_book", ascending=False)
    tbl.index.name = "Ticker"

    # trend-filter test on today's holdings (sleeve weights, daily, signal lagged 1 day)
    rets = px.pct_change()
    on = (px > ma200).shift(1).fillna(False)
    w = risky["w_sleeve"]
    valid = ma200.dropna().index
    base = (rets.loc[valid] * w).sum(axis=1)
    filt_gross = (rets.loc[valid] * on.loc[valid] * w).sum(axis=1)
    switches = on.loc[valid].astype(int).diff().abs().fillna(0)
    cost = (switches * w * a.cost_bps / 1e4).sum(axis=1)
    cash_ret = a.rf / ANN
    filt = filt_gross + ((~on.loc[valid]) * w).sum(axis=1) * cash_ret - cost

    def m(r):
        cum = (1 + r).cumprod()
        cagr = cum.iloc[-1] ** (ANN / len(r)) - 1
        vol = r.std() * np.sqrt(ANN)
        return {"cagr": 100 * cagr, "vol": 100 * vol, "sharpe": (cagr - a.rf) / vol, "max_dd": 100 * (cum / cum.cummax() - 1).min()}

    cmp = pd.DataFrame({"Hold (daily-rebalanced mix)": m(base), "Trend filter (200d SMA, net of costs)": m(filt)}).T
    cmp.index.name = "Strategy"
    exposure = on.loc[valid].mul(w).sum(axis=1).mean()

    md = [f"# Signals ({px.index[-1].date()})", "", md_table(tbl, {"w_book": "{:.1f}%", "vs_SMA50": "{:+.1f}%", "vs_SMA200": "{:+.1f}%", "pctB": "{:.2f}", "RSI14": "{:.0f}"}),
          "", f"%B: 0 = on the lower 20d Bollinger band, 1 = on the upper band. SKHY's 200d SMA is mostly proxy history.", "",
          f"## Does a 200-day trend filter help *this* portfolio? ({valid[0].date()} → {valid[-1].date()}, average invested {100*exposure:.0f}%)",
          md_table(cmp, {"cagr": "{:.1f}%", "vol": "{:.1f}%", "sharpe": "{:.2f}", "max_dd": "{:.1f}%"}), "",
          "One backtest on a window and a basket chosen with hindsight: treat it as a question, not an answer."]
    (out / "signals.md").write_text("\n".join(md) + "\n")

    names = list(tbl.index)
    cols = 4
    rows = int(np.ceil(len(names) / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(16, 3 * rows), sharex=True)
    sl = slice(-250, None)
    for ax, t in zip(axes.flat, names):
        ax.plot(px[t].iloc[sl], color="black", lw=1.2)
        ax.fill_between(px.index[sl], lower[t].iloc[sl], upper[t].iloc[sl], color="#4c78a8", alpha=0.18)
        ax.plot(ma50[t].iloc[sl], color="#f2a900", lw=0.9)
        ax.plot(ma200[t].iloc[sl], color="#d1495b", lw=0.9)
        ax.set_title(f"{t}  ({tbl.loc[t, 'trend']})", fontsize=9)
        ax.tick_params(labelsize=7)
    for ax in list(axes.flat)[len(names):]:
        ax.axis("off")
    fig.suptitle("Last 250 days: price, 20d Bollinger band (blue), 50d SMA (gold), 200d SMA (red)", fontsize=11)
    fig.tight_layout()
    fig.savefig(out / "10_signals.png", dpi=110)
    plt.close(fig)
    print("\n".join(md))


if __name__ == "__main__":
    main()
