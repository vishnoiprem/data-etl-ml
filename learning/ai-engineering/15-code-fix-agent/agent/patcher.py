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

    When multiple edits target the same file, they are applied in order on
    the in-memory copy, so each subsequent old_text check operates on the
    state after prior edits (matching how an LLM would plan them).
    """
    # Pre-flight: every old_text must be unique in its file (vs original)
    snapshots: dict[Path, str] = {}
    for edit in args.edits:
        path = _resolve(root, edit.path)
        if not path.exists():
            raise EditError(f"file not found: {edit.path}")
        if path not in snapshots:
            snapshots[path] = path.read_text(encoding="utf-8")
        current = snapshots[path]
        if edit.old_text not in current:
            raise EditError(
                f"old_text not found verbatim in {edit.path}.\n"
                f"--- looking for ---\n{edit.old_text}\n--- end ---\n"
                f"Hint: make sure whitespace and indentation match exactly."
            )
        count = current.count(edit.old_text)
        if count > 1:
            raise EditError(
                f"old_text is ambiguous ({count} matches) in {edit.path}. "
                f"Include more surrounding context to make it unique."
            )

    # All pre-flight passed — apply in order on in-memory copies
    new_contents: dict[Path, str] = dict(snapshots)
    for edit in args.edits:
        path = _resolve(root, edit.path)
        new_contents[path] = new_contents[path].replace(edit.old_text, edit.new_text, 1)

    # Diff for review
    diffs = []
    root_resolved = root.resolve()
    for path, new in new_contents.items():
        old = snapshots[path]
        try:
            rel = path.relative_to(root_resolved)
        except ValueError:
            # Fallback if paths diverge due to symlinks (macOS /tmp -> /private/tmp)
            rel = Path(path.name)
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