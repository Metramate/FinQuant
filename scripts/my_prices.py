"""Price loader for the personal portfolio.

Downloads adjusted closes from Yahoo and, where a holding is a recent listing (e.g. the
US-listed SKHY, trading since 2026-07), extends its history backwards with the *original*
listing named in the ``history_proxy`` column of ``data/my-portfolio.csv`` (SK hynix on the
Korea exchange: ``000660.KS``), converted to USD.

How the splice works (an approximation, so it is reported by ``fetch_prices``):
* the proxy is converted to USD with the matching ``<CCY>=X`` rate;
* Korea closes before the US opens, so the US price on day t reflects the Korean move on
  t+1 (measured: next-day return correlation 0.51 vs 0.35 same-day) -> proxy is shifted
  back one proxy-trading-day;
* the proxy is scaled so its level equals the real listing on the first real trading day,
  hence no artificial return appears at the junction.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import os
import pathlib

import pandas as pd
import yfinance as yf

# Yahoo FX tickers quoted as <local currency> per 1 USD, keyed by exchange suffix.
FX_BY_SUFFIX = {".KS": "KRW=X", ".KQ": "KRW=X", ".HK": "HKD=X", ".T": "JPY=X", ".SS": "CNY=X"}


def _download(tickers: list[str], start: str) -> pd.DataFrame:
    raw = yf.download(tickers, start=start, auto_adjust=False, progress=False)
    px = raw["Adj Close"] if "Adj Close" in raw.columns.get_level_values(0) else raw["Close"]
    if isinstance(px, pd.Series):
        px = px.to_frame(tickers[0])
    px.index = pd.to_datetime(px.index).tz_localize(None)
    return px


def splice_proxy(real: pd.Series, proxy_usd: pd.Series, calendar: pd.DatetimeIndex) -> pd.Series:
    """Extend ``real`` backwards with ``proxy_usd`` (see module docstring)."""
    real = real.dropna()
    proxy_usd = proxy_usd.dropna()
    first = real.index[0]
    shifted = proxy_usd.shift(-1).dropna()  # value at date t = proxy close of the next proxy day
    cal = calendar.union(proxy_usd.index).union(real.index)  # holidays differ per exchange -> ffill
    aligned = shifted.reindex(cal).ffill()
    scale = real.iloc[0] / aligned.loc[first]
    out = pd.concat([aligned.loc[: first - pd.Timedelta(days=1)] * scale, real])
    return out.rename(real.name)


CACHE_DIR = pathlib.Path(__file__).resolve().parent.parent / ".cache" / "prices"


def fetch_prices(holdings: pd.DataFrame, start: str = "2024-01-01") -> pd.DataFrame:
    """Same-day cached wrapper around ``_fetch_prices`` (set PM_NO_CACHE=1 to force a refresh)."""
    cols = [c for c in ("yahoo_ticker", "history_proxy") if c in holdings]
    key = hashlib.md5((start + dt.date.today().isoformat() + holdings[cols].astype(str).to_csv()).encode()).hexdigest()[:16]
    f = CACHE_DIR / f"{key}.pkl"
    if f.exists() and not os.environ.get("PM_NO_CACHE"):
        return pd.read_pickle(f)
    out = _fetch_prices(holdings, start)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    out.to_pickle(f)
    return out


def _fetch_prices(holdings: pd.DataFrame, start: str = "2024-01-01") -> pd.DataFrame:
    """Prices (one column per ``yahoo_ticker``) with proxy-extended history where configured."""
    rows = holdings.dropna(subset=["yahoo_ticker"])
    tickers = rows["yahoo_ticker"].tolist()
    proxies = {}
    if "history_proxy" in rows:
        proxies = dict(zip(rows["yahoo_ticker"], rows["history_proxy"]))
        proxies = {k: v for k, v in proxies.items() if isinstance(v, str) and v}

    fx = {}
    for proxy in proxies.values():
        suffix = proxy[proxy.rfind(".") :] if "." in proxy else ""
        if suffix in FX_BY_SUFFIX:
            fx[proxy] = FX_BY_SUFFIX[suffix]
        elif suffix:
            raise ValueError(f"No FX mapping for proxy {proxy!r}; add its suffix to FX_BY_SUFFIX")

    extra = sorted(set(proxies.values()) | set(fx.values()))
    eur_listed = [t for t in tickers if t.endswith(".DE")]  # EUR-listed ETFs (e.g. VWCE.DE): convert to USD like everything else
    if eur_listed:
        extra = sorted(set(extra) | {"EURUSD=X"})
    px = _download(tickers + extra, start)
    out = px[tickers].copy()
    for t in eur_listed:
        out[t] = out[t] * px["EURUSD=X"].ffill()
    for tkr, proxy in proxies.items():
        usd = px[proxy] / px[fx[proxy]].ffill() if proxy in fx else px[proxy]
        before = out[tkr].dropna().shape[0]
        out[tkr] = splice_proxy(out[tkr], usd, out.index).reindex(out.index)
        print(f"[prices] {tkr}: {before} real days extended to {out[tkr].dropna().shape[0]} using {proxy}")
    return out
