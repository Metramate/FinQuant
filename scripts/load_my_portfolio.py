"""Load data/my-portfolio.csv into a FinQuant ``Portfolio``.

Two distinct things live in the holdings file and are kept separate here:

* the *position ledger* (quantity, cost basis, cash) -- what you own;
* the *FinQuant allocation* (``Name`` + ``Allocation``) -- the risky-asset
  weights FinQuant needs for analysis/optimisation.

Cash (USDT) has no price history, so it is excluded from the FinQuant
portfolio but reported in the summary so totals still reconcile.

Usage:
    python scripts/load_my_portfolio.py                 # cost-basis weights, offline summary
    python scripts/load_my_portfolio.py --fetch         # also pull prices via yfinance + analyse
    python scripts/load_my_portfolio.py --fetch --start 2024-01-01
"""
import argparse
import pathlib

import pandas as pd

HOLDINGS = pathlib.Path(__file__).resolve().parent.parent / "data" / "my-portfolio.csv"


def load_holdings(path=HOLDINGS) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Integrity check: cost must equal quantity * average price (rounded to $1).
    gap = (df["quantity"] * df["avg_price_usd"] - df["cost_usd"]).abs()
    if (gap > 1.0).any():
        raise ValueError(f"cost_usd != quantity*avg_price_usd:\n{df[gap > 1.0]}")
    return df


def finquant_allocation(df: pd.DataFrame, values: pd.Series | None = None) -> pd.DataFrame:
    """Risky-asset allocation in FinQuant's format (columns: Allocation, Name).

    ``values`` = current market value per yahoo_ticker; defaults to cost basis.
    Allocation is the weight in % of the *risky* sleeve (cash excluded).
    """
    risky = df[df["asset_class"] != "cash"].copy()
    base = risky["cost_usd"] if values is None else risky["yahoo_ticker"].map(values)
    risky["Allocation"] = 100 * base / base.sum()
    return risky.rename(columns={"yahoo_ticker": "Name"})[["Allocation", "Name"]].reset_index(drop=True)


def summary(df: pd.DataFrame, prices: pd.Series | None = None) -> pd.DataFrame:
    out = df.copy()
    if prices is not None:
        px = out["yahoo_ticker"].map(prices).fillna(out["avg_price_usd"])  # cash stays at 1
        out["price_usd"] = px
        out["value_usd"] = out["quantity"] * px
        out["pnl_usd"] = out["value_usd"] - out["cost_usd"]
        out["pnl_pct"] = 100 * out["pnl_usd"] / out["cost_usd"]
        out["weight_now_pct"] = 100 * out["value_usd"] / out["value_usd"].sum()
    else:
        out["weight_cost_pct"] = 100 * out["cost_usd"] / out["cost_usd"].sum()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="download prices from Yahoo and analyse")
    ap.add_argument("--start", default="2024-01-01")
    args = ap.parse_args()

    df = load_holdings()
    print(f"{len(df)} positions, cost basis ${df['cost_usd'].sum():,.0f}")
    by_class = df.groupby("asset_class")["cost_usd"].sum()
    print((100 * by_class / by_class.sum()).round(1).rename("% of cost basis").to_string(), "\n")

    if not args.fetch:
        print(summary(df).round(2).to_string(index=False))
        print("\nFinQuant allocation (risky sleeve, cost-basis weights):")
        print(finquant_allocation(df).round(2).to_string(index=False))
        return

    from finquant.portfolio import build_portfolio

    # Last close per ticker for valuation (first pass with cost weights to get prices).
    alloc = finquant_allocation(df)
    pf = build_portfolio(
        names=alloc["Name"].tolist(),
        pf_allocation=alloc,
        start_date=args.start,
        data_api="yfinance",
    )
    last = pf.data.ffill().iloc[-1]
    print(summary(df, last).round(2).to_string(index=False))

    # Re-weight FinQuant portfolio to *current market value* so analytics reflect today's book.
    live = finquant_allocation(df, df.set_index("yahoo_ticker")["quantity"] * last)
    pf = build_portfolio(data=pf.data, pf_allocation=live)
    pf.properties()


if __name__ == "__main__":
    main()
