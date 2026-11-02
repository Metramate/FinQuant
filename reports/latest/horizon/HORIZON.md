# Reaching EUR 1M (today's money) by age 35-40, starting at 26

Self-test OK (simulator = closed form: EUR 196,140).

Data 1926-07..2023-09 (1167 months, real returns). Savings: EUR 1,000/mo until month 12, then S per month (S varied). Goal ages [35, 38, 40] = [9, 12, 14] years.

## 1. The math (no simulation): EUR per month you must save AFTER the job starts to hold EUR 1M at the goal age
| goal age | 0% real | 3% real | 5% real | 7% real | 10% real |
|---|---|---|---|---|---|
| 35 | 10,187 | 8,959 | 8,212 | 7,517 | 6,567 |
| 36 | 9,056 | 7,835 | 7,099 | 6,420 | 5,501 |
| 37 | 8,150 | 6,937 | 6,212 | 5,549 | 4,659 |
| 38 | 7,409 | 6,204 | 5,489 | 4,841 | 3,981 |
| 39 | 6,792 | 5,593 | 4,889 | 4,256 | 3,425 |
| 40 | 6,269 | 5,077 | 4,384 | 3,765 | 2,963 |
Read: to hold EUR 1M at 38 with 5% real growth you must save about EUR 5,489/mo (= EUR 65,871/yr) from month 12.

At that saving level, 75% of the EUR 1M is money you put in; only 25% is market growth (5% real).

## 2. Journeys: chance of EUR 1M at the goal age (S = EUR saved per month after the job; 3,000 / 5,000 / 6,667 = EUR 80k a year)
### Goal age 35 - Historical start months (about 6-10 independent periods)
| Strategy | P(success) S=5,000 | P(success) S=6,667 | P(success) S=3,000 | median wealth S=5,000 | p10 wealth S=5,000 | saving needed 80% (EUR/mo) | saving needed 90% (EUR/mo) |
|---|---|---|---|---|---|---|---|
| Total market | 9% | 43% | 0% | 739,941 | 491,774 | 9,235 | 10,462 |
| Tech sector only | 23% | 45% | 3% | 708,560 | 456,348 | 9,905 | 11,231 |
| Steady sectors (staples+health) | 15% | 48% | 0% | 751,862 | 514,079 | 8,781 | 9,884 |
| 50% tech / 50% market | 17% | 43% | 1% | 719,306 | 490,153 | 9,530 | 10,485 |
| Core + tech satellite (75/25) | 13% | 43% | 0% | 729,033 | 494,577 | 9,331 | 10,365 |
| 60% market / 40% bonds | 0% | 19% | 0% | 656,116 | 485,384 | 9,502 | 10,506 |
| Equal weight 10 industries | 11% | 46% | 0% | 750,042 | 509,216 | 8,721 | 10,016 |
| T-bills only (safe) | 0% | 0% | 0% | 526,629 | 463,761 | 10,700 | 11,273 |
| 10-yr bonds only | 0% | 3% | 0% | 555,035 | 447,379 | 10,885 | 11,525 |
| Walk-forward max-Sharpe (optimiser) | 5% | 26% | 0% | 612,347 | 436,273 | 9,956 | 11,756 |
| Walk-forward min-variance (optimiser) | 0% | 2% | 0% | 572,095 | 468,273 | 10,464 | 11,034 |
| Chase the 10-yr winner | 17% | 46% | 0% | 720,550 | 411,235 | 10,663 | 12,457 |
| Recommended mix | 9% | 44% | 0% | 732,831 | 507,623 | 9,085 | 10,069 |
| Glide path (100% -> 70% stocks, last 4 yrs) | 6% | 36% | 0% | 714,990 | 497,605 | 9,263 | 10,273 |

### Goal age 35 - Block bootstrap
| Strategy | P(success) S=5,000 | P(success) S=6,667 | P(success) S=3,000 | median wealth S=5,000 | p10 wealth S=5,000 | saving needed 80% (EUR/mo) | saving needed 90% (EUR/mo) |
|---|---|---|---|---|---|---|---|
| Total market | 10% | 39% | 0% | 705,279 | 453,735 | 9,575 | 11,364 |
| Tech sector only | 24% | 47% | 4% | 736,733 | 408,802 | 10,098 | 12,544 |
| Steady sectors (staples+health) | 14% | 42% | 1% | 718,138 | 491,537 | 9,032 | 10,482 |
| 50% tech / 50% market | 18% | 44% | 1% | 725,026 | 436,774 | 9,717 | 11,783 |
| Core + tech satellite (75/25) | 14% | 42% | 1% | 717,308 | 446,740 | 9,589 | 11,448 |
| 60% market / 40% bonds | 2% | 20% | 0% | 648,294 | 483,103 | 9,557 | 10,603 |
| Equal weight 10 industries | 11% | 43% | 0% | 727,647 | 479,093 | 9,161 | 10,758 |
| T-bills only (safe) | 0% | 0% | 0% | 522,579 | 466,067 | 10,583 | 11,089 |
| 10-yr bonds only | 0% | 2% | 0% | 563,501 | 458,662 | 10,470 | 11,324 |
| Recommended mix | 9% | 38% | 0% | 707,052 | 480,312 | 9,332 | 10,665 |
| Glide path (100% -> 70% stocks, last 4 yrs) | 7% | 34% | 0% | 688,240 | 468,306 | 9,513 | 10,946 |

### Goal age 35 - Bootstrap with US stock returns 2 points lower
| Strategy | P(success) S=5,000 | P(success) S=6,667 | P(success) S=3,000 | median wealth S=5,000 | p10 wealth S=5,000 | saving needed 80% (EUR/mo) | saving needed 90% (EUR/mo) |
|---|---|---|---|---|---|---|---|
| Total market | 5% | 27% | 0% | 643,182 | 416,595 | 10,431 | 12,310 |
| Tech sector only | 18% | 38% | 3% | 670,582 | 379,056 | 10,989 | 13,547 |
| Steady sectors (staples+health) | 8% | 30% | 0% | 654,682 | 451,384 | 9,864 | 11,411 |
| 50% tech / 50% market | 11% | 33% | 1% | 660,402 | 402,082 | 10,597 | 12,826 |
| Core + tech satellite (75/25) | 8% | 31% | 0% | 652,777 | 411,605 | 10,471 | 12,453 |
| 60% market / 40% bonds | 1% | 13% | 0% | 612,367 | 458,667 | 10,093 | 11,172 |
| Equal weight 10 industries | 5% | 29% | 0% | 663,264 | 439,275 | 9,987 | 11,708 |
| T-bills only (safe) | 0% | 0% | 0% | 518,523 | 463,293 | 10,627 | 11,127 |
| 10-yr bonds only | 0% | 2% | 0% | 559,040 | 455,285 | 10,511 | 11,357 |
| Recommended mix | 4% | 27% | 0% | 650,478 | 446,220 | 10,077 | 11,493 |
| Glide path (100% -> 70% stocks, last 4 yrs) | 3% | 23% | 0% | 633,419 | 435,706 | 10,266 | 11,768 |

### Goal age 38 - Historical start months (about 6-10 independent periods)
| Strategy | P(success) S=5,000 | P(success) S=6,667 | P(success) S=3,000 | median wealth S=5,000 | p10 wealth S=5,000 | saving needed 80% (EUR/mo) | saving needed 90% (EUR/mo) |
|---|---|---|---|---|---|---|---|
| Total market | 63% | 85% | 13% | 1,154,791 | 662,622 | 6,173 | 7,624 |
| Tech sector only | 54% | 79% | 28% | 1,053,673 | 640,945 | 6,690 | 7,896 |
| Steady sectors (staples+health) | 69% | 87% | 22% | 1,209,923 | 693,914 | 5,613 | 7,284 |
| 50% tech / 50% market | 61% | 84% | 18% | 1,091,573 | 654,922 | 6,232 | 7,727 |
| Core + tech satellite (75/25) | 63% | 85% | 16% | 1,137,349 | 654,868 | 6,193 | 7,715 |
| 60% market / 40% bonds | 48% | 82% | 0% | 989,599 | 655,865 | 6,401 | 7,720 |
| Equal weight 10 industries | 69% | 86% | 10% | 1,185,268 | 684,923 | 5,759 | 7,371 |
| T-bills only (safe) | 0% | 38% | 0% | 719,801 | 630,029 | 7,810 | 8,090 |
| 10-yr bonds only | 13% | 56% | 0% | 787,624 | 598,375 | 7,795 | 8,540 |
| Walk-forward max-Sharpe (optimiser) | 41% | 77% | 5% | 864,739 | 606,545 | 6,925 | 8,324 |
| Walk-forward min-variance (optimiser) | 11% | 67% | 0% | 807,497 | 625,383 | 7,500 | 8,122 |
| Chase the 10-yr winner | 58% | 72% | 18% | 1,168,749 | 570,563 | 8,060 | 8,978 |
| Recommended mix | 65% | 85% | 9% | 1,148,652 | 660,911 | 6,026 | 7,636 |
| Glide path (100% -> 70% stocks, last 4 yrs) | 62% | 84% | 7% | 1,109,523 | 661,320 | 6,140 | 7,638 |

### Goal age 38 - Block bootstrap
| Strategy | P(success) S=5,000 | P(success) S=6,667 | P(success) S=3,000 | median wealth S=5,000 | p10 wealth S=5,000 | saving needed 80% (EUR/mo) | saving needed 90% (EUR/mo) |
|---|---|---|---|---|---|---|---|
| Total market | 59% | 84% | 13% | 1,085,920 | 655,467 | 6,309 | 7,756 |
| Tech sector only | 61% | 80% | 26% | 1,144,578 | 587,166 | 6,722 | 8,650 |
| Steady sectors (staples+health) | 63% | 87% | 16% | 1,125,246 | 721,974 | 5,978 | 7,011 |
| 50% tech / 50% market | 62% | 82% | 20% | 1,121,851 | 635,216 | 6,402 | 7,952 |
| Core + tech satellite (75/25) | 61% | 83% | 16% | 1,104,812 | 650,763 | 6,316 | 7,779 |
| 60% market / 40% bonds | 44% | 83% | 2% | 961,889 | 696,544 | 6,426 | 7,258 |
| Equal weight 10 industries | 64% | 87% | 14% | 1,124,033 | 703,441 | 6,005 | 7,206 |
| T-bills only (safe) | 0% | 25% | 0% | 714,494 | 628,173 | 7,732 | 8,134 |
| 10-yr bonds only | 9% | 58% | 0% | 788,442 | 629,087 | 7,484 | 8,124 |
| Recommended mix | 61% | 86% | 12% | 1,086,592 | 694,121 | 6,123 | 7,292 |
| Glide path (100% -> 70% stocks, last 4 yrs) | 57% | 84% | 10% | 1,054,007 | 680,036 | 6,314 | 7,440 |

### Goal age 38 - Bootstrap with US stock returns 2 points lower
| Strategy | P(success) S=5,000 | P(success) S=6,667 | P(success) S=3,000 | median wealth S=5,000 | p10 wealth S=5,000 | saving needed 80% (EUR/mo) | saving needed 90% (EUR/mo) |
|---|---|---|---|---|---|---|---|
| Total market | 44% | 75% | 6% | 954,190 | 584,179 | 7,136 | 8,685 |
| Tech sector only | 50% | 73% | 18% | 1,006,870 | 528,057 | 7,542 | 9,618 |
| Steady sectors (staples+health) | 48% | 79% | 8% | 987,556 | 643,072 | 6,790 | 7,883 |
| 50% tech / 50% market | 49% | 75% | 11% | 985,846 | 569,534 | 7,223 | 8,869 |
| Core + tech satellite (75/25) | 47% | 75% | 9% | 971,780 | 582,150 | 7,126 | 8,731 |
| 60% market / 40% bonds | 30% | 75% | 1% | 889,812 | 648,139 | 6,927 | 7,804 |
| Equal weight 10 industries | 48% | 78% | 6% | 986,374 | 626,201 | 6,793 | 8,115 |
| T-bills only (safe) | 0% | 22% | 0% | 707,368 | 622,268 | 7,769 | 8,182 |
| 10-yr bonds only | 9% | 56% | 0% | 780,690 | 623,890 | 7,529 | 8,184 |
| Recommended mix | 46% | 77% | 5% | 966,293 | 625,705 | 6,852 | 8,082 |
| Glide path (100% -> 70% stocks, last 4 yrs) | 42% | 75% | 4% | 937,539 | 611,774 | 7,059 | 8,277 |

### Goal age 40 - Historical start months (about 6-10 independent periods)
| Strategy | P(success) S=5,000 | P(success) S=6,667 | P(success) S=3,000 | median wealth S=5,000 | p10 wealth S=5,000 | saving needed 80% (EUR/mo) | saving needed 90% (EUR/mo) |
|---|---|---|---|---|---|---|---|
| Total market | 80% | 92% | 38% | 1,496,549 | 783,950 | 5,011 | 6,439 |
| Tech sector only | 76% | 91% | 40% | 1,340,645 | 763,822 | 5,247 | 6,613 |
| Steady sectors (staples+health) | 85% | 94% | 47% | 1,575,951 | 821,887 | 4,355 | 6,113 |
| 50% tech / 50% market | 81% | 92% | 40% | 1,380,545 | 776,514 | 4,939 | 6,468 |
| Core + tech satellite (75/25) | 81% | 93% | 38% | 1,455,384 | 782,874 | 4,939 | 6,446 |
| 60% market / 40% bonds | 78% | 92% | 9% | 1,247,424 | 775,451 | 5,086 | 6,500 |
| Equal weight 10 industries | 84% | 96% | 43% | 1,513,527 | 817,953 | 4,482 | 6,157 |
| T-bills only (safe) | 1% | 85% | 0% | 860,990 | 745,462 | 6,617 | 6,782 |
| 10-yr bonds only | 39% | 83% | 0% | 949,376 | 708,709 | 6,478 | 7,162 |
| Walk-forward max-Sharpe (optimiser) | 65% | 90% | 22% | 1,056,532 | 752,784 | 5,482 | 6,681 |
| Walk-forward min-variance (optimiser) | 44% | 88% | 0% | 976,308 | 744,313 | 6,033 | 6,783 |
| Chase the 10-yr winner | 68% | 82% | 42% | 1,484,447 | 676,605 | 6,495 | 7,459 |
| Recommended mix | 83% | 93% | 41% | 1,511,824 | 788,221 | 4,669 | 6,409 |
| Glide path (100% -> 70% stocks, last 4 yrs) | 80% | 92% | 36% | 1,444,172 | 777,277 | 4,926 | 6,478 |

### Goal age 40 - Block bootstrap
| Strategy | P(success) S=5,000 | P(success) S=6,667 | P(success) S=3,000 | median wealth S=5,000 | p10 wealth S=5,000 | saving needed 80% (EUR/mo) | saving needed 90% (EUR/mo) |
|---|---|---|---|---|---|---|---|
| Total market | 76% | 90% | 33% | 1,358,641 | 764,784 | 5,292 | 6,603 |
| Tech sector only | 74% | 87% | 44% | 1,480,376 | 695,938 | 5,594 | 7,249 |
| Steady sectors (staples+health) | 81% | 95% | 40% | 1,441,960 | 858,240 | 4,900 | 5,862 |
| 50% tech / 50% market | 76% | 90% | 40% | 1,431,751 | 745,436 | 5,319 | 6,765 |
| Core + tech satellite (75/25) | 76% | 90% | 37% | 1,399,612 | 754,756 | 5,271 | 6,677 |
| 60% market / 40% bonds | 73% | 95% | 13% | 1,187,119 | 828,352 | 5,354 | 6,069 |
| Equal weight 10 industries | 80% | 93% | 38% | 1,422,017 | 826,166 | 4,981 | 6,101 |
| T-bills only (safe) | 8% | 85% | 0% | 847,665 | 735,727 | 6,526 | 6,880 |
| 10-yr bonds only | 39% | 88% | 1% | 946,386 | 745,675 | 6,255 | 6,798 |
| Recommended mix | 79% | 93% | 35% | 1,387,189 | 826,736 | 5,078 | 6,083 |
| Glide path (100% -> 70% stocks, last 4 yrs) | 76% | 92% | 30% | 1,323,027 | 791,245 | 5,279 | 6,378 |

### Goal age 40 - Bootstrap with US stock returns 2 points lower
| Strategy | P(success) S=5,000 | P(success) S=6,667 | P(success) S=3,000 | median wealth S=5,000 | p10 wealth S=5,000 | saving needed 80% (EUR/mo) | saving needed 90% (EUR/mo) |
|---|---|---|---|---|---|---|---|
| Total market | 65% | 85% | 20% | 1,167,583 | 670,746 | 6,123 | 7,516 |
| Tech sector only | 66% | 82% | 33% | 1,268,299 | 611,885 | 6,446 | 8,255 |
| Steady sectors (staples+health) | 70% | 90% | 25% | 1,234,365 | 747,401 | 5,698 | 6,754 |
| 50% tech / 50% market | 66% | 85% | 27% | 1,229,606 | 653,679 | 6,134 | 7,721 |
| Core + tech satellite (75/25) | 66% | 85% | 24% | 1,200,473 | 664,094 | 6,119 | 7,607 |
| 60% market / 40% bonds | 61% | 91% | 7% | 1,082,174 | 761,372 | 5,854 | 6,610 |
| Equal weight 10 industries | 69% | 88% | 22% | 1,219,043 | 719,879 | 5,783 | 6,997 |
| T-bills only (safe) | 6% | 83% | 0% | 838,466 | 730,100 | 6,576 | 6,923 |
| 10-yr bonds only | 37% | 87% | 0% | 936,617 | 739,245 | 6,310 | 6,839 |
| Recommended mix | 68% | 89% | 21% | 1,201,450 | 728,347 | 5,807 | 6,922 |
| Glide path (100% -> 70% stocks, last 4 yrs) | 65% | 87% | 17% | 1,147,841 | 699,520 | 6,031 | 7,206 |

## 3. Detail at goal age 38, S = EUR 5,000/mo after month 12, bootstrap 4000 paths
| Strategy | P(success) | median wealth | median age at 1M | worst vs money put in (p10) | final-3-yr drop (p10) | P(success) if saving stops in tech busts | share of wealth that is deposits |
|---|---|---|---|---|---|---|---|
| Total market | 57% | 1,065,755 | 36.1 | 0.50 | -42% | 48% | 63% |
| Tech sector only | 59% | 1,124,691 | 35.4 | 0.38 | -48% | 52% | 60% |
| Steady sectors (staples+health) | 62% | 1,104,407 | 36.0 | 0.55 | -32% | 50% | 61% |
| 50% tech / 50% market | 59% | 1,101,160 | 35.8 | 0.45 | -46% | 51% | 61% |
| Core + tech satellite (75/25) | 59% | 1,085,488 | 35.9 | 0.48 | -44% | 49% | 62% |
| 60% market / 40% bonds | 42% | 948,354 | 36.9 | 0.67 | -23% | 32% | 71% |
| Equal weight 10 industries | 62% | 1,106,924 | 36.1 | 0.52 | -40% | 51% | 61% |
| T-bills only (safe) | 0% | 712,883 | 37.7 | 0.84 | -2% | 0% | 94% |
| 10-yr bonds only | 9% | 788,269 | 37.5 | 0.79 | -8% | 4% | 85% |
| Recommended mix | 59% | 1,075,650 | 36.0 | 0.52 | -31% | 48% | 62% |
| Glide path (100% -> 70% stocks, last 4 yrs) | 55% | 1,039,639 | 36.1 | 0.52 | -34% | 44% | 65% |
Share of months in which saving pauses in the tech-bust test: 9% (assumption).

Today's EUR 10k book is about 2.4% of the wealth at age 38 (it is dwarfed by new savings).

## 4. How big can the tech satellite be? (rest = 62.5% market / 37.5% steady; goal age 38; S = 5,000)
| tech satellite share of new money | P(success) | median wealth | p10 wealth | worst vs money put in (p10) | saving needed 80% |
|---|---|---|---|---|---|
| 0% | 58% | 1,057,754 | 699,292 | 0.55 | 6,272 |
| 10% | 58% | 1,068,729 | 692,541 | 0.54 | 6,281 |
| 20% | 59% | 1,075,650 | 685,295 | 0.52 | 6,291 |
| 30% | 59% | 1,078,224 | 677,861 | 0.51 | 6,334 |
| 50% | 59% | 1,091,545 | 653,127 | 0.48 | 6,415 |
| 100% | 58% | 1,100,935 | 595,937 | 0.40 | 6,834 |

## 5. Era split at goal age 38 (S = 5,000): start months up to 1974-02 vs after
| Strategy | P(success) early | P(success) late | p10 early | p10 late | rank early (p10) | rank late (p10) |
|---|---|---|---|---|---|---|
| Total market | 56% | 70% | 623,751 | 795,193 | 3 | 7 |
| Tech sector only | 58% | 50% | 597,902 | 725,257 | 10 | 12 |
| Steady sectors (staples+health) | 60% | 77% | 608,483 | 872,577 | 8 | 2 |
| 50% tech / 50% market | 56% | 65% | 614,534 | 790,128 | 7 | 8 |
| Core + tech satellite (75/25) | 57% | 70% | 619,938 | 802,244 | 4 | 5 |
| 60% market / 40% bonds | 35% | 60% | 630,814 | 826,703 | 2 | 3 |
| Equal weight 10 industries | 59% | 79% | 644,708 | 880,101 | 1 | 1 |
| T-bills only (safe) | 0% | 0% | 564,261 | 649,841 | 12 | 13 |
| 10-yr bonds only | 0% | 27% | 571,529 | 768,023 | 11 | 11 |
| Walk-forward max-Sharpe (optimiser) | 43% | 40% | 552,113 | 768,263 | 13 | 10 |
| Walk-forward min-variance (optimiser) | 0% | 22% | 601,590 | 777,205 | 9 | 9 |
| Chase the 10-yr winner | 48% | 68% | 550,561 | 588,819 | 14 | 14 |
| Recommended mix | 55% | 75% | 615,210 | 815,420 | 6 | 4 |
| Glide path (100% -> 70% stocks, last 4 yrs) | 53% | 71% | 615,891 | 796,429 | 5 | 6 |
Rank correlation of bad-case wealth, early vs late: 0.84.

### How often did a 12-year lump investment lose or lag? (real yearly return over every 12-year span since 1926)
| Asset | worst 12y real return/yr | median | best | % of 12-year spans below 0 | % below 3%/yr |
|---|---|---|---|---|---|
| US total market | -3.5 | 7.6 | 16.6 | 11.9 | 25.5 |
| Tech sector | -6.4 | 7.2 | 22.8 | 14.8 | 28.7 |
| Staples | -2.8 | 7.7 | 20.4 | 5.6 | 21.6 |
| Health care | -2.9 | 8.6 | 20.9 | 9.0 | 22.0 |
| 10-yr bonds | -3.7 | 1.3 | 11.3 | 32.8 | 61.8 |
| T-bills | -4.7 | 0.4 | 3.5 | 42.9 | 95.0 |

