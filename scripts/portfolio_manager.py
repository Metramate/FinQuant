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


def recommend(risky, cash, book, rets, cov, rc, px, trades, cur, tgt, max_w, rf):
    recs = []  # (priority 1=high, headline, detail)
    risky_share = 1 - cash / book
    names = list(risky.index)
    ratio = pd.Series(rc / risky["w_sleeve"].values, index=names)

    # 1. positions that carry far more risk than capital
    hot = [(t, 100 * rc[names.index(t)], 100 * risky.loc[t, "w_sleeve"]) for t in names
           if (ratio[t] > 1.5 and rc[names.index(t)] > 0.12) or rc[names.index(t)] > 0.20
           or risky.loc[t, "w_book"] > max_w]
    for t, r_, w_ in sorted(hot, key=lambda x: -x[1]):
        recs.append((1, f"Trim {t}: {w_:.0f}% of capital but {r_:.0f}% of portfolio risk",
                     f"{t}'s volatility is {100*np.sqrt(cov[names.index(t), names.index(t)]):.0f}% a year"
                     + (f" and it is above your {100*max_w:.0f}% single-asset cap. " if risky.loc[t, "w_book"] > max_w else ". ") +
                     f"Moving to ~{100*trades.loc[t,'tgt_book']:.1f}% of the book still leaves it a core position "
                     f"while removing the largest single source of drawdown."))

    # 2. crypto sleeve
    crypto = [t for t in names if risky.loc[t, "theme"] == "Crypto"]
    cw = risky.loc[crypto, "w_book"].sum()
    crc = sum(rc[names.index(t)] for t in crypto)
    small_crypto = [t for t in crypto if risky.loc[t, "w_book"] < 0.03]
    recs.append((1 if crc > 0.4 else 2, f"Crypto is {100*cw:.0f}% of your book but {100*crc:.0f}% of the risk",
                 "Treat it as one bet (BTC/ETH/UNI/NEAR move together). " + (
                     f"{', '.join(small_crypto)} are <3% each: too small to matter for return, still adding alt-coin tail risk. "
                     "Either consolidate into BTC/ETH or size them up deliberately." if small_crypto else "")))

    # 3. hidden overlap in the AI-semis complex
    ai = [t for t in names if risky.loc[t, "theme"] in ("Semis / AI", "Broad tech")]
    aw = risky.loc[ai, "w_book"].sum()
    arc = sum(rc[names.index(t)] for t in ai)
    corr = rets[ai].corr().values
    avg = corr[np.triu_indices(len(ai), 1)].mean()
    recs.append((1 if aw > 0.35 else 3, f"AI/semis/tech complex = {100*aw:.0f}% of book, {100*arc:.0f}% of risk "
                 f"(avg pairwise correlation {avg:.2f})",
                 f"{', '.join(ai)} are largely one trade, and QQQM and SMH already hold NVDA/semis. "
                 "New money should go elsewhere before this grows; do not count these as diversification."))

    # 4. what actually diversifies
    others = [t for t in names if t not in ai and t not in crypto]
    avgc = rets.corr().apply(lambda col: (col.sum() - 1) / (len(col) - 1))
    div = avgc[others].sort_values().head(2)
    recs.append((3, f"Best diversifiers: {', '.join(div.index)}",
                 "Lowest average correlation to everything else ("
                 + ", ".join(f"{k} {v:.2f}" for k, v in div.items())
                 + "). If you add risk, add it here rather than to the AI/crypto blocks."))

    # 5. cash
    ann_vol = np.sqrt(cur["vol"] ** 2) * risky_share
    recs.append((3, f"Cash {100*cash/book:.1f}% (${cash:,.0f}): keep as dry powder, deploy on weakness",
                 f"Portfolio vol on the whole book is ~{100*ann_vol:.0f}% a year, so a 10% pullback in the "
                 f"risky sleeve is a normal event, not a tail. Deploy in 3-4 tranches into the underweights in the rebalance list "
                 f"rather than into names already above target. Cash earns ~{100*rf:.1f}% at my assumed risk-free rate."))

    # 6. trend / drawdown watch (1y)
    one_y = px.iloc[-ANN:]
    dd = one_y.iloc[-1] / one_y.max() - 1
    deep = dd[dd < -0.20].sort_values()
    if len(deep):
        recs.append((2, "Review thesis (>20% below 1-year high): " + ", ".join(f"{k} {100*v:.0f}%" for k, v in deep.items()),
                     "A drawdown alone is not a sell signal. Write down why you own each; if the reason is gone, exit, "
                     "otherwise this is where the cash tranches belong."))

    # 7. rebalance
    buys = trades[trades["trade_usd"] > 0].sort_values("trade_usd", ascending=False)
    sells = trades[trades["trade_usd"] < 0].sort_values("trade_usd")
    turn = trades["trade_usd"].abs().sum() / 2 / book
    recs.append((1, f"Rebalance (≈{100*turn:.0f}% of book turnover): sell "
                 + (", ".join(f"{k} ${-v:,.0f}" for k, v in sells["trade_usd"].items()) or "nothing")
                 + "; buy "
                 + (", ".join(f"{k} ${v:,.0f}" for k, v in buys["trade_usd"].items()) or "nothing"),
                 f"Gets halfway to equal-risk weights: vol {100*cur['vol']:.1f}% → {100*tgt['vol']:.1f}%, "
                 f"worst drawdown {100*cur['max_dd']:.0f}% → {100*tgt['max_dd']:.0f}% (in-sample), "
                 f"cap {100*max_w:.0f}% per asset. Buys are mechanical (low-risk assets get more weight): only buy what you'd want to own anyway. Check tax/fees before selling; use new cash first where possible."))
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

    recs = recommend(risky, cash, book, rets, cov, rc, px, trades, st["Current"], st["Suggested target"], args.max_weight, args.rf)

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
        "## Recommendations (most important first)",
        *[f"{i}. **{h}**  \n   {d}" for i, (_, h, d) in enumerate(recs, 1)],
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
