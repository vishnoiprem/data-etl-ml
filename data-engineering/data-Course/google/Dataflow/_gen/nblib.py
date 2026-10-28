"""Shared helpers for building course notebooks.

The course linter requires nbformat 4.5 (so every cell needs an ``id``)
and requires code cells to be written as a *list* of lines.  Building the
notebook from Python source strings keeps the escaping sane.
"""

from __future__ import annotations

import json
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parent.parent


def md(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.rstrip("\n").splitlines(keepends=True),
    }


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.rstrip("\n").splitlines(keepends=True),
    }


def build(cells: list[dict], notebook_id: str, *, out_path: Path) -> Path:
    """Assemble a notebook dict, stamp cell ids, and write it to disk."""
    for index, cell in enumerate(cells):
        cell["id"] = f"{notebook_id}-cell-{index:02d}"
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# The setup cell is identical across the course notebooks.  It locates the
# course root no matter which directory Jupyter was started from, makes the
# project package importable, and generates the sample data on demand.
# ---------------------------------------------------------------------------

SETUP = '''
import os
import subprocess
import sys
from pathlib import Path

COURSE_ROOT = Path.cwd()
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = COURSE_ROOT.parent
PROJECT_DIR = COURSE_ROOT / "project"
if not PROJECT_DIR.exists():
    PROJECT_DIR = COURSE_ROOT.parent / "project"
sys.path.insert(0, str(PROJECT_DIR))

if not (COURSE_ROOT / "sample_data" / "orders.csv").exists():
    subprocess.run(
        [sys.executable, str(COURSE_ROOT / "resources" / "sample_data.py"),
         "--output-dir", str(COURSE_ROOT / "sample_data")],
        check=True,
    )

import apache_beam as beam

print(f"course root   : {COURSE_ROOT}")
print(f"project dir   : {PROJECT_DIR}")
print(f"beam version  : {beam.__version__}")
print(f"python        : {sys.version.split()[0]}")
'''


def setup_cell() -> dict:
    return code(SETUP)
