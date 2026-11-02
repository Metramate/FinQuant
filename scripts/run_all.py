"""Run the whole portfolio-manager suite in the right order.

    python scripts/run_all.py            # everything
    python scripts/run_all.py --skip watchlist signals

Order matters: backtest first (the report's trim advice is gated by it), then the report, then the rest.
Each step is a separate script and can be run alone. Output goes to reports/latest/ (+ reports/history/ snapshots).
"""
import argparse
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
STEPS = ["backtest", "portfolio_manager", "stress", "signals", "fq_optimise", "watchlist", "checkin", "tax_lots"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip", nargs="*", default=[], choices=STEPS)
    a = ap.parse_args()
    failed = []
    for step in STEPS:
        if step in a.skip:
            continue
        if step == "tax_lots" and not (HERE.parent / "data" / "my-lots.csv").exists():
            print("[skip] tax_lots: run `python scripts/tax_lots.py --init` once to create data/my-lots.csv")
            continue
        t = time.time()
        r = subprocess.run([sys.executable, "-W", "ignore", str(HERE / f"{step}.py")], capture_output=True, text=True)
        ok = r.returncode == 0
        print(f"[{'ok' if ok else 'FAILED'}] {step} ({time.time() - t:.0f}s)")
        if not ok:
            failed.append(step)
            print(r.stderr[-1500:])
    print("\nReports: reports/latest/  (REPORT.md is the main one; checkin.md, stress.md, signals.md, backtest.md, fq_optimise.md, watchlist.md, tax_lots.md)")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
