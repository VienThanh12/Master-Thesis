#!/usr/bin/env python3
"""Macros for the further-host mixed multi-outstanding overload run.

The confirmatory log is one frozen load on major-louse, 6 October 2026:
mixed lifecycle, seven producers, twenty interleaved repeats, and several
requests in flight. The capacity sweep freezes the first measured load where
all four variants complete less than 99% of planned requests in the arrival
window. This dataset is not the reported campaign or part of its tested family.
"""

import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOG_DIR = os.path.join(HERE, "results-pipeline-20261006-louse")
LOG = os.path.join(LOG_DIR, "pipeline-mixed-20261006-130745.jsonl")
CAPACITY = os.path.join(LOG_DIR, "pipeline-mixed-20261006-130135.jsonl")
ENV = os.path.join(LOG_DIR, "env-host-major-louse.txt")
OUT = os.path.join(ROOT, "figures", "gen_pipeline_mixed.tex")

ORDER = ("cpp-system", "rust-system", "cpp-jemalloc", "rust-jemalloc")
KIND_NAMES = (
    "Create",
    "Setup",
    "Signal",
    "AddDrb",
    "BeginReconf",
    "CompleteReconf",
    "AbortReconf",
    "Release",
)
RATE = 560000
PRODUCERS = 7
ACTIVE_UES = 5000
REPEATS = 20
STATS = ("p50", "p99", "p999")


def fail(msg):
    print(f"pipeline_mixed_facts: {msg}", file=sys.stderr)
    sys.exit(1)


def read_rows(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read {path}: {exc}")


def cpu_model():
    try:
        with open(ENV, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("Model name:"):
                    return " ".join(line.split(":", 1)[1].split())
    except OSError as exc:
        fail(f"cannot read {ENV}: {exc}")
    fail(f"no CPU model in {ENV}")


def variant(row):
    return f"{row['lang']}-{row['alloc']}"


def check_common(row, where):
    if row.get("schema") != "pipeline" or row.get("workload") != "mixed":
        fail(f"{where} is not a mixed pipeline row")
    if row.get("queue") != ("mutex" if row.get("lang") == "cpp" else "channel"):
        fail(f"{where} has unexpected queue {row.get('queue')}")
    if row.get("stamp_start") or not row.get("valid"):
        fail(f"{where} is not a confirmatory-clock run")
    if row.get("errors") or row.get("timed_out") or row.get("histogram_overflows"):
        fail(f"{where} failed a validity gate")
    if int(row.get("producers", -1)) != PRODUCERS:
        fail(f"{where} has the wrong producer count")
    if int(row.get("active_ues", -1)) != ACTIVE_UES:
        fail(f"{where} has the wrong active-UE count")
    if row.get("planned") != row.get("enqueue_started") or row.get("planned") != row.get("enqueued"):
        fail(f"{where} did not enqueue every planned request")
    completed = row.get("completed_within_window", -1) + row.get("completed_during_drain", -1)
    if completed != row.get("enqueued"):
        fail(f"{where} lost a completion")
    kinds = row.get("kinds")
    if not isinstance(kinds, list) or len(kinds) != len(KIND_NAMES):
        fail(f"{where} has no eight-class operation count")
    if any(not isinstance(count, int) or count < 0 for count in kinds):
        fail(f"{where} has an invalid operation count")
    if sum(kinds) != row.get("planned"):
        fail(f"{where} operation counts do not sum to planned requests")


def check_capacity():
    rows = read_rows(CAPACITY)
    grouped = {}
    for i, row in enumerate(rows):
        check_common(row, f"capacity row {i}")
        rate = int(row["rate"])
        name = variant(row)
        items = grouped.setdefault(rate, {})
        if name in items:
            fail(f"capacity rate {rate} contains {name} more than once")
        items[name] = row
    if any(set(items) != set(ORDER) for items in grouped.values()):
        fail("the capacity sweep does not contain all four variants at every load")
    rates = sorted(grouped)
    if RATE not in grouped:
        fail(f"the capacity sweep does not contain the frozen rate {RATE}")
    candidates = []
    for rate in rates:
        items = grouped[rate]
        vectors = {tuple(row["kinds"]) for row in items.values()}
        if len(vectors) != 1:
            fail(f"operation counts differ across variants at rate {rate}")
        all_late = all(
            row["completed_within_window"] / row["planned"] < 0.99
            for row in items.values()
        )
        if all_late:
            candidates.append(rate)
    if not candidates:
        fail("no capacity load makes all four variants fall behind")
    if candidates[0] != RATE:
        fail(f"the frozen rate is {RATE}, but the capacity rule selects {candidates[0]}")


def load_confirmatory():
    rows = read_rows(LOG)
    if len(rows) != REPEATS * len(ORDER):
        fail(f"expected {REPEATS * len(ORDER)} rows, found {len(rows)}")
    grouped = {name: [] for name in ORDER}
    by_seed = {}
    for i, row in enumerate(rows):
        check_common(row, f"confirmatory row {i}")
        if int(row["rate"]) != RATE:
            fail(f"confirmatory row {i} is not at the frozen load")
        repeat = i // len(ORDER)
        expected = ORDER[(repeat + (i % len(ORDER))) % len(ORDER)]
        got = variant(row)
        if got != expected:
            fail(f"row {i} is {got}, the interleave expects {expected}")
        grouped[got].append(row)
        by_seed.setdefault(row["seed"], []).append(row)
    if len(by_seed) != REPEATS:
        fail(f"expected {REPEATS} seeds, found {len(by_seed)}")
    for seed, items in by_seed.items():
        if len(items) != len(ORDER) or {variant(row) for row in items} != set(ORDER):
            fail(f"seed {seed} does not contain all four variants")
        if len({tuple(row["kinds"]) for row in items}) != 1:
            fail(f"operation counts differ across variants for seed {seed}")
    for name, items in grouped.items():
        if len(items) != REPEATS:
            fail(f"{name} has {len(items)} repeats")
    return grouped, by_seed


def median(rows, section, key):
    return statistics.median(row[section][key] for row in rows)


def check_direction(grouped):
    counts = {}
    for alloc in ("system", "jemalloc"):
        cpp = grouped[f"cpp-{alloc}"]
        rust = grouped[f"rust-{alloc}"]
        for stat in STATS:
            lower = sum(
                r["primary_ns"][stat] < c["primary_ns"][stat]
                for c, r in zip(cpp, rust)
            )
            counts[(alloc, stat)] = lower
            expected = REPEATS if alloc == "jemalloc" else 0
            if lower != expected:
                fail(f"{alloc} {stat}: Rust was lower in {lower} of {REPEATS} pairs")
        in_service_lower = sum(
            r["in_service_ns"]["p50"] < c["in_service_ns"]["p50"]
            for c, r in zip(cpp, rust)
        )
        if in_service_lower != REPEATS:
            fail(
                f"{alloc} in-service p50: Rust was lower in "
                f"{in_service_lower} of {REPEATS} pairs"
            )
    return counts


def check_components(grouped):
    for name, rows in grouped.items():
        for row in rows:
            primary = row["primary_ns"]["p50"]
            admission = row["admission_ns"]["p50"]
            if primary <= 0 or abs(primary - admission) / primary > 0.02:
                fail(f"{name} admission p50 is not the primary delay")
            if row["in_service_ns"]["p50"] * 1000 > primary:
                fail(f"{name} in-service p50 is not far below the primary delay")


def operation_mix(by_seed):
    totals = [0] * len(KIND_NAMES)
    planned = 0
    for items in by_seed.values():
        row = items[0]
        planned += row["planned"]
        for i, count in enumerate(row["kinds"]):
            totals[i] += count
    if any(count == 0 for count in totals):
        fail("the confirmatory run does not exercise every mixed operation class")
    return totals, planned


def emit(grouped, by_seed, counts):
    totals, mix_planned = operation_mix(by_seed)
    macros = {
        "PipeMixedCpu": cpu_model(),
        "PipeMixedOfferedKops": str(RATE * PRODUCERS // 1000),
        "PipeMixedRepeats": str(REPEATS),
        "PipeMixedActiveUes": str(ACTIVE_UES),
        "PipeMixedRustLowerSystemPairs": str(counts[("system", "p50")]),
        "PipeMixedRustLowerJemallocPairs": str(counts[("jemalloc", "p50")]),
    }
    for name, count in zip(KIND_NAMES, totals):
        macros[f"PipeMixed{name}Pct"] = f"{100.0 * count / mix_planned:.1f}"
    for stat in STATS:
        tag = {"p50": "Fifty", "p99": "NinetyNine", "p999": "NinetyNineNine"}[stat]
        for name, rows in grouped.items():
            lang, alloc = name.split("-")
            label = f"{lang.capitalize()}{alloc.capitalize()}"
            macros[f"PipeMixed{tag}Ms{label}"] = (
                f"{median(rows, 'primary_ns', stat) / 1e6:.1f}"
            )
            if stat == "p50":
                macros[f"PipeMixedAdmMs{label}"] = (
                    f"{median(rows, 'admission_ns', stat) / 1e6:.1f}"
                )
                macros[f"PipeMixedInServiceUs{label}"] = (
                    f"{median(rows, 'in_service_ns', stat) / 1e3:.1f}"
                )
                inside = statistics.median(
                    100.0 * row["completed_within_window"] / row["planned"]
                    for row in rows
                )
                macros[f"PipeMixedInWin{label}Pct"] = f"{inside:.1f}"
                throughput = statistics.median(
                    row["throughput_ops_s"] / 1000.0 for row in rows
                )
                macros[f"PipeMixedThroughputKops{label}"] = f"{throughput:.1f}"
    lines = [
        "% Generated by bench/pipeline_mixed_facts.py.",
        "% Further host, 6 October 2026. Not the reported campaign.",
        "% Not in the reported campaign's tested family.",
        "% PipeMixedInServiceUs is worker completion minus queue entry.",
        "% It includes queue waiting. This run does not time the operation alone.",
        "% PipeMixedAdmMs is planned arrival to queue entry.",
        "% A Pct value is a percent. A Kops value is thousand operations per second.",
        "% A Fifty, NinetyNine, or NinetyNineNine name is that percentile.",
        "% Macro names contain no digits: TeX would end the name at the first one.",
        "% Pair macros count repeats whose Rust median is below C++.",
    ]
    for key in sorted(macros):
        lines.append(f"\\newcommand{{\\{key}}}{{{macros[key]}}}")
    text = "\n".join(lines) + "\n"
    old = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
    if text != old:
        with open(OUT, "w", encoding="utf-8") as fh:
            fh.write(text)
    print(f"pipeline_mixed_facts: {OUT} ({len(macros)} macros)")


def main():
    check_capacity()
    grouped, by_seed = load_confirmatory()
    counts = check_direction(grouped)
    check_components(grouped)
    emit(grouped, by_seed, counts)


if __name__ == "__main__":
    main()
