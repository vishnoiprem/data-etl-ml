#!/usr/bin/env python3
"""
test_course.py — structural tests for the Data Analysis course.

These tests check the *course itself*, not the pipeline:

* every chapter follows the house template
* every chapter is listed in the README
* every interview question is numbered and answered
* the linter catches the mistakes it is supposed to catch
* the semantic layer's semantics are the ones the chapters claim

Run it with:

    python resources/test_course.py

or under pytest:

    python -m pytest resources/test_course.py -v
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import pytest
except ImportError:  # pragma: no cover - pytest is a course dependency
    pytest = None

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS = ROOT / "chapters"
NOTEBOOKS = ROOT / "notebooks"
INTERVIEW = ROOT / "interview"
SQL = ROOT / "sql"
PROJECT = ROOT / "project"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_course import Report, validate_python  # noqa: E402

#: The house template. Every chapter must have these H2 sections, in this
#: order. A section may carry a subtitle after a colon — e.g.
#: `## 🛠️ Hands-On: Building it` — so matching is by prefix.
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
        metadata = [line for line in lines[:8] if line.startswith("> **")]
        assert metadata, f"{path.name} has no metadata line"


def test_chapters_have_code_examples():
    """Every chapter has at least one code block."""
    for path in chapter_files():
        text = path.read_text(encoding="utf-8")
        assert "```" in text, f"{path.name} has no code blocks"


def test_chapters_have_practice_exercises():
    """Every chapter ends with at least one numbered practice exercise."""
    for path in chapter_files():
        text = path.read_text(encoding="utf-8")
        start = _section_index(text, "## 📚 Practice Exercises")
        end = _section_index(text, "## 📖 Further Reading")
        assert start != -1, f"{path.name} has no Practice Exercises section"
        assert end != -1, f"{path.name} has no Further Reading section"
        body = text[start:end]
        numbered = re.findall(r"^\d+\.\s+\S", body, re.MULTILINE)
        assert numbered, f"{path.name} has no numbered practice exercises"


def test_chapters_never_say_the_ratio_is_additive():
    """A ratio is never additive — the chapters must not claim otherwise.

    The average-of-ratios error is the single most common silently-wrong
    number in BI, and a chapter that blurs it would teach the trap.

    The check looks for an *explicit claim* that a ratio is additive, not
    for the two words appearing near each other.
    """
    claims = re.compile(
        r"ratio[^.]{0,80}\bis additive\b"
        r"|\bis additive\b[^.]{0,80}ratio"
        r"|ratios[^.]{0,40}\bare additive\b",
        re.IGNORECASE,
    )
    for path in chapter_files():
        text = path.read_text(encoding="utf-8")
        for match in claims.finditer(text):
            window = text[max(0, match.start() - 300) : match.start() + 400]
            assert re.search(
                r"not additive|is not additive|non-additive|never additive|"
                r"does not roll up|cannot be summed",
                window,
                re.IGNORECASE,
            ), (
                f"{path.name} claims a ratio is additive: "
                f"{match.group(0)!r}"
            )


def test_chapters_never_present_a_count_as_order_count():
    """`COUNT(*)` on a line-grain table counts lines, not orders.

    A chapter that says `COUNT(*)` gives the number of orders is teaching
    the exact confusion the course exists to fix.
    """
    claims = re.compile(
        r"COUNT\(\*\)\s+(?:gives|counts|returns|is|means|tells you)\s+"
        r"(?:you\s+)?(?:the\s+)?(?:number of\s+|the\s+)?orders\b"
        r"|\borders\b\s+(?:are|is)\s+counted\s+with\s+COUNT\(\*\)",
        re.IGNORECASE,
    )
    for path in chapter_files():
        text = path.read_text(encoding="utf-8")
        for match in claims.finditer(text):
            window = text[max(0, match.start() - 300) : match.start() + 400]
            assert re.search(
                r"line|not order|not the number of order|instead of order|"
                r"rather than order",
                window,
                re.IGNORECASE,
            ), (
                f"{path.name} may be conflating COUNT(*) with order count: "
                f"{match.group(0)!r}"
            )


def test_chapters_warn_before_showing_a_fan_out():
    """A fan-out example must be introduced as a mistake.

    The doubling example is powerful *because* it is labelled as wrong. A
    chapter that shows it without a warning teaches the bug.
    """
    for path in chapter_files():
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"2257882|2,257,882", text):
            window = text[max(0, match.start() - 700) : match.start() + 300]
            assert re.search(
                r"wrong|duplicate|double|fan-out|inflated|break",
                window,
                re.IGNORECASE,
            ), (
                f"{path.name} shows the doubled revenue without labelling it "
                f"as the mistake it is"
            )


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


def test_readme_links_every_interview_file():
    """The course README links to the interview bank."""
    readme = _readme_text()
    assert "interview/" in readme, "README.md does not link to the interview bank"
    for path in interview_files():
        assert path.name in readme, f"README.md does not link to {path.name}"


def test_readme_states_the_no_cloud_promise():
    """The README says the course runs without a cloud account."""
    readme = _readme_text().lower()
    assert "no gcp" in readme or "without a gcp" in readme or "no cloud" in readme, (
        "the README does not state that the course runs without a GCP account"
    )


# --------------------------------------------------------------------------
# Interview tests
# --------------------------------------------------------------------------


def test_interview_files_exist():
    """The course has interview material."""
    assert interview_files(), f"no interview files found in {INTERVIEW}"


def test_interview_questions_are_numbered():
    """Every interview question is numbered and uniquely so."""
    for path in interview_files():
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        questions = re.findall(r"^### (\d+)\.\s+\S", text, re.MULTILINE)
        assert questions, f"{path.name} has no numbered questions"
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


def test_interview_answers_contain_a_failure_story():
    """Most answers should carry a production failure story.

    The failure story is the part interviewers probe, and it is the part
    that most distinguishes a real answer from a recited one. A handful of
    purely conceptual questions are allowed to skip it.
    """
    for path in interview_files():
        if path.name == "README.md" or path.name == "top-50.md":
            continue
        text = path.read_text(encoding="utf-8")
        blocks = re.split(r"^### \d+\.\s+", text, flags=re.MULTILINE)[1:]
        without = [
            number
            for number, block in enumerate(blocks, start=1)
            if "failure story" not in block.lower()
        ]
        # At most a quarter may skip it.
        assert len(without) <= max(1, len(blocks) // 4), (
            f"{path.name} has {len(without)} of {len(blocks)} answers with no "
            f"failure story"
        )


def test_top_50_has_exactly_fifty_questions():
    """The top-50 file contains exactly fifty questions."""
    path = INTERVIEW / "top-50.md"
    assert path.exists(), "interview/top-50.md is missing"
    text = path.read_text(encoding="utf-8")
    questions = re.findall(r"^### (\d+)\.\s+\S", text, re.MULTILINE)
    assert len(questions) == 50, (
        f"top-50.md has {len(questions)} questions, not 50"
    )
    assert [int(q) for q in questions] == list(range(1, 51)), (
        "top-50.md questions are not numbered 1..50"
    )


def test_interview_readme_lists_every_module_file():
    """The interview README links every module file."""
    path = INTERVIEW / "README.md"
    assert path.exists(), "interview/README.md is missing"
    text = path.read_text(encoding="utf-8")
    for module in sorted(INTERVIEW.glob("0*.md")):
        assert module.name in text, (
            f"interview/README.md does not link to {module.name}"
        )


# --------------------------------------------------------------------------
# SQL tests
# --------------------------------------------------------------------------


def test_sql_files_exist():
    """The course ships the DDL and the reconciliation queries."""
    names = {p.name for p in SQL.glob("*.sql")}
    assert "create_analytics.sql" in names, (
        "sql/create_analytics.sql is missing"
    )
    assert "reconciliation.sql" in names, "sql/reconciliation.sql is missing"


def test_ddl_records_the_grain_in_a_comment():
    """The orders DDL must state the grain and the primary key.

    The grain is recorded three times, and the DDL is one of the three.
    """
    text = (SQL / "create_analytics.sql").read_text(encoding="utf-8")
    assert "one row per order" in text.lower(), (
        "the DDL does not record the grain of the orders table"
    )
    assert "PRIMARY KEY (line_id)" in text, (
        "the orders table's primary key should be line_id, matching the grain"
    )
    assert "order_id" in text, "the DDL does not define order_id at all"


def test_ddl_has_a_date_spine():
    """The DDL creates the date spine."""
    text = (SQL / "create_analytics.sql").read_text(encoding="utf-8")
    assert "date_spine" in text, "the DDL does not create a date_spine table"


def test_reconciliation_compares_values_not_counts():
    """The reconciliation query must compare values, not row counts."""
    text = (SQL / "reconciliation.sql").read_text(encoding="utf-8")
    assert "IS DISTINCT FROM" in text, (
        "the reconciliation query does not compare values"
    )
    for label in ("MISSING", "EXTRA", "VALUE_MISMATCH"):
        assert label in text, f"the reconciliation query is missing {label}"


def test_reconciliation_has_a_fan_out_check():
    """The reconciliation ships the fan-out check.

    It is the check that catches a join that changed the number, and it is
    the query the runbook points at first.
    """
    text = (SQL / "reconciliation.sql").read_text(encoding="utf-8")
    lowered = text.lower()
    assert "fan" in lowered and "out" in lowered, (
        "the reconciliation has no fan-out check"
    )


# --------------------------------------------------------------------------
# Linter tests
# --------------------------------------------------------------------------


def test_linter_catches_a_python_syntax_error():
    """The linter flags a snippet that does not parse."""
    report = Report()
    validate_python(report, "test.py", "def broken(:\n    pass\n", 1)
    assert report.by_severity("ERROR"), "the linter missed the syntax error"


def test_linter_accepts_valid_python():
    """The linter does not flag correct Python."""
    report = Report()
    validate_python(
        report,
        "test.py",
        "import csv\n\nrows = list(csv.DictReader(open('data.csv')))\n",
        1,
    )
    assert not report.by_severity("ERROR"), (
        f"the linter flagged valid code: {report.by_severity('ERROR')}"
    )


def test_linter_catches_sql_in_a_python_fence():
    """A `python` fence containing SQL is a teaching error.

    The chapter linter parses every `python` fence. SQL in one of them
    means either the fence is mislabelled or the example is wrong, and both
    should fail the build.
    """
    report = Report()
    validate_python(
        report,
        "test.md",
        "SELECT SUM(total_amount)\nFROM analytics.orders;\n",
        1,
    )
    assert report.by_severity("ERROR"), (
        "the linter missed SQL inside a python fence"
    )


# --------------------------------------------------------------------------
# Project tests
# --------------------------------------------------------------------------


def test_project_core_modules_exist():
    """The project ships the four core modules."""
    for name in ("model.py", "date_helpers.py", "lookml.py", "validate.py"):
        assert (PROJECT / "core" / name).exists(), (
            f"project/core/{name} is missing"
        )


def test_the_cli_exists_and_is_executable():
    """The CLI is the course's front door."""
    path = PROJECT / "local_bi.py"
    assert path.exists(), "project/local_bi.py is missing"
    source = path.read_text(encoding="utf-8")
    for command in (
        "query",
        "describe",
        "explores",
        "validate",
        "lookml",
        "spine",
    ):
        assert command in source, f"the CLI does not expose the {command} command"


def test_the_rendered_lookml_is_committed():
    """The rendered LookML ships with the course.

    A test in `project/tests/` asserts it matches the generator, so the two
    can never drift apart silently.
    """
    path = PROJECT / "lookml" / "ecommerce.model.lookml"
    assert path.exists(), "the rendered LookML is missing"
    text = path.read_text(encoding="utf-8")
    assert "view:" in text, "the rendered LookML has no view blocks"
    assert "measure:" in text, "the rendered LookML has no measures"


def test_the_lookml_declares_a_relationship():
    """The rendered LookML declares the join relationships.

    A `relationship:` on a join is what stops the tool fanning it out, and
    a semantic layer that omits it is a semantic layer that hands the
    decision to the report author.
    """
    text = (PROJECT / "lookml" / "ecommerce.model.lookml").read_text(
        encoding="utf-8"
    )
    assert "relationship:" in text, (
        "the rendered LookML declares no join relationships"
    )
    assert "one_to_many" in text, (
        "the rendered LookML contains no fan-out join — the warning about "
        "one has nowhere to live"
    )


def test_the_model_records_the_grain():
    """The orders model's grain is the order line.

    This is the property the whole course rests on, and the property the
    chapters quote.
    """
    import importlib  # noqa: PLC0415

    sys.path.insert(0, str(PROJECT / "core"))
    model_module = importlib.import_module("model")

    model = model_module.build_sales_model()
    assert model.grain == "one row per order line", (
        f"the orders model's grain is {model.grain!r}"
    )
    assert model.primary_key == "line_id", (
        f"the orders model's primary key is {model.primary_key!r}"
    )


def test_the_measures_carry_descriptions():
    """Every measure and dimension has a description.

    The description is the guard rail. A measure without one permits every
    mistake while appearing to be documented.
    """
    import importlib  # noqa: PLC0415

    sys.path.insert(0, str(PROJECT / "core"))
    model_module = importlib.import_module("model")

    for builder in (
        model_module.build_sales_model,
        model_module.build_customer_model,
        model_module.build_product_model,
    ):
        model = builder()
        for measure in model.measures:
            assert measure.description.strip(), (
                f"measure {measure.name!r} has no description"
            )
        for dimension in model.dimensions:
            assert dimension.description.strip(), (
                f"dimension {dimension.name!r} has no description"
            )


def test_the_joins_warn_about_fan_out():
    """Every fan-out join carries a warning in its description.

    The warning is what travels into the tool's UI, where the report author
    will see it.
    """
    import importlib  # noqa: PLC0415

    sys.path.insert(0, str(PROJECT / "core"))
    model_module = importlib.import_module("model")

    fan_outs = []
    for explore in model_module.build_explores():
        for join in explore.joins:
            if join.causes_fan_out:
                fan_outs.append(join)

    assert fan_outs, "the course has no fan-out join to demonstrate"
    for join in fan_outs:
        assert join.description.strip(), (
            f"the fan-out join {join.name!r} has no warning in its description"
        )
        assert re.search(
            r"fan|inflate|multiply|duplicate",
            join.description,
            re.IGNORECASE,
        ), (
            f"the fan-out join {join.name!r} does not say what fan-out does"
        )


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


def test_notebooks_are_in_sync_with_their_builders():
    """Every notebook matches what `build_notebooks.py` would generate.

    The notebooks are generated from `resources/notebook_0*.py`, so a
    builder edit that is not regenerated would leave the course shipping a
    notebook that no longer matches its documented source.

    Returns:
        None.
    """
    import importlib  # noqa: PLC0415
    import json  # noqa: PLC0415

    resources = Path(__file__).resolve().parent
    sys.path.insert(0, str(resources))

    build_notebooks = importlib.import_module("build_notebooks")

    for filename, module_name in build_notebooks.NOTEBOOK_SOURCES.items():
        module = importlib.import_module(module_name)
        payload = json.dumps(module.build(), indent=1) + "\n"
        current = (NOTEBOOKS / filename).read_text(encoding="utf-8")
        assert current == payload, (
            f"{filename} is stale — run `python resources/build_notebooks.py`"
        )


# --------------------------------------------------------------------------
# Resource tests
# --------------------------------------------------------------------------


def test_the_resources_exist():
    """The course ships the four reference documents."""
    for name in ("SETUP.md", "CHEATSHEET.md", "GLOSSARY.md", "FAQ.md"):
        assert (ROOT / "resources" / name).exists(), (
            f"resources/{name} is missing"
        )


def test_the_cheatsheet_covers_the_essentials():
    """The cheatsheet must contain the course's core tables."""
    text = (ROOT / "resources" / "CHEATSHEET.md").read_text(encoding="utf-8")
    for term in ("grain", "additive", "fan-out", "spine", "reconciliation"):
        assert term.lower() in text.lower(), (
            f"the cheatsheet does not mention {term}"
        )


def test_the_glossary_defines_the_core_terms():
    """The glossary must define the course's core terms."""
    text = (ROOT / "resources" / "GLOSSARY.md").read_text(encoding="utf-8")
    for term in (
        "Semantic layer",
        "Grain",
        "Additivity",
        "Fan-out",
        "Date spine",
        "Timeframe",
        "Validation gate",
        "Reconciliation",
    ):
        assert term.lower() in text.lower(), (
            f"the glossary does not define {term}"
        )
