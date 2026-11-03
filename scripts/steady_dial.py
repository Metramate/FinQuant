"""Does a bigger steady share raise the chance of EUR 1M? Steady sectors (staples + health care) vs your thesis (tech sector as proxy).

    python scripts/steady_dial.py

For goal ages 38 and 40 and saving S per month after the job starts (EUR 1,000/mo before, job at month 12): share of steady sectors in the NEW money
from 0% to 60%, the rest in the tech sector (a proxy for your thesis; crypto has no long history so it is NOT in this test). Same 100 years of US
data and block bootstrap as horizon.py, with the same de-risking in the last 4 years. In-sample on hindsight-chosen sectors: read it as a lean.
"""
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from horizon import AGE0, TARGET, book_end, eq_share, idx_boot, journey, need_for, plan_vec, unit_ends  # noqa: E402
from longterm import md_table  # noqa: E402
from longterm_data import build  # noqa: E402

A = build()
T = len(A)
steady = 0.5 * A["NoDur"] + 0.5 * A["Hlth"]
J = 12
rows = {}
for g in (38, 40):
    Y = g - AGE0
    m = Y * 12
    rng = np.random.default_rng(3)
    idx = idx_boot(T, 4000, m, rng)
    Hit = A["HiTec"].values[idx]
    Wb = book_end(Hit)
    e = eq_share(m, Y)
    for s in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6):
        eq = s * steady.values[idx] + (1 - s) * A["HiTec"].values[idx]
        R = e[None, :] * eq + (1 - e)[None, :] * A["Bond10"].values[idx]
        Wp, Wq = unit_ends(R, J)
        jr = journey(R, Hit, plan_vec(m, J, 5000))
        rows[(g, f"{int(100*s)}%")] = {"P(EUR 1M) S=5,000": float(((Wb + Wp + 5000 * Wq) >= TARGET).mean()), "P(EUR 1M) S=6,667": float(((Wb + Wp + 6666.67 * Wq) >= TARGET).mean()),
                                       "bad-case wealth (p10)": float(np.percentile(Wb + Wp + 5000 * Wq, 10)), "lowest vs money put in (p10)": float(np.percentile(jr["min_ratio"], 10)),
                                       "saving needed, 80% chance": float(need_for(0.8, Wb, Wp, Wq))}
df = pd.DataFrame(rows).T
df.index.names = ["goal age", "steady share"]
out = []
for g in (38, 40):
    sub = df.xs(g, level=0).copy(); sub.index.name = f"steady share (age {g})"
    out += [md_table(sub, {"P(EUR 1M) S=5,000": "{:.0%}", "P(EUR 1M) S=6,667": "{:.0%}", "bad-case wealth (p10)": "{:,.0f}", "lowest vs money put in (p10)": "{:.2f}", "saving needed, 80% chance": "{:,.0f}"}), ""]
txt = "# Steady share dial (rest in the tech sector as a proxy for the thesis)\n\n" + "\n".join(out)
(pathlib.Path(__file__).resolve().parent.parent / "reports" / "latest" / "steady_dial.md").write_text(txt + "\n")
print(txt)
