> **SUPERSEDED.** This file assumed a 37-year horizon (goal at age 63). Your goal is age 35-40; see `reports/latest/horizon/HORIZON.md`.

# Long-horizon research: reaching EUR 1M (today's money) by ~63

Self-test: simulator = closed-form annuity formula (EUR 588,121 for 1,000/mo, 5% real, 25y). OK.

Data: 1926-07 to 2023-09 (1167 months), real (inflation-adjusted) returns.
Plan A (your description, real euros): 1,000/mo yrs 1-5, 1,500 yrs 6-10, 2,500 yrs 11-37 = EUR 960,000 saved in total (avg 2,162/mo). Plan B (career upside): 1,000/mo for 2 yrs then 5,000/mo = EUR 2,124,000 (avg 4,784/mo).

## A. Savings math
At 5% real, 40% of the final wealth is money you put in; the market's growth is 60%. Yearly market growth first exceeds your yearly saving after about 18 years (age 44).

Share of total wealth that is today's EUR 10k book (6% real for everything): after 5 yrs 16%, after 10 yrs 8%, after 20 yrs 4%.

Years to EUR 1M (rows: EUR/month, columns: real return):
| EUR/mo | 0% | 2% | 4% | 5% | 6% | 8% | 10% |
|---|---|---|---|---|---|---|---|
| 500 | nan | nan | 50 | 44 | 39 | 33 | 28 |
| 1,000 | nan | 48 | 36 | 32 | 30 | 25 | 22 |
| 1,500 | 55 | 37 | 29 | 26 | 24 | 21 | 19 |
| 2,000 | 41 | 30 | 24 | 22 | 21 | 18 | 16 |
| 2,500 | 33 | 25 | 21 | 20 | 18 | 16 | 15 |
| 3,000 | 28 | 22 | 18 | 17 | 16 | 15 | 13 |
| 4,000 | 21 | 17 | 15 | 14 | 13 | 12 | 11 |
| 5,000 | 16 | 14 | 13 | 12 | 12 | 11 | 10 |
| 6,000 | 14 | 12 | 11 | 10 | 10 | 9 | 9 |

Check of one cell by formula (ignoring the 10k start): 2,000/mo at 5% real needs 22.7 yrs (table with the 10k: 22.3).

## B. 37-year journeys, plan A
Historical: 604 overlapping start months (1936-07 to 1986-10), at most ~2.5 independent periods. 'worst vs money put in' = lowest value of (wealth / total euros you had put in) after year 2, 10th-percentile path (0.60 = at the worst point you held 60% of what you contributed).
### Historical start months
| Strategy | P(reach 1M by 63) | median wealth at 63 | p10 wealth at 63 | p90 wealth at 63 | median age at 1M | p90 age at 1M (slow) | worst vs money put in (p10) | worst drop in final 7 yrs (p10) | saving for 80% (EUR/mo avg) |
|---|---|---|---|---|---|---|---|---|---|
| Total market | 100% | 3,494,072 | 2,492,375 | 4,949,935 | 45.0 | 52.2 | 0.55 | -54% | 710 |
| Tech sector only | 100% | 3,256,575 | 1,913,296 | 6,203,001 | 43.8 | 52.2 | 0.49 | -76% | 810 |
| Steady sectors (staples+health) | 100% | 5,720,915 | 3,224,078 | 7,905,546 | 43.1 | 50.5 | 0.55 | -57% | 484 |
| 50% tech / 50% market | 100% | 3,522,757 | 2,391,938 | 5,293,664 | 44.2 | 51.9 | 0.52 | -62% | 732 |
| Core + tech satellite (75/25) | 100% | 3,516,922 | 2,582,278 | 5,144,531 | 44.5 | 51.9 | 0.53 | -57% | 724 |
| 60% market / 40% bonds | 100% | 2,967,730 | 1,703,530 | 3,782,643 | 47.0 | 54.6 | 0.65 | -42% | 1,043 |
| Equal weight 10 industries | 100% | 4,294,561 | 2,922,673 | 5,759,810 | 44.3 | 51.3 | 0.56 | -54% | 586 |
| Walk-forward max-Sharpe (optimiser) | 100% | 2,636,766 | 1,789,668 | 3,369,648 | 45.7 | 54.5 | 0.68 | -38% | 995 |
| Walk-forward min-variance (optimiser) | 100% | 1,880,394 | 1,252,157 | 2,267,982 | 51.8 | 56.8 | 0.81 | -23% | 1,499 |
| Chase the 10-yr winner (market/tech/steady) | 100% | 2,871,804 | 2,143,905 | 4,706,478 | 43.6 | 53.6 | 0.52 | -76% | 831 |
| Glide path (100% -> 60% stocks) | 100% | 3,469,558 | 2,387,860 | 4,494,363 | 45.0 | 52.3 | 0.55 | -43% | 723 |
| Recommended mix (50 market / 30 steady / 20 tech, light de-risk late) | 100% | 4,099,235 | 2,846,280 | 5,310,844 | 44.4 | 51.3 | 0.53 | -49% | 629 |

### Block bootstrap (4000 paths, 5-year blocks)
| Strategy | P(reach 1M by 63) | median wealth at 63 | p10 wealth at 63 | p90 wealth at 63 | median age at 1M | p90 age at 1M (slow) | worst vs money put in (p10) | worst drop in final 7 yrs (p10) | saving for 80% (EUR/mo avg) |
|---|---|---|---|---|---|---|---|---|---|
| Total market | 97% | 3,782,638 | 1,527,281 | 9,444,532 | 46.0 | 52.4 | 0.38 | -55% | 1,007 |
| Tech sector only | 94% | 4,406,423 | 1,249,516 | 16,851,281 | 44.5 | 52.2 | 0.27 | -76% | 1,096 |
| Steady sectors (staples+health) | 99% | 4,913,391 | 2,008,991 | 12,247,266 | 45.4 | 51.0 | 0.51 | -54% | 751 |
| 50% tech / 50% market | 96% | 4,243,761 | 1,447,133 | 12,641,238 | 45.2 | 52.0 | 0.32 | -66% | 1,014 |
| Core + tech satellite (75/25) | 97% | 4,034,960 | 1,520,089 | 10,854,850 | 45.6 | 52.2 | 0.35 | -59% | 993 |
| 60% market / 40% bonds | 99% | 2,761,929 | 1,534,125 | 5,204,817 | 48.3 | 53.8 | 0.62 | -40% | 1,141 |
| Equal weight 10 industries | 99% | 4,374,549 | 1,840,297 | 10,277,724 | 45.7 | 51.4 | 0.42 | -54% | 842 |
| Glide path (100% -> 60% stocks) | 98% | 3,446,396 | 1,601,930 | 7,704,838 | 45.9 | 52.6 | 0.39 | -44% | 1,019 |
| Recommended mix (50 market / 30 steady / 20 tech, light de-risk late) | 98% | 4,111,613 | 1,746,326 | 9,768,846 | 45.6 | 51.7 | 0.41 | -50% | 884 |

### Bootstrap with US equity returns cut by 2 percentage points a year (the 'US was a lucky winner' case)
| Strategy | P(reach 1M by 63) | median wealth at 63 | p10 wealth at 63 | p90 wealth at 63 | median age at 1M | p90 age at 1M (slow) | worst vs money put in (p10) | worst drop in final 7 yrs (p10) | saving for 80% (EUR/mo avg) |
|---|---|---|---|---|---|---|---|---|---|
| Total market | 91% | 2,432,837 | 1,031,902 | 5,742,568 | 48.0 | 55.2 | 0.34 | -56% | 1,540 |
| Tech sector only | 87% | 2,831,935 | 868,916 | 10,031,641 | 46.0 | 54.3 | 0.24 | -76% | 1,654 |
| Steady sectors (staples+health) | 96% | 3,097,884 | 1,351,331 | 7,274,467 | 47.2 | 54.2 | 0.46 | -55% | 1,191 |
| 50% tech / 50% market | 90% | 2,710,257 | 987,026 | 7,623,797 | 47.1 | 54.8 | 0.29 | -67% | 1,545 |
| Core + tech satellite (75/25) | 91% | 2,585,496 | 1,028,337 | 6,550,211 | 47.5 | 54.8 | 0.32 | -60% | 1,523 |
| 60% market / 40% bonds | 96% | 2,090,325 | 1,204,833 | 3,760,622 | 50.2 | 56.2 | 0.59 | -40% | 1,495 |
| Equal weight 10 industries | 95% | 2,789,348 | 1,237,246 | 6,189,129 | 47.5 | 54.2 | 0.37 | -55% | 1,317 |
| Glide path (100% -> 60% stocks) | 94% | 2,324,931 | 1,155,264 | 4,912,526 | 48.0 | 55.7 | 0.35 | -45% | 1,482 |
| Recommended mix (50 market / 30 steady / 20 tech, light de-risk late) | 95% | 2,702,772 | 1,222,758 | 6,057,657 | 47.3 | 54.4 | 0.36 | -50% | 1,337 |

### Plan B (career upside), bootstrap
| Strategy | P(reach 1M by 63) | median wealth at 63 | p10 wealth at 63 | p90 wealth at 63 | median age at 1M | p90 age at 1M (slow) | worst vs money put in (p10) | worst drop in final 7 yrs (p10) | saving for 80% (EUR/mo avg) |
|---|---|---|---|---|---|---|---|---|---|
| Total market | 100% | 8,988,707 | 3,470,344 | 22,815,068 | 37.8 | 41.6 | 0.40 | -55% | 942 |
| Tech sector only | 99% | 10,581,577 | 2,831,347 | 42,378,830 | 37.2 | 41.7 | 0.28 | -76% | 1,031 |
| Steady sectors (staples+health) | 100% | 11,774,644 | 4,735,910 | 30,134,532 | 37.6 | 40.9 | 0.52 | -54% | 690 |
| 50% tech / 50% market | 100% | 10,134,884 | 3,311,984 | 31,403,248 | 37.5 | 41.6 | 0.35 | -66% | 940 |
| Core + tech satellite (75/25) | 100% | 9,623,662 | 3,495,000 | 26,526,446 | 37.7 | 41.5 | 0.37 | -58% | 930 |
| 60% market / 40% bonds | 100% | 6,326,686 | 3,498,413 | 11,673,623 | 38.9 | 41.9 | 0.64 | -40% | 1,073 |
| Equal weight 10 industries | 100% | 10,475,127 | 4,297,602 | 25,129,284 | 37.6 | 41.1 | 0.43 | -54% | 776 |
| Glide path (100% -> 60% stocks) | 100% | 8,086,897 | 3,641,382 | 18,417,780 | 37.8 | 41.6 | 0.42 | -44% | 950 |
| Recommended mix (50 market / 30 steady / 20 tech, light de-risk late) | 100% | 9,910,743 | 4,041,587 | 23,857,382 | 37.6 | 41.3 | 0.42 | -50% | 820 |

### Plan C: flat EUR 1,000/month for 37 years, no raises (total EUR 444,000). THE case where allocation matters
Historical start months:
| Strategy | P(reach 1M by 63) | median wealth at 63 | p10 wealth at 63 | median age at 1M | worst vs money put in (p10) | worst drop in final 7 yrs (p10) |
|---|---|---|---|---|---|---|
| Total market | 100% | 1,988,450 | 1,543,878 | 50.6 | 0.55 | -55% |
| Tech sector only | 92% | 1,959,923 | 1,045,293 | 46.2 | 0.49 | -76% |
| Steady sectors (staples+health) | 100% | 3,420,520 | 2,034,078 | 46.1 | 0.55 | -57% |
| 50% tech / 50% market | 100% | 2,015,741 | 1,333,963 | 47.9 | 0.52 | -62% |
| Core + tech satellite (75/25) | 100% | 2,021,864 | 1,455,911 | 49.2 | 0.53 | -58% |
| 60% market / 40% bonds | 90% | 1,595,522 | 986,389 | 55.0 | 0.65 | -44% |
| Equal weight 10 industries | 100% | 2,450,267 | 1,825,584 | 49.5 | 0.56 | -54% |
| Walk-forward max-Sharpe (optimiser) | 96% | 1,508,883 | 1,063,188 | 53.2 | 0.67 | -40% |
| Walk-forward min-variance (optimiser) | 53% | 1,017,640 | 670,664 | 60.4 | 0.80 | -29% |
| Chase the 10-yr winner (market/tech/steady) | 99% | 1,646,488 | 1,277,708 | 47.8 | 0.51 | -76% |
| Glide path (100% -> 60% stocks) | 100% | 1,955,265 | 1,470,237 | 50.6 | 0.55 | -44% |
| Recommended mix (50 market / 30 steady / 20 tech, light de-risk late) | 100% | 2,365,171 | 1,738,236 | 48.5 | 0.53 | -49% |

Block bootstrap:
| Strategy | P(reach 1M by 63) | median wealth at 63 | p10 wealth at 63 | median age at 1M | worst vs money put in (p10) | worst drop in final 7 yrs (p10) |
|---|---|---|---|---|---|---|
| Total market | 83% | 2,140,222 | 789,034 | 50.4 | 0.39 | -55% |
| Tech sector only | 80% | 2,483,976 | 645,644 | 47.9 | 0.27 | -76% |
| Steady sectors (staples+health) | 91% | 2,851,844 | 1,094,863 | 49.3 | 0.51 | -55% |
| 50% tech / 50% market | 83% | 2,383,303 | 757,075 | 49.2 | 0.33 | -66% |
| Core + tech satellite (75/25) | 84% | 2,296,033 | 786,041 | 49.8 | 0.36 | -60% |
| 60% market / 40% bonds | 79% | 1,525,586 | 786,387 | 53.9 | 0.62 | -42% |
| Equal weight 10 industries | 89% | 2,495,853 | 968,267 | 49.8 | 0.43 | -54% |
| Glide path (100% -> 60% stocks) | 83% | 1,940,862 | 818,311 | 50.2 | 0.40 | -45% |
| Recommended mix (50 market / 30 steady / 20 tech, light de-risk late) | 88% | 2,371,341 | 905,344 | 49.6 | 0.41 | -50% |

Bootstrap, US stock returns 2 points lower:
| Strategy | P(reach 1M by 63) | median wealth at 63 | p10 wealth at 63 | median age at 1M | worst vs money put in (p10) | worst drop in final 7 yrs (p10) |
|---|---|---|---|---|---|---|
| Total market | 64% | 1,295,899 | 514,038 | 53.0 | 0.34 | -57% |
| Tech sector only | 66% | 1,510,991 | 421,876 | 49.9 | 0.24 | -77% |
| Steady sectors (staples+health) | 77% | 1,697,007 | 685,313 | 52.2 | 0.46 | -56% |
| 50% tech / 50% market | 66% | 1,446,734 | 491,294 | 51.5 | 0.29 | -67% |
| Core + tech satellite (75/25) | 66% | 1,386,788 | 509,741 | 52.2 | 0.32 | -61% |
| 60% market / 40% bonds | 58% | 1,106,732 | 598,798 | 56.1 | 0.58 | -42% |
| Equal weight 10 industries | 72% | 1,498,356 | 617,885 | 52.6 | 0.37 | -55% |
| Glide path (100% -> 60% stocks) | 62% | 1,237,634 | 561,345 | 52.8 | 0.35 | -46% |
| Recommended mix (50 market / 30 steady / 20 tech, light de-risk late) | 70% | 1,453,855 | 600,675 | 52.2 | 0.36 | -51% |

## C. Walk-forward, strictly out-of-sample (weights re-estimated each year from only the previous 10 years)
| Strategy | real CAGR % | vol % | Sharpe vs bills | worst drawdown % |
|---|---|---|---|---|
| Walk-forward max-Sharpe | 4.20 | 8.80 | 0.53 | -44.54 |
| Walk-forward min-variance | 1.83 | 4.17 | 0.50 | -31.64 |
| Equal weight 10 industries (no estimation) | 7.39 | 15.17 | 0.56 | -54.27 |
| Chase the 10-yr winner | 6.04 | 18.92 | 0.42 | -80.65 |
| Total market | 6.74 | 15.89 | 0.50 | -56.29 |
| 60% market / 40% bonds | 4.83 | 10.17 | 0.53 | -41.73 |

## D. Does the winner in one era win in the other? (plan A wealth at 63; early = start months 1936-07..1961-08, late = ..1986-10)
| Strategy | median wealth, early starts | median wealth, late starts | rank early (median) | rank late (median) | p10, early | p10, late | rank early (p10) | rank late (p10) |
|---|---|---|---|---|---|---|---|---|
| Total market | 2,875,499 | 4,174,214 | 5 | 4 | 2,386,334 | 3,310,915 | 4 | 3 |
| Tech sector only | 3,118,831 | 3,553,989 | 3 | 6 | 1,711,755 | 2,585,692 | 8 | 7 |
| Steady sectors (staples+health) | 4,416,031 | 6,795,310 | 1 | 1 | 3,026,748 | 5,164,386 | 1 | 1 |
| 50% tech / 50% market | 3,031,616 | 4,066,595 | 4 | 5 | 2,282,392 | 3,096,446 | 5 | 5 |
| Core + tech satellite (75/25) | 2,846,599 | 4,224,262 | 7 | 3 | 2,501,258 | 3,245,650 | 3 | 4 |
| 60% market / 40% bonds | 2,151,703 | 3,375,825 | 9 | 7 | 1,576,981 | 2,916,021 | 9 | 6 |
| Equal weight 10 industries | 3,436,000 | 5,030,813 | 2 | 2 | 2,751,651 | 4,206,997 | 2 | 2 |
| Walk-forward max-Sharpe (optimiser) | 2,572,158 | 2,652,336 | 8 | 9 | 1,733,562 | 2,147,130 | 7 | 9 |
| Walk-forward min-variance (optimiser) | 1,639,970 | 2,090,104 | 10 | 10 | 1,134,000 | 1,820,793 | 10 | 10 |
| Chase the 10-yr winner (market/tech/steady) | 2,856,067 | 2,882,261 | 6 | 8 | 2,059,153 | 2,253,146 | 6 | 8 |
Rank correlation early vs late: median 0.78, 10th percentile 0.88 (1 = same ranking, 0 = no relation).

Tech beat the market in 57% of all 15-year windows; staples in 64%. Gap range tech: -5.8 to +7.4 pts/yr.

## E. If your income is tied to the tech cycle (AI job): saving pauses when the tech sector's last-12-months return is below -25%
In the bootstrap this applies in 9% of months (assumption, not a measurement of your career).
| Strategy | P(reach 1M by 63) | median wealth at 63 | p10 wealth at 63 | p90 wealth at 63 | median age at 1M | p90 age at 1M (slow) | worst vs money put in (p10) | worst drop in final 7 yrs (p10) | saving for 80% (EUR/mo avg) |
|---|---|---|---|---|---|---|---|---|---|
| Total market | 94% | 3,386,851 | 1,288,353 | 8,930,536 | 46.7 | 54.0 | 0.35 | -55% | 1,159 |
| Tech sector only | 91% | 3,967,681 | 1,070,930 | 15,358,556 | 45.1 | 53.4 | 0.24 | -76% | 1,273 |
| Core + tech satellite (75/25) | 94% | 3,629,365 | 1,276,900 | 10,085,926 | 46.3 | 53.8 | 0.32 | -60% | 1,143 |
| 60% market / 40% bonds | 97% | 2,488,407 | 1,325,815 | 4,862,755 | 49.3 | 55.7 | 0.58 | -41% | 1,312 |
| Steady sectors (staples+health) | 98% | 4,454,244 | 1,734,246 | 11,293,559 | 46.2 | 52.6 | 0.48 | -55% | 858 |

