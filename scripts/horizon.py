"""Reach ~EUR 1M (today's money) by age 35-40, starting at 26 with EUR 10k: what to save and how to invest.

    python scripts/horizon.py            # writes reports/latest/horizon/*.png and HORIZON.md

This replaces the earlier 37-YEAR analysis (longterm.py), which assumed the wrong horizon. Goal ages 35 / 38 / 40 = 9 / 12 / 14
years from now. With a horizon this short, SAVINGS dominate and the risk of a bad stretch near the goal date matters a lot.

Savings plan (ASSUMPTIONS from what you said, real euros per month): EUR 1,000 until a better job starts (default month 12), then
S euros per month. S is varied (3,000 / 5,000 / 6,667 = EUR 80k a year / ...). Everything is in today's money.

Checks (each can be verified on its own):
  * deterministic math: closed form, and the simulator is tested against it;
  * 100 years of US data (Ken French + Shiller): every historical start month, 9-14 year journeys;
  * block bootstrap (3-year blocks) and a case with US stock returns 2 points lower;
  * walk-forward: allocation rules that must be estimated vs simple rules (out-of-sample), and an era split;
  * income link: saving pauses when the tech sector's last-12-months return is below -25%.
Limits: US data, EUR/USD ignored, sector indexes stand in for tech/steady stocks, crypto excluded (no history), the 10k book is
proxied by the tech sector (it is ~1% of the wealth at the goal date, so this barely matters). Not advice.
"""
from __future__ import annotations

import argparse
import pathlib
import shutil
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from longterm import make_series, md_table, rolling_prod, wf_series, winner_series  # noqa: E402
from longterm_data import IND, build  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
AGE0, TARGET, BOOK0 = 26, 1_000_000.0, 10_000.0
GOAL_AGES = [35, 38, 40]
S_GRID = np.arange(2000, 8001, 500)
C = {"Total market": "#4c78a8", "Tech sector only": "#7b4fd3", "Steady sectors (staples+health)": "#2a9d8f", "Recommended mix": "#d1495b",
     "60% market / 40% bonds": "#8d99ae", "T-bills only (safe)": "#bbbbbb", "10-yr bonds only": "#999999", "Equal weight 10 industries": "#f2a900"}


# ------------------------------------------------------------------ engine
def plan_vec(n, j, s, pre=1000.0):
    p = np.full(n, float(s)); p[:j] = pre
    return p


def unit_ends(R, j, pre=1000.0):
    """End values of (a) EUR 'pre' per month for months < j and (b) EUR 1 per month from month j: wealth is linear in S."""
    n, m = R.shape
    Wp, Wq = np.zeros(n), np.zeros(n)
    for k in range(m):
        Wp = (Wp + (pre if k < j else 0.0)) * (1 + R[:, k])
        Wq = (Wq + (1.0 if k >= j else 0.0)) * (1 + R[:, k])
    return Wp, Wq


def book_end(Rbook):
    return BOOK0 * np.prod(1 + Rbook, axis=1)


def journey(R, Rbook, plan, paused=None, late=36):
    n, m = R.shape
    W, Wb, Cc = np.zeros(n), np.full(n, BOOK0), np.zeros(n)
    hit, minr = np.full(n, np.nan), np.full(n, np.inf)
    peak, ldd = np.zeros(n), np.zeros(n)
    for k in range(m):
        c = plan[k] * (np.ones(n) if paused is None else (~paused[:, k]).astype(float))
        W = (W + c) * (1 + R[:, k]); Wb = Wb * (1 + Rbook[:, k]); Cc += c
        tot = W + Wb
        new = np.isnan(hit) & (tot >= TARGET); hit[new] = k + 1
        if k >= 11:
            minr = np.minimum(minr, tot / (Cc + BOOK0))
        if k >= m - late:
            peak = np.maximum(peak, tot); ldd = np.minimum(ldd, tot / peak - 1)
    return {"end": W + Wb, "hit": hit, "min_ratio": minr, "late_dd": ldd, "contrib": Cc, "book": Wb, "flow": W}


def self_test():
    r, m, c = 0.05, 144, 1000.0
    mr = (1 + r) ** (1 / 12) - 1
    out = journey(np.full((1, m), mr), np.zeros((1, m)), np.full(m, c))
    closed = c * (((1 + mr) ** m - 1) / mr) * (1 + mr)
    assert abs(out["flow"][0] - closed) < 1e-6 * closed
    Wp, Wq = unit_ends(np.full((1, m), mr), 12, 1000.0)
    assert abs(Wp[0] + 5000 * Wq[0] - journey(np.full((1, m), mr), np.zeros((1, m)), plan_vec(m, 12, 5000))["flow"][0]) < 1e-6 * closed
    return closed


def idx_hist(starts, m):
    return starts[:, None] + np.arange(m)[None, :]


def idx_boot(T, n, m, rng, block=36):
    nb = int(np.ceil(m / block))
    st = rng.integers(0, T - block, size=(n, nb))
    return (st[:, :, None] + np.arange(block)[None, None, :]).reshape(n, -1)[:, :m]


def eq_share(m, Y, bond_end=0.30, years=4):
    k = np.arange(m) / 12
    return 1.0 - np.where(k < Y - years, 0.0, bond_end * (k - (Y - years)) / years).clip(0, bond_end)


REC = (0.50, 0.30, 0.20)  # market / steady sectors / tech satellite; chosen by principle, informed by results (NOT out-of-sample)


def strat_returns(A, Y, idx, rec_w=REC, with_wf=True):
    """dict name -> (n, m) strategy return matrices on index matrix idx."""
    ser = make_series(A)
    out = {k: v.values[idx] for k, v in ser.items() if k in ("Total market", "Tech sector only", "Steady sectors (staples+health)", "60% market / 40% bonds",
                                                              "Equal weight 10 industries", "Core + tech satellite (75/25)", "50% tech / 50% market")}
    out["T-bills only (safe)"] = A["Bills"].values[idx]
    out["10-yr bonds only"] = A["Bond10"].values[idx]
    if with_wf:  # these rules need 10 real years of history first: only valid on real historical start dates
        out["Walk-forward max-Sharpe (optimiser)"] = wf_series_cached(A, "maxsharpe").values[idx]
        out["Walk-forward min-variance (optimiser)"] = wf_series_cached(A, "minvar").values[idx]
        out["Chase the 10-yr winner"] = winner_series(A).values[idx]
    eq = rec_w[0] * A["Mkt"] + rec_w[1] * (0.5 * A["NoDur"] + 0.5 * A["Hlth"]) + rec_w[2] * A["HiTec"]
    e = eq_share(idx.shape[1], Y)
    out["Recommended mix"] = e[None, :] * eq.values[idx] + (1 - e)[None, :] * A["Bond10"].values[idx]
    g = eq_share(idx.shape[1], Y)
    out["Glide path (100% -> 70% stocks, last 4 yrs)"] = g[None, :] * A["Mkt"].values[idx] + (1 - g)[None, :] * A["Bond10"].values[idx]
    return out


_WF = {}


def wf_series_cached(A, kind):
    key = (kind, id(A))
    if key not in _WF:
        _WF[key] = wf_series(A, kind)
    return _WF[key]


def tech_dial(A, Y, idx, t):
    base = (0.625 * A["Mkt"] + 0.375 * (0.5 * A["NoDur"] + 0.5 * A["Hlth"]))
    eq = (1 - t) * base + t * A["HiTec"]
    e = eq_share(idx.shape[1], Y)
    return e[None, :] * eq.values[idx] + (1 - e)[None, :] * A["Bond10"].values[idx]


def need_for(conf, Wb, Wp, Wq):
    return np.maximum(np.quantile((TARGET - Wb - Wp) / Wq, conf), 0.0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--job-start-month", type=int, default=12)
    ap.add_argument("--sims", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=5)
    ap.add_argument("--out", default=str(ROOT / "reports" / "latest" / "horizon"))
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    J = a.job_start_month
    md = ["# Reaching EUR 1M (today's money) by age 35-40, starting at 26", "",
          f"Self-test OK (simulator = closed form: EUR {self_test():,.0f}).", ""]

    A = build()
    T = len(A)
    hit_all = A["HiTec"].values
    hair = A.copy()
    for c in IND + ["Mkt"]:
        hair[c] = (1 + hair[c]) * (1 - 0.02 / 12) - 1
    md += [f"Data {A.index[0]}..{A.index[-1]} ({T} months, real returns). Savings: EUR 1,000/mo until month {J}, then S per month (S varied). Goal ages {GOAL_AGES} = {[g-AGE0 for g in GOAL_AGES]} years.", ""]

    # ---------------- 1. deterministic math
    def det(Y, S, r):
        mr = (1 + r) ** (1 / 12) - 1
        W, Wb = 0.0, BOOK0
        for k in range(Y * 12):
            W = (W + (1000.0 if k < J else S)) * (1 + mr); Wb *= 1 + mr
        return W + Wb

    # required S by goal age and real return (closed form via bisection on the monotone function)
    rets = [0.0, 0.03, 0.05, 0.07, 0.10]
    need = {}
    for g in GOAL_AGES + [36, 37, 39]:
        Y = g - AGE0
        for r in rets:
            lo, hi = 0.0, 30000.0
            for _ in range(60):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if det(Y, mid, r) < TARGET else (lo, mid)
            need[(g, r)] = hi
    nd = pd.DataFrame({f"{100*r:.0f}% real": {g: need[(g, r)] for g in [35, 36, 37, 38, 39, 40]} for r in rets})
    nd.index.name = "goal age"
    md += ["## 1. The math (no simulation): EUR per month you must save AFTER the job starts to hold EUR 1M at the goal age",
           md_table(nd, {c: "{:,.0f}" for c in nd.columns}),
           "Read: to hold EUR 1M at 38 with 5% real growth you must save about EUR " + f"{need[(38, 0.05)]:,.0f}/mo (= EUR {12*need[(38, 0.05)]:,.0f}/yr) from month {J}.", ""]
    Y38 = 38 - AGE0
    pre_dep = 1000 * J
    w38 = det(Y38, need[(38, 0.05)], 0.05)
    deposits = pre_dep + need[(38, 0.05)] * (Y38 * 12 - J) + BOOK0
    md += [f"At that saving level, {100*deposits/w38:.0f}% of the EUR 1M is money you put in; only {100*(1-deposits/w38):.0f}% is market growth (5% real).", ""]

    fig, ax = plt.subplots(1, 2, figsize=(15, 5.4))
    ages = AGE0 + np.arange(1, 14 * 12 + 1) / 12
    for S, col in ((3000, "#9aa5b1"), (5000, "#2a9d8f"), (80000 / 12, "#7b4fd3")):
        wp = []
        mr = 1.05 ** (1 / 12) - 1
        W, Wb = 0.0, BOOK0
        for k in range(14 * 12):
            W = (W + (1000.0 if k < J else S)) * (1 + mr); Wb *= 1 + mr
            wp.append(W + Wb)
        ax[0].plot(ages, wp, color=col, lw=2.2, label=f"save EUR {S:,.0f}/mo (EUR {12*S/1000:,.0f}k/yr) after the job starts")
    ax[0].axhline(TARGET, color="black", ls="--", lw=.9); ax[0].axvspan(35, 40, color="#f2a900", alpha=.12)
    ax[0].yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"{v/1e6:.1f}M"))
    ax[0].set_xlabel("your age"); ax[0].set_title("Money over time at 5% real growth (today's euros). Shaded = your goal window, age 35-40", fontsize=10)
    ax[0].legend(frameon=False, fontsize=8, loc="upper left")
    xs = np.array([35, 36, 37, 38, 39, 40])
    for r, col in ((0.0, "#9aa5b1"), (0.03, "#4c78a8"), (0.05, "#2a9d8f"), (0.07, "#7b4fd3"), (0.10, "#d1495b")):
        ax[1].plot(xs, [need[(g, r)] for g in xs], marker="o", color=col, label=f"{100*r:.0f}% real growth")
    ax[1].set_xlabel("age at which you want EUR 1M"); ax[1].set_ylabel("EUR per month to save after the job starts")
    ax[1].set_title("What you must save each month", fontsize=10); ax[1].legend(frameon=False, fontsize=8)
    ax[1].yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    fig.tight_layout(); fig.savefig(out / "01_the_math.png", dpi=130); plt.close(fig)

    # ---------------- 2. journeys at each goal age
    res = {}
    store = {}
    for g in GOAL_AGES:
        Y = g - AGE0
        m = Y * 12
        starts = np.arange(120, T - m + 1)
        Ih, Ib = idx_hist(starts, m), idx_boot(T, a.sims, m, rng)
        for scen, (AA, I, label) in {"hist": (A, Ih, "historical"), "boot": (A, Ib, "bootstrap"), "haircut": (hair, Ib, "bootstrap, US stocks -2pts/yr")}.items():
            SR = strat_returns(hair if scen == "haircut" else A, Y, I, with_wf=(scen == "hist"))
            Hit = AA["HiTec"].values[I]
            Wb = book_end(Hit)
            for name, R in SR.items():
                Wp, Wq = unit_ends(R, J)
                store[(g, scen, name)] = (Wb, Wp, Wq)
                res[(g, scen, name)] = {"P(success) S=5,000": float(((Wb + Wp + 5000 * Wq) >= TARGET).mean()),
                                        "P(success) S=6,667": float(((Wb + Wp + 6666.67 * Wq) >= TARGET).mean()),
                                        "P(success) S=3,000": float(((Wb + Wp + 3000 * Wq) >= TARGET).mean()),
                                        "median wealth S=5,000": float(np.median(Wb + Wp + 5000 * Wq)),
                                        "p10 wealth S=5,000": float(np.percentile(Wb + Wp + 5000 * Wq, 10)),
                                        "saving needed 80% (EUR/mo)": float(need_for(0.8, Wb, Wp, Wq)),
                                        "saving needed 90% (EUR/mo)": float(need_for(0.9, Wb, Wp, Wq))}
    df = pd.DataFrame(res).T
    df.index.names = ["goal age", "scenario", "Strategy"]
    fmtR = {c: "{:.0%}" for c in df.columns if c.startswith("P(")} | {"median wealth S=5,000": "{:,.0f}", "p10 wealth S=5,000": "{:,.0f}", "saving needed 80% (EUR/mo)": "{:,.0f}", "saving needed 90% (EUR/mo)": "{:,.0f}"}
    md += ["## 2. Journeys: chance of EUR 1M at the goal age (S = EUR saved per month after the job; 3,000 / 5,000 / 6,667 = EUR 80k a year)"]
    for g in GOAL_AGES:
        for scen, lab in (("hist", "Historical start months (about 6-10 independent periods)"), ("boot", "Block bootstrap"), ("haircut", "Bootstrap with US stock returns 2 points lower")):
            sub = df.xs((g, scen), level=(0, 1)).copy(); sub.index.name = "Strategy"
            md += [f"### Goal age {g} - {lab}", md_table(sub, fmtR), ""]

    # ---------------- 3. plan details at age 38 (full paths): age at 1M, pain
    g = 38; Y = g - AGE0; m = Y * 12
    Ib = idx_boot(T, a.sims, m, np.random.default_rng(a.seed + 1))
    SR = strat_returns(A, Y, Ib, with_wf=False)
    Hit = A["HiTec"].values[Ib]
    plan = plan_vec(m, J, 5000)
    full = {k: journey(R, Hit, plan) for k, R in SR.items()}
    paused = rolling_prod(Hit, 12) < -0.25
    paused[:, :12] = False
    fullp = {k: journey(R, Hit, plan, paused) for k, R in SR.items()}
    pr = {k: {"P(success)": float((v["end"] >= TARGET).mean()), "median wealth": float(np.median(v["end"])),
              "median age at 1M": float(np.nanmedian(AGE0 + v["hit"] / 12)) if (~np.isnan(v["hit"])).any() else np.nan,
              "worst vs money put in (p10)": float(np.percentile(v["min_ratio"], 10)), "final-3-yr drop (p10)": float(np.percentile(v["late_dd"], 10)),
              "P(success) if saving stops in tech busts": float((fullp[k]["end"] >= TARGET).mean()),
              "share of wealth that is deposits": float(np.median(v["contrib"] / v["end"]))} for k, v in full.items()}
    pr = pd.DataFrame(pr).T
    pr.index.name = "Strategy"
    md += [f"## 3. Detail at goal age {g}, S = EUR 5,000/mo after month {J}, bootstrap {a.sims} paths",
           md_table(pr, {"P(success)": "{:.0%}", "median wealth": "{:,.0f}", "median age at 1M": "{:.1f}", "worst vs money put in (p10)": "{:.2f}", "final-3-yr drop (p10)": "{:.0%}",
                         "P(success) if saving stops in tech busts": "{:.0%}", "share of wealth that is deposits": "{:.0%}"}),
           f"Share of months in which saving pauses in the tech-bust test: {100*float(paused.mean()):.0f}% (assumption).", ""]

    # how long until the 10k book matters
    md += [f"Today's EUR 10k book is about {100*float(np.median(full['Total market']['book']/full['Total market']['end'])):.1f}% of the wealth at age {g} (it is dwarfed by new savings).", ""]

    # ---------------- 4. tech dial at age 38
    dial = {}
    for t in (0.0, 0.10, 0.20, 0.30, 0.50, 1.0):
        R = tech_dial(A, Y, Ib, t)
        jr = journey(R, Hit, plan)
        Wp, Wq = unit_ends(R, J)
        Wb = book_end(Hit)
        dial[f"{100*t:.0f}%"] = {"P(success)": float((jr["end"] >= TARGET).mean()), "median wealth": float(np.median(jr["end"])), "p10 wealth": float(np.percentile(jr["end"], 10)),
                                 "worst vs money put in (p10)": float(np.percentile(jr["min_ratio"], 10)), "saving needed 80%": float(need_for(0.8, Wb, Wp, Wq))}
    dd = pd.DataFrame(dial).T
    dd.index.name = "tech satellite share of new money"
    md += [f"## 4. How big can the tech satellite be? (rest = 62.5% market / 37.5% steady; goal age {g}; S = 5,000)",
           md_table(dd, {"P(success)": "{:.0%}", "median wealth": "{:,.0f}", "p10 wealth": "{:,.0f}", "worst vs money put in (p10)": "{:.2f}", "saving needed 80%": "{:,.0f}"}), ""]

    # ---------------- 5. era split + walk-forward (12-year windows)
    starts = np.arange(120, T - m + 1)
    mid = (starts[0] + starts[-1]) // 2
    Ih = idx_hist(starts, m)
    SRh = strat_returns(A, Y, Ih)
    Hh = A["HiTec"].values[Ih]
    Wbh = book_end(Hh)
    rows = {}
    for k, R in SRh.items():
        Wp, Wq = unit_ends(R, J)
        e = Wbh + Wp + 5000 * Wq
        early, late = starts <= mid, starts > mid
        rows[k] = {"median wealth early": np.median(e[early]), "median wealth late": np.median(e[~early]),
                   "p10 early": np.percentile(e[early], 10), "p10 late": np.percentile(e[~early], 10),
                   "P(success) early": float((e[early] >= TARGET).mean()), "P(success) late": float((e[~early] >= TARGET).mean())}
    er = pd.DataFrame(rows).T
    er["rank early (p10)"] = er["p10 early"].rank(ascending=False)
    er["rank late (p10)"] = er["p10 late"].rank(ascending=False)
    rho = er["rank early (p10)"].corr(er["rank late (p10)"], method="spearman")
    er.index.name = "Strategy"
    md += [f"## 5. Era split at goal age {g} (S = 5,000): start months up to {A.index[mid]} vs after",
           md_table(er[["P(success) early", "P(success) late", "p10 early", "p10 late", "rank early (p10)", "rank late (p10)"]],
                    {"P(success) early": "{:.0%}", "P(success) late": "{:.0%}", "p10 early": "{:,.0f}", "p10 late": "{:,.0f}", "rank early (p10)": "{:.0f}", "rank late (p10)": "{:.0f}"}),
           f"Rank correlation of bad-case wealth, early vs late: {rho:.2f}.", ""]
    # rolling 12-year real return: how often did each asset lose money over 12 years?
    roll = {}
    for c, lab in (("Mkt", "US total market"), ("HiTec", "Tech sector"), ("NoDur", "Staples"), ("Hlth", "Health care"), ("Bond10", "10-yr bonds"), ("Bills", "T-bills")):
        r12 = (1 + A[c]).rolling(m).apply(np.prod, raw=True) ** (12 / m) - 1
        r12 = r12.dropna()
        roll[lab] = {"worst 12y real return/yr": 100 * r12.min(), "median": 100 * r12.median(), "best": 100 * r12.max(), "% of 12-year spans below 0": 100 * (r12 < 0).mean(), "% below 3%/yr": 100 * (r12 < 0.03).mean()}
    rl = pd.DataFrame(roll).T
    rl.index.name = "Asset"
    md += [f"### How often did a {Y}-year lump investment lose or lag? (real yearly return over every {Y}-year span since 1926)",
           md_table(rl, {c: "{:.1f}" for c in rl.columns}), ""]

    # ---------------- charts
    show = ["Total market", "Tech sector only", "Steady sectors (staples+health)", "Recommended mix", "60% market / 40% bonds", "T-bills only (safe)"]
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.2), sharey=True)
    for ax, gg in zip(axes, GOAL_AGES):
        for nme in show:
            ys = []
            for S in S_GRID:
                Wb, Wp, Wq = store[(gg, "boot", nme)]
                ys.append(float(((Wb + Wp + S * Wq) >= TARGET).mean()) * 100)
            ax.plot(S_GRID, ys, lw=2.4 if nme == "Recommended mix" else 1.6, color=C[nme], label=nme, ls="--" if "T-bills" in nme else "-")
        ax.axvline(80000 / 12, color="black", ls=":", lw=1); ax.text(80000 / 12 + 50, 4, "EUR 80k/yr", fontsize=8, rotation=90)
        ax.set_title(f"Goal: EUR 1M at age {gg}", fontsize=11); ax.set_xlabel("EUR saved per month after the job starts")
        ax.xaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    axes[0].set_ylabel("chance of reaching it (%)"); axes[0].legend(frameon=False, fontsize=8, loc="upper left")
    fig.suptitle("Chance of holding EUR 1M (today's money) vs how much you save (bootstrap of 100 years of history)", fontsize=12)
    fig.tight_layout(); fig.savefig(out / "02_chance_vs_saving.png", dpi=130); plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(15, 5.6), gridspec_kw={"width_ratios": [1.2, 1]})
    names = ["Total market", "Tech sector only", "Steady sectors (staples+health)", "Recommended mix", "60% market / 40% bonds", "Equal weight 10 industries", "Glide path (100% -> 70% stocks, last 4 yrs)", "T-bills only (safe)"]
    for i, nme in enumerate(names):
        age = AGE0 + full[nme]["hit"] / 12
        if np.isnan(age).mean() > .9:
            ax[0].text(33.2, i, "rarely reaches EUR 1M by 41", va="center", fontsize=8); continue
        lo, med, hi = np.nanpercentile(age, [10, 50, 90])
        ax[0].plot([lo, hi], [i, i], lw=7, alpha=.4, color=C.get(nme, "#4c78a8"), solid_capstyle="round")
        ax[0].scatter([med], [i], color="white", edgecolor="black", s=60, zorder=5); ax[0].text(hi + .2, i, f"median {med:.0f}", va="center", fontsize=8)
    ax[0].axvspan(35, 40, color="#f2a900", alpha=.12); ax[0].set_xlim(33, 42); ax[0].set_yticks(range(len(names)), [n.replace(" (100% -> 70% stocks, last 4 yrs)", "") for n in names], fontsize=8)
    ax[0].set_xlabel("age you first hold EUR 1M (bar = 10th-90th percentile)")
    ax[0].set_title(f"Saving EUR 5,000/mo after month {J}: when do you get there?", fontsize=10)
    for nme in names:
        if nme in pr.index:
            col = C.get(nme, "#4c78a8")
            Wb, Wp, Wq = store[(38, "boot", nme)] if (38, "boot", nme) in store else (None, None, None)
            if Wb is None:
                continue
            need80 = float(need_for(0.8, Wb, Wp, Wq))
            ax[1].scatter(100 * (1 - pr.loc[nme, "worst vs money put in (p10)"]), need80, s=130 if nme == "Recommended mix" else 70, color=col, edgecolor="white", zorder=5)
            ax[1].annotate(nme.split(" (")[0].replace(" 100% -> 70% stocks, last 4 yrs", ""), (100 * (1 - pr.loc[nme, "worst vs money put in (p10)"]), need80), xytext=(6, 8 if nme in ("Total market", "Steady sectors (staples+health)") else -10), textcoords="offset points", fontsize=8)
    ax[1].set_xlabel("PAIN: lowest point vs money put in, bad 1-in-10 case (% below)")
    ax[1].set_ylabel("COST: EUR/mo needed after the job for an 80% chance at 38")
    ax[1].set_title("Pain vs cost (lower-left is better)", fontsize=10)
    fig.tight_layout(); fig.savefig(out / "03_when_and_pain_vs_cost.png", dpi=130); plt.close(fig)

    fig, ax = plt.subplots(1, 3, figsize=(16, 4.6))
    xs = list(dd.index)
    ax[0].plot(xs, 100 * dd["P(success)"], marker="o", color="#2a9d8f"); ax[0].set_ylim(40, 80); ax[0].set_title("Chance of EUR 1M by 38 (S=5,000): basically flat", fontsize=10)
    ax[1].plot(xs, dd["p10 wealth"], marker="o", color="#4c78a8"); ax[1].set_title("A bad (1-in-10) outcome: wealth at 38, EUR", fontsize=10)
    ax[1].yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"{v/1000:,.0f}k"))
    ax[2].plot(xs, 100 * (1 - dd["worst vs money put in (p10)"]), marker="o", color="#d1495b"); ax[2].set_title("PAIN: lowest point vs money put in (% below)", fontsize=10)
    for a_ in ax:
        a_.set_xlabel("tech/AI/crypto-style satellite as % of NEW money")
    fig.suptitle("The tech dial: how much of the monthly money can go to your thesis?", fontsize=12)
    fig.tight_layout(); fig.savefig(out / "04_tech_dial.png", dpi=130); plt.close(fig)

    keys = ["Total market", "Tech sector only", "Steady sectors (staples+health)", "Recommended mix", "60% market / 40% bonds"]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    x = np.arange(len(keys))
    ax.bar(x - .2, [100 * pr.loc[k, "P(success)"] for k in keys], .4, color="#4c78a8", label="income steady")
    ax.bar(x + .2, [100 * pr.loc[k, "P(success) if saving stops in tech busts"] for k in keys], .4, color="#d1495b", label="saving stops when tech is in a bust")
    ax.set_xticks(x, [k.replace(" (staples+health)", "").replace(" / ", "/") for k in keys], fontsize=8); ax.set_ylabel("chance of EUR 1M by 38 (%)")
    ax.legend(frameon=False, fontsize=8); ax.set_title("If your income follows the tech cycle (AI job), the plan is weaker", fontsize=11)
    fig.tight_layout(); fig.savefig(out / "05_income_link.png", dpi=130); plt.close(fig)

    for f in ("05_walk_forward.png", "06_regime_flips.png"):
        src = ROOT / "reports" / "latest" / "longterm" / f
        if src.exists():
            shutil.copy(src, out / ("06_" + f if f.startswith("05") else "07_" + f))

    (out / "HORIZON.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
