# My plan (optimised version with the world fund VT; prices as of 3 Nov 2026, EURUSD 1.12)

Book **$10,902 = EUR 9,742** (dry powder about EUR 900 is separate and untouched). Money per month: EUR 1,000.
Rule: each month put the money into the (max 5) positions furthest BELOW target. Never sell. Overweights just get diluted.
Targets come from `scripts/construct.py` (risk budgeting, caps, no-sell floors, validated out-of-sample). Policy in `data/policy.json`, full rules in `reports/latest/IPS.md`.
Monthly: `python scripts/monthly_plan.py --monthly-eur 1000`; after buying: add `--apply`.

## 1. What I hold now vs the target (book under EUR 20k)
| Ticker | Value EUR | Now % | Target % | Status |
|---|---|---|---|---|
| BTC | 2,130 | 21.9 | 10.9 | over: no buys until about month 11 |
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
New positions: **Visa (V) 7.6%, Mastercard (MA) 7.6%, world fund VT 7.6%, HOOD 2.2%**. (The world fund is back: I had cut it when I gave it a 1% risk budget; with a 5% budget the optimiser sizes it at 7.6%.)

## 2. The next EUR 1,000 (month 1)
| Buy | EUR | USD | Shares |
|---|---|---|---|
| Visa (V) | 271 | 304 | 0.7213 |
| Mastercard (MA) | 271 | 304 | 0.4690 |
| Vanguard Total World (VT) | 271 | 304 | 1.9568 |
| UFO | 107 | 120 | 2.9438 |
| HOOD | 79 | 88 | 1.0329 |
VT pays quarterly dividends. If your platform does not credit dividends on it, ask support first (message in chat); without VT this month would be about V 320, MA 320, UFO 153, HOOD 105, NLR 101.

## 3. The next 12 months at EUR 1,000 (constant prices: rerun the tool each month)
| Month | Buys (EUR) |
|---|---|
| 1 | V 271, MA 271, VT 271, UFO 107, HOOD 79 |
| 2 | V 258, MA 258, VT 258, LLY 114, UFO 111 |
| 3 | V 226, MA 226, VT 226, ITA 167, NLR 155 |
| 4 | QTUM 213, V 197, MA 197, VT 197, LLY 195 |
| 5 | UFO 251, ITA 220, HOOD 203, NLR 192, NVDA 136 |
| 6 | V 220, MA 220, VT 220, LLY 181, QTUM 160 |
| 7 | QQQM 294, SKHY 221, ITA 176, UFO 164, NLR 145 |
| 8 | V 212, MA 212, VT 212, NVDA 204, LLY 160 |
| 9 | QQQM 269, QTUM 202, VST 200, HOOD 182, ITA 147 |
| 10 | UFO 221, NLR 208, V 190, MA 190, VT 190 |
| 11 | SKHY 229, LLY 216, QQQM 204, BTC 200, NVDA 151 |
| 12 | PICK 582, GEV 336, ITA 82 |

## 4. As the book grows
| Book reaches | New positions | When at EUR 1,000/mo | At EUR 1,500/mo |
|---|---|---|---|
| EUR 20,000 | GE Vernova (GEV) and mining ETF (PICK) | about month 11-12 | about month 7 |
| EUR 30,000 | India (INDA) and gene editing (CRSP) | about month 21 | about month 14 |
After 3 years (constant prices): crypto 17% (vs 38% pro rata), AI/semis/tech 25.5% (vs 41%), other thesis 33%, Visa+Mastercard 14.5%, world fund 7.8%, 22 positions.

## 5. What the optimisation changed vs my first plan
- Out-of-sample (2021-2026): slightly lower return (25.7% vs 26.2% a year) with clearly lower risk: volatility 22.0% vs 24.8%, worst drop -30% vs -37%.
- Target mixes: volatility 24.7% / 24.2% / 23.0% (stages A/B/C) vs 30.3% today; worst drop about -22 to -24% vs -30%; crypto share of risk 30-32% vs 52% today.
- Sizes moved: BTC 10.9% (was 17), Visa/Mastercard 7.6% each (was 4), world fund 7.6% (was 8), India 5.7% (was 3), HOOD 2.2% (was 3).

## 6. HOOD
Risk-budget sizing says about 2.2% now and no more after. At 3% it adds +0.6 pt volatility and -0.8 pt to the worst 20-day loss, and is the only candidate that raises risk; Q3 2026: record revenue $1.42B, EPS -16%, crypto revenue -55% y/y, funded customers +7%, Gold subscribers +34%. A conviction bet, sized small.

Caveats: policy numbers are my proposal; history-based results are hindsight with a hindsight-picked universe; assumes fills at the latest close; not financial advice.
