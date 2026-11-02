"""Walk-forward backtest: does trimming reduce risk AND raise profit, net of costs?

    python scripts/backtest.py                  # defaults: monthly rebalance, 10bp / 25bp crypto costs

Strategies (all on today's 14 holdings, sleeve weights, monthly rebalance, trades hit costs):
  hold          buy & hold from the first test day with today's weights (no rebalancing, weights drift)
  constant_mix  monthly rebalance back to today's weights (the BASELINE the others are judged against)
  cap_20        constant mix, but any asset above 20% of the whole book is cut and the excess
                spread pro-rata over the rest (the "trim BTC" rule)
  crypto_cap_30 constant mix, but total crypto capped at 30% of the sleeve, excess spread pro-rata
  erc_blend     monthly: 50% today's weights + 50% risk-parity from the TRAILING 252 days only
                (no look-ahead)

Caveat that matters: the *choice of the 14 names* uses hindsight (you hold today's winners), the same
for every strategy, so differences BETWEEN strategies are the informative part, not the levels.

Gate used by portfolio_manager.py for trim advice: a rule passes only if, versus constant_mix, it has
lower volatility AND higher net CAGR on the full test window AND in both halves of it.
"""
from __future__ import annotations

import argparse
import json
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
from portfolio_manager import ANN, build_book, md_table, optimise, risk_contrib  # noqa: E402

LOOKBACK = 252


def cap_weights(w: np.ndarray, cap: float) -> np.ndarray:
    """Cut anything above ``cap`` and spread the excess pro-rata over the rest (iterated)."""
    w = w.copy()
    for _ in range(20):
        over = w > cap + 1e-12
        if not over.any():
            break
        excess = (w[over] - cap).sum()
        w[over] = cap
        room = ~over
        w[room] += excess * w[room] / w[room].sum()
    return w


def theme_cap(w: np.ndarray, mask: np.ndarray, cap: float) -> np.ndarray:
    w = w.copy()
    if w[mask].sum() > cap:
        scale = cap / w[mask].sum()
        excess = w[mask].sum() * (1 - scale)
        w[mask] *= scale
        w[~mask] += excess * w[~mask] / w[~mask].sum()
    return w


def simulate(rets: pd.DataFrame, target_fn, cost: np.ndarray, start: int, w0: np.ndarray) -> pd.Series:
    """Daily net returns. ``target_fn(i)`` -> target weights using data up to row i only (or None=hold)."""
    n = rets.shape[1]
    w = w0.copy()
    out, turnover = [], []
    idx = rets.index
    month_end = pd.Series(idx.to_period("M"), index=idx)
    is_me = (month_end != month_end.shift(-1)).values
    for i in range(start, len(rets)):
        r = rets.values[i]
        port = float(w @ r)
        w = w * (1 + r) / (1 + port)  # drift
        if is_me[i] and target_fn is not None and i < len(rets) - 1:
            tgt = target_fn(i)
            trade = np.abs(tgt - w)
            port -= float(cost @ trade)  # cost charged on the day of rebalance
            turnover.append(trade.sum() / 2)
            w = tgt
        out.append(port)
    s = pd.Series(out, index=idx[start:])
    s.attrs["turnover"] = float(np.mean(turnover)) * 12 if turnover else 0.0  # annualised one-way
    return s


def metrics(r: pd.Series, rf: float) -> dict:
    cum = (1 + r).cumprod()
    cagr = cum.iloc[-1] ** (ANN / len(r)) - 1
    vol = r.std(ddof=1) * np.sqrt(ANN)
    return {"cagr": cagr, "vol": vol, "sharpe": (cagr - rf) / vol, "max_dd": (cum / cum.cummax() - 1).min(),
            "turnover_pa": r.attrs.get("turnover", 0.0)}


def run(px: pd.DataFrame, risky: pd.DataFrame, rf: float, cost_bps: float, crypto_bps: float, max_w_book: float,
        risky_share: float, crypto_cap: float):
    rets = px.pct_change().dropna()
    names = list(rets.columns)
    w_now = risky.loc[names, "w_sleeve"].values
    is_crypto = np.array([risky.loc[t, "theme"] == "Crypto" for t in names])
    cost = np.where(is_crypto, crypto_bps, cost_bps) / 1e4
    cap_sleeve = max_w_book / risky_share
    lo, hi = 0.01 / risky_share, cap_sleeve

    def trailing_cov(i):
        return rets.iloc[max(0, i - LOOKBACK + 1): i + 1].cov().values * ANN

    def erc_blend(i):
        cov = trailing_cov(i)
        x0 = np.clip(w_now, lo, hi)
        erc = optimise(lambda w: ((risk_contrib(w, cov) - 1 / len(names)) ** 2).sum() * 1e4, len(names), lo, hi, x0 / x0.sum())
        return 0.5 * w_now + 0.5 * erc

    strategies = {
        "hold": None,
        "constant_mix": lambda i: w_now,
        "cap_20": lambda i: cap_weights(w_now, cap_sleeve),
        "crypto_cap_30": lambda i: theme_cap(w_now, is_crypto, crypto_cap),
        "erc_blend": erc_blend,
    }
    start = LOOKBACK
    res = {}
    for k, fn in strategies.items():
        w0 = w_now if k in ("hold", "constant_mix") else (fn(start) if k != "erc_blend" else w_now)
        res[k] = simulate(rets, fn, cost, start, w0)
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", default="2024-01-01")
    ap.add_argument("--rf", type=float, default=0.04)
    ap.add_argument("--cost-bps", type=float, default=10.0, help="one-way trading cost, stocks/ETFs (my assumption)")
    ap.add_argument("--crypto-bps", type=float, default=25.0, help="one-way trading cost, crypto (my assumption)")
    ap.add_argument("--max-weight", type=float, default=0.20)
    ap.add_argument("--crypto-cap", type=float, default=0.30)
    ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parent.parent / "reports" / "latest"))
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    df = load_holdings()
    risky, cash, book, px = build_book(df, fetch_prices(df, a.start))
    res = run(px, risky, a.rf, a.cost_bps, a.crypto_bps, a.max_weight, 1 - cash / book, a.crypto_cap)

    full = pd.DataFrame({k: metrics(v, a.rf) for k, v in res.items()}).T
    half = len(next(iter(res.values()))) // 2
    halves = {}
    for lab, sl in (("H1", slice(0, half)), ("H2", slice(half, None))):
        halves[lab] = pd.DataFrame({k: metrics(v.iloc[sl], a.rf) for k, v in res.items()}).T

    base = "constant_mix"
    verdict = {}
    for k in res:
        if k in ("hold", base):
            continue
        ok = all((tab.loc[k, "vol"] < tab.loc[base, "vol"]) and (tab.loc[k, "cagr"] > tab.loc[base, "cagr"])
                 for tab in (full, halves["H1"], halves["H2"]))
        verdict[k] = {"passes_gate": bool(ok),
                      "d_vol": float(full.loc[k, "vol"] - full.loc[base, "vol"]),
                      "d_cagr": float(full.loc[k, "cagr"] - full.loc[base, "cagr"]),
                      "d_vol_H1": float(halves["H1"].loc[k, "vol"] - halves["H1"].loc[base, "vol"]),
                      "d_cagr_H1": float(halves["H1"].loc[k, "cagr"] - halves["H1"].loc[base, "cagr"]),
                      "d_vol_H2": float(halves["H2"].loc[k, "vol"] - halves["H2"].loc[base, "vol"]),
                      "d_cagr_H2": float(halves["H2"].loc[k, "cagr"] - halves["H2"].loc[base, "cagr"])}
    (out / "backtest.json").write_text(json.dumps({"window": [str(next(iter(res.values())).index[0].date()),
                                                             str(next(iter(res.values())).index[-1].date())],
                                                   "verdict": verdict}, indent=1))

    def fmt(t):
        t = t.copy()
        for c in ("cagr", "vol", "max_dd", "turnover_pa"):
            t[c] *= 100
        t.index.name = "Strategy"
        return md_table(t, {"cagr": "{:.1f}%", "vol": "{:.1f}%", "sharpe": "{:.2f}", "max_dd": "{:.1f}%", "turnover_pa": "{:.0f}%"})

    first, last = next(iter(res.values())).index[[0, -1]]
    md = [f"# Rebalance backtest ({first.date()} → {last.date()}, {len(next(iter(res.values())))} days)",
          f"Costs: {a.cost_bps:g}bp stocks/ETFs, {a.crypto_bps:g}bp crypto per side (assumptions). Net of costs.", "",
          "## Full window", fmt(full), "", "## First half", fmt(halves["H1"]), "", "## Second half", fmt(halves["H2"]), "",
          "## Gate: lower vol AND higher net CAGR than constant_mix, in full window and both halves",
          *[f"- **{k}**: {'PASS' if v['passes_gate'] else 'FAIL'} "
            f"(full: vol {100*v['d_vol']:+.1f}pt, CAGR {100*v['d_cagr']:+.1f}pt; "
            f"H1: {100*v['d_vol_H1']:+.1f}/{100*v['d_cagr_H1']:+.1f}; H2: {100*v['d_vol_H2']:+.1f}/{100*v['d_cagr_H2']:+.1f})"
            for k, v in verdict.items()], "",
          "Hindsight warning: the 14 names are today's holdings, same for every strategy; compare strategies, not levels."]
    (out / "backtest.md").write_text("\n".join(md) + "\n")

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    cols = {"hold": "#999", "constant_mix": "black", "cap_20": "#d1495b", "crypto_cap_30": "#f2a900", "erc_blend": "#2a9d8f"}
    for k, v in res.items():
        cum = 100 * (1 + v).cumprod()
        a1.plot(cum, label=k, color=cols[k], lw=2 if k == base else 1.2)
        if k in (base, "erc_blend"):
            a2.plot(cum / cum.cummax() - 1, color=cols[k], lw=1)
    a1.set_title("Walk-forward backtest, net of costs (growth of 100)")
    a1.legend(frameon=False, ncol=3)
    a2.set_ylabel("Drawdown")
    fig.tight_layout()
    fig.savefig(out / "08_backtest.png", dpi=130)
    plt.close(fig)
    print("\n".join(md))


if __name__ == "__main__":
    main()
