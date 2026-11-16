"""Make `src/trade_sourcing_ai` and the repo root importable from any cwd.

The shared trade-finder modules (`find_opportunities.py`, `verify_suppliers.py`,
`demand_in.py`) live outside this project, so the repo's `projects/` directory
has to be on the path as well.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "src"
TRADE_FINDER = HERE.parent / "realtime-stock-pipeline" / "trade-finder"

for path in (SRC, TRADE_FINDER):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
