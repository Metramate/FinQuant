# Portfolio construction

## 1. Out-of-sample validation (2021-07-01 to 2026-11-03, monthly refit on the previous 3 years, ~20 assets available on average)
| Method | CAGR % | vol % | Sharpe | max drawdown % | worst 20d % | turnover %/yr |
|---|---|---|---|---|---|---|
| Equal weight | 24.9 | 25.5 | 0.86 | -32.3 | -19.0 | 59.4 |
| Hand-set plan weights | 26.2 | 25.2 | 0.92 | -37.3 | -17.5 | 52.8 |
| FinQuant max-Sharpe (cap 15%) | 25.6 | 18.7 | 1.21 | -21.1 | -15.0 | 85.4 |
| FinQuant min-variance (cap 15%) | 19.8 | 15.0 | 1.13 | -16.2 | -11.6 | 49.9 |
| Equal risk contribution (cap 15%) | 23.8 | 19.3 | 1.08 | -23.3 | -14.2 | 49.8 |
| Risk budgets by sleeve + position caps | 25.2 | 20.7 | 1.07 | -27.7 | -14.7 | 51.5 |

Costs: 10bp per side (25bp crypto). All methods see the same hindsight-picked universe, so compare rows against each other.
## 2. Optimised targets (% of whole book, 5% cash on top) vs my hand-set ones
| Ticker | now % | optimised A | optimised B | optimised C | hand-set A | hand-set B | hand-set C |
|---|---|---|---|---|---|---|---|
| BTC | 21.9 | 10.7 | 10.2 | 9.7 | 17.0 | 14.5 | 13.0 |
| COST | 0.0 | 7.6 | 7.6 | 7.6 | 0.0 | 0.0 | 0.0 |
| CRSP | 0.0 | 0.0 | 0.0 | 2.3 | 0.0 | 0.0 | 2.0 |
| ETH | 9.1 | 4.4 | 4.0 | 3.8 | 6.0 | 5.0 | 4.5 |
| GEV | 0.0 | 0.0 | 3.0 | 2.2 | 0.0 | 3.0 | 3.0 |
| INDA | 0.0 | 0.0 | 0.0 | 5.7 | 0.0 | 0.0 | 3.0 |
| ITA | 4.1 | 5.7 | 5.7 | 5.3 | 4.0 | 4.0 | 4.0 |
| LLY | 4.0 | 7.6 | 7.5 | 6.9 | 4.0 | 4.0 | 4.0 |
| MA | 0.0 | 7.6 | 7.6 | 7.6 | 4.0 | 5.0 | 5.5 |
| NEAR | 1.7 | 1.0 | 1.1 | 1.0 | 1.5 | 1.0 | 1.0 |
| NLR | 2.9 | 5.7 | 3.7 | 2.7 | 3.0 | 3.0 | 3.0 |
| NVDA | 5.1 | 4.0 | 3.8 | 3.7 | 5.0 | 4.5 | 4.5 |
| PICK | 0.0 | 0.0 | 5.4 | 3.9 | 0.0 | 3.0 | 3.0 |
| QQQM | 14.8 | 9.4 | 8.7 | 8.3 | 12.0 | 10.5 | 9.5 |
| QTUM | 3.0 | 3.9 | 3.6 | 3.5 | 3.0 | 3.0 | 3.0 |
| SKHY | 5.1 | 3.7 | 3.5 | 3.4 | 5.0 | 4.5 | 4.0 |
| SMH | 9.9 | 4.8 | 3.9 | 3.8 | 7.0 | 6.5 | 6.0 |
| UFO | 2.0 | 5.7 | 4.0 | 2.9 | 2.0 | 2.0 | 2.0 |
| UNI | 2.0 | 1.1 | 1.1 | 1.1 | 1.5 | 1.5 | 1.5 |
| V | 0.0 | 7.6 | 7.6 | 7.6 | 4.0 | 5.0 | 5.5 |
| VST | 5.1 | 4.4 | 2.8 | 2.1 | 5.0 | 4.5 | 4.0 |

## 3. Risk by sleeve (% of total portfolio risk) at each optimised stage
| sleeve | A | B | C |
|---|---|---|---|
| ai_tech | 30.5 | 29.2 | 29.2 |
| crypto | 33.7 | 31.5 | 31.3 |
| other_thesis | 23.6 | 27.0 | 26.4 |
| steady | 12.2 | 12.4 | 13.1 |

## 4. Stage mixes: optimised vs hand-set (covariance since the last 3 years)
| stage / mix | vol % | worst drawdown % | largest weight % | crypto share of risk % | no-sell floor binding |
|---|---|---|---|---|---|
| stage A optimised | 21.2 | -22.9 | 10.7 | 33.7 | BTC, ETH, SMH |
| stage A hand-set | 26.9 | -28.3 | 19.2 | 50.1 | - |
| stage B optimised | 21.4 | -22.0 | 10.2 | 31.5 | - |
| stage B hand-set | 26.2 | -27.0 | 16.3 | 40.6 | - |
| stage C optimised | 20.4 | -21.0 | 9.7 | 31.3 | - |
| stage C hand-set | 25.0 | -25.8 | 14.4 | 37.8 | - |

