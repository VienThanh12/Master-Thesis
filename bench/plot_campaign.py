#!/usr/bin/env python3
"""Plot an aggregated campaign CSV (from aggregate.py): median latency vs offered
load per variant, with a shaded 95% bootstrap-CI band.

Usage:
    python3 bench/plot_campaign.py [agg.csv] [--metric p99_ns] [--out file.png]

If no CSV is given, the most recent bench/results/campaign-*.agg.csv is used.
Requires matplotlib; without it the script explains how to install and exits 0.
"""
import argparse
import csv
import glob
import os


def latest_agg():
    here = os.path.dirname(os.path.abspath(__file__))
    files = sorted(glob.glob(os.path.join(here, "results", "campaign-*.agg.csv")))
    return files[-1] if files else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="?", default=None)
    ap.add_argument("--metric", default="p99_ns")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    path = args.csv or latest_agg()
    if not path or not os.path.exists(path):
        print("no aggregated campaign CSV found; run bench/campaign.sh first")
        return
    metric = args.metric
    out = args.out or (os.path.splitext(path)[0] + f".{metric}.png")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed. Install it with:")
        print("    pip install --user matplotlib")
        print(f"then re-run: python3 bench/plot_campaign.py {path} --metric {metric}")
        return

    med_c, lo_c, hi_c = f"{metric}_median", f"{metric}_lo", f"{metric}_hi"
    series = {}
    with open(path) as f:
        rdr = csv.DictReader(f)
        if med_c not in rdr.fieldnames:
            print(f"metric '{metric}' not in {path}; available stems: "
                  + ", ".join(sorted({c[:-7] for c in rdr.fieldnames if c.endswith('_median')})))
            return
        for row in rdr:
            key = f'{row["lang"]}/{row["alloc"]}'
            series.setdefault(key, []).append((
                float(row["offered_ops_s"]),
                float(row[med_c]) / 1000.0,   # ns -> us
                float(row[lo_c]) / 1000.0,
                float(row[hi_c]) / 1000.0,
            ))

    plt.figure(figsize=(8, 5))
    for key, pts in sorted(series.items()):
        pts.sort()
        xs = [p[0] for p in pts]
        med = [p[1] for p in pts]
        lo = [p[2] for p in pts]
        hi = [p[3] for p in pts]
        line, = plt.plot(xs, med, marker="o", label=key)
        plt.fill_between(xs, lo, hi, color=line.get_color(), alpha=0.18)
    # Human-readable metric label: p999_ns -> "p99.9", mean_ns -> "mean", etc.
    stem = metric[:-3] if metric.endswith("_ns") else metric
    pretty = {"p50": "p50", "p90": "p90", "p99": "p99", "p999": "p99.9",
              "max": "max", "mean": "mean"}.get(stem, stem)
    plt.xlabel("offered load (ops/s)")
    plt.ylabel(f"{pretty} latency (\u00b5s)")
    plt.yscale("log")
    plt.title(f"UECM load sweep \u2014 {pretty} latency vs offered load (median \u00b1 95% CI)")
    plt.grid(True, which="both", ls=":", alpha=0.5)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out, dpi=120)
    print("wrote", out)


if __name__ == "__main__":
    main()
