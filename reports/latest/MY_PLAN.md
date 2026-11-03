# My plan (prices as of the latest close; EURUSD 1.119)

Book **$10,756 = EUR 9,609** (cash $1,007 ≈ EUR 900 is separate dry powder and is not touched). Money per month: EUR 1,000.
Rule: each month put the money into the (max 5) positions furthest BELOW their target. Never sell. Overweight positions just get diluted.
Re-run every month (prices change): `python scripts/monthly_plan.py --monthly-eur 1000`, then after you actually buy: add `--apply`.

## 1. What I hold now vs the target (stage A, book under EUR 20k)
| Ticker | Value EUR | Now % | Target % | Status |
|---|---|---|---|---|
| BTC | 2,117 | 22.0 | 17 | over: no buys until month ~4 |
| QQQM | 1,435 | 14.9 | 12 | over |
| SMH | 943 | 9.8 | 7 | over |
| ETH | 877 | 9.1 | 6 | over |
| SKHY | 480 | 5.0 | 5 | on target |
| NVDA | 479 | 5.0 | 5 | on target |
| VST | 472 | 4.9 | 5 | on target |
| ITA | 397 | 4.1 | 4 | on target |
| LLY | 386 | 4.0 | 4 | on target |
| NLR | 285 | 3.0 | 3 | on target |
| QTUM | 284 | 3.0 | 3 | on target |
| UNI | 196 | 2.0 | 1.5 | slightly over |
| UFO | 192 | 2.0 | 2 | on target |
| NEAR | 167 | 1.7 | 1.5 | slightly over (-14% vs cost) |
| Cash (USDT) | ~900 | 9.4 | 5 | dry powder, untouched |
New positions to open: **WORLD** (Vanguard FTSE All-World UCITS ETF Acc, ISIN IE00BK5BQT80, ticker VWCE) 8%, **V** 4%, **MA** 4%, **HOOD** 3%.

## 2. The next EUR 1,000 (month 1)
| Buy | EUR | USD | Shares |
|---|---|---|---|
| WORLD (VWCE) | 421 | 471 | 2.5131 |
| Visa (V) | 211 | 236 | 0.5538 |
| Mastercard (MA) | 211 | 236 | 0.3581 |
| HOOD | 158 | 177 | 2.1080 |

## 3. The next 12 months at EUR 1,000 (constant prices: re-run the tool each month for the real list)
| Month | Buys (EUR) |
|---|---|
| 1 | WORLD 421, V 211, MA 211, HOOD 158 |
| 2 | WORLD 390, V 195, MA 195, HOOD 146, VST 74 |
| 3 | WORLD 269, NVDA 211, SKHY 209, LLY 164, ITA 148 |
| 4 | QQQM 240, BTC 221, V 183, MA 183, VST 173 |
| 5 | QTUM 233, NLR 233, HOOD 202, BTC 180, UFO 151 |
| 6 | QQQM 268, WORLD 233, SMH 207, BTC 167, SKHY 125 |
| 7 | NVDA 226, BTC 207, ITA 193, ETH 190, LLY 183 |
| 8 | QQQM 255, VST 245, V 176, MA 176, BTC 148 |
| 9 | WORLD 258, SMH 224, BTC 185, SKHY 171, NEAR 162 |
| 10 | QQQM 281, BTC 208, ETH 196, UNI 170, HOOD 144 |
| 11 | NVDA 234, NLR 202, QTUM 201, LLY 185, BTC 178 |
| 12 | GEV 312, PICK 312, V 156, MA 156, ITA 64 |

## 4. As the book grows (EUR thresholds)
| Book reaches | New positions | When (EUR 1,000/mo, no market gains) | When (EUR 1,500/mo) |
|---|---|---|---|
| EUR 20,000 (stage B) | GE Vernova (GEV) 3% and a mining ETF (PICK) 3% | about month 11-12 | about month 7 |
| EUR 30,000 (stage C) | India (INDA) 3% and gene editing (CRSP) 2% | about month 21 | about month 14 |

Targets by stage (% of book): crypto 26 → 22 → 20; AI/semis/tech 32 → 29 → 27; other thesis names 21 → 26.5 → 31; Visa+Mastercard 8 → 10 → 11; world fund 8 → 7.5 → 6; cash 5.
After 3 years the book is about 21% crypto and 28% AI/semis/tech (vs 38% and 41% if all new money went pro rata into the 14).

## 5. HOOD: does it make sense on the numbers?
- At 3% of the book: volatility 28.3% → 28.9% (+0.6 pt), worst 20-day loss -15.2% → -16.0%, about 5% of total portfolio risk. If HOOD falls 40% the book loses 1.2%; falls 50% -1.5%; rises 60% +1.8%.
- It is the only candidate I screened that raises risk: V, MA, INDA each LOWER volatility by about 0.7 pt; HOOD adds 0.55. Correlation with your book 0.65 (V 0.20, INDA 0.34). It is 69% volatile and 43% below its 1-year high.
- Business (Q3 2026, reported 27 Oct): record revenue $1.42B (+12%), but EPS -16% to $0.51; crypto revenue $120M (-55% y/y; $94M without the new Robinhood Chain); funded customers 28.7M (+7%), Gold subscribers 5.2M (+34%); prediction-market revenue $173M (6x y/y). Management warned crypto and equity transaction revenue may face pressure in Q4.
- Verdict: the numbers do not make the case for HOOD; your conviction in the platform does. It is cheap enough to try (cost ≈ 0.6 pt of volatility, no change in the odds of EUR 1M). Keep it at 3%, buy it in tranches as the calendar does, and stop adding above 5% of the book.

Caveats: targets are my proposal (edit `data/targets.json`); history-based numbers are hindsight since 2024; assumes fills at the latest close; not financial advice.
