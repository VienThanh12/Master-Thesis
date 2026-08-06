#!/usr/bin/env python3
"""Generate thesis figures and LaTeX tables from measured benchmark data.

Reads the campaign JSONL (repeated, interleaved runs), the load-sweep CSV, and
the fault-injection taxonomy CSV, and writes vector (PDF) figures plus
ready-to-\\input LaTeX tables into ../figures/.

Everything here is reproducible: rerun after a bare-metal campaign to refresh
every figure and table with testbed-grade numbers.

Usage:
    python3 plot_figures.py \
        --campaign results/campaign-YYYYMMDD-HHMMSS.jsonl \
        --sweep    results/sweep-YYYYMMDD-HHMMSS.csv \
        --taxonomy ../faults/results/taxonomy.csv \
        --outdir   ../figures
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import random
import statistics
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

PRODUCERS_DEFAULT = 8
NS_PER_US = 1000.0

# Consistent per-variant styling across every figure.
VARIANT_STYLE = {
    ("cpp", "system"): ("C++ (system alloc)", "#1f77b4", "-", "o"),
    ("cpp", "jemalloc"): ("C++ (jemalloc)", "#2c5f8a", "--", "s"),
    ("rust", "system"): ("Rust (system alloc)", "#d62728", "-", "^"),
    ("rust", "jemalloc"): ("Rust (jemalloc)", "#8c2a2a", "--", "v"),
}


def bootstrap_ci(values, n_boot=2000, alpha=0.05, seed=12345):
    """Return (median, lo, hi) with a nonparametric bootstrap CI on the median."""
    vals = [v for v in values if v is not None]
    if not vals:
        return (float("nan"), float("nan"), float("nan"))
    if len(vals) == 1:
        return (vals[0], vals[0], vals[0])
    rng = random.Random(seed)
    n = len(vals)
    meds = []
    for _ in range(n_boot):
        sample = [vals[rng.randrange(n)] for _ in range(n)]
        meds.append(statistics.median(sample))
    meds.sort()
    lo = meds[int((alpha / 2) * n_boot)]
    hi = meds[int((1 - alpha / 2) * n_boot)]
    return (statistics.median(vals), lo, hi)


def load_campaign(path):
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def balance_repeats(rows):
    """Truncate every (lang, alloc, load) cell to the same number of repeats.

    A campaign interrupted part-way through a repeat leaves some cells with one
    more run than others. Comparing cells of unequal size would let the variant
    that happened to be measured first in the final repeat carry extra weight, and
    it would make "measured over N repeats" ambiguous. Keeping the first N runs of
    each cell, N the smallest cell count, restores the balanced factorial design
    the interleaving discipline assumes. The raw log is never modified.
    """
    by_cell = defaultdict(list)
    for r in rows:
        by_cell[(r["lang"], r["alloc"], offered_load(r))].append(r)
    n = min(len(v) for v in by_cell.values())
    kept = {id(r) for v in by_cell.values() for r in v[:n]}
    dropped = len(rows) - len(kept)
    if dropped:
        print(f"balancing: {dropped} run(s) from an incomplete repeat dropped; "
              f"using {n} repeats per cell")
    return [r for r in rows if id(r) in kept]


def offered_load(row):
    prod = row.get("producers", PRODUCERS_DEFAULT)
    return row["rate"] * prod


def group_metric(rows, metric_fn):
    """Group metric_fn(row) by (lang, alloc, offered) -> list of values."""
    g = defaultdict(list)
    for r in rows:
        g[(r["lang"], r["alloc"], offered_load(r))].append(metric_fn(r))
    return g


def variants_present(rows):
    seen = []
    for r in rows:
        key = (r["lang"], r["alloc"])
        if key not in seen:
            seen.append(key)
    order = list(VARIANT_STYLE.keys())
    return [k for k in order if k in seen]


def loads_present(rows):
    return sorted({offered_load(r) for r in rows})


# --------------------------------------------------------------------------- #
# Figure 1: tail latency (p99) vs offered load, with 95% CI band.
# --------------------------------------------------------------------------- #
def fig_latency_vs_load(rows, outdir, percentile="p99"):
    g = group_metric(rows, lambda r: r["lat_ns"][percentile] / NS_PER_US)
    loads = loads_present(rows)
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    for key in variants_present(rows):
        label, color, ls, mk = VARIANT_STYLE[key]
        xs, meds, los, his = [], [], [], []
        for load in loads:
            vals = g.get((key[0], key[1], load))
            if not vals:
                continue
            m, lo, hi = bootstrap_ci(vals)
            xs.append(load / 1000.0)
            meds.append(m)
            los.append(lo)
            his.append(hi)
        if not xs:
            continue
        ax.plot(xs, meds, ls, color=color, marker=mk, ms=4, lw=1.6, label=label)
        ax.fill_between(xs, los, his, color=color, alpha=0.15)
    ax.set_xlabel("Offered load (kops/s)")
    ax.set_ylabel(f"{percentile.upper()} latency (\u00b5s)")
    ax.set_yscale("log")
    ax.grid(True, which="both", ls=":", alpha=0.4)
    ax.legend(fontsize=8, framealpha=0.9)
    fig.tight_layout()
    out = os.path.join(outdir, "fig_latency_vs_load.pdf")
    fig.savefig(out)
    plt.close(fig)
    return out


# --------------------------------------------------------------------------- #
# Figure 2: throughput vs offered load (saturation view).
# --------------------------------------------------------------------------- #
def fig_throughput_vs_load(rows, outdir):
    g = group_metric(rows, lambda r: r["throughput_ops_s"] / 1000.0)
    loads = loads_present(rows)
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    ax.plot(
        [l / 1000.0 for l in loads],
        [l / 1000.0 for l in loads],
        color="0.6",
        ls=":",
        lw=1.2,
        label="ideal (offered = achieved)",
    )
    for key in variants_present(rows):
        label, color, ls, mk = VARIANT_STYLE[key]
        xs, meds, los, his = [], [], [], []
        for load in loads:
            vals = g.get((key[0], key[1], load))
            if not vals:
                continue
            m, lo, hi = bootstrap_ci(vals)
            xs.append(load / 1000.0)
            meds.append(m)
            los.append(lo)
            his.append(hi)
        ax.plot(xs, meds, ls, color=color, marker=mk, ms=4, lw=1.6, label=label)
        ax.fill_between(xs, los, his, color=color, alpha=0.15)
    ax.set_xlabel("Offered load (kops/s)")
    ax.set_ylabel("Achieved throughput (kops/s)")
    ax.grid(True, ls=":", alpha=0.4)
    ax.legend(fontsize=8, framealpha=0.9)
    fig.tight_layout()
    out = os.path.join(outdir, "fig_throughput_vs_load.pdf")
    fig.savefig(out)
    plt.close(fig)
    return out


# --------------------------------------------------------------------------- #
# Figure 3: latency-by-percentile "tail curve" at a representative load.
# --------------------------------------------------------------------------- #
def pick_representative_load(rows):
    """Highest offered load at which every variant stays below 5 ms at p99."""
    loads = loads_present(rows)
    g = group_metric(rows, lambda r: r["lat_ns"]["p99"] / NS_PER_US)
    variants = variants_present(rows)
    best = loads[0]
    for load in loads:
        ok = True
        for key in variants:
            vals = g.get((key[0], key[1], load))
            if not vals or statistics.median(vals) > 5000.0:
                ok = False
                break
        if ok:
            best = load
    return best


def fig_tail_percentiles(rows, outdir, load):
    pcts = ["p50", "p90", "p99", "p999"]
    pct_x = [50, 90, 99, 99.9]
    pct_labels = ["p50", "p90", "p99", "p99.9"]
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    for key in variants_present(rows):
        label, color, ls, mk = VARIANT_STYLE[key]
        ys = []
        for p in pcts:
            vals = [
                r["lat_ns"][p] / NS_PER_US
                for r in rows
                if r["lang"] == key[0]
                and r["alloc"] == key[1]
                and offered_load(r) == load
            ]
            ys.append(statistics.median(vals) if vals else float("nan"))
        ax.plot(range(len(pcts)), ys, ls, color=color, marker=mk, ms=5, lw=1.6, label=label)
    ax.set_xticks(range(len(pcts)))
    ax.set_xticklabels(pct_labels)
    ax.set_xlabel("Latency percentile")
    ax.set_ylabel("Latency (\u00b5s)")
    ax.set_yscale("log")
    ax.grid(True, which="both", ls=":", alpha=0.4)
    ax.legend(fontsize=8, framealpha=0.9)
    fig.tight_layout()
    out = os.path.join(outdir, "fig_tail_percentiles.pdf")
    fig.savefig(out)
    plt.close(fig)
    return out


# --------------------------------------------------------------------------- #
# Figure 4: resource use (peak RSS and CPU utilisation) per variant.
# --------------------------------------------------------------------------- #
def fig_resources(rows, outdir, load):
    variants = variants_present(rows)
    labels = [VARIANT_STYLE[k][0] for k in variants]
    colors = [VARIANT_STYLE[k][1] for k in variants]
    rss_med, cpu_med = [], []
    for key in variants:
        rss = [
            r["rss_peak_kb"] / 1024.0
            for r in rows
            if r["lang"] == key[0] and r["alloc"] == key[1] and offered_load(r) == load
        ]
        cpu = [
            r["cpu_pct"]
            for r in rows
            if r["lang"] == key[0] and r["alloc"] == key[1] and offered_load(r) == load
        ]
        rss_med.append(statistics.median(rss) if rss else 0.0)
        cpu_med.append(statistics.median(cpu) if cpu else 0.0)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.4, 3.6))
    xs = range(len(variants))
    short = [l.replace(" (", "\n(") for l in labels]
    ax1.bar(xs, rss_med, color=colors)
    ax1.set_xticks(xs)
    ax1.set_xticklabels(short, fontsize=7)
    ax1.set_ylabel("Peak RSS (MiB)")
    ax1.grid(True, axis="y", ls=":", alpha=0.4)
    ax2.bar(xs, cpu_med, color=colors)
    ax2.set_xticks(xs)
    ax2.set_xticklabels(short, fontsize=7)
    ax2.set_ylabel("CPU utilisation (%)")
    ax2.grid(True, axis="y", ls=":", alpha=0.4)
    fig.tight_layout()
    out = os.path.join(outdir, "fig_resources.pdf")
    fig.savefig(out)
    plt.close(fig)
    return out


# --------------------------------------------------------------------------- #
# Figure 5: fault-injection outcome matrix (heatmap).
# --------------------------------------------------------------------------- #
def fig_taxonomy(taxonomy_csv, outdir):
    if not os.path.exists(taxonomy_csv):
        return None
    rows = list(csv.DictReader(open(taxonomy_csv)))
    # Cases Rust prevents first, then the boundary cases it does not, so the figure
    # reads as a map of where the guarantee stops rather than as a scoreboard.
    prevented = [r for r in rows if "compile-time" in r["rust_compile"]]
    boundary = [r for r in rows if "compile-time" not in r["rust_compile"]]
    rows = prevented + boundary
    defects = [r["defect"].replace("_", " ") for r in rows]
    cols = ["C++ ASan", "C++ TSan", "Safe Rust"]

    # code: 2 = prevented at compile time (best), 1 = detected at runtime, 0 = missed.
    grid, labels = [], []
    for r in rows:
        asan_hit = r["cpp_asan"].strip() == "detected"
        tsan_hit = r["cpp_tsan"].strip() == "detected"
        rust_prevented = "compile-time" in r["rust_compile"]
        grid.append([1 if asan_hit else 0, 1 if tsan_hit else 0, 2 if rust_prevented else 0])
        labels.append([
            "runtime" if asan_hit else "missed",
            "runtime" if tsan_hit else "missed",
            "compile" if rust_prevented else "none",
        ])

    cmap = matplotlib.colors.ListedColormap(["#c0392b", "#e6b800", "#1e8449"])
    norm = matplotlib.colors.BoundaryNorm([-0.5, 0.5, 1.5, 2.5], cmap.N)

    fig, ax = plt.subplots(figsize=(6.6, 0.46 * len(defects) + 1.7))
    ax.imshow(grid, cmap=cmap, norm=norm, aspect="auto")
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels(cols, fontsize=9)
    ax.set_yticks(range(len(defects)))
    ax.set_yticklabels(defects, fontsize=9)
    for i in range(len(defects)):
        for j in range(len(cols)):
            ax.text(
                j, i, labels[i][j], ha="center", va="center",
                color="white", fontsize=8, fontweight="bold",
            )
    ax.set_xticks([x - 0.5 for x in range(1, len(cols))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(defects))], minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", length=0)

    # Mark where the compile-time guarantee stops. The label goes inside the axes
    # so it cannot widen the saved bounding box and squeeze the cells.
    if prevented and boundary:
        split = len(prevented) - 0.5
        ax.axhline(split, color="black", linewidth=2.0)
        ax.text(
            -0.5, split - 0.06, " boundary of the guarantee ",
            ha="left", va="bottom", fontsize=7.5, style="italic",
            bbox=dict(boxstyle="square,pad=0.15", facecolor="white",
                      edgecolor="black", linewidth=0.8),
        )

    legend = [
        Patch(facecolor="#1e8449", label="prevented at compile time"),
        Patch(facecolor="#e6b800", label="detected at runtime only"),
        Patch(facecolor="#c0392b", label="not detected / not prevented"),
    ]
    ax.legend(handles=legend, loc="upper center", bbox_to_anchor=(0.5, -0.14),
              ncol=3, fontsize=7, framealpha=0.9)
    fig.tight_layout()
    out = os.path.join(outdir, "fig_taxonomy.pdf")
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


# --------------------------------------------------------------------------- #
# LaTeX tables.
# --------------------------------------------------------------------------- #
def fig_ffi(metrics_json, outdir):
    """Bar chart: raw FFI crossing cost vs end-to-end op round-trip (log scale)."""
    if not os.path.exists(metrics_json):
        return None
    m = json.load(open(metrics_json))
    crossing = m.get("ffi_crossing_ns", 0.0)
    roundtrip = m.get("op_roundtrip_ns", 0.0)
    if crossing <= 0 or roundtrip <= 0:
        return None
    labels = ["Raw FFI crossing\n(uecm_abi_noop)", "End-to-end signaling op\n(submit+complete)"]
    vals = [crossing, roundtrip]
    colors = ["#1e8449", "#1f77b4"]

    fig, ax = plt.subplots(figsize=(6.0, 3.6))
    bars = ax.bar(range(2), vals, color=colors, width=0.55)
    ax.set_yscale("log")
    ax.set_xticks(range(2))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Cost per call (ns, log scale)")
    ax.grid(True, axis="y", which="both", ls=":", alpha=0.4)
    for b, v in zip(bars, vals):
        txt = f"{v:.2f} ns" if v < 100 else f"{v/1000.0:.1f} \u00b5s"
        ax.text(b.get_x() + b.get_width() / 2, v * 1.15, txt,
                ha="center", va="bottom", fontsize=9, fontweight="bold")
    ratio = roundtrip / crossing
    ax.set_title(f"FFI crossing is ~{ratio:,.0f}\u00d7 cheaper than one service op",
                 fontsize=9)
    ax.set_ylim(top=roundtrip * 4)
    fig.tight_layout()
    out = os.path.join(outdir, "fig_ffi_cost.pdf")
    fig.savefig(out)
    plt.close(fig)
    return out


def write_ffi_table(metrics_json, outdir):
    if not os.path.exists(metrics_json):
        return None
    m = json.load(open(metrics_json))
    rows = [
        ("C-ABI entry points", f"{m.get('entry_points', 0)}"),
        ("Seam size (Rust \\texttt{lib.rs})", f"{m.get('seam_loc_rust', 0)} LOC"),
        ("Hand-written C header", f"{m.get('header_loc', 0)} LOC"),
        ("\\texttt{unsafe} in core library", f"{m.get('unsafe_core', 0)}"),
        ("\\texttt{unsafe} in FFI seam", f"{m.get('unsafe_seam', 0)}"),
        ("Raw FFI crossing", f"{m.get('ffi_crossing_ns', 0):.2f} ns/call"),
        ("End-to-end signaling op", f"{m.get('op_roundtrip_ns', 0) / 1000.0:.1f} \\textmu s/call"),
    ]
    out = os.path.join(outdir, "tab_ffi.tex")
    with open(out, "w") as f:
        f.write(" \\\\\n".join(f"{k} & {v}" for k, v in rows) + "\n")
    return out


def fmt_us(ns):
    return f"{ns / NS_PER_US:.1f}"


def med_ci_cell(values, decimals=None):
    """Format a metric as `median $\\pm$ h`, h the half-width of the bootstrap 95% CI.

    The methodology commits to reporting a median with a nonparametric CI rather
    than a bare point estimate, so every numeric cell in the result tables carries
    its dispersion. A half-width is used instead of an explicit [lo, hi] interval
    only to keep the tables inside the text block; it is symmetrised as the larger
    of the two one-sided distances, so it never understates the interval.

    Precision adapts to magnitude: quoting a 20 ms latency to a tenth of a
    microsecond would be false precision, and it is also what pushes the LaTeX
    table past the text width once the sweep reaches overload.
    """
    med, lo, hi = bootstrap_ci(values)
    half = max(med - lo, hi - med)
    if decimals is None:
        decimals = 1 if abs(med) < 1000 else 0
    return f"{med:.{decimals}f}\\,$\\pm$\\,{half:.{decimals}f}"


def _subset(rows, key, load):
    return [
        r
        for r in rows
        if r["lang"] == key[0] and r["alloc"] == key[1] and offered_load(r) == load
    ]


def write_latency_table(rows, outdir, load):
    """Emit the body of tab:latency at the representative load (values in \u00b5s)."""
    lines = []
    for key in variants_present(rows):
        label = VARIANT_STYLE[key][0]
        sub = _subset(rows, key, load)
        if not sub:
            continue

        def cell(field):
            return med_ci_cell([r["lat_ns"][field] / NS_PER_US for r in sub])

        lines.append(
            f"{label} & {cell('p50')} & {cell('p99')} & {cell('p999')} & {cell('max')}"
        )
    out = os.path.join(outdir, "tab_latency.tex")
    with open(out, "w") as f:
        # Rows separated by \\ but no trailing \\, so \input can be followed by
        # \\\hline in the caller without a "Misplaced \noalign" boundary error.
        f.write(" \\\\\n".join(lines) + "\n")
    return out, load


def write_generated_macros(rows, outdir, load):
    """Emit the campaign's summary numbers as LaTeX macros.

    Every quantity the prose quotes about the campaign is defined here and used by
    name in the text, so a rerun on different hardware updates the narrative
    together with the figures instead of leaving stale literals behind.
    """
    variants = variants_present(rows)
    loads = loads_present(rows)
    repeats = min(len(_subset(rows, k, l)) for k in variants for l in loads)

    def med_at(key, load_, fn):
        sub = _subset(rows, key, load_)
        return statistics.median([fn(r) for r in sub]) if sub else float("nan")

    thr_kops = lambda r: r["throughput_ops_s"] / 1000.0
    p99_us = lambda r: r["lat_ns"]["p99"] / NS_PER_US

    p50_us = lambda r: r["lat_ns"]["p50"] / NS_PER_US
    ach = [med_at(k, load, thr_kops) for k in variants]
    p99 = [med_at(k, load, p99_us) for k in variants]
    p50 = [med_at(k, load, p50_us) for k in variants]
    # Widest 95% CI half-width on any single variant's p99 at the representative
    # load, against the spread between variants. When the former exceeds the
    # latter the measurement cannot order the variants at all, which is a finding
    # about the environment rather than about the languages.
    p99_ci = []
    for k in variants:
        sub = _subset(rows, k, load)
        if sub:
            m, lo, hi = bootstrap_ci([p99_us(r) for r in sub])
            p99_ci.append(max(m - lo, hi - m))
    # Saturation knee: highest achieved throughput anywhere in the sweep, taken as
    # the minimum across variants so the quoted knee holds for all four.
    knee = min(max(med_at(k, l, thr_kops) for l in loads) for k in variants)
    # Highest offered load at which every variant still tracks the ideal line to 5%.
    tracking = [
        l for l in loads
        if all(med_at(k, l, thr_kops) >= 0.95 * l / 1000.0 for k in variants)
    ]

    macros = {
        "ReprLoad": f"{load / 1000.0:.0f}",
        "ReprLoadAch": f"{statistics.median(ach):.1f}",
        "ReprLoadShortfall": f"{100.0 * (1 - statistics.median(ach) / (load / 1000.0)):.1f}",
        "SatKnee": f"{knee:.0f}",
        "TrackingLoad": f"{max(tracking) / 1000.0:.0f}" if tracking else "0",
        "NRepeats": str(repeats),
        "NLoadLevels": str(len(loads)),
        "NVariants": str(len(variants)),
        "NRuns": str(len(rows)),
        "PNineNineSpread": f"{100.0 * (max(p99) / min(p99) - 1):.0f}",
        "PFiftySpread": f"{100.0 * (max(p50) / min(p50) - 1):.1f}",
        "PFiftyRange": f"{max(p50) - min(p50):.0f}",
        "PNineNineRange": f"{max(p99) - min(p99):.0f}",
        "PNineNineMaxCI": f"{max(p99_ci):.0f}" if p99_ci else "0",
        "MaxOfferedLoad": f"{max(loads) / 1000.0:.0f}",
    }
    out = os.path.join(outdir, "gen_macros.tex")
    with open(out, "w") as f:
        f.write("% Generated by bench/plot_figures.py -- do not edit by hand.\n")
        for k, v in macros.items():
            f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
    return out


def write_resource_table(rows, outdir, load):
    lines = []
    for key in variants_present(rows):
        label = VARIANT_STYLE[key][0]
        sub = _subset(rows, key, load)
        if not sub:
            continue
        thr = med_ci_cell([r["throughput_ops_s"] / 1000.0 for r in sub], decimals=2)
        rss = med_ci_cell([r["rss_peak_kb"] / 1024.0 for r in sub])
        cpu = med_ci_cell([r["cpu_pct"] for r in sub])
        lines.append(f"{label} & {thr} & {rss} & {cpu}")
    out = os.path.join(outdir, "tab_resource.tex")
    with open(out, "w") as f:
        f.write(" \\\\\n".join(lines) + "\n")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--campaign", default=None)
    ap.add_argument("--sweep", default=None)
    ap.add_argument("--taxonomy", default="../faults/results/taxonomy.csv")
    ap.add_argument("--ffi", default="../ffi/results/metrics.json")
    ap.add_argument("--outdir", default="../figures")
    ap.add_argument("--load", type=float, default=None,
                    help="Representative offered load (ops/s); auto if omitted.")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    outdir = os.path.abspath(os.path.join(here, args.outdir)) if not os.path.isabs(args.outdir) else args.outdir
    os.makedirs(outdir, exist_ok=True)

    campaign = args.campaign
    if campaign is None:
        cands = sorted(glob.glob(os.path.join(here, "results", "campaign-*.jsonl")))
        campaign = cands[-1] if cands else os.path.join(here, "results", "latest.jsonl")
    rows = balance_repeats(load_campaign(campaign))

    load = args.load if args.load is not None else pick_representative_load(rows)
    print(f"campaign: {campaign}  rows={len(rows)}  representative load={load:.0f} ops/s")

    produced = []
    produced.append(fig_latency_vs_load(rows, outdir))
    produced.append(fig_throughput_vs_load(rows, outdir))
    produced.append(fig_tail_percentiles(rows, outdir, load))
    produced.append(fig_resources(rows, outdir, load))
    tax = fig_taxonomy(os.path.abspath(os.path.join(here, args.taxonomy)) if not os.path.isabs(args.taxonomy) else args.taxonomy, outdir)
    if tax:
        produced.append(tax)

    ffi_json = os.path.abspath(os.path.join(here, args.ffi)) if not os.path.isabs(args.ffi) else args.ffi
    ffi_fig = fig_ffi(ffi_json, outdir)
    if ffi_fig:
        produced.append(ffi_fig)
    ffi_tab = write_ffi_table(ffi_json, outdir)
    if ffi_tab:
        produced.append(ffi_tab)

    lat_tab, _ = write_latency_table(rows, outdir, load)
    res_tab = write_resource_table(rows, outdir, load)
    macros = write_generated_macros(rows, outdir, load)
    produced.extend([lat_tab, res_tab, macros])

    for p in produced:
        print("wrote", os.path.relpath(p, here))


if __name__ == "__main__":
    main()
