#!/usr/bin/env python3
"""Plot a load-sweep CSV (latency vs offered load) produced by load_sweep.sh.

Usage:
    python3 bench/plot_sweep.py [sweep.csv] [--metric p99_ns] [--out sweep.png]

If no CSV is given, the most recent bench/results/sweep-*.csv is used. Requires
matplotlib (`pip install --user matplotlib`); without it, the script explains how
to install and exits without error.
"""
import csv
import glob
import os
import sys


def latest_csv():
    here = os.path.dirname(os.path.abspath(__file__))
    files = sorted(glob.glob(os.path.join(here, "results", "sweep-*.csv")))
    return files[-1] if files else None


def main():
    args = sys.argv[1:]
    metric = "p99_ns"
    out = None
    positional = []
    i = 0
    while i < len(args):
        if args[i] == "--metric":
            metric = args[i + 1]
            i += 2
        elif args[i] == "--out":
            out = args[i + 1]
            i += 2
        else:
            positional.append(args[i])
            i += 1

    path = positional[0] if positional else latest_csv()
    if not path or not os.path.exists(path):
        print("no sweep CSV found; run bench/load_sweep.sh first")
        return
    if out is None:
        out = os.path.splitext(path)[0] + f".{metric}.png"

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed. Install it with:")
        print("    pip install --user matplotlib")
        print(f"then re-run: python3 {sys.argv[0]} {path}")
        return

    series = {}
    with open(path) as f:
        for row in csv.DictReader(f):
            key = f'{row["lang"]}/{row["alloc"]}'
            series.setdefault(key, []).append(
                (float(row["offered_ops_s"]), float(row[metric]) / 1000.0)  # ns -> us
            )

    plt.figure(figsize=(8, 5))
    for key, pts in sorted(series.items()):
        pts.sort()
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        plt.plot(xs, ys, marker="o", label=key)
    plt.xlabel("offered load (ops/s)")
    plt.ylabel(f"{metric} latency (us)")
    plt.yscale("log")
    plt.title(f"UECM load sweep - {metric} vs offered load")
    plt.grid(True, which="both", ls=":", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    print("wrote", out)


if __name__ == "__main__":
    main()
