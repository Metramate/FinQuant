# FinQuant optimiser

| Portfolio | return | vol | sharpe | net_change_vs_current |
|---|---|---|---|---|
| Current | 38.6% | 31.2% | 1.11 | - |
| FinQuant min-vol | 23.8% | 17.3% | 1.14 | lower risk, lower return |
| FinQuant max-Sharpe | 64.3% | 31.7% | 1.91 | higher return, same/higher risk |
| FinQuant same return, min risk | 38.6% | 20.6% | 1.68 | lower risk, same return |
| FinQuant same risk, max return | 63.4% | 31.2% | 1.91 | higher return, same/higher risk |
| Constrained: same risk, shrunk returns, 20% cap | 61.2% | 31.2% | 1.83 | higher return, same/higher risk |

## Weights (% of whole book; cash held constant)
| % of whole book | Current | FinQuant same risk, max return | FinQuant same return, min risk | Constrained: same risk, shrunk returns, 20% cap |
|---|---|---|---|---|
| BTC | 22.0 | 0.0 | 2.9 | 1.0 |
| ETH | 9.1 | 0.0 | 0.0 | 1.0 |
| UNI | 2.0 | 0.3 | 0.0 | 1.0 |
| NEAR | 1.8 | 0.9 | 0.0 | 1.0 |
| QQQM | 15.0 | 0.0 | 11.2 | 1.0 |
| SMH | 9.8 | 0.0 | 0.0 | 1.0 |
| NVDA | 5.0 | 17.4 | 6.4 | 20.0 |
| SKHY | 5.0 | 24.1 | 10.0 | 20.0 |
| VST | 4.9 | 8.1 | 1.0 | 11.2 |
| LLY | 4.0 | 32.4 | 21.8 | 20.0 |
| ITA | 4.1 | 3.0 | 37.2 | 3.4 |
| NLR | 3.0 | 0.0 | 0.0 | 1.0 |
| QTUM | 3.0 | 0.0 | 0.0 | 1.0 |
| UFO | 2.0 | 4.4 | 0.0 | 8.0 |

Every row above is IN-SAMPLE: the optimiser picks whatever did best in this window (here LLY, NVDA, SKHY; it drops all crypto). Treat the return gains as a ceiling made of hindsight, not a plan, including the capped row, which just hits the 20% caps.

## Honesty check: fit on the first half, run on the second half
| Out-of-sample | 2nd-half CAGR | 2nd-half vol | max_dd |
|---|---|---|---|
| Current mix | 25.4% | 29.0% | -21.9% |
| Max-Sharpe fitted on 1st half | -1.7% | 29.2% | -30.0% |
| Min-vol fitted on 1st half | 19.8% | 17.1% | -13.6% |

If the fitted portfolios do not beat the current mix out-of-sample, the in-sample 'improvement' was overfitting.
