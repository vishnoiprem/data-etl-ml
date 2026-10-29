"""File-reading helpers — what the agent sees when it asks for context."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .schemas import GrepArgs, ListDirArgs, ReadFileArgs


class FileContextError(Exception):
    """Raised when a read fails (path traversal, missing file, etc)."""


def _resolve(root: Path, p: str) -> Path:
    """Resolve a repo-relative path and verify it stays under root."""
    target = (root / p).resolve()
    if not str(target).startswith(str(root.resolve())):
        raise FileContextError(f"path escapes repo: {p!r}")
    return target


def read_file(root: Path, args: ReadFileArgs, max_lines: int = 400) -> str:
    """Read a file. Truncate to max_lines to keep prompt costs bounded."""
    path = _resolve(root, args.path)
    if not path.exists():
        raise FileContextError(f"file not found: {args.path}")
    if path.stat().st_size > 200_000:
        raise FileContextError(f"file too large (>200KB): {args.path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > 200_000:
        return text[:200_000] + "\n\n[... truncated at 200K of characters ...]"
    lines = text.splitlines()
    if len(lines) > max_lines:
        return "\n".join(lines[:max_lines]) + f"\n\n[... truncated at {max_lines} of {len(lines)} lines ...]"
    return text


def grep(root: Path, args: GrepArgs) -> str:
    """Regex search using ripgrep if available, else fallback to Python re."""
    path = _resolve(root, args.path)
    try:
        cmd = ["rg", "--line-number", "--no-heading", args.pattern, str(path)]
        if args.include:
            cmd.extend(["--glob", args.include])
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if out.returncode in (0, 1):  # 0 = found, 1 = no match (still ok)
            return out.stdout[:8000] or "(no matches)"
    except FileNotFoundError:
        pass  # rg not installed — fallback

    # Fallback: pure Python
    matches = []
    pattern = re.compile(args.pattern)
    for p in path.rglob(args.include or "*") if path.is_dir() else [path]:
        if not p.is_file():
            continue
        try:
            for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
                if pattern.search(line):
                    matches.append(f"{p}:{i}:{line}")
                    if len(matches) > 200:
                        break
        except Exception:
            continue
    return "\n".join(matches[:200]) or "(no matches)"


def list_dir(root: Path, args: ListDirArgs) -> str:
    """List directory contents up to `depth` levels."""
    path = _resolve(root, args.path)
    if not path.is_dir():
        raise FileContextError(f"not a directory: {args.path}")

    lines = []
    for p in sorted(path.iterdir()):
        try:
            rel = p.relative_to(root)
        except ValueError:
            continue
        if len(rel.parts) > args.depth + 1:
            continue
        marker = "/" if p.is_dir() else ""
        lines.append(f"{p.name}{marker}")
    return "\n".join(lines[:300]) or "(empty)"


def depth_unlimited(d: int) -> bool:
    return d <= 0