# Investment Policy Statement (personal, age 26)

Written down so decisions are made by rules, not by mood. Numbers come from `scripts/construct.py`, `monthly_plan.py`, `horizon.py` and `data/policy.json`. Everything in **bold** is a policy choice I proposed; change it in `data/policy.json` and re-run.

## 1. Objective
- Hold about **EUR 1,000,000 in today's money, liquid, between age 35 and 40 (target 38)**.
- Savings do most of the work: at 5% real growth you need about EUR 5,500/month (EUR 66k/yr) after the job starts to hit it at 38, about EUR 4,400/month at 40. Investing decisions change the odds by a few points, not the outcome.
- Style: **aggressive growth**. This is a choice, not a mistake: the plan is about 80% thesis names after 3 years, with portfolio volatility of about 23-25% (Nasdaq-100 is about 22%).

## 2. Constraints
- **Liquid, listed assets only.** No private-market funds or ELTIFs (illiquid, about 3.4% all-in costs, smoothed risk).
- Income is correlated with the tech cycle (AI job). **Emergency fund of 6-12 months of expenses sits OUTSIDE the book** and does not count toward the EUR 1M.
- Savings continue in every market. A pause costs more than any allocation choice (tested: -7 to -12 points of success probability).
- Currency: EUR investor holding USD assets (EUR/USD moved between -29% and +13% over 4-year periods since 2010). Not hedged.
- Tax: unknown country. Sells are avoided by design; check local rules before any sale.

## 3. Risk policy
- Accepts drawdowns of 40-50% in the worst cases (e.g. a dot-com-style shock hits the plan for about -53 to -57% of the book; the old pro-rata approach about -62%).
- **Sleeve risk budgets** (share of total portfolio risk): crypto 33%, AI/semis/tech 31%, other thesis 30%, steady compounders 5%, world fund 1% (excluded).
- **Position caps** (max % of invested money in one holding): crypto 15, AI/tech 12, other thesis 6, steady 8; **no-sell floors** override a cap.
- **Sleeve ranges (% of whole book):** crypto 10-22 (hard max 25), AI/semis/tech 20-32, other thesis 25-40, steady 10-18, cash 2-8. HOOD max 4%.
- Today's book is outside the ranges (crypto 35%, AI/tech 38%, no steady names). It is brought inside by new money only.

## 4. How the weights are built (and why I trust it only this far)
- Method: risk budgeting by sleeve, Ledoit-Wolf shrunk covariance (last 3 years), position caps, no-sell floors, solved per stage (book under EUR 20k, 20-30k, over 30k).
- Out-of-sample test (2021-07 to 2026-11, monthly refit using only the previous 3 years, costs included):

| Method | CAGR | Vol | Sharpe | Worst drop |
|---|---|---|---|---|
| Hand-set weights (my first plan) | 27.4% | 25.6% | 0.95 | -37.3% |
| **Risk budgets + caps (used)** | 27.0% | 22.7% | 1.06 | -30.3% |
| Equal risk contribution | 25.0% | 20.4% | 1.08 | -23.7% |
| FinQuant max-Sharpe (cap 15%) | 28.3% | 20.5% | 1.23 | -24.2% |
| Equal weight | 26.5% | 27.0% | 0.87 | -33.5% |

- Max-Sharpe scores best but is **not used**: the 22 names were picked with hindsight (winners), which flatters any method that chases recent winners, it trades about twice as much (99% a year), and in my 100-year test optimisers lost to simple rules. Risk-based construction kept about the same return as my hand-set weights with clearly lower risk (volatility -2.9 pts, worst drop -7 pts); an earlier run showed the same pattern for lookbacks of 504, 756 and 1008 days.
- Limits: one AI/crypto boom plus the 2022 bear; 22 hindsight-picked names; covariance is estimated; risk budgets are my policy choices.

## 5. Implementation rules
- Each month: `python scripts/monthly_plan.py --monthly-eur 1000` (use 1500 if you can). Put the money into the (max 5) positions furthest under target, minimum about EUR 60 per buy. Never sell.
- After buying: rerun with `--apply` so the holdings file stays true (backup kept).
- **Stages:** book under EUR 20k (17 positions), EUR 20-30k adds GE Vernova and a mining ETF (19), over EUR 30k adds India and gene editing (21).
- HOOD: about 2.5% now, no further adds after it reaches 4%. Lottery positions (IONQ-type, single gene-editing names) at most 2%.

## 6. Rebalancing
- New money only. Overweight positions (BTC 22%, SMH 9.9%, ETH 9.1%, QQQM 14.8% today) are diluted, not sold.
- If a sleeve is above its maximum for 2 months in a row, redirect new money away from it.
- Sell only for a written thesis break or a real emergency, never for a price move.

## 7. Drawdown protocol (decide now, not in the crash)
- Down 20% from the book's peak: do nothing, keep saving.
- Down 35%: reread the thesis for each of the 5 largest positions; write one line on why it still holds.
- Down 50%: do not sell for portfolio reasons. Optional pre-commitment: deploy the dry powder (about EUR 900) in 3 equal tranches at -25%, -35%, -45%.

## 8. De-risking
- Hold the plan until **4 years before the target date**, then move new money into bonds/cash-like assets, reaching about 25-30% by the goal date (tested: cuts the final-3-year bad-case drop from -42% to about -31%, costs about 2 points of success probability).

## 9. Monitoring
- Monthly: `monthly_plan.py`. Quarterly: `checkin.py` (alerts in `data/pm_rules.json`). Yearly (or after a job change): `python scripts/run_all.py`, then rerun `construct.py --validate --build`.
- Review triggers: job or income change, goal date change, book crossing EUR 20k / 30k, a written thesis break.

## 10. What I can and cannot tell you
- All results use history since 2024 for the actual names (and a century of US data for the allocation research). They describe the past, not the future.
- Valuation of individual stocks is not modelled (Yahoo's fundamentals are not reachable from here).
- Not financial advice.
