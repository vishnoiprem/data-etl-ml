"""End-to-end: the CLI, the demo, and the full pipeline over the samples."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = PROJECT_ROOT / "scripts"


def _run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        env={
            "PYTHONPATH": str(PROJECT_ROOT / "src"),
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "HOME": "/tmp",
        },
        check=False,
    )


class TestCli:
    def test_the_dry_run_prints_the_plan(self, tmp_path):
        draft = tmp_path / "draft.md"
        draft.write_text(
            "# T\n\nIn today's fast-paced world, pipelines are hard and nobody "
            "knows what to do about it.\n\n## End\n\nIn conclusion, it is a "
            "journey.\n"
        )
        result = _run("write_article.py", str(draft), "--dry-run")
        assert result.returncode == 0, result.stderr
        assert "Plan for" in result.stdout
        assert "cta" in result.stdout

    def test_it_writes_an_output_file(self, tmp_path):
        draft = tmp_path / "draft.md"
        draft.write_text(
            "# T\n\nIn today's fast-paced world, pipelines are hard and nobody "
            "knows what to do about it.\n\n## End\n\nIn conclusion, it is a "
            "journey.\n"
        )
        out = tmp_path / "out.md"
        result = _run("write_article.py", str(draft), "-o", str(out))
        assert result.returncode == 0, result.stderr
        assert out.exists()
        assert "copyforge:" in out.read_text()

    def test_it_writes_in_place(self, tmp_path):
        draft = tmp_path / "draft.md"
        original = (
            "# T\n\nIn today's fast-paced world, pipelines are hard and nobody "
            "knows what to do about it.\n\n## End\n\nIn conclusion, it is a "
            "journey.\n"
        )
        draft.write_text(original)
        result = _run("write_article.py", str(draft), "--in-place")
        assert result.returncode == 0, result.stderr
        assert draft.read_text() != original
        assert "copyforge:" in draft.read_text()

    def test_a_missing_file_fails_cleanly(self, tmp_path):
        result = _run("write_article.py", str(tmp_path / "nope.md"))
        assert result.returncode == 1
        assert "No such file" in result.stderr

    def test_the_score_is_reported(self, tmp_path):
        draft = tmp_path / "draft.md"
        draft.write_text(
            "# T\n\nIn today's fast-paced world, pipelines are hard and nobody "
            "knows what to do about it.\n\n## End\n\nIn conclusion, it is a "
            "journey.\n"
        )
        result = _run("write_article.py", str(draft))
        assert "rubric score" in result.stdout


class TestDemo:
    def test_the_demo_runs(self):
        result = _run("run_demo.py")
        assert result.returncode == 0, result.stderr
        assert "CopyForge AI" in result.stdout

    def test_the_demo_writes_a_report(self):
        result = _run("run_demo.py")
        assert result.returncode == 0, result.stderr
        report = PROJECT_ROOT / "reports" / "copyforge_report.json"
        assert report.exists()
        payload = json.loads(report.read_text())
        assert payload["blocks"]
        assert payload["score"]["delta"] > 0

    def test_the_report_only_mode_is_quiet(self):
        result = _run("run_demo.py", "--report-only")
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == ""


class TestPipeline:
    def test_the_full_pipeline_improves_the_score(self, weak_draft, router):
        from copyforge_ai.scoring import compare
        from copyforge_ai.writer import write_article

        result = write_article(weak_draft, router=router)
        comparison = compare(weak_draft, result.document)
        assert comparison["delta"] > 0

    def test_the_pipeline_preserves_every_author_paragraph(self, weak_draft, router):
        from copyforge_ai.markdown import parse
        from copyforge_ai.writer import write_article

        result = write_article(weak_draft, router=router)
        after = [b.text.strip() for b in parse(result.document).prose_blocks()]
        for paragraph in [
            b.text.strip() for b in parse(weak_draft).prose_blocks() if b.text.strip()
        ]:
            assert paragraph in after

    def test_the_pipeline_is_idempotent(self, weak_draft, router):
        from copyforge_ai.writer import write_article

        first = write_article(weak_draft, router=router)
        second = write_article(first.document, router=router)
        assert second.document == first.document

    def test_every_sample_draft_improves(self, router):
        from copyforge_ai.scoring import compare
        from copyforge_ai.writer import write_article

        for path in sorted((PROJECT_ROOT / "data").glob("*.md")):
            original = path.read_text()
            result = write_article(original, router=router)
            comparison = compare(original, result.document)
            assert comparison["delta"] > 0, f"{path.name} did not improve"


@pytest.mark.parametrize("name", ["sample_draft.md", "sample_draft_2.md"])
def test_the_sample_drafts_exist(name):
    assert (PROJECT_ROOT / "data" / name).exists()
