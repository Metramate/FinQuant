"""Stress tests for the current book.

    python scripts/stress.py

1. Historical: the worst 20-day windows your CURRENT weights would have suffered since --start,
   with a per-holding breakdown of who caused the loss.
2. Hypothetical: factor shocks. Each holding is regressed on QQQM (equity beta) and BTC (crypto beta) over
   the window; a scenario (e.g. QQQM -15%, BTC -40%) is pushed through those betas. Leftover (idiosyncratic)
   moves are ignored, and betas measured in calm periods understate crash behaviour -> treat as a floor.
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
from portfolio_manager import build_book, md_table  # noqa: E402

SCENARIOS = {
    "Market -10% (QQQM)": {"QQQM": -0.10, "BTC": 0.0},
    "Market -20% (QQQM)": {"QQQM": -0.20, "BTC": 0.0},
    "Crypto -40% (BTC)": {"QQQM": 0.0, "BTC": -0.40},
    "Crypto -60% (BTC)": {"QQQM": 0.0, "BTC": -0.60},
    "Risk-off: QQQM -15%, BTC -40%": {"QQQM": -0.15, "BTC": -0.40},
    "2022-style: QQQM -30%, BTC -60%": {"QQQM": -0.30, "BTC": -0.60},
    "Melt-up: QQQM +15%, BTC +40%": {"QQQM": 0.15, "BTC": 0.40},
}


def worst_windows(port: pd.Series, rets: pd.DataFrame, w: pd.Series, k: int = 3, win: int = 20):
    roll = (1 + port).rolling(win).apply(np.prod, raw=True) - 1
    picks, taken = [], pd.Series(False, index=port.index)
    for end in roll.sort_values().index:
        i = port.index.get_loc(end)
        if taken.iloc[max(0, i - win): i + win].any():
            continue
        taken.iloc[i] = True
        seg = rets.iloc[i - win + 1: i + 1]
        contrib = ((1 + seg).prod() - 1) * w  # approx: window return of each holding x its weight
        picks.append((end, roll.loc[end], contrib.sort_values().head(4)))
        if len(picks) == k:
            break
    return picks


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", default="2024-01-01")
    ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parent.parent / "reports" / "latest"))
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    df = load_holdings()
    risky, cash, book, px = build_book(df, fetch_prices(df, a.start))
    rets = px.pct_change().dropna()
    w = risky["w_book"]  # whole-book weights; cash assumed to hold value
    port = pd.Series(rets.values @ w.values, index=rets.index)

    # 1. historical
    picks = worst_windows(port, rets, w)
    # 2. hypothetical via betas
    X = np.c_[np.ones(len(rets)), rets["QQQM"], rets["BTC"]]
    betas = pd.DataFrame(np.linalg.lstsq(X, rets.values, rcond=None)[0][1:], index=["b_QQQM", "b_BTC"], columns=rets.columns).T
    rows = {}
    for name, sh in SCENARIOS.items():
        asset = betas["b_QQQM"] * sh["QQQM"] + betas["b_BTC"] * sh["BTC"]
        rows[name] = {"book_pct": 100 * float((asset * w).sum()), "usd": float((asset * w).sum() * book)}
    sc = pd.DataFrame(rows).T
    sc.index.name = "Scenario"
    shocked = (betas["b_QQQM"] * -0.15 + betas["b_BTC"] * -0.40) * w * book

    md = [f"# Stress tests (book ${book:,.0f}, cash ${cash:,.0f} assumed flat)", "",
          "## Worst 20-day windows for today's weights"]
    for end, ret, contrib in picks:
        md.append(f"- ending **{end.date()}**: {100*ret:.1f}% of the book. Biggest damage: "
                  + ", ".join(f"{k} {100*v:.1f}pt" for k, v in contrib.items()))
    md += ["", "## Hypothetical shocks (factor betas to QQQM and BTC)",
           md_table(sc, {"book_pct": "{:+.1f}%", "usd": "${:+,.0f}"}), "",
           "Betas (each holding vs QQQM and BTC):", md_table(betas.round(2).rename_axis("Ticker")), "",
           "Floor, not ceiling: betas come from a mostly calm sample, idiosyncratic moves are ignored, and correlations rise in crashes."]
    (out / "stress.md").write_text("\n".join(md) + "\n")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 5.2), gridspec_kw={"width_ratios": [1.2, 1]})
    sc_sorted = sc.sort_values("book_pct")
    a1.barh(sc_sorted.index, sc_sorted["book_pct"], color=["#d1495b" if x < 0 else "#2a9d8f" for x in sc_sorted["book_pct"]])
    for i, v in enumerate(sc_sorted["book_pct"]):
        a1.text(v + (0.4 if v > 0 else -0.4), i, f"{v:+.1f}%", va="center", ha="left" if v > 0 else "right", fontsize=8)
    a1.set_title("Hypothetical shocks: impact on whole book")
    a1.margins(x=0.18)
    s = shocked.sort_values().head(8)
    a2.barh(s.index, s.values, color="#d1495b")
    a2.set_title("Who hurts most in 'Risk-off: QQQM -15%, BTC -40%' ($)")
    fig.tight_layout()
    fig.savefig(out / "09_stress.png", dpi=130)
    plt.close(fig)
    print("\n".join(md))


if __name__ == "__main__":
    main()
