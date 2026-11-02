"""Tax-aware view of proposed sells, from purchase lots.

    python scripts/tax_lots.py --init                       # create data/my-lots.csv from your holdings (1 lot each)
    python scripts/tax_lots.py                              # tax on the sells in reports/latest/trades.json
    python scripts/tax_lots.py --sell BTC=800 ETH=250       # or specific USD sells
    python scripts/tax_lots.py --short-rate 0.30 --long-rate 0.15

Lots: ``data/my-lots.csv`` (ticker, lot_id, acquired, quantity, price_usd, fees_usd). ``--init`` only knows your
AVERAGE price, so each position starts as one lot with a blank date: edit in your real lots/dates for real answers.
A blank date is treated as SHORT-term (conservative). Lot choice is HIFO (highest cost first = smallest gain).

ASSUMPTIONS, not facts about you: tax rates default to placeholders (short 30%, long 15%). Rules differ by country;
wash-sale / crypto rules change: check yours. This is an estimate, not tax advice.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from load_my_portfolio import load_holdings  # noqa: E402
from my_prices import fetch_prices  # noqa: E402
from portfolio_manager import md_table  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOTS = ROOT / "data" / "my-lots.csv"


def init_lots(df: pd.DataFrame) -> pd.DataFrame:
    r = df[df["asset_class"] != "cash"]
    return pd.DataFrame({"ticker": r["ticker"], "lot_id": 1, "acquired": "", "quantity": r["quantity"],
                         "price_usd": r["avg_price_usd"], "fees_usd": 0.0})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--sell", nargs="*", help="TICKER=USD ...")
    ap.add_argument("--short-rate", type=float, default=0.30)
    ap.add_argument("--long-rate", type=float, default=0.15)
    ap.add_argument("--trades", default=str(ROOT / "reports" / "latest" / "trades.json"))
    ap.add_argument("--out", default=str(ROOT / "reports" / "latest"))
    a = ap.parse_args()
    df = load_holdings()

    if a.init:
        if LOTS.exists():
            sys.exit(f"{LOTS} already exists; not overwriting")
        init_lots(df).to_csv(LOTS, index=False)
        print(f"Wrote {LOTS}: one lot per position (average price, blank date). Edit it with your real lots.")
        return

    if not LOTS.exists():
        sys.exit("No data/my-lots.csv yet: run with --init first")
    lots = pd.read_csv(LOTS, parse_dates=["acquired"])
    yahoo = df.set_index("ticker")["yahoo_ticker"]
    px = fetch_prices(df, "2026-09-01").ffill().iloc[-1]
    price = {t: float(px[yahoo[t]]) for t in lots["ticker"].unique()}
    today = pd.Timestamp.today().normalize()

    if a.sell:
        sells = {k: float(v) for k, v in (x.split("=") for x in a.sell)}
    else:
        tj = json.loads(pathlib.Path(a.trades).read_text()) if pathlib.Path(a.trades).exists() else {}
        sells = {k: -v for k, v in tj.items() if v < 0}
    rows, detail = [], []
    for t, usd in sells.items():
        need = usd / price[t]
        gain_s = gain_l = 0.0
        L = lots[lots["ticker"] == t].copy()
        L["unit_cost"] = (L["price_usd"] * L["quantity"] + L["fees_usd"]) / L["quantity"]
        for _, lot in L.sort_values("unit_cost", ascending=False).iterrows():
            take = min(need, lot["quantity"])
            if take <= 0:
                break
            g = take * (price[t] - lot["unit_cost"])
            long_ = pd.notna(lot["acquired"]) and (today - lot["acquired"]).days > 365
            gain_l, gain_s = (gain_l + g, gain_s) if long_ else (gain_l, gain_s + g)
            need -= take
        tax = max(gain_s, 0) * a.short_rate + max(gain_l, 0) * a.long_rate
        rows.append({"Ticker": t, "sell_usd": usd, "gain_short": gain_s, "gain_long": gain_l, "est_tax": tax,
                     "tax_pct_of_sale": 100 * tax / usd})
    tab = pd.DataFrame(rows).set_index("Ticker") if rows else pd.DataFrame()

    # unrealised losses = tax-loss harvest candidates
    cur = lots.assign(value=lots["quantity"] * lots["ticker"].map(price), cost=lots["quantity"] * lots["price_usd"] + lots["fees_usd"])
    cur["unrealised"] = cur["value"] - cur["cost"]
    loss = cur[cur["unrealised"] < -1].sort_values("unrealised")

    md = ["# Tax-aware trades (estimate)", f"Rates (ASSUMED): short {100*a.short_rate:.0f}%, long {100*a.long_rate:.0f}%. Blank lot dates count as short-term.", ""]
    if len(tab):
        md += [md_table(tab, {"sell_usd": "${:,.0f}", "gain_short": "${:+,.0f}", "gain_long": "${:+,.0f}", "est_tax": "${:,.0f}", "tax_pct_of_sale": "{:.1f}%"}),
               f"\nTotal estimated tax on these sells: **${tab['est_tax'].sum():,.0f}**"]
    else:
        md += ["No sells given/suggested."]
    md += ["", "## Loss-harvest candidates (unrealised losses by lot)"]
    md += [md_table(loss.set_index("ticker")[["quantity", "price_usd", "value", "unrealised"]],
                    {"quantity": "{:.4f}", "price_usd": "{:,.2f}", "value": "${:,.0f}", "unrealised": "${:+,.0f}"})] if len(loss) else ["None."]
    md += ["", "Estimate only; check your jurisdiction's wash-sale and crypto rules before acting."]
    (pathlib.Path(a.out) / "tax_lots.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
