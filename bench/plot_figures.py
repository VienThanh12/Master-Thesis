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
import math
import os
import random
import re
import statistics
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

PRODUCERS_DEFAULT = 8
NS_PER_US = 1000.0

# Paired permutation test: enumerate all 2**n sign assignments up to this many
# repeats, and fall back to a seeded Monte Carlo sample above it. Set to cover the
# campaign's repeat count, because the thesis quotes the attainable p floor as a
# property of an exact test: at 20 repeats the sampled branch floors at
# 2 / PERM_SAMPLES = 1e-5 rather than at 2 / 2**20 = 1.9e-6, and quoting the
# latter while computing the former would overstate the design's resolving power.
EXACT_MAX = 20
PERM_SAMPLES = 200000

# How a language is named in prose, so a generated macro reads as the thesis
# writes it rather than as the campaign records it.
LANG_LABEL = {"cpp": "C++", "rust": "Rust"}

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


def paired_permutation_test(a, b):
    """Exact two-sided paired permutation test. Returns (median_diff, p, n_pairs).

    The campaign interleaves the four variants inside every repeat, so run i of
    one variant and run i of another were measured back to back under the same
    ambient conditions. That makes the repeats a matched design rather than two
    independent samples, and it is what lets the noise common to a repeat cancel
    in the pairwise difference instead of inflating both variances.

    Under the null hypothesis that a pair differs only by run-to-run noise, the
    sign of each paired difference is exchangeable. With n repeats there are
    exactly 2**n sign assignments, so for the repeat counts used here the test is
    enumerated in full rather than sampled: the p-value is exact, and no
    distributional assumption is imposed on a latency sample that is known to be
    skewed. The statistic is the mean of the paired differences; the effect size
    reported alongside it is their median, to stay consistent with the
    median-based reporting used everywhere else.

    Note the resolving power this buys is bounded by n: the smallest attainable
    two-sided p-value is 2 / 2**n, so a campaign of 7 repeats cannot report a
    p below about 0.016 no matter how large the effect.

    Beyond EXACT_MAX pairs the enumeration is replaced by a seeded Monte Carlo
    sample over sign assignments, which keeps a larger bare-metal campaign
    tractable at the cost of making the p-value an estimate rather than exact.
    """
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    n = len(pairs)
    if n == 0:
        return (float("nan"), float("nan"), 0)
    diffs = [y - x for x, y in pairs]
    observed = abs(sum(diffs))
    at_least_as_extreme = 0
    if n <= EXACT_MAX:
        # Enumerate every sign assignment via the bits of an n-bit counter.
        total_assignments = 1 << n
        for mask in range(total_assignments):
            total = 0.0
            for i, d in enumerate(diffs):
                total += -d if (mask >> i) & 1 else d
            if abs(total) >= observed - 1e-12:
                at_least_as_extreme += 1
    else:
        rng = random.Random(20260807)
        total_assignments = PERM_SAMPLES
        for _ in range(total_assignments):
            total = sum(d if rng.getrandbits(1) else -d for d in diffs)
            if abs(total) >= observed - 1e-12:
                at_least_as_extreme += 1
    return (statistics.median(diffs), at_least_as_extreme / float(total_assignments), n)


def paired_tost(a, b, delta):
    """Two one-sided paired permutation tests against an equivalence margin.

    A non-significant paired test supports nothing. It is consistent with a real
    effect the campaign was too small to see, which is why the statistical
    treatment has to spend a paragraph on the attainable floor, and why the honest
    reading of the tail is "cannot tell" rather than "equivalent". TOST asks the answerable
    question instead: not whether the difference is zero, which no experiment can
    establish, but whether it is small enough not to matter.

    The null is that the true difference is at least as large as ``delta`` in one
    direction or the other, and the two one-sided tests reject it from both sides.
    Rejecting both licenses "equivalent within +/- delta", which is a positive
    claim with its own stated limit -- not the over-claim of calling a null result
    equivalence.

    Under the shift null the differences minus the margin are symmetric about
    zero, so sign flipping is exactly as valid here as in the two-sided test
    above, and the same enumeration is reused. The returned p is the larger of
    the two one-sided values, which is the TOST p-value.
    """
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    n = len(pairs)
    if n == 0 or delta <= 0:
        return (float("nan"), n)
    diffs = [y - x for x, y in pairs]

    def one_sided(shifted, upper):
        """P(permuted sum at least as extreme as observed), in one direction."""
        observed = sum(shifted)
        count = 0
        if n <= EXACT_MAX:
            total_assignments = 1 << n
            for mask in range(total_assignments):
                total = 0.0
                for i, d in enumerate(shifted):
                    total += -d if (mask >> i) & 1 else d
                if (total <= observed + 1e-12) if upper else (total >= observed - 1e-12):
                    count += 1
        else:
            rng = random.Random(20260814)
            total_assignments = PERM_SAMPLES
            for _ in range(total_assignments):
                total = sum(d if rng.getrandbits(1) else -d for d in shifted)
                if (total <= observed + 1e-12) if upper else (total >= observed - 1e-12):
                    count += 1
        return count / float(total_assignments)

    # H0+: true difference >= +delta, rejected when the shifted sum is small.
    # H0-: true difference <= -delta, rejected when the shifted sum is large.
    p_upper = one_sided([d - delta for d in diffs], upper=True)
    p_lower = one_sided([d + delta for d in diffs], upper=False)
    return (max(p_upper, p_lower), n)


def equivalence_bound(a, b, alpha=0.05, n_boot=2000, seed=12345):
    """Smallest margin at which the paired difference can be called equivalent.

    Choosing an equivalence margin invites an argument about the margin, and a
    margin picked once the data is in is not a margin at all. Inverting the test
    avoids both: rather than asking whether the difference is inside some chosen
    delta, report the tightest delta the data supports and let the reader apply
    their own threshold to it.

    This uses the standard confidence-interval reading of TOST -- equivalence at
    level alpha holds exactly when the (1 - 2*alpha) interval lies inside
    [-delta, +delta] -- so the bound is the larger absolute endpoint of a 90%
    bootstrap interval on the paired difference. Note the 90%: a 95% interval
    would give a two-sided test at 0.025 per side and overstate the bound.

    Returns the bound in the metric's own units, so "the paired median difference
    is within +/- 1.6 microseconds" replaces "p = 0.7", which said nothing.
    """
    paired = [y - x for x, y in zip(a, b) if x is not None and y is not None]
    if not paired:
        return float("nan")
    rng = random.Random(seed)
    n = len(paired)
    medians = []
    for _ in range(n_boot):
        medians.append(statistics.median([paired[rng.randrange(n)] for _ in range(n)]))
    medians.sort()
    lo = medians[int(alpha * n_boot)]
    hi = medians[min(n_boot - 1, int((1.0 - alpha) * n_boot))]
    return max(abs(lo), abs(hi))


def attainable_floor(n):
    """Smallest two-sided p the paired test can return at n pairs.

    Mirrors the branch taken in paired_permutation_test rather than assuming the
    exact one, so the floor the thesis quotes cannot claim a resolution the
    computation did not deliver.
    """
    if n <= 0:
        return 1.0
    if n <= EXACT_MAX:
        return 2.0 / (1 << n)
    return 2.0 / PERM_SAMPLES


def holm_adjust(pvalues):
    """Holm-Bonferroni step-down adjustment for a family of p-values.

    Every metric in the result tables is tested for both allocators, so the
    family-wise error rate has to be controlled or the chance of one spurious
    "significant" difference grows with the number of comparisons. Holm is used
    rather than plain Bonferroni because it is uniformly more powerful while
    making no assumption about dependence between the tests.
    """
    m = len(pvalues)
    order = sorted(range(m), key=lambda i: pvalues[i])
    adjusted = [0.0] * m
    running = 0.0
    for rank, idx in enumerate(order):
        val = (m - rank) * pvalues[idx]
        running = max(running, val)
        adjusted[idx] = min(1.0, running)
    return adjusted


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
# Figure 2b: the same two sweeps as one two-panel figure, for the thesis.
#
# The single-panel versions above are kept because build_deck.py places them
# side by side on their own slide, where two separate images are what the layout
# wants. The thesis reads them as a pair against one x axis, so it takes this
# one instead and pays a single caption and a single block of float whitespace.
# (a) keeps the four variants on one linear scale, because that is where they
# separate by a few microseconds and can be compared at a glance. In (b) and
# (c) the system allocator and jemalloc follow one path, so drawing them in
# one panel hides the second stroke. Each variant gets its own panel there.
# --------------------------------------------------------------------------- #
def fig_load_sweep(rows, outdir, percentile="p99"):
    loads = loads_present(rows)
    variants = variants_present(rows)
    xs_ideal = [l / 1000.0 for l in loads]
    sweep_color = {
        ("cpp", "system"): "#2171b5",
        ("cpp", "jemalloc"): "#08306b",
        ("rust", "system"): "#cb181d",
        ("rust", "jemalloc"): "#67000d",
    }
    dash = {
        ("cpp", "system"): "-",
        ("cpp", "jemalloc"): (0, (5, 2)),
        ("rust", "system"): "-",
        ("rust", "jemalloc"): (0, (5, 2)),
    }
    short_name = {
        ("cpp", "system"): "C++ system",
        ("cpp", "jemalloc"): "C++ jemalloc",
        ("rust", "system"): "Rust system",
        ("rust", "jemalloc"): "Rust jemalloc",
    }

    fig = plt.figure(figsize=(9.6, 8.8))
    gs = fig.add_gridspec(
        3, 4, height_ratios=[1.05, 1.15, 1.05],
        left=0.08, right=0.985, top=0.94, bottom=0.06,
        hspace=0.58, wspace=0.18,
    )
    ax_a = fig.add_subplot(gs[0, :])

    def series(g, key, load_max=None):
        label, _color, _ls, mk = VARIANT_STYLE[key]
        color = sweep_color[key]
        xs, meds, los, his = [], [], [], []
        for load in loads:
            if load_max is not None and load > load_max:
                continue
            vals = g.get((key[0], key[1], load))
            if not vals:
                continue
            m, lo, hi = bootstrap_ci(vals)
            xs.append(load / 1000.0)
            meds.append(m)
            los.append(lo)
            his.append(hi)
        return label, color, mk, xs, meds, los, his

    def draw(ax, g, key, z, load_max=None, band=True, markers=True):
        label, color, mk, xs, meds, los, his = series(g, key, load_max)
        if not xs:
            return
        if band:
            ax.fill_between(xs, los, his, color=color, alpha=0.13, lw=0, zorder=1)
        if dash[key] == "-":
            ax.plot(
                xs, meds, color=color, lw=2.6, linestyle="-",
                solid_capstyle="round", zorder=z,
            )
        else:
            # A light gap cut into the solid line, then the dashed stroke in it,
            # so the second allocator is not hidden where the two agree.
            ax.plot(
                xs, meds, color="white", lw=4.2, linestyle=dash[key],
                solid_capstyle="butt", zorder=z,
            )
            ax.plot(
                xs, meds, color=color, lw=1.8, linestyle=dash[key],
                solid_capstyle="butt", zorder=z + 0.5,
            )
        if markers:
            ax.plot(
                xs, meds, linestyle="none", marker=mk, ms=6.5, color=color,
                markerfacecolor=color, markeredgecolor="white", markeredgewidth=0.7,
                zorder=z + 1,
            )

    g_lat = group_metric(rows, lambda r: r["lat_ns"][percentile] / NS_PER_US)
    # Last load at which every variant is still on the flat region. The next
    # rung is where C++ leaves a linear scale of tens of microseconds.
    tracking = None
    for load in loads:
        meds = []
        for key in variants:
            vals = g_lat.get((key[0], key[1], load))
            if not vals:
                meds = []
                break
            meds.append(statistics.median(vals))
        if not meds:
            continue
        if max(meds) > 5 * min(meds):
            break
        tracking = load

    # ---- (a) four variants below the knee, linear ------------------------ #
    for z, key in enumerate(variants):
        draw(ax_a, g_lat, key, z=3 + 2 * z, load_max=tracking, band=False)
    flat_y = []
    for key in variants:
        _label, _color, _mk, _xs, meds, _los, _his = series(g_lat, key, tracking)
        flat_y.extend(meds)
    pad = 1.0
    ax_a.set_ylim(min(flat_y) - pad, max(flat_y) + pad)
    ax_a.set_xlim(left=0)
    ax_a.set_xlabel("Offered load (kops/s)")
    ax_a.set_ylabel(f"{percentile} latency (\u00b5s)")
    ax_a.set_title("(a) Below the knee, linear scale", fontsize=11, loc="left")
    ax_a.grid(True, ls=":", alpha=0.45)
    ax_a.set_axisbelow(True)

    # ---- (b) and (c): one variant per panel, shared scale within the row -- #
    def variant_row(row, g, ylabel, yscale=None, ylim=None, ideal=False):
        left = fig.add_subplot(gs[row, 0])
        axes = [left]
        for i in range(1, 4):
            axes.append(fig.add_subplot(gs[row, i], sharex=left, sharey=left))
        if yscale:
            for ax in axes:
                ax.set_yscale(yscale)
        for ax, key in zip(axes, variants):
            label, color, mk, xs, meds, los, his = series(g, key)
            if ideal:
                ax.plot(
                    xs_ideal, xs_ideal, color="0.55", lw=1.15,
                    linestyle=(0, (1.2, 1.5)), zorder=2,
                )
            ax.fill_between(xs, los, his, color=color, alpha=0.18, lw=0, zorder=1)
            ax.plot(xs, meds, color=color, lw=2.4, solid_capstyle="round", zorder=3)
            ax.plot(
                xs, meds, linestyle="none", marker=mk, ms=5.5, color=color,
                markerfacecolor=color, markeredgecolor="white", markeredgewidth=0.6,
                zorder=4,
            )
            ax.set_title(short_name[key], fontsize=9, color=color, pad=3)
            ax.grid(True, which="major", ls=":", alpha=0.45)
            ax.set_axisbelow(True)
            ax.tick_params(labelsize=7)
            ax.set_xlabel("Offered load (kops/s)", fontsize=7.5)
            if ax is not left:
                ax.tick_params(labelleft=False)
        if ylim:
            left.set_ylim(*ylim)
        left.set_xlim(left=0)
        left.set_ylabel(ylabel, fontsize=8)
        return left

    ax_b = variant_row(1, g_lat, f"{percentile} latency (\u00b5s)", yscale="log")
    g_thr = group_metric(rows, lambda r: r["throughput_ops_s"] / 1000.0)
    ax_c = variant_row(
        2, g_thr, "Achieved throughput\n(kops/s)",
        ylim=(0, max(xs_ideal) * 1.08), ideal=True,
    )
    for anchor, text in (
        (ax_b, "(b) Whole sweep, log scale. One variant per panel."),
        (ax_c, "(c) Achieved throughput. The dotted line matches the offered load."),
    ):
        pos = anchor.get_position()
        fig.text(0.5, pos.y1 + 0.025, text, ha="center", va="bottom", fontsize=10)

    out = os.path.join(outdir, "fig_load_sweep.pdf")
    fig.savefig(out)
    plt.close(fig)
    return out


# --------------------------------------------------------------------------- #
# Figure 3: latency-by-percentile "tail curve" at a representative load.
# --------------------------------------------------------------------------- #
#: The operating point the below-saturation tables and tests report, in ops/s.
#:
#: This is pinned rather than derived, and the reason is a finding rather than a
#: convenience. The original rule, kept below as deadline_limited_load(), took the
#: busiest swept load at which every variant held p99 under 5 ms. On the
#: virtualised guest that rule returned 56 kops/s because p99 there was 4667 us at
#: that load, a hair under the threshold: the rule was locating where the host's
#: noise reached 5 ms, not where the service stopped meeting a deadline. On a
#: quiet bare-metal host p99 at the same load is 76 us, so the same rule climbs
#: until capacity binds and returns the tracking limit itself, collapsing the
#: representative point onto the saturation knee. One rule, two different
#: quantities, decided by how noisy the machine was.
#:
#: Holding the point fixed costs the appearance of derivation and buys two things
#: the derived version cannot give: the two hosts are compared at the same offered
#: load, and the point stays below saturation on both, which every below-saturation
#: claim in the thesis and the exclusion of achieved throughput from the test
#: family already assume.
REPR_LOAD_OPS = 56000


def deadline_limited_load(rows, deadline_us=5000.0):
    """Highest offered load at which every variant stays below the p99 deadline.

    Retained as a diagnostic, not as the operating point. It answers "how far can
    this host be pushed before p99 crosses the deadline", which is a property of
    the host as much as of the code, and comparing its answer against
    REPR_LOAD_OPS is what exposed that.
    """
    loads = loads_present(rows)
    g = group_metric(rows, lambda r: r["lat_ns"]["p99"] / NS_PER_US)
    variants = variants_present(rows)
    best = loads[0]
    for load in loads:
        ok = True
        for key in variants:
            vals = g.get((key[0], key[1], load))
            if not vals or statistics.median(vals) > deadline_us:
                ok = False
                break
        if ok:
            best = load
    return best


def pick_representative_load(rows):
    """The pinned operating point, snapped to the nearest swept load present."""
    loads = loads_present(rows)
    if REPR_LOAD_OPS in loads:
        return REPR_LOAD_OPS
    # A campaign that never swept the pinned point cannot report at it. Fall back
    # to the closest level it did sweep and say so, rather than silently
    # reporting a different operating point under the same macro name.
    nearest = min(loads, key=lambda l: abs(l - REPR_LOAD_OPS))
    print(f"note: campaign did not sweep {REPR_LOAD_OPS} ops/s; "
          f"reporting at the nearest swept load, {nearest} ops/s")
    return nearest


def pick_overload_load(rows, tracking_ratio=0.9):
    """Highest swept load at which every variant is past saturation, or None.

    Below saturation achieved throughput is pinned to the offered rate by
    construction, so it cannot express a language effect however the languages
    behave. Above saturation that reverses: the offered rate is no longer being
    met, and what each variant still sustains is precisely the observable. The
    two regimes therefore need separate operating points, and this picks the
    second one.

    The deepest swept load is chosen rather than the first point past the knee
    because the transition point is the noisiest place on the curve, while behaviour
    well beyond it is stable. Returning None when no swept load saturates is the
    important case: it says the sweep never reached the regime the question is
    about, which is a fact about the campaign that should stop the analysis rather
    than be papered over by reporting the top of the ladder regardless.
    """
    saturated = [
        load
        for load in loads_present(rows)
        if all(
            (vals := group_metric(rows, lambda r: r["throughput_ops_s"])
                     .get((key[0], key[1], load)))
            and statistics.median(vals) < tracking_ratio * load
            for key in variants_present(rows)
        )
    ]
    return max(saturated) if saturated else None


def has_metric(rows, path):
    """True when every row carries the nested key path, e.g. ("lat_ns", "p9999").

    Campaigns recorded before p99.99 and inter-operation jitter were emitted are
    still valid input, and a figure or table must not present a partially measured
    quantity as if the whole campaign had it.
    """
    for r in rows:
        cur = r
        for key in path:
            if not isinstance(cur, dict) or key not in cur:
                return False
            cur = cur[key]
    return True


def fig_tail_percentiles(rows, outdir, load):
    """Percentile fan for the four variants, with the resolution argument beside it.

    Panel (a) carries a bootstrap band on every curve rather than a bare line. Left
    as lines the four variants lie on top of one another and the figure reads as a
    claim of equivalence, which is the one reading the performance results refuse: a
    measurement that cannot separate two things has not shown them to be the same.

    Panel (b) says how far the comparison can be trusted. At each percentile it
    draws the spread between the four variants against the widest confidence
    interval any single variant carries there. Below one, the spread is the larger
    quantity and an ordering means something. Above one, the uncertainty about a
    single variant exceeds the gap between all of them, and whatever order the
    curves fall in is the scheduler's and not the language's. Which side of one
    the ratio lands on is a property of the host, so the panel's title is chosen
    from the data: on the virtualised guest the crossover happened above the
    median, and on a quiet host it does not happen at all.
    """
    # Stops at p99.9 on purpose. Both panels are built from per-run percentiles
    # aggregated across repeats, and the per-run p99.99 is the statistic Section
    # 4.5 calls dominated by sampling noise: tab:latency reports that percentile
    # pooled instead, precisely so the thesis never quotes the per-run version.
    # Drawing it here would put the disowned statistic on a figure, and panel (b)
    # would compare a spread against an interval that the reported far tail does
    # not have.
    pcts = ["p50", "p90", "p99", "p999"]
    pct_labels = ["p50", "p90", "p99", "p99.9"]
    variants = variants_present(rows)

    stats = {}
    for key in variants:
        sub = _subset(rows, key, load)
        for p in pcts:
            stats[(key, p)] = bootstrap_ci([r["lat_ns"][p] / NS_PER_US for r in sub])

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(9.6, 3.7),
                                     gridspec_kw={"width_ratios": [1.15, 1.0]})

    # ---- (a) the fan, with a bootstrap band per variant -------------------- #
    xs = range(len(pcts))
    for key in variants:
        label, color, ls, mk = VARIANT_STYLE[key]
        med = [stats[(key, p)][0] for p in pcts]
        lo = [stats[(key, p)][1] for p in pcts]
        hi = [stats[(key, p)][2] for p in pcts]
        ax_a.plot(xs, med, ls, color=color, marker=mk, ms=4.5, lw=1.5, label=label)
        ax_a.fill_between(xs, lo, hi, color=color, alpha=0.16, lw=0)
    ax_a.set_xticks(list(xs))
    ax_a.set_xticklabels(pct_labels)
    ax_a.set_xlabel("Latency percentile")
    ax_a.set_ylabel("Latency (\u00b5s)")
    ax_a.set_yscale("log")
    ax_a.set_title("(a) The four variants, with bootstrap bands", fontsize=9.5)
    ax_a.grid(True, which="both", ls=":", alpha=0.4)
    ax_a.set_axisbelow(True)
    ax_a.legend(fontsize=8, framealpha=0.95, loc="lower right")

    # ---- (b) between-variant spread against within-variant uncertainty ---- #
    spread, widest = [], []
    for p in pcts:
        meds = [stats[(key, p)][0] for key in variants]
        spread.append(max(meds) - min(meds))
        widest.append(max(stats[(key, p)][2] - stats[(key, p)][1] for key in variants))
    width = 0.36
    left = [x - width / 2 for x in xs]
    right = [x + width / 2 for x in xs]
    ax_b.bar(left, spread, width=width, color="#4a5c6a",
             label="spread between the four variants")
    ax_b.bar(right, widest, width=width, color="#f2d4d0", hatch="//",
             edgecolor="#a5281b", lw=0.8,
             label="widest CI on a single variant")
    ax_b.set_yscale("log")
    ax_b.set_xticks(list(xs))
    ax_b.set_xticklabels(pct_labels)
    ax_b.set_xlabel("Latency percentile")
    ax_b.set_ylabel("Latency (\u00b5s, log scale)")
    # The title states what this host did, not what a host is expected to do. On
    # the virtualised guest the widest interval overtook the between-variant
    # spread above the median, and the panel was headed "Where the host stops
    # resolving the comparison". On a quiet host the crossover never happens, and
    # a fixed title would have the figure announce a limit its own bars refute.
    crossed = any(w > s for s, w in zip(spread, widest))
    ax_b.set_title(
        "(b) Where the host stops resolving the comparison" if crossed
        else "(b) The comparison stays resolvable at every percentile",
        fontsize=9.5)
    ax_b.grid(True, axis="y", which="both", ls=":", alpha=0.4)
    ax_b.set_axisbelow(True)
    ax_b.legend(fontsize=8, framealpha=0.95, loc="upper left")
    # The ratio between the two bars, annotated at every percentile rather than
    # only where it exceeds one. Printed throughout, it says how much resolving
    # power is left: below one the spread is the larger quantity and an ordering
    # means something, above one reporting an ordering would be reporting the
    # interference.
    top = max(max(spread), max(widest))
    for x, s, w in zip(xs, spread, widest):
        if s <= 0:
            continue
        ratio = w / s
        ax_b.annotate(f"{ratio:.1f}\u00d7" if ratio < 2 else f"{ratio:.0f}\u00d7",
                      xy=(x, max(s, w)), xytext=(0, 4),
                      textcoords="offset points", ha="center", fontsize=8.5,
                      color="#a5281b" if ratio > 1 else "#4a5c6a")
    ax_b.set_ylim(top=top * 6)

    fig.tight_layout()
    out = os.path.join(outdir, "fig_tail_percentiles.pdf")
    fig.savefig(out)
    plt.close(fig)
    return out


# --------------------------------------------------------------------------- #
# Figure 4: resource use (peak RSS and CPU utilisation) per variant.
# --------------------------------------------------------------------------- #
def _paired_effect(rows, key_a, key_b, load, metric_fn):
    """Median and bootstrap interval of the paired (b - a) difference at one load.

    Pairing is by position, which is pairing by repeat: the campaign's outer loop
    is the repeat and every variant is measured inside it, so the i-th run of two
    variants shares its ambient conditions whether the two differ in language or
    in allocator. That makes the allocator contrast a matched comparison on the
    same footing as the language contrast, which is what lets the two be drawn
    against each other.
    """
    a = [metric_fn(r) for r in _subset(rows, key_a, load)]
    b = [metric_fn(r) for r in _subset(rows, key_b, load)]
    if not a or not b:
        return None
    return bootstrap_ci([y - x for x, y in zip(a, b)])


def rss_low_run_offset(rows, load):
    """How far below its own mode a contaminated peak-RSS run sits, in MiB.

    Section 6.4.3 reads one peak-RSS row from its interval rather than its
    p-value, and the justification is that a few runs report a resident set well
    below their variant's mode while being otherwise indistinguishable. That
    offset was typed into the prose until now, which meant a rerun could not
    move it. It is measured here instead.

    The split is by the largest gap between consecutive sorted values rather
    than by a threshold, because a threshold would be a number chosen after
    seeing the data. A variant whose runs are unimodal contributes nothing: the
    minority group has to be a minority, and the gap has to be the dominant
    feature of the spread, or the variant is skipped. Returns None when no
    variant qualifies, so the macro is absent rather than zero on a campaign
    that does not show the defect.
    """
    offsets = []
    for key in variants_present(rows):
        vals = sorted(r["rss_peak_kb"] / 1024.0 for r in _subset(rows, key, load))
        if len(vals) < 6:
            continue
        gaps = [(vals[i + 1] - vals[i], i) for i in range(len(vals) - 1)]
        gap, at = max(gaps)
        lo, hi = vals[:at + 1], vals[at + 1:]
        # The low group must be the minority, and the gap must dominate the
        # dispersion inside either group, or this is spread and not bimodality.
        inner = max(hi[-1] - hi[0], lo[-1] - lo[0])
        if len(lo) >= len(hi) or gap <= inner:
            continue
        offsets.append(statistics.median(hi) - statistics.median(lo))
    return statistics.median(offsets) if offsets else None


def fig_resources(rows, outdir, load):
    """Resource use at the representative load, and the two effects inside it.

    Panels (a) and (c) group by allocator so that both contrasts the design
    controls for are visible in one place: the two bars inside a group differ only
    in language, the two groups differ only in allocator. Confidence intervals are
    drawn because peak RSS is the one metric here whose intervals separate the
    variants, and a bar chart without them cannot show that.

    Panel (b) draws the allocator gap and the language gap on one axis, so the
    two sizes can be compared. The wide strip is what the slide slot holds. The
    column figure is the one the thesis includes: the same strip, scaled into
    the text width, left the labels near 4 pt.
    """
    variants = variants_present(rows)
    allocs = [a for a in ("system", "jemalloc") if any(k[1] == a for k in variants)]
    langs = [l for l in ("cpp", "rust") if any(k[0] == l for k in variants)]
    names = {"cpp": "C++", "rust": "Rust"}
    alloc_names = {"system": "system allocator", "jemalloc": "jemalloc"}
    rss_of = lambda r: r["rss_peak_kb"] / 1024.0
    cpu_of = lambda r: r["cpu_pct"]

    def paint(ax_a, ax_b, ax_c, tick, title_pt, legend_pt, value_pt,
              wrap_ticks=False, bar_h=0.5, xlim_pad=1.22, slide=False,
              rss_headroom=0.0, rss_legend="best",
              cpu_letter="(c)", effect_letter="(b)"):
        def grouped(ax, metric_fn, ylabel, title, headroom=0.0, legend_loc="best"):
            width = 0.34
            for i, lang in enumerate(langs):
                xs, med, err_lo, err_hi = [], [], [], []
                for j, alloc in enumerate(allocs):
                    key = (lang, alloc)
                    if key not in VARIANT_STYLE:
                        continue
                    m, lo, hi = bootstrap_ci([metric_fn(r) for r in _subset(rows, key, load)])
                    xs.append(j + (i - (len(langs) - 1) / 2) * width)
                    med.append(m)
                    err_lo.append(max(0.0, m - lo))
                    err_hi.append(max(0.0, hi - m))
                color = VARIANT_STYLE[(lang, allocs[0])][1]
                ax.bar(xs, med, width=width, color=color, label=names[lang],
                       yerr=[err_lo, err_hi], capsize=3,
                       error_kw={"lw": 1.0, "ecolor": "#333333"})
            ax.set_xticks(range(len(allocs)))
            tick_labels = [alloc_names[a].replace(" ", "\n") if wrap_ticks
                           else alloc_names[a] for a in allocs]
            ax.set_xticklabels(tick_labels, fontsize=tick)
            ax.set_ylabel(ylabel, fontsize=None if slide else tick)
            ax.set_title(title, fontsize=title_pt)
            if not slide:
                ax.tick_params(axis="y", labelsize=tick)
            ax.grid(True, axis="y", ls=":", alpha=0.4)
            ax.set_axisbelow(True)
            if headroom:
                lo_y, hi_y = ax.get_ylim()
                ax.set_ylim(lo_y, hi_y + (hi_y - lo_y) * headroom)
            ax.legend(fontsize=legend_pt, framealpha=0.95, loc=legend_loc)

        grouped(ax_a, rss_of, "Peak RSS (MiB)", "(a) Peak resident set size",
                headroom=rss_headroom, legend_loc=rss_legend)
        # Every variant saturates a core here, so all four bars run to the top of the
        # axis and "best" has nowhere free to sit: it lands on the system-allocator
        # pair. The headroom gives the legend a lane of its own.
        grouped(ax_c, cpu_of, "CPU utilisation (%)", f"{cpu_letter} CPU utilisation",
                headroom=0.34, legend_loc="upper left")

        # ---- (b) the allocator effect against the language effect --------- #
        effects = []
        if len(allocs) > 1:
            for lang in langs:
                eff = _paired_effect(rows, (lang, "system"), (lang, "jemalloc"), load, rss_of)
                if eff:
                    effects.append((f"jemalloc \u2212 system,\nin {names[lang]}", eff, "#7f8c8d"))
        for alloc in allocs:
            eff = _paired_effect(rows, ("cpp", alloc), ("rust", alloc), load, rss_of)
            if eff:
                effects.append((f"Rust \u2212 C++,\nunder {alloc_names[alloc]}", eff, "#c0392b"))

        ys = list(range(len(effects)))[::-1]
        hi_cap = max(e[1][2] for e in effects) if effects else 1.0
        for y, (label, (med, lo, hi), color) in zip(ys, effects):
            ax_b.barh([y], [med], height=bar_h, color=color,
                      xerr=[[max(0.0, med - lo)], [max(0.0, hi - med)]], capsize=3,
                      error_kw={"lw": 1.0, "ecolor": "#333333"})
            ax_b.text(hi + hi_cap * 0.03, y, f"{med:.1f}",
                      va="center", fontsize=value_pt)
        ax_b.set_yticks(ys)
        ax_b.set_yticklabels([e[0] for e in effects], fontsize=8 if slide else tick)
        ax_b.set_xlabel("Paired difference in peak RSS (MiB)",
                        fontsize=None if slide else tick)
        effect_title = f"{effect_letter} Allocator effect against language effect"
        if not slide:
            effect_title = f"{effect_letter} Allocator effect\nagainst language effect"
        ax_b.set_title(effect_title, fontsize=title_pt)
        if not slide:
            ax_b.tick_params(axis="x", labelsize=tick)
        ax_b.axvline(0.0, color="#333333", lw=0.9)
        ax_b.grid(True, axis="x", ls=":", alpha=0.4)
        ax_b.set_axisbelow(True)
        if effects:
            ax_b.set_xlim(0, hi_cap * xlim_pad)

    # Wide strip for the slide slot. The thesis column cannot hold this at a
    # size where the labels stay readable, so the page gets the stacked file.
    fig, (ax_a, ax_b, ax_c) = plt.subplots(
        1, 3, figsize=(10.2, 3.5), gridspec_kw={"width_ratios": [1.0, 1.22, 1.0]})
    paint(ax_a, ax_b, ax_c, tick=8.5, title_pt=9.5, legend_pt=8, value_pt=8.5,
          slide=True)
    fig.tight_layout()
    out = os.path.join(outdir, "fig_resources.pdf")
    fig.savefig(out)
    plt.close(fig)

    # (a) is the left column, full height, so it shares a left edge with the
    # figure. (b) sits above (c) on the right. A top-left box left (a) inset
    # over the wide panel and the letters did not match the reading order.
    fig = plt.figure(figsize=(6.3, 5.4), layout="constrained")
    gs = fig.add_gridspec(2, 2, width_ratios=[0.92, 1.35], height_ratios=[1.0, 1.25])
    paint(fig.add_subplot(gs[:, 0]), fig.add_subplot(gs[1, 1]),
          fig.add_subplot(gs[0, 1]),
          tick=10, title_pt=11, legend_pt=9, value_pt=10,
          wrap_ticks=True, bar_h=0.5, xlim_pad=1.42,
          rss_headroom=0.18, rss_legend="upper left",
          cpu_letter="(b)", effect_letter="(c)")
    column = os.path.join(outdir, "fig_resources_column.pdf")
    fig.savefig(column, bbox_inches="tight")
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
    # reads as a map of where the guarantee stops rather than as a scoreboard. The
    # split is on the expectation recorded before the run, which is what
    # write_taxonomy_table uses: a figure that grouped on the result and a table
    # that grouped on the expectation would put a case that changed sides in
    # different halves, and the caption claims the two cannot disagree.
    prevented = [r for r in rows if r["rust_expected"].strip() == "prevented"]
    boundary = [r for r in rows if r["rust_expected"].strip() != "prevented"]
    rows = prevented + boundary
    defects = [r["defect"].replace("_", " ") for r in rows]
    # UBSan is a third axis, not a refinement of the other two: signed overflow
    # is invisible to ASan and TSan alike, so without its own column the
    # integer-overflow row would read as undetected in C++ when it is not.
    cols = ["C++ ASan", "C++ TSan", "C++ UBSan", "Safe Rust"]

    # code: 3 = prevented at compile time (best), 2 = detected at runtime,
    #       1 = detected at runtime but only intermittently, 0 = missed.
    def cell(value):
        v = value.strip()
        if v == "detected":
            return 2, "runtime"
        if v == "flaky":
            return 1, "sometimes"
        return 0, "missed"

    grid, labels = [], []
    for r in rows:
        asan = cell(r["cpp_asan"])
        tsan = cell(r["cpp_tsan"])
        ubsan = cell(r.get("cpp_ubsan", ""))
        rust_prevented = "compile-time" in r["rust_compile"]
        grid.append([asan[0], tsan[0], ubsan[0], 3 if rust_prevented else 0])
        labels.append([asan[1], tsan[1], ubsan[1],
                       "compile" if rust_prevented else "none"])

    cmap = matplotlib.colors.ListedColormap(
        ["#c0392b", "#e67e22", "#e6b800", "#1e8449"])
    norm = matplotlib.colors.BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], cmap.N)

    # The matrix used to be drawn nearly square and 7.4 in wide, which no place
    # that reproduces it can carry: both the thesis column and the slide slot are
    # landscape, so the figure was scaled to about 55% and its type landed near
    # 4 pt. Rows are tighter and the proportions match the slot, so the same
    # labels are reproduced at close to full size and the type can stay large.
    fig, ax = plt.subplots(figsize=(5.6, 0.27 * len(defects) + 1.3))
    ax.imshow(grid, cmap=cmap, norm=norm, aspect="auto")
    ax.set_xticks(range(len(cols)))
    # Two lines per column: at one line the four headings are wider than the
    # columns they label and run into each other.
    ax.set_xticklabels([c.replace(" ", "\n") for c in cols], fontsize=10)
    ax.set_yticks(range(len(defects)))
    ax.set_yticklabels(defects, fontsize=10)
    for i in range(len(defects)):
        for j in range(len(cols)):
            ax.text(
                j, i, labels[i][j], ha="center", va="center",
                color="white", fontsize=8.5, fontweight="bold",
            )
    ax.set_xticks([x - 0.5 for x in range(1, len(cols))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(defects))], minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", length=0)

    # Mark where the compile-time guarantee stops. The rule is named in the legend
    # rather than labelled in place: a caption box on the rule has to sit inside a
    # row, and at this row height it covers the outcome it is drawn next to.
    if prevented and boundary:
        ax.axhline(len(prevented) - 0.5, color="black", linewidth=2.0)

    legend = [
        Patch(facecolor="#1e8449", label="prevented at compile time"),
        Patch(facecolor="#e6b800", label="detected at runtime only"),
        Patch(facecolor="#e67e22", label="detected on some runs only"),
        Patch(facecolor="#c0392b", label="not detected / not prevented"),
    ]
    if prevented and boundary:
        legend.append(plt.Line2D([], [], color="black", linewidth=2.0,
                                 label="boundary of the guarantee"))
    ax.legend(handles=legend, loc="upper center", bbox_to_anchor=(0.5, -0.14),
              ncol=2, fontsize=8.5, framealpha=0.9)
    fig.tight_layout()
    out = os.path.join(outdir, "fig_taxonomy.pdf")
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def write_taxonomy_table(taxonomy_csv, outdir):
    """Emit the body of tab:taxonomy from the fault runner's own log.

    This table was typed by hand beside the artefact for longer than any other
    results table in the thesis, which meant the runner could record one outcome
    and the page print another with nothing to catch it. Everything below is
    derived: the class labels and the misbehaviour each boundary case exhibits
    are declared in faults/run_faults.sh, where the expectation the runner
    enforces is declared, and the outcomes come from the run.

    The two groups are split on the expectation recorded *before* the run
    (rust_expected) rather than on what the compiler did. Splitting on the
    result would make the table's own structure a restatement of it, so a case
    that changed sides would silently move rather than show up as the
    discrepancy the design exists to surface.
    """
    if not os.path.exists(taxonomy_csv):
        return None
    with open(taxonomy_csv, newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        return None

    # A sanitiser that never reported and a sanitiser whose program deadlocked
    # under it both leave the defect undetected, and the table says so in one
    # phrase. Which of the two happened is not lost: a row that hung anywhere
    # carries the dagger whose footnote explains that nothing was corrupted and
    # nothing was undefined, the binary simply had to be killed.
    cell = {"detected": "detected", "clean": "not detected", "hung": "not detected",
            "flaky": "intermittent$^{\\S}$"}

    def sanitiser(value):
        v = value.strip()
        if v not in cell:
            raise SystemExit(
                f"plot_figures.py: taxonomy.csv reports sanitiser outcome {v!r}, "
                "which has no cell in tab:taxonomy. Add it here rather than "
                "letting the table print a blank")
        return cell[v]

    def rust(r):
        outcome = r["rust_compile"]
        prevented = re.match(r"compile-time prevented \((.*)\)", outcome)
        if prevented:
            codes = prevented.group(1).split(",")
            # Several diagnostics fire on some cases. The table shows the first
            # and the footnote names the rest, because five error codes in a
            # cell read as severity rather than as one rejection.
            marker = "$^{\\dagger}$" if len(codes) > 1 else ""
            return f"compile error ({codes[0]}{marker})"
        observed = r.get("rust_observed", "").strip()
        if not observed:
            raise SystemExit(
                f"plot_figures.py: boundary case {r['defect']!r} records no "
                "misbehaviour in taxonomy.csv. Give it one in the eighth field "
                "of the defect list in faults/run_faults.sh")
        return f"compiles, {observed}"

    groups = [("prevented", "Within the guarantee"),
              ("not-prevented", "Boundary of the guarantee")]
    lines = []
    for expected, heading in groups:
        sel = [r for r in rows if r["rust_expected"].strip() == expected]
        if not sel:
            continue
        if lines:
            lines.append("\\hline")
        # A \multicolumn has to be the first token of its cell and cannot be
        # when the row arrives through \input, so the heading is set in an
        # \rlap, which contributes no width. Same reason as tab:significance.
        lines.append(f"\\rlap{{\\emph{{{heading}}}}} & & & &")
        for r in sel:
            label = r.get("label", "").strip() or r["defect"].replace("_", " ")
            if "hung" in (r["cpp_asan"], r["cpp_tsan"], r["cpp_ubsan"]):
                label += "$^{\\ddagger}$"
            lines.append(f"{label} & {sanitiser(r['cpp_asan'])} & "
                         f"{sanitiser(r['cpp_tsan'])} & {sanitiser(r['cpp_ubsan'])} & "
                         f"{rust(r)}")

    out = os.path.join(outdir, "tab_taxonomy.tex")
    with open(out, "w") as f:
        body = ""
        for i, line in enumerate(lines):
            if line == "\\hline":
                body += "\\\\\n\\hline\n"
                continue
            if i and lines[i - 1] != "\\hline":
                body += " \\\\\n"
            body += line
        f.write(body + "\n")
    return out


# --------------------------------------------------------------------------- #
# LaTeX tables.
# --------------------------------------------------------------------------- #
def load_op_cost(path):
    """Read the interleaved native-vs-seam repeats emitted by ffi/build.sh.

    Returns (native_ns, seam_ns) in run order, so position is repeat index. The
    runner alternates the two callers inside every repeat, which is what makes the
    pair matched: a host whose handoff cost drifts over minutes moves both members
    of a pair together and cancels in their difference.
    """
    if not os.path.exists(path):
        return ([], [])
    native, seam = [], []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("lang") == "cpp-via-seam" and "op_ns" in rec:
                seam.append(rec["op_ns"])
            elif rec.get("lang") == "rust" and "service_ns" in rec:
                native.append(rec["service_ns"])
    n = min(len(native), len(seam))
    return (native[:n], seam[:n])


def fig_ffi(metrics_json, outdir, op_cost_path=None):
    """The seam's cost on a real operation, measured rather than argued.

    The earlier version of this figure put the empty crossing beside a full
    round-trip and reported the ratio. That comparison bounds the crossing and
    nothing else, because an \\texttt{extern "C"} call with no work behind it and a
    cross-thread round-trip are not the same experiment, and the migration results
    decline to reason from one to the other. What answers RQ4 is the same operation
    invoked natively and then through the seam, interleaved.

    Panel (a) draws each repeat as its own line, which is the argument for
    interleaving: the run-to-run spread of the handoff is wide enough that single
    passes of each would have supported almost any conclusion, and one pass taken
    while preparing the section made the seam look faster by a third. Panel (b)
    reduces the pairs to their difference. It reports no detected cost together
    with the bound on what the measurement could have missed, because a
    non-significant paired test on its own establishes nothing.
    """
    if not os.path.exists(metrics_json):
        return None
    m = json.load(open(metrics_json))
    if op_cost_path is None:
        op_cost_path = os.path.join(os.path.dirname(metrics_json), "op_cost.jsonl")
    native, seam = load_op_cost(op_cost_path)
    if len(native) < 2:
        print(f"note: no interleaved native-vs-seam repeats at {op_cost_path}; "
              f"fig_ffi_cost.pdf not written (the RQ4 figure is the paired "
              f"comparison, not the empty crossing)")
        return None

    native_us = [v / NS_PER_US for v in native]
    seam_us = [v / NS_PER_US for v in seam]
    diffs = [s - n for n, s in zip(native, seam)]
    med, lo, hi = bootstrap_ci(diffs)

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(9.6, 3.6),
                                     gridspec_kw={"width_ratios": [1.0, 1.15]})

    # ---- (a) one line per interleaved repeat ------------------------------ #
    for n_us, s_us in zip(native_us, seam_us):
        colour = "#c0392b" if s_us > n_us else "#2c7fb8"
        ax_a.plot([0, 1], [n_us, s_us], "-", color=colour, lw=1.0, alpha=0.55,
                  marker="o", ms=3.0)
    ax_a.plot([0, 1], [statistics.median(native_us), statistics.median(seam_us)],
              "-", color="#111111", lw=2.2, marker="D", ms=6, zorder=5,
              label="median of the repeats")
    n_up = sum(1 for n_us, s_us in zip(native_us, seam_us) if s_us > n_us)
    for colour, count, sense in (("#c0392b", n_up, "dearer"),
                                 ("#2c7fb8", len(native) - n_up, "cheaper")):
        ax_a.plot([], [], "-", color=colour, lw=1.2,
                  label=f"seam {sense} on {count} repeats")
    ax_a.set_xlim(-0.35, 1.35)
    ax_a.set_xticks([0, 1])
    ax_a.set_xticklabels(["called natively\nfrom Rust",
                          "called from C++\nthrough the seam"], fontsize=8.5)
    ax_a.set_ylabel("One signalling operation (\u00b5s)")
    ax_a.set_title(f"(a) {len(native)} interleaved repeats", fontsize=9.5)
    ax_a.grid(True, axis="y", ls=":", alpha=0.4)
    ax_a.set_axisbelow(True)
    lo_y, hi_y = ax_a.get_ylim()
    ax_a.set_ylim(lo_y, hi_y + (hi_y - lo_y) * 0.24)
    ax_a.legend(fontsize=8, framealpha=0.95, loc="upper right")

    # ---- (b) the paired difference against zero --------------------------- #
    span = max(abs(lo), abs(hi)) * 1.6
    ax_b.axvspan(lo, hi, color="#f2d4d0", alpha=0.55, lw=0,
                 label="95% CI: what the measurement could have missed")
    ax_b.axvline(0.0, color="#333333", lw=1.1, ls="--")
    ax_b.errorbar([med], [0], xerr=[[med - lo], [hi - med]], fmt="D",
                  color="#1e8449", ms=7, lw=1.6, capsize=4,
                  label="paired difference (seam \u2212 native)")
    crossing = m.get("ffi_crossing_ns", 0.0)
    if crossing > 0:
        # The empty crossing plotted on the axis the operation is measured on:
        # it lands indistinguishably from zero, which is the honest way to show
        # that it was never the quantity in question.
        ax_b.plot([crossing], [0], marker="|", ms=14, color="#111111", mew=1.4)
        ax_b.annotate(f"the empty crossing, {crossing:.2f} ns",
                      xy=(crossing, -0.06), xytext=(-span * 0.52, -0.55),
                      textcoords="data", ha="center", fontsize=8,
                      color="#111111",
                      arrowprops=dict(arrowstyle="->", color="#111111", lw=0.9,
                                      shrinkB=2))
    native_med = statistics.median(native)
    ax_b.set_xlim(-span, span)
    ax_b.set_ylim(-1.15, 0.95)
    ax_b.set_yticks([])
    ax_b.set_xlabel("Seam cost per operation (ns)")
    ax_b.set_title("(b) No cost detected, and the bound on it", fontsize=9.5)
    ax_b.grid(True, axis="x", ls=":", alpha=0.4)
    ax_b.set_axisbelow(True)
    ax_b.annotate(f"upper bound {100.0 * hi / native_med:.1f}% of the operation\n"
                  f"$p = {m.get('op_paired_p', float('nan')):.3f}$",
                  xy=(0.03, 0.88), xycoords="axes fraction", ha="left",
                  va="top", fontsize=8, color="#a5281b")
    ax_b.legend(fontsize=8, framealpha=0.95, loc="lower right")

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
        ("\\texttt{unsafe} functions in core library", f"{m.get('unsafe_core', 0)}"),
        ("\\texttt{unsafe} functions in FFI seam", f"{m.get('unsafe_seam', 0)}"),
        ("Raw FFI crossing", f"{m.get('ffi_crossing_ns', 0):.2f} ns/call"),
    ]
    # The direct A/B: the same operation, the same service configuration, and the
    # same loop, called natively and then through the seam. An empty crossing
    # measured against a full round-trip bounds the crossing but says nothing
    # about what the seam costs on an operation, because it is not the same
    # experiment.
    native = m.get("op_roundtrip_native_ns", 0)
    through = m.get("op_roundtrip_ns", 0)
    if native > 0 and through > 0 and "op_seam_delta_ns" in m:
        rows += [
            ("Signaling op, native caller", f"{native / 1000.0:.1f} \\textmu s/call"),
            ("Signaling op, through the seam", f"{through / 1000.0:.1f} \\textmu s/call"),
            # Math mode so the signs typeset as minus rather than hyphen, which
            # the surrounding rows get for free from \mci.
            ("Seam cost per operation (paired)",
             f"${m['op_seam_delta_ns']:+.0f}$ ns "
             f"$[{m['op_seam_delta_lo_ns']:+.0f}, {m['op_seam_delta_hi_ns']:+.0f}]$"),
            ("\\quad as a fraction of the operation",
             f"${100.0 * m['op_seam_delta_hi_ns'] / native:+.2f}\\%$ at the upper bound"),
        ]
    else:
        rows.append(
            ("End-to-end signaling op", f"{through / 1000.0:.1f} \\textmu s/call"))
    out = os.path.join(outdir, "tab_ffi.tex")
    with open(out, "w") as f:
        f.write(" \\\\\n".join(f"{k} & {v}" for k, v in rows) + "\n")
    return out


def fmt_us_adaptive(ns):
    """Microseconds at a precision that suits the magnitude."""
    us = ns / NS_PER_US
    if abs(us) < 1:
        return f"{us:.3f}"
    if abs(us) < 100:
        return f"{us:.2f}"
    return f"{us:.1f}"


def load_budget(path):
    """Read the latency-budget repeats emitted by bench/latency_budget.sh.

    Returns {lang: [record, ...]} in run order. Order matters: the runner
    interleaves the two languages inside each repeat, so the i-th C++ record and
    the i-th Rust record were measured in the same block and can be paired.
    """
    if not os.path.exists(path):
        return {}
    out = defaultdict(list)
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                rec = json.loads(line)
                out[rec["lang"]].append(rec)
    return dict(out)


#: Components of the end-to-end cost, in table order: (label, JSON key, unit).
#:
#: The two terms differ by more than three orders of magnitude, which is the point
#: of the table, so each is quoted in the unit that suits it. Forcing both into
#: microseconds would print the operation as 0.019 with a confidence interval that
#: rounds to a single repeated value, hiding the precision the measurement has.
BUDGET_COMPONENTS = [
    ("Operation alone, no queue in the path (ns)", "core_ns", 1.0),
    ("Cross-thread submit-and-complete handoff (\\textmu s)", "handoff_ns", NS_PER_US),
    ("End-to-end round-trip, uncontended (\\textmu s)", "service_ns", NS_PER_US),
]


def budget_median(budget, lang, key):
    return statistics.median(r[key] for r in budget[lang])


def write_budget_table(budget, outdir):
    """Emit the body of tab:budget: where the end-to-end latency actually goes.

    The sweep measures one number per operation and cannot say how much of it is
    the work the language performs and how much is the cross-thread handoff that
    delivers it. Both are measured here in both languages, so a bound on the
    paired median difference can be read against the part of the cost a language
    could plausibly change rather than against the total.

    Reported the same way as the sweep: median over interleaved repeats above its
    bootstrap interval, with the language comparison tested on the paired repeats
    rather than read off the two medians.
    """
    if not budget or "cpp" not in budget or "rust" not in budget:
        return None
    if not budget["cpp"] or not budget["rust"]:
        return None

    def cell(lang, key, scale):
        med, lo, hi = bootstrap_ci([r[key] / scale for r in budget[lang]])
        d = 2 if scale > 1 else 1
        return f"\\mci{{{med:.{d}f}}}{{{lo:.{d}f}}}{{{hi:.{d}f}}}"

    lines = []
    for label, key, scale in BUDGET_COMPONENTS:
        cpp_vals = [r[key] for r in budget["cpp"]]
        rust_vals = [r[key] for r in budget["rust"]]
        _, p, _ = paired_permutation_test(cpp_vals, rust_vals)
        lines.append(
            f"{label} & {cell('cpp', key, scale)} & {cell('rust', key, scale)} & {fmt_p(p)}")
    shares = {
        lang: statistics.median(r["core_share_pct"] for r in budget[lang])
        for lang in ("cpp", "rust")
    }
    lines.append(
        f"Operation's share of the round-trip & {shares['cpp']:.3f}\\,\\% & "
        f"{shares['rust']:.3f}\\,\\% & ")

    out = os.path.join(outdir, "tab_budget.tex")
    with open(out, "w") as f:
        f.write(" \\\\\n".join(lines) + "\n")
    return out


def load_contention(path):
    """Read contended-queue repeats from bench/queue_contention.sh."""
    return load_budget(path)


def write_contention_table(contention, outdir):
    """Emit tab_contention.tex: throughput under multi-producer queue load."""
    if not contention or "cpp" not in contention or "rust" not in contention:
        return None
    if not contention["cpp"] or not contention["rust"]:
        return None

    def cell(lang, key, scale=1.0, digits=1):
        med, lo, hi = bootstrap_ci([r[key] / scale for r in contention[lang]])
        return f"\\mci{{{med:.{digits}f}}}{{{lo:.{digits}f}}}{{{hi:.{digits}f}}}"

    cpp_thr = [r["throughput_kops"] for r in contention["cpp"]]
    rust_thr = [r["throughput_kops"] for r in contention["rust"]]
    effect, p, _ = paired_permutation_test(cpp_thr, rust_thr)

    lines = [
        f"C++ & {cell('cpp', 'throughput_kops')} & {cell('cpp', 'ns_per_op', 1.0, 0)} & "
        f"\\multicolumn{{1}}{{c}}{{---}}",
        f"Rust & {cell('rust', 'throughput_kops')} & {cell('rust', 'ns_per_op', 1.0, 0)} & "
        f"{fmt_p(p)}",
    ]
    out = os.path.join(outdir, "tab_contention.tex")
    with open(out, "w") as f:
        f.write(" \\\\\n".join(lines) + "\n")
    return out


def fig_budget(budget, sig_results, outdir, for_thesis=False):
    """Two-panel decomposition of the end-to-end latency the sweep reports.

    The table states this in numbers, but the numbers span four orders of
    magnitude and that is exactly the thing a reader skims past. Panel (a) draws
    the round-trip at true proportion, so the operation is a sliver the caption
    has to point at. Panel (b) puts the operation on a log axis next to the
    smallest paired difference the sweep could have resolved, which is the
    comparison that decides whether an end-to-end null result bounds a language
    effect at all. It does not: the instrument is coarser than the quantity by
    three orders of magnitude.
    """
    if not budget or not budget.get("cpp") or not budget.get("rust"):
        return None
    med = lambda lang, key: budget_median(budget, lang, key)
    core = {l: med(l, "core_ns") for l in ("cpp", "rust")}
    handoff = {l: med(l, "handoff_ns") for l in ("cpp", "rust")}
    if min(core.values()) <= 0:
        return None

    # The slide keeps the wide, small-type figure. The thesis column is
    # drawn larger so the labels survive \\linewidth instead of coming out
    # near 5 pt.
    if for_thesis:
        fig_w, fig_h = 7.5, 4.55
        title_pt, tick_pt, note_pt, legend_pt, value_pt = 13, 11, 10.5, 9.5, 11
        out_name = "fig_budget_thesis.pdf"
    else:
        fig_w, fig_h = 9.6, 3.5
        title_pt, tick_pt, note_pt, legend_pt, value_pt = 9.5, 8.5, 8, 7.5, 8.5
        out_name = "fig_budget.pdf"
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(fig_w, fig_h),
                                     gridspec_kw={"width_ratios": [1.0, 1.25]})

    # ---- (a) the round-trip at true proportion ---------------------------- #
    langs = ["cpp", "rust"]
    names = {"cpp": "C++", "rust": "Rust"}
    ypos = [1, 0]
    core_us = [core[l] / NS_PER_US for l in langs]
    hand_us = [handoff[l] / NS_PER_US for l in langs]
    ax_a.barh(ypos, core_us, height=0.45, color="#c0392b",
              label="operation (the language)")
    ax_a.barh(ypos, hand_us, height=0.45, left=core_us, color="#b6c2cf",
              label="cross-thread handoff (the OS)")
    ax_a.set_yticks(ypos)
    ax_a.set_yticklabels([names[l] for l in langs],
                         fontsize=tick_pt if for_thesis else None)
    ax_a.set_xlabel("End-to-end round-trip (\u00b5s)",
                    fontsize=tick_pt if for_thesis else None)
    ax_a.set_title("(a) Drawn at true proportion", fontsize=title_pt)
    if for_thesis:
        ax_a.tick_params(axis="x", labelsize=tick_pt)
    ax_a.grid(True, axis="x", ls=":", alpha=0.4)
    ax_a.set_axisbelow(True)
    ax_a.set_xlim(0, max(c + h for c, h in zip(core_us, hand_us)) * 1.32)
    for y, c, h in zip(ypos, core_us, hand_us):
        ax_a.text(c + h, y, f"  {c + h:.1f} \u00b5s", va="center", fontsize=value_pt)
    share = max(med(l, "core_share_pct") for l in langs)
    ax_a.annotate(f"the operation:\n{share:.3f}% of the bar",
                  xy=(0, 1.23), xytext=(max(hand_us) * 0.22, 1.60),
                  fontsize=note_pt, color="#c0392b", ha="left",
                  arrowprops=dict(arrowstyle="->", color="#c0392b", lw=1.1))
    ax_a.set_ylim(-0.75, 2.05)
    ax_a.legend(fontsize=legend_pt, loc="lower right", framealpha=0.95)

    # ---- (b) the same quantities on a log axis ---------------------------- #
    # The sweep's resolving power on the paired median difference: the widest
    # bound its confidence interval supports. Anything smaller than this is
    # invisible to the sweep however many repeats are added, because the
    # dispersion is interference rather than sampling noise.
    p50_sig = [r for r in sig_results if r["metric"].startswith("p50")]
    bound_us = (max(max(abs(r["lo"]), abs(r["hi"])) for r in p50_sig)
                if p50_sig else None)

    labels, vals, colors = [], [], []
    for l in langs:
        labels.append(f"{names[l]} operation")
        vals.append(core[l])
        colors.append("#d62728" if l == "rust" else "#1f77b4")
    labels.append("Cross-thread handoff")
    vals.append(max(handoff.values()))
    colors.append("#8794a3")
    if bound_us:
        # Drawn as a bar rather than a marker on purpose: it is a blind zone, not
        # a measurement. Everything it covers is invisible to the sweep, and the
        # two operation bars sit well inside it.
        labels.append("Sweep's blind zone\n(bound on the paired p50)")
        vals.append(bound_us * NS_PER_US)
        colors.append("#f2d4d0")

    yb = list(range(len(vals)))[::-1]
    bars = ax_b.barh(yb, vals, height=0.5, color=colors)
    if bound_us:
        bars[-1].set_hatch("//")
        bars[-1].set_edgecolor("#a5281b")
    ax_b.set_xscale("log")
    ax_b.set_yticks(yb)
    ax_b.set_yticklabels(labels, fontsize=tick_pt)
    ax_b.set_xlabel("Cost (ns, log scale)",
                    fontsize=tick_pt if for_thesis else None)
    b_title = "(b) The instrument against the quantity"
    if for_thesis:
        b_title = "(b) The instrument\nagainst the quantity"
    ax_b.set_title(b_title, fontsize=title_pt)
    if for_thesis:
        ax_b.tick_params(axis="x", labelsize=tick_pt)
    ax_b.grid(True, axis="x", which="both", ls=":", alpha=0.4)
    ax_b.set_axisbelow(True)
    ax_b.set_xlim(min(vals) * 0.4, max(vals) * 7)
    for y, v in zip(yb, vals):
        txt = f"{v:.0f} ns" if v < 1000 else f"{v / NS_PER_US:.0f} \u00b5s"
        ax_b.text(v * 1.25, y, txt, va="center", fontsize=value_pt)
    if bound_us:
        ratio = bound_us * NS_PER_US / max(core.values())
        note = f"{ratio:.0f}\u00d7 the quantity it would have to constrain"
        if for_thesis:
            # Two lines under the axis. Inside the axes the larger type
            # sat on the hatched bar and ran off the right edge.
            note = f"{ratio:.0f}\u00d7 the quantity it would\nhave to constrain"
            ax_b.text(0.5, -0.34, note, transform=ax_b.transAxes,
                      ha="center", va="top", fontsize=note_pt, color="#a5281b",
                      clip_on=False)
            ax_b.set_ylim(-0.65, len(vals) - 0.4)
        else:
            ax_b.annotate(note,
                          xy=(0.5, -0.55), xycoords=("axes fraction", "data"),
                          ha="center", fontsize=note_pt, color="#a5281b")
            ax_b.set_ylim(-1.15, len(vals) - 0.4)

    fig.tight_layout()
    if for_thesis:
        fig.subplots_adjust(bottom=0.24)
    out = os.path.join(outdir, out_name)
    fig.savefig(out, bbox_inches="tight" if for_thesis else None)
    plt.close(fig)
    return out


#: Blocks of the paired-effect figure, in the order tab:significance uses them and
#: with the same meaning. The figure and the table have to agree on the grouping,
#: because the grouping is where the statistical treatment's reading rule applies.
EFFECT_BLOCKS = [
    ("robust", "robust to interference on single operations", "#1f4e79"),
    ("tail", "determined by it: high percentiles", "#9aa5ad"),
]


def fig_effects(sig_results, outdir):
    """The whole Holm family as paired effects, one row per test.

    The significance table carries five columns of numbers per row and asks the
    reader to hold fourteen rows in mind at once. Three things are hard to see that
    way and easy to see here: which effects clear the correction, whether an effect
    keeps its sign when the allocator changes, and how much wider the tail
    intervals are than the robust ones.

    Effects are normalised by the C++ median because the family mixes
    microseconds, mebibytes, percentage points and kops/s, and a shared axis is the
    only way to put them side by side. The tables keep each metric's own units, so
    nothing here replaces them.

    The tail rows are drawn but greyed. They are computed from exactly the
    operations interference falls on, so an interval excluding zero is not read as
    a finding, and the figure has to show that rule being applied rather than
    quietly drop the rows it inconveniences.
    """
    if not sig_results:
        return None
    points = []
    for point, title in (("repr", "Below saturation"), ("overload", "Past saturation")):
        sel = [r for r in sig_results if r.get("point", "repr") == point]
        if sel:
            points.append((point, title, sel))
    if not points:
        return None

    fig, axes = plt.subplots(1, len(points), figsize=(9.6, 3.9),
                             gridspec_kw={"width_ratios": [1.0] * len(points)})
    if len(points) == 1:
        axes = [axes]

    for ax, (point, title, sel), panel in zip(axes, points, "abcdefg"):
        # Rows in table order: block by block, and inside a block in the order the
        # metrics were tested, with the two allocators of a metric adjacent so the
        # cross-allocator check is a glance rather than a search.
        ordered, seen = [], []
        for r in sel:
            if _plain(r["metric"]) not in seen:
                seen.append(_plain(r["metric"]))
        for kind, _heading, _colour in EFFECT_BLOCKS:
            for metric in seen:
                for r in sel:
                    if r["kind"] == kind and _plain(r["metric"]) == metric:
                        ordered.append(r)
        ys = list(range(len(ordered)))[::-1]
        colour_of = {kind: colour for kind, _h, colour in EFFECT_BLOCKS}

        for y, r in zip(ys, ordered):
            base = r.get("base") or 0.0
            if base == 0:
                continue
            scale = 100.0 / abs(base)
            med, lo, hi = r["diff"] * scale, r["lo"] * scale, r["hi"] * scale
            colour = colour_of.get(r["kind"], "#1f4e79")
            clears = r.get("holm", 1.0) < 0.05
            ax.errorbar([med], [y], xerr=[[med - lo], [hi - med]], fmt="o",
                        color=colour, ms=6, lw=1.5, capsize=3,
                        markerfacecolor=colour if clears else "white",
                        markeredgewidth=1.4, zorder=3)
        # A band behind the tail rows, so the block is visible without a second
        # axis or a legend entry that would have to be read first.
        ax.axvline(0.0, color="#333333", lw=1.0, ls="--", zorder=1)
        ax.set_yticks(ys)
        ax.set_yticklabels([f"{_plain(r['metric'])}, {r['alloc']}" for r in ordered],
                           fontsize=8.5)
        # Room below the bottom row for the legend, and room to the right of the
        # widest interval for the block label, so neither is laid over data.
        ax.set_ylim(-1.9 if point == "repr" else -0.7, len(ordered) - 0.3)
        x0, x1 = ax.get_xlim()
        ax.set_xlim(x0, x1 + (x1 - x0) * 0.22)
        tail_ys = [y for y, r in zip(ys, ordered) if r["kind"] == "tail"]
        if tail_ys:
            ax.axhspan(min(tail_ys) - 0.5, max(tail_ys) + 0.5,
                       color="#eceff1", zorder=0)
            ax.annotate("not read\nas findings",
                        xy=(0.985, (min(tail_ys) + max(tail_ys)) / 2.0),
                        xycoords=("axes fraction", "data"),
                        ha="right", va="center", fontsize=8, color="#5b6770")
        load_kops = ordered[0]["load"] / 1000.0 if ordered else 0.0
        ax.set_title(f"({panel}) {title}, {load_kops:.0f} kops/s", fontsize=9.5)
        ax.grid(True, axis="x", ls=":", alpha=0.4)
        ax.set_axisbelow(True)

    handles = [
        plt.Line2D([], [], marker="o", ls="none", color="#1f4e79", ms=6,
                   markerfacecolor="#1f4e79", label="clears the Holm correction"),
        plt.Line2D([], [], marker="o", ls="none", color="#1f4e79", ms=6,
                   markerfacecolor="white", markeredgewidth=1.4,
                   label="does not clear it"),
    ]
    axes[0].legend(handles=handles, fontsize=8, framealpha=0.95, loc="lower left")

    # One shared label rather than one per panel. Both panels measure the same
    # quantity on the same normalised axis, so the label was duplicated anyway,
    # and a per-axes copy is wider than the right-hand axes: centred on that
    # axes it overhung the figure and lost its last word, which no amount of
    # bbox_inches recovered because a tight bbox crops to the artists it can
    # measure and the overhang was not one of them.
    fig.supxlabel("Paired effect, Rust $-$ C++ (% of the C++ median)",
                  fontsize=10, y=0.02)
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    out = os.path.join(outdir, "fig_effects.pdf")
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def fig_overload(rows, deferred_rows, outdir, overload):
    """Compare the in-run and deferred coordinated-omission fill.

    The campaign shows two apparent effects while the histogram fill runs inside
    the timed window: an allocator split at the first rung one heap still
    serves, and a language gap at the deepest overload point. Clock B keeps
    the intended-send origin, the correction cap, the pin and the kernel
    control, and moves only the fill to after the window. Both bars are that
    same host.

    Allocators remain in separate panels, so the figure does not hide the
    allocator control by pooling it.
    """
    if overload is None or not deferred_rows:
        return None
    variants = variants_present(rows)
    allocs = [a for a in ("system", "jemalloc")
              if (any(k[1] == a for k in variants)
                  and _subset(rows, ("cpp", a), overload)
                  and _subset(deferred_rows, ("cpp", a), overload))]
    langs = [l for l in ("cpp", "rust") if any(k[0] == l for k in variants)]
    if not allocs or len(langs) < 2:
        return None
    names = {"cpp": "C++", "rust": "Rust"}
    alloc_names = {"system": "system allocator", "jemalloc": "jemalloc"}
    thr_kops = lambda r: r["throughput_ops_s"] / 1000.0

    # The left-hand rung is the campaign's own first disagreement, derived here
    # so a typed load cannot drift from gen_macros.tex. When the two languages
    # stop tracking at different loads, that rung is the higher limit and both
    # allocators have to hold 95% of the offered rate. When they stop together,
    # the rung is the higher per-allocator limit, which is where one heap still
    # serves and the other has already fallen. The figure then has a bar for
    # the split the macros name, rather than for a language gap that was not
    # emitted.
    loads = sorted({r["rate"] * r["producers"] for r in rows})

    def variant_tracks(lang, alloc, load):
        vals = [thr_kops(r) for r in _subset(rows, (lang, alloc), load)]
        return bool(vals) and statistics.median(vals) >= 0.95 * load / 1000.0

    def lang_limit(lang):
        held = [
            load for load in loads
            if all(variant_tracks(lang, alloc, load) for alloc in allocs)
        ]
        return max(held) if held else 0

    limits = {lang: lang_limit(lang) for lang in langs}
    per_alloc = [
        max(
            (load for load in loads if variant_tracks(lang, alloc, load)),
            default=0,
        )
        for lang in langs for alloc in allocs
    ]
    if len(set(limits.values())) > 1:
        knee_gap = max(limits.values())
    elif len(set(per_alloc)) > 1:
        knee_gap = max(per_alloc)
    else:
        knee_gap = max(limits.values())
    points = [knee_gap, overload]
    if not knee_gap or knee_gap == overload:
        return None

    fig, axes = plt.subplots(1, len(allocs), figsize=(9.2, 3.8), sharey=True)
    if len(allocs) == 1:
        axes = [axes]

    clocks = [
        ("Fill during, this host", rows, ""),
        ("Fill after, this host", deferred_rows, "///"),
    ]
    width = 0.18
    offsets = (-1.5 * width, -0.5 * width, 0.5 * width, 1.5 * width)

    for ax, alloc, panel in zip(axes, allocs, ("a", "b")):
        series = 0
        for clock_name, source, hatch in clocks:
            for lang in langs:
                med, err_lo, err_hi = [], [], []
                for load in points:
                    vals = [thr_kops(r) for r in _subset(source, (lang, alloc), load)]
                    m, lo, hi = bootstrap_ci(vals)
                    med.append(m)
                    err_lo.append(max(0.0, m - lo))
                    err_hi.append(max(0.0, hi - m))
                xs = [j + offsets[series] for j in range(len(points))]
                colour = VARIANT_STYLE[(lang, alloc)][1]
                bars = ax.bar(
                    xs, med, width=width, color=colour, hatch=hatch,
                    edgecolor="#333333", linewidth=0.7,
                    label=f"{names[lang]}, {clock_name.lower()}",
                    yerr=[err_lo, err_hi], capsize=2.5,
                    error_kw={"lw": 0.9, "ecolor": "#333333"},
                )
                for bar, value in zip(bars, med):
                    ax.text(
                        bar.get_x() + bar.get_width() / 2, value + 7,
                        f"{value:.0f}", ha="center", va="bottom", fontsize=7.5,
                    )
                series += 1
        ax.set_xticks(range(len(points)))
        ax.set_xticklabels([f"{load / 1000:.0f} kops/s" for load in points])
        ax.set_xlabel("Offered load")
        ax.set_title(f"({panel}) {alloc_names[alloc]}", fontsize=9.5)
        ax.grid(True, axis="y", ls=":", alpha=0.4)
        ax.set_axisbelow(True)
        ax.set_ylim(0, max(points) / 1000.0 * 0.68)
    axes[0].set_ylabel("Sustained throughput (kops/s)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles, labels, ncol=2, fontsize=7.8, framealpha=0.95,
        loc="upper center", bbox_to_anchor=(0.5, 1.02),
    )
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    out = os.path.join(outdir, "fig_overload.pdf")
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def fmt_us(ns):
    return f"{ns / NS_PER_US:.1f}"


def fmt_p(p):
    """Format a p-value without rounding a small one away to ``0.000``.

    The attainable floor of the exact test falls as 2 / 2**n, so at the repeat
    counts a real campaign uses it drops below what three decimals can show. A
    floor printed as ``0.000`` would read as "vanishingly small" when the point
    of quoting it is to say exactly how small.
    """
    if p >= 0.001 or p <= 0.0:
        return f"{p:.3f}"
    exponent = max(3, int(math.ceil(-math.log10(p))) + 1)
    return f"{p:.{exponent}f}"


def med_ci_cell(values, decimals=None):
    """Format a metric as a median above its explicit bootstrap 95% [lo, hi] interval.

    The interval is reported in full rather than as a symmetric half-width. A
    bootstrap interval on the median of a heavy-tailed latency sample is strongly
    asymmetric, so collapsing it to a single `median +/- h` understates the upper
    tail, overstates the lower one, and at these dispersions produces a nominal
    lower bound below zero -- an impossible latency, and an artefact of the
    notation rather than of the data.

    Precision adapts to magnitude: quoting a 20 ms latency to a tenth of a
    microsecond would be false precision, and it is also what pushes the LaTeX
    table past the text width once the sweep reaches overload.
    """
    med, lo, hi = bootstrap_ci(values)
    if decimals is None:
        decimals = 1 if abs(med) < 1000 else 0
    return (
        f"\\mci{{{med:.{decimals}f}}}"
        f"{{{lo:.{decimals}f}}}{{{hi:.{decimals}f}}}"
    )


def _subset(rows, key, load):
    return [
        r
        for r in rows
        if r["lang"] == key[0] and r["alloc"] == key[1] and offered_load(r) == load
    ]


def _tail_resolution(rows, variants, load):
    """Whether the measurement resolves the comparison at each percentile.

    Panel (b) of fig:tailpct sets the spread between the four variants against
    the widest bootstrap interval on any one of them. When the ratio passes one
    the uncertainty about a single variant exceeds the gap between all four and
    no ordering can be read. These macros let the prose report which of those
    two states the campaign is in instead of asserting the one the previous host
    was in.
    """
    # Same range as fig:tailpct and for the same reason: the ratio needs an
    # across-repeat interval, the reported p99.99 is pooled and has none, and the
    # per-run p99.99 is the statistic Section 4.5 disowns.
    fields = [("p50", "p50"), ("p90", "p90"), ("p99", "p99"), ("p99.9", "p999")]
    worst, worst_at, crossed = 0.0, None, []
    for label, field in fields:
        if not has_metric(rows, ("lat_ns", field)):
            continue
        meds, widths = [], []
        for key in variants:
            vals = [r["lat_ns"][field] / NS_PER_US for r in _subset(rows, key, load)]
            if not vals:
                continue
            med, lo, hi = bootstrap_ci(vals)
            meds.append(med)
            widths.append(hi - lo)
        if len(meds) < 2:
            continue
        spread = max(meds) - min(meds)
        if spread <= 0:
            continue
        ratio = max(widths) / spread
        if ratio > worst:
            worst, worst_at = ratio, label
        if ratio > 1.0:
            crossed.append(label)
    if worst_at is None:
        return {}
    return {
        "TailResolveRatioMax": f"{worst:.1f}",
        "TailResolveRatioMaxAt": worst_at,
        "TailResolveCrossed": "yes" if crossed else "no",
    }


def pooled_far_tail(campaign_path, load):
    """Read the pooled far tail of one campaign at one offered load, in \u00b5s.

    A per-run p99.99 rests on about seventeen observations at the representative
    load, so `bench/pool_hist.py` concatenates the repeats' persisted HDR buckets
    and takes one percentile of the pooled distribution instead. That is a
    different statistic from the rest of tab:latency, and the difference is the
    point rather than an inconvenience: pooling takes the *operation* as the unit
    of analysis and resolves the far tail, at the cost of having no across-repeat
    dispersion to quote, while the median-of-repeats columns keep the *repeat* as
    the unit and are the only basis for a paired test. Mixing the two inside one
    claim is what `pool_hist.py` warns against, so the pooled column is printed
    without an interval and the caption says which column it is.

    Returns a dict keyed by (lang, alloc) with the pooled p99.99 and the sample
    count behind it, or None when the campaign has no pooled sidecar. Returning
    None rather than falling back to the per-run field is deliberate: a silent
    fallback is how the prose came to describe a statistic the pipeline was not
    computing.
    """
    if not campaign_path:
        return None
    base = re.sub(r"\.jsonl$", "", campaign_path)
    path = f"{base}.hist.pooled.csv"
    if not os.path.exists(path):
        print(f"note: no pooled histogram at {path}; "
              f"tab:latency will omit its p99.99 column. "
              f"Run bench/pool_hist.py on the campaign's .hist.jsonl sidecar.")
        return None
    out = {}
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if int(row["offered_ops_s"]) != int(load):
                continue
            out[(row["lang"], row["alloc"])] = {
                "p9999": int(row["p9999_ns"]) / NS_PER_US,
                "samples": int(row["samples"]),
            }
    return out or None


def latency_table_fields(rows, pooled=None):
    """Columns of tab:latency, widened to p99.99 when the far tail was pooled.

    The p99.99 column appears when a *pooled* figure exists, not when the runs
    happen to carry a per-run `p9999` field. The per-run version of that
    percentile is the one Section 4.5 calls dominated by sampling noise, so
    printing it would put a number in the table that the methodology chapter
    disowns two pages earlier.
    """
    fields = ["p50", "p99", "p999"]
    labels = ["p50", "p99", "p99.9"]
    if pooled:
        fields.append("p9999")
        labels.append("p99.99$^{\\dagger}$")
    fields.append("max")
    labels.append("max")
    return fields, labels


def write_latency_table(rows, outdir, load, pooled=None):
    """Emit the body of tab:latency at the representative load (values in \u00b5s)."""
    fields, _labels = latency_table_fields(rows, pooled)
    lines = []
    for key in variants_present(rows):
        label = VARIANT_STYLE[key][0]
        sub = _subset(rows, key, load)
        if not sub:
            continue

        def cell(field):
            # The pooled far tail is one percentile of one concatenated
            # distribution, so it has no interval to print. Everything else is a
            # median over repeats above its bootstrap interval.
            if field == "p9999":
                entry = (pooled or {}).get(key)
                return f"{entry['p9999']:.1f}" if entry else "---"
            return med_ci_cell([r["lat_ns"][field] / NS_PER_US for r in sub])

        lines.append(label + " & " + " & ".join(cell(f) for f in fields))
    out = os.path.join(outdir, "tab_latency.tex")
    with open(out, "w") as f:
        # Rows separated by \\ but no trailing \\, so \input can be followed by
        # \\\hline in the caller without a "Misplaced \noalign" boundary error.
        f.write(" \\\\\n".join(lines) + "\n")
    return out, load


def write_jitter_table(rows, outdir, load):
    """Emit the body of tab:jitter, or nothing when the campaign has no jitter data.

    Inter-operation jitter (IPDV) is only recorded when the run was made with
    --jitter, so this returns None for older campaigns rather than emitting a table
    of zeros that would read as a measured result.
    """
    if not has_metric(rows, ("jitter_ns", "p50")):
        return None
    lines = []
    for key in variants_present(rows):
        label = VARIANT_STYLE[key][0]
        sub = _subset(rows, key, load)
        if not sub:
            continue

        def cell(field):
            return med_ci_cell([r["jitter_ns"][field] / NS_PER_US for r in sub])

        lines.append(label + " & " + " & ".join(cell(f) for f in ("p50", "p99", "p999", "max")))
    out = os.path.join(outdir, "tab_jitter.tex")
    with open(out, "w") as f:
        f.write(" \\\\\n".join(lines) + "\n")
    return out


def _host_distro(text, envs, prior, kernel, image_distro):
    """The operating system of the machine, not of the image the build ran in.

    A capture written inside the container reads /etc/os-release from the image,
    so its distro line describes the toolchain's userland while every other field
    around it describes the host. That is exactly the pair a reader trips over:
    tab:testbed prints one kernel for a column whose distro belongs to something
    else. The host's own name has to come from the capture taken outside the
    container in the same session.

    Candidates are matched on the kernel, because a container shares the host's
    and that is the one field the two captures must agree on, so a stray capture
    from another machine cannot pass. Ordering follows the rule the caller uses
    for the campaign itself, nearest at or before the campaign first, then later
    captures. Nothing found leaves the value unknown rather than guessing, and an
    uncontainerised campaign has only the one operating system to report.
    """
    container = re.search(r"^container:\s+(\S+)", text, re.M)
    if not container or container.group(1) in ("none", "unknown"):
        return image_distro
    later = [e for e in envs if e not in prior]
    for path in list(reversed(prior[:-1])) + later:
        other = open(path, encoding="utf-8").read()
        if not re.search(r"^container:\s+none\s*$", other, re.M):
            continue
        found = re.search(r"Linux \S+ (\S+)", other)
        if not found or found.group(1) != kernel:
            continue
        distro = re.search(r"^distro:\s+(.+)", other, re.M)
        if distro:
            return distro.group(1).strip()
    return "unknown"


def main_host_macros(campaign_path):
    """Describe the host the reported campaign ran on, from its own capture.

    The testbed section used to spell the machine out in prose, which is exactly
    the kind of literal that survives a change of host and quietly describes the
    wrong one. Prefixed Main so a sentence cannot quote this host while appearing
    to describe either of the other two the study has used.

    The capture is matched to the campaign by timestamp rather than by taking the
    newest file, because a later probe run on the same box writes a later capture.
    """
    macros = {}
    stamp = re.search(r"campaign-(\d{8}-\d{6})", os.path.basename(campaign_path))
    if not stamp:
        return macros
    envs = sorted(glob.glob(os.path.join(os.path.dirname(campaign_path), "env-*.txt")))
    # The capture is written just before the sweep starts, so the match is the
    # latest capture at or before the campaign's own stamp.
    prior = [e for e in envs
             if (m := re.search(r"env-(\d{8}-\d{6})", e)) and m.group(1) <= stamp.group(1)]
    if not prior:
        return macros
    text = open(prior[-1], encoding="utf-8").read()

    def grab(pattern, default="unknown"):
        m = re.search(pattern, text, re.M)
        return m.group(1).strip() if m else default

    model = grab(r"Model name:\s+(.+)")
    macros["MainCpu"] = re.sub(r"\s*\d+-Core Processor\s*$", "", model).strip()
    cores = grab(r"Core\(s\) per socket:\s+(\d+)", "0")
    sockets = grab(r"Socket\(s\):\s+(\d+)", "0")
    if cores.isdigit() and sockets.isdigit() and int(cores) and int(sockets):
        macros["MainCores"] = str(int(cores) * int(sockets))
        macros["MainSockets"] = sockets
    macros["MainNumaNodes"] = grab(r"NUMA node\(s\):\s+(\d+)")
    macros["MainDistro"] = grab(r"distro:\s+(.+)")
    kernel = grab(r"Linux \S+ (\S+)")
    macros["MainKernel"] = kernel.replace("_", r"\_")
    macros["MainHostDistro"] = _host_distro(text, envs, prior, kernel, macros["MainDistro"])
    macros["MainVirt"] = grab(r"virtualisation:\s+(\S+)")
    macros["MainGovernor"] = grab(r"governors:\s+(\S+)")
    macros["MainSmt"] = grab(r"smt/control:\s+(\S+)")
    macros["MainThp"] = grab(r"transparent hugepages:\s+(\S+)")
    pinned = grab(r"cpus allowed here:\s+(\S+)")
    macros["MainPinned"] = re.sub(r"(\d)-(\d)", r"\1--\2", pinned)
    # How many cores that range actually is. The prose compares busy cores
    # against pinned cores past saturation, and the count was typed by hand and
    # went stale the first time the range changed.
    count = 0
    for part in pinned.split(","):
        if "-" in part:
            lo, hi = part.split("-")
            count += int(hi) - int(lo) + 1
        elif part.strip():
            count += 1
    if count:
        macros["MainPinnedCount"] = str(count)
    for field, key in (("isolcpus", "MainIsolcpus"), ("nohz_full", "MainNohzFull")):
        val = grab(rf"{field}:\s+(.+)")
        macros[key] = "none" if val.strip() == "(none)" else val.strip()
    gpp = grab(r"(g\+\+ \(.*?\) [\d.]+)")
    if gpp:
        macros["MainGpp"] = re.sub(r"g\+\+ \(.*?\) ", "", gpp)
    rustc = grab(r"rustc (\d+\.\d+\.\d+|\d+\.\d+)")
    if rustc:
        macros["MainRustc"] = rustc
    return macros


def write_generated_macros(rows, outdir, load, sig_results=(), budget=None, ffi=None,
                           overload=None, contention=None, campaign_path=None):
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

    def shown(xs, decimals=1):
        return [float(f"{x:.{decimals}f}") for x in xs]

    def shown_range(xs, decimals=1):
        """Spread as the reader would subtract it off tab:latency.

        A whole microsecond turned 1.536 into 2. Formatting the raw difference
        to one decimal would print 1.5 against the table's 73.7 minus 72.1.
        Subtracting the displayed medians keeps the prose checkable against
        the table that reports them. The matching percentage uses the same
        displayed pair, so 1.6 µs and 2.2% are one gap, not two roundings.
        """
        rounded = shown(xs, decimals)
        return max(rounded) - min(rounded)

    def shown_spread_pct(xs, decimals=1):
        rounded = shown(xs, decimals)
        return 100.0 * (max(rounded) / min(rounded) - 1)

    def shown_width(lo, hi, decimals=1):
        return abs(float(f"{hi:.{decimals}f}") - float(f"{lo:.{decimals}f}"))

    # Widest 95% CI on any single variant's p99 at the representative load,
    # measured as the full width of the interval, against the spread between
    # variants. When the former exceeds the latter the measurement cannot order
    # the variants at all, which is a finding about the environment rather than
    # about the languages. Widths are taken from the printed endpoints, the
    # same rule as shown_range: a whole microsecond turned 0.768 into 1 next
    # to a 1.6 µs gap.
    p99_ci = []
    for k in variants:
        sub = _subset(rows, k, load)
        if sub:
            _, lo, hi = bootstrap_ci([p99_us(r) for r in sub])
            p99_ci.append(shown_width(lo, hi))
    # Saturation knee: highest achieved throughput anywhere in the sweep, taken as
    # the minimum across variants so the quoted knee holds for all four. That
    # minimum is a floor and not a shared value, and on a host where the two
    # languages saturate at different loads it conceals the difference, so the
    # per-language figures below are emitted beside it and the prose quotes those
    # when it describes where each variant stops coping.
    knee = min(max(med_at(k, l, thr_kops) for l in loads) for k in variants)

    def tracks(keys, l):
        return all(med_at(k, l, thr_kops) >= 0.95 * l / 1000.0 for k in keys)

    # Highest offered load at which every variant still tracks the ideal line to 5%.
    tracking = [l for l in loads if tracks(variants, l)]
    by_lang = {}
    for lang in sorted({k[0] for k in variants}):
        keys = [k for k in variants if k[0] == lang]
        held = [l for l in loads if tracks(keys, l)]
        by_lang[lang] = {
            "tracking": max(held) if held else 0,
            "knee": min(max(med_at(k, l, thr_kops) for l in loads) for k in keys),
        }

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
        "PNineNineSpread": f"{shown_spread_pct(p99):.1f}",
        "PFiftySpread": f"{shown_spread_pct(p50):.1f}",
        "PFiftyRange": f"{shown_range(p50):.1f}",
        "PNineNineRange": f"{shown_range(p99):.1f}",
        "PNineNineMaxCI": f"{max(p99_ci):.1f}" if p99_ci else "0",
        # The same comparison fig:tailpct panel (b) draws, as one number: the
        # largest ratio of within-variant uncertainty to between-variant spread
        # across the percentile range. Below one at every percentile means the
        # measurement resolves the comparison everywhere it is read. The prose
        # quoted a crossover here for as long as the guest campaign was reported,
        # and a crossover is exactly what this macro exists to stop asserting
        # when the data does not show one.
        **_tail_resolution(rows, variants, load),
        "MaxOfferedLoad": f"{max(loads) / 1000.0:.0f}",
        # The median's own magnitude, so prose can say what a resolved difference
        # of a microsecond or two is a difference *in* without typing the scale.
        # Rounded to ten because it is quoted as an order of size and not as a
        # measurement: a reader comparing "1.6 against 80" should not be invited
        # to read the second figure to the same precision as the first.
        "PFiftyMedian": f"{round(statistics.median(p50) / 10.0) * 10:.0f}",
        # The two ends of the tracking region, and how much p99 moves between
        # them. The prose describes the shape of Figure fig:loadsweep panel (a),
        # so the numbers anchoring that description belong here rather than in
        # the sentence. All three are the median across variants and not an
        # extreme, because the sentence is about the four behaving alike inside
        # the region: quoting one variant's worst point would describe a curve
        # the figure does not draw.
        #
        # The shape these measure is a *flat* region, not a climb. Both ends are
        # therefore kept in microseconds. An earlier version divided the upper end
        # by a thousand and printed it as milliseconds, which rounded to zero on a
        # quiet host and anchored the cliff sentence at "0 ms".
        "PNineNineLightest": (
            f"{statistics.median([med_at(k, min(loads), p99_us) for k in variants]):.0f}"
        ),
        "PNineNineTrackingTop": (
            f"{statistics.median([med_at(k, max(tracking), p99_us) for k in variants]):.0f}"
            if tracking else "0"
        ),
        # Signed, because the direction is the finding: on the virtualised host
        # p99 rose across the tracking region and on a quiet one it falls
        # slightly, so a sentence claiming a gentle climb is host-specific.
        "PNineNineTrackingDrift": (
            f"{statistics.median([med_at(k, max(tracking), p99_us) for k in variants]) - statistics.median([med_at(k, min(loads), p99_us) for k in variants]):+.0f}"
            if tracking else "0"
        ),
        # Where each language stops meeting its offered rate, and what it peaks
        # at. Quoted instead of SatKnee wherever the prose says where a variant
        # stops coping, because SatKnee is a minimum across all four.
        "TrackingLoadCpp": f"{by_lang['cpp']['tracking'] / 1000.0:.0f}" if "cpp" in by_lang else "0",
        "TrackingLoadRust": f"{by_lang['rust']['tracking'] / 1000.0:.0f}" if "rust" in by_lang else "0",
        "SatKneeCpp": f"{by_lang['cpp']['knee']:.0f}" if "cpp" in by_lang else "0",
        "SatKneeRust": f"{by_lang['rust']['knee']:.0f}" if "rust" in by_lang else "0",
        "KneeShared": (
            "yes" if len({v["tracking"] for v in by_lang.values()}) == 1 else "no"
        ),
    }

    # The rung between the two languages' tracking limits, when they differ. One
    # language still serves its offered rate there and the other has collapsed,
    # which is the largest throughput gap anywhere in the sweep and runs opposite
    # to the gap at the pre-committed overload point. Reported descriptively and
    # deliberately not tested: the operating point was identified after seeing the
    # data, and Section 4.5 fixes the family in advance precisely so that a point
    # chosen this way cannot enter it.
    limits = {lang: v["tracking"] for lang, v in by_lang.items()}
    if len(set(limits.values())) > 1:
        ahead = max(limits, key=lambda lang: limits[lang])
        behind = min(limits, key=lambda lang: limits[lang])
        rung = limits[ahead]
        fast = [med_at(k, rung, thr_kops) for k in variants if k[0] == ahead]
        slow = [med_at(k, rung, thr_kops) for k in variants if k[0] == behind]
        fast_med, slow_med = statistics.median(fast), statistics.median(slow)
        # Per-repeat sign agreement, paired by position inside the allocator, the
        # same pairing _paired_effect documents.
        agree = total = 0
        for alloc in sorted({k[1] for k in variants}):
            a = [thr_kops(r) for r in _subset(rows, (behind, alloc), rung)]
            b = [thr_kops(r) for r in _subset(rows, (ahead, alloc), rung)]
            for x, y in zip(a, b):
                total += 1
                agree += 1 if y > x else 0
        macros.update({
            "KneeGapLoad": f"{rung / 1000.0:.0f}",
            "KneeGapFaster": LANG_LABEL.get(ahead, ahead),
            "KneeGapSlower": LANG_LABEL.get(behind, behind),
            "KneeGapThrFast": f"{fast_med:.0f}",
            "KneeGapThrSlow": f"{slow_med:.0f}",
            "KneeGapRatio": f"{fast_med / slow_med:.1f}",
            "KneeGapAgree": f"{agree}/{total}",
        })

    # Per-allocator tracking. A language can fail the both-heaps test because
    # one heap's median has fallen while the other still serves the offered
    # rate, and the repeats on the fallen heap can be split rather than all
    # collapsed. Those facts are generated here so a sentence cannot invent a
    # language knee from the absence of KneeGap, and cannot type the repeat
    # count.
    alloc_tag = {"system": "System", "jemalloc": "Jemalloc"}
    alloc_limit = {}
    for lang in sorted({k[0] for k in variants}):
        for alloc in sorted({k[1] for k in variants if k[0] == lang}):
            held = [
                l for l in loads
                if med_at((lang, alloc), l, thr_kops) >= 0.95 * l / 1000.0
            ]
            limit = max(held) if held else 0
            alloc_limit[(lang, alloc)] = limit
            tag = {"cpp": "Cpp", "rust": "Rust"}[lang]
            macros[f"TrackingLoad{tag}{alloc_tag[alloc]}"] = (
                f"{limit / 1000.0:.0f}"
            )

    splits = []
    for lang in sorted({k[0] for k in alloc_limit}):
        pair = {alloc: alloc_limit[(lang, alloc)] for alloc in alloc_tag
                if (lang, alloc) in alloc_limit}
        if len(pair) < 2 or len(set(pair.values())) < 2:
            continue
        keep = max(pair, key=pair.get)
        drop = min(pair, key=pair.get)
        splits.append((pair[keep] - pair[drop], lang, keep, drop, pair[keep]))
    if splits:
        _, lang, keep, drop, rung = max(splits)
        runs = _subset(rows, (lang, drop), rung)
        meet = sum(
            1 for r in runs if thr_kops(r) >= 0.95 * rung / 1000.0
        )
        macros.update({
            "KneeSplitLoad": f"{rung / 1000.0:.0f}",
            "KneeSplitLang": LANG_LABEL.get(lang, lang),
            "KneeSplitKeepHeap": "jemalloc" if keep == "jemalloc" else "system allocator",
            "KneeSplitDropHeap": "jemalloc" if drop == "jemalloc" else "system allocator",
            "KneeSplitMeet": str(meet),
            "KneeSplitRepeats": str(len(runs)),
            "KneeSplitMedKeep": f"{med_at((lang, keep), rung, thr_kops):.0f}",
            "KneeSplitMedDrop": f"{med_at((lang, drop), rung, thr_kops):.0f}",
        })

    # The preamble of tab:latency travels with its generated body. The table gains
    # a p99.99 column the moment a campaign records one, and a hand-written
    # column specification in the thesis would then be one column short of the
    # \input body -- a build error at best and a silently mislabelled table at
    # worst. Generating both keeps the two in step with no manual edit.
    #
    # The whole \begin{tabular}{...} is emitted rather than just the column
    # specification, because the array package's preamble scanner does not expand
    # macros: `\begin{tabular}{\LatencyCols}` fails with "Illegal pream-token".
    # Expanding a macro that already contains the \begin leaves literal preamble
    # tokens for the scanner to read.
    pooled = pooled_far_tail(campaign_path, load)
    lat_fields, lat_labels = latency_table_fields(rows, pooled)
    cols = "@{}l" + " r" * len(lat_fields) + "@{}"
    macros["LatencyTabular"] = "\\begin{tabular}{" + cols + "}"
    # Units sit in the header a reader looks at, not only in the caption.
    # tab:resource already names (kops/s), (MiB) and (%) on its columns.
    # tab:latency used to bury microseconds in the caption's second sentence,
    # which left the body looking like a unitless score. The spanning row
    # is generated with the column count so a campaign that drops p99.99
    # cannot leave a five-column banner over four number columns.
    n = len(lat_labels)
    macros["LatencyHead"] = (
        f"& \\multicolumn{{{n}}}{{c}}{{(\\textmu s)}} \\\\ "
        "Variant & " + " & ".join(lat_labels)
    )

    # p99.99 and inter-operation jitter, reported descriptively.
    #
    # Neither is added to the Holm-tested family (see TESTED_METRICS). The rule
    # this thesis pre-commits is that pairing cancels the interference a whole
    # interleaved block shares, not interference landing on one run of a pair, so
    # it rescues run-level and central statistics and not high percentiles, which
    # are computed from exactly the disturbed operations. p99.99 is the extreme
    # case of that, and a jitter percentile is a dispersion of the same disturbed
    # samples. Testing them would spend two more slots of the family-wise budget
    # on comparisons that cannot resolve and make Holm harsher on the ones that
    # can -- the same reasoning that removed achieved throughput from the family.
    # The far tail comes from the pooled distribution and never from the per-run
    # p9999 field, which is the statistic Section 4.5 calls dominated by sampling
    # noise. Reading it from the campaign JSONL would put a number on the page
    # that the methodology chapter disowns, and it did until 27 August 2026.
    if pooled:
        far = [pooled[k]["p9999"] for k in variants if k in pooled]
        samples = [pooled[k]["samples"] for k in variants if k in pooled]
        fast = min(pooled.items(), key=lambda kv: kv[1]["p9999"])[0]
        macros.update({
            "FarTailSpread": f"{100.0 * (max(far) / min(far) - 1):.0f}",
            "FarTailRange": f"{max(far) - min(far):.0f}",
            "FarTailMax": f"{max(far):.0f}",
            "FarTailMin": f"{min(far):.0f}",
            "FarTailLower": LANG_LABEL.get(fast[0], fast[0]),
            "FarTailSamplesMin": f"{min(samples):,}".replace(",", "\\,"),
            "FarTailSamplesMax": f"{max(samples):,}".replace(",", "\\,"),
            # Whether the two languages separate at this percentile with no
            # overlap between their variants, which is what licenses an ordering from
            # a statistic that carries no interval.
            "FarTailByLang": (
                "yes" if max(pooled[k]["p9999"] for k in pooled if k[0] == "rust")
                < min(pooled[k]["p9999"] for k in pooled if k[0] == "cpp")
                else "no"
            ),
            # The gap *between the languages*, which is the worst-case pair and
            # not the range across all four. FarTailRange spans the extremes, so
            # it is the right number for "the widest gap between variants" and
            # the wrong one for "Rust is ahead by", which is this. Quoting the
            # range for the separation overstates the effect by about three
            # quarters.
            "FarTailLangSep": (
                f"{min(pooled[k]['p9999'] for k in pooled if k[0] == 'cpp') - max(pooled[k]['p9999'] for k in pooled if k[0] == 'rust'):.0f}"
            ),
        })
    if has_metric(rows, ("lat_ns", "p25")) and has_metric(rows, ("lat_ns", "p75")):
        iqr_us = lambda r: (r["lat_ns"]["p75"] - r["lat_ns"]["p25"]) / NS_PER_US
        iqr = [med_at(k, load, iqr_us) for k in variants]
        macros.update({
            "IqrSpread": f"{100.0 * (max(iqr) / min(iqr) - 1):.0f}",
            "IqrLo": f"{min(iqr):.0f}",
            "IqrHi": f"{max(iqr):.0f}",
        })
    if has_metric(rows, ("jitter_ns", "p50")):
        jp50_us = lambda r: r["jitter_ns"]["p50"] / NS_PER_US
        jp99_us = lambda r: r["jitter_ns"]["p99"] / NS_PER_US
        jp50 = [med_at(k, load, jp50_us) for k in variants]
        jp99 = [med_at(k, load, jp99_us) for k in variants]
        # Emitted as separate endpoints rather than as one "lo--hi" string. A
        # combined range macro reads naturally in the source and typesets as two
        # minus signs the moment the sentence wraps it in math mode for the \mu,
        # which is how "1--2" reached the page as "1 - -2". Every other range in
        # this file is a Lo/Hi pair for the same reason.
        macros.update({
            # Two decimals, because JitterSpread is computed from the unrounded
            # medians and the prose prints both in the same sentence. At one
            # decimal the bounds read 1.4 and 1.7, which divide to 21 per cent
            # against a printed spread of 26.
            "JitterLo": f"{min(jp50):.2f}",
            "JitterHi": f"{max(jp50):.2f}",
            "JitterSpread": f"{100.0 * (max(jp50) / min(jp50) - 1):.0f}",
            "JitterPNineNineLo": f"{min(jp99):.0f}",
            "JitterPNineNineHi": f"{max(jp99):.0f}",
            # Jitter against the median it perturbs, as a percentage, which is
            # what says whether consecutive operations vary by a rounding error
            # or by a whole median. Named for the unit it carries: an earlier
            # name invited the prose to print it as a multiple, and the prose did.
            "JitterVsMedianPct": (
                f"{100.0 * statistics.median(jp50) / statistics.median(p50):.0f}"
            ),
            "JitterPNineNineVsMedianPct": (
                f"{100.0 * statistics.median(jp99) / statistics.median(p50):.0f}"
            ),
        })

    if sig_results:
        # The exact paired test cannot report a p below 2 / 2**n, so the floor is
        # quoted alongside the results: whether a null finding is a statement
        # about the data or about the design's resolving power depends on where
        # that floor sits relative to the threshold being applied.
        n_pairs = max(r["n"] for r in sig_results)
        # Scoped to the representative load: an overload row carries the same
        # metric name for a different quantity, and these macros are quoted in
        # sentences about the below-saturation operating point.
        pick = lambda pre: [r for r in sig_results
                            if r["metric"].startswith(pre) and r.get("point", "repr") == "repr"]
        p50_rows, rss_rows, cpu_rows = pick("p50"), pick("Peak RSS"), pick("CPU")
        floor = attainable_floor(n_pairs)
        macros.update({
            "NTests": str(len(sig_results)),
            "MinAttainableP": fmt_p(floor),
            # The smallest Holm-adjusted value the design can return at all: the
            # most significant test is compared against the full family size, so
            # the corrected floor is NTests times the uncorrected one. Quoting it
            # is what lets the reader tell a null result from an unresolvable one.
            "CorrectedFloor": fmt_p(min(1.0, len(sig_results) * floor)),
            "NSignificant": str(sum(1 for r in sig_results if r["holm"] < 0.05)),
            "SmallestHolm": fmt_p(min(r["holm"] for r in sig_results)),
            # How the one interval-based reading applies across the whole family,
            # so the text can state the rule once and be held to it.
            "NExclZero": str(sum(1 for r in sig_results if r["excl_zero"])),
            "NTailExclZero": str(
                sum(1 for r in sig_results if r["excl_zero"] and r["kind"] == "tail")
            ),
            # How many tail rows clear the correction, which is a different
            # question from how many have an interval excluding zero and is the
            # one the results prose asks. The two are equal today and there is no
            # reason they must stay equal, so a sentence about the correction
            # quotes this and not NTailExclZero.
            "NTailSignificant": str(
                sum(1 for r in sig_results if r["holm"] < 0.05 and r["kind"] == "tail")
            ),
            "TailExclZeroRows": describe_rows(sig_results, "tail"),
            "RobustExclZeroRows": describe_rows(sig_results, "robust"),
            "PFiftyDiffAbsMax": (
                f"{max(abs(r['diff']) for r in p50_rows):.1f}" if p50_rows else "0"
            ),
            # One decimal, not zero. BudgetBoundVsCore divides this same bound by
            # the operation's own cost and rounds only the ratio, so printing the
            # bound as a whole number put "an interval of 1 us ... is 38 times the
            # operation's cost" in one sentence, where 1 / 0.0345 is 29. It is also
            # the same quantity as EqvBoundPFifty, which has always carried a
            # decimal, so the two disagreed with each other on the same page.
            "PFiftyDiffCIMax": (
                f"{max(max(abs(r['lo']), abs(r['hi'])) for r in p50_rows):.1f}"
                if p50_rows else "0"
            ),
            # Equivalence bounds: the tightest margin each unresolved comparison
            # supports. These say what a p-value cannot, which is how large the
            # difference could be given that the test did not find one.
            "NEqvUnresolved": str(sum(1 for r in sig_results if r["holm"] >= 0.05)),
            "EqvBoundPFifty": (
                f"{max(r['eqv'] for r in p50_rows):.1f}" if p50_rows else "0"
            ),
            "EqvBoundTailMax": (
                f"{max(r['eqv'] for r in sig_results if r['kind'] == 'tail'):.0f}"
                if any(r["kind"] == "tail" for r in sig_results) else "0"
            ),
        })
        if rss_rows:
            macros.update({
                "RssLangDiffLo": f"{min(r['diff'] for r in rss_rows):.1f}",
                "RssLangDiffHi": f"{max(r['diff'] for r in rss_rows):.1f}",
                "RssLangCILo": f"{min(r['lo'] for r in rss_rows):.1f}",
                "RssLangCIHi": f"{max(r['hi'] for r in rss_rows):.1f}",
            })
            # The per-repeat sign agreement for the peak-RSS row that fails Holm,
            # and the size of the contaminated runs that make it fail. Together
            # these are the whole justification for reading that row from its
            # interval instead of its p-value, so a rerun has to be able to move
            # them: OverloadThrAgree is the same quantity for the overload family
            # and has been generated since the eighth pass.
            worst = max(rss_rows, key=lambda r: r["holm"])
            macros["RssAgree"] = f"{worst['agree']}/{worst['n']}"
            low_offset = rss_low_run_offset(rows, load)
            if low_offset is not None:
                macros["RssLowRunOffset"] = f"{low_offset:.0f}"
        if cpu_rows:
            macros["CpuDiffAbsMax"] = f"{max(abs(r['diff']) for r in cpu_rows):.1f}"

        # Which effects survive the allocator control as a replication check.
        consistent, reversed_ = cross_allocator_agreement(sig_results)
        join = lambda xs: (xs[0] if len(xs) == 1
                           else ", ".join(xs[:-1]) + " and " + xs[-1]) if xs else "none"
        macros.update({
            "CrossAllocConsistent": join(consistent),
            "CrossAllocReversed": join(reversed_),
            "NCrossAllocReversed": str(len(reversed_)),
        })

        # The overload operating point. Whether the sweep reached it at all is
        # recorded first, because every sentence below is conditional on that and
        # a campaign whose ladder stopped short should say so rather than quote
        # the top of its own range as though it were a saturation point.
        thr_rows = [r for r in sig_results
                    if r.get("point") == "overload" and r["metric"].startswith("Sustained")]
        macros["SatReached"] = "yes" if overload is not None else "no"
        if overload is not None and thr_rows:
            cpp_thr = statistics.median(
                [med_at(("cpp", a), overload, thr_kops) for a in ("system", "jemalloc")
                 if _subset(rows, ("cpp", a), overload)])
            rust_thr = statistics.median(
                [med_at(("rust", a), overload, thr_kops) for a in ("system", "jemalloc")
                 if _subset(rows, ("rust", a), overload)])
            hi_lang, lo_lang = (("C++", "Rust") if cpp_thr >= rust_thr else ("Rust", "C++"))
            macros.update({
                "OverloadLoad": f"{overload / 1000.0:.0f}",
                "OverloadThrCpp": f"{cpp_thr:.0f}",
                "OverloadThrRust": f"{rust_thr:.0f}",
                "OverloadThrRatio": f"{max(cpp_thr, rust_thr) / min(cpp_thr, rust_thr):.1f}",
                "OverloadSustainedFaster": hi_lang,
                "OverloadSustainedSlower": lo_lang,
                # The weakest of the per-allocator results is quoted, so the
                # sentence holds under either allocator rather than under the
                # more favourable one. The bound is the interval endpoint nearest
                # zero across both, which supports "at least this large" rather
                # than an interval that would read backwards once the two
                # allocators' negative intervals were combined endpoint-wise.
                "OverloadThrDiff": f"{min(abs(r['diff']) for r in thr_rows):.0f}",
                "OverloadThrBound": (
                    f"{min(min(abs(r['lo']), abs(r['hi'])) for r in thr_rows):.0f}"
                ),
                "OverloadThrP": fmt_p(max(r["p"] for r in thr_rows)),
                "OverloadThrHolm": fmt_p(max(r["holm"] for r in thr_rows)),
                "OverloadThrAgree": (f"{min(r['agree'] for r in thr_rows)}/"
                                     f"{max(r['n'] for r in thr_rows)}"),
            })
            # CPU spent per completed operation, as a ratio between the languages.
            # Total CPU alone understates the effect: the slower variant is not
            # idle while it under-delivers, so the interesting quantity is the
            # cost of the work that did complete.
            cpu_pct = lambda r: r["cpu_pct"]
            per_op = {}
            for lang in ("cpp", "rust"):
                vals = [
                    med_at((lang, a), overload, cpu_pct) / med_at((lang, a), overload, thr_kops)
                    for a in ("system", "jemalloc") if _subset(rows, (lang, a), overload)
                ]
                if vals:
                    per_op[lang] = statistics.median(vals)
            if len(per_op) == 2 and min(per_op.values()) > 0:
                higher = max(per_op, key=per_op.get)
                macros["OverloadCpuPerOpRatio"] = (
                    f"{per_op[higher] / min(per_op.values()):.1f}"
                )
                macros["OverloadCpuPerOpHigher"] = LANG_LABEL.get(higher, higher)

    # The allocator effect on peak RSS, held against the language effect above:
    # jemalloc minus the system allocator, with the language held fixed.
    rss_mib = lambda r: r["rss_peak_kb"] / 1024.0
    alloc_diffs = []
    for lang in ("cpp", "rust"):
        sys_runs = [rss_mib(r) for r in _subset(rows, (lang, "system"), load)]
        jem_runs = [rss_mib(r) for r in _subset(rows, (lang, "jemalloc"), load)]
        if sys_runs and jem_runs:
            alloc_diffs.append(paired_permutation_test(sys_runs, jem_runs)[0])
    if alloc_diffs:
        macros["RssAllocDiffLo"] = f"{min(alloc_diffs):.1f}"
        macros["RssAllocDiffHi"] = f"{max(alloc_diffs):.1f}"

    if budget and budget.get("cpp") and budget.get("rust"):
        med = lambda lang, key: budget_median(budget, lang, key)
        core_cpp, core_rust = med("cpp", "core_ns"), med("rust", "core_ns")
        macros.update({
            "BudgetRepeats": str(min(len(budget["cpp"]), len(budget["rust"]))),
            # The decomposition runs fewer repeats than the sweep, so it has its
            # own floor and the prose has to quote that one and not the sweep's.
            # Derived from the same helper as MinAttainableP rather than typed,
            # so changing BudgetRepeats moves it.
            "BudgetFloor": fmt_p(
                attainable_floor(min(len(budget["cpp"]), len(budget["rust"])))),
            "BudgetCoreCpp": f"{core_cpp:.1f}",
            "BudgetCoreRust": f"{core_rust:.1f}",
            "BudgetSvcCpp": fmt_us_adaptive(med("cpp", "service_ns")),
            "BudgetSvcRust": fmt_us_adaptive(med("rust", "service_ns")),
            "BudgetHandoffCpp": fmt_us_adaptive(med("cpp", "handoff_ns")),
            "BudgetHandoffRust": fmt_us_adaptive(med("rust", "handoff_ns")),
            "BudgetCoreShareMax": f"{max(med(l, 'core_share_pct') for l in budget):.3f}",
            # The same quantity read the other way round, because the prose makes
            # the point in both directions and an eyeballed complement got it
            # wrong once: 0.250 leaves 99.750, not "better than 99.9".
            "BudgetCoreShareRest": (
                f"{100.0 - max(med(l, 'core_share_pct') for l in budget):.3f}"),
            # Which language runs the bare operation faster, and by how much. The
            # sweep cannot see this at all: it is four ten-thousandths of the
            # number the sweep reports.
            "BudgetCoreFaster": "Rust" if core_rust < core_cpp else "C++",
            "BudgetCoreRatio": (
                f"{max(core_cpp, core_rust) / min(core_cpp, core_rust):.1f}"
                if min(core_cpp, core_rust) > 0 else "0"
            ),
            "BudgetHandoffSlower": (
                "Rust" if med("rust", "handoff_ns") > med("cpp", "handoff_ns") else "C++"
            ),
        })
        # How many times the operation's own cost the paired median bound is.
        # This is the number that decides what the bound actually excludes: a
        # bound of a fifth of the end-to-end median is a bound of many times the
        # work if the median is mostly handoff.
        p50_sig = [x for x in sig_results if x["metric"].startswith("p50")]
        core_us_max = max(core_cpp, core_rust) / NS_PER_US
        if p50_sig and core_us_max > 0:
            bound_us = max(max(abs(r["lo"]), abs(r["hi"])) for r in p50_sig)
            macros["BudgetBoundVsCore"] = f"{bound_us / core_us_max:.0f}"

    if contention and contention.get("cpp") and contention.get("rust"):
        med_thr = lambda lang: statistics.median(
            r["throughput_kops"] for r in contention[lang])
        cpp_thr, rust_thr = med_thr("cpp"), med_thr("rust")
        _, cont_p, _ = paired_permutation_test(
            [r["throughput_kops"] for r in contention["cpp"]],
            [r["throughput_kops"] for r in contention["rust"]],
        )
        if min(cpp_thr, rust_thr) > 0:
            macros.update({
                "ContentionRepeats": str(
                    min(len(contention["cpp"]), len(contention["rust"]))),
                "ContentionThrCpp": f"{cpp_thr:.0f}",
                "ContentionThrRust": f"{rust_thr:.0f}",
                "ContentionFaster": "C++" if cpp_thr > rust_thr else "Rust",
                "ContentionRatio": (
                    f"{max(cpp_thr, rust_thr) / min(cpp_thr, rust_thr):.1f}"),
                "ContentionP": fmt_p(cont_p),
                "ContentionProducers": str(
                    contention["cpp"][0].get("producers", 7)),
            })

    if ffi:
        native, through = ffi.get("op_roundtrip_native_ns", 0), ffi.get("op_roundtrip_ns", 0)
        if native > 0 and through > 0 and "op_seam_delta_ns" in ffi:
            macros.update({
                "FfiCrossing": f"{ffi.get('ffi_crossing_ns', 0):.2f}",
                "FfiOpRepeats": str(ffi.get("op_repeats", 0)),
                "FfiOpNative": f"{native / 1000.0:.1f}",
                "FfiOpSeam": f"{through / 1000.0:.1f}",
                "FfiOpDelta": f"{ffi['op_seam_delta_ns']:+.0f}",
                "FfiOpDeltaLo": f"{ffi['op_seam_delta_lo_ns']:+.0f}",
                "FfiOpDeltaHi": f"{ffi['op_seam_delta_hi_ns']:+.0f}",
                "FfiOpP": f"{ffi.get('op_paired_p', 1):.3f}",
                # The bound the interval places on the seam, as a fraction of the
                # operation it is charged against. This is what RQ4 can actually
                # claim: not that the cost is zero, but that it is at most this.
                "FfiOpBoundPct": f"{100.0 * ffi['op_seam_delta_hi_ns'] / native:.2f}",
            })

    if campaign_path:
        macros.update(main_host_macros(campaign_path))

    out = os.path.join(outdir, "gen_macros.tex")
    with open(out, "w") as f:
        f.write("% Generated by bench/plot_figures.py -- do not edit by hand.\n")
        for k, v in macros.items():
            f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
    return out


#: Metrics carried into the paired significance test, in table order.
#:
#: Each entry is (label, extractor, decimals, kind). ``kind`` records whether the
#: statistic is *robust* to interference landing on a few samples within a run or
#: is *determined* by it. A run-level summary (peak RSS, CPU) and a central order
#: statistic over tens of thousands of samples (p50) barely move when a handful of
#: operations are descheduled; p99 and p99.9 are computed from exactly those
#: operations. Pairing cancels the interference a whole block shares, so it
#: rescues the first group and not the second, and the tables and prose need to
#: distinguish them rather than reading every interval the same way.
#:
#: Achieved throughput is deliberately absent. The representative load is chosen
#: below saturation, where achieved throughput equals offered load for every
#: variant by construction, so the comparison cannot resolve a language effect
#: whatever the languages do: it re-measures the operating point, not the code.
#: Including it would still consume two slots in the family-wise correction and
#: make Holm more punitive on the comparisons that can resolve. It is reported
#: with its interval in the resource table instead, where it serves its real
#: purpose of confirming the operating point is sustained rather than nominal.
#:
#: p99.99 and inter-operation jitter are absent for the same structural reason
#: rather than an oversight. Both are computed from precisely the operations that
#: interference lands on, which is the class of statistic the pre-committed rule
#: says pairing does not rescue, so a paired interval on them could not be read as
#: a language effect. They are reported descriptively, in tab:latency, tab:jitter,
#: fig_tail_percentiles and their macros, and the family stays at the size the
#: design committed to.
TESTED_METRICS = [
    ("p50 latency (\\textmu s)", lambda r: r["lat_ns"]["p50"] / NS_PER_US, 1, "robust"),
    ("p99 latency (\\textmu s)", lambda r: r["lat_ns"]["p99"] / NS_PER_US, 0, "tail"),
    ("p99.9 latency (\\textmu s)", lambda r: r["lat_ns"]["p999"] / NS_PER_US, 0, "tail"),
    ("Peak RSS (MiB)", lambda r: r["rss_peak_kb"] / 1024.0, 1, "robust"),
    ("CPU utilisation (\\%)", lambda r: r["cpu_pct"], 1, "robust"),
]

# Metrics tested at the overload operating point. Achieved throughput leads
# because past saturation it stops being pinned to the offered rate and becomes
# the quantity that separates the variants; CPU accompanies it because it says
# whether a variant that delivers less is idle or busy while doing so.
#
# The latency percentiles are deliberately absent. Above saturation the measured
# phase is truncated and the coordinated-omission backfill is capped, so a
# reported tail there is a lower bound rather than an estimate, and testing a
# lower bound would attach a p-value to an artefact of the harness.
OVERLOAD_METRICS = [
    ("Sustained throughput (kops/s)", lambda r: r["throughput_ops_s"] / 1000.0, 1, "robust"),
    ("CPU utilisation (\\%)", lambda r: r["cpu_pct"], 1, "robust"),
]


def significance_results(rows, load, overload=None):
    """Paired C++-vs-Rust tests, one per metric x allocator x operating point.

    The allocator is held fixed inside each comparison so that the only thing
    varying is the language, which is the independent variable the whole study is
    built around. Pairing is by repeat index: the campaign's outer loop is the
    repeat, so the i-th run of each variant at a given load belongs to the same
    interleaved block.

    When an overload point is supplied its comparisons join the same family rather
    than forming a second one. Holm then corrects across everything reported, which
    is the conservative reading: two separately corrected families would let a
    reader wonder whether the split was chosen once the p-values were known.
    """
    results = []
    points = [("repr", load, TESTED_METRICS)]
    if overload is not None and overload != load:
        points.append(("overload", overload, OVERLOAD_METRICS))

    for point, point_load, metrics in points:
        allocs = [a for a in ("system", "jemalloc")
                  if ("cpp", a) in VARIANT_STYLE and _subset(rows, ("cpp", a), point_load)]
        for label, fn, decimals, kind in metrics:
            for alloc in allocs:
                cpp = [fn(r) for r in _subset(rows, ("cpp", alloc), point_load)]
                rust = [fn(r) for r in _subset(rows, ("rust", alloc), point_load)]
                if not cpp or not rust:
                    continue
                diff, p, n = paired_permutation_test(cpp, rust)
                paired = [y - x for x, y in zip(cpp, rust)]
                _, lo, hi = bootstrap_ci(paired)
                # How many repeats agree with the sign of the median effect. A
                # count carries information a p-value computed from the mean does
                # not: it is unmoved by a single contaminated run, so the two
                # disagreeing is itself diagnostic.
                sign = (diff > 0) - (diff < 0)
                agree = sum(1 for d in paired if ((d > 0) - (d < 0)) == sign) if sign else 0
                results.append({
                    "metric": label, "alloc": alloc, "decimals": decimals, "kind": kind,
                    "point": point, "load": point_load,
                    "diff": diff, "lo": lo, "hi": hi, "p": p, "n": n,
                    "agree": agree,
                    # The C++ median this effect is a difference from. Carried so a
                    # figure can put metrics measured in microseconds, mebibytes,
                    # percent and kops/s on one axis as a share of their own
                    # baseline; the tables keep the metric's own units.
                    "base": statistics.median(cpp),
                    # The tightest margin within which this comparison can be
                    # called equivalent. Reported for every row, including the
                    # ones that reach significance, where it doubles as an upper
                    # bound on how large the effect can be.
                    "eqv": equivalence_bound(cpp, rust),
                    # Whether the paired interval sits wholly on one side of zero.
                    # Recorded per row so the prose can apply one rule to the whole
                    # family instead of picking the rows it likes.
                    "excl_zero": (lo > 0.0 and hi > 0.0) or (lo < 0.0 and hi < 0.0),
                })
    for res, adj in zip(results, holm_adjust([r["p"] for r in results])):
        res["holm"] = adj
    return results


def _plain(label):
    """Drop the parenthesised unit from a metric label for use in running prose.

    The result is spliced into a LaTeX macro, so it must stay free of the markup
    the table labels carry (``\\textmu s``, ``\\%``); dropping the unit removes it
    and reads better in a sentence than a table heading would.
    """
    return label.split(" (")[0]


def describe_rows(results, kind=None, point="repr"):
    """Render the rows whose paired interval excludes zero as an English phrase.

    Emitted as a macro so the sentence that names them cannot go stale when the
    campaign is rerun: if a row drops out of the set, the prose stops naming it.

    Scoped to one operating point, because the sentences that consume this speak
    about the representative load and would otherwise silently acquire rows
    measured in overload, where the same metric name means a different thing.
    """
    sel = [r for r in results
           if r["excl_zero"] and (kind is None or r["kind"] == kind)
           and (point is None or r.get("point", "repr") == point)]
    if not sel:
        return "none"
    # Collect the metrics that share an allocator set, so the phrase reads as
    # prose ("p99 and p99.9 latency under jemalloc") rather than as a list of
    # table coordinates repeating the same qualifier.
    by_metric = {}
    for r in sel:
        by_metric.setdefault(_plain(r["metric"]), []).append(r["alloc"])
    by_allocs = {}
    for metric, allocs in by_metric.items():
        by_allocs.setdefault(tuple(sorted(allocs)), []).append(metric)

    def join(items):
        if len(items) == 1:
            return items[0]
        return ", ".join(items[:-1]) + " and " + items[-1]

    parts = []
    for allocs, metrics in by_allocs.items():
        # "p99 latency" and "p99.9 latency" collapse to "p99 and p99.9 latency".
        words = [m.split(" ") for m in metrics]
        if len(metrics) > 1 and len({w[-1] for w in words}) == 1:
            tail_word = words[0][-1]
            heads = [" ".join(w[:-1]) for w in words]
            subject = f"{join(heads)} {tail_word}"
        else:
            subject = join(metrics)
        where = "both allocators" if len(allocs) > 1 else allocs[0]
        parts.append(f"{subject} under {where}")
    return join(parts)


def cross_allocator_agreement(results):
    """Split the tested metrics by whether their effect keeps its sign across allocators.

    The allocator control was introduced to stop an allocator difference being
    read as a language difference, but it also supplies a replication check the
    design gets for free. A genuine language effect should appear with the same
    sign whichever allocator is linked, because the allocator is not what is
    being varied. An effect that reverses between the two is telling us about the
    run rather than about the language, however small its p-value happens to be
    on one side. Applied here this is what separates the peak-RSS result, which
    holds, from results that do not.

    Returns (consistent, reversed), each a list of plain metric names.
    """
    by_metric = defaultdict(dict)
    for r in results:
        if r.get("point", "repr") != "repr":
            continue
        by_metric[_plain(r["metric"])][r["alloc"]] = r["diff"]
    consistent, reversed_ = [], []
    for metric, effects in by_metric.items():
        if len(effects) < 2:
            continue
        signs = {(v > 0) - (v < 0) for v in effects.values()}
        (consistent if len(signs) == 1 else reversed_).append(metric)
    return consistent, reversed_


def write_significance_table(results, outdir):
    """Emit the body of tab:significance, split by how the statistic behaves.

    The rows are grouped rather than listed flat, because the grouping is the
    argument. An interval that excludes zero means one thing for a statistic a
    few descheduled operations cannot move, and something much weaker for one
    those operations define. Blocking the table by that distinction states the
    reading rule in the table itself, so it cannot be applied to some rows and
    quietly dropped for others.
    """
    if not results:
        return None

    def signed(value, decimals):
        # A value that rounds to zero prints as a bare 0, never as "-0.00":
        # a sign on a quantity the measurement resolves as zero reads as a
        # direction the data does not actually support.
        if abs(round(value, decimals)) < 10 ** -decimals / 2:
            return f"{0:.{decimals}f}"
        return f"{value:+.{decimals}f}"

    def row(r):
        d = r["decimals"]
        cell = (f"\\mci{{{signed(r['diff'], d)}}}"
                f"{{{signed(r['lo'], d)}}}{{{signed(r['hi'], d)}}}")
        return (f"{r['metric']} & {r['alloc']} & {cell} & "
                f"{fmt_p(r['p'])} & {fmt_p(r['holm'])}")

    results = [r for r in results if r.get("point", "repr") == "repr"]
    if not results:
        return None

    blocks = [
        ("robust", "Robust to interference on single operations"),
        ("tail", "Determined by it: high percentiles"),
    ]
    # The block heading is set in an \rlap rather than a \multicolumn. A
    # \multicolumn has to be the first token of its cell so that it can \omit the
    # column template, and it cannot be when the row arrives through \input: the
    # cell has already begun by the time the file is read, and LaTeX rejects it
    # with "Misplaced \omit". An \rlap contributes zero width, so the heading
    # overhangs the remaining columns without widening the first one.
    lines = []
    for kind, heading in blocks:
        sel = [r for r in results if r["kind"] == kind]
        if not sel:
            continue
        if lines:
            lines.append("\\hline")
        lines.append(f"\\rlap{{\\emph{{{heading}}}}} & & & &")
        lines.extend(row(r) for r in sel)

    out = os.path.join(outdir, "tab_significance.tex")
    with open(out, "w") as f:
        # A \hline placed as its own "row" must not be preceded by \\ or LaTeX
        # sees a misplaced \noalign, so the separator is folded into the join.
        body = ""
        for i, line in enumerate(lines):
            if line == "\\hline":
                body += "\\\\\n\\hline\n"
                continue
            if i and lines[i - 1] != "\\hline":
                body += " \\\\\n"
            body += line
        f.write(body + "\n")
    return out


def write_equivalence_table(results, outdir):
    """Emit the body of tab:equivalence: the tightest bound each comparison supports.

    Kept as its own table rather than a column bolted onto tab:significance,
    because it answers the opposite question and mixing the two invites the
    reader to treat a small p and a tight bound as the same kind of evidence.
    tab:significance asks whether a difference is there; this asks how large it
    could be if it is. A row can be interesting in one and dull in the other:
    a null with a tight bound is a real result, and a null with a wide one is
    the campaign saying it could not see.
    """
    results = [r for r in results if r.get("point", "repr") == "repr"]
    if not results:
        return None

    def row(r):
        d = r["decimals"]
        verdict = "significant" if r["holm"] < 0.05 else "not resolved"
        return (f"{r['metric']} & {r['alloc']} & {abs(r['diff']):.{d}f} & "
                f"{r['eqv']:.{d}f} & {verdict}")

    out = os.path.join(outdir, "tab_equivalence.tex")
    with open(out, "w") as f:
        f.write(" \\\\\n".join(row(r) for r in results) + "\n")
    return out


def write_overload_table(rows, results, outdir, overload):
    """Emit the body of tab:overload: what each variant still sustains past saturation.

    Reports the per-variant medians beside the paired comparison, because the
    absolute figures are the finding a practitioner would act on and the paired
    test is what establishes that the gap between them is not run-to-run noise.
    """
    sel = [r for r in results if r.get("point") == "overload"]
    if not sel or overload is None:
        return None

    thr = lambda r: r["throughput_ops_s"] / 1000.0
    lines = []
    for key in variants_present(rows):
        sub = _subset(rows, key, overload)
        if not sub:
            continue
        lines.append(f"{VARIANT_STYLE[key][0]} & {med_ci_cell([thr(r) for r in sub], decimals=1)}"
                     f" & {med_ci_cell([r['cpu_pct'] for r in sub])}")

    out = os.path.join(outdir, "tab_overload.tex")
    with open(out, "w") as f:
        f.write(" \\\\\n".join(lines) + "\n")

    # The paired comparison goes in its own file so the two can be typeset as
    # separate tables: one is per-variant state, the other is a test.
    trows = []
    for r in sel:
        d = r["decimals"]
        cell = (f"\\mci{{{r['diff']:+.{d}f}}}{{{r['lo']:+.{d}f}}}{{{r['hi']:+.{d}f}}}")
        trows.append(f"{r['metric']} & {r['alloc']} & {cell} & "
                     f"{r['agree']}/{r['n']} & {fmt_p(r['p'])} & {fmt_p(r['holm'])}")
    out2 = os.path.join(outdir, "tab_overload_test.tex")
    with open(out2, "w") as f:
        f.write(" \\\\\n".join(trows) + "\n")
    return out, out2


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
    ap.add_argument(
        "--probe-after",
        default=None,
        help="Clock B JSONL with coordinated-omission fill deferred until after "
             "the timed run; newest fair-after log if omitted.",
    )
    ap.add_argument("--sweep", default=None)
    ap.add_argument("--taxonomy", default="../faults/results/taxonomy.csv")
    ap.add_argument("--ffi", default="../ffi/results/metrics.json")
    ap.add_argument("--budget", default="results/latency_budget.json")
    ap.add_argument("--contention", default="results/queue_contention.json")
    ap.add_argument("--outdir", default="../figures")
    ap.add_argument("--load", type=float, default=None,
                    help="Representative offered load (ops/s); auto if omitted.")
    ap.add_argument("--overload", type=float, default=None,
                    help="Offered load (ops/s) for the past-saturation comparison; "
                         "auto (deepest saturated load) if omitted.")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    outdir = os.path.abspath(os.path.join(here, args.outdir)) if not os.path.isabs(args.outdir) else args.outdir
    os.makedirs(outdir, exist_ok=True)

    campaign = args.campaign
    if campaign is None:
        cands = sorted(glob.glob(os.path.join(here, "results", "campaign-*.jsonl")))
        campaign = cands[-1] if cands else os.path.join(here, "results", "latest.jsonl")
    rows = balance_repeats(load_campaign(campaign))
    probe_after = args.probe_after
    if probe_after is None:
        probe_cands = sorted(
            p for p in glob.glob(os.path.join(here, "results", "fair-after-*.jsonl"))
            if ".hist." not in p
        )
        probe_after = probe_cands[-1] if probe_cands else None
    deferred_rows = (
        balance_repeats(load_campaign(probe_after)) if probe_after else []
    )

    load = args.load if args.load is not None else pick_representative_load(rows)
    overload = args.overload if args.overload is not None else pick_overload_load(rows)
    print(f"campaign: {campaign}  rows={len(rows)}  representative load={load:.0f} ops/s")
    if overload is None:
        print("note: no swept load is past saturation, so the overload comparison is "
              "skipped. Extend the rate ladder: RQ1's overload question needs a load "
              "at which the service stops meeting the offered rate.")
    else:
        print(f"overload operating point: {overload:.0f} ops/s")
    if probe_after:
        print(f"deferred-fill probe: {probe_after}  rows={len(deferred_rows)}")
    else:
        print("note: no fair-after probe found; overload instrument comparison skipped")

    produced = []
    produced.append(fig_latency_vs_load(rows, outdir))
    produced.append(fig_throughput_vs_load(rows, outdir))
    produced.append(fig_load_sweep(rows, outdir))
    produced.append(fig_tail_percentiles(rows, outdir, load))
    produced.append(fig_resources(rows, outdir, load))
    taxonomy_csv = (args.taxonomy if os.path.isabs(args.taxonomy)
                    else os.path.abspath(os.path.join(here, args.taxonomy)))
    tax = fig_taxonomy(taxonomy_csv, outdir)
    if tax:
        produced.append(tax)
    tax_tab = write_taxonomy_table(taxonomy_csv, outdir)
    if tax_tab:
        produced.append(tax_tab)

    ffi_json = os.path.abspath(os.path.join(here, args.ffi)) if not os.path.isabs(args.ffi) else args.ffi
    ffi_fig = fig_ffi(ffi_json, outdir)
    if ffi_fig:
        produced.append(ffi_fig)
    ffi_tab = write_ffi_table(ffi_json, outdir)
    if ffi_tab:
        produced.append(ffi_tab)
    ffi_metrics = json.load(open(ffi_json)) if os.path.exists(ffi_json) else None

    budget_path = args.budget if os.path.isabs(args.budget) else os.path.join(here, args.budget)
    budget = load_budget(budget_path)
    budget_tab = write_budget_table(budget, outdir)
    if budget_tab:
        produced.append(budget_tab)
    else:
        print(f"note: no latency-budget data at {budget_path}; "
              f"run bench/latency_budget.sh (tab_budget.tex left as is)")

    contention_path = (args.contention if os.path.isabs(args.contention)
                       else os.path.join(here, args.contention))
    contention = load_contention(contention_path)
    contention_tab = write_contention_table(contention, outdir)
    if contention_tab:
        produced.append(contention_tab)
    else:
        print(f"note: no queue-contention data at {contention_path}; "
              f"run bench/queue_contention.sh (tab_contention.tex left as is)")

    sig = significance_results(rows, load, overload)
    budget_fig = fig_budget(budget, sig, outdir)
    if budget_fig:
        produced.append(budget_fig)
    effects_fig = fig_effects(sig, outdir)
    if effects_fig:
        produced.append(effects_fig)
    overload_fig = fig_overload(rows, deferred_rows, outdir, overload)
    if overload_fig:
        produced.append(overload_fig)
    # tab:latency's far-tail column is pooled across repeats, so the pooled
    # sidecar is read once here and passed to both the table and the macros.
    pooled = pooled_far_tail(campaign, load)
    if pooled:
        print(f"far tail: pooled p99.99 read for {len(pooled)} variants, "
              f"{min(v['samples'] for v in pooled.values()):,} to "
              f"{max(v['samples'] for v in pooled.values()):,} operations per group")
    lat_tab = write_latency_table(rows, outdir, load, pooled)[0]
    res_tab = write_resource_table(rows, outdir, load)
    jitter_tab = write_jitter_table(rows, outdir, load)
    if jitter_tab:
        produced.append(jitter_tab)
    else:
        print("note: campaign has no inter-operation jitter data; run campaign.sh "
              "with --jitter (tab_jitter.tex not written)")
    macros = write_generated_macros(rows, outdir, load, sig, budget, ffi_metrics,
                                    overload, contention, campaign_path=campaign)
    produced.extend([lat_tab, res_tab, macros])
    over_tabs = write_overload_table(rows, sig, outdir, overload)
    if over_tabs:
        produced.extend(over_tabs)
    sig_tab = write_significance_table(sig, outdir)
    if sig_tab:
        produced.append(sig_tab)
        n_sig = sum(1 for r in sig if r["holm"] < 0.05)
        print(f"significance: {len(sig)} paired tests, {n_sig} significant after Holm")
    eqv_tab = write_equivalence_table(sig, outdir)
    if eqv_tab:
        produced.append(eqv_tab)

    for p in produced:
        print("wrote", os.path.relpath(p, here))


if __name__ == "__main__":
    main()
