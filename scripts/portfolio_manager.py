"""Portfolio-manager report for ``data/my-portfolio.csv``.

    python scripts/portfolio_manager.py                # fetch prices, write reports/latest/
    python scripts/portfolio_manager.py --start 2025-01-01 --rf 0.04 --max-weight 0.20

Produces charts (PNG) + ``REPORT.md`` and prints the recommendations.

Design notes (read before trusting any number):
* All statistics are *in-sample* on history since ``--start`` with the CURRENT weights held
  constant (daily-rebalanced). That is a description of the past, not a forecast.
* Return estimates are noisy, so the max-Sharpe portfolio uses means shrunk 50% toward the
  cross-sectional average, and the recommended target is only HALF-way to the risk-balanced
  (equal-risk-contribution) portfolio, with a no-trade band. Risk estimates (covariances) are
  far more stable than return estimates, which is why the target is built on risk balance.
* SKHY's pre-2026-07 history is a proxy (SK hynix on the Korea exchange, in USD) -- see
  ``my_prices.py``.
* Policy inputs that are MY assumptions, not facts about you: ``--rf`` (risk-free rate) and
  ``--max-weight`` (cap per asset, % of whole book).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.cluster.hierarchy import leaves_list, linkage  # noqa: E402
from scipy.optimize import minimize  # noqa: E402
from scipy.spatial.distance import squareform  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from load_my_portfolio import load_holdings  # noqa: E402
from my_prices import fetch_prices  # noqa: E402

ANN = 252
THEME_COLORS = {
    "Crypto": "#f2a900",
    "Broad tech": "#4c78a8",
    "Semis / AI": "#7b4fd3",
    "Power / nuclear": "#2a9d8f",
    "Aerospace & defense": "#d1495b",
    "Space": "#8d99ae",
    "Healthcare": "#52b788",
    "Cash": "#bdbdbd",
}
CUR, TGT, BAD = "#4c78a8", "#2a9d8f", "#d1495b"


# --------------------------------------------------------------------------- data
def build_book(df: pd.DataFrame, prices: pd.DataFrame):
    """Holdings table (value, weights) and the aligned risky-asset price frame."""
    risky = df[df["asset_class"] != "cash"].set_index("ticker").copy()
    last = prices.ffill().iloc[-1]
    risky["price"] = risky["yahoo_ticker"].map(last)
    risky["value"] = risky["quantity"] * risky["price"]
    risky["pnl_pct"] = 100 * (risky["value"] / risky["cost_usd"] - 1)
    cash = float(df.loc[df["asset_class"] == "cash", "quantity"].sum())  # stablecoin ~ $1
    book = float(risky["value"].sum() + cash)
    risky["w_book"] = risky["value"] / book
    risky["w_sleeve"] = risky["value"] / risky["value"].sum()

    px = prices[risky["yahoo_ticker"].tolist()].copy()
    px.columns = risky.index
    px = px[prices.notna().mean(axis=1) >= 0.5]  # drop weekends/holidays (crypto trades 7d)
    px = px.dropna()
    return risky, cash, book, px


# --------------------------------------------------------------------------- maths
def risk_contrib(w: np.ndarray, cov: np.ndarray) -> np.ndarray:
    var = w @ cov @ w
    return w * (cov @ w) / var


def optimise(obj, n: int, lo: float, hi: float, x0: np.ndarray) -> np.ndarray:
    res = minimize(
        obj,
        x0,
        method="SLSQP",
        bounds=[(lo, hi)] * n,
        constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}],
        options={"maxiter": 500, "ftol": 1e-12},
    )
    if not res.success:
        print(f"[warn] optimiser: {res.message}")
    return res.x


def portfolios(mu, cov, n, lo, hi, x0, rf):
    shrunk = 0.5 * mu + 0.5 * mu.mean()
    minvol = optimise(lambda w: w @ cov @ w, n, lo, hi, x0)
    maxsh = optimise(lambda w: -(w @ shrunk - rf) / np.sqrt(w @ cov @ w), n, lo, hi, x0)
    erc = optimise(lambda w: ((risk_contrib(w, cov) - 1 / n) ** 2).sum() * 1e4, n, lo, hi, x0)
    return shrunk, minvol, maxsh, erc


def stats(w, rets: pd.DataFrame, rf: float) -> dict:
    pr = rets.values @ w
    cum = np.cumprod(1 + pr)
    dd = cum / np.maximum.accumulate(cum) - 1
    ann_ret = cum[-1] ** (ANN / len(pr)) - 1
    vol = pr.std(ddof=1) * np.sqrt(ANN)
    var95 = -np.percentile(pr, 5)
    return {
        "ann_return": ann_ret,
        "vol": vol,
        "sharpe": (ann_ret - rf) / vol,
        "max_dd": dd.min(),
        "var95_1d": var95,
        "cvar95_1d": -pr[pr <= -var95].mean(),
    }


# --------------------------------------------------------------------------- charts
def fig_allocation(risky, cash, book, tgt_book, path):
    d = risky.assign(tgt=tgt_book).sort_values("w_book")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 6.2), gridspec_kw={"width_ratios": [1.7, 1]})
    y = np.arange(len(d))
    a1.barh(y + 0.2, 100 * d["w_book"], 0.38, color=CUR, label="Current")
    a1.barh(y - 0.2, 100 * d["tgt"], 0.38, color=TGT, label="Suggested target")
    a1.set_yticks(y, d.index)
    a1.set_xlabel("% of whole book (cash held constant)")
    a1.set_title("Position weights: now vs suggested")
    a1.legend(frameon=False, loc="lower right")
    for yi, (c, t) in enumerate(zip(d["w_book"], d["tgt"])):
        a1.text(100 * c + 0.2, yi + 0.2, f"{100*c:.1f}", va="center", fontsize=8)
        a1.text(100 * t + 0.2, yi - 0.2, f"{100*t:.1f}", va="center", fontsize=8, color=TGT)
    th = risky.groupby("theme")["value"].sum()
    th["Cash"] = cash
    th = th.sort_values(ascending=False)
    a2.pie(
        th,
        labels=[f"{k}\n{100*v/book:.0f}%" for k, v in th.items()],
        colors=[THEME_COLORS.get(k, "#999") for k in th.index],
        startangle=90,
        counterclock=False,
        wedgeprops={"width": 0.42, "edgecolor": "white"},
        textprops={"fontsize": 8},
    )
    a2.set_title(f"By theme (book ${book:,.0f})")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def fig_performance(px, rets, w, path):
    pr = pd.Series(rets.values @ w, index=rets.index)
    cum = 100 * (1 + pr).cumprod()
    dd = cum / cum.cummax() - 1
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    a1.plot(cum, color="black", lw=2, label="Your portfolio (current weights)")
    for name, col in (("QQQM", CUR), ("BTC", THEME_COLORS["Crypto"]), ("SMH", THEME_COLORS["Semis / AI"])):
        if name in px:
            a1.plot(100 * px[name] / px[name].iloc[0], color=col, lw=1.1, alpha=0.9, label=name)
    a1.set_yscale("log")
    a1.yaxis.set_major_formatter(matplotlib.ticker.ScalarFormatter())
    a1.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    a1.set_yticks([100, 150, 200, 300, 400])
    a1.set_ylabel("Growth of 100 (log scale)")
    a1.set_title("Performance since start of window")
    a1.legend(frameon=False, ncol=4)
    a2.fill_between(dd.index, 100 * dd, 0, color=BAD, alpha=0.5)
    a2.set_ylabel("Drawdown %")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def fig_risk(risky, rc, path):
    d = pd.DataFrame({"w": 100 * risky["w_sleeve"], "rc": 100 * rc}).sort_values("rc")
    fig, ax = plt.subplots(figsize=(10, 6.2))
    y = np.arange(len(d))
    ax.barh(y + 0.2, d["w"], 0.38, color="#9ecae1", label="% of capital")
    ax.barh(y - 0.2, d["rc"], 0.38, color=BAD, label="% of portfolio risk")
    ax.set_yticks(y, d.index)
    ax.set_xlabel("% of risky sleeve")
    ax.set_title("Where the risk really comes from (red beyond blue = punches above its weight)")
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def fig_corr(rets, path):
    c = rets.corr()
    order = leaves_list(linkage(squareform(np.sqrt(0.5 * (1 - c.values)), checks=False), "average"))
    c = c.iloc[order, order]
    fig, ax = plt.subplots(figsize=(9, 7.5))
    im = ax.imshow(c, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(c)), c.columns, rotation=60, ha="right")
    ax.set_yticks(range(len(c)), c.index)
    for i in range(len(c)):
        for j in range(len(c)):
            ax.text(j, i, f"{c.iloc[i, j]:.2f}", ha="center", va="center", fontsize=7)
    fig.colorbar(im, shrink=0.8)
    ax.set_title("Daily-return correlation (clustered: blocks = hidden same-bet groups)")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def fig_frontier(shrunk, cov, pts, path, seed=0):
    rng = np.random.default_rng(seed)
    n = len(shrunk)
    W = rng.dirichlet(np.ones(n) * 0.8, 6000)
    r = W @ shrunk
    v = np.sqrt(np.einsum("ij,jk,ik->i", W, cov, W))
    fig, ax = plt.subplots(figsize=(10, 6.5))
    sc = ax.scatter(100 * v, 100 * r, c=r / v, s=6, cmap="viridis", alpha=0.5)
    fig.colorbar(sc, label="return/vol (shrunk-return Sharpe-like)")
    styles = {"Current": ("black", "o"), "Min-vol": ("#2a9d8f", "s"), "Max-Sharpe*": ("#f2a900", "^"),
              "Risk-parity": ("#7b4fd3", "D"), "Suggested target": (BAD, "*")}
    for name, w in pts.items():
        col, m = styles[name]
        ax.scatter(100 * np.sqrt(w @ cov @ w), 100 * (w @ shrunk), s=190 if m == "*" else 90,
                   c=col, marker=m, edgecolor="white", zorder=5, label=name)
    ax.set_xlabel("Volatility % (annualised)")
    ax.set_ylabel("Expected return % (history shrunk 50% to average)")
    ax.set_title("Risk/return map of long-only mixes of your holdings\n(*max-Sharpe is return-estimate-driven: treat as a ceiling, not a plan)")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def fig_trades(trades, path):
    t = trades[trades["trade_usd"].abs() > 0].sort_values("trade_usd")
    fig, ax = plt.subplots(figsize=(9, max(3, 0.38 * len(t) + 1.5)))
    ax.barh(t.index, t["trade_usd"], color=[TGT if x > 0 else BAD for x in t["trade_usd"]])
    for i, x in enumerate(t["trade_usd"]):
        ax.text(x + (15 if x > 0 else -15), i, f"{x:+,.0f}", va="center", ha="left" if x > 0 else "right", fontsize=8)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_xlabel("USD to buy (+) / sell (-)")
    ax.set_title("Suggested rebalance (cash-neutral within the risky sleeve)")
    ax.margins(x=0.15)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


# --------------------------------------------------------------------------- advice
def md_table(df: pd.DataFrame, fmt: dict | None = None) -> str:
    fmt = fmt or {}
    cols = [df.index.name or ""] + list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for idx, row in df.iterrows():
        cells = [str(idx)] + [fmt.get(c, "{}").format(row[c]) for c in df.columns]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def trim_test(t, w0, names, target_sleeve_w, rets, rf, cur):
    """Effect of cutting ``t`` to ``target_sleeve_w`` (excess spread pro-rata). Returns (stats, passes)."""
    i = names.index(t)
    w = w0.copy()
    excess = w[i] - target_sleeve_w
    w[i] = target_sleeve_w
    rest = np.arange(len(w)) != i
    w[rest] += excess * w[rest] / w[rest].sum()
    st = stats(w, rets, rf)
    return st, (st["vol"] < cur["vol"] and st["ann_return"] >= cur["ann_return"])


def recommend(risky, cash, book, rets, cov, rc, px, trades, cur, tgt, max_w, rf, bt=None):
    """Aggressive-by-design advice. A trim is recommended ONLY if it lowers risk AND does not lower return
    (in-sample test of that exact trim + the walk-forward backtest gate when available). Otherwise: keep."""
    recs = []  # (priority 1=high, headline, detail)
    risky_share = 1 - cash / book
    names = list(risky.index)
    w0 = risky["w_sleeve"].values
    ratio = pd.Series(rc / w0, index=names)
    bt = (bt or {}).get("verdict", {})

    def gate(rule):
        v = bt.get(rule)
        return None if v is None else v["passes_gate"]

    # 1. big risk drivers: trim only if it passes BOTH tests
    hot = [t for t in names if (ratio[t] > 1.5 and rc[names.index(t)] > 0.12) or rc[names.index(t)] > 0.20
           or risky.loc[t, "w_book"] > max_w]
    for t in sorted(hot, key=lambda x: -rc[names.index(x)]):
        i = names.index(t)
        tgt_w = trades.loc[t, "tgt_book"] / risky_share
        st, ins_ok = trim_test(t, w0, names, tgt_w, rets, rf, cur)
        is_crypto = risky.loc[t, "theme"] == "Crypto"
        g = gate("crypto_cap_30" if is_crypto else "erc_blend")
        facts = (f"{t} is {100*w0[i]:.0f}% of capital and {100*rc[i]:.0f}% of risk. Cutting it to "
                 f"~{100*trades.loc[t,'tgt_book']:.1f}% of the book (excess spread pro-rata) moves vol {100*cur['vol']:.1f}% → "
                 f"{100*st['vol']:.1f}% and return {100*cur['ann_return']:.1f}% → {100*st['ann_return']:.1f}% (in-sample)")
        if ins_ok and g is not False:
            recs.append((1, f"Trim {t}: lowers risk AND raises return in the tests",
                         facts + (f"; walk-forward backtest gate: {'PASS' if g else 'not run'}. " if g is not None else ". ")
                         + "Passes your rule, but both tests share one regime (crypto lagged), so size the trim to what you are comfortable with."))
        else:
            why = ("it would cost return in-sample" if not ins_ok and st["vol"] < cur["vol"] else
                   "it would not lower risk" if not ins_ok else "the backtest gate failed")
            recs.append((3, f"Keep {t} (aggressive by design): trimming fails your rule — {why}",
                         facts + ". No action; this is a risk you are choosing."))

    # 2. crypto sleeve: information, then a gated option
    crypto = [t for t in names if risky.loc[t, "theme"] == "Crypto"]
    cw, crc = risky.loc[crypto, "w_book"].sum(), sum(rc[names.index(t)] for t in crypto)
    small_crypto = [t for t in crypto if risky.loc[t, "w_book"] < 0.03]
    g = gate("crypto_cap_30")
    detail = "Know this number: it is your single biggest driver of drawdowns. "
    if g is not None and "crypto_cap_30" in bt:
        v = bt["crypto_cap_30"]
        detail += (f"Capping crypto at 30% of the sleeve in the backtest changed vol {100*v['d_vol']:+.1f}pt and net CAGR "
                   f"{100*v['d_cagr']:+.1f}pt vs holding the mix ({'passes' if g else 'fails'} your gate). ")
    if small_crypto:
        detail += (f"{', '.join(small_crypto)} are <3% each: too small to move return but they add alt-coin risk "
                   "(optional tidy-up: fold into BTC/ETH, or size up on purpose).")
    recs.append((2, f"Crypto is {100*cw:.0f}% of your book and {100*crc:.0f}% of the risk", detail))

    # 3. AI / semis complex: accepted concentration
    ai = [t for t in names if risky.loc[t, "theme"] in ("Semis / AI", "Broad tech")]
    aw, arc = risky.loc[ai, "w_book"].sum(), sum(rc[names.index(t)] for t in ai)
    corr = rets[ai].corr().values
    avg = corr[np.triu_indices(len(ai), 1)].mean()
    recs.append((3, f"AI/semis/tech = {100*aw:.0f}% of book, {100*arc:.0f}% of risk (avg correlation {avg:.2f}): accepted concentration",
                 f"{', '.join(ai)} are largely one trade (QQQM and SMH already hold NVDA/semis). No trim recommended; "
                 "just know that a semis sell-off hits all five at once, and don't count them as diversification."))

    # 4. what actually diversifies (for new money)
    others = [t for t in names if t not in ai and t not in crypto]
    avgc = rets.corr().apply(lambda col: (col.sum() - 1) / (len(col) - 1))
    div = avgc[others].sort_values().head(2)
    recs.append((3, f"If you add risk, the best diversifiers you already own are {', '.join(div.index)}",
                 "Lowest average correlation to everything else (" + ", ".join(f"{k} {v:.2f}" for k, v in div.items()) + ")."))

    # 5. cash
    recs.append((3, f"Cash {100*cash/book:.1f}% (${cash:,.0f}): dry powder for new positions",
                 f"At {100*cur['vol']*risky_share:.0f}% whole-book volatility a 10% pullback is a normal event. Deploy in tranches; "
                 f"new cash (e.g. your planned 2-3% HOOD) avoids selling anything. Cash earns ~{100*rf:.1f}% at my assumed risk-free rate."))

    # 6. drawdown watch
    one_y = px.iloc[-ANN:]
    dd = one_y.iloc[-1] / one_y.max() - 1
    deep = dd[dd < -0.20].sort_values()
    if len(deep):
        recs.append((2, "Thesis check (>20% below 1-year high): " + ", ".join(f"{k} {100*v:.0f}%" for k, v in deep.items()),
                     "A drawdown alone is not a sell signal. If the reason you bought is intact, these are candidates for new cash, not for selling."))

    # 7. full rebalance: optional, gated by the walk-forward backtest
    g = gate("erc_blend")
    buys = trades[trades["trade_usd"] > 0].sort_values("trade_usd", ascending=False)
    sells = trades[trades["trade_usd"] < 0].sort_values("trade_usd")
    turn = trades["trade_usd"].abs().sum() / 2 / book
    trade_txt = ("sell " + (", ".join(f"{k} ${-v:,.0f}" for k, v in sells["trade_usd"].items()) or "nothing")
                 + "; buy " + (", ".join(f"{k} ${v:,.0f}" for k, v in buys["trade_usd"].items()) or "nothing"))
    effect = (f"in-sample vol {100*cur['vol']:.1f}% → {100*tgt['vol']:.1f}%, return {100*cur['ann_return']:.1f}% → {100*tgt['ann_return']:.1f}%")
    if g is None:
        recs.append((2, f"Optional risk-balanced rebalance (~{100*turn:.0f}% turnover): {trade_txt}",
                     effect + ". Run scripts/backtest.py to test it before acting."))
    elif g and tgt["vol"] < cur["vol"] and tgt["ann_return"] >= cur["ann_return"]:
        v = bt["erc_blend"]
        recs.append((1, f"Optional rebalance passes your rule (~{100*turn:.0f}% turnover): {trade_txt}",
                     f"{effect}. Walk-forward, net of costs, monthly: vol {100*v['d_vol']:+.1f}pt and CAGR {100*v['d_cagr']:+.1f}pt "
                     "vs holding the mix, in both halves. Caveat: one window where crypto lagged; do it gradually with new cash first."))
    else:
        recs.append((3, "Skip the full rebalance: it does not lower risk AND raise return in the tests",
                     effect + ". Keep the portfolio as is."))
    return sorted(recs, key=lambda r: r[0])


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", default="2024-01-01")
    ap.add_argument("--rf", type=float, default=0.04, help="risk-free rate (my assumption)")
    ap.add_argument("--max-weight", type=float, default=0.20, help="cap per asset, share of whole book")
    ap.add_argument("--min-weight", type=float, default=0.01)
    ap.add_argument("--out", default=str(pathlib.Path(__file__).resolve().parent.parent / "reports" / "latest"))
    args = ap.parse_args()
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    df = load_holdings()
    prices = fetch_prices(df, args.start)
    risky, cash, book, px = build_book(df, prices)
    rets = px.pct_change().dropna()
    names, n = list(risky.index), len(risky)
    risky_share = 1 - cash / book
    mu, cov = rets.mean().values * ANN, rets.cov().values * ANN
    w0 = risky["w_sleeve"].values
    lo, hi = args.min_weight / risky_share, args.max_weight / risky_share
    w0c = np.clip(w0, lo, hi)  # optimiser start only

    shrunk, w_minvol, w_maxsh, w_erc = portfolios(mu, cov, n, lo, hi, w0c / w0c.sum(), args.rf)
    w_tgt = 0.5 * w0 + 0.5 * w_erc  # convex mix: feasible if w0 is (BTC above cap is handled below)
    w_tgt = np.clip(w_tgt, lo, hi)
    w_tgt /= w_tgt.sum()

    ports = {"Current": w0, "Min-vol": w_minvol, "Max-Sharpe*": w_maxsh, "Risk-parity": w_erc, "Suggested target": w_tgt}
    st = {k: stats(v, rets, args.rf) for k, v in ports.items()}
    rc = risk_contrib(w0, cov)

    # trades: no-trade band 0.5% of book / $25
    tgt_book = pd.Series(w_tgt * risky_share, index=names)
    delta = (tgt_book - risky["w_book"]) * book
    delta[(delta.abs() < 0.005 * book) | (delta.abs() < 25)] = 0.0
    delta -= delta.sum() * (np.abs(delta) / np.abs(delta).sum()) if delta.abs().sum() else 0  # cash-neutral
    delta = delta.round(0)
    trades = pd.DataFrame({"now_book": risky["w_book"], "tgt_book": tgt_book, "trade_usd": delta})
    tgt_after = (risky["value"] + delta) / book
    trades["tgt_book"] = tgt_after  # weight after the (banded) trades
    (out / "trades.json").write_text(json.dumps({k: float(v) for k, v in trades["trade_usd"].items() if v}, indent=1))

    # robustness: fit risk-parity on 1st half, evaluate on 2nd
    h = len(rets) // 2
    cov1 = rets.iloc[:h].cov().values * ANN
    erc1 = optimise(lambda w: ((risk_contrib(w, cov1) - 1 / n) ** 2).sum() * 1e4, n, lo, hi, w0c / w0c.sum())
    oos_cur = stats(w0, rets.iloc[h:], args.rf)
    oos_erc = stats(erc1, rets.iloc[h:], args.rf)

    # charts
    fig_allocation(risky, cash, book, trades["tgt_book"], out / "01_allocation.png")
    fig_performance(px, rets, w0, out / "02_performance.png")
    fig_risk(risky, rc, out / "03_risk_contribution.png")
    fig_corr(rets, out / "04_correlation.png")
    fig_frontier(shrunk, cov, ports, out / "05_risk_return_map.png")
    fig_trades(trades, out / "06_rebalance.png")

    bt_file = out / "backtest.json"
    bt = json.loads(bt_file.read_text()) if bt_file.exists() else None
    recs = recommend(risky, cash, book, rets, cov, rc, px, trades, st["Current"], st["Suggested target"], args.max_weight, args.rf, bt)

    # report
    today = dt.date.today().isoformat()
    beta = np.cov(rets.values @ w0, rets["QQQM"])[0, 1] / rets["QQQM"].var() if "QQQM" in rets else float("nan")
    pos = risky[["theme", "price", "value", "w_book", "pnl_pct"]].copy()
    pos["w_book"] *= 100
    pos["vol"] = 100 * np.sqrt(np.diag(cov))
    pos["risk_share"] = 100 * rc
    pos = pos.sort_values("value", ascending=False)
    pos.index.name = "Ticker"
    st_df = pd.DataFrame(st).T
    for c in ("ann_return", "vol", "max_dd", "var95_1d", "cvar95_1d"):
        st_df[c] *= 100
    st_df.index.name = "Portfolio"
    md = [
        f"# Portfolio manager report — {today}",
        f"Book **${book:,.0f}** (risky ${book-cash:,.0f} + cash ${cash:,.0f}). Window {px.index[0].date()} → {px.index[-1].date()} "
        f"({len(rets)} trading days). Beta to QQQM {beta:.2f}.",
        "",
        "_Policy: your portfolio is aggressive on purpose. A trim is recommended only if it lowers risk AND does not lower return "
        "(in-sample test of that trim + walk-forward backtest). Everything else is reported as a risk you are choosing._",
        "",
        "## Recommendations (most important first)",
        *[f"{i}. **{h}**  \n   {d}" for i, (_, h, d) in enumerate(recs, 1)],
        "",
        "See also: [check-in & alerts](checkin.md) · [stress tests](stress.md) · [signals](signals.md) · [backtest](backtest.md) · "
        "[FinQuant optimiser](fq_optimise.md) · [watchlist](watchlist.md) · [tax lots](tax_lots.md)",
        "",
        "## Charts",
        *[f"![{p.stem}]({p.name})" for p in sorted(out.glob("*.png"))],
        "",
        "## Positions",
        md_table(pos, {"price": "{:,.2f}", "value": "${:,.0f}", "w_book": "{:.1f}%", "pnl_pct": "{:+.1f}%", "vol": "{:.0f}%", "risk_share": "{:.1f}%"}),
        "",
        "## Portfolio variants (in-sample, constant weights)",
        md_table(st_df, {"ann_return": "{:.1f}%", "vol": "{:.1f}%", "sharpe": "{:.2f}", "max_dd": "{:.1f}%", "var95_1d": "{:.2f}%", "cvar95_1d": "{:.2f}%"}),
        "",
        f"Out-of-sample sanity check: risk-parity weights fitted on the first half, run on the second half → "
        f"vol {100*oos_erc['vol']:.1f}% vs {100*oos_cur['vol']:.1f}% for your current mix; "
        f"max drawdown {100*oos_erc['max_dd']:.0f}% vs {100*oos_cur['max_dd']:.0f}%.",
        "",
        "## Rebalance trades",
        md_table(trades.assign(now_book=100 * trades["now_book"], tgt_book=100 * trades["tgt_book"]).rename_axis("Ticker"),
                 {"now_book": "{:.1f}%", "tgt_book": "{:.1f}%", "trade_usd": "{:+,.0f}"}),
        "",
        "## Caveats",
        "- In-sample history, constant weights; the window includes a strong crypto/AI bull run, which flatters returns.",
        "- SKHY before 2026-07-10 is a proxy from the Korean listing (000660.KS → USD, scaled, shifted a day).",
        f"- Assumptions I made, not facts: risk-free {100*args.rf:.1f}%, max {100*args.max_weight:.0f}% per asset.",
        "- Research tool, not licensed financial advice; check tax, fees and your own time horizon before trading.",
    ]
    (out / "REPORT.md").write_text("\n".join(md) + "\n")

    print(f"\nBook ${book:,.0f}  |  vol {100*st['Current']['vol']:.1f}%  Sharpe {st['Current']['sharpe']:.2f}  "
          f"maxDD {100*st['Current']['max_dd']:.0f}%  beta(QQQM) {beta:.2f}")
    for i, (_, h, d) in enumerate(recs, 1):
        print(f"\n{i}. {h}\n   {d}")
    print(f"\nWrote {out}/REPORT.md and charts")


if __name__ == "__main__":
    main()
