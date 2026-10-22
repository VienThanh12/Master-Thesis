#!/usr/bin/env python3
"""Per-request allocations by the difference of two run lengths (allocs.jsonl from run.sh)."""
import json
import os
import sys

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "allocs.jsonl")
rows = [json.loads(l) for l in open(path)]
by = {}
for r in rows:
    v, h, n = r["label"].split("|")
    by[(v, h, int(n))] = {b[0]: b[1:] for b in r["buckets"]}
producers = 7
for h in ("bench", "pipeline"):
    print(f"=== {h}: per request, difference of 120000 and 20000 ops per sender ===")
    for v in ("cpp-stock", "cpp-ring", "rust-stock", "rust-oneshot", "rust-mutexq"):
        a, b = by[(v, h, 20000)], by[(v, h, 120000)]
        d_ops = (120000 - 20000) * producers
        tot = [0.0, 0.0, 0.0]
        byte_alloc = byte_cross = 0.0
        lines = []
        for size in sorted(set(a) | set(b)):
            x = [(b.get(size, [0, 0, 0])[i] - a.get(size, [0, 0, 0])[i]) / d_ops for i in range(3)]
            if max(abs(t) for t in x) < 0.01:
                continue
            lines.append(f"      {size:>5}-{size + 15:<5} B  alloc {x[0]:5.2f}  freed same thread {x[1]:5.2f}  "
                         f"freed by other thread {x[2]:5.2f}")
            for i in range(3):
                tot[i] += x[i]
            byte_alloc += x[0] * (size + 8)
            byte_cross += x[2] * (size + 8)
        print(f"  {v:13} allocs {tot[0]:4.2f}/req  same-thread frees {tot[1]:4.2f}  cross-thread frees {tot[2]:4.2f}"
              f"  ~{byte_alloc:5.0f} B allocated, ~{byte_cross:5.0f} B freed across threads")
        for l in lines:
            print(l)
    print()
