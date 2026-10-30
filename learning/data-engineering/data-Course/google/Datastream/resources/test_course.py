#!/usr/bin/env python3
"""
test_course.py — structural tests for the Datastream course.

These tests check the *course itself*, not the pipeline:

* every chapter follows the house template
* every chapter is listed in the README
* every interview question is numbered and answered
* the linter catches the mistakes it is supposed to catch
* the merge semantics in `project/cdc.py` are the ones the chapters claim

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


def test_no_chapter_recommends_a_streaming_not_matched_by_source():
    """The clause that empties a table must only ever appear as a warning.

    ``WHEN NOT MATCHED BY SOURCE THEN DELETE`` is the correct clause for a
    *synchronised* merge and a catastrophic one for a streaming merge. If a
    chapter shows it as something to write, that is a teaching error.

    Args:
        None.

    Returns:
        None.
    """
    for path in chapter_files():
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"WHEN NOT MATCHED BY SOURCE", text):
            window = text[max(0, match.start() - 400) : match.start() + 200].lower()
            warned = any(
                marker in window
                for marker in ("never", "not ", "empty", "wrong", "synchronised", "do not")
            )
            assert warned, (
                f"{path.name} presents WHEN NOT MATCHED BY SOURCE without a warning"
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
    """The course ships SQL for the destination and the reconciliation."""
    names = {p.name for p in SQL.glob("*.sql")}
    assert "create_customers.sql" in names, "sql/create_customers.sql is missing"
    assert "reconciliation.sql" in names, "sql/reconciliation.sql is missing"


def test_customers_ddl_clusters_on_the_merge_key():
    """The BigQuery destination is clustered on the merge key."""
    text = (SQL / "create_customers.sql").read_text(encoding="utf-8")
    assert "CLUSTER BY customer_id" in text, (
        "the destination table is not clustered on the merge key"
    )


def test_transactions_ddl_has_a_primary_key():
    """The Postgres transactions table has a primary key — the idempotency
    guarantee for the Kafka path."""
    path = SQL / "create_transactions.sql"
    assert path.exists(), "sql/create_transactions.sql is missing"
    text = path.read_text(encoding="utf-8")
    assert "PRIMARY KEY" in text, (
        "the transactions table has no primary key — the Kafka path loses "
        "its idempotency guarantee"
    )
    assert "transaction_id" in text, (
        "the primary key should be the business key (transaction_id)"
    )


def test_reconciliation_compares_values_not_counts():
    """The reconciliation query must compare values, not row counts."""
    text = (SQL / "reconciliation.sql").read_text(encoding="utf-8")
    assert "IS DISTINCT FROM" in text, (
        "the reconciliation query does not compare values"
    )
    for label in ("MISSING", "EXTRA", "VALUE_MISMATCH"):
        assert label in text, f"the reconciliation query is missing {label}"


# --------------------------------------------------------------------------
# Linter tests
# --------------------------------------------------------------------------


def test_linter_catches_a_python_syntax_error():
    """The linter flags a snippet that does not parse."""
    report = Report()
    validate_python(report, "test.py", "def broken(:\n    pass\n", 1)
    assert report.by_severity("ERROR"), "the linter missed the syntax error"


def test_linter_catches_a_bad_sdk_attribute():
    """The linter flags a BigQuery attribute that does not exist.

    The linter resolves ``<module_alias>.<attr>`` against the installed
    library, so the misspelled attribute must be accessed on the module
    itself — which is exactly the mistake a reader would make after
    misremembering an SDK API.

    The BigQuery SDK is a hard dependency of the course, so this check runs
    everywhere. The Secret Manager equivalent is skipped when that SDK is
    not installed.
    """
    report = Report()
    validate_python(
        report,
        "test.py",
        "from google.cloud import bigquery\n"
        "client = bigquery.NoSuchClient()\n",
        1,
    )
    messages = [i.message for i in report.by_severity("ERROR")]
    assert any("NoSuchClient" in m for m in messages), (
        f"the linter missed the bad attribute: {messages}"
    )


def test_linter_catches_a_bad_secret_manager_attribute():
    """The linter flags a Secret Manager attribute that does not exist.

    Skipped when `google-cloud-secretmanager` is not installed, because the
    linter deliberately skips the check in that case.
    """
    if pytest is None:
        return
    try:
        import google.cloud.secretmanager  # noqa: F401, PLC0415
    except ImportError:
        return

    report = Report()
    validate_python(
        report,
        "test.py",
        "from google.cloud import secretmanager\n"
        "client = secretmanager.NoSuchClient()\n",
        1,
    )
    messages = [i.message for i in report.by_severity("ERROR")]
    assert any("NoSuchClient" in m for m in messages), (
        f"the linter missed the bad attribute: {messages}"
    )


def test_linter_accepts_valid_bigquery_usage():
    """The linter does not flag correct BigQuery code."""
    report = Report()
    validate_python(
        report,
        "test.py",
        "from google.cloud import bigquery\n"
        "client = bigquery.Client()\n"
        "dataset = client.dataset('d')\n"
        "table = dataset.table('t')\n"
        "rows = list(client.list_rows(table))\n",
        1,
    )
    assert not report.by_severity("ERROR"), (
        f"the linter flagged valid code: "
        f"{[i.message for i in report.by_severity('ERROR')]}"
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
# Merge semantics tests
# --------------------------------------------------------------------------


def test_merge_semantics_match_the_documented_table():
    """`project/cdc.py` implements the merge table the chapters teach."""
    sys.path.insert(0, str(ROOT / "project"))
    import cdc  # noqa: PLC0415

    state = cdc.CdcState(merge_keys=["customer_id"])

    def event(op, before=None, after=None):
        return cdc.ChangeEvent(
            op=op,
            before=before,
            after=after,
            source_timestamp="2026-01-01T00:00:00Z",
            server_timestamp="2026-01-01T00:00:01Z",
            key_values=("c1",),
        )

    # INSERT of a new key → inserted.
    state.apply(event(cdc.INSERT, after={"customer_id": "c1", "tier": "gold"}))
    assert state.rows[("c1",)]["tier"] == "gold"

    # INSERT of an existing key → converges, counted as a duplicate.
    state.apply(event(cdc.INSERT, after={"customer_id": "c1", "tier": "gold"}))
    assert state.skipped_reasons.get("duplicate_insert") == 1

    # UPDATE of an existing key → updated.
    state.apply(event(cdc.UPDATE, after={"customer_id": "c1", "tier": "silver"}))
    assert state.rows[("c1",)]["tier"] == "silver"

    # UPDATE of an absent key → inserted (not dropped).
    state.apply(event(cdc.UPDATE, after={"customer_id": "c2", "tier": "gold"}))
    assert ("c2",) in state.rows

    # DELETE of an absent key → no-op, counted.
    state.apply(event(cdc.DELETE, before={"customer_id": "c3"}))
    assert state.skipped_reasons.get("delete_of_absent_row") == 1

    # DELETE of a present key → removed.
    state.apply(event(cdc.DELETE, before={"customer_id": "c1"}))
    assert ("c1",) not in state.rows


def test_merge_is_idempotent():
    """Applying the same event twice has the same effect as applying it once."""
    sys.path.insert(0, str(ROOT / "project"))
    import cdc  # noqa: PLC0415

    def build():
        state = cdc.CdcState(merge_keys=["customer_id"])
        for _ in range(3):
            state.apply(
                cdc.ChangeEvent(
                    op=cdc.UPDATE,
                    before=None,
                    after={"customer_id": "c1", "amount": 10},
                    source_timestamp="2026-01-01T00:00:00Z",
                    server_timestamp="2026-01-01T00:00:01Z",
                    key_values=("c1",),
                )
            )
        return state

    assert build().rows == build().rows
    assert build().rows[("c1",)]["amount"] == 10


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------


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
