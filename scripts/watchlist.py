"""Rank candidate additions by what they do to YOUR book.

    python scripts/watchlist.py                                  # default candidates, 2.5% new cash each
    python scripts/watchlist.py --tickers HOOD IBKR GLD --pct 3

For each candidate, funded with brand-new cash (existing positions unchanged, cash earns rf):
  d_vol          change in whole-book volatility (negative = diversifies)
  d_worst20      change in the worst past 20-day loss (positive = shallower loss)
  corr_book      correlation of the candidate with your current book
  beta_QQQM/BTC  how it moves with equities / crypto
  own_return/vol the candidate's own history (hindsight: NOT a forecast)
Sorted by d_vol. Aggressive portfolios may prefer high-return/high-vol adds; the table shows both sides so you
choose on purpose. Everything is in-sample on candidates with full history over the window.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import numpy as np
import pandas as pd
import yfinance as yf

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from load_my_portfolio import load_holdings  # noqa: E402
from my_prices import fetch_prices  # noqa: E402
from portfolio_manager import ANN, build_book, md_table  # noqa: E402

DEFAULTS = ["HOOD", "IBKR", "SCHW", "COIN", "GLD", "TLT", "XLU", "XLP", "BRK-B", "MSFT", "AVGO", "PLTR", "XLE", "IBIT"]


def worst20(pr: np.ndarray) -> float:
    return float((pd.Series(1 + pr).rolling(20).apply(np.prod, raw=True) - 1).min())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tickers", nargs="+", default=DEFAULTS)
    ap.add_argument("--pct", type=float, default=2.5, help="size as %% of the new book")
    ap.add_argument("--start", default="2024-01-01")
    ap.add_argument("--rf", type=float, default=0.04)
    ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parent.parent / "reports" / "latest"))
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    x = a.pct / 100

    df = load_holdings()
    risky, cash, book, px = build_book(df, fetch_prices(df, a.start))
    rets = px.pct_change().dropna()
    base = pd.Series(rets.values @ risky["w_book"].values + cash / book * a.rf / ANN, index=rets.index)

    cand = yf.download(a.tickers, start=a.start, auto_adjust=False, progress=False)["Adj Close"]
    if isinstance(cand, pd.Series):
        cand = cand.to_frame(a.tickers[0])
    cand.index = pd.to_datetime(cand.index).tz_localize(None)
    cand = cand.reindex(px.index).ffill()

    base_vol, base_w20 = base.std() * np.sqrt(ANN), worst20(base.values)
    rows, skipped = {}, []
    for t in a.tickers:
        if t not in cand or cand[t].isna().mean() > 0.05:
            skipped.append(t)
            continue
        c = cand[t].pct_change().reindex(rets.index).fillna(0.0)
        new = (1 - x) * base + x * c
        rows[t] = {
            "d_vol": 100 * (new.std() - base.std()) * np.sqrt(ANN),
            "d_worst20": 100 * (worst20(new.values) - base_w20),
            "corr_book": float(np.corrcoef(c, base)[0, 1]),
            "beta_QQQM": float(np.cov(c, rets["QQQM"])[0, 1] / rets["QQQM"].var()),
            "beta_BTC": float(np.cov(c, rets["BTC"])[0, 1] / rets["BTC"].var()),
            "own_return": 100 * ((1 + c).prod() ** (ANN / len(c)) - 1),
            "own_vol": 100 * c.std() * np.sqrt(ANN),
            "from_1y_high": 100 * (cand[t].iloc[-1] / cand[t].iloc[-ANN:].max() - 1),
        }
    tab = pd.DataFrame(rows).T.sort_values("d_vol")
    tab.index.name = "Candidate"
    md = [f"# Watchlist: add {a.pct:g}% of the book in new cash",
          f"Baseline: book vol {100*base_vol:.1f}%, worst 20-day {100*base_w20:.1f}%.", "",
          md_table(tab, {"d_vol": "{:+.2f}pt", "d_worst20": "{:+.2f}pt", "corr_book": "{:.2f}", "beta_QQQM": "{:.2f}", "beta_BTC": "{:.2f}",
                         "own_return": "{:+.0f}%", "own_vol": "{:.0f}%", "from_1y_high": "{:+.0f}%"}), "",
          (f"Skipped (missing history): {', '.join(skipped)}. " if skipped else "")
          + "own_return is hindsight over the window, not a forecast. Negative d_vol = lowers book risk; positive d_worst20 = shallower worst loss."]
    (out / "watchlist.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
