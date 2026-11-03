# Rebalance backtest (2025-01-03 → 2026-10-30, 458 days)
Costs: 10bp stocks/ETFs, 25bp crypto per side (assumptions). Net of costs.

## Full window
| Strategy | cagr | vol | sharpe | max_dd | turnover_pa |
|---|---|---|---|---|---|
| hold | 31.6% | 36.1% | 0.76 | -30.6% | 0% |
| constant_mix | 22.9% | 31.2% | 0.61 | -31.5% | 50% |
| cap_20 | 24.0% | 31.1% | 0.64 | -31.7% | 50% |
| crypto_cap_30 | 27.5% | 29.8% | 0.79 | -30.5% | 47% |
| erc_blend | 30.3% | 28.8% | 0.91 | -29.2% | 59% |

## First half
| Strategy | cagr | vol | sharpe | max_dd | turnover_pa |
|---|---|---|---|---|---|
| hold | 27.5% | 31.1% | 0.76 | -30.6% | 0% |
| constant_mix | 25.7% | 32.7% | 0.66 | -31.5% | 50% |
| cap_20 | 26.7% | 32.7% | 0.69 | -31.7% | 50% |
| crypto_cap_30 | 31.8% | 31.3% | 0.89 | -30.5% | 47% |
| erc_blend | 32.8% | 30.6% | 0.94 | -29.2% | 59% |

## Second half
| Strategy | cagr | vol | sharpe | max_dd | turnover_pa |
|---|---|---|---|---|---|
| hold | 35.8% | 40.6% | 0.78 | -25.8% | 0% |
| constant_mix | 20.2% | 29.6% | 0.55 | -18.6% | 50% |
| cap_20 | 21.3% | 29.5% | 0.59 | -18.2% | 50% |
| crypto_cap_30 | 23.3% | 28.3% | 0.68 | -16.6% | 47% |
| erc_blend | 27.9% | 26.9% | 0.89 | -16.6% | 59% |

## Gate: lower vol AND higher net CAGR than constant_mix, in full window and both halves
- **cap_20**: FAIL (full: vol -0.1pt, CAGR +1.0pt; H1: +0.0/+1.0; H2: -0.2/+1.1)
- **crypto_cap_30**: PASS (full: vol -1.4pt, CAGR +4.5pt; H1: -1.4/+6.0; H2: -1.4/+3.1)
- **erc_blend**: PASS (full: vol -2.4pt, CAGR +7.4pt; H1: -2.1/+7.0; H2: -2.7/+7.7)

Hindsight warning: the 14 names are today's holdings, same for every strategy; compare strategies, not levels.
