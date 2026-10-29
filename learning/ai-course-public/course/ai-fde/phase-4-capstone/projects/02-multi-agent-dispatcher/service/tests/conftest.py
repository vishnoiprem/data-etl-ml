"""conftest.py — make the sibling `service/` dir + Phase 3 + Project 1 importable for pytest."""
import sys
from pathlib import Path

# Project 2's own service/ dir
SVC = Path(__file__).parent.parent
if str(SVC) not in sys.path:
    sys.path.insert(0, str(SVC))

# Project 1's MCP server (sibling in phase-4-capstone/projects/)
_PROJ1 = SVC.parent.parent / "01-mcp-drafter" / "service"
if str(_PROJ1) not in sys.path:
    sys.path.insert(0, str(_PROJ1))

# Phase 3's service (sibling in course/ai-fde/ — 4 levels up from project dir)
# SVC = .../02-multi-agent-dispatcher/service
# SVC.parent = .../02-multi-agent-dispatcher
# SVC.parent.parent = .../projects
# SVC.parent.parent.parent = .../phase-4-capstone
# SVC.parent.parent.parent.parent = .../ai-fde  <-- HERE
_PHASE3 = SVC.parent.parent.parent.parent / "phase-2-core-build" / "service"
if str(_PHASE3) not in sys.path:
    sys.path.insert(0, str(_PHASE3))