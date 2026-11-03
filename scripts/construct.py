"""Professional portfolio construction for the personal book: walk-forward validation + constrained optimisation.

    python scripts/construct.py --validate     # out-of-sample test of construction methods (monthly refit, trailing 3y, costs)
    python scripts/construct.py --build        # optimise target weights per stage -> data/targets_optimised.json + reports/latest/construction.md

What it does
  1. VALIDATE: on 2021-2026 daily data (history proxies for young tickers), every month re-estimate from only the previous 3 years
     and hold for a month: equal weight, my hand-set plan weights, FinQuant max-Sharpe / min-variance (with a position cap),
     equal-risk-contribution, and RISK BUDGETING by sleeve (your policy in data/policy.json). Compare Sharpe, drawdown, turnover.
  2. BUILD: for each stage, solve the risk-budget problem with Ledoit-Wolf shrunk covariance, per-position caps, and NO-SELL floors
     (final weight at the end of the stage cannot be below what you already hold). Output = new targets for monthly_plan.py.

Honest limits: the 22 names are chosen with hindsight (same for every method, so compare methods, not levels); the test window holds
one AI/crypto boom and the 2022 bear; covariance is estimated, not known; budgets are policy choices, not facts. Not advice.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yfinance as yf  # noqa: E402
from scipy.optimize import minimize  # noqa: E402
from sklearn.covariance import LedoitWolf  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from finquant.efficient_frontier import EfficientFrontier  # noqa: E402
from load_my_portfolio import load_holdings  # noqa: E402
from monthly_plan import current_state, eurusd, extended_holdings  # noqa: E402
from my_prices import splice_proxy  # noqa: E402
from portfolio_manager import ANN, md_table  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
POLICY = json.loads((ROOT / "data" / "policy.json").read_text())
TARGETS = json.loads((ROOT / "data" / "targets.json").read_text())
YAHOO = {"BTC": "BTC-USD", "ETH": "ETH-USD", "UNI": "UNI7083-USD", "NEAR": "NEAR-USD", "QQQM": "QQQM", "SMH": "SMH", "NVDA": "NVDA", "SKHY": "SKHY",
         "QTUM": "QTUM", "VST": "VST", "ITA": "ITA", "NLR": "NLR", "UFO": "UFO", "LLY": "LLY", "HOOD": "HOOD", "GEV": "GEV", "PICK": "PICK",
         "INDA": "INDA", "CRSP": "CRSP", "V": "V", "MA": "MA", "WORLD": "VT", "VEU": "VEU"}  # WORLD is priced with VT (all-world, USD) for history
COST = {"crypto": 0.0025}  # one-way cost: crypto 25bp, everything else 10bp (assumptions)
NAMES = [n for n in POLICY["sleeves"] if n not in POLICY.get("exclude", [])]


# ------------------------------------------------------------------ data
def panel(start="2017-06-01") -> pd.DataFrame:
    cache = ROOT / ".cache" / "construct"
    cache.mkdir(parents=True, exist_ok=True)
    extra = ["QQQ", "000660.KS", "KRW=X"]
    tick = sorted(set(YAHOO.values()) | set(extra))
    f = cache / (hashlib.md5((",".join(tick) + start + dt.date.today().isoformat()).encode()).hexdigest()[:16] + ".pkl")
    if f.exists():
        return pd.read_pickle(f)
    px = yf.download(tick, start=start, auto_adjust=False, progress=False)["Adj Close"]
    px.index = pd.to_datetime(px.index).tz_localize(None)
    cal = px["QQQ"].dropna().index
    P = px.reindex(cal).ffill(limit=5)
    out = pd.DataFrame(index=cal)
    for n in POLICY["sleeves"]:
        out[n] = P[YAHOO[n]]
    # QQQM <- QQQ (same market, near-identical): scale at the junction
    q, qq = out["QQQM"].dropna(), P["QQQ"]
    out["QQQM"] = pd.concat([qq.loc[: q.index[0] - pd.Timedelta(days=1)] * (q.iloc[0] / qq.loc[q.index[0]]), q])
    # SKHY <- SK hynix on the Korea exchange in USD (see my_prices.py)
    usd = P["000660.KS"] / P["KRW=X"].ffill()
    out["SKHY"] = splice_proxy(P["SKHY"].dropna(), usd, cal).reindex(cal)
    out.to_pickle(f)
    return out


def lw_cov(R: pd.DataFrame) -> np.ndarray:
    return LedoitWolf().fit(R.values).covariance_ * ANN


def risk_contrib(w, cov):
    v = w @ cov @ w
    return w * (cov @ w) / v


# ------------------------------------------------------------------ construction methods
def solve(obj, n, lo, hi, x0=None):
    x0 = np.clip(np.ones(n) / n, lo, hi) if x0 is None else x0
    res = minimize(obj, x0 / x0.sum(), method="SLSQP", bounds=list(zip(lo, hi)), constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}],
                   options={"maxiter": 400, "ftol": 1e-12})
    return res.x


def budgets_for(cols: list[str], pol=POLICY) -> np.ndarray:
    """Risk budget per asset: sleeve budget (renormalised over sleeves present) split by within-sleeve shares (equal if not given)."""
    sl = {c: pol["sleeves"][c] for c in cols}
    present = {s: pol["risk_budget_pct"][s] for s in set(sl.values())}
    tot = sum(present.values())
    b = np.zeros(len(cols))
    for s, bs in present.items():
        members = [c for c in cols if sl[c] == s]
        shares = {c: pol["within_sleeve_pct"].get(s, {}).get(c, None) for c in members}
        if any(v is None for v in shares.values()):
            shares = {c: 1.0 for c in members}
        z = sum(shares.values())
        for c in members:
            b[cols.index(c)] = (bs / tot) * shares[c] / z
    return b / b.sum()


def w_equal(R, cols, **k):
    return np.ones(len(cols)) / len(cols)


def w_plan(R, cols, **k):
    wt = TARGETS["stages"][-1]["weights"]
    w = np.array([wt.get(c, 0.0) for c in cols])
    return w / w.sum()


def caps(n, cap):
    hi = max(cap, 1.5 / n)
    return np.zeros(n), np.full(n, hi)


def w_fq(R, cols, kind, cap=0.15, **k):
    n = len(cols)
    mu = R.mean() * ANN
    mu = 0.5 * mu + 0.5 * mu.mean()
    cov = pd.DataFrame(lw_cov(R), index=cols, columns=cols)
    ef = EfficientFrontier(mu, cov, risk_free_rate=0.03, freq=ANN)
    lo, hi = caps(n, cap)
    ef.bounds = tuple(zip(lo, hi))
    df = ef.maximum_sharpe_ratio() if kind == "maxsharpe" else ef.minimum_volatility()
    w = df["Allocation"].reindex(cols).values.astype(float)
    return np.clip(w, 0, None) / np.clip(w, 0, None).sum()


def w_erc(R, cols, cap=0.15, **k):
    n = len(cols); cov = lw_cov(R); lo, hi = caps(n, cap)
    return solve(lambda w: ((risk_contrib(w, cov) - 1 / n) ** 2).sum() * 1e4, n, lo, hi)


def hi_for(cols):
    sm = POLICY.get("sleeve_max_pct", {})
    return np.array([min(POLICY["single_max_pct"], sm.get(POLICY["sleeves"][c], 100)) / 100 for c in cols])


def w_rb(R, cols, cap=0.15, **k):
    n = len(cols); cov = lw_cov(R); lo = np.zeros(n); hi = np.maximum(hi_for(cols), 1.5 / n); b = budgets_for(cols)
    return solve(lambda w: (((risk_contrib(w, cov) - b) / b) ** 2).sum(), n, lo, hi)


METHODS = {"Equal weight": w_equal, "Hand-set plan weights": w_plan,
           "FinQuant max-Sharpe (cap 15%)": lambda R, c, **k: w_fq(R, c, "maxsharpe"),
           "FinQuant min-variance (cap 15%)": lambda R, c, **k: w_fq(R, c, "minvar"),
           "Equal risk contribution (cap 15%)": w_erc, "Risk budgets by sleeve + position caps": w_rb}


# ------------------------------------------------------------------ walk-forward
def walk_forward(P: pd.DataFrame, start="2021-06-01", lookback=756, minhist=378):
    R = P.pct_change()
    idx = R.index
    me = pd.Series(idx, index=idx).groupby([idx.year, idx.month]).last().values
    reb = [d for d in me if d >= pd.Timestamp(start) and d < idx[-1]]
    out = {m: [] for m in METHODS}
    turn = {m: [] for m in METHODS}
    nass = []
    prev = {m: pd.Series(dtype=float) for m in METHODS}
    for k, d in enumerate(reb):
        i = idx.get_loc(d)
        win = R.iloc[max(1, i - lookback + 1): i + 1]
        avail = [c for c in R.columns if win[c].notna().sum() >= minhist and pd.notna(R.iloc[i][c])]
        sub = win[avail].dropna()
        while len(sub) < minhist and len(avail) > 3:
            first = {c: win[c].first_valid_index() for c in avail}
            avail.remove(max(first, key=first.get))
            sub = win[avail].dropna()
        nxt = reb[k + 1] if k + 1 < len(reb) else idx[-1]
        days = idx[(idx > d) & (idx <= nxt)]
        nass.append(len(avail))
        for m, fn in METHODS.items():
            w = pd.Series(fn(sub, avail), index=avail)
            drift = prev[m].reindex(avail).fillna(0.0)
            tv = (w - drift).abs()
            cost = float(sum(tv[c] * (COST["crypto"] if POLICY["sleeves"][c] == "crypto" else 0.001) for c in avail))
            turn[m].append(float(tv.sum()) / 2)
            cur = w.copy()
            first = True
            for day in days:
                r = R.loc[day, avail].fillna(0.0)
                port = float(cur @ r)
                if first:
                    port -= cost
                    first = False
                out[m].append((day, port))
                cur = cur * (1 + r) / (1 + port + (0 if True else 0))
            prev[m] = cur / cur.sum()
    series = {m: pd.Series(dict(v)) for m, v in out.items()}
    return series, {m: 12 * float(np.mean(v)) for m, v in turn.items()}, float(np.mean(nass))


def perf(s: pd.Series, rf=0.03) -> dict:
    cum = (1 + s).cumprod()
    yrs = len(s) / ANN
    cagr = cum.iloc[-1] ** (1 / yrs) - 1
    vol = s.std() * np.sqrt(ANN)
    return {"CAGR %": 100 * cagr, "vol %": 100 * vol, "Sharpe": (cagr - rf) / vol, "max drawdown %": 100 * (cum / cum.cummax() - 1).min(),
            "worst 20d %": 100 * ((1 + s).rolling(20).apply(np.prod, raw=True) - 1).min()}


# ------------------------------------------------------------------ build
def build(P: pd.DataFrame):
    R = P.pct_change().iloc[-756:]
    df = load_holdings()
    dfe = extended_holdings(df, TARGETS)
    values, price, cash, px = current_state(dfe)
    fx = eurusd()
    stage_names = {"A": [n for n in NAMES if n not in ("GEV", "PICK", "INDA", "CRSP")],
                   "B": [n for n in NAMES if n not in ("INDA", "CRSP")], "C": NAMES}
    out_json = {"_comment": "Generated by scripts/construct.py from data/policy.json: risk-budgeted weights, Ledoit-Wolf covariance, caps, NO-SELL floors. Weights are % of the whole book incl. 5% cash.",
                "stages": [], "groups": {g: [t for t in ts if t in NAMES or t == "CASH"] for g, ts in TARGETS["groups"].items() if any(t in NAMES or t == "CASH" for t in ts)},
                "new_positions": {k: v for k, v in TARGETS["new_positions"].items() if k in NAMES}}
    rows, stat_rows = {}, {}
    risk_rows = {}
    for st, names in stage_names.items():
        sub = R[names].dropna(how="all")
        sub = sub.dropna()
        cov = lw_cov(sub)
        T_end = POLICY["stage_book_end_eur"][st] * fx * (1 - POLICY["cash_pct"] / 100)
        lo = np.array([max(POLICY["single_min_pct"] / 100, values.get(n, 0.0) / T_end) for n in names])
        hi = np.maximum(hi_for(names), lo)  # a floor above the cap (no-sell) wins
        assert lo.sum() < 1.0, (st, lo.sum())
        b = budgets_for(names)
        w = solve(lambda x: (((risk_contrib(x, cov) - b) / b) ** 2).sum(), len(names), lo, hi)
        w = pd.Series(w, index=names)
        binding = [n for n, a, l in zip(names, w.values, lo) if a - l < 1e-4 and values.get(n, 0) > 0]
        book_w = (100 * w * (1 - POLICY["cash_pct"] / 100)).round(1)
        wt = {n: float(book_w[n]) for n in names}
        wt["CASH"] = float(POLICY["cash_pct"])
        drift = round(100 - sum(wt.values()), 1)
        wt[max(wt, key=lambda k: wt[k] if k != "CASH" else -1)] += drift  # absorb rounding in the largest position
        out_json["stages"].append({"name": {"A": "A", "B": "B (adds turbines + mining)", "C": "C (adds India + gene editing)"}[st],
                                   "from_eur": {"A": 0, "B": 20000, "C": 30000}[st], "weights": wt})
        rows[st] = book_w
        rc = pd.Series(risk_contrib(w.values, cov), index=names)
        sleeve = pd.Series({n: POLICY["sleeves"][n] for n in names})
        risk_rows[st] = (100 * rc.groupby(sleeve).sum()).round(1)
        hand = pd.Series({n: TARGETS["stages"][{"A": 0, "B": 1, "C": 2}[st]]["weights"].get(n, 0.0) for n in names})
        hw = hand / hand.sum()
        for lab, ww in (("optimised", w), ("hand-set", hw)):
            r = sub.values @ ww.values
            cum = np.cumprod(1 + r)
            stat_rows[(st, lab)] = {"vol %": 100 * np.sqrt(ww.values @ cov @ ww.values), "worst drawdown %": 100 * (cum / np.maximum.accumulate(cum) - 1).min(),
                                    "largest weight %": 100 * ww.max() * 0.95, "crypto share of risk %": 100 * float(risk_contrib(ww.values, cov)[[names.index(n) for n in names if POLICY["sleeves"][n] == "crypto"]].sum())}
        if binding:
            stat_rows[(st, "optimised")]["no-sell floor binding"] = ", ".join(binding)
    return out_json, rows, risk_rows, pd.DataFrame(stat_rows).T, values, fx


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--preset", choices=list(POLICY.get("presets", {})), help="risk-budget preset from data/policy.json (default: active_preset)")
    ap.add_argument("--include", nargs="*", default=[], help="un-exclude positions listed in policy 'exclude' (e.g. VEU)")
    ap.add_argument("--no-write", action="store_true", help="do not write targets_optimised.json / construction.md")
    ap.add_argument("--out", default=str(ROOT / "reports" / "latest"))
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    POLICY["risk_budget_pct"] = POLICY["presets"][a.preset or POLICY["active_preset"]]
    global NAMES
    POLICY["exclude"] = [x for x in POLICY.get("exclude", []) if x not in a.include]
    NAMES = [n for n in POLICY["sleeves"] if n not in POLICY["exclude"]]
    P = panel()[NAMES]
    md = ["# Portfolio construction", ""]
    if a.validate:
        series, turn, navg = walk_forward(P)
        rows = {m: perf(s) | {"turnover %/yr": 100 * turn[m]} for m, s in series.items()}
        t = pd.DataFrame(rows).T
        t.index.name = "Method"
        s0 = next(iter(series.values()))
        md += [f"## 1. Out-of-sample validation ({s0.index[0].date()} to {s0.index[-1].date()}, monthly refit on the previous 3 years, ~{navg:.0f} assets available on average)",
               md_table(t, {c: "{:.1f}" for c in t.columns} | {"Sharpe": "{:.2f}"}), "",
               "Costs: 10bp per side (25bp crypto). All methods see the same hindsight-picked universe, so compare rows against each other."]
        fig, ax = plt.subplots(1, 2, figsize=(15, 5))
        for m, s in series.items():
            cum = (1 + s).cumprod()
            ax[0].plot(cum, label=f"{m} (Sharpe {t.loc[m,'Sharpe']:.2f})", lw=2.4 if "Risk budgets" in m else 1.3)
            ax[1].plot(100 * (cum / cum.cummax() - 1), lw=2.4 if "Risk budgets" in m else 1.0)
        ax[0].set_yscale("log"); ax[0].legend(frameon=False, fontsize=7); ax[0].set_title("Growth of 1 (out-of-sample, after costs)")
        ax[1].set_title("Drawdown %")
        fig.tight_layout(); fig.savefig(out / "14_construction_validation.png", dpi=130); plt.close(fig)
    if a.build:
        oj, rows, risk_rows, stats, values, fx = build(P)
        if not a.no_write:
            (ROOT / "data" / "targets_optimised.json").write_text(json.dumps(oj, indent=1))
        w = pd.DataFrame(rows).fillna(0.0)
        hand = pd.DataFrame({st: pd.Series(TARGETS["stages"][i]["weights"]) for i, st in enumerate("ABC")}).drop(index="CASH")
        cmp = pd.concat({"optimised": w, "hand-set": hand.reindex(w.index).fillna(0.0)}, axis=1)
        cmp.columns = [f"{a_} {b_}" for a_, b_ in cmp.columns]
        cmp.insert(0, "now %", pd.Series({n: 0.0 for n in w.index}))
        book = sum(values.values()) + 1007.0
        for n in w.index:
            cmp.loc[n, "now %"] = round(100 * values.get(n, 0.0) / book, 1)
        cmp.index.name = "Ticker"
        md += ["## 2. Optimised targets (% of whole book, 5% cash on top) vs my hand-set ones", md_table(cmp, {c: "{:.1f}" for c in cmp.columns}), "",
               "## 3. Risk by sleeve (% of total portfolio risk) at each optimised stage", md_table(pd.DataFrame(risk_rows).fillna(0.0).rename_axis("sleeve"), {c: "{:.1f}" for c in "ABC"}), "",
               "## 4. Stage mixes: optimised vs hand-set (covariance since the last 3 years)", md_table(stats.set_axis([f"stage {a_} {b_}" for a_, b_ in stats.index]).rename_axis("stage / mix").fillna("-"), {c: "{:.1f}" for c in ["vol %", "worst drawdown %", "largest weight %", "crypto share of risk %"]}), ""]
    if not a.no_write:
        (out / "construction.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
