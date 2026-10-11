import os, re
from collections import defaultdict

root = '.'
issues = []
for r, dirs, files in os.walk(root):
    if any(s in r for s in ['.git', '__pycache__', 'node_modules', '.venv']):
        continue
    for f in files:
        if f != 'README.md':
            continue
        path = os.path.join(r, f)
        try:
            with open(path) as fh:
                text = fh.read()
        except Exception:
            continue
        for m in re.finditer(r'\]\(([^)]+)\)', text):
            l = m.group(1)
            if l.startswith(('http://', 'https://', '#', 'mailto:')):
                continue
            target = l.split('#')[0]
            if not target:
                continue
            base = os.path.dirname(path)
            full = os.path.join(base, target)
            if not os.path.exists(full):
                issues.append((path, 'broken-link', l))
        for marker in [r'\bTODO\b', r'\bFIXME\b', r'\bTBD\b', r'\bXXX\b', r'\[insert', r'\[fill', r'placeholder', r'lorem']:
            if re.search(marker, text, re.IGNORECASE):
                issues.append((path, 'placeholder', marker))
        if not re.search(r'^# ', text, re.MULTILINE):
            issues.append((path, 'no-h1', ''))

print(f"Total issues: {len(issues)}")
by_file = defaultdict(list)
for path, kind, detail in issues:
    by_file[path].append((kind, detail))
for path, lst in sorted(by_file.items()):
    print(path)
    for k, d in lst:
        print(f"  - {k}: {d}")
