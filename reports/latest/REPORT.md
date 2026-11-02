# Portfolio manager report — 2026-11-02
Book **$10,896** (risky $9,889 + cash $1,007). Window 2024-01-02 → 2026-10-30 (710 trading days). Beta to QQQM 1.15.

## Recommendations (most important first)
1. **Trim BTC: 24% of capital but 30% of portfolio risk**  
   BTC's volatility is 47% a year and it is above your 20% single-asset cap. Moving to ~13.9% of the book still leaves it a core position while removing the largest single source of drawdown.
2. **Trim ETH: 10% of capital but 18% of portfolio risk**  
   ETH's volatility is 67% a year. Moving to ~6.4% of the book still leaves it a core position while removing the largest single source of drawdown.
3. **Crypto is 35% of your book but 57% of the risk**  
   Treat it as one bet (BTC/ETH/UNI/NEAR move together). UNI, NEAR are <3% each: too small to matter for return, still adding alt-coin tail risk. Either consolidate into BTC/ETH or size them up deliberately.
4. **AI/semis/tech complex = 38% of book, 31% of risk (avg pairwise correlation 0.64)**  
   QQQM, SMH, NVDA, SKHY, QTUM are largely one trade, and QQQM and SMH already hold NVDA/semis. New money should go elsewhere before this grows; do not count these as diversification.
5. **Rebalance (≈16% of book turnover): sell BTC $885, ETH $291, QQQM $285, SMH $241; buy LLY $529, ITA $493, UFO $281, QTUM $209, NLR $191**  
   Gets halfway to equal-risk weights: vol 31.3% → 27.9%, worst drawdown -31% → -29% (in-sample), cap 20% per asset. Buys are mechanical (low-risk assets get more weight): only buy what you'd want to own anyway. Check tax/fees before selling; use new cash first where possible.
6. **Review thesis (>20% below 1-year high): NLR -44%, SKHY -42%, ETH -42%, UFO -41%, UNI -30%, BTC -30%, VST -28%, SMH -22%, QTUM -20%**  
   A drawdown alone is not a sell signal. Write down why you own each; if the reason is gone, exit, otherwise this is where the cash tranches belong.
7. **Best diversifiers: LLY, VST**  
   Lowest average correlation to everything else (LLY 0.09, VST 0.34). If you add risk, add it here rather than to the AI/crypto blocks.
8. **Cash 9.2% ($1,007): keep as dry powder, deploy on weakness**  
   Portfolio vol on the whole book is ~28% a year, so a 10% pullback in the risky sleeve is a normal event, not a tail. Deploy in 3-4 tranches into the underweights in the rebalance list rather than into names already above target. Cash earns ~4.0% at my assumed risk-free rate.

## Charts
![01_allocation](01_allocation.png)
![02_performance](02_performance.png)
![03_risk_contribution](03_risk_contribution.png)
![04_correlation](04_correlation.png)
![05_risk_return_map](05_risk_return_map.png)
![06_rebalance](06_rebalance.png)

## Positions
| Ticker | theme | price | value | w_book | pnl_pct | vol | risk_share |
|---|---|---|---|---|---|---|---|
| BTC | Crypto | 77,742.21 | $2,396 | 22.0% | +0.4% | 47% | 30.4% |
| QQQM | Broad tech | 284.34 | $1,628 | 14.9% | +0.0% | 21% | 8.3% |
| SMH | Semis / AI | 522.49 | $1,085 | 10.0% | -0.0% | 38% | 9.7% |
| ETH | Crypto | 2,284.30 | $990 | 9.1% | +1.4% | 67% | 17.8% |
| SKHY | Semis / AI | 149.21 | $543 | 5.0% | +0.0% | 70% | 5.7% |
| NVDA | Semis / AI | 204.64 | $543 | 5.0% | -0.0% | 48% | 5.2% |
| VST | Power / nuclear | 138.37 | $543 | 5.0% | -0.0% | 59% | 5.4% |
| ITA | Aerospace & defense | 209.74 | $434 | 4.0% | +0.0% | 21% | 1.4% |
| LLY | Healthcare | 1,417.54 | $434 | 4.0% | -0.0% | 36% | 0.8% |
| QTUM | Semis / AI | 133.83 | $326 | 3.0% | +0.0% | 30% | 2.4% |
| NLR | Power / nuclear | 91.75 | $326 | 3.0% | -0.0% | 38% | 2.3% |
| UNI | Crypto | 7.25 | $222 | 2.0% | +2.2% | 107% | 4.6% |
| UFO | Space | 40.24 | $217 | 2.0% | -0.0% | 35% | 1.4% |
| NEAR | Crypto | 4.10 | $201 | 1.8% | -7.5% | 105% | 4.5% |

## Portfolio variants (in-sample, constant weights)
| Portfolio | ann_return | vol | sharpe | max_dd | var95_1d | cvar95_1d |
|---|---|---|---|---|---|---|
| Current | 40.2% | 31.3% | 1.16 | -31.2% | 2.95% | 4.11% |
| Min-vol | 33.3% | 20.2% | 1.45 | -20.2% | 1.99% | 2.81% |
| Max-Sharpe* | 44.7% | 21.7% | 1.88 | -20.6% | 2.05% | 2.98% |
| Risk-parity | 43.1% | 25.4% | 1.54 | -26.6% | 2.38% | 3.54% |
| Suggested target | 41.8% | 27.9% | 1.35 | -28.9% | 2.57% | 3.79% |

Out-of-sample sanity check: risk-parity weights fitted on the first half, run on the second half → vol 25.0% vs 29.1% for your current mix; max drawdown -14% vs -22%.

## Rebalance trades
| Ticker | now_book | tgt_book | trade_usd |
|---|---|---|---|
| BTC | 22.0% | 13.9% | -885 |
| ETH | 9.1% | 6.4% | -291 |
| UNI | 2.0% | 2.0% | +0 |
| NEAR | 1.8% | 1.8% | +0 |
| QQQM | 14.9% | 12.3% | -285 |
| SMH | 10.0% | 7.7% | -241 |
| NVDA | 5.0% | 5.0% | +0 |
| SKHY | 5.0% | 5.0% | +0 |
| VST | 5.0% | 5.0% | +0 |
| LLY | 4.0% | 8.8% | +529 |
| ITA | 4.0% | 8.5% | +493 |
| NLR | 3.0% | 4.7% | +191 |
| QTUM | 3.0% | 4.9% | +209 |
| UFO | 2.0% | 4.6% | +281 |

## Caveats
- In-sample history, constant weights; the window includes a strong crypto/AI bull run, which flatters returns.
- SKHY before 2026-07-10 is a proxy from the Korean listing (000660.KS → USD, scaled, shifted a day).
- Assumptions I made, not facts: risk-free 4.0%, max 20% per asset.
- Research tool, not licensed financial advice; check tax, fees and your own time horizon before trading.
