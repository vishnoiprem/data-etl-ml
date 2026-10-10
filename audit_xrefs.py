#!/usr/bin/env python3
"""Audit cross-references in lecture files. Walks the current working directory."""
import os, re, sys

# collect all .md files in cwd
all_md = []
for dirpath, dirs, files in os.walk('.'):
    for f in files:
        if f.endswith('.md'):
            all_md.append(os.path.join(dirpath, f))

# existing files set (relative to cwd)
existing = {os.path.relpath(p, '.').replace('\\', '/') for p in all_md}

# Cross-ref patterns
patterns = [
    re.compile(r'\[[^\]]+\]\(([^)]+\.md)\)'),
    re.compile(r'`?(s\d{2}/L\d+-\d+-[^`)\s]+\.md)`?'),
    re.compile(r'\(([^)]*L\d+-\d+-[^)]*\.md)\)'),
]

broken = []
all_refs = []

for f in all_md:
    with open(f) as fh:
        text = fh.read()
    for pat in patterns:
        for m in pat.finditer(text):
            ref = m.group(1)
            if ref.startswith('http'):
                continue
            all_refs.append((f, ref))
            d = os.path.dirname(os.path.relpath(f, '.').replace('\\', '/'))
            cand = os.path.normpath(os.path.join(d, ref)).replace('\\', '/')
            if cand in existing:
                continue
            cand2 = os.path.normpath(ref).replace('\\', '/')
            if cand2 in existing:
                continue
            broken.append((os.path.relpath(f, '.'), ref))

seen = set()
uniq = []
for src, ref in broken:
    key = (src, ref)
    if key in seen:
        continue
    seen.add(key)
    uniq.append((src, ref))

print(f"Total cross-references found: {len(all_refs)}")
print(f"Unique references: {len(set(r for _, r in all_refs))}")
print(f"Broken references: {len(uniq)}")
print()
for src, ref in uniq:
    print(f"  {src} -> {ref}")
