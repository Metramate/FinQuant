# Portfolio manager report — 2026-11-03
Book **$10,738** (risky $9,731 + cash $1,007). Window 2024-01-02 → 2026-10-30 (710 trading days). Beta to QQQM 1.15.

_Policy: your portfolio is aggressive on purpose. A trim is recommended only if it lowers risk AND does not lower return (in-sample test of that trim + walk-forward backtest). Everything else is reported as a risk you are choosing._

## Recommendations (most important first)
1. **Trim BTC: lowers risk AND raises return in the tests**  
   BTC is 24% of capital and 31% of risk. Cutting it to ~13.9% of the book (excess spread pro-rata) moves vol 31.2% → 30.4% and return 40.2% → 41.9% (in-sample); walk-forward backtest gate: PASS. Passes your rule, but both tests share one regime (crypto lagged), so size the trim to what you are comfortable with.
2. **Trim ETH: lowers risk AND raises return in the tests**  
   ETH is 10% of capital and 18% of risk. Cutting it to ~6.4% of the book (excess spread pro-rata) moves vol 31.2% → 30.4% and return 40.2% → 41.3% (in-sample); walk-forward backtest gate: PASS. Passes your rule, but both tests share one regime (crypto lagged), so size the trim to what you are comfortable with.
3. **Optional rebalance passes your rule (~16% turnover): sell BTC $870, ETH $286, QQQM $282, SMH $231; buy LLY $519, ITA $477, UFO $276, QTUM $207, NLR $190**  
   in-sample vol 31.2% → 27.9%, return 40.2% → 41.8%. Walk-forward, net of costs, monthly: vol -2.4pt and CAGR +7.4pt vs holding the mix, in both halves. Caveat: one window where crypto lagged; do it gradually with new cash first.
4. **Crypto is 35% of your book and 57% of the risk**  
   Know this number: it is your single biggest driver of drawdowns. Capping crypto at 30% of the sleeve in the backtest changed vol -1.4pt and net CAGR +4.5pt vs holding the mix (passes your gate). UNI, NEAR are <3% each: too small to move return but they add alt-coin risk (optional tidy-up: fold into BTC/ETH, or size up on purpose).
5. **Thesis check (>20% below 1-year high): NLR -44%, SKHY -42%, ETH -42%, UFO -41%, UNI -30%, BTC -30%, VST -28%, SMH -22%, QTUM -20%**  
   A drawdown alone is not a sell signal. If the reason you bought is intact, these are candidates for new cash, not for selling.
6. **AI/semis/tech = 38% of book, 31% of risk (avg correlation 0.64): accepted concentration**  
   QQQM, SMH, NVDA, SKHY, QTUM are largely one trade (QQQM and SMH already hold NVDA/semis). No trim recommended; just know that a semis sell-off hits all five at once, and don't count them as diversification.
7. **If you add risk, the best diversifiers you already own are LLY, VST**  
   Lowest average correlation to everything else (LLY 0.09, VST 0.34).
8. **Cash 9.4% ($1,007): dry powder for new positions**  
   At 28% whole-book volatility a 10% pullback is a normal event. Deploy in tranches; new cash (e.g. your planned 2-3% HOOD) avoids selling anything. Cash earns ~4.0% at my assumed risk-free rate.

See also: [check-in & alerts](checkin.md) · [stress tests](stress.md) · [signals](signals.md) · [backtest](backtest.md) · [FinQuant optimiser](fq_optimise.md) · [watchlist](watchlist.md) · [tax lots](tax_lots.md)

## Charts
![01_allocation](01_allocation.png)
![02_performance](02_performance.png)
![03_risk_contribution](03_risk_contribution.png)
![04_correlation](04_correlation.png)
![05_risk_return_map](05_risk_return_map.png)
![06_rebalance](06_rebalance.png)
![07_what_if_HOOD](07_what_if_HOOD.png)
![08_backtest](08_backtest.png)
![09_stress](09_stress.png)
![10_signals](10_signals.png)
![11_fq_frontier](11_fq_frontier.png)
![12_fq_monte_carlo](12_fq_monte_carlo.png)
![13_plan_paths](13_plan_paths.png)
![14_construction_validation](14_construction_validation.png)

## Positions
| Ticker | theme | price | value | w_book | pnl_pct | vol | risk_share |
|---|---|---|---|---|---|---|---|
| BTC | Crypto | 76,550.21 | $2,360 | 22.0% | -1.1% | 47% | 30.5% |
| QQQM | Broad tech | 280.49 | $1,606 | 15.0% | -1.4% | 21% | 8.4% |
| SMH | Semis / AI | 508.31 | $1,056 | 9.8% | -2.7% | 38% | 9.6% |
| ETH | Crypto | 2,245.91 | $974 | 9.1% | -0.3% | 67% | 17.8% |
| SKHY | Semis / AI | 147.71 | $538 | 5.0% | -1.0% | 70% | 5.7% |
| NVDA | Semis / AI | 202.06 | $536 | 5.0% | -1.3% | 48% | 5.2% |
| VST | Power / nuclear | 134.61 | $528 | 4.9% | -2.7% | 59% | 5.3% |
| ITA | Aerospace & defense | 214.68 | $444 | 4.1% | +2.4% | 21% | 1.5% |
| LLY | Healthcare | 1,410.99 | $432 | 4.0% | -0.5% | 36% | 0.9% |
| NLR | Power / nuclear | 89.65 | $319 | 3.0% | -2.3% | 38% | 2.3% |
| QTUM | Semis / AI | 130.68 | $318 | 3.0% | -2.4% | 30% | 2.3% |
| UNI | Crypto | 7.09 | $217 | 2.0% | +0.0% | 107% | 4.6% |
| UFO | Space | 39.89 | $215 | 2.0% | -0.9% | 35% | 1.4% |
| NEAR | Crypto | 3.86 | $189 | 1.8% | -12.8% | 105% | 4.3% |

## Portfolio variants (in-sample, constant weights)
| Portfolio | ann_return | vol | sharpe | max_dd | var95_1d | cvar95_1d |
|---|---|---|---|---|---|---|
| Current | 40.2% | 31.2% | 1.16 | -31.1% | 2.94% | 4.10% |
| Min-vol | 33.3% | 20.2% | 1.45 | -20.2% | 1.99% | 2.81% |
| Max-Sharpe* | 44.7% | 21.7% | 1.88 | -20.6% | 2.05% | 2.98% |
| Risk-parity | 43.1% | 25.4% | 1.54 | -26.6% | 2.38% | 3.54% |
| Suggested target | 41.8% | 27.9% | 1.36 | -28.8% | 2.57% | 3.78% |

Out-of-sample sanity check: risk-parity weights fitted on the first half, run on the second half → vol 25.0% vs 29.0% for your current mix; max drawdown -14% vs -22%.

## Rebalance trades
| Ticker | now_book | tgt_book | trade_usd |
|---|---|---|---|
| BTC | 22.0% | 13.9% | -870 |
| ETH | 9.1% | 6.4% | -286 |
| UNI | 2.0% | 2.0% | +0 |
| NEAR | 1.8% | 1.8% | +0 |
| QQQM | 15.0% | 12.3% | -282 |
| SMH | 9.8% | 7.7% | -231 |
| NVDA | 5.0% | 5.0% | +0 |
| SKHY | 5.0% | 5.0% | +0 |
| VST | 4.9% | 4.9% | +0 |
| LLY | 4.0% | 8.9% | +519 |
| ITA | 4.1% | 8.6% | +477 |
| NLR | 3.0% | 4.7% | +190 |
| QTUM | 3.0% | 4.9% | +207 |
| UFO | 2.0% | 4.6% | +276 |

## Caveats
- In-sample history, constant weights; the window includes a strong crypto/AI bull run, which flatters returns.
- SKHY before 2026-07-10 is a proxy from the Korean listing (000660.KS → USD, scaled, shifted a day).
- Assumptions I made, not facts: risk-free 4.0%, max 20% per asset.
- Research tool, not licensed financial advice; check tax, fees and your own time horizon before trading.
