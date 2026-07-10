#!/usr/bin/env python3
"""Aggregate a repeated load-sweep campaign into per-(variant, load) statistics.

Reads the raw JSONL emitted by campaign.sh (one bench result per line, several
repeats per (variant, rate) point), and for each metric computes the median across
repeats plus a 95% confidence interval of the median via nonparametric bootstrap
(dependency-free, seeded for reproducibility).

Outputs:
  --out  <csv>   tidy wide CSV: one row per (lang, alloc, workload, offered load)
                 with <metric>_median / _lo / _hi columns for plotting + tables.
  --tex  <tex>   a LaTeX latency table at a representative load (default: the
                 highest offered load at which the achieved throughput still keeps
                 up with the offer, i.e. just before saturation).

Usage:
  python3 aggregate.py campaign-XXXX.jsonl --out agg.csv --tex tab.tex --producers 8
"""
import argparse
import json
import random
import statistics as st

# Metrics pulled from each bench JSON record. (key in record, column stem)
LAT = ["p50", "p90", "p99", "p999", "max", "mean"]


def load_rows(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def sample_metrics(r):
    """Flatten one bench record into a {metric: value} dict."""
    L = r["lat_ns"]
    m = {f"{k}_ns": float(L[k]) for k in LAT}
    m["achieved_ops_s"] = float(r["throughput_ops_s"])
    m["rss_peak_kb"] = float(r.get("rss_peak_kb", 0))
    m["cpu_pct"] = float(r.get("cpu_pct", 0.0))
    return m


def bootstrap_median_ci(xs, iters=2000, alpha=0.05, rng=None):
    """Return (median, lo, hi) with a bootstrap CI of the median."""
    xs = list(xs)
    n = len(xs)
    med = st.median(xs)
    if n <= 1:
        return med, med, med
    rng = rng or random.Random(12345)
    meds = []
    for _ in range(iters):
        resample = [xs[rng.randrange(n)] for _ in range(n)]
        meds.append(st.median(resample))
    meds.sort()
    lo = meds[int((alpha / 2) * iters)]
    hi = meds[min(iters - 1, int((1 - alpha / 2) * iters))]
    return med, lo, hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--tex", default=None)
    ap.add_argument("--producers", type=int, default=None)
    ap.add_argument("--rep-load", type=float, default=None,
                    help="offered ops/s to use for the LaTeX table (default: auto)")
    args = ap.parse_args()

    rows = load_rows(args.jsonl)
    if not rows:
        print("no rows in", args.jsonl)
        return

    # Group by (lang, alloc, workload, offered load).
    groups = {}
    for r in rows:
        producers = args.producers or int(r.get("producers", 1))
        offered = round(float(r.get("rate", 0.0)) * producers)
        key = (r["lang"], r["alloc"], r.get("workload", "-"), offered)
        groups.setdefault(key, []).append(sample_metrics(r))

    metrics = [f"{k}_ns" for k in LAT] + ["achieved_ops_s", "rss_peak_kb", "cpu_pct"]
    rng = random.Random(12345)

    # Build aggregated rows.
    agg = []
    for (lang, alloc, workload, offered), samples in sorted(groups.items()):
        rec = {"lang": lang, "alloc": alloc, "workload": workload,
               "offered_ops_s": offered, "n": len(samples)}
        for m in metrics:
            xs = [s[m] for s in samples]
            med, lo, hi = bootstrap_median_ci(xs, rng=rng)
            rec[f"{m}_median"] = med
            rec[f"{m}_lo"] = lo
            rec[f"{m}_hi"] = hi
        agg.append(rec)

    # Write tidy CSV.
    cols = ["lang", "alloc", "workload", "offered_ops_s", "n"]
    for m in metrics:
        cols += [f"{m}_median", f"{m}_lo", f"{m}_hi"]
    with open(args.out, "w") as f:
        f.write(",".join(cols) + "\n")
        for rec in agg:
            f.write(",".join(_fmt(rec.get(c, "")) for c in cols) + "\n")
    print("wrote", args.out, f"({len(agg)} points, n={agg[0]['n']} repeats)")

    if args.tex:
        write_latex(agg, args.tex, args.rep_load)


def _fmt(v):
    if isinstance(v, float):
        return f"{v:.3f}" if abs(v) < 1000 else f"{v:.0f}"
    return str(v)


def choose_rep_load(agg):
    """Highest offered load where achieved still tracks the offer (pre-saturation)."""
    best = None
    for rec in agg:
        off = rec["offered_ops_s"]
        ach = rec["achieved_ops_s_median"]
        if off > 0 and ach >= 0.95 * off:
            best = off if best is None else max(best, off)
    if best is None:  # everything saturated; fall back to the largest offered load
        best = max(rec["offered_ops_s"] for rec in agg)
    return best


def write_latex(agg, path, rep_load):
    load = rep_load if rep_load is not None else choose_rep_load(agg)
    # rows for this load, one per variant
    at = [r for r in agg if r["offered_ops_s"] == load]
    at.sort(key=lambda r: (r["lang"], r["alloc"]))

    def us(rec, stem):  # ns median -> microseconds
        return rec[f"{stem}_ns_median"] / 1000.0

    lines = []
    lines.append("% Auto-generated by bench/aggregate.py -- latency at a representative load.")
    lines.append("% Values are the median over repeats; latencies in microseconds.")
    lines.append("\\begin{table}")
    lines.append("\\centering")
    lines.append(f"\\caption{{Latency at a representative offered load of {load:g} ops/s "
                 f"(median over $n$ repeats; microseconds).\\label{{tab:latency}}}}")
    lines.append("\\begin{tabular}{l l r r r r r r}")
    lines.append("\\hline\\hline")
    lines.append("Language & Alloc & achieved (op/s) & mean & p50 & p99 & p99.9 & max \\\\")
    lines.append("\\hline")
    for r in at:
        lines.append(
            f"{r['lang']} & {r['alloc']} & {r['achieved_ops_s_median']:.0f} & "
            f"{us(r,'mean'):.1f} & {us(r,'p50'):.1f} & {us(r,'p99'):.1f} & "
            f"{us(r,'p999'):.1f} & {us(r,'max'):.1f} \\\\")
    lines.append("\\hline")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("wrote", path, f"(representative load = {load:g} ops/s)")


if __name__ == "__main__":
    main()
