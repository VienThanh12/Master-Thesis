#!/usr/bin/env python3
"""Generated macros for the bare-metal confirmation campaign.

The load sweep the thesis reports throughout was measured on a virtualised KVM
guest, and three questions could not be answered there: the far tail below
saturation, the mechanism behind the operation-level and peak-RSS results, and
whether either result is a property of that host. A separate campaign on a
dedicated bare-metal machine answers all three.

It is reported as a confirmation and not as a replacement, because it does not
share the main campaign's design: the shard and producer count differ, it sweeps
fewer load levels, and it runs fifteen repeats against twenty. Substituting it
for the canonical sweep would change a fairness control and a repeat count at the
same time as the host, which is three changes and one conclusion. Kept separate
it changes one thing, the machine, and asks whether the findings survive it.

Every value the prose quotes about that campaign is written here, for the same
reason plot_figures.py writes the main campaign's: a number typed into a sentence
cannot be re-derived, and this one describes a host the author no longer has.

Reads bench/results-baremetal/ and writes figures/gen_baremetal.tex.
"""

import glob
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(HERE, "results-baremetal")

sys.path.insert(0, HERE)
from plot_figures import holm_adjust, paired_permutation_test  # noqa: E402

NS_PER_US = 1000.0
KB_PER_MIB = 1024.0

#: The below-saturation sweep and the sweep through the knee are two runs on one
#: host on one day. They are kept apart because they answer different questions
#: and because merging two sessions into one curve would hide the seam.
BELOW = "campaign-20260826-102047"
OVERLOAD = "campaign-20260826-124950"


def load_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def by_variant(rows):
    out = {}
    for r in rows:
        out.setdefault((r["lang"], r["alloc"], r["rate"]), []).append(r)
    return out


def offered(row):
    return row["rate"] * row["producers"]


def fmt(value, digits=0):
    if digits == 0:
        return f"{value:.0f}"
    return f"{value:.{digits}f}"


# --------------------------------------------------------------------------- #
# Host, taken from the environment capture rather than retyped.
# --------------------------------------------------------------------------- #
def host_facts(macros):
    envs = sorted(glob.glob(os.path.join(RESULTS, "env-*.txt")))
    if not envs:
        return ["no environment capture in results-baremetal"]
    text = open(envs[-1], encoding="utf-8").read()

    def grab(pattern, default=None):
        m = re.search(pattern, text)
        return m.group(1).strip() if m else default

    model = grab(r"Model name:\s+(.+)")
    if model:
        # "AMD EPYC 7443P 24-Core Processor" reads better without the suffix,
        # which the core count row states anyway.
        macros["BmCpu"] = model.replace(" 24-Core Processor", "").strip()
    cores = grab(r"Core\(s\) per socket:\s+(\d+)")
    sockets = grab(r"Socket\(s\):\s+(\d+)")
    if cores and sockets:
        macros["BmCores"] = str(int(cores) * int(sockets))
        macros["BmSockets"] = sockets
    numa = grab(r"NUMA node\(s\):\s+(\d+)")
    if numa:
        macros["BmNumaNodes"] = numa
    macros["BmKernel"] = grab(r"Linux \S+ (\S+)", "unknown")
    macros["BmDistro"] = grab(r"distro:\s+(.+)", "unknown")
    macros["BmVirt"] = grab(r"virtualisation:\s+(\S+)", "unknown")
    macros["BmGovernor"] = grab(r"governors:\s+(\S+)", "unknown")
    macros["BmSmt"] = grab(r"smt/control:\s+(\S+)", "unknown")
    macros["BmPinned"] = grab(r"cpus allowed here:\s+(\S+)", "unknown")
    gpp = grab(r"(g\+\+ \(.*?\) [\d.]+)")
    if gpp:
        macros["BmGpp"] = re.sub(r"g\+\+ \(.*?\) ", "", gpp)
    rustc = grab(r"rustc (\d+\.\d+)")
    if rustc:
        macros["BmRustc"] = rustc
    return []


def steal_facts(macros):
    files = sorted(glob.glob(os.path.join(RESULTS, "steal-*.json")))
    if not files:
        return ["no steal probe in results-baremetal"]
    d = json.load(open(files[-1], encoding="utf-8"))
    macros["BmStealIntervals"] = str(d["intervals"])
    macros["BmStealWithSteal"] = str(d["intervals_with_steal"])
    macros["BmStealMs"] = fmt(d["steal_ms_total"], 1)
    macros["BmStealWindow"] = fmt(d["wall_seconds"])
    macros["BmStealCores"] = str(d["n_cpus"])
    return []


# --------------------------------------------------------------------------- #
# Instrument quality. This is the whole reason the trip was worth taking, so it
# is measured rather than asserted: the dispersion of a variant's own p99 across
# repeats, on each host, over the loads the two campaigns share.
# --------------------------------------------------------------------------- #
def dispersion(rows, only_loads=None):
    out = []
    for (_lang, _alloc, _rate), runs in by_variant(rows).items():
        if only_loads is not None and offered(runs[0]) not in only_loads:
            continue
        vals = [r["lat_ns"]["p99"] for r in runs]
        mean = statistics.mean(vals)
        if mean:
            out.append(statistics.pstdev(vals) / mean)
    return out


def instrument_facts(macros, below):
    """The obstacle the main campaign reports, measured again on this host.

    Section 6.4 states the blocker in a specific form: the 95% interval on one
    variant's own p99 is several times the spread across all four, so no
    ordering can be read off. Those two quantities are computed here the same
    way, which makes the comparison one of like with like even though the two
    campaigns do not share a rate grid and so cannot be compared point by point.

    The highest load is excluded for the reason far_tail_facts gives.
    """
    from plot_figures import bootstrap_ci

    top = max(offered(r) for r in below)
    scoped = [r for r in below if offered(r) < top]

    cv = dispersion(scoped)
    macros["BmPNineNineCvMed"] = fmt(statistics.median(cv) * 100, 1)
    macros["BmPNineNineCvMax"] = fmt(max(cv) * 100, 1)

    widths, ranges = [], []
    for load in sorted({offered(r) for r in scoped}):
        at_load = {}
        for r in scoped:
            if offered(r) == load:
                at_load.setdefault((r["lang"], r["alloc"]), []).append(
                    r["lat_ns"]["p99"] / NS_PER_US)
        meds = []
        for vals in at_load.values():
            med, lo, hi = bootstrap_ci(vals)
            meds.append(med)
            widths.append(hi - lo)
        ranges.append(max(meds) - min(meds))
    macros["BmPNineNineMaxCI"] = fmt(max(widths), 1)
    macros["BmPNineNineRange"] = fmt(max(ranges), 1)
    return []


# --------------------------------------------------------------------------- #
# The far tail, pooled. A single run's p99.99 rests on too few observations to
# read; pooling the repeats is what makes the percentile a measurement.
# --------------------------------------------------------------------------- #
def far_tail_facts(macros):
    import csv
    path = os.path.join(RESULTS, f"{BELOW}.hist.pooled.csv")
    if not os.path.exists(path):
        return ["no pooled histogram; run bench/pool_hist.py"]
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    samples = [int(r["samples"]) for r in rows]
    macros["BmPoolSamplesMin"] = f"{min(samples):,}".replace(",", "\\,")
    macros["BmPoolSamplesMax"] = f"{max(samples):,}".replace(",", "\\,")

    # Quoted over the loads where the languages separate and the sweep is
    # regular. Two exclusions, both stated in the prose that quotes this.
    # Below 32 kops/s the two are indistinguishable, so averaging the flat
    # region in would understate a difference that is real above it. The
    # highest load is held out because its pooled median falls while every
    # percentile above it stays flat, a shape this campaign does not explain.
    loads = sorted({int(r["offered_ops_s"]) for r in rows})
    top = max(loads)
    macros["BmFarTailTopLoad"] = fmt(top / 1000)
    sep = [r for r in rows
           if 32000 <= int(r["offered_ops_s"]) < top]
    cpp = [int(r["p9999_ns"]) / NS_PER_US for r in sep if r["lang"] == "cpp"]
    rust = [int(r["p9999_ns"]) / NS_PER_US for r in sep if r["lang"] == "rust"]
    if cpp and rust:
        macros["BmFarTailCppLo"] = fmt(min(cpp))
        macros["BmFarTailCppHi"] = fmt(max(cpp))
        macros["BmFarTailRustLo"] = fmt(min(rust))
        macros["BmFarTailRustHi"] = fmt(max(rust))
        macros["BmFarTailSepLoad"] = "32"
        macros["BmFarTailSepHi"] = fmt(max(
            ld for ld in loads if ld < top) / 1000)
    return []


# --------------------------------------------------------------------------- #
# Paired language contrasts, by the same test and correction the main campaign
# uses, so the two are read on one scale.
# --------------------------------------------------------------------------- #
def paired_facts(macros, below):
    grouped = {}
    for r in below:
        key = (r["alloc"], r["rate"])
        grouped.setdefault(key, {}).setdefault(r["lang"], []).append(r)

    def contrast(extract):
        raw = []
        for key in sorted(grouped):
            d = grouped[key]
            if "cpp" not in d or "rust" not in d:
                continue
            a = [extract(x) for x in d["cpp"]]
            b = [extract(x) for x in d["rust"]]
            if any(v is None for v in a + b):
                continue
            md, p, _n = paired_permutation_test(a, b)
            raw.append((md, p))
        adj = holm_adjust([p for _md, p in raw])
        return raw, adj

    raw, adj = contrast(lambda r: r["lat_ns"]["p50"])
    sig = [md for (md, _p), pa in zip(raw, adj) if pa < 0.05]
    macros["BmPFiftyTested"] = str(len(raw))
    macros["BmPFiftySig"] = str(len(sig))
    if sig:
        macros["BmPFiftyDiffLo"] = fmt(min(abs(m) for m in sig) / NS_PER_US, 1)
        macros["BmPFiftyDiffHi"] = fmt(max(abs(m) for m in sig) / NS_PER_US, 1)
        macros["BmPFiftyFaster"] = "Rust" if statistics.median(sig) < 0 else "C++"

    # The median's own magnitude, so the prose can say what a difference of a
    # microsecond is a difference *in* without typing the scale. Rounded to the
    # nearest microsecond, and taken over the whole sweep because it is flat
    # below saturation.
    macros["BmPFiftyMedian"] = fmt(
        statistics.median([r["lat_ns"]["p50"] for r in below]) / NS_PER_US)

    raw, adj = contrast(lambda r: r["rss_peak_kb"])
    sig = [md for (md, _p), pa in zip(raw, adj) if pa < 0.05]
    macros["BmRssTested"] = str(len(raw))
    macros["BmRssSig"] = str(len(sig))

    # CPU utilisation. On the guest this comparison cleared Holm under one
    # allocator and reversed under the other, so Section 6.4.3 reports it
    # unresolved. On a quiet host it resolves: whether it resolves with one sign
    # is the thing worth recording, so the sign agreement is counted rather than
    # asserted and the direction is read from the data.
    raw, adj = contrast(lambda r: r["cpu_pct"])
    sig = [md for (md, _p), pa in zip(raw, adj) if pa < 0.05]
    macros["BmCpuTested"] = str(len(raw))
    macros["BmCpuSig"] = str(len(sig))
    if sig:
        macros["BmCpuDiffLo"] = fmt(min(abs(m) for m in sig), 1)
        macros["BmCpuDiffHi"] = fmt(max(abs(m) for m in sig), 1)
        macros["BmCpuLower"] = "Rust" if statistics.median(sig) < 0 else "C++"
        one_sign = all(m < 0 for m in sig) or all(m > 0 for m in sig)
        macros["BmCpuOneSign"] = "yes" if one_sign else "no"

    # Language and allocator effects at steady state. Below 32 kops/s the
    # footprint is still filling, so the early loads describe warm-up.
    steady = [r for r in below if offered(r) >= 32000]
    cell = {}
    for r in steady:
        cell.setdefault((r["lang"], r["alloc"], r["rate"]), []).append(
            r["rss_peak_kb"])
    rates = sorted({r["rate"] for r in steady})

    def med(lang, alloc, rate):
        return statistics.median(cell[(lang, alloc, rate)]) / KB_PER_MIB

    lang_eff, alloc_eff = [], []
    for rate in rates:
        for alloc in ("system", "jemalloc"):
            lang_eff.append(med("rust", alloc, rate) - med("cpp", alloc, rate))
        for lang in ("cpp", "rust"):
            alloc_eff.append(med(lang, "jemalloc", rate) - med(lang, "system", rate))
    macros["BmRssLangLo"] = fmt(min(lang_eff), 1)
    macros["BmRssLangHi"] = fmt(max(lang_eff), 1)
    macros["BmRssAllocLo"] = fmt(min(alloc_eff), 1)
    macros["BmRssAllocHi"] = fmt(max(alloc_eff), 1)
    macros["BmRssLargerEffect"] = (
        "allocator" if statistics.median(alloc_eff) > statistics.median(lang_eff)
        else "language")
    return []


# --------------------------------------------------------------------------- #
# Saturation and overload. The knee is bracketed rather than pinned, because the
# sweep steps over it, and the point between the last served load and the first
# collapsed one is metastable: reporting a median there would average a
# distribution with a mode at each end.
# --------------------------------------------------------------------------- #
def overload_facts(macros):
    path = os.path.join(RESULTS, f"{OVERLOAD}.jsonl")
    if not os.path.exists(path):
        return ["no overload campaign in results-baremetal"]
    rows = load_jsonl(path)
    grouped = by_variant(rows)
    loads = sorted({offered(r) for r in rows})

    def served(load):
        return all(
            statistics.median([x["throughput_ops_s"] for x in runs]) / load > 0.99
            for (lang, alloc, rate), runs in grouped.items()
            if rate * runs[0]["producers"] == load)

    tracking = [ld for ld in loads if served(ld)]
    collapsed = [ld for ld in loads if not served(ld)]
    if tracking:
        macros["BmTrackingMax"] = fmt(max(tracking) / 1000)
    if collapsed:
        macros["BmKneeLo"] = fmt(max(tracking) / 1000) if tracking else "0"
        macros["BmKneeHi"] = fmt(min(collapsed) / 1000)

    # Deep overload is the load where every arm has stopped tracking and each
    # one's own repeats agree. That second condition is what the first collapsed
    # load fails.
    def spread(load):
        out = []
        for (lang, alloc, rate), runs in grouped.items():
            if rate * runs[0]["producers"] != load:
                continue
            vals = [x["throughput_ops_s"] for x in runs]
            out.append(statistics.pstdev(vals) / statistics.mean(vals))
        return max(out)

    stable = [ld for ld in collapsed if spread(ld) < 0.05]
    if not stable:
        return ["no stable overload point; every collapsed load is metastable"]
    deep = max(stable)
    macros["BmOverloadLoad"] = fmt(deep / 1000)
    macros["BmOverloadCv"] = fmt(spread(deep) * 100, 1)

    metastable = [ld for ld in collapsed if spread(ld) >= 0.05]
    if metastable:
        macros["BmMetastableLoad"] = fmt(min(metastable) / 1000)
        macros["BmMetastableCv"] = fmt(spread(min(metastable)) * 100)

    def thr(lang, alloc):
        rate = deep / rows[0]["producers"]
        return statistics.median(
            [x["throughput_ops_s"] for x in grouped[(lang, alloc, rate)]]) / 1000

    cpp = statistics.median([thr("cpp", a) for a in ("system", "jemalloc")])
    rust = statistics.median([thr("rust", a) for a in ("system", "jemalloc")])
    macros["BmOverloadThrCpp"] = fmt(cpp)
    macros["BmOverloadThrRust"] = fmt(rust)
    macros["BmOverloadThrRatio"] = fmt(cpp / rust, 2)
    macros["BmOverloadFaster"] = "C++" if cpp > rust else "Rust"
    return []


# --------------------------------------------------------------------------- #
# Hardware counters. The operation scope is the one that speaks to the language,
# because the end-to-end path is almost entirely cross-thread handoff.
# --------------------------------------------------------------------------- #
def counter_facts(macros):
    files = sorted(glob.glob(os.path.join(RESULTS, "counters-*.jsonl")))
    if not files:
        return ["no counters in results-baremetal"]
    rows = load_jsonl(files[-1])
    grouped = {}
    for r in rows:
        grouped.setdefault((r["scope"], r["lang"], r["alloc"]), []).append(r)

    scope, alloc = "op", "system"
    if (scope, "cpp", alloc) not in grouped:
        return ["counters carry no op scope"]
    macros["BmCounterRepeats"] = str(len(grouped[(scope, "cpp", alloc)]))

    def series(lang, field, event=None):
        runs = sorted(grouped[(scope, lang, alloc)], key=lambda r: r["repeat"])
        if event:
            return [r["events"][event]["value"] for r in runs]
        return [r[field] for r in runs]

    def ratio(name, macro, event=None, field=None):
        a, b = series("cpp", field, event), series("rust", field, event)
        if any(v is None for v in a + b):
            return
        _md, p, _n = paired_permutation_test(a, b)
        ma, mb = statistics.median(a), statistics.median(b)
        macros[macro] = fmt(abs(1 - mb / ma) * 100)
        macros[macro + "P"] = f"{p:.4f}".rstrip("0")
        macros[macro + "Dir"] = "fewer" if mb < ma else "more"

    ratio("instructions", "BmInstrDelta", event="instructions")
    ratio("cycles", "BmCycleDelta", event="cycles")
    ratio("misses", "BmMissDelta", field="cache_misses_per_kinstr")
    return []


def main():
    macros, notes = {}, []
    below_path = os.path.join(RESULTS, f"{BELOW}.jsonl")
    if not os.path.exists(below_path):
        sys.exit(f"missing {below_path}; nothing to generate")
    below = load_jsonl(below_path)

    # The binary does not echo its run id, so the repeat count is recovered from
    # the design rather than read off a field that is not there.
    levels = len({r["rate"] for r in below})
    variants = len({(r["lang"], r["alloc"]) for r in below})
    macros["BmRepeats"] = str(len(below) // (levels * variants))
    macros["BmRuns"] = str(len(below))
    macros["BmLoadLevels"] = str(levels)
    macros["BmShards"] = str(below[0]["shards"])
    macros["BmProducers"] = str(below[0]["producers"])
    macros["BmLoadLo"] = fmt(min(offered(r) for r in below) / 1000)
    macros["BmLoadHi"] = fmt(max(offered(r) for r in below) / 1000)

    notes += host_facts(macros)
    notes += steal_facts(macros)
    notes += instrument_facts(macros, below)
    notes += far_tail_facts(macros)
    notes += paired_facts(macros, below)
    notes += overload_facts(macros)
    notes += counter_facts(macros)

    out = os.path.join(ROOT, "figures", "gen_baremetal.tex")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("% Generated by bench/baremetal_facts.py -- do not edit by hand.\n")
        for k in sorted(macros):
            fh.write(f"\\newcommand{{\\{k}}}{{{macros[k]}}}\n")

    print(f"wrote {os.path.relpath(out, ROOT)} ({len(macros)} macros)")
    for k in sorted(macros):
        print(f"  {k} = {macros[k]}")
    for note in notes:
        print("  SKIP:", note, file=sys.stderr)


if __name__ == "__main__":
    main()
