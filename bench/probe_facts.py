#!/usr/bin/env python3
"""Generated macros for the two fair-clock probe sweeps.

The reported campaign measures latency from the intended send time and applies
Gil Tene's coordinated-omission correction at the moment each sample is
recorded. Past saturation that correction writes up to 10 000 synthetic samples
per completed call, on the producer thread, inside the timed window. Two sweeps
ask what the same service does when that work is moved.

Clock A (--latency-origin start --correction-cap 0) times the call from the
actual send and writes no synthetic samples. It tests whether the high-load
throughput split persists without fill. It is NOT a better latency instrument:
dropping the correction reintroduces exactly the coordinated-omission bias the
thesis cites Tene for, so its percentiles must never be quoted as the study's
tail result.

Clock B (--correction-when after) keeps the intended origin and the 10 000
sample cap, and only defers the fill until the timed window has closed. Its
statistics are the corrected ones. Its collapsed p50 is schedule drift by
construction and is not service time.

Both are reported as diagnostics and not as replacements. The original
campaign remains the pre-committed compared pair. The later clocks were
designed after the campaign to diagnose its high-load recorder path, so they
change the interpretation of the overload gaps without replacing the tested
family.

Every value the prose quotes about these sweeps is written here, because a
number typed into a sentence cannot be re-derived.

Reads bench/results/fair-start-*.jsonl and fair-after-*.jsonl and writes
figures/gen_probes.tex.
"""

import glob
import json
import os
import re
import statistics
import sys

from plot_figures import paired_permutation_test

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS = os.path.join(HERE, "results")
OUT = os.path.join(ROOT, "figures", "gen_probes.tex")

NS_PER_US = 1000.0
OPS_PER_KOP = 1000.0
ALLOCS = ("system", "jemalloc")
LANGS = ("cpp", "rust")

# The campaign grid these sweeps repeat. Offered load is per-producer rate
# times the producer count, so it is read from the runs rather than assumed.
TRACK_TOLERANCE = 0.95


def knee_load():
    """The campaign's \\KneeGapLoad, in ops/s, or None when it was not emitted.

    Read from the generated macros rather than repeated here, because the
    knee comparison is only meaningful if both datasets are quoted at the
    same rung. If the campaign is ever re-derived and the knee moves, this
    follows it instead of silently comparing two different loads. A campaign
    whose two languages share a tracking limit does not emit the macro, and
    that absence is the signal: there is no language rung to compare.
    """
    path = os.path.join(ROOT, "figures", "gen_macros.tex")
    text = open(path).read()
    # A shared language knee when the two tracking limits differ. Otherwise the
    # allocator split, which is the disagreement this campaign actually emits.
    # plot_figures.py runs first, so the macro read here is the one just written.
    gap = re.search(r"\\newcommand\{\\KneeGapLoad\}\{(\d+)\}", text)
    split = re.search(r"\\newcommand\{\\KneeSplitLoad\}\{(\d+)\}", text)
    chosen = gap or split
    if not chosen:
        return None
    return int(chosen.group(1)) * int(OPS_PER_KOP)


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    if not n:
        raise ValueError("median of empty sequence")
    return xs[n // 2] if n % 2 else 0.5 * (xs[n // 2 - 1] + xs[n // 2])


def newest(pattern):
    """Newest run log for a prefix. The .hist. sidecars share the glob."""
    hits = sorted(
        p for p in glob.glob(os.path.join(RESULTS, pattern)) if ".hist." not in p
    )
    if not hits:
        raise SystemExit(f"probe_facts: no log matching {pattern} in {RESULTS}")
    return hits[-1]


def matching_env(log_path):
    """The capture written for this run, matched by timestamp.

    Taking the newest capture would silently repoint the host description when
    a later sweep lands, which is the defect AGENT.md records against reading
    a raw capture through ENV. The capture is written just before the log, so
    the match is the latest stamp at or below the log's own.
    """
    stamp = os.path.basename(log_path).rsplit("-", 2)[-2:]
    stamp = "-".join(stamp).replace(".jsonl", "")
    best = None
    for env in sorted(glob.glob(os.path.join(RESULTS, "env-*.txt"))):
        env_stamp = os.path.basename(env)[len("env-") : -len(".txt")]
        if env_stamp <= stamp:
            best = env
    if best is None:
        raise SystemExit(f"probe_facts: no env capture at or before {stamp}")
    return best


def host_facts(env_path, prefix, macros):
    """Host description taken from the capture rather than retyped."""
    text = open(env_path, encoding="utf-8").read()

    def grab(pattern, default="unknown"):
        m = re.search(pattern, text)
        return m.group(1).strip() if m else default

    model = grab(r"Model name:\s+(.+)")
    macros[f"{prefix}Cpu"] = model.replace(" 24-Core Processor", "").strip()
    macros[f"{prefix}Kernel"] = grab(r"Linux \S+ (\S+)").replace("_", r"\_")
    macros[f"{prefix}Smt"] = grab(r"smt/control:\s+(\S+)")
    pinned = grab(r"cpus allowed here:\s+(\S+)")
    macros[f"{prefix}Pinned"] = re.sub(r"(\d)-(\d)", r"\1--\2", pinned)
    # The two isolation settings the reported host carries and this one may
    # not. The capture writes "(none)" for an absent kernel command line
    # setting, which reads better in prose as "none".
    for field, key in (("isolcpus", "Isolcpus"), ("nohz_full", "NohzFull")):
        val = grab(rf"{field}:\s+(.+)")
        macros[f"{prefix}{key}"] = "none" if val == "(none)" else val
    macros[f"{prefix}Env"] = os.path.basename(env_path).replace("_", r"\_")


def load(path):
    rows = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    if not rows:
        raise SystemExit(f"probe_facts: {path} is empty")
    return rows


def cells(rows):
    """Group runs by (lang, alloc, offered ops/s)."""
    out = {}
    for r in rows:
        key = (r["lang"], r["alloc"], int(r["rate"] * r["producers"]))
        out.setdefault(key, []).append(r)
    return out


def by_lang(cell, lang, load_ops, field):
    """Median over allocators of the per-allocator median over repeats."""
    per_alloc = []
    for alloc in ALLOCS:
        runs = cell.get((lang, alloc, load_ops))
        if runs:
            per_alloc.append(median([field(r) for r in runs]))
    if not per_alloc:
        raise SystemExit(f"probe_facts: no runs for {lang} at {load_ops}")
    return median(per_alloc)


def thr_kops(r):
    return r["throughput_ops_s"] / OPS_PER_KOP


def p99_us(r):
    return r["lat_ns"]["p99"] / NS_PER_US


def worst_spread_pct(cell):
    worst = 0.0
    for runs in cell.values():
        vals = [r["throughput_ops_s"] for r in runs]
        if len(vals) > 1 and statistics.mean(vals):
            cv = statistics.pstdev(vals) / statistics.mean(vals) * 100.0
            worst = max(worst, cv)
    return worst


def tracking_load(cell, lang, loads):
    """Highest offered load where both allocators still finish ~the rate."""
    held = []
    for L in loads:
        ok = True
        for alloc in ALLOCS:
            runs = cell.get((lang, alloc, L))
            if not runs:
                continue
            if median([r["throughput_ops_s"] for r in runs]) < TRACK_TOLERANCE * L:
                ok = False
        if ok:
            held.append(L)
    return max(held) if held else None


def fmt_p(p):
    if p < 1e-3:
        return "<0.001"
    return f"{p:.3f}"


def summarise(rows, prefix, macros, percentiles):
    """Write the macros for one clock.

    percentiles is False for Clock B on purpose. That clock keeps the intended
    send time as the origin, so past saturation its percentiles are schedule
    drift measured in seconds, not service time. Emitting them as PNineNine
    macros would invite a sentence that reads a drift figure as a tail latency,
    which is the one defect no build gate catches.
    """
    cell = cells(rows)
    loads = sorted({k[2] for k in cell})
    overload = max(loads)
    sample = rows[0]

    macros[f"{prefix}Runs"] = str(len(rows))
    macros[f"{prefix}Repeats"] = str(max(len(v) for v in cell.values()))
    macros[f"{prefix}Loads"] = str(len(loads))
    macros[f"{prefix}Spread"] = f"{worst_spread_pct(cell):.1f}"

    for lang, tag in (("cpp", "Cpp"), ("rust", "Rust")):
        macros[f"{prefix}Thr{tag}"] = (
            f"{by_lang(cell, lang, overload, thr_kops):.0f}"
        )
        track = tracking_load(cell, lang, loads)
        macros[f"{prefix}Track{tag}"] = (
            f"{track / OPS_PER_KOP:.0f}" if track else "n/a"
        )
        if percentiles:
            macros[f"{prefix}PNineNine{tag}"] = (
                f"{by_lang(cell, lang, overload, p99_us):.1f}"
            )

    cpp_thr = by_lang(cell, "cpp", overload, thr_kops)
    rust_thr = by_lang(cell, "rust", overload, thr_kops)
    macros[f"{prefix}ThrRatio"] = f"{cpp_thr / rust_thr:.2f}"
    # CPU per completed operation, the same quantity as OverloadCpuPerOpRatio:
    # the per-allocator median of cpu_pct divided by the per-allocator median
    # throughput, then the median across allocators, then the ratio of the two
    # languages. Emitted for both clocks so the deferred-fill residual is read
    # from this log and not from another machine.
    per_op = {}
    for lang, tag in (("cpp", "Cpp"), ("rust", "Rust")):
        vals = []
        for alloc in ALLOCS:
            runs = cell.get((lang, alloc, overload))
            if not runs:
                continue
            thr = median([thr_kops(r) for r in runs])
            if thr <= 0:
                continue
            vals.append(median([r["cpu_pct"] for r in runs]) / thr)
        if vals:
            per_op[lang] = median(vals)
            macros[f"{prefix}CpuPerOp{tag}"] = f"{per_op[lang]:.2f}"
    if len(per_op) == 2 and min(per_op.values()) > 0:
        higher = max(per_op, key=per_op.get)
        macros[f"{prefix}CpuPerOpRatio"] = (
            f"{per_op[higher] / min(per_op.values()):.2f}"
        )
        macros[f"{prefix}CpuPerOpHigher"] = "C++" if higher == "cpp" else "Rust"

    if percentiles:
        # How many of the fourteen loads have the lower Rust p99.
        lower = sum(
            1
            for L in loads
            if by_lang(cell, "rust", L, p99_us) < by_lang(cell, "cpp", L, p99_us)
        )
        macros[f"{prefix}RustLowerLoads"] = str(lower)

    for alloc, tag in (("system", "System"), ("jemalloc", "Jemalloc")):
        cpp_runs = cell[("cpp", alloc, overload)]
        rust_runs = cell[("rust", alloc, overload)]
        cpp_values = [thr_kops(r) for r in cpp_runs]
        rust_values = [thr_kops(r) for r in rust_runs]
        _effect, p, n = paired_permutation_test(
            cpp_values,
            rust_values,
        )
        cpp_median = median(cpp_values)
        rust_median = median(rust_values)
        macros[f"{prefix}ThrCpp{tag}"] = f"{cpp_median:.0f}"
        macros[f"{prefix}ThrRust{tag}"] = f"{rust_median:.0f}"
        macros[f"{prefix}ThrRatio{tag}"] = f"{cpp_median / rust_median:.2f}"
        macros[f"{prefix}ThrFaster{tag}"] = (
            "C++" if cpp_median > rust_median else "Rust"
        )
        macros[f"{prefix}ThrP{tag}"] = fmt_p(p)
        macros[f"{prefix}Pairs{tag}"] = str(n)

    # The campaign's knee rung, where its asymmetry runs the other way: Rust
    # still serves the offered rate there and C++ has already fallen.
    knee = knee_load()
    if knee is not None and knee in loads:
        macros[f"{prefix}KneeLoad"] = f"{knee / OPS_PER_KOP:.0f}"
        for lang, tag in (("cpp", "Cpp"), ("rust", "Rust")):
            macros[f"{prefix}KneeThr{tag}"] = (
                f"{by_lang(cell, lang, knee, thr_kops):.0f}"
            )

    macros[f"{prefix}OverloadLoad"] = f"{overload / OPS_PER_KOP:.0f}"
    macros[f"{prefix}Origin"] = str(sample["latency_origin"])
    macros[f"{prefix}When"] = str(sample["correction_when"])
    # Thin-separated so the prose can quote it in math mode as the rest of
    # the document writes four-digit counts.
    macros[f"{prefix}Cap"] = f"{int(sample['correction_cap']):,}".replace(",", r"\,")


def main():
    macros = {}
    start = newest("fair-start-*.jsonl")
    after = newest("fair-after-*.jsonl")

    summarise(load(start), "ProbeStart", macros, percentiles=True)
    summarise(load(after), "ProbeAfter", macros, percentiles=False)

    host_facts(matching_env(start), "ProbeStart", macros)
    host_facts(matching_env(after), "ProbeAfter", macros)

    # Shared names exist only when the two captures agree. Clock A can be an
    # earlier host while Clock B is the campaign's own fill control, and a
    # single ProbeCpu would then describe the wrong machine for one of them.
    # A disagreement is reported. It is not a mismatched log.
    disagreed = [
        field for field in ("Cpu", "NohzFull", "Kernel", "Pinned")
        if macros[f"ProbeStart{field}"] != macros[f"ProbeAfter{field}"]
    ]
    if disagreed:
        print(
            "probe_facts: clocks differ in "
            + ", ".join(disagreed)
            + "; shared ProbeCpu and ProbeNohzFull omitted"
        )
    else:
        macros["ProbeCpu"] = macros["ProbeStartCpu"]
        macros["ProbeNohzFull"] = macros["ProbeStartNohzFull"]

    macros["ProbeStartLog"] = os.path.basename(start).replace("_", r"\_")
    macros["ProbeAfterLog"] = os.path.basename(after).replace("_", r"\_")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        fh.write("% Generated by bench/probe_facts.py -- do not edit by hand.\n")
        fh.write("% Clock A is the newest fair-start log and is not this campaign's host.\n")
        fh.write("% Clock B is the newest fair-after log. When it shares the campaign host,\n")
        fh.write("% it is the fill control. Clock B percentiles are not emitted.\n")
        for name in sorted(macros):
            fh.write(f"\\newcommand{{\\{name}}}{{{macros[name]}}}\n")
    print(f"wrote {OUT} ({len(macros)} macros)")
    print(f"  clock A: {os.path.basename(start)}")
    print(f"  clock B: {os.path.basename(after)}")


if __name__ == "__main__":
    sys.exit(main())
