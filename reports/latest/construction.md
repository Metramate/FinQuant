# Portfolio construction

## 1. Out-of-sample validation (2021-07-01 to 2026-11-03, monthly refit on the previous 3 years, ~21 assets available on average)
| Method | CAGR % | vol % | Sharpe | max drawdown % | worst 20d % | turnover %/yr |
|---|---|---|---|---|---|---|
| Equal weight | 25.7 | 26.3 | 0.86 | -33.1 | -18.7 | 60.0 |
| Hand-set plan weights | 26.2 | 24.8 | 0.94 | -36.6 | -17.1 | 52.1 |
| FinQuant max-Sharpe (cap 15%) | 27.9 | 20.2 | 1.23 | -23.1 | -15.5 | 109.0 |
| FinQuant min-variance (cap 15%) | 19.1 | 15.2 | 1.06 | -17.3 | -10.4 | 48.3 |
| Equal risk contribution (cap 15%) | 24.0 | 20.1 | 1.05 | -23.9 | -13.6 | 50.2 |
| Risk budgets by sleeve + position caps | 25.7 | 22.0 | 1.04 | -29.9 | -14.4 | 51.5 |

Costs: 10bp per side (25bp crypto). All methods see the same hindsight-picked universe, so compare rows against each other.
## 2. Optimised targets (% of whole book, 5% cash on top) vs my hand-set ones
| Ticker | now % | optimised A | optimised B | optimised C | hand-set A | hand-set B | hand-set C |
|---|---|---|---|---|---|---|---|
| BTC | 21.9 | 10.9 | 10.8 | 10.2 | 17.0 | 14.5 | 13.0 |
| CRSP | 0.0 | 0.0 | 0.0 | 2.1 | 0.0 | 0.0 | 2.0 |
| ETH | 9.1 | 4.4 | 4.3 | 4.1 | 6.0 | 5.0 | 4.5 |
| GEV | 0.0 | 0.0 | 2.6 | 2.0 | 0.0 | 3.0 | 3.0 |
| HOOD | 0.0 | 2.2 | 1.6 | 1.2 | 3.0 | 3.0 | 3.0 |
| INDA | 0.0 | 0.0 | 0.0 | 5.7 | 0.0 | 0.0 | 3.0 |
| ITA | 4.1 | 5.7 | 5.7 | 4.8 | 4.0 | 4.0 | 4.0 |
| LLY | 4.0 | 5.7 | 5.7 | 5.7 | 4.0 | 4.0 | 4.0 |
| MA | 0.0 | 7.6 | 7.5 | 7.0 | 4.0 | 5.0 | 5.5 |
| NEAR | 1.7 | 1.1 | 1.2 | 1.1 | 1.5 | 1.0 | 1.0 |
| NLR | 2.9 | 4.6 | 3.2 | 2.5 | 3.0 | 3.0 | 3.0 |
| NVDA | 5.1 | 4.5 | 4.3 | 4.1 | 5.0 | 4.5 | 4.5 |
| PICK | 0.0 | 0.0 | 4.5 | 3.4 | 0.0 | 3.0 | 3.0 |
| QQQM | 14.8 | 10.3 | 9.4 | 9.0 | 12.0 | 10.5 | 9.5 |
| QTUM | 3.0 | 4.3 | 4.0 | 3.9 | 3.0 | 3.0 | 3.0 |
| SKHY | 5.1 | 4.2 | 3.9 | 3.8 | 5.0 | 4.5 | 4.0 |
| SMH | 9.9 | 4.8 | 4.4 | 4.2 | 7.0 | 6.5 | 6.0 |
| UFO | 2.0 | 4.9 | 3.4 | 2.6 | 2.0 | 2.0 | 2.0 |
| UNI | 2.0 | 1.2 | 1.2 | 1.2 | 1.5 | 1.5 | 1.5 |
| V | 0.0 | 7.6 | 7.4 | 6.9 | 4.0 | 5.0 | 5.5 |
| VST | 5.1 | 3.4 | 2.4 | 1.9 | 5.0 | 4.5 | 4.0 |
| WORLD | 0.0 | 7.6 | 7.6 | 7.6 | 8.0 | 7.5 | 6.0 |

## 3. Risk by sleeve (% of total portfolio risk) at each optimised stage
| sleeve | A | B | C |
|---|---|---|---|
| ai_tech | 31.8 | 30.7 | 30.6 |
| crypto | 32.9 | 31.7 | 31.5 |
| other_thesis | 25.7 | 27.8 | 28.0 |
| steady | 5.2 | 5.2 | 5.2 |
| world | 4.4 | 4.5 | 4.8 |

## 4. Stage mixes: optimised vs hand-set (covariance since the last 3 years)
| stage / mix | vol % | worst drawdown % | largest weight % | crypto share of risk % | no-sell floor binding |
|---|---|---|---|---|---|
| stage A optimised | 22.6 | -24.1 | 10.9 | 32.9 | ETH, SMH |
| stage A hand-set | 26.2 | -27.2 | 17.0 | 44.7 | - |
| stage B optimised | 23.0 | -23.6 | 10.8 | 31.7 | - |
| stage B hand-set | 25.8 | -26.1 | 14.5 | 36.2 | - |
| stage C optimised | 22.0 | -22.5 | 10.2 | 31.5 | - |
| stage C hand-set | 24.9 | -25.3 | 13.0 | 33.9 | - |

