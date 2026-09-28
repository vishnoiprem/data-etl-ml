"""Pydantic schemas — the contract between the model and the agent's tools.

The model hallucinates tool arguments; Pydantic catches them before they
hit the filesystem. Same pattern as Module 11 (Harness Engineering).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


# ── read_file ────────────────────────────────────────────────────────────
class ReadFileArgs(BaseModel):
    path: str = Field(description="Repo-relative path of the file to read")

    @field_validator("path")
    @classmethod
    def no_traversal(cls, v: str) -> str:
        if v.startswith("/") or ".." in v.split("/"):
            raise ValueError(f"path must be repo-relative and contain no '..': {v!r}")
        return v


# ── grep ────────────────────────────────────────────────────────────────
class GrepArgs(BaseModel):
    pattern: str = Field(description="Regex pattern to search for")
    path: str = Field(default=".", description="Where to search")
    include: str | None = Field(default=None, description="Glob, e.g. '*.py'")


# ── list_dir ────────────────────────────────────────────────────────────
class ListDirArgs(BaseModel):
    path: str = Field(default=".", description="Directory to list")
    depth: int = Field(default=2, ge=1, le=5)


# ── apply_edit ──────────────────────────────────────────────────────────
class FileEdit(BaseModel):
    """A single find/replace edit. The agent may propose multiple."""
    path: str
    old_text: str = Field(description="Exact text to replace (must be unique in file)")
    new_text: str = Field(description="Replacement text")
    rationale: str = Field(description="Why this edit is needed")


class ApplyEditsArgs(BaseModel):
    edits: list[FileEdit] = Field(min_length=1, max_length=5)


# ── run_tests ───────────────────────────────────────────────────────────
class RunTestsArgs(BaseModel):
    target: str = Field(
        default="",
        description="Pytest target, e.g. 'tests/test_foo.py::test_bar'. Empty = run all.",
    )
    timeout_s: int = Field(default=120, ge=5, le=600)


# ── git_commit ──────────────────────────────────────────────────────────
class GitCommitArgs(BaseModel):
    message: str = Field(description="Commit message")
    add_paths: list[str] = Field(description="Files to stage before committing")


# ── git_push ────────────────────────────────────────────────────────────
class GitPushArgs(BaseModel):
    remote: str = Field(default="origin")
    branch: str = Field(description="Branch to push")
    set_upstream: bool = Field(default=False)


# ── open_pr ─────────────────────────────────────────────────────────────
class OpenPRArgs(BaseModel):
    title: str
    body: str
    base: str = Field(default="master")
    head: str = Field(description="Branch to merge from")


# ── tool registry ────────────────────────────────────────────────────────
TOOL_SCHEMAS = [
    ReadFileArgs, GrepArgs, ListDirArgs, ApplyEditsArgs,
    RunTestsArgs, GitCommitArgs, GitPushArgs, OpenPRArgs,
]

TOOL_NAMES = [t.__name__.replace("Args", "") for t in TOOL_SCHEMAS]


# ── agent decision output ───────────────────────────────────────────────
class AgentDecision(BaseModel):
    """The structured output the planner emits each step."""
    thought: str = Field(description="One-sentence reasoning about current state")
    next_action: Literal["read_file", "grep", "list_dir", "apply_edits",
                         "run_tests", "git_commit", "git_push", "open_pr", "finish"]
    args: dict = Field(default_factory=dict)
    is_done: bool = False
    final_summary: str | None = None