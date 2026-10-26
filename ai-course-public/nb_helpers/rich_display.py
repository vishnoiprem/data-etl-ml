"""
nb_helpers/rich_display.py — Rich HTML/IPython display helpers for Jupyter notebooks.

Usage in any notebook:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path.cwd()))  # if nb_helpers/ is at the repo root
    from nb_helpers.rich_display import (
        display_h1, display_h2, display_h3, display_p,
        display_box, display_kv, display_table, display_json,
        display_status, display_divider, display_banner, display_step,
    )

All display functions return an IPython.display object that renders
as rich HTML in JupyterLab/nbviewer. They never print to stdout.

Design goals:
  1. Drop-in: import + call, no setup.
  2. Composable: every helper returns the rendered object.
  3. Quiet: no print() side effects, no JSON dumps to stdout.
  4. Pretty: uses the system font stack, color-coded boxes, monospace where needed.
"""

from __future__ import annotations

import html
import json
from typing import Any, Mapping, Sequence

try:
    from IPython.display import HTML, display  # type: ignore
except ImportError:  # fallback for non-notebook contexts
    HTML = None  # type: ignore
    def display(*args, **kwargs):  # type: ignore
        return None


# ---------------------------------------------------------------------------
# Color palette (dark + light theme safe)
# ---------------------------------------------------------------------------
COLORS = {
    "primary":   "#2563eb",  # blue-600
    "success":   "#16a34a",  # green-600
    "warning":   "#d97706",  # amber-600
    "danger":    "#dc2626",  # red-600
    "muted":     "#6b7280",  # gray-500
    "bg_blue":   "#eff6ff",  # blue-50
    "bg_green":  "#f0fdf4",  # green-50
    "bg_amber":  "#fffbeb",  # amber-50
    "bg_red":    "#fef2f2",  # red-50
    "bg_gray":   "#f9fafb",  # gray-50
    "border":    "#e5e7eb",  # gray-200
    "text":      "#111827",  # gray-900
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _render(html_str: str) -> "HTML | str":
    """Render an HTML string. Returns IPython.display.HTML if available, else raw str."""
    if HTML is not None:
        return HTML(html_str)
    return html_str


def _esc(s: Any) -> str:
    """HTML-escape a value."""
    return html.escape(str(s))


# ---------------------------------------------------------------------------
# Headings
# ---------------------------------------------------------------------------
def display_h1(text: str, color: str = "primary") -> "HTML | str":
    """Big section header. Color is one of: primary, success, warning, danger, muted."""
    c = COLORS.get(color, color)
    return _render(
        f'<h1 style="color:{c}; border-bottom:3px solid {c}; padding-bottom:8px; '
        f'font-family:system-ui,-apple-system,Segoe UI,sans-serif; margin-top:24px;">'
        f'{_esc(text)}</h1>'
    )


def display_h2(text: str, color: str = "primary") -> "HTML | str":
    """Medium section header."""
    c = COLORS.get(color, color)
    return _render(
        f'<h2 style="color:{c}; margin-top:20px; '
        f'font-family:system-ui,-apple-system,Segoe UI,sans-serif;">{_esc(text)}</h2>'
    )


def display_h3(text: str, color: str = "text") -> "HTML | str":
    """Small section header."""
    c = COLORS.get(color, color)
    return _render(
        f'<h3 style="color:{c}; margin-top:16px; '
        f'font-family:system-ui,-apple-system,Segoe UI,sans-serif;">{_esc(text)}</h3>'
    )


def display_p(text: str) -> "HTML | str":
    """Plain paragraph."""
    return _render(
        f'<p style="font-family:system-ui,-apple-system,Segoe UI,sans-serif; '
        f'line-height:1.6; color:{COLORS["text"]};">{_esc(text)}</p>'
    )


# ---------------------------------------------------------------------------
# Boxes (the workhorse)
# ---------------------------------------------------------------------------
def display_box(
    text: str,
    *,
    kind: str = "info",
    title: str | None = None,
    mono: bool = False,
) -> "HTML | str":
    """A colored info/success/warning/danger box.

    Args:
        text: The body text. Newlines preserved.
        kind: One of: info, success, warning, danger, note, code.
        title: Optional bold title at the top of the box.
        mono: Render body in monospace (good for ASCII art, JSON, code).
    """
    bg_map = {
        "info":    COLORS["bg_blue"],
        "success": COLORS["bg_green"],
        "warning": COLORS["bg_amber"],
        "danger":  COLORS["bg_red"],
        "note":    COLORS["bg_gray"],
        "code":    COLORS["bg_gray"],
    }
    border_map = {
        "info":    COLORS["primary"],
        "success": COLORS["success"],
        "warning": COLORS["warning"],
        "danger":  COLORS["danger"],
        "note":    COLORS["muted"],
        "code":    COLORS["muted"],
    }
    bg = bg_map.get(kind, COLORS["bg_gray"])
    border = border_map.get(kind, COLORS["muted"])
    font = "monospace" if mono else "system-ui,-apple-system,Segoe UI,sans-serif"
    title_html = (
        f'<div style="font-weight:600; margin-bottom:6px; color:{COLORS["text"]};">{_esc(title)}</div>'
        if title else ""
    )
    body = _esc(text) if not mono else f'<pre style="margin:0; white-space:pre-wrap; font-family:monospace;">{_esc(text)}</pre>'
    return _render(
        f'<div style="background:{bg}; border-left:4px solid {border}; '
        f'padding:12px 16px; margin:12px 0; border-radius:4px; font-family:{font}; '
        f'color:{COLORS["text"]}; line-height:1.5;">'
        f'{title_html}{body}</div>'
    )


# ---------------------------------------------------------------------------
# Key-value pairs (great for status reports, shipment lookups)
# ---------------------------------------------------------------------------
def display_kv(
    data: Mapping[str, Any],
    *,
    title: str | None = None,
    ok_keys: Sequence[str] = (),
    warn_keys: Sequence[str] = (),
) -> "HTML | str":
    """Render a key-value table. Useful for showing structured data like Shipment objects.

    Args:
        data: Dict-like of {key: value}.
        title: Optional title above the table.
        ok_keys: Keys whose values are success (green check).
        warn_keys: Keys whose values are warnings (amber exclamation).
    """
    rows = []
    for k, v in data.items():
        icon = ""
        color = COLORS["text"]
        if k in ok_keys:
            icon = '<span style="color:#16a34a; margin-right:6px;">&#10003;</span>'
        elif k in warn_keys:
            icon = '<span style="color:#d97706; margin-right:6px;">&#9888;</span>'
        rows.append(
            f'<tr><td style="padding:6px 12px; font-weight:600; color:{COLORS["muted"]}; '
            f'vertical-align:top; white-space:nowrap;">{_esc(k)}</td>'
            f'<td style="padding:6px 12px; color:{color};">{icon}{_esc(v)}</td></tr>'
        )
    table = (
        f'<table style="border-collapse:collapse; font-family:system-ui,-apple-system,Segoe UI,sans-serif; '
        f'width:100%; max-width:800px; background:{COLORS["bg_gray"]}; border:1px solid {COLORS["border"]}; '
        f'border-radius:4px; overflow:hidden;">{"".join(rows)}</table>'
    )
    title_html = (
        f'<div style="font-weight:600; margin:12px 0 6px 0; color:{COLORS["text"]};">{_esc(title)}</div>'
        if title else ""
    )
    return _render(f"{title_html}{table}")


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------
def display_table(
    rows: Sequence[Sequence[Any]],
    *,
    headers: Sequence[str] | None = None,
    title: str | None = None,
) -> "HTML | str":
    """Render a 2D table with optional headers."""
    head_html = ""
    if headers:
        cells = "".join(
            f'<th style="padding:8px 12px; background:{COLORS["primary"]}; color:white; '
            f'text-align:left; font-weight:600;">{_esc(h)}</th>'
            for h in headers
        )
        head_html = f'<thead><tr>{cells}</tr></thead>'
    body_rows = []
    for r in rows:
        cells = "".join(
            f'<td style="padding:6px 12px; border-bottom:1px solid {COLORS["border"]}; '
            f'color:{COLORS["text"]};">{_esc(v)}</td>'
            for v in r
        )
        body_rows.append(f'<tr>{cells}</tr>')
    table = (
        f'<table style="border-collapse:collapse; font-family:system-ui,-apple-system,Segoe UI,sans-serif; '
        f'width:100%; max-width:800px; border:1px solid {COLORS["border"]}; border-radius:4px; overflow:hidden;">'
        f'{head_html}<tbody>{"".join(body_rows)}</tbody></table>'
    )
    title_html = (
        f'<div style="font-weight:600; margin:12px 0 6px 0; color:{COLORS["text"]};">{_esc(title)}</div>'
        if title else ""
    )
    return _render(f"{title_html}{table}")


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------
def display_json(data: Any, *, title: str | None = None) -> "HTML | str":
    """Render a JSON object as a syntax-highlighted code block."""
    text = json.dumps(data, indent=2, ensure_ascii=False, default=str)
    title_html = (
        f'<div style="font-weight:600; margin:12px 0 6px 0; color:{COLORS["text"]};">{_esc(title)}</div>'
        if title else ""
    )
    return _render(
        f'{title_html}<pre style="background:#0f172a; color:#e2e8f0; padding:14px 18px; '
        f'border-radius:6px; font-family:Menlo,Monaco,Consolas,monospace; font-size:13px; '
        f'line-height:1.5; overflow-x:auto; margin:0;">{_esc(text)}</pre>'
    )


# ---------------------------------------------------------------------------
# Status badges
# ---------------------------------------------------------------------------
def display_status(text: str, kind: str = "info") -> "HTML | str":
    """A small inline status badge (e.g., PASS, FAIL, OK, NOT FOUND)."""
    color_map = {
        "info":    COLORS["primary"],
        "ok":      COLORS["success"],
        "pass":    COLORS["success"],
        "success": COLORS["success"],
        "fail":    COLORS["danger"],
        "error":   COLORS["danger"],
        "warn":    COLORS["warning"],
        "warning": COLORS["warning"],
        "muted":   COLORS["muted"],
    }
    bg_map = {
        "info":    COLORS["bg_blue"],
        "ok":      COLORS["bg_green"],
        "pass":    COLORS["bg_green"],
        "success": COLORS["bg_green"],
        "fail":    COLORS["bg_red"],
        "error":   COLORS["bg_red"],
        "warn":    COLORS["bg_amber"],
        "warning": COLORS["bg_amber"],
        "muted":   COLORS["bg_gray"],
    }
    c = color_map.get(kind, COLORS["muted"])
    bg = bg_map.get(kind, COLORS["bg_gray"])
    return _render(
        f'<span style="display:inline-block; background:{bg}; color:{c}; padding:2px 10px; '
        f'border-radius:10px; font-family:system-ui,-apple-system,Segoe UI,sans-serif; '
        f'font-size:13px; font-weight:600; margin-right:6px;">{_esc(text)}</span>'
    )


# ---------------------------------------------------------------------------
# Dividers, banners, steps
# ---------------------------------------------------------------------------
def display_divider() -> "HTML | str":
    """A horizontal rule."""
    return _render(
        f'<hr style="border:none; border-top:1px solid {COLORS["border"]}; '
        f'margin:24px 0;"/>'
    )


def display_banner(
    text: str,
    *,
    kind: str = "info",
    emoji: str | None = None,
) -> "HTML | str":
    """A large banner at the top of a section. Use sparingly."""
    color_map = {"info": COLORS["primary"], "success": COLORS["success"],
                 "warning": COLORS["warning"], "danger": COLORS["danger"]}
    bg_map = {"info": COLORS["bg_blue"], "success": COLORS["bg_green"],
              "warning": COLORS["bg_amber"], "danger": COLORS["bg_red"]}
    c = color_map.get(kind, COLORS["primary"])
    bg = bg_map.get(kind, COLORS["bg_blue"])
    emoji_html = f'<span style="font-size:28px; margin-right:12px;">{emoji}</span>' if emoji else ""
    return _render(
        f'<div style="background:{bg}; border:2px solid {c}; border-radius:8px; '
        f'padding:16px 20px; margin:16px 0; font-family:system-ui,-apple-system,Segoe UI,sans-serif;">'
        f'<div style="display:flex; align-items:center;">{emoji_html}'
        f'<div style="font-size:18px; font-weight:600; color:{c};">{_esc(text)}</div>'
        f'</div></div>'
    )


def display_step(
    number: int,
    title: str,
    *,
    total: int | None = None,
) -> "HTML | str":
    """A numbered step header (e.g., 'Step 2 of 5 — EXTRACT')."""
    label = f"Step {number}" + (f" of {total}" if total else "") + f" — {title}"
    return _render(
        f'<div style="background:{COLORS["bg_blue"]}; border-left:4px solid {COLORS["primary"]}; '
        f'padding:10px 16px; margin:20px 0 12px 0; border-radius:4px; font-family:system-ui,-apple-system,Segoe UI,sans-serif;">'
        f'<span style="font-weight:700; color:{COLORS["primary"]}; font-size:15px;">{_esc(label)}</span>'
        f'</div>'
    )


# ---------------------------------------------------------------------------
# All-export
# ---------------------------------------------------------------------------
__all__ = [
    "display_h1", "display_h2", "display_h3", "display_p",
    "display_box", "display_kv", "display_table", "display_json",
    "display_status", "display_divider", "display_banner", "display_step",
    "COLORS",
]
