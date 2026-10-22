#!/usr/bin/env python3
"""Macros for the same-handoff probe and the deferred-fill timer test.

Both ran on a further host (Cherry Lithuania `composed-killdeer`, AMD EPYC 7443P,
19 October 2026), so nothing here is the reported campaign and nothing is in the
Holm-tested family. See docs/OVERLOAD_MECHANISM.md §4.16 and §4.17.

The same-handoff probe (bench/matched_probes.sh) runs the real ShardCore behind
each language's own standard-library handoff and behind one hand-written queue
and reply slot that both languages share by design. Its kernel calls per request
come from a separate bpftrace session (bench/futex_counts.sh --matched).

The timer test (fillwindow.sh, kept with the results) set the deferred fill's
cap to 0, which in that mode removes only the fill, once before bench.rs closed
its window ahead of the fill and once after.

Every sentence Thesis_v5 builds on these numbers is checked here, the way
probe_facts.py checks the queue swap: a log that stops supporting a sentence
stops the build instead of quietly changing what the sentence means.

Reads bench/results-probes-20261019-killdeer/ and writes figures/gen_handoff.tex.
"""

import glob
import json
import os
import re
import statistics
import sys

from plot_figures import paired_permutation_test
from probe_facts import fmt_p, median

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROBES = os.path.join(HERE, "results-probes-20261019-killdeer")
# The second further host (Cherry Chicago `select-bream`, 20 October 2026): the time per
# part of a call (`matched_probes.sh --stages`) and a repeat of the throughput comparison.
STAGES = os.path.join(HERE, "results-probes-20261020-bream")
OUT = os.path.join(ROOT, "figures", "gen_handoff.tex")
PARTS = (("queue_us", "Queue"), ("worker_us", "Worker"), ("reply_us", "Reply"),
         ("sender_us", "Sender"))

# The timer test ran twice on the same host and boot: before and after bench.rs
# was changed to close its window ahead of the fill. Named, not globbed, because
# "newest" would quietly swap the bias measurement for its verification.
FILL_BEFORE = "fillwindow-20261019-151109.jsonl"
FILL_AFTER = "fillwindow-20261019-152452.jsonl"

STABLE_CV = 0.05
ALPHA = 0.05
WAKE_OPS = {"1", "10"}


def fail(msg):
    raise SystemExit(f"handoff_facts: {msg}")


def load(path):
    with open(path, encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    if not rows:
        fail(f"{path} is empty")
    return rows


def by_arm(rows):
    out = {}
    for r in rows:
        out.setdefault(r["arm"], {})[r["repeat"]] = r
    return out


def paired(arms, names, field):
    reps = sorted(set.intersection(*(set(arms[a]) for a in names)))
    if not reps:
        fail(f"no repeat holds all of {names}")
    return reps, {a: [arms[a][k][field] for k in reps] for a in names}


def pct(base, probe):
    """Median over repeats of the paired change from base to probe, in per cent."""
    return median([(y - x) / x * 100.0 for x, y in zip(base, probe)])


def host_cpu(path):
    text = open(path, encoding="utf-8").read()
    m = re.search(r"Model name:\s+(.+)", text)
    if not m:
        fail(f"no CPU model in {path}")
    return m.group(1).replace(" 24-Core Processor", "").strip()


def overload_load():
    """The deferred-fill sweep's top load, which the caveat calls the highest load."""
    text = open(os.path.join(ROOT, "figures", "gen_probes.tex"), encoding="utf-8").read()
    m = re.search(r"\\newcommand\{\\ProbeAfterOverloadLoad\}\{(\d+)\}", text)
    if not m:
        fail("gen_probes.tex has no ProbeAfterOverloadLoad")
    return int(m.group(1))


def same_handoff(macros):
    path = sorted(glob.glob(os.path.join(PROBES, "matched_probes-*.jsonl")))[-1]
    rows = load(path)
    arms = by_arm(rows)

    if any(r["errors"] for r in rows):
        fail(f"{os.path.basename(path)} has failed operations")
    for arm, runs in arms.items():
        vals = [r["ops_per_s"] for r in runs.values()]
        cv = statistics.pstdev(vals) / statistics.mean(vals)
        if cv > STABLE_CV:
            fail(f"{arm} varies by {cv:.1%} across repeats, above the driver's 5% rule")

    names = [f"{lang}-{design}-{heap}" for lang in ("cpp", "rust")
             for design in ("stock", "matched") for heap in ("system", "jemalloc")]
    reps, thr = paired(arms, names, "ops_per_s")
    macros["HandoffPairs"] = str(len(reps))

    for heap, tag in (("system", "System"), ("jemalloc", "Jemalloc")):
        cpp_s, rust_s = thr[f"cpp-stock-{heap}"], thr[f"rust-stock-{heap}"]
        cpp_m, rust_m = thr[f"cpp-matched-{heap}"], thr[f"rust-matched-{heap}"]
        stock, same = pct(cpp_s, rust_s), pct(cpp_m, rust_m)
        # Thesis_v5: Rust finished more calls through its own library, and the gap
        # fell with the same handoff.
        if stock <= 0 or same >= stock:
            fail(f"{heap}: Rust over C++ is {stock:.1f}% stock and {same:.1f}% with the "
                 "same handoff. Thesis_v5 says the gap fell from a Rust lead.")
        macros[f"HandoffStockLead{tag}"] = f"{stock:.1f}"
        macros[f"HandoffSameLead{tag}"] = f"{same:.1f}"
        macros[f"HandoffSameAhead{tag}"] = str(sum(r > c for c, r in zip(cpp_m, rust_m)))
        _md, p, _n = paired_permutation_test(cpp_m, rust_m)
        macros[f"HandoffSameP{tag}"] = fmt_p(p)
        if heap == "jemalloc" and p <= ALPHA:
            fail(f"jemalloc same-handoff gap now has p = {p:.3f}. Thesis_v5 says the "
                 "test cannot separate it from no difference.")
        if heap == "system":
            if same <= 0:
                fail("Rust is no longer ahead with the same handoff. Thesis_v5 says it is.")
            for lang, ltag in (("cpp", "Cpp"), ("rust", "Rust")):
                gain = pct(thr[f"{lang}-stock-{heap}"], thr[f"{lang}-matched-{heap}"])
                macros[f"HandoffGain{ltag}"] = f"{gain:.1f}"

    def arm_median(arm, value):
        return median([value(r) for r in arms[arm].values()])

    user_cpp = arm_median("cpp-matched-system", lambda r: r["cpu_user_s"] / r["ops"] * 1e6)
    user_rust = arm_median("rust-matched-system", lambda r: r["cpu_user_s"] / r["ops"] * 1e6)
    if user_rust >= user_cpp:
        fail("Rust no longer uses less user CPU per call with the same handoff.")
    macros["HandoffUserLessUs"] = f"{user_cpp - user_rust:.2f}"
    macros["HandoffCallUs"] = (
        f"{arm_median('rust-matched-system', lambda r: r['us_per_op_per_sender']):.1f}"
    )

    envs = sorted(glob.glob(os.path.join(PROBES, "env-matched-*.txt")))
    if not envs:
        fail("no env-matched capture next to the same-handoff log")
    macros["HandoffCpu"] = host_cpu(envs[-1])
    return path


def replication(macros):
    """The same comparison repeated on the second further host, without stamps."""
    logs = sorted(glob.glob(os.path.join(STAGES, "matched_probes-*.jsonl")))
    if not logs:
        fail(f"no matched_probes log in {STAGES}")
    rows = load(logs[-1])
    arms = by_arm(rows)
    if any(r["errors"] for r in rows):
        fail(f"{os.path.basename(logs[-1])} has failed operations")
    for arm, runs in arms.items():
        vals = [r["ops_per_s"] for r in runs.values()]
        if statistics.pstdev(vals) / statistics.mean(vals) > STABLE_CV:
            fail(f"repeat host: {arm} varies by more than the driver's 5% rule")
    names = [f"{lang}-{design}-{heap}" for lang in ("cpp", "rust")
             for design in ("stock", "matched") for heap in ("system", "jemalloc")]
    reps, thr = paired(arms, names, "ops_per_s")
    macros["HandoffRepPairs"] = str(len(reps))
    for heap, tag in (("system", "System"), ("jemalloc", "Jemalloc")):
        stock = pct(thr[f"cpp-stock-{heap}"], thr[f"rust-stock-{heap}"])
        same = pct(thr[f"cpp-matched-{heap}"], thr[f"rust-matched-{heap}"])
        if stock <= 0 or same >= stock:
            fail(f"repeat host, {heap}: Rust over C++ is {stock:.1f}% stock and {same:.1f}% "
                 "with the same handoff. Thesis_v5 says the gap fell there too.")
        macros[f"HandoffRepStockLead{tag}"] = f"{stock:.1f}"
        macros[f"HandoffRepSameLead{tag}"] = f"{same:.1f}"
        macros[f"HandoffRepSameAhead{tag}"] = str(sum(
            r > c for c, r in zip(thr[f"cpp-matched-{heap}"], thr[f"rust-matched-{heap}"])))
    # The range the discussion quotes for the system allocator, low end first.
    pair = sorted([float(macros["HandoffSameLeadSystem"]), float(macros["HandoffRepSameLeadSystem"])])
    if pair[0] <= 0:
        fail("Rust is not ahead with the same handoff on both hosts. Thesis_v5 says it is.")
    macros["HandoffSameLeadLo"], macros["HandoffSameLeadHi"] = (f"{v:.1f}" for v in pair)
    return logs[-1]


def kernel_calls(macros):
    """Per finished request, by the difference of the 6 s and 3 s windows."""
    logs = []
    for path in sorted(glob.glob(os.path.join(PROBES, "futex_counts-*.jsonl"))):
        if any(r["arm"] == "cpp-matched" for r in load(path)):
            logs.append(path)
    if not logs:
        fail("no futex_counts log with the same-handoff arms")
    rows = load(logs[-1])

    def flat(m):
        return m if isinstance(m, dict) else {"": m}

    def counts(r):
        bt = r["bpftrace"]
        zero = flat(bt.get("@zero", {}))
        empty = sum(v for k, v in zero.items() if k in WAKE_OPS)
        calls = sum(flat(bt.get("@sys", {})).values())
        return empty, calls, r["bench"]["ops"]

    per = {}
    for arm, rep in sorted({(r["arm"], r["repeat"]) for r in rows}):
        pair = {r["max_run_s"]: r for r in rows if r["arm"] == arm and r["repeat"] == rep}
        if len(pair) != 2:
            continue
        (_s, short), (_l, long_) = sorted(pair.items())
        es, cs, os_ = counts(short)
        el, cl, ol = counts(long_)
        if ol <= os_:
            continue
        per.setdefault(arm, []).append(((el - es) / (ol - os_), (cl - cs) / (ol - os_)))

    def med(arm, i):
        if arm not in per:
            fail(f"{arm} has no complete pair of windows")
        return median([v[i] for v in per[arm]])

    empty_cpp, empty_rust = med("cpp-mstock", 0), med("rust-mstock", 0)
    if empty_cpp <= empty_rust:
        fail("the C++ service no longer makes more empty wakes than the Rust one.")
    macros["HandoffEmptyWakesCpp"] = f"{empty_cpp:.2f}"
    macros["HandoffEmptyWakesRust"] = f"{empty_rust:.2f}"
    same = {f"{med(a, 1):.2f}" for a in ("cpp-matched", "rust-matched")}
    # The prose gives one figure for both languages, so they must agree.
    if len(same) != 1:
        fail(f"system calls per request differ with the same handoff: {same}")
    macros["HandoffSyscallsSame"] = same.pop()
    return logs[-1]


def timer_test(macros):
    """The deferred fill counted against Rust's window and not against C++'s."""
    def read(name):
        path = os.path.join(PROBES, name)
        arms = by_arm(load(path))
        reps, thr = paired(arms, ["cpp-10000", "cpp-0", "rust-10000", "rust-0"],
                           "throughput_ops_s")
        return arms, reps, thr

    arms, reps, thr = read(FILL_BEFORE)
    gain = pct(thr["rust-10000"], thr["rust-0"])
    _md, p_rust, _n = paired_permutation_test(thr["rust-10000"], thr["rust-0"])
    _md, p_cpp, _n = paired_permutation_test(thr["cpp-10000"], thr["cpp-0"])
    if gain <= 0 or p_rust >= ALPHA:
        fail(f"before the fix, leaving the fill out moved Rust by {gain:+.1f}% "
             f"(p = {p_rust:.3f}). Thesis_v5 says it raised Rust's throughput.")
    if p_cpp < ALPHA:
        fail(f"before the fix, leaving the fill out moved C++ (p = {p_cpp:.3f}). "
             "Thesis_v5 says it did not change C++.")
    first = next(iter(next(iter(arms.values())).values()))
    load_kops = round(first["rate"] * first["producers"] / 1000.0)
    if load_kops != overload_load():
        fail(f"the timer test ran at {load_kops} kops/s, not the sweep's top load "
             f"{overload_load()}. Thesis_v5 says the highest load.")
    macros["FillWindowRustGain"] = f"{gain:.1f}"
    macros["FillWindowRustAhead"] = str(sum(
        y > x for x, y in zip(thr["rust-10000"], thr["rust-0"])))
    macros["FillWindowPairs"] = str(len(reps))

    _arms, _reps, thr = read(FILL_AFTER)
    _md, p_after, _n = paired_permutation_test(thr["rust-10000"], thr["rust-0"])
    if p_after < ALPHA and pct(thr["rust-10000"], thr["rust-0"]) > 0:
        fail("after the fix, leaving the fill out still raises Rust's throughput. "
             "Thesis_v5 says the harness was corrected.")


def call_parts(macros):
    """Time per part of a call, median over repeats of each run's mean, in microseconds."""
    logs = sorted(glob.glob(os.path.join(STAGES, "matched_stages-*.jsonl")))
    if not logs:
        fail(f"no matched_stages log in {STAGES}")
    rows = load(logs[-1])
    arms = by_arm(rows)
    names = [f"{lang}-{design}-system" for lang in ("cpp", "rust")
             for design in ("stock", "matched")]
    reps, _thr = paired(arms, names, "ops_per_s")
    if any(r["errors"] for r in rows):
        fail(f"{os.path.basename(logs[-1])} has failed operations")
    for arm in names:
        for field in ("us_per_op_per_sender", "queue_us", "reply_us"):
            vals = [arms[arm][k][field] for k in reps]
            cv = statistics.pstdev(vals) / statistics.mean(vals)
            if cv > STABLE_CV:
                fail(f"{arm} {field} varies by {cv:.1%} across repeats")
        for k in reps:
            r = arms[arm][k]
            total = sum(r[f] for f, _ in PARTS)
            if abs(total - r["us_per_op_per_sender"]) > 0.02 * r["us_per_op_per_sender"]:
                fail(f"{arm} repeat {k}: the parts miss the time per call")

    med = {a: {f: median([arms[a][k][f] for k in reps])
               for f in ["us_per_op_per_sender"] + [f for f, _ in PARTS]} for a in names}
    tags = {"cpp-stock-system": "CppOwn", "rust-stock-system": "RustOwn",
            "cpp-matched-system": "CppSame", "rust-matched-system": "RustSame"}
    for arm, tag in tags.items():
        for field, part in PARTS:
            macros[f"Stage{part}{tag}"] = f"{med[arm][field]:.2f}"
        macros[f"StageCall{tag}"] = f"{sum(med[arm][f] for f, _ in PARTS):.2f}"

    share = {a: {f: med[a][f] / sum(med[a][g] for g, _ in PARTS) for f, _ in PARTS}
             for a in names}
    # Thesis_v5: the two handoffs are nearly the whole call, the operation a sliver.
    for a in names:
        if share[a]["queue_us"] + share[a]["reply_us"] < 0.95:
            fail(f"{a}: queue and reply are only {share[a]['queue_us'] + share[a]['reply_us']:.0%} "
                 "of a call. Thesis_v5 says they are nearly all of it.")
        # Thesis_v5: the call splits roughly in half between the queue and the reply.
        for f in ("queue_us", "reply_us"):
            if not 0.4 <= share[a][f] <= 0.6:
                fail(f"{a}: {f} is {share[a][f]:.0%} of a call. Thesis_v5 says roughly half.")
    macros["StageHandoffShareMin"] = (
        f"{100 * min(share[a]['queue_us'] + share[a]['reply_us'] for a in names):.0f}")
    macros["StageWorkerShareMax"] = f"{100 * max(share[a]['worker_us'] for a in names):.1f}"
    # Thesis_v5: through the standard libraries most of the gap sits in the queue.
    gap_q = med["cpp-stock-system"]["queue_us"] - med["rust-stock-system"]["queue_us"]
    gap_r = med["cpp-stock-system"]["reply_us"] - med["rust-stock-system"]["reply_us"]
    gap_call = sum(med["cpp-stock-system"][f] - med["rust-stock-system"][f] for f, _ in PARTS)
    if gap_call <= 0 or gap_q < 0.5 * gap_call or gap_q <= gap_r:
        fail(f"own libraries: queue gap {gap_q:.2f}, reply gap {gap_r:.2f}, call gap "
             f"{gap_call:.2f} us. Thesis_v5 says most of the gap is in the queue.")
    macros["StageQueueGapOwn"] = f"{gap_q:.2f}"
    macros["StageCallGapOwn"] = f"{gap_call:.2f}"
    # Thesis_v5: with the same handoff the two handoff parts match closely.
    same = max(abs(med["cpp-matched-system"][f] - med["rust-matched-system"][f])
               for f in ("queue_us", "reply_us"))
    macros["StageSameMaxDiff"] = f"{same:.2f}"
    # Thesis_v5: Rust's worker part is the shorter one in both designs.
    for design in ("stock", "matched"):
        if med[f"rust-{design}-system"]["worker_us"] >= med[f"cpp-{design}-system"]["worker_us"]:
            fail(f"{design}: Rust's worker part is no longer the shorter one")
    macros["StagePairs"] = str(len(reps))
    envs = sorted(glob.glob(os.path.join(STAGES, "env-*.txt")))
    if not envs:
        fail(f"no env capture in {STAGES}")
    macros["StageCpu"] = host_cpu(envs[-1])
    return logs[-1]


def main():
    macros = {}
    matched = same_handoff(macros)
    repeat = replication(macros)
    futex = kernel_calls(macros)
    timer_test(macros)
    stages = call_parts(macros)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("% Generated by bench/handoff_facts.py -- do not edit by hand.\n")
        fh.write("% Further hosts (composed-killdeer, 19 October 2026, and select-bream for\n")
        fh.write("% Stage* and HandoffRep*, 20 October 2026). Not the reported campaign and\n")
        fh.write("% not in the Holm-tested family.\n")
        for name in sorted(macros):
            fh.write(f"\\newcommand{{\\{name}}}{{{macros[name]}}}\n")
    print(f"wrote {OUT} ({len(macros)} macros)")
    print(f"  same handoff: {os.path.basename(matched)}")
    print(f"  repeat host:  {os.path.basename(repeat)}")
    print(f"  kernel calls: {os.path.basename(futex)}")
    print(f"  timer test:   {FILL_BEFORE} and {FILL_AFTER}")
    print(f"  call parts:   {os.path.basename(stages)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
