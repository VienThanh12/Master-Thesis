#!/usr/bin/env python3
"""Re-names every frame in our own binary with addr2line -i, which resolves the inlined frames that
perf prints as ??. Reads `perf script --inline -F tid,time,period,ip,sym,symoff,dso` on stdin and
writes the same layout without offsets, ready for classify.py. Disposable diagnostic.

usage: perf script ... | resolve_inline.py <binary> > resolved.txt
"""
import re
import subprocess
import sys

binary = sys.argv[1]

symaddr = {}
for line in subprocess.run(["nm", "-S", "--defined-only", binary], capture_output=True, text=True).stdout.splitlines():
    parts = line.split()
    if len(parts) == 4 and parts[2] in "tTwW":
        symaddr.setdefault(parts[3], (int(parts[0], 16), int(parts[1], 16)))
lo = min(a for a, _ in symaddr.values())
hi = max(a + s for a, s in symaddr.values())
is_pie = "DYN" in subprocess.run(["readelf", "-h", binary], capture_output=True, text=True).stdout

frame_re = re.compile(r"^\t\s*([0-9a-f]+) (.*) \((.*)\)$")
lines = sys.stdin.read().splitlines()

base = 0
if is_pie:
    base = None
    for line in lines:
        m = frame_re.match(line)
        if not m or m.group(3) != binary:
            continue
        mm = re.match(r"(.+)\+0x([0-9a-f]+)$", m.group(2))
        if mm and mm.group(1) in symaddr:
            base = int(m.group(1), 16) - (symaddr[mm.group(1)][0] + int(mm.group(2), 16))
            break
    if base is None:
        sys.exit("resolve_inline: could not find the load base")


def ours(addr):
    return lo <= addr - base < hi


# Split into samples: a header line, then frame lines. Within a sample, the first address group is
# the sampled instruction and every later group is a return address, looked up one byte earlier.
samples = []
cur = None
for line in lines:
    m = frame_re.match(line)
    if m:
        if cur is not None:
            cur[1].append((int(m.group(1), 16), m.group(2), m.group(3)))
        continue
    if cur is not None:
        samples.append(cur)
    cur = (line, []) if line.strip() else None
if cur is not None:
    samples.append(cur)

queries = {}
for _, frames in samples:
    first = frames[0][0] if frames else None
    for addr, _, _ in frames:
        if ours(addr):
            queries.setdefault(addr - base if addr == first else addr - base - 1, None)
keys = list(queries)
res = subprocess.run(["addr2line", "-i", "-f", "-C", "-a", "-e", binary],
                     input="".join(f"{k:x}\n" for k in keys), capture_output=True, text=True).stdout.splitlines()
chains = {}
i = 0
k = -1
while i < len(res):
    if res[i].startswith("0x"):
        k += 1
        chains[keys[k]] = []
        i += 1
        continue
    chains[keys[k]].append(res[i])
    i += 2

out = sys.stdout
for header, frames in samples:
    out.write(header + "\n")
    first = frames[0][0] if frames else None
    done = set()
    for addr, sym, dso in frames:
        if ours(addr):
            key = addr - base if addr == first else addr - base - 1
            names = chains.get(key) or []
            if names and names[0] != "??":
                if addr in done:
                    continue
                done.add(addr)
                for name in names:
                    out.write(f"\t{addr:16x} {name} ({binary})\n")
                continue
        plain = re.sub(r"\+0x[0-9a-f]+$", "", sym)
        out.write(f"\t{addr:16x} {plain} ({dso})\n")
    out.write("\n")
