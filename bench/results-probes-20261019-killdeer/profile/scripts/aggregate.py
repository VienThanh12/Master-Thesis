#!/usr/bin/env python3
"""Mean and range over the cycle-sampled repeats, per build. Disposable."""
import glob
import json
import os
import statistics
from collections import defaultdict

d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
arms = ["cpp-deque", "rust-channel", "rust-oneshot"]
owners = ["UE operation", "shard queue", "reply handle", "service dispatch", "harness",
          "handoff, unresolved", "unknown"]
kinds = ["own code", "allocator", "kernel"]
runs = {a: [json.load(open(f)) for f in sorted(glob.glob(os.path.join(d, f"cprof-{a}-[789].json")))]
        for a in arms}


def cell(rs, key):
    vals = [r["us_per_call"].get(key, 0.0) for r in rs]
    return statistics.mean(vals), min(vals), max(vals)


def owner_total(r, o):
    return sum(r["us_per_call"].get(f"{k}|{o}", 0.0) for k in kinds + ["unwind failed"])


summary = {}
for a in arms:
    rs = runs[a]
    print(f"== {a}: {len(rs)} repeats, {statistics.mean(r['throughput_ops_s'] for r in rs) / 1e3:.1f} kops/s "
          f"while profiled, {statistics.mean(r['us_per_call_total'] for r in rs):.2f} us of CPU per call "
          f"(range {min(r['us_per_call_total'] for r in rs):.2f} to {max(r['us_per_call_total'] for r in rs):.2f})")
    print(f"   {'owner':<20}" + "".join(f"{k:>12}" for k in kinds) + f"{'total':>10}{'range':>16}")
    summary[a] = {}
    for o in owners:
        vals = [owner_total(r, o) for r in rs]
        if max(vals) < 0.005:
            continue
        cells = [cell(rs, f"{k}|{o}")[0] for k in kinds]
        summary[a][o] = statistics.mean(vals)
        print(f"   {o:<20}" + "".join(f"{v:>12.3f}" for v in cells)
              + f"{statistics.mean(vals):>10.3f}   {min(vals):.3f}-{max(vals):.3f}")
    kd = defaultdict(list)
    for r in rs:
        for k, v in r["kernel_us_per_call"].items():
            kd[k].append(v)
    print("   kernel time by activity:")
    for k, v in sorted(kd.items(), key=lambda kv: -sum(kv[1])):
        m = sum(v) / len(rs)
        if m >= 0.05:
            print(f"      {k:<52} {m:.3f}")
    how = defaultdict(float)
    for r in rs:
        for k, v in r["owner_found_by_us_per_call"].items():
            how[k] += v / len(rs)
    chk = defaultdict(float)
    for r in rs:
        for k, v in r.get("rule_check_us_per_call", {}).items():
            chk[k] += v / len(rs)
    agree = chk["agree"] / (chk["agree"] + chk["disagree"]) * 100 if chk else float("nan")
    print("   owner found by: " + ", ".join(f"{k} {v:.2f}" for k, v in sorted(how.items(), key=lambda kv: -kv[1]))
          + f"; rule agrees with named frames {agree:.0f}%")
    tops = defaultdict(float)
    for r in rs:
        for fn, v in r["top"].get("own code|UE operation", []):
            tops[fn] += v / len(rs)
    print("   UE operation, top functions (ns per call):")
    for fn, v in sorted(tops.items(), key=lambda kv: -kv[1])[:6]:
        print(f"      {v * 1000:6.1f}  {fn[:100]}")
    print()
json.dump(summary, open(os.path.join(d, "cycles-summary.json"), "w"), indent=1)
