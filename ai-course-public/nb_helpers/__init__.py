"""nb_helpers — shared notebook utilities for the ai-course-public curriculum.

Importable from any notebook via:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path.cwd()))
    from nb_helpers import (
        display_h1, display_h2, display_box, display_kv,
        display_table, display_json, display_status,
        display_divider, display_banner, display_step,
    )
"""
from nb_helpers.rich_display import (
    display_h1, display_h2, display_h3, display_p,
    display_box, display_kv, display_table, display_json,
    display_status, display_divider, display_banner, display_step,
    COLORS,
)

__all__ = [
    "display_h1", "display_h2", "display_h3", "display_p",
    "display_box", "display_kv", "display_table", "display_json",
    "display_status", "display_divider", "display_banner", "display_step",
    "COLORS",
]
