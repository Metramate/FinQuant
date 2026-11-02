# Personal portfolio tooling

| file | what |
|---|---|
| `data/my-portfolio.csv` | holdings ledger. `theme` groups holdings for the report; `history_proxy` names an older listing used to extend a young ticker's price history (SKHY -> `000660.KS`) |
| `scripts/my_prices.py` | Yahoo price loader with proxy splice (currency-converted, 1-day lead alignment, junction-continuous) |
| `scripts/load_my_portfolio.py` | quick FinQuant summary (`--fetch` for analytics) |
| `scripts/portfolio_manager.py` | **main entry**: risk analytics, optimisation, 6 charts, `reports/latest/REPORT.md`, recommendations |

```
pip install -e . yfinance
python scripts/portfolio_manager.py                  # defaults: start 2024-01-01, rf 4%, 20% cap
python scripts/portfolio_manager.py --max-weight 0.15 --rf 0.035
```

To update holdings, edit `quantity`/`avg_price_usd`/`cost_usd` in the CSV (cost must equal quantity x avg price) and rerun.
Re-running overwrites `reports/latest/`; point `--out` elsewhere to keep a dated copy.
