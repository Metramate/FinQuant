# My plan (steady-tilted, no VT, no HOOD for now; prices 3 Nov 2026, EURUSD 1.12)

Book **$10,906 = EUR 9,740** (dry powder about EUR 900 untouched). Rule: each month put the money into the (max 5) positions furthest BELOW target. Never sell. Overweights just get diluted.
Targets come from `scripts/construct.py` (risk budgets, caps, no-sell floors); policy in `data/policy.json`; rules in `reports/latest/IPS.md`.
Monthly: `python scripts/monthly_plan.py --monthly-usd 1100` (or `--monthly-eur 1000`); after buying add `--apply`.

## 1. What I hold now vs the target (book under EUR 20k)
| Ticker | Now % | Target % | Status |
|---|---|---|---|
| BTC | 21.9 | 10.7 | over: no buys until about month 11 |
| QQQM | 14.8 | 9.4 | over |
| SMH | 9.9 | 4.8 | over |
| ETH | 9.1 | 4.4 | over |
| SKHY | 5.1 | 3.7 | over |
| NVDA | 5.1 | 4.0 | over |
| VST | 5.1 | 4.4 | over |
| ITA | 4.1 | 5.7 | under |
| LLY | 4.0 | 7.6 | under |
| NLR | 2.9 | 5.7 | under |
| QTUM | 3.0 | 3.9 | under |
| UNI | 2.0 | 1.1 | over |
| UFO | 2.0 | 5.7 | under |
| NEAR | 1.7 | 1.0 | over |
| Cash (USDT) | 9.2 | dry powder | untouched |
New positions: **Visa 7.6%, Mastercard 7.6%, Berkshire 7.6%**. Steady sleeve (Visa, Mastercard, Berkshire, Eli Lilly) = about 30% of the book.

## 2. Buy now with exactly $1,100
| Buy | USD | EUR | Shares |
|---|---|---|---|
| Visa (V) | 275 | 245 | 0.6506 |
| Mastercard (MA) | 275 | 245 | 0.4231 |
| Berkshire (BRK-B) | 275 | 245 | 0.2688 |
| Eli Lilly (LLY) | 139 | 124 | 0.0978 |
| UFO | 137 | 123 | 3.3797 |
Total about $1,100. BTC, ETH, QQQM, SMH get nothing: they are over target.

## 3. The next 12 months at about EUR 1,000/mo (constant prices: rerun the tool each month)
| Month | Buys (EUR) |
|---|---|
| 1 | V 245, MA 245, BRK-B 245, LLY 124, UFO 123 |
| 2 | V 237, MA 237, BRK-B 237, NLR 138, LLY 134 |
| 3 | V 218, MA 218, BRK-B 218, UFO 184, ITA 145 |
| 4 | LLY 219, NLR 200, V 188, MA 188, BRK-B 188 |
| 5 | UFO 239, ITA 207, QTUM 205, LLY 174, V 157 |
| 6 | MA 243, BRK-B 243, NLR 217, VST 159, UFO 119 |
| 7 | LLY 228, V 222, ITA 199, NVDA 175, QTUM 159 |
| 8 | QQQM 217, MA 216, BRK-B 216, NLR 169, SKHY 164 |
| 9 | UFO 255, VST 213, V 188, LLY 188, ITA 139 |
| 10 | QQQM 255, MA 203, BRK-B 203, NVDA 162, QTUM 159 |
| 11 | NLR 272, LLY 189, V 189, SKHY 172, BTC 160 |
| 12 | PICK 584, GEV 325, ITA 73 |

## 4. As the book grows
| Book reaches | New positions | When at EUR 1,000/mo |
|---|---|---|
| EUR 20,000 | GE Vernova (GEV) and mining ETF (PICK) | about month 11-12 |
| EUR 30,000 | India (INDA) and gene editing (CRSP) | about month 21 |
HOOD and the world fund (VT) are parked: add them later by removing them from `exclude` in `data/policy.json` and rerunning `construct.py --build`.
After 3 years (constant prices): crypto 16% (vs 38% if everything went pro rata), AI/semis/tech 23% (vs 41%), steady 31%, other thesis 28%, 21 positions.

## 5. What this does
- Risk of the target mixes (history since March 2024, hindsight): volatility 21.8% / 21.4% / 20.4% (stages A/B/C) vs 30.3% today; worst drop about -18 to -19% vs -30%; crypto share of risk 28-29% vs 52% today. Nasdaq-100 volatility is about 22%, so this is still aggressive.
- Out-of-sample (2021-2026): 25.2% a year vs 26.2% for my hand-set weights, with volatility 20.7% vs 25.2% and worst drop -28% vs -37%.
- Does steady help the odds of EUR 1M? Yes, modestly. Dial (tech sector as the thesis proxy, goal age 38, EUR 5,000/mo): chance 59% with 0% steady, 60% at 30%, 62% at 60%; at EUR 6,667/mo 78% → 82% → 85%. Bad-case wealth EUR 592k → 643k → 689k; saving needed for an 80% chance falls about EUR 380/mo at 30% steady (`reports/latest/steady_dial.md`). Crypto is not in that test.

Caveats: policy numbers are my proposal; history-based results are hindsight with a hindsight-picked universe; assumes fills at the latest close; not financial advice.
