#!/usr/bin/env python3
"""Top leaf functions per owner and kind, averaged over the cycle-sampled repeats. Disposable."""
import glob
import json
import os
from collections import defaultdict

d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
for arm in ("cpp-deque", "rust-channel"):
    rs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(d, f"cprof-{arm}-[789].json")))]
    print(f"== {arm}")
    for key in ("own code|reply handle", "allocator|reply handle", "own code|shard queue",
                "allocator|shard queue", "own code|service dispatch"):
        tops = defaultdict(float)
        for r in rs:
            for fn, v in r["top"].get(key, []):
                tops[fn] += v / len(rs)
        if not tops:
            continue
        print(f"  {key}")
        for fn, v in sorted(tops.items(), key=lambda kv: -kv[1])[:5]:
            print(f"     {v * 1000:6.1f} ns  {fn[:110]}")
