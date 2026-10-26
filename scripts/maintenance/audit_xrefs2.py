#!/usr/bin/env python3
"""Verify all internal L0X-Y-*.md cross-references in lecture bodies exist."""
import os, re, sys

LECTURE_RE = re.compile(r'L\d+-\d+-[a-z0-9-]+\.md')
# Matches: `L9-2-foo.md` or `S9-.../L9-1-foo.md`
BARE_RE = re.compile(r'`((?:s\d{2}-[\w-]+/)?L\d+-\d+-[\w-]+\.md)`', re.IGNORECASE)

# Build set of existing lecture files
existing = set()
for d in os.listdir('.'):
    if d.startswith('s') and os.path.isdir(d):
        for f in os.listdir(d):
            if re.match(r'L\d+-\d+-.+\.md$', f):
                existing.add(f)

print(f"Existing lectures: {len(existing)}")

# Walk all L*.md and check refs
broken = []
for dirpath, dirs, files in os.walk('.'):
    for f in files:
        if not re.match(r'L\d+-\d+-.+\.md$', f):
            continue
        full = os.path.join(dirpath, f)
        with open(full) as fh:
            text = fh.read()
        for m in BARE_RE.finditer(text):
            ref = m.group(1)
            # extract just the L...md part
            base = ref.split('/')[-1]
            if base not in existing:
                broken.append((full, ref))

# Dedupe
seen = set()
uniq = []
for src, ref in broken:
    k = (src, ref)
    if k in seen:
        continue
    seen.add(k)
    uniq.append((src, ref))

print(f"Broken internal cross-references: {len(uniq)}")
for src, ref in uniq:
    print(f"  {src} -> {ref}")
