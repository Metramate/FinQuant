# Stress tests (book $10,738, cash $1,007 assumed flat)

## Worst 20-day windows for today's weights
- ending **2026-02-05**: -15.1% of the book. Biggest damage: BTC -6.9pt, ETH -3.9pt, UNI -0.9pt, NEAR -0.8pt
- ending **2025-03-10**: -15.0% of the book. Biggest damage: BTC -4.1pt, ETH -2.6pt, VST -1.7pt, QQQM -1.4pt
- ending **2024-08-07**: -14.0% of the book. Biggest damage: SMH -2.4pt, ETH -2.2pt, QQQM -2.0pt, SKHY -1.6pt

## Hypothetical shocks (factor betas to QQQM and BTC)
| Scenario | book_pct | usd |
|---|---|---|
| Market -10% (QQQM) | -7.1% | $-765 |
| Market -20% (QQQM) | -14.2% | $-1,530 |
| Crypto -40% (BTC) | -14.9% | $-1,597 |
| Crypto -60% (BTC) | -22.3% | $-2,396 |
| Risk-off: QQQM -15%, BTC -40% | -25.6% | $-2,745 |
| 2022-style: QQQM -30%, BTC -60% | -43.7% | $-4,691 |
| Melt-up: QQQM +15%, BTC +40% | +25.6% | $+2,745 |

Betas (each holding vs QQQM and BTC):
| Ticker | b_QQQM | b_BTC |
|---|---|---|
| BTC | -0.0 | 1.0 |
| ETH | 0.41 | 1.1 |
| UNI | 0.49 | 1.15 |
| NEAR | 0.53 | 1.33 |
| QQQM | 1.0 | -0.0 |
| SMH | 1.7 | -0.04 |
| NVDA | 1.71 | -0.02 |
| SKHY | 1.43 | 0.03 |
| VST | 1.4 | 0.03 |
| LLY | 0.28 | 0.01 |
| ITA | 0.5 | 0.03 |
| NLR | 0.94 | 0.09 |
| QTUM | 1.2 | 0.05 |
| UFO | 0.9 | 0.11 |

Floor, not ceiling: betas come from a mostly calm sample, idiosyncratic moves are ignored, and correlations rise in crashes.
