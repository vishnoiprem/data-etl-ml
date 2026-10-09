"""
scan_fde.py — single for-loop scan of the entire FDE course (v2).

Refinements over v1:
  - The phase-leak regex now requires the reference to be a DIRECTORY mention,
    not a code-path like `phase-2-core-build/service/app.py` (which is
    legitimate; Phase 3's hardened code lives there).
  - ROLE_MISMATCH now allows `system` (the internal service role).
"""
from __future__ import annotations

import ast
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path("/Users/vishnoiprem/PycharmProjects/data-etl-ml/ai-course-public/course/ai-fde")
if not ROOT.exists():
    sys.exit(f"root not found: {ROOT}")

findings: dict[str, list[str]] = defaultdict(list)


def bug(category: str, path: Path, message: str) -> None:
    findings[category].append(f"  {path.relative_to(ROOT)}  ->  {message}")


# 1. AST-parse every .py
print("[1/6] AST-parsing every .py file ...", flush=True)
py_files = sorted(p for p in ROOT.rglob("*.py") if "/__pycache__/" not in str(p))
print(f"  found {len(py_files)} python files")
for p in py_files:
    src = p.read_text(encoding="utf-8", errors="replace")
    try:
        ast.parse(src, filename=str(p))
    except SyntaxError as e:
        bug("PY_SYNTAX", p, f"line {e.lineno}: {e.msg}")

# 2. Cross-reference check
print("[2/6] Checking cross-references in every .md ...", flush=True)
md_files = sorted(p for p in ROOT.rglob("*.md"))
print(f"  found {len(md_files)} markdown files")
for m in md_files:
    text = m.read_text(encoding="utf-8", errors="replace")
    for ref in re.findall(r"\]\(([^)]+)\)", text):
        ref = ref.split("#", 1)[0].strip("\"'")
        if not ref or ref.startswith(("http", "mailto:", "javascript:", "/")):
            continue
        candidate = (m.parent / ref).resolve()
        if not candidate.exists():
            alt = (ROOT / ref).resolve()
            if not alt.exists():
                bug("MD_BROKEN_LINK", m, f"link target missing: {ref!r}")

# 3. Phase-leak check (refined)
# Only flag phase-2-core-build references that are:
#   (a) preceded by "Phase 3" (case-insensitive) and
#   (b) NOT followed by `/service/`, `/shared/`, `/tests/` (which are legitimate
#       code paths to the existing Phase 2-3 service code).
print("[3/6] Checking phase-leaks (refined regex) ...", flush=True)
leak_re = re.compile(
    r"[Pp]hase\s*3\b[^\n]{0,80}phase-2-core-build(?!/(?:service|shared|tests|consulting/technical))"
)
for m in md_files:
    text = m.read_text(encoding="utf-8", errors="replace")
    for hit in leak_re.findall(text):
        bug("PHASE_LEAK", m, f"Phase 3 doc references phase-2-core-build: {hit!r}")

# 4. Role / endpoint consistency
print("[4/6] Checking role + endpoint consistency ...", flush=True)
mcp_yaml_path = ROOT / "phase-4-capstone/projects/01-mcp-drafter/service/mcp_policies.yaml"
mcp_py_path = ROOT / "phase-4-capstone/projects/01-mcp-drafter/service/mcp_server.py"

# Only look at the `roles:` block of the YAML
yaml_roles: set[str] = set()
if mcp_yaml_path.exists():
    yaml_text = mcp_yaml_path.read_text()
    in_roles = False
    for line in yaml_text.splitlines():
        if re.match(r"^roles:\s*$", line):
            in_roles = True
            continue
        if in_roles:
            if re.match(r"^[a-z_]+:\s*$", line) and not line.startswith(" "):
                in_roles = False
                continue
            m = re.match(r"^\s{2}([a-z_]+):\s*$", line)
            if m:
                yaml_roles.add(m.group(1))
    print(f"  YAML roles: {sorted(yaml_roles)}")

# Only look at the `_DEFAULT_POLICIES["roles"]` block of the PY
py_roles: set[str] = set()
if mcp_py_path.exists():
    py_text = mcp_py_path.read_text()
    # The roles block in the dict is "cs_junior", "cs_senior", etc.
    # The functional role names are: cs_junior, cs_senior, ops, it, system
    # These map to the customer story in a comment.
    # We accept both: functional names (cs_junior/cs_senior/ops/it/system)
    # OR customer names (cs_mei/cs_senior/ops_sarah/it_daniel/system).
    py_roles = set(re.findall(
        r'^\s+"(cs_[a-z_]+|ops|it|system)":\s*\{',
        py_text, re.MULTILINE,
    ))
    print(f"  PY  roles (functional or customer names): {sorted(py_roles)}")

# The customer story uses: cs_mei, cs_senior, ops_sarah, it_daniel, system
# The functional names: cs_junior, cs_senior, ops, it, system
# Both are valid; the comment in mcp_server.py maps one to the other.
allowed_role_sets = [
    {"cs_mei", "cs_senior", "ops_sarah", "it_daniel", "system"},
    {"cs_junior", "cs_senior", "ops", "it", "system"},
]
if yaml_roles and yaml_roles not in allowed_role_sets:
    bug("ROLE_MISMATCH", mcp_yaml_path,
        f"YAML roles {sorted(yaml_roles)} not in either allowed set")
if py_roles and py_roles not in allowed_role_sets:
    bug("ROLE_MISMATCH", mcp_py_path,
        f"PY roles {sorted(py_roles)} not in either allowed set")

# Endpoint count
app_py = (ROOT / "phase-2-core-build/service/app.py").read_text()
endpoint_re = re.compile(r"^@app\.(get|post|put|delete)\([\"'](/[a-z_/]+)[\"']", re.MULTILINE)
eps = endpoint_re.findall(app_py)
print(f"  Phase 2/3 endpoints: {len(eps)} ({[e for _, e in eps]})")
if len(eps) != 9:
    bug("ENDPOINT_COUNT", ROOT / "phase-2-core-build/service/app.py",
        f"app.py has {len(eps)} endpoints; docstring claims 9")

# 5. Run all test_*.py files
print("[5/6] Running every test_*.py file ...", flush=True)
test_files = sorted(p for p in ROOT.rglob("test_*.py") if "/__pycache__/" not in str(p))
print(f"  found {len(test_files)} test files")
for tf in test_files:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(tf), "-q", "--tb=line", "--no-header"],
        capture_output=True, text=True, timeout=60,
        cwd=str(ROOT.parent),
    )
    if result.returncode != 0:
        combined = (result.stdout + result.stderr).strip().splitlines()
        last = " | ".join(combined[-3:])[:300] if combined else "(no output)"
        bug("TEST_FAIL", tf, f"exit {result.returncode} | {last}")

# 6. Test counts
print("[6/6] Verifying test counts ...", flush=True)
p2_dir = ROOT / "phase-2-core-build/service/tests"
p2_test_files = list(p2_dir.glob("test_*.py"))
p4_test_files = []
for proj in (ROOT / "phase-4-capstone/projects").iterdir():
    if proj.is_dir():
        p4_test_files.extend(p for p in proj.rglob("test_*.py") if "/__pycache__/" not in str(p))


def count_test_fns(p: Path) -> int:
    return len(re.findall(r"^def\s+(test_[a-z0-9_]+)", p.read_text(), re.MULTILINE))


p2_n = sum(count_test_fns(p) for p in p2_test_files)
p4_n = sum(count_test_fns(p) for p in p4_test_files)
print(f"  Phase 2 test files: {len(p2_test_files)} | functions: {p2_n}")
print(f"  Phase 4 test files: {len(p4_test_files)} | functions: {p4_n}")
print(f"  TOTAL: {p2_n + p4_n}")

# ---------- report ----------
print()
print("=" * 80)
print("REPORT")
print("=" * 80)
total = 0
for cat, items in sorted(findings.items()):
    print(f"\n[{cat}]  {len(items)} issue(s)")
    for it in items:
        print(it)
    total += len(items)
print(f"\nTOTAL ISSUES: {total}")
if total == 0:
    print("\nAll clear — Phase 5 can proceed.")
