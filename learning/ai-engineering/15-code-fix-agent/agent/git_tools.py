"""Git operations — commit + push, or open a PR via the GitHub CLI / API."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from .schemas import GitCommitArgs, GitPushArgs, OpenPRArgs


class GitError(Exception):
    pass


def _run(cmd: list[str], cwd: Path, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)


def git_commit(root: Path, args: GitCommitArgs) -> str:
    """Stage the listed paths, commit with the given message, return the SHA."""
    for p in args.add_paths:
        _run(["git", "add", p], cwd=root)

    # Check there's actually something to commit
    status = _run(["git", "diff", "--cached", "--stat"], cwd=root)
    if not status.stdout.strip():
        raise GitError("nothing staged to commit")

    res = _run(["git", "commit", "-m", args.message], cwd=root)
    if res.returncode != 0:
        raise GitError(f"commit failed: {res.stderr.strip()}")

    sha = _run(["git", "rev-parse", "HEAD"], cwd=root).stdout.strip()
    return sha


def git_push(root: Path, args: GitPushArgs) -> str:
    """Push the branch. Returns 'pushed <remote>/<branch>' on success."""
    cmd = ["git", "push"]
    if args.set_upstream:
        cmd += ["-u", args.remote, args.branch]
    else:
        cmd += [args.remote, args.branch]
    res = _run(cmd, cwd=root, timeout=120)
    if res.returncode != 0:
        raise GitError(f"push failed: {res.stderr.strip()}")
    return f"pushed {args.remote}/{args.branch}"


def open_pr(root: Path, args: OpenPRArgs, github_token: str | None = None) -> str:
    """Open a PR using `gh` CLI if available, else fall back to git push only.

    Returns the PR URL if opened, else a push success message.
    """
    token = github_token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    # Try gh CLI first
    gh_check = subprocess.run(["which", "gh"], capture_output=True, text=True)
    if gh_check.returncode == 0:
        env = os.environ.copy()
        if token:
            env["GH_TOKEN"] = token
        res = subprocess.run(
            ["gh", "pr", "create",
             "--title", args.title,
             "--body", args.body,
             "--base", args.base,
             "--head", args.head],
            cwd=str(root),
            capture_output=True,
            text=True,
            env=env,
            timeout=60,
        )
        if res.returncode == 0:
            return res.stdout.strip()  # PR URL
        raise GitError(f"gh pr create failed: {res.stderr.strip()}")

    # Fallback: just push the branch and tell the user to open a PR manually
    git_push(root, GitPushArgs(branch=args.head, set_upstream=True))
    return (
        f"(gh CLI not installed; branch '{args.head}' pushed. "
        f"Open a PR manually: https://github.com/<owner>/<repo>/compare/{args.base}...{args.head})"
    )


def current_branch(root: Path) -> str:
    res = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root)
    return res.stdout.strip() or "HEAD"


def dirty_files(root: Path) -> list[str]:
    res = _run(["git", "status", "--porcelain"], cwd=root)
    return [line[3:] for line in res.stdout.splitlines() if line.strip()]