"""100-year monthly dataset for the long-horizon savings research (cached in .cache/longterm.pkl).

Sources (all public, fetched at runtime):
  * Ken French data library: US market (Mkt-RF + RF), 10 value-weighted industry portfolios, 1-month T-bill (RF), 1926-
  * Robert Shiller ie_data.xls: CPI and 10-year Treasury yield (GS10), 1871-2023-09 (so the dataset ends 2023-09)
  * 10-year Treasury total return is APPROXIMATED from yields: monthly carry + repricing a par 10y bond at the new yield.

Everything is converted to REAL (inflation-adjusted) monthly returns, so euros are 'today's money'.
Assumptions that matter: US history stands in for 'global equities' (US was the 20th-century winner: see haircut in
longterm.py); EUR/USD currency effects are ignored.
"""
from __future__ import annotations

import io
import pathlib
import urllib.request
import zipfile

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "longterm.pkl"
FRENCH = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
IND = ["NoDur", "Durbl", "Manuf", "Enrgy", "HiTec", "Telcm", "Shops", "Hlth", "Utils", "Other"]


def _get(url: str) -> bytes:
    return urllib.request.urlopen(url, timeout=90).read()


def _french_factors() -> pd.DataFrame:
    z = zipfile.ZipFile(io.BytesIO(_get(FRENCH + "F-F_Research_Data_Factors_CSV.zip")))
    rows = []
    for line in z.read(z.namelist()[0]).decode("latin1").splitlines():
        p = line.split(",")
        if len(p) >= 5 and p[0].strip().isdigit() and len(p[0].strip()) == 6:
            rows.append([p[0].strip()] + [float(x) for x in p[1:5]])
    df = pd.DataFrame(rows, columns=["d", "MktRF", "SMB", "HML", "RF"])
    df.index = pd.PeriodIndex(df.pop("d"), freq="M")
    return df / 100


def _french_industries() -> pd.DataFrame:
    z = zipfile.ZipFile(io.BytesIO(_get(FRENCH + "10_Industry_Portfolios_CSV.zip")))
    t = z.read(z.namelist()[0]).decode("latin1").splitlines()
    i = [k for k, line in enumerate(t) if "Average Value Weighted Returns -- Monthly" in line][0]
    hdr = [h.strip() for h in t[i + 1].split(",")][1:]
    j, rows, idx = i + 2, [], []
    while t[j].strip():
        p = t[j].split(",")
        idx.append(p[0].strip())
        rows.append([float(x) for x in p[1:]])
        j += 1
    return pd.DataFrame(rows, columns=hdr, index=pd.PeriodIndex(idx, freq="M")) / 100


def _macro() -> pd.DataFrame:
    """CPI level and GS10 (percent) monthly from Shiller (1871 - 2023-09)."""
    sh = pd.read_excel(io.BytesIO(_get("http://www.econ.yale.edu/~shiller/data/ie_data.xls")), sheet_name="Data", skiprows=7, engine="xlrd")
    sh = sh[pd.to_numeric(sh["Date"], errors="coerce").notna()].copy()
    d = sh["Date"].astype(float).map(lambda v: f"{v:.2f}")
    sh.index = pd.PeriodIndex([f"{s[:4]}-{s[5:]}" for s in d], freq="M")
    out = pd.DataFrame({"CPI": pd.to_numeric(sh["CPI"], errors="coerce"), "GS10": pd.to_numeric(sh["Rate GS10"], errors="coerce")}).dropna()

    return out  # ends 2023-09 (end of the Shiller file); the dataset is truncated there on purpose


def bond_return(y: pd.Series) -> pd.Series:
    """Monthly total return of a rolling 10y par bond from yields in percent."""
    y = y / 100
    yp, yn = y.shift(1), y
    n = 19.83  # semi-annual periods left after one month
    c = yp / 2
    price = c * (1 - (1 + yn / 2) ** -n) / (yn / 2) + (1 + yn / 2) ** -n
    return (price - 1) + yp / 12


def build(refresh: bool = False) -> pd.DataFrame:
    """Monthly REAL returns: Mkt, 10 industries, Bond10, Bills; plus column 'infl' (monthly inflation)."""
    if CACHE.exists() and not refresh:
        return pd.read_pickle(CACHE)
    ff, ind, mac = _french_factors(), _french_industries(), _macro()
    nom = pd.DataFrame({"Mkt": ff["MktRF"] + ff["RF"], "Bills": ff["RF"]})
    nom = nom.join(ind[IND])
    nom["Bond10"] = bond_return(mac["GS10"])
    infl = mac["CPI"].pct_change()
    nom = nom.join(infl.rename("infl")).dropna()
    real = (1 + nom.drop(columns="infl")).div(1 + nom["infl"], axis=0) - 1
    real["infl"] = nom["infl"]
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    real.to_pickle(CACHE)
    return real


def cagr(r: pd.Series) -> float:
    return float((1 + r).prod() ** (12 / len(r)) - 1)


if __name__ == "__main__":
    d = build(refresh=True)
    print(d.index[0], "->", d.index[-1], len(d), "months")
    nom_infl = cagr(d["infl"])
    print(f"Inflation CAGR {100*nom_infl:.2f}%")
    for c in ["Mkt", "HiTec", "NoDur", "Hlth", "Utils", "Bond10", "Bills"]:
        r = d[c]
        print(f"{c:7} real CAGR {100*cagr(r):5.2f}%  vol {100*r.std()*12**.5:5.1f}%  worst real drawdown {100*((1+r).cumprod()/(1+r).cumprod().cummax()-1).min():5.1f}%")
