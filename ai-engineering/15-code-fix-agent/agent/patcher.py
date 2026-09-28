"""Apply file edits safely with validation and atomic rollback."""

from __future__ import annotations

import difflib
from pathlib import Path

from .editor import _resolve, FileContextError
from .schemas import ApplyEditsArgs, FileEdit


class EditError(Exception):
    pass


def apply_edits(root: Path, args: ApplyEditsArgs, dry_run: bool = False) -> str:
    """Apply all edits atomically. Either every edit succeeds or none do.

    Returns a unified diff for the user to review.
    """
    # Pre-flight: every old_text must be unique in its file
    snapshots: dict[Path, str] = {}
    for edit in args.edits:
        path = _resolve(root, edit.path)
        if not path.exists():
            raise EditError(f"file not found: {edit.path}")
        original = path.read_text(encoding="utf-8")
        if edit.old_text not in original:
            raise EditError(
                f"old_text not found verbatim in {edit.path}.\n"
                f"--- looking for ---\n{edit.old_text}\n--- end ---\n"
                f"Hint: make sure whitespace and indentation match exactly."
            )
        count = original.count(edit.old_text)
        if count > 1:
            raise EditError(
                f"old_text is ambiguous ({count} matches) in {edit.path}. "
                f"Include more surrounding context to make it unique."
            )
        snapshots[path] = original

    # All pre-flight passed — apply in memory
    new_contents: dict[Path, str] = {}
    for edit in args.edits:
        path = _resolve(root, edit.path)
        new_contents[path] = snapshots[path].replace(edit.old_text, edit.new_text, 1)

    # Diff for review
    diffs = []
    for path, new in new_contents.items():
        old = snapshots[path]
        rel = path.relative_to(root)
        diff = "".join(
            difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile=f"a/{rel}",
                tofile=f"b/{rel}",
                n=2,
            )
        )
        diffs.append(f"=== {rel} ===\n{diff}")

    if not dry_run:
        for path, content in new_contents.items():
            path.write_text(content, encoding="utf-8")

    return "\n".join(diffs)


def rollback(root: Path, snapshots: dict[Path, str]) -> None:
    """Write the original contents back. Used when post-edit tests fail."""
    for path, original in snapshots.items():
        path.write_text(original, encoding="utf-8")