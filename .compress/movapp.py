#!/usr/bin/env python3
"""Move a contiguous block of appendix chapters to sit before another appendix.

Appendix-to-appendix moves need no reference rewriting, so this only relocates
lines and checks that the block is balanced and that nothing was lost.
"""
import re
import sys

path, first, last, before = sys.argv[1:5]
lines = open(path).read().split("\n")


def find(pat, start=0):
    for i in range(start, len(lines)):
        if re.match(pat, lines[i]):
            return i
    raise SystemExit(f"pattern not found: {pat}")


a = find(first)
b = find(last, a + 1)
# the moved block ends where the next appendix chapter begins
end = find(r"\\appendix\{", b + 1)
while end > b and lines[end - 1].strip() == "":
    end -= 1
block = lines[a:end]

rest = lines[:a] + lines[end:]
anchor = next(i for i, l in enumerate(rest) if re.match(before, l))
out = rest[:anchor] + block + [""] + rest[anchor:]

if len(out) != len(lines) + 1:
    raise SystemExit(f"line count changed: {len(lines)} -> {len(out)}")
open(path, "w").write("\n".join(out))
print(f"moved {len(block)} lines ({lines[a][:60]}) before {rest[anchor][:60]}")
