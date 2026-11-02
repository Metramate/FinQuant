# Glass cannon vs steady compounders

## 1. Facts (2016 on, dividends included; book proxy since 2020-10-14)
| Asset | cagr | vol | maxdd | underwater_yrs | worst_year | pos_years |
|---|---|---|---|---|---|---|
| Visa | 17.9 | 24.3 | -36.4 | 2.1 | -3.4 | 81.8 |
| Mastercard | 20.1 | 26.6 | -41.0 | 1.4 | -2.7 | 90.9 |
| Steady basket (8 stocks) | 18.7 | 18.7 | -33.6 | 1.5 | -9.9 | 90.9 |
| S&P 500 | 14.7 | 17.7 | -33.7 | 1.9 | -18.2 | 81.8 |
| Nasdaq-100 (QQQ) | 19.0 | 22.2 | -35.1 | 2.0 | -32.6 | 81.8 |
| Semis (SMH) | 32.5 | 33.0 | -45.3 | 1.5 | -33.5 | 81.8 |
| Bitcoin | 61.5 | 65.3 | -83.0 | 2.9 | -74.5 | 63.6 |
| ARKK (innovation ETF) | 14.2 | 39.8 | -80.9 | 5.7 | -67.0 | 72.7 |
| PayPal | 4.7 | 38.7 | -87.3 | 5.3 | -62.2 | 63.6 |
| Intel | 7.6 | 45.8 | -70.8 | 5.0 | -59.6 | 72.7 |
| Kraft Heinz | -5.2 | 27.0 | -76.1 | 9.7 | -42.2 | 45.5 |
| 3M | 6.6 | 26.2 | -59.1 | 7.7 | -29.6 | 63.6 |
| YOUR book (proxy, since 2020-10-14) | 42.8 | 32.7 | -48.3 | 2.1 | -41.5 | 85.7 |

Visa / Mastercard since 2021: 12.9% / 11.8% a year (vs 18% / 20% since 2016). 'About 20%' depended on the start date.

Since 2020-10-14: your-book proxy 43%/yr, vol 33%, worst fall -48%, longest time under water 2.1 yrs; steady basket 15%/yr, vol 17%, worst fall -20%, underwater 1.5 yrs.

## 2. Rolling 4-year holds (annualised %)
| Asset | worst | p10 | median | p90 | best | pct_neg | n_start_days | from |
|---|---|---|---|---|---|---|---|---|
| Steady basket | 8.2 | 14.0 | 21.4 | 26.8 | 31.4 | 0.0 | 3225 | 2010-01-05 |
| S&P 500 | 4.2 | 10.6 | 13.3 | 17.5 | 25.4 | 0.0 | 3225 | 2010-01-05 |
| Nasdaq-100 | 6.5 | 13.4 | 18.1 | 25.8 | 30.1 | 0.0 | 3225 | 2010-01-05 |
| Semis (SMH) | 9.0 | 14.5 | 24.5 | 34.6 | 61.6 | 0.0 | 3225 | 2010-01-05 |
| ARKK | -23.7 | -13.5 | 8.5 | 44.5 | 65.0 | 39.2 | 2009 | 2014-11-03 |
| Bitcoin | 6.6 | 20.7 | 54.9 | 134.7 | 176.9 | 0.0 | 2041 | 2014-09-18 |
| YOUR book (proxy) | 17.5 | 25.2 | 32.5 | 50.3 | 54.3 | 0.0 | 512 | 2020-10-14 |

Head to head on identical start dates since 2020-10-14: your-book proxy beat the steady basket in 100% of 512 overlapping 4-year windows (median gap +19.4pt/yr; worst gap +3.8pt). These windows overlap heavily: effectively ~1-2 independent samples.

## 3. Simulation: 4-year paths for ~EUR 1,000 (= $1,119 at EURUSD 1.119) added to a $10,817 book
Bootstrap of real joint daily returns (21-day blocks, 4000 paths, sample 2021-07-30 to 2026-11-02 (1321 days)). Start value $11,936. 'History' replays what 2021-26 delivered to today's holdings (hindsight-flattered: book 30%/yr, steady 13%/yr, HOOD 43%/yr average). 'Sober' keeps the same crash shapes but ASSUMES average returns of 15% (book), 12% (steady), 15% (HOOD): my assumptions.

### History replay
| Scenario | median_end | p10_end | p90_end | P(end<start) | median_maxdd | P(beats D) |
|---|---|---|---|---|---|---|
| Do nothing (new money sits in cash) | 29,491 | 14,387 | 61,767 | 5% | -32% | 22% |
| A. More of the same (glass cannon) | 31,258 | 14,431 | 67,216 | 5% | -34% | 87% |
| B. HOOD 2.5% + rest more of the same | 31,397 | 14,304 | 68,173 | 6% | -35% | 82% |
| C. HOOD 2.5% + rest steady compounders | 30,424 | 14,395 | 64,987 | 5% | -33% | 56% |
| D. All new money into steady compounders | 29,873 | 14,513 | 62,773 | 5% | -32% | 0% |

### Sober case
| Scenario | median_end | p10_end | p90_end | P(end<start) | median_maxdd | P(beats D) |
|---|---|---|---|---|---|---|
| Do nothing (new money sits in cash) | 17,200 | 8,970 | 34,797 | 25% | -37% | 27% |
| A. More of the same (glass cannon) | 17,565 | 8,395 | 37,169 | 26% | -40% | 53% |
| B. HOOD 2.5% + rest more of the same | 17,406 | 8,276 | 37,043 | 26% | -41% | 44% |
| C. HOOD 2.5% + rest steady compounders | 17,434 | 8,760 | 35,834 | 25% | -39% | 24% |
| D. All new money into steady compounders | 17,501 | 9,031 | 35,676 | 23% | -38% | 0% |

## 4. What you must believe
Swingy sleeve vol 32%, steady 17%, correlation 0.42. Volatility drag: to merely TIE a steady 14%/yr sleeve, the swingy one must average ~18%/yr (arithmetic) i.e. +4pt, before it is ahead. Table of P(swingy wins), rows = years, columns = believed yearly return:
| hold | 8% | 10% | 12% | 14% | 16% | 18% | 20% | 22% | 24% | 26% | 28% | 30% | 32% | 34% |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1y | 37.0 | 40.0 | 42.0 | 46.0 | 48.0 | 51.0 | 55.0 | 57.0 | 61.0 | 64.0 | 66.0 | 70.0 | 72.0 | 75.0 |
| 2y | 32.0 | 36.0 | 40.0 | 44.0 | 48.0 | 52.0 | 57.0 | 61.0 | 65.0 | 69.0 | 73.0 | 76.0 | 79.0 | 83.0 |
| 4y | 26.0 | 31.0 | 37.0 | 41.0 | 48.0 | 53.0 | 60.0 | 65.0 | 70.0 | 76.0 | 80.0 | 84.0 | 88.0 | 91.0 |
| 8y | 18.0 | 24.0 | 31.0 | 38.0 | 46.0 | 55.0 | 63.0 | 71.0 | 78.0 | 84.0 | 88.0 | 92.0 | 95.0 | 97.0 |
| 15y | 10.0 | 16.0 | 24.0 | 33.0 | 45.0 | 56.0 | 67.0 | 77.0 | 85.0 | 91.0 | 95.0 | 98.0 | 99.0 | 99.0 |

## EUR note
EURUSD now 1.119. Over rolling 4-year periods since 2010 the euro moved between -29% and +13% against the dollar: as a euro investor in dollar assets you carry that on top: if the euro rises 13% against the dollar, the same dollar holdings are worth about 12% less in euros; if it falls 29%, they are worth about 41% more.
