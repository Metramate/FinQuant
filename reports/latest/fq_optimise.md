# FinQuant optimiser

| Portfolio | return | vol | sharpe | net_change_vs_current |
|---|---|---|---|---|
| Current | 38.5% | 31.1% | 1.11 | - |
| FinQuant min-vol | 24.0% | 17.3% | 1.16 | lower risk, lower return |
| FinQuant max-Sharpe | 62.3% | 30.7% | 1.90 | lower risk AND higher return |
| FinQuant same return, min risk | 38.5% | 20.5% | 1.68 | lower risk, same return |
| FinQuant same risk, max return | 63.1% | 31.1% | 1.90 | higher return, same/higher risk |
| Constrained: same risk, shrunk returns, 20% cap | 60.9% | 31.1% | 1.83 | higher return, same/higher risk |

## Weights (% of whole book; cash held constant)
| % of whole book | Current | FinQuant same risk, max return | FinQuant same return, min risk | Constrained: same risk, shrunk returns, 20% cap |
|---|---|---|---|---|
| BTC | 21.9 | 0.0 | 2.7 | 1.0 |
| ETH | 9.0 | 0.0 | 0.0 | 1.0 |
| UNI | 2.0 | 0.6 | 0.0 | 1.0 |
| NEAR | 1.8 | 0.3 | 0.0 | 1.0 |
| QQQM | 15.0 | 0.0 | 10.8 | 1.0 |
| SMH | 9.9 | 0.0 | 0.0 | 1.0 |
| NVDA | 5.0 | 17.9 | 6.5 | 20.0 |
| SKHY | 5.0 | 24.5 | 9.9 | 20.0 |
| VST | 4.9 | 7.7 | 0.6 | 11.2 |
| LLY | 4.0 | 31.3 | 21.4 | 20.0 |
| ITA | 4.1 | 4.7 | 38.8 | 3.7 |
| NLR | 3.0 | 0.0 | 0.0 | 1.0 |
| QTUM | 3.0 | 0.0 | 0.0 | 1.0 |
| UFO | 2.0 | 3.7 | 0.0 | 7.8 |

Every row above is IN-SAMPLE: the optimiser picks whatever did best in this window (here LLY, NVDA, SKHY; it drops all crypto). Treat the return gains as a ceiling made of hindsight, not a plan, including the capped row, which just hits the 20% caps.

## Honesty check: fit on the first half, run on the second half
| Out-of-sample | 2nd-half CAGR | 2nd-half vol | max_dd |
|---|---|---|---|
| Current mix | 25.1% | 28.9% | -21.7% |
| Max-Sharpe fitted on 1st half | -2.1% | 29.2% | -30.0% |
| Min-vol fitted on 1st half | 20.8% | 17.1% | -13.6% |

If the fitted portfolios do not beat the current mix out-of-sample, the in-sample 'improvement' was overfitting.
