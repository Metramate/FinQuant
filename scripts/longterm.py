"""Long-horizon research: how to reach ~EUR 1M (today's money) at ~63 from monthly savings, starting at 26.

    python scripts/longterm.py            # writes reports/latest/longterm/*.png and LONGTERM.md

Method (each block can be checked on its own):
  A. SAVINGS MATH      deterministic: where the money comes from, dilution of today's book, years-to-1M table.
                       Self-test: the simulator is checked against the closed-form annuity formula.
  B. JOURNEYS          replay 37-year savings plans on every historical start month (1936-1986 starts, real returns from
                       100 years of US data) and on a block bootstrap, for ~10 allocation strategies.
  C. WALK-FORWARD      allocation rules that must be ESTIMATED (max-Sharpe, min-variance on trailing 10 years, refit
                       yearly) are tested strictly out-of-sample against simple rules (market, 1/N, 60/40, ...).
  D. ERA SPLIT         does the ranking of strategies found in one half of history hold in the other half?
  E. INCOME LINK       what if saving pauses whenever the tech sector is in a bust (AI-industry job risk)?

Honest limits: US data (the 20th-century winner; a 2pp haircut case is included), EUR/USD ignored, sector indexes stand
in for 'tech' and 'steady' stocks, crypto has no long history (kept out of the tests), ~2.5 truly independent 37-year
periods exist in 100 years. Contribution plans below are ASSUMPTIONS taken from your description.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.optimize import minimize  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from longterm_data import IND, build, cagr  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
AGE0, YEARS, TARGET, BOOK0 = 26, 37, 1_000_000.0, 10_000.0
REC = (0.50, 0.30, 0.20)  # market / steady sectors / tech satellite for NEW money (chosen by principle, then informed by these results: not out-of-sample)
REC_NAME = f"Recommended mix ({100*REC[0]:.0f} market / {100*REC[1]:.0f} steady / {100*REC[2]:.0f} tech, light de-risk late)"
N = YEARS * 12


def md_table(df: pd.DataFrame, fmt: dict | None = None) -> str:
    fmt = fmt or {}
    cols = [df.index.name or ""] + list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for idx, row in df.iterrows():
        out.append("| " + " | ".join([str(idx)] + [fmt.get(c, "{}").format(row[c]) for c in df.columns]) + " |")
    return "\n".join(out)


# ------------------------------------------------------------------ plans (real euros per month; ASSUMPTIONS)
def plan_a(n=N):  # your description: 1,000 for 5y, 1,500 for 5y, then 2,500
    p = np.full(n, 2500.0); p[:60] = 1000.0; p[60:120] = 1500.0
    return p


def plan_b(n=N):  # career upside: 1,000 for 2y then 5,000 (a haircut of the 80k/yr you mentioned)
    p = np.full(n, 5000.0); p[:24] = 1000.0
    return p


def plan_c(n=N):  # conservative: flat 1,000/mo for 37 years, no raises, no career upside
    return np.full(n, 1000.0)


# ------------------------------------------------------------------ engine
def journey(Rs, Rbook, plan, paused=None, target=TARGET):
    """Vectorised savings journey. Rs/Rbook: (paths, months) real returns. Contribution at start of each month."""
    n, m = Rs.shape
    W, Wb, Ccum = np.zeros(n), np.full(n, BOOK0), np.zeros(n)
    hit, minratio = np.full(n, np.nan), np.full(n, np.inf)
    late_peak, late_dd = np.zeros(n), np.zeros(n)
    for k in range(m):
        c = plan[k] * (np.ones(n) if paused is None else (~paused[:, k]).astype(float))
        W = (W + c) * (1 + Rs[:, k])
        Wb = Wb * (1 + Rbook[:, k])
        Ccum += c
        tot = W + Wb
        new = np.isnan(hit) & (tot >= target)
        hit[new] = k + 1
        if k >= 23:
            minratio = np.minimum(minratio, tot / (Ccum + BOOK0))
        if k >= m - 84:  # last 7 years before the goal date: worst fall from the highest value in that stretch
            late_peak = np.maximum(late_peak, tot)
            late_dd = np.minimum(late_dd, tot / late_peak - 1)
    return {"end": W + Wb, "flow": W, "book": Wb, "hit": hit, "min_ratio": minratio, "contrib": Ccum, "late_dd": late_dd}


def self_test():
    r, m, c = 0.05, 300, 1000.0
    mr = (1 + r) ** (1 / 12) - 1
    out = journey(np.full((1, m), mr), np.zeros((1, m)), np.full(m, c))
    closed = c * (((1 + mr) ** m - 1) / mr) * (1 + mr)
    assert abs(out["flow"][0] - closed) < 1e-6 * closed, (out["flow"][0], closed)
    return closed


def rolling_prod(R, w):
    L = np.cumsum(np.log1p(R), axis=1)
    Lw = np.concatenate([np.zeros((R.shape[0], w)), L[:, :-w]], axis=1)
    return np.exp(L - Lw) - 1


def idx_hist(T, starts, m=N):
    return starts[:, None] + np.arange(m)[None, :]


def idx_boot(T, n, m, rng, block=60):
    nb = int(np.ceil(m / block))
    st = rng.integers(0, T - block, size=(n, nb))
    return (st[:, :, None] + np.arange(block)[None, None, :]).reshape(n, -1)[:, :m]


# ------------------------------------------------------------------ strategies
def make_series(A: pd.DataFrame) -> dict:
    """Monthly real return series for fixed-weight strategies (monthly rebalanced)."""
    s = {
        "Total market": A["Mkt"],
        "Tech sector only": A["HiTec"],
        "Steady sectors (staples+health)": 0.5 * A["NoDur"] + 0.5 * A["Hlth"],
        "50% tech / 50% market": 0.5 * A["HiTec"] + 0.5 * A["Mkt"],
        "Core + tech satellite (75/25)": 0.75 * A["Mkt"] + 0.25 * A["HiTec"],
        "60% market / 40% bonds": 0.6 * A["Mkt"] + 0.4 * A["Bond10"],
        "Equal weight 10 industries": A[IND].mean(axis=1),
    }
    return s


def glide_weights(m=N, start_year=22, end_eq=0.60):
    k = np.arange(m) / 12
    return np.where(k < start_year, 1.0, 1.0 - (1 - end_eq) * (k - start_year) / (YEARS - start_year)).clip(end_eq, 1.0)


def wf_series(A: pd.DataFrame, kind: str, lookback=120, refit=12, cap=0.4) -> pd.Series:
    cols = IND + ["Bond10", "Bills"]
    X = A[cols].values
    T, K = X.shape
    out = np.full(T, np.nan)
    w = np.ones(K) / K
    for t in range(lookback, T):
        if (t - lookback) % refit == 0:
            win = X[t - lookback:t]
            mu, cov = win.mean(axis=0) * 12, np.cov(win.T) * 12 + 1e-8 * np.eye(K)
            rf = mu[-1]
            if kind == "maxsharpe":
                obj = lambda x: -(x @ mu - rf) / np.sqrt(x @ cov @ x)  # noqa: E731
            else:
                obj = lambda x: x @ cov @ x  # noqa: E731
            res = minimize(obj, np.ones(K) / K, method="SLSQP", bounds=[(0, cap)] * K,
                           constraints=[{"type": "eq", "fun": lambda x: x.sum() - 1}], options={"maxiter": 300, "ftol": 1e-10})
            w = res.x
        out[t] = X[t] @ w  # weights chosen only from data before t
    return pd.Series(out, index=A.index)


def equity_share(m=N, start_year=25, end_bond=0.25):
    k = np.arange(m) / 12
    return 1.0 - np.where(k < start_year, 0.0, end_bond * (k - start_year) / (YEARS - start_year))


def winner_series(A: pd.DataFrame, lookback=120, refit=12) -> pd.Series:
    """Each year hold whichever of {market, tech, steady} had the best trailing 10-year return (performance chasing)."""
    cand = pd.DataFrame({"Mkt": A["Mkt"], "HiTec": A["HiTec"], "Steady": 0.5 * A["NoDur"] + 0.5 * A["Hlth"]})
    out, pick = np.full(len(A), np.nan), None
    for t in range(lookback, len(A)):
        if (t - lookback) % refit == 0:
            pick = (1 + cand.iloc[t - lookback:t]).prod().idxmax()
        out[t] = cand.iloc[t][pick]
    return pd.Series(out, index=A.index)


def run_all(series: dict, glide_pair, Hit, Bk, idx, plan, paused_thr=None, target=TARGET, rec_pair=None):
    """Run all strategies on index matrix idx; returns dict name -> journey result."""
    res = {}
    paused = None
    if paused_thr is not None:
        paused = rolling_prod(Hit[idx], 12) < paused_thr
        paused[:, :12] = False
    for name, ser in series.items():
        res[name] = journey(ser.values[idx], Bk[idx], plan, paused, target)
    gm, gb = glide_pair
    g = glide_weights(idx.shape[1])
    Rg = g[None, :] * gm[idx] + (1 - g)[None, :] * gb[idx]
    res["Glide path (100% -> 60% stocks)"] = journey(Rg, Bk[idx], plan, paused, target)
    if rec_pair is not None:
        eq, bd = rec_pair
        e = equity_share(idx.shape[1])
        Rr = e[None, :] * eq[idx] + (1 - e)[None, :] * bd[idx]
        res[REC_NAME] = journey(Rr, Bk[idx], plan, paused, target)
    return res


def summarise(res, plan_scale_sum, target=TARGET):
    rows = {}
    for k, r in res.items():
        hit = r["hit"]
        age = AGE0 + hit / 12
        need = np.quantile((target - r["book"]) / r["flow"], 0.80)  # multiple of the plan needed for 80% success
        rows[k] = {
            "P(reach 1M by 63)": float((r["end"] >= target).mean()),
            "median wealth at 63": float(np.median(r["end"])),
            "p10 wealth at 63": float(np.percentile(r["end"], 10)),
            "p90 wealth at 63": float(np.percentile(r["end"], 90)),
            "median age at 1M": float(np.nanmedian(age)),
            "p90 age at 1M (slow)": float(np.nanpercentile(age, 90)) if np.isfinite(np.nanpercentile(age, 90)) else np.nan,
            "worst vs money put in (p10)": float(np.percentile(r["min_ratio"], 10)),
            "worst drop in final 7 yrs (p10)": float(np.percentile(r["late_dd"], 10)),
            "saving for 80% (EUR/mo avg)": float(max(need, 0) * plan_scale_sum / N),
        }
    return pd.DataFrame(rows).T


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sims", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--out", default=str(ROOT / "reports" / "latest" / "longterm"))
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    md = ["# Long-horizon research: reaching EUR 1M (today's money) by ~63", ""]
    closed = self_test()
    md += [f"Self-test: simulator = closed-form annuity formula (EUR {closed:,.0f} for 1,000/mo, 5% real, 25y). OK.", ""]

    A = build()
    T = len(A)
    Hit, Bk = A["HiTec"].values, A["HiTec"].values  # today's 10k book proxied by the tech sector (assumption; small effect)
    PA, PB = plan_a(), plan_b()
    sumA, sumB = PA.sum(), PB.sum()
    md += [f"Data: {A.index[0]} to {A.index[-1]} ({T} months), real (inflation-adjusted) returns.",
           f"Plan A (your description, real euros): 1,000/mo yrs 1-5, 1,500 yrs 6-10, 2,500 yrs 11-37 = EUR {sumA:,.0f} saved in total (avg {sumA/N:,.0f}/mo). "
           f"Plan B (career upside): 1,000/mo for 2 yrs then 5,000/mo = EUR {sumB:,.0f} (avg {sumB/N:,.0f}/mo).", ""]

    # ---------------- A. savings math
    def wealth_path(r_annual, plan, book=BOOK0):
        mr = (1 + r_annual) ** (1 / 12) - 1
        W, Wb, rows = 0.0, book, []
        C = 0.0
        for k in range(len(plan)):
            W = (W + plan[k]) * (1 + mr); Wb *= 1 + mr; C += plan[k]
            rows.append((W + Wb, C + book, Wb))
        return np.array(rows)

    fig, ax = plt.subplots(1, 2, figsize=(15, 5.6))
    yrs = np.arange(1, N + 1) / 12
    for r, col in ((0.0, "#9aa5b1"), (0.03, "#4c78a8"), (0.05, "#2a9d8f"), (0.07, "#7b4fd3")):
        wp = wealth_path(r, PA)
        ax[0].plot(AGE0 + yrs, wp[:, 0], color=col, lw=2.2, label=f"{100*r:.0f}% real return  ->  EUR {wp[-1,0]/1000:,.0f}k at 63")
    ax[0].axhline(TARGET, color="black", ls="--", lw=.9)
    ax[0].text(AGE0 + 0.5, TARGET * 1.03, "EUR 1M (today's money)", fontsize=8)
    ax[0].yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M"))
    ax[0].set_xlabel("your age"); ax[0].set_title("Your savings plan A, at different average real returns\n(real euros: inflation already removed, i.e. today's purchasing power)", fontsize=10)
    ax[0].legend(frameon=False, fontsize=8, loc="upper left")
    wp = wealth_path(0.05, PA)
    ax[1].stackplot(AGE0 + yrs, wp[:, 2] * 0 + (wp[:, 1]), wp[:, 0] - wp[:, 1], colors=["#c7d2de", "#2a9d8f"], labels=["money you put in", "growth the market added"])
    ax[1].set_title("At 5% real: how much of the wealth is YOUR money vs the market's", fontsize=10)
    ax[1].yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M"))
    share_c = wp[-1, 1] / wp[-1, 0]
    ax[1].set_xlabel("your age"); ax[1].legend(frameon=False, loc="upper left")
    ann_growth = np.diff(wp[:, 0] - wp[:, 1], prepend=0) * 12  # growth part change per year
    cross = int(np.argmax(ann_growth > PA * 12)) / 12 if (ann_growth > PA * 12).any() else np.nan
    fig.tight_layout(); fig.savefig(out / "01_where_it_comes_from.png", dpi=130); plt.close(fig)
    md += ["## A. Savings math", f"At 5% real, {100*share_c:.0f}% of the final wealth is money you put in; the market's growth is {100*(1-share_c):.0f}%. "
           f"Yearly market growth first exceeds your yearly saving after about {cross:.0f} years (age {AGE0+cross:.0f}).", ""]

    # dilution of today's book
    fig, ax = plt.subplots(figsize=(10, 4.8))
    for g_book, g_flow, col, lab in ((0.06, 0.06, "#7b4fd3", "book grows like everything else (6% real)"),
                                    (0.12, 0.05, "#d1495b", "book grows 12% real, new money 5% (very optimistic for the book)")):
        wb = BOOK0 * (1 + g_book) ** yrs
        wf = wealth_path(g_flow, PA, book=0.0)[:, 0]
        ax.plot(AGE0 + yrs, 100 * wb / (wb + wf), color=col, lw=2.4, label=lab)
    ax.set_ylabel("% of everything you own that is today's EUR 10k book"); ax.set_xlabel("your age")
    ax.set_title("Your current portfolio gets diluted by your own savings, quickly", fontsize=11)
    ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(out / "02_dilution.png", dpi=130); plt.close(fig)
    wb6, wf6 = BOOK0 * 1.06 ** np.array([5, 10, 20]), wealth_path(0.06, PA, 0.0)[[59, 119, 239], 0]
    md += ["Share of total wealth that is today's EUR 10k book (6% real for everything): " + ", ".join(f"after {y} yrs {100*b/(b+f):.0f}%" for y, b, f in zip([5, 10, 20], wb6, wf6)) + ".", ""]

    # years-to-1M heatmap (flat saving)
    savings = np.array([500, 1000, 1500, 2000, 2500, 3000, 4000, 5000, 6000])
    rets = np.array([0.0, 0.02, 0.04, 0.05, 0.06, 0.08, 0.10])
    Z = np.zeros((len(savings), len(rets)))
    for i, s in enumerate(savings):
        for j, r in enumerate(rets):
            plan = np.full(12 * 60, float(s))
            wp_ = wealth_path(r, plan)[:, 0]
            Z[i, j] = (np.argmax(wp_ >= TARGET) + 1) / 12 if (wp_ >= TARGET).any() else np.nan
    fig, ax = plt.subplots(figsize=(10, 5.2))
    im = ax.imshow(Z, cmap="RdYlGn_r", vmin=6, vmax=45, aspect="auto", origin="lower")
    ax.set_xticks(range(len(rets)), [f"{100*r:.0f}%" for r in rets]); ax.set_yticks(range(len(savings)), [f"{s:,}" for s in savings])
    for i in range(len(savings)):
        for j in range(len(rets)):
            ax.text(j, i, "n/a" if np.isnan(Z[i, j]) else f"{Z[i,j]:.0f}", ha="center", va="center", fontsize=9)
    ax.set_xlabel("average yearly return above inflation"); ax.set_ylabel("EUR saved per month (flat, today's money)")
    ax.set_title("Years until you first hold EUR 1M (today's money), starting from EUR 10k", fontsize=11)
    fig.colorbar(im, label="years"); fig.tight_layout(); fig.savefig(out / "03_years_to_million.png", dpi=130); plt.close(fig)
    md += ["Years to EUR 1M (rows: EUR/month, columns: real return):", md_table(pd.DataFrame(Z, index=[f"{s:,}" for s in savings], columns=[f"{100*r:.0f}%" for r in rets]).round(0).rename_axis("EUR/mo"), {c: "{:.0f}" for c in [f"{100*r:.0f}%" for r in rets]}), ""]
    # second route for one cell: 2,000/mo @5% real
    mr = 1.05 ** (1 / 12) - 1
    n_exact = np.log(1 + (TARGET - BOOK0 * 0) * mr / (2000 * (1 + mr))) / np.log(1 + mr)  # ignoring the 10k start (conservative)
    md += [f"Check of one cell by formula (ignoring the 10k start): 2,000/mo at 5% real needs {n_exact/12:.1f} yrs (table with the 10k: {Z[3, 3]:.1f}).", ""]

    # ---------------- B. journeys
    series = make_series(A)
    wf_ms, wf_mv = wf_series(A, "maxsharpe"), wf_series(A, "minvar")
    series_wf = {"Walk-forward max-Sharpe (optimiser)": wf_ms, "Walk-forward min-variance (optimiser)": wf_mv,
                 "Chase the 10-yr winner (market/tech/steady)": winner_series(A)}
    rec_eq = REC[0] * A["Mkt"] + REC[1] * (0.5 * A["NoDur"] + 0.5 * A["Hlth"]) + REC[2] * A["HiTec"]
    rec_pair = (rec_eq.values, A["Bond10"].values)
    glide_pair = (A["Mkt"].values, A["Bond10"].values)
    starts = np.arange(120, T - N + 1)
    Ih = idx_hist(T, starts)
    Ib = idx_boot(T, a.sims, N, rng)
    all_series = {**series, **series_wf}
    resH = run_all(all_series, glide_pair, Hit, Bk, Ih, PA, rec_pair=rec_pair)
    resB = run_all(series, glide_pair, Hit, Bk, Ib, PA, rec_pair=rec_pair)
    sH, sB = summarise(resH, sumA), summarise(resB, sumA)
    fmtS = {"P(reach 1M by 63)": "{:.0%}", "median wealth at 63": "{:,.0f}", "p10 wealth at 63": "{:,.0f}", "p90 wealth at 63": "{:,.0f}", "median age at 1M": "{:.1f}",
            "p90 age at 1M (slow)": "{:.1f}", "worst vs money put in (p10)": "{:.2f}", "worst drop in final 7 yrs (p10)": "{:.0%}", "saving for 80% (EUR/mo avg)": "{:,.0f}"}
    md += ["## B. 37-year journeys, plan A", f"Historical: {len(starts)} overlapping start months ({A.index[starts[0]]} to {A.index[starts[-1]]}), at most ~2.5 independent periods. "
           "'worst vs money put in' = lowest value of (wealth / total euros you had put in) after year 2, 10th-percentile path (0.60 = at the worst point you held 60% of what you contributed).",
           "### Historical start months", md_table(sH.rename_axis("Strategy"), fmtS), "", f"### Block bootstrap ({a.sims} paths, 5-year blocks)", md_table(sB.rename_axis("Strategy"), fmtS), ""]

    # haircut scenario: US equity returns 2pp/yr lower
    haircut = A.copy()
    for c in IND + ["Mkt"]:
        haircut[c] = (1 + haircut[c]) * (1 - 0.02 / 12) - 1
    rec_hc = REC[0] * haircut["Mkt"] + REC[1] * (0.5 * haircut["NoDur"] + 0.5 * haircut["Hlth"]) + REC[2] * haircut["HiTec"]
    resHC = run_all(make_series(haircut), (haircut["Mkt"].values, haircut["Bond10"].values), haircut["HiTec"].values, haircut["HiTec"].values, Ib, PA, rec_pair=(rec_hc.values, haircut["Bond10"].values))
    sHC = summarise(resHC, sumA)
    md += ["### Bootstrap with US equity returns cut by 2 percentage points a year (the 'US was a lucky winner' case)", md_table(sHC.rename_axis("Strategy"), fmtS), ""]

    # plan B
    resBB = run_all(series, glide_pair, Hit, Bk, Ib, PB, rec_pair=rec_pair)
    sBB = summarise(resBB, sumB)
    md += ["### Plan B (career upside), bootstrap", md_table(sBB.rename_axis("Strategy"), {**fmtS, "saving for 80% (EUR/mo avg)": "{:,.0f}"}), ""]

    # plan C: flat 1,000/mo, the case where allocation actually matters
    sumC = plan_c().sum()
    resCH = run_all(all_series, glide_pair, Hit, Bk, Ih, plan_c(), rec_pair=rec_pair)
    resCB = run_all(series, glide_pair, Hit, Bk, Ib, plan_c(), rec_pair=rec_pair)
    resCC = run_all(make_series(haircut), (haircut["Mkt"].values, haircut["Bond10"].values), haircut["HiTec"].values, haircut["HiTec"].values, Ib, plan_c(), rec_pair=(rec_hc.values, haircut["Bond10"].values))
    sCH, sCB, sCC = summarise(resCH, sumC), summarise(resCB, sumC), summarise(resCC, sumC)
    keyc = ["P(reach 1M by 63)", "median wealth at 63", "p10 wealth at 63", "median age at 1M", "worst vs money put in (p10)", "worst drop in final 7 yrs (p10)"]
    md += [f"### Plan C: flat EUR 1,000/month for 37 years, no raises (total EUR {sumC:,.0f}). THE case where allocation matters",
           "Historical start months:", md_table(sCH[keyc].rename_axis("Strategy"), fmtS), "", "Block bootstrap:", md_table(sCB[keyc].rename_axis("Strategy"), fmtS), "",
           "Bootstrap, US stock returns 2 points lower:", md_table(sCC[keyc].rename_axis("Strategy"), fmtS), ""]

    # chart 4: age at 1M
    names = list(sB.index)
    fig, ax = plt.subplots(1, 2, figsize=(15, 5.8), gridspec_kw={"width_ratios": [1.25, 1]})
    order = sB["median age at 1M"].sort_values().index
    for i, nme in enumerate(order):
        age = AGE0 + resB[nme]["hit"] / 12
        lo, med, hi = np.nanpercentile(age, [10, 50, 90])
        col = "#7b4fd3" if "Tech" in nme else ("#2a9d8f" if "Steady" in nme or "60%" in nme else "#4c78a8")
        ax[0].plot([lo, hi], [i, i], color=col, lw=7, alpha=.35, solid_capstyle="round")
        ax[0].scatter([med], [i], color="white", edgecolor="black", s=60, zorder=5)
        ax[0].text(hi + .3, i, f"median {med:.0f}", va="center", fontsize=8)
    ax[0].set_yticks(range(len(order)), order, fontsize=8)
    ax[0].set_xlabel("age when you first hold EUR 1M in today's money (bar = 10th-90th percentile of futures)")
    ax[0].set_title("Plan A: when do you get to EUR 1M? (block bootstrap of 100 yrs of data)", fontsize=10)
    ord2 = sB["saving for 80% (EUR/mo avg)"].sort_values().index
    yy = np.arange(len(ord2))
    ax[1].barh(yy + .2, [sB.loc[o, "saving for 80% (EUR/mo avg)"] for o in ord2], height=.38, color="#4c78a8", label="normal times")
    ax[1].barh(yy - .2, [sHC.loc[o, "saving for 80% (EUR/mo avg)"] if o in sHC.index else 0 for o in ord2], height=.38, color="#d1495b", label="stock returns 2 pts lower")
    ax[1].axvline(sumA / N, color="black", ls="--", lw=1)
    ax[1].text(sumA / N - 20, -0.9, "plan A average", fontsize=8, ha="right")
    ax[1].set_yticks(range(len(ord2)), ord2, fontsize=8)
    ax[1].set_xlabel("average EUR saved per month needed for an 80% chance of EUR 1M at 63")
    ax[1].set_title("How much saving each strategy needs", fontsize=10); ax[1].legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout(); fig.savefig(out / "04_when_and_how_much.png", dpi=130); plt.close(fig)

    # ---------------- C. walk-forward (strict out-of-sample)
    base_idx = A.index[120:]
    cmp = {"Walk-forward max-Sharpe": wf_ms, "Walk-forward min-variance": wf_mv, "Equal weight 10 industries (no estimation)": series["Equal weight 10 industries"],
           "Chase the 10-yr winner": series_wf["Chase the 10-yr winner (market/tech/steady)"],
           "Total market": A["Mkt"], "60% market / 40% bonds": series["60% market / 40% bonds"]}
    wf_stats = {}
    for k, s in cmp.items():
        s = s.loc[base_idx]
        cum = (1 + s).cumprod()
        wf_stats[k] = {"real CAGR %": 100 * cagr(s), "vol %": 100 * s.std() * 12 ** .5, "Sharpe vs bills": (s.mean() - A["Bills"].loc[base_idx].mean()) * 12 / (s.std() * 12 ** .5),
                       "worst drawdown %": 100 * (cum / cum.cummax() - 1).min()}
    wfd = pd.DataFrame(wf_stats).T
    fig, ax = plt.subplots(1, 2, figsize=(15, 5.2), gridspec_kw={"width_ratios": [1.5, 1]})
    for (k, s), col in zip(cmp.items(), ["#d1495b", "#e9a8a0", "#8d99ae", "#f2a900", "#4c78a8", "#2a9d8f"]):
        ax[0].plot((1 + s.loc[base_idx]).cumprod().values, color=col, lw=1.8, label=f"{k} (Sharpe {wfd.loc[k,'Sharpe vs bills']:.2f})")
    ax[0].set_yscale("log"); ax[0].set_xticks(np.arange(0, len(base_idx), 120), [str(base_idx[i])[:4] for i in range(0, len(base_idx), 120)])
    ax[0].yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"{v:.0f}x")); ax[0].set_title(f"Strictly out-of-sample, {base_idx[0]}-{base_idx[-1]}: growth of 1 real euro", fontsize=10)
    ax[0].legend(frameon=False, fontsize=8)
    ax[1].bar(range(len(wfd)), wfd["Sharpe vs bills"], color=["#d1495b", "#e9a8a0", "#8d99ae", "#f2a900", "#4c78a8", "#2a9d8f"])
    ax[1].set_xticks(range(len(wfd)), ["WF\nmax-Sharpe", "WF\nmin-var", "1/N", "Chase\nwinner", "Market", "60/40"], fontsize=8)
    ax[1].set_title("Risk-adjusted return (Sharpe), out-of-sample", fontsize=10)
    fig.tight_layout(); fig.savefig(out / "05_walk_forward.png", dpi=130); plt.close(fig)
    md += ["## C. Walk-forward, strictly out-of-sample (weights re-estimated each year from only the previous 10 years)",
           md_table(wfd.rename_axis("Strategy"), {c: "{:.2f}" for c in wfd.columns}), ""]

    # ---------------- D. era split + regime flips
    mid = (starts[0] + starts[-1]) // 2
    eraA, eraB = starts <= mid, starts > mid
    rk = {}
    for name in all_series:
        e = resH[name]["end"]
        rk[name] = {"median wealth, early starts": np.median(e[eraA]), "median wealth, late starts": np.median(e[eraB]),
                    "p10, early": np.percentile(e[eraA], 10), "p10, late": np.percentile(e[eraB], 10)}
    rk = pd.DataFrame(rk).T
    rk["rank early (median)"] = rk["median wealth, early starts"].rank(ascending=False)
    rk["rank late (median)"] = rk["median wealth, late starts"].rank(ascending=False)
    rho = rk["rank early (median)"].corr(rk["rank late (median)"], method="spearman")
    rk["rank early (p10)"] = rk["p10, early"].rank(ascending=False)
    rk["rank late (p10)"] = rk["p10, late"].rank(ascending=False)
    rho10 = rk["rank early (p10)"].corr(rk["rank late (p10)"], method="spearman")
    md += ["## D. Does the winner in one era win in the other? (plan A wealth at 63; early = start months " + f"{A.index[starts[0]]}..{A.index[mid]}, late = ..{A.index[starts[-1]]})",
           md_table(rk[["median wealth, early starts", "median wealth, late starts", "rank early (median)", "rank late (median)", "p10, early", "p10, late", "rank early (p10)", "rank late (p10)"]].rename_axis("Strategy"),
                    {"median wealth, early starts": "{:,.0f}", "median wealth, late starts": "{:,.0f}", "p10, early": "{:,.0f}", "p10, late": "{:,.0f}", "rank early (median)": "{:.0f}", "rank late (median)": "{:.0f}", "rank early (p10)": "{:.0f}", "rank late (p10)": "{:.0f}"}),
           f"Rank correlation early vs late: median {rho:.2f}, 10th percentile {rho10:.2f} (1 = same ranking, 0 = no relation).", ""]
    g15 = lambda s: (1 + s).rolling(180).apply(np.prod, raw=True) ** (12 / 180) - 1  # noqa: E731
    gap_t = (g15(A["HiTec"]) - g15(A["Mkt"])).dropna()
    gap_s = (g15(A["NoDur"]) - g15(A["Mkt"])).dropna()
    fig, ax = plt.subplots(figsize=(13, 4.8))
    ax.plot(gap_t.index.to_timestamp(), 100 * gap_t.values, color="#7b4fd3", lw=2, label="Tech sector minus market")
    ax.plot(gap_s.index.to_timestamp(), 100 * gap_s.values, color="#2a9d8f", lw=2, label="Staples sector minus market")
    ax.axhline(0, color="black", lw=.8)
    ax.fill_between(gap_t.index.to_timestamp(), 0, 100 * gap_t.values, where=gap_t.values > 0, color="#7b4fd3", alpha=.12)
    ax.set_ylabel("yearly return gap over the previous 15 years (pts)")
    ax.set_title("Who wins flips with the era: 15-year windows, gap vs the total market (dated at window end)", fontsize=11)
    ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(out / "06_regime_flips.png", dpi=130); plt.close(fig)
    md += [f"Tech beat the market in {100*(gap_t>0).mean():.0f}% of all 15-year windows; staples in {100*(gap_s>0).mean():.0f}%. Gap range tech: {100*gap_t.min():.1f} to {100*gap_t.max():+.1f} pts/yr.", ""]

    # ---------------- E. income link
    resI = run_all(series, glide_pair, Hit, Bk, Ib, PA, paused_thr=-0.25)
    sI = summarise(resI, sumA)
    share_paused = float((rolling_prod(Hit[Ib], 12) < -0.25).mean())
    keys = ["Total market", "Tech sector only", "Core + tech satellite (75/25)", "60% market / 40% bonds", "Steady sectors (staples+health)"]
    fig, ax = plt.subplots(1, 2, figsize=(14, 4.8))
    x = np.arange(len(keys))
    ax[0].bar(x - .2, [sB.loc[k, "saving for 80% (EUR/mo avg)"] for k in keys], .4, color="#4c78a8", label="income steady")
    ax[0].bar(x + .2, [sI.loc[k, "saving for 80% (EUR/mo avg)"] for k in keys], .4, color="#d1495b", label="saving stops in tech busts")
    ax[0].set_xticks(x, ["Total\nmarket", "Tech\nonly", "Core+tech\n75/25", "60/40", "Steady\nsectors"], fontsize=8)
    ax[0].set_title("Saving needed for an 80% chance of EUR 1M (avg EUR/mo)", fontsize=10); ax[0].legend(frameon=False, fontsize=8)
    ax[1].bar(x - .2, [100 * sB.loc[k, "P(reach 1M by 63)"] for k in keys], .4, color="#4c78a8")
    ax[1].bar(x + .2, [100 * sI.loc[k, "P(reach 1M by 63)"] for k in keys], .4, color="#d1495b")
    ax[1].set_xticks(x, ["Total\nmarket", "Tech\nonly", "Core+tech\n75/25", "60/40", "Steady\nsectors"], fontsize=8)
    ax[1].set_ylim(80, 101); ax[1].set_title("Chance of reaching EUR 1M by 63 with plan A (%)", fontsize=10)
    fig.tight_layout(); fig.savefig(out / "07_income_link.png", dpi=130); plt.close(fig)
    md += ["## E. If your income is tied to the tech cycle (AI job): saving pauses when the tech sector's last-12-months return is below -25%",
           f"In the bootstrap this applies in {100*share_paused:.0f}% of months (assumption, not a measurement of your career).", md_table(sI.loc[keys].rename_axis("Strategy"), fmtS), ""]

    # chart 8: cost of safety (plan C, bootstrap): pain vs saving needed
    fig, ax = plt.subplots(figsize=(11, 6.2))
    for nme in sCB.index:
        pain = 100 * (1 - sCB.loc[nme, "worst vs money put in (p10)"])
        need = float(np.quantile((TARGET - resCB[nme]["book"]) / resCB[nme]["flow"], 0.80) * 1000)
        col = "#7b4fd3" if "Tech" in nme else "#2a9d8f" if ("Steady" in nme or "60%" in nme) else "#d1495b" if "Recommended" in nme else "#4c78a8"
        ax.scatter(pain, need, s=140 if "Recommended" in nme else 70, color=col, edgecolor="white", zorder=5)
        ax.annotate(nme.split(" (")[0].replace("Recommended mix", "RECOMMENDED mix"), (pain, need), xytext=(5, 4), textcoords="offset points", fontsize=8)
    ax.set_xlabel("PAIN: in the worst 1-in-10 futures, at the low point you were down this % versus the money you had put in")
    ax.set_ylabel("COST: EUR per month (flat) needed for an 80% chance of EUR 1M at 63")
    ax.set_title("Pain vs. what you must save: lower-left is better (flat-saving plan C, 100 years of bootstrapped history)", fontsize=10)
    fig.tight_layout(); fig.savefig(out / "08_pain_vs_cost.png", dpi=130); plt.close(fig)

    # chart 9: recommended allocation by age
    ages = AGE0 + np.arange(N) / 12
    e = equity_share()
    fig, ax = plt.subplots(figsize=(11, 4.8))
    ax.stackplot(ages, 100 * e * REC[0], 100 * e * REC[1], 100 * e * REC[2], 100 * (1 - e), colors=["#4c78a8", "#2a9d8f", "#7b4fd3", "#c7d2de"],
                 labels=["Broad all-world stock fund (core)", "Steady/quality tilt (staples, health, payments)", "Your thesis satellite: tech / AI / crypto", "Bonds (de-risk in last 12 years)"])
    ax.set_xlabel("your age"); ax.set_ylabel("% of NEW money"); ax.set_ylim(0, 100)
    ax.set_title("Suggested split for incoming money (your existing holdings stay untouched and get diluted)", fontsize=10)
    ax.legend(frameon=False, loc="lower left", fontsize=8)
    fig.tight_layout(); fig.savefig(out / "09_suggested_split.png", dpi=130); plt.close(fig)

    (out / "LONGTERM.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
