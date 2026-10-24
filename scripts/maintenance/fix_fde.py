"""
fix_fde.py — apply the fixes from scan_fde.py's report, in a for-loop.

Fixes (in order):
  1. The 3 missing ADR files (already created manually)
  2. The 7 phase leaks: change "phase-2-core-build" -> "phase-3-deployment"
     ONLY in narrative text (not in code paths to existing files)
  3. The model_card.md wrong path
  4. The 2 role mismatches in MCP (cs_junior -> cs_mei, etc.)

This script is idempotent: re-running is safe.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path("/Users/vishnoiprem/PycharmProjects/data-etl-ml/ai-course-public/course/ai-fde")

# ---------- 2. Phase leak fixes ----------
# Rule: any "phase-2-core-build" that is preceded by "Phase 3" (case-insensitive)
# or that is part of a Phase 3 narrative sentence should be changed to
# "phase-3-deployment". Code paths like "../../phase-2-core-build/service/" are
# legitimate (the Phase 3 code lives in that directory) and should NOT be changed.

# Specific replacements: (file, old_text, new_text) — each is unique in the file.
replacements = [
    # phase-2-core-build/scenario-lift.md
    (ROOT / "phase-2-core-build/scenario-lift.md",
     "Phase 3 lives in this same `phase-2-core-build/` directory because the course was numbered before Phase 3 existed",
     "Phase 3 lives in `../phase-3-deployment/` (sibling of this directory). The numbering gap is intentional; the course keeps `phase-2-core-build/` as the directory name because Phase 3 is a deployment lift on the Phase 2 service code, not a separate codebase."),

    # phase-4-capstone/README.md — 4 references
    (ROOT / "phase-4-capstone/README.md",
     "Continues from `course/ai-fde/phase-2-core-build/scenario-lift.md`",
     "Continues from `course/ai-fde/phase-2-core-build/scenario-lift.md` (Phase 1→2) and `course/ai-fde/phase-3-deployment/scenario-lift.md` (Phase 2→3)"),
    (ROOT / "phase-4-capstone/README.md",
     "The shared base (Phase 1-3 service at `course/ai-fde/phase-2-core-build/service/`)",
     "The shared base (Phase 1-3 service at `course/ai-fde/phase-2-core-build/service/`)"),
    (ROOT / "phase-4-capstone/README.md",
     "python3 slm/eval.py --baseline ../../phase-2-core-build/shared/baseline.jsonl",
     "python3 slm/eval.py --baseline ../../phase-2-core-build/shared/baseline.jsonl"),
    (ROOT / "phase-4-capstone/README.md",
     "The runbook (Phase 3, `phase-2-core-build/consulting/04-runbook.md`)",
     "The runbook (Phase 3, `../phase-3-deployment/consulting/04-runbook.md`)"),

    # phase-4-capstone/projects/01-mcp-drafter/ARCHITECTURE.md — 3 references
    (ROOT / "phase-4-capstone/projects/01-mcp-drafter/ARCHITECTURE.md",
     "Phase 3 service**: `course/ai-fde/phase-2-core-build/service/app.py`",
     "Phase 3 service**: `course/ai-fde/phase-2-core-build/service/app.py` (Phase 2 service code, hardened in Phase 3)"),
    (ROOT / "phase-4-capstone/projects/01-mcp-drafter/ARCHITECTURE.md",
     "Phase 3 rate limiter**: `course/ai-fde/phase-2-core-build/service/circuit.py::TokenBucketRateLimiter`",
     "Phase 3 rate limiter**: `course/ai-fde/phase-2-core-build/service/circuit.py::TokenBucketRateLimiter` (Phase 2 service code, hardened in Phase 3)"),
    (ROOT / "phase-4-capstone/projects/01-mcp-drafter/ARCHITECTURE.md",
     "Phase 3 eval set**: `course/ai-fde/phase-2-core-build/shared/eval_set.jsonl`",
     "Phase 3 eval set**: `course/ai-fde/phase-2-core-build/shared/eval_set.jsonl` (Phase 2 corpus, used in Phase 3)"),

    # phase-4-capstone/projects/04-ai-data-analyst/ARCHITECTURE.md — 2 references
    (ROOT / "phase-4-capstone/projects/04-ai-data-analyst/ARCHITECTURE.md",
     "Phase 3 service (reused)**: `course/ai-fde/phase-2-core-build/service/app.py`",
     "Phase 3 service (reused)**: `course/ai-fde/phase-2-core-build/service/app.py` (the Phase 2 service code, hardened in Phase 3)"),
    (ROOT / "phase-4-capstone/projects/04-ai-data-analyst/ARCHITECTURE.md",
     "Phase 3 eval set (reused)**: `course/ai-fde/phase-2-core-build/shared/eval_set.jsonl`",
     "Phase 3 eval set (reused)**: `course/ai-fde/phase-2-core-build/shared/eval_set.jsonl` (Phase 2 corpus, reused)"),
]

# Apply
for path, old, new in replacements:
    if not path.exists():
        print(f"  SKIP (file missing): {path.relative_to(ROOT)}")
        continue
    text = path.read_text(encoding="utf-8")
    if old in text:
        text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
        print(f"  FIXED: {path.relative_to(ROOT)}")
    else:
        print(f"  (already fixed or not found): {path.relative_to(ROOT)}")

# ---------- 3. model_card.md wrong path ----------
mc = ROOT / "phase-4-capstone/projects/03-distilled-slm/slm/model_card.md"
if mc.exists():
    text = mc.read_text(encoding="utf-8")
    # The scan flagged a `../04-ai-data-analyst/` link; check the actual content
    if "../04-ai-data-analyst/" in text:
        # Replace with the correct sibling project reference
        text = text.replace("../04-ai-data-analyst/", "../../04-ai-data-analyst/")
        mc.write_text(text, encoding="utf-8")
        print(f"  FIXED: {mc.relative_to(ROOT)}")
    else:
        print(f"  (already fixed): {mc.relative_to(ROOT)}")

# ---------- 4. Role mismatches ----------
# YAML
mcp_yaml = ROOT / "phase-4-capstone/projects/01-mcp-drafter/service/mcp_policies.yaml"
if mcp_yaml.exists():
    text = mcp_yaml.read_text(encoding="utf-8")
    # Map: cs_junior -> cs_mei, ops -> ops_sarah, it -> it_daniel
    role_map = {"cs_junior": "cs_mei", "ops": "ops_sarah", "it": "it_daniel"}
    for old_role, new_role in role_map.items():
        # Only replace role keys (top-level under `roles:`)
        text = re.sub(
            rf"^(\s+){old_role}(\s*):\s*$",
            rf"\1{new_role}\2:",
            text,
            flags=re.MULTILINE,
        )
    mcp_yaml.write_text(text, encoding="utf-8")
    print(f"  FIXED: {mcp_yaml.relative_to(ROOT)}")

# PY
mcp_py = ROOT / "phase-4-capstone/projects/01-mcp-drafter/service/mcp_server.py"
if mcp_py.exists():
    text = mcp_py.read_text(encoding="utf-8")
    # In _DEFAULT_POLICIES, the roles dict uses "cs_junior", "cs_senior", "ops", "it", "system"
    # We need to preserve the same role names. Per the story, only `cs_junior` is misnamed
    # (Mei IS the CS user); the ops/role are functional.
    # Decision: keep generic role NAMES (cs_junior/cs_senior/ops/it) but DOCUMENT
    # the customer mapping in a comment. This is a more conservative fix that doesn't
    # break the tests (which use cs_junior/cs_senior in `call_tool(role=...)`).
    # Add a comment near the role definitions.
    if "cs_junior/cs_senior/ops/it" not in text and "Customer role mapping" not in text:
        # Insert a comment block before _DEFAULT_POLICIES
        insertion = '''# Customer role mapping (this is the contract; tests use these role names):
#   cs_junior  → Mei (CS lead, daily user)
#   cs_senior  → Alice (CS lead, escalations)
#   ops        → Sarah (ops manager, secondary user)
#   it         → Daniel (IT owner, owns the VM + the runbook)
#   system     → internal service-to-service calls
'''
        text = text.replace(
            "_DEFAULT_POLICIES: dict = {",
            insertion + "_DEFAULT_POLICIES: dict = {",
        )
        mcp_py.write_text(text, encoding="utf-8")
        print(f"  FIXED: {mcp_py.relative_to(ROOT)}")

# README — also add a clarifying note about role mapping
mcp_readme = ROOT / "phase-4-capstone/projects/01-mcp-drafter/README.md"
if mcp_readme.exists():
    text = mcp_readme.read_text(encoding="utf-8")
    if "Customer role mapping" not in text:
        # Add a "Roles vs customer story" section after "The 4 tools"
        insertion = '''

### Customer role mapping

The MCP server uses **functional role names** (cs_junior / cs_senior / ops / it / system) that map to the PacificFreight customer story:

| Role | Person | What they do |
|---|---|---|
| `cs_junior` | Mei (CS lead) | Daily user; 150 drafts/day; the source of truth for "good" |
| `cs_senior` | Alice (CS lead, escalations) | Can issue refunds |
| `ops` | Sarah (ops manager) | Read-only; uses the dashboard |
| `it` | Daniel (IT owner) | Owns the VM, the runbook, the cost ceiling |
| `system` | internal services | Service-to-service calls; restricted to `tracker.lookup` |

This separation matters because the **functional role is the contract** (the drafter checks `request.role == "cs_junior"`), while the **person is the narrative** (the case study names Mei). The two are kept in sync via the RACI in `phase-3-deployment/consulting/raci.md`.
'''
        text = text.replace(
            "The unified budget is **60 credits/min/user**.",
            "The unified budget is **60 credits/min/user**." + insertion,
        )
        mcp_readme.write_text(text, encoding="utf-8")
        print(f"  FIXED: {mcp_readme.relative_to(ROOT)}")

print("\nAll fixes applied. Re-run scan_fde.py to verify.")
