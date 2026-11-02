# Rebalance backtest (2025-01-03 → 2026-11-02, 459 days)
Costs: 10bp stocks/ETFs, 25bp crypto per side (assumptions). Net of costs.

## Full window
| Strategy | cagr | vol | sharpe | max_dd | turnover_pa |
|---|---|---|---|---|---|
| hold | 31.4% | 36.1% | 0.76 | -30.6% | 0% |
| constant_mix | 22.7% | 31.1% | 0.60 | -31.5% | 49% |
| cap_20 | 23.7% | 31.1% | 0.63 | -31.7% | 49% |
| crypto_cap_30 | 27.1% | 29.8% | 0.77 | -30.5% | 47% |
| erc_blend | 30.0% | 28.7% | 0.90 | -29.2% | 59% |

## First half
| Strategy | cagr | vol | sharpe | max_dd | turnover_pa |
|---|---|---|---|---|---|
| hold | 27.7% | 31.1% | 0.76 | -30.6% | 0% |
| constant_mix | 25.9% | 32.7% | 0.67 | -31.5% | 49% |
| cap_20 | 26.8% | 32.7% | 0.70 | -31.7% | 49% |
| crypto_cap_30 | 31.7% | 31.3% | 0.89 | -30.5% | 47% |
| erc_blend | 32.8% | 30.6% | 0.94 | -29.2% | 59% |

## Second half
| Strategy | cagr | vol | sharpe | max_dd | turnover_pa |
|---|---|---|---|---|---|
| hold | 35.3% | 40.6% | 0.77 | -25.9% | 0% |
| constant_mix | 19.6% | 29.5% | 0.53 | -18.5% | 49% |
| cap_20 | 20.6% | 29.4% | 0.57 | -18.1% | 49% |
| crypto_cap_30 | 22.6% | 28.2% | 0.66 | -16.6% | 47% |
| erc_blend | 27.2% | 26.9% | 0.86 | -16.6% | 59% |

## Gate: lower vol AND higher net CAGR than constant_mix, in full window and both halves
- **cap_20**: FAIL (full: vol -0.1pt, CAGR +1.0pt; H1: +0.0/+0.9; H2: -0.1/+1.0)
- **crypto_cap_30**: PASS (full: vol -1.3pt, CAGR +4.4pt; H1: -1.3/+5.9; H2: -1.3/+3.0)
- **erc_blend**: PASS (full: vol -2.4pt, CAGR +7.3pt; H1: -2.1/+7.0; H2: -2.7/+7.6)

Hindsight warning: the 14 names are today's holdings, same for every strategy; compare strategies, not levels.
