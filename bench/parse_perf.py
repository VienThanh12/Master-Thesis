#!/usr/bin/env python3
"""Turn `perf stat -x,` output into JSON records, and summarise a set of them.

Split out of bench/counters.sh so it can be tested without a PMU. The counters it
parses can only be collected on the bare-metal testbed, so the parsing has to be
known-good *before* that visit rather than debugged during it; `--self-test`
exercises it against the exact output formats perf produces, including the ones
that carry no number.

`perf stat -x,` emits one line per event:

    value,unit,event,run-time,pct-enabled[,metric,metric-unit]

An event the host cannot count appears with `<not supported>` or `<not counted>`
in the value field. Those are recorded as null rather than zero: a counter that
did not run is not a counter that read zero, and averaging the two together would
manufacture a result.

Usage:
  parse_perf.py record <csv> <scope> <lang> <alloc> <repeat> <kind>
  parse_perf.py summarise <counters.jsonl>
  parse_perf.py --self-test
"""
import json
import statistics
import sys

# Derived ratios worth reporting. Raw counts scale with how long a run happened to
# last, so they cannot be compared across variants; these forms can.
DERIVED_LABELS = [
    ("ipc", "IPC", ">7.3f"),
    ("cache_miss_rate", "miss rate", ">10.4f"),
    ("cache_misses_per_kinstr", "miss/kins", ">10.3f"),
    ("llc_load_misses_per_kinstr", "LLC/kins", ">9.3f"),
]


def parse_events(text):
    """Parse `perf stat -x,` text into {event: {"value": float|None, "unit": str|None}}."""
    events = {}
    for line in text.splitlines():
        line = line.strip()
        # perf -o prepends a comment banner and a blank line.
        if not line or line.startswith("#"):
            continue
        parts = line.split(",")
        if len(parts) < 3:
            continue
        raw, unit, event = parts[0].strip(), parts[1].strip(), parts[2].strip()
        if not event:
            continue
        try:
            value = float(raw)
        except ValueError:
            value = None
        events[event] = {"value": value, "unit": unit or None}
    return events


def derive(events):
    """Comparable ratios, computed only from events that actually counted."""
    def val(name):
        e = events.get(name)
        return e["value"] if e and e["value"] is not None else None

    out = {}
    cycles, instructions = val("cycles"), val("instructions")
    if cycles and instructions:
        out["ipc"] = round(instructions / cycles, 4)
    misses, refs = val("cache-misses"), val("cache-references")
    if misses is not None and refs:
        out["cache_miss_rate"] = round(misses / refs, 6)
    if misses is not None and instructions:
        out["cache_misses_per_kinstr"] = round(1000.0 * misses / instructions, 4)
    llc = val("LLC-load-misses")
    if llc is not None and instructions:
        out["llc_load_misses_per_kinstr"] = round(1000.0 * llc / instructions, 4)
    return out


def build_record(text, scope, lang, alloc, repeat, kind):
    events = parse_events(text)
    rec = {
        "scope": scope,
        "lang": lang,
        "alloc": alloc,
        "repeat": int(repeat),
        "kind": kind,
        "events": events,
    }
    if not events:
        # A failed run must be visible in the data rather than simply missing from
        # it, or the repeat count silently drops for one variant.
        rec["error"] = "no counter output (perf produced nothing parseable)"
    rec.update(derive(events))
    return rec


def summarise(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    if not rows:
        sys.exit(f"no counter records in {path}")

    groups = {}
    for r in rows:
        groups.setdefault((r["scope"], r["lang"], r["alloc"]), []).append(r)

    def med(rs, key):
        xs = [r[key] for r in rs if r.get(key) is not None]
        return statistics.median(xs) if xs else None

    head = f"{'scope':5} {'lang':5} {'alloc':9}"
    for _key, label, fmt in DERIVED_LABELS:
        width = int(fmt.lstrip(">").split(".")[0])
        head += f" {label:>{width}}"
    head += "   n"
    print(head)
    print("-" * len(head))
    for key in sorted(groups):
        rs = groups[key]
        line = f"{key[0]:5} {key[1]:5} {key[2]:9}"
        for metric, _label, fmt in DERIVED_LABELS:
            v = med(rs, metric)
            width = int(fmt.lstrip(">").split(".")[0])
            line += " " + (format(v, fmt) if v is not None else f"{'n/a':>{width}}")
        line += f"  {len(rs)}"
        print(line)

    failed = [r for r in rows if "error" in r]
    if failed:
        print(f"\n{len(failed)} run(s) produced no counters at all; see 'error' in the JSONL.")
    unsupported = sorted({e for r in rows for e, v in r["events"].items()
                          if v["value"] is None})
    if unsupported:
        print("\nnot counted on this host:", ", ".join(unsupported))
        print("Recorded as null, not zero: a counter that did not run is not one")
        print("that read zero, and the two must not be averaged together.")


def self_test():
    """Check the parser against the shapes perf actually emits."""
    # Real `perf stat -x, -o file` output: banner, blank line, then events. The
    # LLC line is the "unsupported event" case, which is common in guests.
    sample = """# started on Fri Aug 14 12:00:00 2026

12345678901,,cycles,4001234567,100.00
9876543210,,instructions,4001234567,100.00,0.80,insn per cycle
123456789,,cache-references,4001234567,100.00
12345678,,cache-misses,4001234567,100.00,10.000,of all cache refs
<not supported>,,LLC-load-misses,4001234567,0.00
"""
    events = parse_events(sample)
    assert set(events) == {"cycles", "instructions", "cache-references",
                           "cache-misses", "LLC-load-misses"}, events
    assert events["cycles"]["value"] == 12345678901
    assert events["LLC-load-misses"]["value"] is None, "unsupported must be null, not 0"

    # Tolerances allow for the deliberate rounding in `derive`.
    d = derive(events)
    assert abs(d["ipc"] - 9876543210 / 12345678901) < 5e-5, d
    assert abs(d["cache_miss_rate"] - 12345678 / 123456789) < 5e-7, d
    assert abs(d["cache_misses_per_kinstr"] - 1000.0 * 12345678 / 9876543210) < 5e-5, d
    assert "llc_load_misses_per_kinstr" not in d, "must not derive from a null counter"

    # Software events carry a unit, and multiplexing appends fields.
    soft = parse_events("4001.23,msec,task-clock,4001234567,100.00,7.998,CPUs utilized\n"
                        "512,,page-faults,4001234567,100.00\n"
                        "<not counted>,,cpu-migrations,0,0.00\n")
    assert soft["task-clock"]["unit"] == "msec", soft
    assert soft["page-faults"]["value"] == 512
    assert soft["cpu-migrations"]["value"] is None
    assert derive(soft) == {}, "software events derive nothing"

    # Degenerate input must produce a record flagged as failed, not a silent gap.
    rec = build_record("", "op", "cpp", "system", 1, "hardware")
    assert rec["events"] == {} and "error" in rec, rec

    # A zero instruction count must not divide.
    z = parse_events("100,,cycles,1,100.00\n0,,instructions,1,100.00\n")
    assert derive(z) == {}, derive(z)

    print("parse_perf self-test: all checks pass")


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--self-test":
        self_test()
        return
    if len(sys.argv) >= 2 and sys.argv[1] == "summarise":
        summarise(sys.argv[2])
        return
    if len(sys.argv) == 8 and sys.argv[1] == "record":
        _, _, csv, scope, lang, alloc, repeat, kind = sys.argv
        with open(csv) as f:
            text = f.read()
        print(json.dumps(build_record(text, scope, lang, alloc, repeat, kind)))
        return
    sys.exit(__doc__)


if __name__ == "__main__":
    main()
