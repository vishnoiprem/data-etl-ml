"""The main agent loop — orchestrates planner, tools, and the harness.

This is the same loop pattern as Module 10's minimal agent, with the
harness layer from Module 11 wrapped around it.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from .editor import FileContextError, read_file, grep, list_dir
from .git_tools import current_branch, dirty_files, git_commit, git_push, open_pr
from .patcher import EditError, apply_edits, rollback
from .planner import Planner
from .runner import run_tests
from .schemas import (
    AgentDecision, ApplyEditsArgs, GitCommitArgs, GitPushArgs,
    GrepArgs, ListDirArgs, OpenPRArgs, ReadFileArgs, RunTestsArgs,
)


MAX_STEPS = 8
console = Console()


def run(
    task: str,
    root: Path,
    dry_run: bool = False,
    push: bool = True,
    pr: bool = False,
    max_steps: int = MAX_STEPS,
    traceback: str | None = None,
) -> dict:
    """Top-level agent run. Returns a structured report."""
    started_branch = current_branch(root)
    full_task = task
    if traceback:
        full_task += f"\n\nTRACEBACK:\n{traceback}"

    planner = Planner()
    history: list[dict] = []
    snapshots: dict[Path, str] = {}
    applied_edits: list = []
    final_summary = "Agent did not finish."
    committed = False

    console.print(Panel(f"[bold]{task}[/bold]", title="code-fix agent", subtitle=root.name))

    for step_num in range(1, max_steps + 1):
        decision: AgentDecision = planner.decide(history, full_task)
        console.print(f"\n[cyan]step {step_num}[/cyan] [dim]${planner.cost_usd:.4f}[/dim]  {decision.thought}")

        try:
            action = decision.next_action
            args = decision.args or {}
            result = ""

            # ── dispatch ──────────────────────────────────────────────
            if action == "read_file":
                result = read_file(root, ReadFileArgs(**args))

            elif action == "grep":
                result = grep(root, GrepArgs(**args))

            elif action == "list_dir":
                result = list_dir(root, ListDirArgs(**args))

            elif action == "apply_edits":
                # Snapshot before editing so we can rollback
                for path in {e["path"] for e in args.get("edits", [])}:
                    p = (root / path).resolve()
                    if p not in snapshots:
                        snapshots[p] = p.read_text(encoding="utf-8")
                result = apply_edits(root, ApplyEditsArgs(**args), dry_run=dry_run)
                applied_edits.extend(args.get("edits", []))

            elif action == "run_tests":
                t = run_tests(root, RunTestsArgs(**args))
                result = t.summary() + "\n"
                if not t.passed and t.failures:
                    result += "\n".join(
                        f"  - {f['file']}::{f['test']}\n    {f['msg'][:300]}"
                        for f in t.failures[:5]
                    )

            elif action == "git_commit":
                if dry_run:
                    result = "(dry-run: skipped commit)"
                else:
                    sha = git_commit(root, GitCommitArgs(**args))
                    committed = True
                    result = f"committed {sha[:8]}"

            elif action == "git_push":
                if dry_run or not push:
                    result = "(skipped push)"
                else:
                    branch = args.get("branch", started_branch)
                    set_up = args.get("set_upstream", branch != started_branch)
                    result = git_push(root, GitPushArgs(branch=branch, set_upstream=set_up))

            elif action == "open_pr":
                if dry_run or not push:
                    result = "(skipped PR)"
                else:
                    result = open_pr(root, OpenPRArgs(**args))

            elif action == "finish":
                final_summary = decision.final_summary or "Done."
                history.append({"action": "finish", "thought": decision.thought, "result": result})
                break

            else:
                result = f"unknown action: {action}"

            history.append({"action": action, "thought": decision.thought, "result": str(result)[:3000]})

        except (FileContextError, EditError, Exception) as e:
            history.append({"action": action, "thought": decision.thought, "result": f"ERROR: {e}"})
            console.print(f"  [red]tool error:[/red] {e}")

    # ── final cleanup / report ─────────────────────────────────────────
    report = {
        "task": task,
        "steps": len(history),
        "llm_calls": planner.calls,
        "cost_usd": planner.cost_usd,
        "started_branch": started_branch,
        "final_branch": current_branch(root),
        "committed": committed,
        "applied_edits": [e.get("rationale") for e in applied_edits],
        "final_summary": final_summary,
        "history": history,
    }
    return report


def main():
    ap = argparse.ArgumentParser(description="Code-fix agent")
    ap.add_argument("task", nargs="?", default="",
                    help="Failing test path, or a 'fix this bug' prompt")
    ap.add_argument("--root", type=Path, default=Path.cwd(),
                    help="Repo root to operate on")
    ap.add_argument("--dry-run", action="store_true",
                    help="Don't actually edit files or run git")
    ap.add_argument("--no-push", action="store_true",
                    help="Don't push or open PR after committing")
    ap.add_argument("--pr", action="store_true",
                    help="Open a PR after pushing (uses gh CLI)")
    ap.add_argument("--traceback", default=None,
                    help="Optional raw traceback to feed into the task")
    ap.add_argument("--max-steps", type=int, default=MAX_STEPS)
    args = ap.parse_args()

    if not args.task and not args.traceback:
        ap.error("provide a task or --traceback")

    report = run(
        task=args.task or "fix this error",
        root=args.root.resolve(),
        dry_run=args.dry_run,
        push=not args.no_push,
        pr=args.pr,
        traceback=args.traceback,
        max_steps=args.max_steps,
    )

    # Final summary panel
    console.print()
    console.print(Panel(
        f"[bold]{report['final_summary']}[/bold]\n\n"
        f"Steps: {report['steps']}   LLM calls: {report['llm_calls']}   "
        f"Cost: ${report['cost_usd']:.4f}\n"
        f"Branch: {report['started_branch']} → {report['final_branch']}   "
        f"Committed: {report['committed']}",
        title="code-fix agent — done",
    ))

    # Exit code reflects success
    sys.exit(0 if report["committed"] or args.dry_run else 1)


if __name__ == "__main__":
    main()