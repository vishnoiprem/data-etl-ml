"""Tests for the file context tools (read_file, grep, list_dir)."""

import textwrap
from pathlib import Path

import pytest

from agent.editor import FileContextError, grep, list_dir, read_file
from agent.schemas import GrepArgs, ListDirArgs, ReadFileArgs


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def hello():\n    print('hi')\n")
    (tmp_path / "README.md").write_text("# hello world\n")
    return tmp_path


def test_read_file(repo):
    content = read_file(repo, ReadFileArgs(path="src/main.py"))
    assert "def hello" in content


def test_read_file_path_traversal_blocked(repo):
    with pytest.raises(FileContextError):
        read_file(repo, ReadFileArgs(path="../../../etc/passwd"))


def test_read_file_absolute_blocked(repo):
    with pytest.raises(FileContextError):
        read_file(repo, ReadFileArgs(path="/etc/passwd"))


def test_read_file_missing(repo):
    with pytest.raises(FileContextError):
        read_file(repo, ReadFileArgs(path="nope.py"))


def test_read_file_truncates_huge_files(repo):
    big = "\n".join(f"line {i}" for i in range(1000))
    (repo / "big.txt").write_text(big)
    content = read_file(repo, ReadFileArgs(path="big.txt"))
    assert "[... truncated" in content


def test_grep_finds_matches(repo):
    out = grep(repo, GrepArgs(pattern="hello", path="src"))
    assert "main.py" in out
    assert "def hello" in out


def test_grep_no_match_returns_message(repo):
    out = grep(repo, GrepArgs(pattern="zzzzzz_no_match", path="."))
    assert "no matches" in out.lower()


def test_list_dir(repo):
    out = list_dir(repo, ListDirArgs(path=".", depth=1))
    assert "src/" in out
    assert "README.md" in out