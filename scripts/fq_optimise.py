"""FinQuant's own optimiser on your holdings: efficient frontier, max-Sharpe, same-risk / same-return mixes, Monte Carlo.

    python scripts/fq_optimise.py

Answers your rule directly ("only if it reduces risk AND increases profitability"):
  * same return, lowest risk   -> FinQuant ef_efficient_return(target = your current return)
  * same risk, highest return  -> FinQuant ef_efficient_volatility(target = your current volatility)
  * a CONSTRAINED version      -> my SLSQP, max 20% per asset, 50%-shrunk expected returns (less hindsight)
The unconstrained FinQuant answers are corner solutions built on in-sample returns (very hindsight-heavy);
read them as a ceiling on what rebalancing could add, not a plan. Cross-check: FinQuant's min-vol result equals
my independent scipy optimiser (17.31% vol / 24.08% return on the 2024-01-01 window).
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
from scipy.optimize import minimize  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from finquant.portfolio import build_portfolio  # noqa: E402
from load_my_portfolio import load_holdings  # noqa: E402
from my_prices import fetch_prices  # noqa: E402
from portfolio_manager import ANN, build_book, md_table  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", default="2024-01-01")
    ap.add_argument("--rf", type=float, default=0.04)
    ap.add_argument("--max-weight", type=float, default=0.20, help="per-asset cap, share of whole book")
    ap.add_argument("--mc", type=int, default=3000, help="Monte Carlo portfolios")
    ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parent.parent / "reports" / "latest"))
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    df = load_holdings()
    risky, cash, book, px = build_book(df, fetch_prices(df, a.start))
    names = list(px.columns)
    alloc = pd.DataFrame({"Name": names, "Allocation": 100 * risky["w_sleeve"].values})
    pf = build_portfolio(data=px, pf_allocation=alloc)
    pf.risk_free_rate = a.rf

    rets = px.pct_change().dropna()
    mu, cov = rets.mean().values * ANN, rets.cov().values * ANN
    w0 = risky["w_sleeve"].values

    def st(w):
        r = float(w @ mu)
        v = float(np.sqrt(w @ cov @ w))
        return {"return": r, "vol": v, "sharpe": (r - a.rf) / v}

    def fq(w_df):
        return w_df["Allocation"].reindex(names).values.astype(float)

    cur = st(w0)
    ports = {"Current": w0}
    ports["FinQuant min-vol"] = fq(pf.ef_minimum_volatility())
    ports["FinQuant max-Sharpe"] = fq(pf.ef_maximum_sharpe_ratio())
    ports["FinQuant same return, min risk"] = fq(pf.ef_efficient_return(cur["return"]))
    ports["FinQuant same risk, max return"] = fq(pf.ef_efficient_volatility(cur["vol"]))

    # constrained (caps, shrunk means): maximise shrunk return subject to vol <= current vol
    risky_share = 1 - cash / book
    hi = a.max_weight / risky_share
    shrunk = 0.5 * mu + 0.5 * mu.mean()
    res = minimize(lambda w: -(w @ shrunk), np.clip(w0, 0, hi) / np.clip(w0, 0, hi).sum(), method="SLSQP",
                   bounds=[(0.01 / risky_share, hi)] * len(names),
                   constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1},
                                {"type": "ineq", "fun": lambda w: cur["vol"] - np.sqrt(w @ cov @ w)}],
                   options={"maxiter": 500, "ftol": 1e-12})
    ports["Constrained: same risk, shrunk returns, 20% cap"] = res.x

    tab = pd.DataFrame({k: st(np.asarray(v)) for k, v in ports.items()}).T
    tab["net_change_vs_current"] = ["-" if k == "Current" else
                                    ("lower risk AND higher return" if tab.loc[k, "vol"] < cur["vol"] - 1e-6 and tab.loc[k, "return"] > cur["return"] + 0.005
                                     else "lower risk, same return" if tab.loc[k, "vol"] < cur["vol"] - 1e-6 and abs(tab.loc[k, "return"] - cur["return"]) <= 0.005
                                     else "lower risk, lower return" if tab.loc[k, "vol"] < cur["vol"] - 1e-6
                                     else "higher return, same/higher risk" if tab.loc[k, "return"] > cur["return"] + 1e-6 else "-") for k in tab.index]
    for c in ("return", "vol"):
        tab[c] *= 100
    tab.index.name = "Portfolio"

    weights = pd.DataFrame({k: 100 * np.asarray(v) * risky_share for k, v in ports.items()}, index=names)
    weights.index.name = "% of whole book"
    weights = weights[["Current", "FinQuant same risk, max return", "FinQuant same return, min risk",
                       "Constrained: same risk, shrunk returns, 20% cap"]]

    # Monte Carlo (library)
    pf.mc_optimisation(num_trials=a.mc)
    fig_ef = plt.figure(figsize=(10, 6))
    pf.ef_plot_efrontier()
    pf.ef_plot_optimal_portfolios()
    ax = plt.gca()
    ax.scatter(cur["vol"], cur["return"], c="black", s=120, marker="o", zorder=10, label="Current")
    ax.legend(frameon=False)
    ax.set_title("FinQuant efficient frontier (unconstrained, in-sample)")
    plt.tight_layout()
    plt.savefig(out / "11_fq_frontier.png", dpi=130)
    plt.close("all")
    pf.mc_plot_results()
    plt.gca().set_title(f"FinQuant Monte Carlo ({a.mc} random portfolios)")
    plt.tight_layout()
    plt.savefig(out / "12_fq_monte_carlo.png", dpi=130)
    plt.close("all")

    # out-of-sample honesty check: fit on first half of the window, judge on the second
    from portfolio_manager import optimise
    h = len(rets) // 2
    r1, r2 = rets.iloc[:h], rets.iloc[h:]
    mu1, cov1 = r1.mean().values * ANN, r1.cov().values * ANN
    n = len(names)
    w_ms = optimise(lambda w: -(w @ mu1 - a.rf) / np.sqrt(w @ cov1 @ w), n, 0.0, 1.0, np.ones(n) / n)
    w_mv = optimise(lambda w: w @ cov1 @ w, n, 0.0, 1.0, np.ones(n) / n)

    def oos(w):
        pr = r2.values @ w
        cum = np.cumprod(1 + pr)
        cagr = cum[-1] ** (ANN / len(pr)) - 1
        vol = pr.std(ddof=1) * np.sqrt(ANN)
        return {"2nd-half CAGR": 100 * cagr, "2nd-half vol": 100 * vol, "max_dd": 100 * (cum / np.maximum.accumulate(cum) - 1).min()}

    oost = pd.DataFrame({"Current mix": oos(w0), "Max-Sharpe fitted on 1st half": oos(w_ms), "Min-vol fitted on 1st half": oos(w_mv)}).T
    oost.index.name = "Out-of-sample"

    md = ["# FinQuant optimiser", "",
          md_table(tab, {"return": "{:.1f}%", "vol": "{:.1f}%", "sharpe": "{:.2f}"}), "",
          "## Weights (% of whole book; cash held constant)",
          md_table(weights, {c: "{:.1f}" for c in weights.columns}), "",
          "Every row above is IN-SAMPLE: the optimiser picks whatever did best in this window (here LLY, NVDA, SKHY; it drops all crypto). "
          "Treat the return gains as a ceiling made of hindsight, not a plan, including the capped row, which just hits the 20% caps.", "",
          "## Honesty check: fit on the first half, run on the second half",
          md_table(oost, {"2nd-half CAGR": "{:.1f}%", "2nd-half vol": "{:.1f}%", "max_dd": "{:.1f}%"}), "",
          "If the fitted portfolios do not beat the current mix out-of-sample, the in-sample 'improvement' was overfitting."]
    (out / "fq_optimise.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
