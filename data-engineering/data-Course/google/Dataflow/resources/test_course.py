#!/usr/bin/env python3
"""
test_course.py — structural tests for the Dataflow course.

These tests check the *course itself*, not the pipelines:

* every chapter follows the house template
* every chapter is listed in the README
* every interview question is numbered and answered
* the linter catches the mistakes it is supposed to catch

Run it with:

    python resources/test_course.py

or under pytest:

    python -m pytest resources/test_course.py -v
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS = ROOT / "chapters"
NOTEBOOKS = ROOT / "notebooks"
INTERVIEW = ROOT / "interview"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_course import Report, validate_python  # noqa: E402

#: The house template. Every chapter must have these H2 sections, in this
#: order. A section may carry a subtitle after a colon — e.g.
#: `## 🛠️ Hands-On: Building the pipeline` — so matching is by prefix.
REQUIRED_SECTIONS = [
    "## 🎯 What you will learn",
    "## 🧠 Concept",
    "## 🛠️ Hands-On",
    "## 🛠️ Common Errors and Fixes",
    "## 💡 Production Notes",
    "## 🔑 Key Takeaways",
    "## 📚 Practice Exercises",
    "## 📖 Further Reading",
]

#: Sections that may appear between "Concept" and "Hands-On".
OPTIONAL_CONCEPT_SECTIONS = ("## 🧠",)


def _section_index(text: str, section: str) -> int:
    """Return the index of a section heading, matching by prefix.

    A heading may carry a subtitle (``## 🛠️ Hands-On: Building it``), so
    the match is anchored at the start of a line and ends at the newline.

    Args:
        text: The chapter text.
        section: The section heading prefix to find.

    Returns:
        The character index of the heading, or -1 if it is absent.
    """
    match = re.search(rf"^{re.escape(section)}.*$", text, re.MULTILINE)
    return match.start() if match else -1


def chapter_files() -> list[Path]:
    """Return every chapter file, sorted."""
    return sorted(CHAPTERS.glob("*.md"))


def interview_files() -> list[Path]:
    """Return every interview file, sorted."""
    return sorted(INTERVIEW.glob("*.md"))


# --------------------------------------------------------------------------
# Chapter tests
# --------------------------------------------------------------------------


def test_chapters_exist():
    """The course has chapters."""
    files = chapter_files()
    assert files, f"no chapters found in {CHAPTERS}"


def test_chapter_filenames_are_numbered():
    """Chapter files use the NN-kebab-case.md convention."""
    pattern = re.compile(r"^\d{2}-[a-z0-9-]+\.md$")
    for path in chapter_files():
        assert pattern.match(path.name), f"bad chapter filename: {path.name}"


def test_chapter_numbers_are_sequential():
    """Chapter numbers run 01, 02, 03, ... with no gaps."""
    numbers = [int(path.name[:2]) for path in chapter_files()]
    assert numbers == list(range(1, len(numbers) + 1)), (
        f"chapter numbers are not sequential: {numbers}"
    )


def test_every_chapter_has_the_required_sections():
    """Every chapter has all eight template sections, in order."""
    for path in chapter_files():
        text = path.read_text(encoding="utf-8")
        positions = []
        for section in REQUIRED_SECTIONS:
            index = _section_index(text, section)
            assert index != -1, f"{path.name} is missing {section!r}"
            positions.append(index)

        assert positions == sorted(positions), (
            f"{path.name} has its sections out of order"
        )


def test_every_chapter_has_a_title_and_metadata():
    """Every chapter starts with an H1 and a metadata line."""
    for path in chapter_files():
        lines = path.read_text(encoding="utf-8").splitlines()
        assert lines and lines[0].startswith("# "), f"{path.name} has no H1 title"
        assert re.match(r"^# \d+\.\d+ — ", lines[0]), (
            f"{path.name} title is not in the '# N.M — Title' form"
        )
        metadata = [line for line in lines[:6] if line.startswith("> **")]
        assert metadata, f"{path.name} has no metadata line"


def test_chapters_have_code_examples():
    """Every chapter has at least one code block."""
    for path in chapter_files():
        text = path.read_text(encoding="utf-8")
        assert "```" in text, f"{path.name} has no code blocks"


def test_chapters_have_practice_exercises():
    """Every chapter ends with at least one practice exercise."""
    for path in chapter_files():
        text = path.read_text(encoding="utf-8")
        start = _section_index(text, "## 📚 Practice Exercises")
        end = _section_index(text, "## 📖 Further Reading")
        assert start != -1, f"{path.name} has no Practice Exercises section"
        assert end != -1, f"{path.name} has no Further Reading section"
        body = text[start:end]
        numbered = re.findall(r"^\d+\.\s+\S", body, re.MULTILINE)
        assert numbered, f"{path.name} has no numbered practice exercises"


# --------------------------------------------------------------------------
# README tests
# --------------------------------------------------------------------------


def _readme_text() -> str:
    """Return the course README, asserting that it exists."""
    path = ROOT / "README.md"
    assert path.exists(), "the course README.md is missing"
    return path.read_text(encoding="utf-8")


def test_readme_links_every_chapter():
    """The course README links to every chapter."""
    readme = _readme_text()
    for path in chapter_files():
        assert path.name in readme, f"README.md does not link to {path.name}"


def test_readme_links_every_notebook():
    """The course README links to every notebook."""
    readme = _readme_text()
    for path in sorted(NOTEBOOKS.glob("*.ipynb")):
        assert path.name in readme, f"README.md does not link to {path.name}"


# --------------------------------------------------------------------------
# Interview tests
# --------------------------------------------------------------------------


def test_interview_files_exist():
    """The course has interview material."""
    assert interview_files(), f"no interview files found in {INTERVIEW}"


def test_interview_questions_are_numbered():
    """Every interview question is numbered and has an answer."""
    for path in interview_files():
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        questions = re.findall(r"^### (\d+)\.\s+\S", text, re.MULTILINE)
        assert questions, f"{path.name} has no numbered questions"
        # The numbering must be unique within the file.
        assert len(questions) == len(set(questions)), (
            f"{path.name} has duplicate question numbers"
        )


def test_interview_answers_are_substantive():
    """Every interview question has a real answer, not a stub."""
    for path in interview_files():
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        blocks = re.split(r"^### \d+\.\s+", text, flags=re.MULTILINE)[1:]
        for number, block in enumerate(blocks, start=1):
            answer = block.split("\n##", 1)[0].strip()
            assert len(answer) > 150, (
                f"{path.name} question {number} has a too-short answer "
                f"({len(answer)} chars)"
            )


# --------------------------------------------------------------------------
# Linter tests
# --------------------------------------------------------------------------


def test_linter_catches_a_bad_beam_attribute():
    """The linter flags a Beam transform that does not exist."""
    report = Report()
    validate_python(
        report,
        "test.py",
        "import apache_beam as beam\nx = beam.NoSuchTransform()\n",
        1,
    )
    messages = [i.message for i in report.by_severity("ERROR")]
    assert any("NoSuchTransform" in m for m in messages), (
        f"the linter missed the bad attribute: {messages}"
    )


def test_linter_accepts_valid_beam_usage():
    """The linter does not flag correct Beam code."""
    report = Report()
    validate_python(
        report,
        "test.py",
        "import apache_beam as beam\n"
        "x = beam.Map(lambda v: v)\n"
        "y = beam.combiners.Count.PerKey()\n"
        "z = beam.Flatten()\n"
        "w = beam.WindowInto(beam.transforms.window.FixedWindows(60))\n",
        1,
    )
    assert not report.by_severity("ERROR"), (
        f"the linter flagged valid code: "
        f"{[i.message for i in report.by_severity('ERROR')]}"
    )


def test_linter_catches_duplicate_transform_labels():
    """The linter flags two transforms sharing a label."""
    report = Report()
    validate_python(
        report,
        "test.py",
        "import apache_beam as beam\n"
        "p = p | 'Same' >> beam.Map(lambda v: v) | 'Same' >> beam.Filter(lambda v: True)\n",
        1,
    )
    messages = [i.message for i in report.by_severity("ERROR")]
    assert any("Same" in m for m in messages), (
        f"the linter missed the duplicate label: {messages}"
    )


def test_linter_catches_a_python_syntax_error():
    """The linter flags a snippet that does not parse."""
    report = Report()
    validate_python(report, "test.py", "def broken(:\n    pass\n", 1)
    assert report.by_severity("ERROR"), "the linter missed the syntax error"


# --------------------------------------------------------------------------
# Notebook tests
# --------------------------------------------------------------------------


def test_notebooks_exist():
    """The course has notebooks."""
    assert sorted(NOTEBOOKS.glob("*.ipynb")), f"no notebooks found in {NOTEBOOKS}"


def test_notebook_filenames_are_numbered():
    """Notebook files use the NN-kebab-case.ipynb convention."""
    pattern = re.compile(r"^\d{2}-[a-z0-9-]+\.ipynb$")
    for path in sorted(NOTEBOOKS.glob("*.ipynb")):
        assert pattern.match(path.name), f"bad notebook filename: {path.name}"


def main() -> int:
    """Run every test in this module and report the result.

    Returns:
        0 when all tests pass, 1 otherwise.
    """
    failures = 0
    tests = [
        (name, value)
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]

    for name, func in tests:
        try:
            func()
            print(f"  PASS  {name}")
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {name}")
            print(f"        {exc}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"  ERROR {name}")
            print(f"        {type(exc).__name__}: {exc}")

    total = len(tests)
    print()
    print(f"{total - failures}/{total} course tests passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
