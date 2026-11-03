# My plan (optimised version; prices as of 3 Nov 2026, EURUSD 1.119)

Book **$10,902 = EUR 9,742** (dry powder about EUR 900 is separate and untouched). Money per month: EUR 1,000.
Rule: each month put the money into the (max 5) positions furthest BELOW target. Never sell. Overweights just get diluted.
Targets come from `scripts/construct.py` (risk budgeting, caps, no-sell floors, validated out-of-sample). Policy in `data/policy.json`, full rules in `reports/latest/IPS.md`.
Monthly: `python scripts/monthly_plan.py --monthly-eur 1000`; after buying: add `--apply`.

## 1. What I hold now vs the target (book under EUR 20k)
| Ticker | Value EUR | Now % | Target % | Status |
|---|---|---|---|---|
| BTC | 2,130 | 21.9 | 12.5 | over: no buys until about month 8 |
| QQQM | 1,444 | 14.8 | 11.4 | over |
| SMH | 969 | 9.9 | 5.3 | over |
| ETH | 886 | 9.1 | 5.0 | over |
| SKHY | 498 | 5.1 | 4.6 | slightly over |
| NVDA | 495 | 5.1 | 5.0 | on target |
| VST | 487 | 5.0 | 3.8 | over |
| ITA | 400 | 4.1 | 5.7 | under |
| LLY | 391 | 4.0 | 5.7 | under |
| NLR | 289 | 3.0 | 5.2 | under |
| QTUM | 287 | 2.9 | 4.9 | under |
| UNI | 201 | 2.1 | 1.4 | over |
| UFO | 194 | 2.0 | 5.5 | under |
| NEAR | 170 | 1.7 | 1.3 | over |
| Cash (USDT) | ~900 | 9.2 | 5 | dry powder |
New positions: **Visa (V) 7.6%, Mastercard (MA) 7.6%, HOOD 2.5%**. (I dropped the world fund: after risk budgeting it came out under 2%, too small to matter.)

## 2. The next EUR 1,000 (month 1)
| Buy | EUR | USD | Shares |
|---|---|---|---|
| Visa (V) | 320 | 358 | 0.8514 |
| Mastercard (MA) | 320 | 358 | 0.5510 |
| UFO | 153 | 171 | 4.2408 |
| HOOD | 105 | 118 | 1.3944 |
| NLR | 101 | 113 | 1.2444 |
Two thirds of month 1 goes to Visa and Mastercard because they are the biggest hole in a book that is 73% crypto + AI. If that feels too boring, lower `steady` in `sleeve_max_pct` in `data/policy.json` and rerun `construct.py --build`.

## 3. The next 12 months at EUR 1,000 (constant prices: rerun the tool each month)
| Month | Buys (EUR) |
|---|---|
| 1 | V 320, MA 320, UFO 153, HOOD 105, NLR 101 |
| 2 | V 287, MA 287, UFO 147, QTUM 143, LLY 136 |
| 3 | V 234, MA 234, ITA 214, NLR 177, HOOD 142 |
| 4 | UFO 227, LLY 222, QTUM 212, V 170, MA 170 |
| 5 | NVDA 227, ITA 211, QQQM 211, NLR 185, SKHY 167 |
| 6 | V 227, MA 227, HOOD 185, LLY 183, UFO 178 |
| 7 | QQQM 304, QTUM 217, VST 182, ITA 156, NLR 142 |
| 8 | NVDA 266, SKHY 243, V 176, MA 176, BTC 138 |
| 9 | QQQM 290, LLY 222, UFO 213, ITA 144, NLR 131 |
| 10 | BTC 342, QTUM 185, ETH 172, V 151, MA 151 |
| 11 | SMH 235, QQQM 224, VST 213, NEAR 173, UNI 155 |
| 12 | PICK 602, GEV 330, ITA 68 |

## 4. As the book grows
| Book reaches | New positions | When at EUR 1,000/mo | At EUR 1,500/mo |
|---|---|---|---|
| EUR 20,000 | GE Vernova (GEV) and mining ETF (PICK) | about month 11-12 | about month 7 |
| EUR 30,000 | India (INDA) and gene editing (CRSP) | about month 21 | about month 14 |
After 3 years (constant prices): crypto 19% (vs 38% pro rata), AI/semis/tech 28.5% (vs 41%), other thesis 35%, Visa+Mastercard 15.6%, 21 positions.

## 5. What the optimisation changed vs my first plan
- Out-of-sample (2021-2026): CAGR 26.7% vs 26.2%, volatility 22.6% vs 24.8%, worst drop -30% vs -37%.
- Target mixes: volatility 24.7% / 24.2% / 23.0% (stages A/B/C) vs 30.3% today; worst drop about -22 to -24% vs -30%; crypto share of risk 30-32% vs 52% today.
- Sizes moved: BTC 12.5% (was 17), Visa/Mastercard 7.6% each (was 4), India 5.7% (was 3), HOOD 2.5% (was 3).

## 6. HOOD
Risk-budget sizing says about 2.5% now and no more after. At 3% it adds +0.6 pt volatility and -0.8 pt to the worst 20-day loss, and is the only candidate that raises risk; Q3 2026: record revenue $1.42B, EPS -16%, crypto revenue -55% y/y, funded customers +7%, Gold subscribers +34%. A conviction bet, sized small.

Caveats: policy numbers are my proposal; history-based results are hindsight with a hindsight-picked universe; assumes fills at the latest close; not financial advice.
