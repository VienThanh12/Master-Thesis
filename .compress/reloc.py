#!/usr/bin/env python3
"""Move a body block into the appendices and fix every reference prefix that points at it.

Usage:  .reloc.py FILE 'start-line-prefix' 'end-line-prefix' 'anchor-line-prefix' [--demote]

The block runs from the first line starting with `start-line-prefix` up to (not including) the
first later line starting with `end-line-prefix`. It is inserted immediately before the first
line starting with `anchor-line-prefix`, which must sit inside the appendices environment.

A relocated \\section or \\chapter becomes \\appendix{Title\\label{...}}. With --demote the
block's \\subsection commands become \\section, which keeps the heading hierarchy sensible when a
former section becomes an appendix.

Every \\label defined inside the block is collected, and every reference to one of those labels
anywhere in the document has its prefix rewritten to Appendix. Anything the rewriter cannot
classify is printed so it can be fixed by hand.
"""
import re
import sys

path, start_pat, end_pat, anchor_pat = sys.argv[1:5]
demote = '--demote' in sys.argv[5:]

lines = open(path).read().split('\n')


def first(pred, frm=0):
    for i in range(frm, len(lines)):
        if pred(i):
            return i
    raise SystemExit(f'pattern not found in {path}')


s = first(lambda i: lines[i].startswith(start_pat))
e = first(lambda i: lines[i].startswith(end_pat), s + 1)
anchor = first(lambda i: lines[i].startswith(anchor_pat))
if s <= anchor < e:
    raise SystemExit('anchor sits inside the block being moved')

block = lines[s:e]
labels = set(re.findall(r'\\label\{([^}]*)\}', '\n'.join(block)))

forced = None
for a in sys.argv[5:]:
    if a.startswith('--title='):
        forced = a.split('=', 1)[1]

head = block[0]
if forced is not None:
    block = [f'\\appendix{{{forced}}}'] + block
    m = None
else:
    m = re.match(r'\\(?:chapter|section|subsection)\*?\{(.*)\}\s*$', head)
if m:
    title = m.group(1)
    # a trailing \label{...} inside the braces is kept, one outside is folded in
    if '\\label' not in title:
        nxt = re.match(r'\s*\\label\{([^}]*)\}\s*$', block[1]) if len(block) > 1 else None
        if nxt:
            title += f'\\label{{{nxt.group(1)}}}'
            block = [block[0]] + block[2:]
        else:
            inline = re.match(r'(.*?)\\label\{([^}]*)\}(.*)', head)
            if inline:
                title = inline.group(1) + inline.group(3) + f'\\label{{{inline.group(2)}}}'
    block[0] = f'\\appendix{{{title}}}'
elif forced is None:
    raise SystemExit(f'block does not open with a chapter or section: {head[:60]}')

if demote:
    block = [re.sub(r'^\\subsection\{', r'\\section{', b) for b in block]

rest = lines[:s] + lines[e:]
# the anchor index shifts once the block is lifted out
shift = anchor - (e - s) if anchor > s else anchor
out = rest[:shift] + block + [''] + rest[shift:]

text = '\n'.join(out)
unresolved = []
for lab in sorted(labels):
    q = re.escape(lab)
    text = re.sub(r'(?:Section|Chapter|Subsection)s?~\\ref\{' + q + r'\}', f'Appendix~\\\\ref{{{lab}}}', text)
    text = re.sub(r'\\S\\ref\{' + q + r'\}', f'Appendix~\\\\ref{{{lab}}}', text)
    for mm in re.finditer(r'(\S{0,24})\\(?:page)?ref\{' + q + r'\}', text):
        before = mm.group(1)
        if 'Appendix' not in before and 'appendix' not in before:
            unresolved.append((lab, mm.group(0)))

open(path, 'w').write(text)
print(f'moved {e - s} lines ({len(labels)} labels) before {anchor_pat[:40]!r}')
print('  labels:', ', '.join(sorted(labels)) or 'none')
if unresolved:
    print('  CHECK these reference sites by hand:')
    for lab, ctx in unresolved:
        print(f'    {lab}: ...{ctx}')
