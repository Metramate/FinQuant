"""Glass cannon vs steady compounders: does the swingy tech/crypto book out-earn Visa-style steady stocks?

    python scripts/compounders.py            # writes reports/latest/compounders/*.png and COMPOUNDERS.md

Four separate checks (each with its own pass/fail evidence):
 1. FACTS      real CAGR / volatility / worst fall of V, MA and a steady basket, plus "compounders that stopped".
 2. HISTORY    rolling 4-year outcomes (best / typical / worst) for steady basket, S&P 500, QQQ, SMH, BTC, ARKK
               and a proxy of YOUR current book (current weights, assets renormalised when young).
 3. SIMULATION where ~EUR 1,000 of new money goes: more of the same / HOOD+same / HOOD+steady / all steady,
               by block-bootstrapping real daily returns (joint, so crashes hit all sleeves together).
 4. BELIEFS    what you would have to believe: probability the swingy book beats the steady one vs its assumed
               yearly return and horizon (volatility drag means it must out-earn by roughly (sB^2 - sS^2)/2 just to tie).

Biases (read them): the steady list is picked with hindsight (survivors), so it is compared with the S&P 500 and with
fallen "compounders"; the book is today's holdings (also hindsight); the bootstrap sample (2021-08 on) holds one AI/crypto
boom and the 2022 crash; HOOD's own history is extreme. Not a forecast, not financial advice.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yfinance as yf  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from load_my_portfolio import load_holdings  # noqa: E402
from my_prices import fetch_prices  # noqa: E402
from portfolio_manager import ANN, build_book, md_table  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
STEADY = ["V", "MA", "SPGI", "MCO", "COST", "BRK-B", "ADP", "WM"]
REFS = ["SPY", "QQQ", "SMH", "ARKK", "BTC-USD", "MSFT"]
FALLEN = ["PYPL", "INTC", "KHC", "MMM"]
C = {"steady": "#2a9d8f", "book": "#7b4fd3", "spy": "#8d99ae", "qqq": "#4c78a8", "smh": "#1d3557", "btc": "#f2a900",
     "arkk": "#d1495b", "hood": "#e76f51", "V": "#1a759f", "MA": "#e63946"}


# ------------------------------------------------------------------ data
def download(tickers, start):
    cache = ROOT / ".cache" / "prices"
    cache.mkdir(parents=True, exist_ok=True)
    f = cache / (hashlib.md5((",".join(sorted(tickers)) + start + dt.date.today().isoformat()).encode()).hexdigest()[:16] + ".pkl")
    if f.exists():
        return pd.read_pickle(f)
    p = yf.download(tickers, start=start, auto_adjust=False, progress=False)["Adj Close"]
    p.index = pd.to_datetime(p.index).tz_localize(None)
    p.to_pickle(f)
    return p


def stats(r: pd.Series) -> dict:
    r = r.dropna()
    cum = (1 + r).cumprod()
    yrs = len(r) / ANN
    dd = cum / cum.cummax() - 1
    under = (dd < 0).astype(int)
    grp = (under.diff().fillna(0) != 0).cumsum()
    longest = int(under.groupby(grp).sum().max()) if under.any() else 0
    cal = (1 + r).groupby(r.index.year).prod() - 1
    return {"cagr": 100 * (cum.iloc[-1] ** (1 / yrs) - 1), "vol": 100 * r.std() * np.sqrt(ANN), "maxdd": 100 * dd.min(),
            "underwater_yrs": longest / ANN, "worst_year": 100 * cal.min(), "pos_years": 100 * (cal > 0).mean()}


def rolling_ann(r: pd.Series, years: float) -> pd.Series:
    h = int(years * ANN)
    cum = (1 + r.fillna(0)).cumprod()
    out = (cum.shift(-h) / cum) ** (1 / years) - 1
    return out.dropna()


# ------------------------------------------------------------------ sims
def bootstrap(R: np.ndarray, horizon: int, sims: int, block: int, rng) -> np.ndarray:
    """Joint block bootstrap of rows of R (T x k) -> (sims, horizon, k)."""
    T = R.shape[0]
    nb = int(np.ceil(horizon / block))
    starts = rng.integers(0, T - block, size=(sims, nb))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(sims, -1)[:, :horizon]
    return R[idx]


def prob_beats(mu_b, sig_b, mu_s, sig_s, rho, years, sims, rng):
    """P(wealth of risky sleeve B > wealth of steady sleeve S) with annual lognormal returns."""
    m = np.array([np.log(1 + mu_b) - sig_b ** 2 / 2 * 0, np.log(1 + mu_s)])  # placeholders, replaced below
    # parametrise by arithmetic mean mu (annual): log-drift = ln(1+mu) - 0.5*ln(1+(sig/(1+mu))^2); sd = sqrt(ln(1+(sig/(1+mu))^2))
    def lp(mu, sig):
        v = np.log(1 + (sig / (1 + mu)) ** 2)
        return np.log(1 + mu) - v / 2, np.sqrt(v)
    mb, sb = lp(mu_b, sig_b)
    ms, ss = lp(mu_s, sig_s)
    z1 = rng.standard_normal((sims, years))
    z2 = rho * z1 + np.sqrt(1 - rho ** 2) * rng.standard_normal((sims, years))
    lb = (mb + sb * z1).sum(axis=1)
    ls = (ms + ss * z2).sum(axis=1)
    return float((lb > ls).mean())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--new-eur", type=float, default=1000.0)
    ap.add_argument("--hood-pct", type=float, default=2.5, help="HOOD as %% of the book after adding the new money")
    ap.add_argument("--years", type=int, default=4)
    ap.add_argument("--sims", type=int, default=4000)
    ap.add_argument("--rf", type=float, default=0.04)
    ap.add_argument("--mu-b", type=float, default=0.15, help="sober case: assumed average yearly return of your book")
    ap.add_argument("--mu-s", type=float, default=0.12, help="sober case: steady basket")
    ap.add_argument("--mu-h", type=float, default=0.15, help="sober case: HOOD")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default=str(ROOT / "reports" / "latest" / "compounders"))
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    md = ["# Glass cannon vs steady compounders", ""]

    # ---------------- load
    allp = download(STEADY + REFS + FALLEN + ["HOOD", "EURUSD=X"], "2010-01-01")
    cal = allp["SPY"].dropna().index
    P = allp.reindex(cal).ffill(limit=5)
    R = P.pct_change()
    eurusd = float(allp["EURUSD=X"].dropna().iloc[-1])

    df = load_holdings()
    risky, cash, book, _ = build_book(df, fetch_prices(df, "2024-01-01"))
    long = fetch_prices(df, "2014-09-01")
    long = long.rename(columns=dict(zip(df["yahoo_ticker"], df["ticker"]))).reindex(cal).ffill(limit=5)
    rl = long[risky.index].pct_change()
    w = risky["w_sleeve"]
    avail = rl.notna()
    cov_w = (avail * w).sum(axis=1)
    book_r = ((rl.fillna(0) * w).sum(axis=1) / cov_w.replace(0, np.nan))
    book_r = book_r[cov_w >= 0.90]  # only when >= 90% of today's weights exist
    steady_r = R[STEADY].mean(axis=1).dropna()
    book_start = book_r.index[0]

    # ---------------- 1. facts
    T = {}
    for lab, r in {"Visa": R["V"], "Mastercard": R["MA"], "Steady basket (8 stocks)": steady_r, "S&P 500": R["SPY"], "Nasdaq-100 (QQQ)": R["QQQ"],
                   "Semis (SMH)": R["SMH"], "Bitcoin": R["BTC-USD"], "ARKK (innovation ETF)": R["ARKK"],
                   "PayPal": R["PYPL"], "Intel": R["INTC"], "Kraft Heinz": R["KHC"], "3M": R["MMM"]}.items():
        T[lab] = stats(r[r.index >= "2016-01-01"])
    T[f"YOUR book (proxy, since {book_start.date()})"] = stats(book_r)
    facts = pd.DataFrame(T).T
    md += ["## 1. Facts (2016 on, dividends included; book proxy since " + str(book_start.date()) + ")",
           md_table(facts.rename_axis("Asset"), {c: "{:.1f}" for c in facts.columns}), ""]
    v21 = stats(R["V"][R.index >= "2021-01-01"])["cagr"]
    m21 = stats(R["MA"][R.index >= "2021-01-01"])["cagr"]
    md += [f"Visa / Mastercard since 2021: {v21:.1f}% / {m21:.1f}% a year (vs 18% / 20% since 2016). 'About 20%' depended on the start date.", ""]

    # D1 growth since 2016
    fig, ax = plt.subplots(1, 2, figsize=(15, 6))
    s16 = R.index >= "2016-01-01"
    series = {"Steady basket": (steady_r, C["steady"], 3), "Visa": (R["V"], C["V"], 1.3), "Mastercard": (R["MA"], C["MA"], 1.3),
              "S&P 500": (R["SPY"], C["spy"], 2), "Nasdaq-100": (R["QQQ"], C["qqq"], 2), "Semis (SMH)": (R["SMH"], C["smh"], 1.5), "Bitcoin": (R["BTC-USD"], C["btc"], 1.5)}
    for lab, (r, col, lw) in series.items():
        g = 10000 * (1 + r[r.index >= "2016-01-01"].fillna(0)).cumprod()
        ax[0].plot(g, color=col, lw=lw, label=f"{lab}  ${g.iloc[-1]:,.0f}")
    ax[0].set_yscale("log")
    ax[0].yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax[0].set_yticks([10000, 30000, 100000, 300000, 1000000])
    ax[0].yaxis.set_minor_formatter(mt.NullFormatter())
    ax[0].set_title("What $10,000 put in at the start of 2016 became\n(log scale: equal steps = equal % growth)", fontsize=11)
    ax[0].legend(frameon=False, fontsize=8, loc="upper left")
    for lab, col in (("Visa", C["V"]), ("Mastercard", C["MA"])):
        pass
    fall = {"Visa": R["V"], "Mastercard": R["MA"], "PayPal": R["PYPL"], "Intel": R["INTC"], "Kraft Heinz": R["KHC"], "3M": R["MMM"]}
    cols = [C["V"], C["MA"], "#d1495b", "#6c757d", "#adb5bd", "#e9a8a0"]
    for (lab, r), col in zip(fall.items(), cols):
        g = 10000 * (1 + r[r.index >= "2016-01-01"].fillna(0)).cumprod()
        ax[1].plot(g, color=col, lw=2 if lab in ("Visa", "Mastercard") else 1.4, label=f"{lab}  ${g.iloc[-1]:,.0f}")
    ax[1].set_title("'Steady compounders' that stopped compounding\n(the same 10-year start: survivors are only visible afterwards)", fontsize=11)
    ax[1].yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"${v:,.0f}"))
    ax[1].legend(frameon=False, fontsize=8, loc="upper left")
    fig.tight_layout()
    fig.savefig(out / "01_growth_and_fallen.png", dpi=130)
    plt.close(fig)

    # D2 pain chart
    fig, ax = plt.subplots(figsize=(13, 5.2))
    for lab, r, col in (("Steady basket", steady_r, C["steady"]), ("S&P 500", R["SPY"], C["spy"]), ("Nasdaq-100", R["QQQ"], C["qqq"]), ("YOUR book (proxy)", book_r, C["book"])):
        r = r[r.index >= book_start]
        cum = (1 + r.fillna(0)).cumprod()
        dd = cum / cum.cummax() - 1
        ax.plot(100 * dd, color=col, lw=2.2 if "YOUR" in lab else 1.4, label=f"{lab}  (worst {100*dd.min():.0f}%)")
    ax.set_title("Pain chart: how far below its previous peak each one was, since " + str(book_start.date()), fontsize=11)
    ax.set_ylabel("% below peak")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(out / "02_pain_chart.png", dpi=130)
    plt.close(fig)
    tr = stats(book_r)
    ts = stats(steady_r[steady_r.index >= book_start])
    md += [f"Since {book_start.date()}: your-book proxy {tr['cagr']:.0f}%/yr, vol {tr['vol']:.0f}%, worst fall {tr['maxdd']:.0f}%, longest time under water {tr['underwater_yrs']:.1f} yrs; "
           f"steady basket {ts['cagr']:.0f}%/yr, vol {ts['vol']:.0f}%, worst fall {ts['maxdd']:.0f}%, underwater {ts['underwater_yrs']:.1f} yrs.", ""]

    # ---------------- 2. rolling 4-year outcomes
    H = a.years
    cand = {"Steady basket": steady_r, "S&P 500": R["SPY"], "Nasdaq-100": R["QQQ"], "Semis (SMH)": R["SMH"], "ARKK": R["ARKK"][R["ARKK"].notna()],
            "Bitcoin": R["BTC-USD"][R["BTC-USD"].notna()], "YOUR book (proxy)": book_r}
    roll = {k: rolling_ann(v.dropna(), H) for k, v in cand.items()}
    rows = {k: {"worst": 100 * s.min(), "p10": 100 * s.quantile(.1), "median": 100 * s.median(), "p90": 100 * s.quantile(.9), "best": 100 * s.max(),
                "pct_neg": 100 * (s < 0).mean(), "n_start_days": len(s), "from": str(s.index[0].date())} for k, s in roll.items()}
    rt = pd.DataFrame(rows).T
    fig, ax = plt.subplots(figsize=(12, 5.8))
    order = list(rt.index)
    colors = [C["steady"], C["spy"], C["qqq"], C["smh"], C["arkk"], C["btc"], C["book"]]
    for i, (k, c) in enumerate(zip(order, colors)):
        ax.plot([i, i], [rt.loc[k, "worst"], rt.loc[k, "best"]], color=c, lw=3, alpha=.35, solid_capstyle="round")
        ax.plot([i, i], [rt.loc[k, "p10"], rt.loc[k, "p90"]], color=c, lw=10, alpha=.75, solid_capstyle="butt")
        ax.scatter([i], [rt.loc[k, "median"]], color="white", edgecolor="black", s=70, zorder=5)
        ax.text(i + .12, rt.loc[k, "median"], f"{rt.loc[k,'median']:.0f}%", va="center", fontsize=8)
    ax.axhline(0, color="black", lw=.8)
    ax.set_xticks(range(len(order)), [o.replace(" (", "\n(") for o in order], fontsize=8)
    ax.set_ylabel("average yearly return over a 4-year hold (%)")
    ax.set_title("If you had held for 4 years: worst-to-best (thin line), typical range (thick bar), median (dot)\nStarts on every trading day since each asset's own start", fontsize=11)
    fig.tight_layout()
    fig.savefig(out / "03_four_year_outcomes.png", dpi=130)
    plt.close(fig)
    # head to head on identical dates
    both = pd.concat([roll["YOUR book (proxy)"], roll["Steady basket"]], axis=1, keys=["book", "steady"]).dropna()
    win = float((both["book"] > both["steady"]).mean())
    md += ["## 2. Rolling 4-year holds (annualised %)", md_table(rt.rename_axis("Asset"), {c: "{:.1f}" for c in ("worst","p10","median","p90","best","pct_neg")} | {"n_start_days": "{:.0f}"}), "",
           f"Head to head on identical start dates since {both.index[0].date()}: your-book proxy beat the steady basket in {100*win:.0f}% of {len(both)} overlapping 4-year windows "
           f"(median gap {100*(both['book']-both['steady']).median():+.1f}pt/yr; worst gap {100*(both['book']-both['steady']).min():+.1f}pt). These windows overlap heavily: effectively ~1-2 independent samples.", ""]

    # ---------------- 3. simulation of the new money
    common = pd.concat([book_r.rename("B"), steady_r.rename("S"), R["HOOD"].rename("H")], axis=1).dropna()
    common = common[common.index >= R["HOOD"].dropna().index[0]]
    Rm = common.values  # columns B,S,H
    new_usd = a.new_eur * eurusd
    book_now = risky["value"].sum()
    total0 = book_now + cash + new_usd
    h_usd = a.hood_pct / 100 * total0
    scen = {
        "Do nothing (new money sits in cash)": dict(B=book_now, S=0, H=0, cash=cash + new_usd),
        "A. More of the same (glass cannon)": dict(B=book_now + new_usd, S=0, H=0, cash=cash),
        f"B. HOOD {a.hood_pct:g}% + rest more of the same": dict(B=book_now + new_usd - h_usd, S=0, H=h_usd, cash=cash),
        f"C. HOOD {a.hood_pct:g}% + rest steady compounders": dict(B=book_now, S=new_usd - h_usd, H=h_usd, cash=cash),
        "D. All new money into steady compounders": dict(B=book_now, S=new_usd, H=0, cash=cash),
    }
    horizon = H * ANN
    sober_mu = np.array([a.mu_b, a.mu_s, a.mu_h])
    cases = {"history": Rm, "sober": Rm - Rm.mean(axis=0) + sober_mu / ANN}  # sober: same crash shapes, assumed average returns
    cash_g = (1 + a.rf / ANN) ** np.arange(1, horizon + 1)
    RES, PATHS = {}, {}
    for case, Rc in cases.items():
        rng_c = np.random.default_rng(a.seed)
        growth = np.cumprod(1 + bootstrap(Rc, horizon, a.sims, 21, rng_c), axis=1)
        res, paths = {}, {}
        for name, amt in scen.items():
            v = amt["B"] * growth[:, :, 0] + amt["S"] * growth[:, :, 1] + amt["H"] * growth[:, :, 2] + amt["cash"] * cash_g[None, :]
            paths[name] = v
            mdd = (v / np.maximum.accumulate(v, axis=1) - 1).min(axis=1)
            end = v[:, -1]
            res[name] = {"median_end": np.median(end), "p10_end": np.percentile(end, 10), "p90_end": np.percentile(end, 90),
                         "P(end<start)": float((end < total0).mean()), "median_maxdd": 100 * np.median(mdd)}
        ref = paths["D. All new money into steady compounders"][:, -1]
        for name in scen:
            res[name]["P(beats D)"] = float((paths[name][:, -1] > ref).mean())
        RES[case], PATHS[case] = pd.DataFrame(res).T, paths
    sample_note = f"{common.index[0].date()} to {common.index[-1].date()} ({len(common)} days)"
    fmt = {c: "{:,.0f}" for c in ("median_end", "p10_end", "p90_end")} | {"P(end<start)": "{:.0%}", "P(beats D)": "{:.0%}", "median_maxdd": "{:.0f}%"}
    md += [f"## 3. Simulation: {H}-year paths for ~EUR {a.new_eur:,.0f} (= ${new_usd:,.0f} at EURUSD {eurusd:.3f}) added to a ${book_now+cash:,.0f} book",
           f"Bootstrap of real joint daily returns (21-day blocks, {a.sims} paths, sample {sample_note}). Start value ${total0:,.0f}. "
           f"'History' replays what 2021-26 delivered to today's holdings (hindsight-flattered: book {100*Rm[:,0].mean()*ANN:.0f}%/yr, steady {100*Rm[:,1].mean()*ANN:.0f}%/yr, HOOD {100*Rm[:,2].mean()*ANN:.0f}%/yr average). "
           f"'Sober' keeps the same crash shapes but ASSUMES average returns of {100*a.mu_b:.0f}% (book), {100*a.mu_s:.0f}% (steady), {100*a.mu_h:.0f}% (HOOD): my assumptions.", "",
           "### History replay", md_table(RES["history"].rename_axis("Scenario"), fmt), "", "### Sober case", md_table(RES["sober"].rename_axis("Scenario"), fmt), ""]

    names = list(scen)[1:4]
    fig, axes = plt.subplots(2, 3, figsize=(16, 9), sharex=True)
    for row, (case, ttl) in enumerate((("sober", "SOBER case (assumed average returns)"), ("history", "HISTORY replay (hindsight-flattered)"))):
        ymax = max(np.percentile(PATHS[case][n], 90, axis=0).max() for n in names) * 1.05
        for ax, name in zip(axes[row], names):
            v = PATHS[case][name]
            x = np.arange(horizon) / ANN
            ax.fill_between(x, np.percentile(v, 10, axis=0), np.percentile(v, 90, axis=0), color=C["book"], alpha=.18, label="middle 80% of outcomes")
            ax.fill_between(x, np.percentile(v, 25, axis=0), np.percentile(v, 75, axis=0), color=C["book"], alpha=.32, label="middle 50%")
            ax.plot(x, np.median(v, axis=0), color="black", lw=2, label="median")
            ax.axhline(total0, color="gray", ls="--", lw=.8)
            r_ = RES[case].loc[name]
            ax.set_title((ttl + "\n" if name == names[0] else "") + name + f"\nmedian \\${r_['median_end']:,.0f} · 1-in-10 bad \\${r_['p10_end']:,.0f} · ends below start {100*r_['P(end<start)']:.0f}%", fontsize=8.5)
            ax.set_ylim(0, ymax)
            ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v_, _: f"${v_/1000:,.0f}k"))
        axes[row][0].legend(frameon=False, fontsize=8, loc="upper left")
    for ax in axes[1]:
        ax.set_xlabel("years from now")
    fig.suptitle(f"Where the whole book could be in {H} years: replaying real market days (not a prediction)", fontsize=12)
    fig.tight_layout()
    fig.savefig(out / "04_fan_charts.png", dpi=130)
    plt.close(fig)

    fig, ax = plt.subplots(1, 3, figsize=(16, 4.8))
    opt = list(scen)[1:]
    labs = ["A\nmore same", "B\nHOOD+same", "C\nHOOD+steady", "D\nall steady"]
    xs = np.arange(len(opt))
    for a_, key, ttl in zip(ax, ["median_end", "p10_end", "median_maxdd"], ["Typical result after 4 years (median)", "Bad case (1-in-10)", "Typical worst drop on the way"]):
        for off, case, hatch, alpha in ((-.2, "sober", "", .95), (.2, "history", "//", .55)):
            vals = [RES[case].loc[n, key] for n in opt]
            bars = a_.bar(xs + off, vals, .38, color=[C["book"], C["hood"], C["steady"], "#264653"], hatch=hatch, alpha=alpha, edgecolor="white")
            for xi, v in zip(xs + off, vals):
                a_.text(xi, v, (f"${v/1000:,.1f}k" if "end" in key else f"{v:.0f}%"), ha="center", va="bottom" if v >= 0 else "top", fontsize=7)
        a_.set_xticks(xs, labs, fontsize=8)
        a_.set_title(ttl, fontsize=10)
    fig.suptitle(f"The EUR {a.new_eur:,.0f} choice over {H} years. Solid = sober case, hatched = history replay. New money = only {100*new_usd/total0:.0f}% of the book", fontsize=11)
    fig.tight_layout()
    fig.savefig(out / "05_options_compared.png", dpi=130)
    plt.close(fig)

    # ---------------- 4. what you would have to believe
    vol_b = stats(common["B"])["vol"] / 100
    vol_s = stats(common["S"])["vol"] / 100
    rho = float(common["B"].corr(common["S"]))
    mu_s = 0.14
    grid_mu = np.arange(0.08, 0.341, 0.02)
    yrs_list = [1, 2, 4, 8, 15]
    Z = np.array([[prob_beats(m, vol_b, mu_s, vol_s, rho, y, 20000, rng) for m in grid_mu] for y in yrs_list])
    be = mu_s + (vol_b ** 2 - vol_s ** 2) / 2
    fig, ax = plt.subplots(figsize=(11.5, 5.2))
    im = ax.imshow(100 * Z, origin="lower", cmap="RdYlGn", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(len(grid_mu)), [f"{100*m:.0f}%" for m in grid_mu])
    ax.set_yticks(range(len(yrs_list)), [f"{y} yr" for y in yrs_list])
    for i in range(len(yrs_list)):
        for j in range(len(grid_mu)):
            ax.text(j, i, f"{100*Z[i,j]:.0f}", ha="center", va="center", fontsize=8)
    ax.set_xlabel("average yearly return you BELIEVE the swingy book will earn")
    ax.set_ylabel("how long you hold")
    ax.set_title(f"Chance (%) the swingy book ends up richer than a steady one earning {100*mu_s:.0f}%/yr\n"
                 f"(swingy vol {100*vol_b:.0f}%, steady vol {100*vol_s:.0f}%, correlation {rho:.2f}; they tie around {100*be:.0f}%)", fontsize=10)
    fig.colorbar(im, label="% chance swingy wins")
    fig.tight_layout()
    fig.savefig(out / "06_what_you_must_believe.png", dpi=130)
    plt.close(fig)
    md += ["## 4. What you must believe", f"Swingy sleeve vol {100*vol_b:.0f}%, steady {100*vol_s:.0f}%, correlation {rho:.2f}. Volatility drag: to merely TIE a steady {100*mu_s:.0f}%/yr sleeve, the swingy one must "
           f"average ~{100*be:.0f}%/yr (arithmetic) i.e. +{100*(be-mu_s):.0f}pt, before it is ahead. Table of P(swingy wins), rows = years, columns = believed yearly return:",
           md_table(pd.DataFrame(100 * Z, index=[f"{y}y" for y in yrs_list], columns=[f"{100*m:.0f}%" for m in grid_mu]).round(0).rename_axis("hold")), ""]

    # EURUSD note
    fx = allp["EURUSD=X"].dropna()
    fx4 = (fx / fx.shift(4 * 365)).dropna() - 1
    md += [f"## EUR note", f"EURUSD now {eurusd:.3f}. Over rolling 4-year periods since 2010 the euro moved between {100*fx4.min():.0f}% and {100*fx4.max():+.0f}% against the dollar: "
           f"as a euro investor in dollar assets you carry that on top: if the euro rises 13% against the dollar, the same dollar holdings are worth about {100*(1-1/1.13):.0f}% less in euros; if it falls 29%, they are worth about {100*(1/0.71-1):.0f}% more."]
    (out / "COMPOUNDERS.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
