# Portfolio construction

## 1. Out-of-sample validation (2021-07-01 to 2026-11-03, monthly refit on the previous 3 years, ~21 assets available on average)
| Method | CAGR % | vol % | Sharpe | max drawdown % | worst 20d % | turnover %/yr |
|---|---|---|---|---|---|---|
| Equal weight | 25.7 | 26.3 | 0.86 | -33.1 | -18.7 | 60.0 |
| Hand-set plan weights | 26.2 | 24.8 | 0.93 | -36.6 | -17.1 | 52.1 |
| FinQuant max-Sharpe (cap 15%) | 27.9 | 20.2 | 1.23 | -23.1 | -15.5 | 109.0 |
| FinQuant min-variance (cap 15%) | 19.1 | 15.2 | 1.06 | -17.3 | -10.4 | 48.3 |
| Equal risk contribution (cap 15%) | 24.0 | 20.1 | 1.05 | -23.9 | -13.6 | 50.2 |
| Risk budgets by sleeve + position caps | 26.7 | 22.6 | 1.05 | -30.4 | -14.7 | 53.2 |

Costs: 10bp per side (25bp crypto). All methods see the same hindsight-picked universe, so compare rows against each other.
## 2. Optimised targets (% of whole book, 5% cash on top) vs my hand-set ones
| Ticker | now % | optimised A | optimised B | optimised C | hand-set A | hand-set B | hand-set C |
|---|---|---|---|---|---|---|---|
| BTC | 22.0 | 12.5 | 12.1 | 11.3 | 17.0 | 14.5 | 13.0 |
| CRSP | 0.0 | 0.0 | 0.0 | 2.3 | 0.0 | 0.0 | 2.0 |
| ETH | 9.1 | 5.0 | 4.8 | 4.5 | 6.0 | 5.0 | 4.5 |
| GEV | 0.0 | 0.0 | 2.8 | 2.2 | 0.0 | 3.0 | 3.0 |
| HOOD | 0.0 | 2.5 | 1.8 | 1.4 | 3.0 | 3.0 | 3.0 |
| INDA | 0.0 | 0.0 | 0.0 | 5.7 | 0.0 | 0.0 | 3.0 |
| ITA | 4.1 | 5.7 | 5.7 | 5.3 | 4.0 | 4.0 | 4.0 |
| LLY | 4.0 | 5.7 | 5.7 | 5.7 | 4.0 | 4.0 | 4.0 |
| MA | 0.0 | 7.6 | 7.6 | 7.6 | 4.0 | 5.0 | 5.5 |
| NEAR | 1.7 | 1.3 | 1.3 | 1.2 | 1.5 | 1.0 | 1.0 |
| NLR | 3.0 | 5.2 | 3.5 | 2.7 | 3.0 | 3.0 | 3.0 |
| NVDA | 5.0 | 5.0 | 4.7 | 4.5 | 5.0 | 4.5 | 4.5 |
| PICK | 0.0 | 0.0 | 5.1 | 3.8 | 0.0 | 3.0 | 3.0 |
| QQQM | 14.9 | 11.4 | 10.8 | 10.0 | 12.0 | 10.5 | 9.5 |
| QTUM | 3.0 | 4.9 | 4.5 | 4.3 | 3.0 | 3.0 | 3.0 |
| SKHY | 5.0 | 4.6 | 4.3 | 4.1 | 5.0 | 4.5 | 4.0 |
| SMH | 9.8 | 5.3 | 4.9 | 4.7 | 7.0 | 6.5 | 6.0 |
| UFO | 2.0 | 5.5 | 3.8 | 2.9 | 2.0 | 2.0 | 2.0 |
| UNI | 2.0 | 1.4 | 1.3 | 1.3 | 1.5 | 1.5 | 1.5 |
| V | 0.0 | 7.6 | 7.6 | 7.5 | 4.0 | 5.0 | 5.5 |
| VST | 4.9 | 3.8 | 2.7 | 2.1 | 5.0 | 4.5 | 4.0 |

## 3. Risk by sleeve (% of total portfolio risk) at each optimised stage
| sleeve | A | B | C |
|---|---|---|---|
| ai_tech | 33.2 | 32.3 | 32.1 |
| crypto | 35.9 | 34.4 | 33.9 |
| other_thesis | 26.3 | 28.5 | 28.8 |
| steady | 4.6 | 4.8 | 5.2 |

## 4. Stage mixes: optimised vs hand-set (covariance since the last 3 years)
| stage / mix | vol % | worst drawdown % | largest weight % | crypto share of risk % |
|---|---|---|---|---|
| stage A optimised | 24.0 | -25.3 | 12.5 | 35.9 |
| stage A hand-set | 27.6 | -28.3 | 18.6 | 47.0 |
| stage B optimised | 24.2 | -24.7 | 12.1 | 34.4 |
| stage B hand-set | 27.0 | -27.0 | 15.7 | 38.1 |
| stage C optimised | 23.0 | -23.4 | 11.3 | 33.9 |
| stage C hand-set | 25.8 | -25.9 | 13.9 | 35.3 |

