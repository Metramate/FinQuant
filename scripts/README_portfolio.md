# Personal portfolio tooling

One command: `python scripts/run_all.py` (about 30 s; prices cached per day in `.cache/`, `PM_NO_CACHE=1` to refresh).
Start with `reports/latest/REPORT.md`; every script also runs alone.

| script | question it answers |
|---|---|
| `portfolio_manager.py` | **main report**: risk contributions, charts 01-06, ranked recommendations. Trims are recommended only if they lower risk AND don't lower return (in-sample + backtest gate); otherwise "keep, aggressive by design" |
| `backtest.py` | does trimming/rebalancing (cap 20%, crypto cap 30%, risk-balanced blend) beat the plain mix, walk-forward, net of costs, in both halves? Writes `backtest.json` used by the report |
| `stress.py` | worst 20-day windows replayed on today's weights; shocks like BTC -40%, QQQM -15% (factor betas) |
| `signals.py` | 50/200-day SMA, Bollinger %B, RSI per holding (FinQuant's `finquant.moving_average`); tests a 200d trend filter on your mix |
| `fq_optimise.py` | FinQuant's efficient frontier / Monte Carlo; same-risk-max-return and same-return-min-risk mixes; out-of-sample overfitting check |
| `watchlist.py` | rank candidate adds (new cash, default 2.5%) by effect on your risk, correlation, betas |
| `what_if.py` | one ticker at X% of the book (`--fund new/prorata/cash`) |
| `checkin.py` | dated snapshot in `reports/history/`, change since last run, alerts from `data/pm_rules.json` (max weights, drift vs plan, theme risk, 5-day moves, oversold) |
| `tax_lots.py` | tax estimate for suggested sells from `data/my-lots.csv` (`--init` creates it); loss-harvest candidates |
| `compounders.py` | glass cannon vs steady compounders (V, MA, ...): facts, rolling 4-year holds, EUR 1,000 simulation, 'what you must believe' heatmap (`reports/latest/compounders/`) |
| `horizon.py` | **goal age 35-40 research (current)**: EUR 1M (today's money) from job-based savings plans, 100 years of data, bootstrap, walk-forward, tech dial, income link (`reports/latest/horizon/`) |
| `longterm.py` + `longterm_data.py` | (superseded: assumed a 37-year horizon) long-horizon savings research on 100 years of US data (Ken French + Shiller): where EUR 1M comes from, 37-year journeys for ~12 strategies, walk-forward out-of-sample tests, era split, income-vs-tech-cycle test, suggested split (`reports/latest/longterm/`) |
| `monthly_plan.py` + `data/targets.json` | **monthly buy list**: new money goes to the (max 5) positions furthest under target, never sells; targets change at EUR 20k and 30k (turbines + mining, then India + gene editing); `--apply` writes buys to the CSV (backup kept), `--simulate 36 --report` shows the path and risk |
| `picks.py` | screen candidate quirky picks / steady compounders against your book (data only) |
| `my_prices.py` | shared Yahoo loader; extends young listings with `history_proxy` (SKHY <- `000660.KS`) |
| `load_my_portfolio.py` | quick FinQuant summary (`--fetch`) |

Data you edit: `data/my-portfolio.csv` (holdings; `theme`, `history_proxy`), `data/my-lots.csv` (real purchase lots + dates),
`data/pm_rules.json` (alert limits, my starting assumptions).

Assumptions that are mine, not facts: risk-free 4%, 20% per-asset cap, trading costs 10bp/25bp crypto, tax rates 30%/15%.
All statistics are in-sample history since 2024 (a strong crypto/AI bull run); the stock selection is hindsight-biased.
Not financial or tax advice.
