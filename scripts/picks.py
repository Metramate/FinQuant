"""Screen candidate 'quirky' picks and 'steady compounders' against YOUR current book.

    python scripts/picks.py                       # default candidate lists
    python scripts/picks.py --quirky RKLB KTOS    # your own list

For every candidate: history length, volatility, distance from 1-year high, hindsight return (NOT a forecast), and
correlation with your current book / QQQM / BTC. Then a greedy selection that picks names from DIFFERENT themes with the
lowest correlation to your book and to each other, so the sleeve adds exposure instead of repeating what you hold.

What this cannot tell you: valuation, business quality, or whether a theme works. Yahoo's fundamentals endpoint is not
reachable from here, so check those yourself. Not advice.
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

ROOT = pathlib.Path(__file__).resolve().parent.parent
QUIRKY = {  # theme -> tickers (my candidate universe; verify each exists/trades for you)
    "Defense tech / drones": ["KTOS", "AVAV", "PLTR", "AXON"],
    "Space": ["RKLB", "ASTS", "PL"],
    "Nuclear / uranium": ["CCJ", "OKLO", "SMR", "LEU", "UEC"],
    "Quantum": ["IONQ", "RGTI"],
    "AI infrastructure": ["VRT", "ANET", "ALAB", "CRWV"],
    "Semis (non-NVDA)": ["TSM", "ASML", "MU", "AVGO"],
    "Power / grid": ["GEV", "CEG", "BE"],
    "Fintech / crypto": ["SOFI", "COIN"],
    "Cybersecurity / software": ["CRWD", "PANW"],
    "Robotics / autos": ["TSLA", "ISRG"],
}
STEADY = ["V", "MA", "SPGI", "MCO", "COST", "BRK-B", "ADP", "WM", "MSFT", "ROP", "ODFL", "LIN"]


def metrics(px: pd.DataFrame, book: pd.Series, qqqm: pd.Series, btc: pd.Series) -> pd.DataFrame:
    r = px.pct_change()
    rows = {}
    for t in px:
        s = r[t].dropna()
        p = px[t].dropna()
        both = pd.concat([s, book], axis=1, keys=["a", "b"]).dropna()
        rows[t] = {
            "years": len(p) / ANN,
            "vol %": 100 * s.std() * np.sqrt(ANN),
            "from 1y high %": 100 * (p.iloc[-1] / p.iloc[-ANN:].max() - 1),
            "1y return % (hindsight)": 100 * (p.iloc[-1] / p.iloc[-ANN] - 1) if len(p) > ANN else np.nan,
            "corr book": both["a"].corr(both["b"]) if len(both) > 100 else np.nan,
            "corr QQQM": s.corr(qqqm),
            "corr BTC": s.corr(btc),
            "worst 1y drawdown %": 100 * (p.iloc[-ANN:] / p.iloc[-ANN:].cummax() - 1).min(),
        }
    return pd.DataFrame(rows).T


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quirky", nargs="*")
    ap.add_argument("--steady", nargs="*", default=STEADY)
    ap.add_argument("--start", default="2023-01-01")
    ap.add_argument("--min-years", type=float, default=1.5)
    ap.add_argument("--out", default=str(ROOT / "reports" / "latest"))
    a = ap.parse_args()
    q = {"custom": a.quirky} if a.quirky else QUIRKY
    qt = [t for v in q.values() for t in v]

    df = load_holdings()
    risky, cash, book, bpx = build_book(df, fetch_prices(df, "2024-01-01"))
    book_r = (bpx.pct_change().dropna() * risky["w_sleeve"]).sum(axis=1)

    allt = sorted(set(qt + a.steady))
    px = yf.download(allt + ["QQQM", "BTC-USD"], start=a.start, auto_adjust=False, progress=False)["Adj Close"]
    px.index = pd.to_datetime(px.index).tz_localize(None)
    px = px[px["QQQM"].notna()].ffill()
    qqqm, btc = px["QQQM"].pct_change(), px["BTC-USD"].pct_change()
    have = [t for t in allt if t in px and px[t].notna().sum() > 60]
    missing = sorted(set(allt) - set(have))
    M = metrics(px[have], book_r, qqqm, btc)
    theme_of = {t: th for th, v in q.items() for t in v}

    # greedy sleeve: one name per theme, lowest correlation to the book and to already-picked names
    R = px[have].pct_change()
    chosen, rows = [], []
    cands = {th: [t for t in v if t in M.index and M.loc[t, "years"] >= a.min_years] for th, v in q.items()}
    pool = {th: v for th, v in cands.items() if v}
    while pool and len(chosen) < 10:
        best = None
        for th, v in pool.items():
            for t in v:
                pair = np.mean([R[t].corr(R[c]) for c in chosen]) if chosen else 0.0
                score = M.loc[t, "corr book"] + pair + M.loc[t, "vol %"] / 200  # lower is better; small vol penalty
                if best is None or score < best[0]:
                    best = (score, th, t)
        _, th, t = best
        chosen.append(t); rows.append((th, t)); pool.pop(th)
    sleeve = R[chosen].mean(axis=1).dropna() if chosen else pd.Series(dtype=float)
    sv = 100 * sleeve.std() * np.sqrt(ANN) if len(sleeve) else np.nan
    sc = sleeve.corr(book_r) if len(sleeve) else np.nan

    steady = M.loc[[t for t in a.steady if t in M.index]].sort_values("corr book")
    quirky = M.loc[[t for t in qt if t in M.index]].copy()
    quirky.insert(0, "theme", [theme_of[t] for t in quirky.index])
    quirky.index.name = steady.index.name = "Ticker"
    fmt = {"years": "{:.1f}", "vol %": "{:.0f}", "from 1y high %": "{:+.0f}", "1y return % (hindsight)": "{:+.0f}", "corr book": "{:.2f}", "corr QQQM": "{:.2f}", "corr BTC": "{:.2f}", "worst 1y drawdown %": "{:.0f}"}
    md = ["# Candidate screen (data only: no valuation, no fundamentals)", "",
          f"Your book's returns are the current weights of {len(risky)} holdings. 'corr book' near 1 = moves like what you already own.", "",
          "## Quirky candidates (sorted by theme)", md_table(quirky.sort_values(["theme", "corr book"]), fmt), "",
          f"## Suggested spread (one per theme, lowest correlation to your book and to each other): {', '.join(f'{t} ({th})' for th, t in rows)}",
          f"Equal-weighted sleeve: vol {sv:.0f}%, correlation with your book {sc:.2f}.", "",
          "## Steady compounders (sorted by lowest correlation with your book)", md_table(steady, fmt), "",
          (f"Not found / too little data: {', '.join(missing)}" if missing else ""), "Hindsight returns are not forecasts; check valuation and business quality yourself."]
    (pathlib.Path(a.out) / "picks.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
