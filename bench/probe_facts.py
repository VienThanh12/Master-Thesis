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

Clock B also leaves a smaller Rust lead where throughput has stopped rising.
Its kernel and user CPU per call say where that lead sits (the Sys* macros),
and two swap probes on a further host with the same processor test what
carries it (the Sg* macros). Those probes are diagnostics too, outside the
tested family.

Every value the prose quotes about these sweeps is written here, because a
number typed into a sentence cannot be re-derived.

Reads bench/results/fair-start-*.jsonl and fair-after-*.jsonl, and the probe
logs in bench/results-probes-20260930-sg/, and writes figures/gen_probes.tex.
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
# Swap probes from the 30 September 2026 host. Kept out of results/ so that
# refresh_thesis.sh can never take one of them for a campaign.
SG_DIR_LEGACY = os.path.join(HERE, "results-probes-20260930-sg")
SG_DIR_CAMPAIGN = os.path.join(HERE, "results-probes-campaign-jaybird")


def sg_dir():
    override = os.environ.get("THESIS_SG_DIR")
    if override:
        return override
    if os.path.isdir(SG_DIR_CAMPAIGN):
        import glob

        if glob.glob(os.path.join(SG_DIR_CAMPAIGN, "probe-sg-queue-nocount-*.jsonl")):
            return SG_DIR_CAMPAIGN
    return SG_DIR_LEGACY
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


def newest(pattern, directory=RESULTS):
    """Newest run log for a prefix. The .hist. sidecars share the glob."""
    hits = sorted(
        p for p in glob.glob(os.path.join(directory, pattern)) if ".hist." not in p
    )
    if not hits:
        raise SystemExit(f"probe_facts: no log matching {pattern} in {directory}")
    return hits[-1]


def matching_env(log_path, directory=RESULTS):
    """The capture written for this run, matched by timestamp.

    Taking the newest capture would silently repoint the host description when
    a later sweep lands, which is the defect AGENT.md records against reading
    a raw capture through ENV. The capture is written just before the log, so
    the match is the latest stamp at or below the log's own.
    """
    stamp = os.path.basename(log_path).rsplit("-", 2)[-2:]
    stamp = "-".join(stamp).replace(".jsonl", "")
    best = None
    for env in sorted(glob.glob(os.path.join(directory, "env-*.txt"))):
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


LANG_NAME = {"cpp": "C++", "rust": "Rust"}


def kernel_split(rows, prefix, macros):
    """Kernel CPU per completed call, the place the deferred-fill lead sits.

    Each sender waits for its reply, so past saturation throughput is set by
    the round-trip, and the round-trip is mostly the cross-thread handoff,
    whose cost the kernel carries. Same chain as CpuPerOp, with cpu_sys_s over
    wall_s in place of cpu_pct.

    The kernel share is per run and its denominator includes the deferred
    fill, which is user code, so it understates the handoff's share.
    """
    cell = cells(rows)
    loads = sorted({k[2] for k in cell})
    top = max(loads)

    def sys_per_op(lang, alloc, load_ops):
        runs = cell[(lang, alloc, load_ops)]
        rate = median([100.0 * r["cpu_sys_s"] / r["wall_s"] for r in runs])
        return rate / median([thr_kops(r) for r in runs])

    at_top = {
        lang: median([sys_per_op(lang, alloc, top) for alloc in ALLOCS])
        for lang in LANGS
    }
    higher = max(at_top, key=at_top.get)
    lower = min(at_top, key=at_top.get)
    macros[f"{prefix}SysHigher"] = LANG_NAME[higher]
    macros[f"{prefix}SysLower"] = LANG_NAME[lower]
    macros[f"{prefix}SysRatio"] = f"{at_top[higher] / at_top[lower]:.2f}"
    macros[f"{prefix}SysLowerLoads"] = str(sum(
        1
        for L in loads
        if all(sys_per_op(lower, a, L) < sys_per_op(higher, a, L) for a in ALLOCS)
    ))
    shares = [
        median([
            r["cpu_sys_s"] / (r["cpu_sys_s"] + r["cpu_user_s"])
            for r in cell[(lang, alloc, top)]
        ])
        for lang in LANGS
        for alloc in ALLOCS
    ]
    macros[f"{prefix}SysShareLo"] = f"{100.0 * min(shares):.0f}"
    macros[f"{prefix}SysShareHi"] = f"{100.0 * max(shares):.0f}"


def sg_facts(macros):
    """Two swap probes on a further host with the campaign's processor.

    Both run on the deferred-fill clock, interleaved against the stock builds
    in one session: an open-addressed C++ map, and the C++ queue design given
    to Rust, with a C++ ring buffer that keeps the lock as the control. The
    queue swap is read from the session without perf, because counting context
    switches slowed every arm by about a tenth and hid the lead. The counted
    session supplies only switches per call, at a load where the send schedule
    and not the counter sets the rate.
    """
    sg_root = sg_dir()
    flat_log = newest("probe-sg-flatmap-112000-*.jsonl", SG_DIR_LEGACY)
    queue_log = newest("probe-sg-queue-nocount-112000-*.jsonl", sg_root)
    count_log = newest("probe-sg-queue-8000-*.jsonl", SG_DIR_LEGACY)

    host_facts(matching_env(queue_log, sg_root), "Sg", macros)
    # That capture was taken on the host, outside the container, so it lists
    # every online CPU. The runs were pinned to 2-17 by the container.
    del macros["SgPinned"]

    def by_arm(rows):
        out = {}
        for r in rows:
            out.setdefault(r["arm"], {})[r["repeat"]] = r
        return out

    def paired(arms):
        reps = sorted(set.intersection(*(set(v) for v in arms.values())))
        thr = {a: [arms[a][k]["throughput_ops_s"] for k in reps] for a in arms}
        return reps, thr

    def load_kops(arms):
        r = next(iter(next(iter(arms.values())).values()))
        return f"{r['rate'] * r['producers'] / OPS_PER_KOP:.0f}"

    flat = by_arm(load(flat_log))
    reps, thr = paired(flat)
    macros["SgFlatLoad"] = load_kops(flat)
    macros["SgFlatPairs"] = str(len(reps))
    macros["SgFlatRustAhead"] = str(sum(
        r > c for r, c in zip(thr["rust-stock"], thr["cpp-stock"])))
    macros["SgFlatCppFaster"] = str(sum(
        f > c for f, c in zip(thr["cpp-flat"], thr["cpp-stock"])))

    queue = by_arm(load(queue_log))
    reps, thr = paired(queue)
    med = {a: median(v) for a, v in thr.items()}
    lead = med["rust-channel"] - med["cpp-deque"]
    closed = (med["rust-channel"] - med["rust-mutexq"]) / lead if lead > 0 else 0.0
    slower = sum(m < s for m, s in zip(thr["rust-mutexq"], thr["rust-channel"]))
    # Thesis_v5 says the C++ queue removed the lead and quotes no share. That
    # was the reading fixed before the run for a swap that closes all of the
    # lead in at least 8 of 10 pairs. A log that breaks it breaks the sentence.
    if closed < 1.0 or slower < 0.8 * len(reps):
        raise SystemExit(
            f"probe_facts: the queue swap closes {closed:.0%} of the lead, slower "
            f"in {slower} of {len(reps)} pairs. Thesis_v5 says it removed the lead."
        )
    def sys_us_per_call(arm):
        rs = list(queue[arm].values())
        rate = median([r["cpu_sys_s"] / r["wall_s"] for r in rs])
        return rate / median([r["throughput_ops_s"] for r in rs]) * 1e6

    sys_us = {a: sys_us_per_call(a) for a in queue}
    # Thesis_v5 also says the C++ queue adds kernel time to each handoff.
    if sys_us["rust-mutexq"] <= sys_us["rust-channel"]:
        raise SystemExit(
            "probe_facts: Rust with the C++ queue no longer spends more kernel "
            "time per call than stock Rust. Thesis_v5 says it does."
        )
    _effect, p, _n = paired_permutation_test(thr["rust-channel"], thr["rust-mutexq"])
    for arm, tag in (("cpp-deque", "Cpp"), ("rust-channel", "Rust"),
                     ("rust-mutexq", "RustMutex")):
        macros[f"SgQueueSys{tag}"] = f"{sys_us[arm]:.2f}"
    macros["SgQueueLoad"] = load_kops(queue)
    macros["SgQueuePairs"] = str(len(reps))
    macros["SgQueueRustAhead"] = str(sum(
        r > c for r, c in zip(thr["rust-channel"], thr["cpp-deque"])))
    macros["SgQueueMutexSlower"] = str(slower)
    macros["SgQueueClosedPct"] = f"{100.0 * closed:.0f}"
    macros["SgQueueMutexP"] = fmt_p(p)
    macros["SgQueueRingAbsPct"] = (
        f"{abs(med['cpp-ring'] - med['cpp-deque']) / med['cpp-deque'] * 100.0:.1f}"
    )

    counted = by_arm(load(count_log))
    per_call = {}
    for arm, runs in counted.items():
        rs = [r for r in runs.values() if r.get("ctx_switches") is not None]
        if not rs:
            raise SystemExit(f"probe_facts: {arm} has no context-switch counts")
        rate = median([r["ctx_switches"] / r["wall_s"] for r in rs])
        per_call[arm] = rate / median([r["throughput_ops_s"] for r in rs])
    shown = {f"{v:.1f}" for v in per_call.values()}
    # The prose gives one figure for all four builds, so they must agree.
    if len(shown) != 1:
        raise SystemExit(f"probe_facts: switches per call differ by arm: {per_call}")
    macros["SgSwitchLow"] = shown.pop()
    macros["SgSwitchLowLoad"] = load_kops(counted)


def main():
    macros = {}
    start = newest("fair-start-*.jsonl")
    after = newest("fair-after-*.jsonl")

    after_rows = load(after)
    summarise(load(start), "ProbeStart", macros, percentiles=True)
    summarise(after_rows, "ProbeAfter", macros, percentiles=False)
    kernel_split(after_rows, "ProbeAfter", macros)
    sg_facts(macros)

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
        fh.write("% Sg* queue swap: campaign host when bench/results-probes-campaign-jaybird/\n")
        fh.write("% exists; otherwise bench/results-probes-20260930-sg/. Flat-map probe stays\n")
        fh.write("% on the further host. Not in the Holm-tested family.\n")
        for name in sorted(macros):
            fh.write(f"\\newcommand{{\\{name}}}{{{macros[name]}}}\n")
    print(f"wrote {OUT} ({len(macros)} macros)")
    print(f"  clock A: {os.path.basename(start)}")
    print(f"  clock B: {os.path.basename(after)}")


if __name__ == "__main__":
    sys.exit(main())
