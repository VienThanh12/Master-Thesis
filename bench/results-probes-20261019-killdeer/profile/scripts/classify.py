#!/usr/bin/env python3
"""Attributes perf samples to parts of a call. Reads `perf script --inline -F tid,time,period,ip,sym,dso`
on stdin. Each sample is assigned a kind (own code, allocator, kernel) and an owner (UE operation,
shard queue, reply handle, service dispatch, harness). Disposable diagnostic, not a reported result.

usage: perf script ... | classify.py <bench.json> <label> <out.json> [kallsyms]
"""
import bisect
import json
import re
import sys
from collections import Counter, defaultdict

bench_path, label, out_path = sys.argv[1:4]
kallsyms = sys.argv[4] if len(sys.argv) > 4 else None

KADDR = 0xffff800000000000
kaddrs, knames = [], []
if kallsyms:
    for line in open(kallsyms):
        parts = line.split()
        if len(parts) >= 3 and parts[1] in "tTwW":
            kaddrs.append(int(parts[0], 16))
            knames.append(parts[2])
    order = sorted(range(len(kaddrs)), key=kaddrs.__getitem__)
    kaddrs = [kaddrs[i] for i in order]
    knames = [knames[i] for i in order]


def kname(addr):
    if not kaddrs:
        return "?"
    i = bisect.bisect_right(kaddrs, addr) - 1
    return knames[i] if i >= 0 else "?"


import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from classify_rules import (ALLOC, GLUE, HARNESS, QUEUE, REPLY, SYSCALL_WRAPPERS, WAIT,
                            WAKE, has, owner_of, parse, role_hint)


samples = list(parse(sys.stdin))
is_cpp = any("pf-cpp-" in dso for s in samples[:200] for _, _, dso in s["frames"])
# Cycle-sampled profiles record periods in cycles. PERIOD_SCALE converts them to nanoseconds.
scale = float(os.environ.get("PERIOD_SCALE", "1"))
for s in samples:
    s["period"] = int(s["period"] * scale)

# Thread roles by majority over each thread's samples that carry role evidence.
votes = defaultdict(Counter)
for s in samples:
    hint = role_hint([f"{sym} ({dso})" for _, sym, dso in s["frames"]])
    if hint:
        votes[s["tid"]][hint] += 1
roles = {tid: c.most_common(1)[0][0] for tid, c in votes.items()}

ns = defaultdict(int)            # (kind, owner) -> ns
kernel_detail = defaultdict(int)  # (owner, kernel function group) -> ns
role_ns = defaultdict(int)
top = defaultdict(Counter)        # (kind, owner) -> leaf function -> ns
how = Counter()                   # how each sample's owner was found -> ns
check = Counter()                 # thread-and-direction rule against named frames -> ns
times = []
total = 0
for s in samples:
    role = roles.get(s["tid"], "unknown")
    if not s["frames"]:
        kind, owner, leaf = "unwind failed", "unknown", "?"
        how["no frames"] += s["period"]
    else:
        texts = [f"{sym} ({dso})" for _, sym, dso in s["frames"]]
        leaf_addr = s["frames"][0][0]
        kind = "kernel" if leaf_addr >= KADDR else None
        owner = None
        start = 0
        kfuncs = []
        if kind == "kernel":
            while start < len(s["frames"]) and s["frames"][start][0] >= KADDR:
                start += 1
            kfuncs = [kname(a) for a, _, _ in s["frames"][:start]]
        elif has(texts[0], *SYSCALL_WRAPPERS):
            kind = "kernel"
        for t in texts[start:]:
            if kind is None and has(t, *ALLOC):
                kind = "allocator"
                continue
            # In the C++ build the queue's kernel calls come from inside libpthread, so a direct
            # syscall() is the reply handle's futex (std::promise and std::future).
            o = "reply handle" if is_cpp and "syscall (" in t else owner_of(t)
            if o:
                owner = o
                break
        if kind is None:
            kind = "own code"
        joined_all = " ".join(kfuncs + texts)
        rule = None
        direction = "wait" if has(joined_all, *WAIT) else "wake" if has(joined_all, *WAKE) else None
        if direction and role in ("sender", "worker"):
            rule = {("sender", "wake"): "shard queue", ("sender", "wait"): "reply handle",
                    ("worker", "wake"): "reply handle", ("worker", "wait"): "shard queue"}[(role, direction)]
        if owner:
            how["named frame"] += s["period"]
            if rule and owner in ("shard queue", "reply handle"):
                check["agree" if rule == owner else "disagree"] += s["period"]
                # Rust frames beyond a parked thread are often mis-unwound. Outside lock contention a
                # Rust worker only waits on its queue and wakes its sender, and a sender the reverse.
                contended = has(joined_all, "lock_contended", "Mutex>::spin", "5Mutex4spin",
                                "__lll_lock_wait", "pthread_mutex_lock")
                if not is_cpp and rule != owner and not contended:
                    how["named frame overruled"] += s["period"]
                    owner = rule
        else:
            # Handoff code shared by queue and reply: a sender only wakes its worker through the
            # queue and only sleeps on its reply, and a worker does the reverse.
            if rule:
                owner = rule
                how["thread and direction"] += s["period"]
            else:
                owner = "handoff, unresolved" if has(joined_all, *(WAKE + WAIT), "SyncWaker", "Mutex4spin",
                                                     "7Context", "syscall") else "unknown"
                how["unresolved"] += s["period"]
        if kind == "kernel":
            joined = " ".join(kfuncs)
            if not kfuncs:
                group = "entering or leaving the kernel"
            elif "futex_wake" in joined or "try_to_wake_up" in joined or "wake_up_q" in joined:
                group = "waking a thread"
            elif "futex_wait" in joined or "schedule" in joined:
                group = "putting a thread to sleep"
            elif "futex" in joined:
                group = "other futex"
            elif kaddrs:
                group = "other kernel"
            else:
                group = "kernel (unnamed)"
            kernel_detail[(owner, group)] += s["period"]
        leaf = s["frames"][start][1] if start < len(s["frames"]) else s["frames"][0][1]
        if kind == "kernel" and kfuncs:
            leaf = kname(leaf_addr)
    top[(kind, owner)][leaf] += s["period"]
    ns[(kind, owner)] += s["period"]
    role_ns[role] += s["period"]
    times.append(s["time"])
    total += s["period"]

bench = json.load(open(bench_path))
window_s = max(times) - min(times)
calls = bench["throughput_ops_s"] * window_s
per_call = lambda v: v / calls / 1000.0  # ns per call -> us per call

owners = ["UE operation", "shard queue", "reply handle", "service dispatch", "harness",
          "handoff, unresolved", "unknown"]
kinds = ["own code", "allocator", "kernel", "unwind failed"]
result = {
    "label": label,
    "throughput_ops_s": bench["throughput_ops_s"],
    "window_s": window_s,
    "samples_ns_total": total,
    "us_per_call_total": per_call(total),
    "us_per_call": {f"{k}|{o}": per_call(v) for (k, o), v in ns.items()},
    "kernel_us_per_call": {f"{o}|{g}": per_call(v) for (o, g), v in kernel_detail.items()},
    "role_us_per_call": {r: per_call(v) for r, v in role_ns.items()},
    "owner_found_by_us_per_call": {h: per_call(v) for h, v in how.items()},
    "rule_check_us_per_call": {h: per_call(v) for h, v in check.items()},
    "threads": {str(t): r for t, r in roles.items()},
    "top": {f"{k}|{o}": [(f, per_call(v)) for f, v in c.most_common(6)] for (k, o), c in top.items()},
}
json.dump(result, open(out_path, "w"), indent=1)

print(f"== {label}: {bench['throughput_ops_s'] / 1e3:.1f} kops/s, window {window_s:.2f} s, "
      f"{per_call(total):.2f} us of CPU per finished call ==")
print(f"{'owner':<18}" + "".join(f"{k:>16}" for k in kinds) + f"{'total':>10}")
for o in owners:
    row = [per_call(ns.get((k, o), 0)) for k in kinds]
    if sum(row) < 0.005:
        continue
    print(f"{o:<18}" + "".join(f"{v:>16.3f}" for v in row) + f"{sum(row):>10.3f}")
print("kernel time by what the kernel was doing (us per call):")
for (o, g), v in sorted(kernel_detail.items(), key=lambda kv: -kv[1]):
    if per_call(v) >= 0.01:
        print(f"    {o:<18} {g:<28} {per_call(v):.3f}")
print("by thread: " + ", ".join(f"{r} {per_call(v):.2f}" for r, v in sorted(role_ns.items()))
      + f"  ({sum(1 for r in roles.values() if r == 'worker')} workers, "
      f"{sum(1 for r in roles.values() if r == 'sender')} senders identified)")
print("owner found by: " + ", ".join(f"{h} {per_call(v):.2f}" for h, v in how.most_common()))
if check:
    agree = check["agree"] / (check["agree"] + check["disagree"]) * 100
    print(f"thread-and-direction rule matches the named frame for {agree:.1f}% of the queue and reply "
          f"time where both are known ({per_call(check['agree'] + check['disagree']):.2f} us per call)")
if len(sys.argv) > 5:
    for key in sys.argv[5].split(","):
        print(f"  top in {key}:")
        for fn, v in top.get(tuple(key.split("|")), Counter()).most_common(8):
            print(f"     {per_call(v) * 1000:7.1f} ns  {fn[:120]}")
