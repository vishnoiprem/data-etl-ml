"""The scoring rubric and the eval harness."""

from __future__ import annotations

import json

from copyforge_ai.config import load_settings
from copyforge_ai.evaluation import run_eval
from copyforge_ai.llm import StubRouter
from copyforge_ai.scoring import CRITERIA, MAX_SCORE, compare, score_document
from copyforge_ai.writer import write_article


class TestScoring:
    def test_the_maximum_is_the_sum_of_the_criteria(self):
        assert MAX_SCORE == sum(maximum for _, _, maximum in CRITERIA)

    def test_a_strong_draft_scores_higher_than_a_weak_one(self, strong_draft, weak_draft):
        assert score_document(strong_draft).total > score_document(weak_draft).total

    def test_the_score_is_bounded(self, strong_draft):
        score = score_document(strong_draft)
        assert 0 <= score.total <= MAX_SCORE

    def test_the_score_is_a_percentage(self, strong_draft):
        score = score_document(strong_draft)
        assert 0 <= score.percent <= 100

    def test_every_criterion_is_reported(self, strong_draft):
        score = score_document(strong_draft)
        for name, _description, _maximum in CRITERIA:
            assert name in score.per_criterion
            assert name in score.maxima

    def test_a_generic_hook_scores_lower_than_a_specific_one(self, strong_draft, weak_draft):
        assert (
            score_document(strong_draft).per_criterion["hook_specific"]
            > score_document(weak_draft).per_criterion["hook_specific"]
        )

    def test_machine_filler_is_penalised(self, weak_draft):
        score = score_document(weak_draft)
        assert score.per_criterion["no_ai_filler"] < score.maxima["no_ai_filler"]
        assert any("machine-filler" in note for note in score.notes)

    def test_a_long_paragraph_is_penalised(self):
        draft = "# T\n\n" + ("word " * 200) + "\n"
        score = score_document(draft)
        assert score.per_criterion["readability"] < score.maxima["readability"]

    def test_a_missing_cta_is_penalised(self, weak_draft):
        score = score_document(weak_draft)
        assert score.per_criterion["cta_present"] == 0

    def test_the_notes_are_empty_for_a_clean_draft(self, strong_draft):
        score = score_document(strong_draft)
        assert isinstance(score.notes, list)

    def test_the_dict_form_is_serialisable(self, strong_draft):
        payload = score_document(strong_draft).as_dict()
        assert json.dumps(payload)


class TestCompare:
    def test_the_comparison_reports_the_delta(self, weak_draft, router):
        result = write_article(weak_draft, router=router)
        comparison = compare(weak_draft, result.document)
        assert comparison["delta"] > 0
        assert comparison["improved"]

    def test_the_comparison_reports_both_scores(self, weak_draft, router):
        result = write_article(weak_draft, router=router)
        comparison = compare(weak_draft, result.document)
        assert comparison["before"]["total"] < comparison["after"]["total"]

    def test_comparing_a_document_with_itself_is_zero(self, strong_draft):
        comparison = compare(strong_draft, strong_draft)
        assert comparison["delta"] == 0
        assert not comparison["improved"]


class TestEvaluation:
    def test_the_harness_runs_over_the_sample_drafts(self):
        settings = load_settings()
        drafts = sorted(settings.data_dir.glob("*.md"))
        assert drafts, "the sample drafts are missing"

        result = run_eval(drafts, settings, router=StubRouter())
        assert result.drafts
        assert result.skipped == []

    def test_the_mean_score_delta_is_positive(self):
        settings = load_settings()
        drafts = sorted(settings.data_dir.glob("*.md"))
        result = run_eval(drafts, settings, router=StubRouter())
        assert result.mean_delta() > 0

    def test_every_draft_is_idempotent(self):
        settings = load_settings()
        drafts = sorted(settings.data_dir.glob("*.md"))
        result = run_eval(drafts, settings, router=StubRouter())
        assert result.idempotent_ratio() == 1.0

    def test_every_draft_preserves_the_author_text(self):
        settings = load_settings()
        drafts = sorted(settings.data_dir.glob("*.md"))
        result = run_eval(drafts, settings, router=StubRouter())
        assert result.preserved_ratio() == 1.0

    def test_the_acceptance_gate_passes(self):
        settings = load_settings()
        drafts = sorted(settings.data_dir.glob("*.md"))
        result = run_eval(drafts, settings, router=StubRouter())
        assert result.passed, result.acceptance

    def test_a_missing_draft_is_skipped_not_failed(self, tmp_path):
        settings = load_settings()
        result = run_eval(
            [tmp_path / "does-not-exist.md"], settings, router=StubRouter()
        )
        assert result.skipped == ["does-not-exist.md"]
        assert result.drafts == []

    def test_an_empty_draft_is_skipped(self, tmp_path):
        path = tmp_path / "empty.md"
        path.write_text("")
        result = run_eval([path], load_settings(), router=StubRouter())
        assert result.skipped == ["empty.md"]

    def test_the_result_is_serialisable(self):
        settings = load_settings()
        drafts = sorted(settings.data_dir.glob("*.md"))
        result = run_eval(drafts, settings, router=StubRouter())
        assert json.dumps(result.as_dict())

    def test_the_router_name_is_reported(self):
        settings = load_settings()
        drafts = sorted(settings.data_dir.glob("*.md"))
        result = run_eval(drafts, settings, router=StubRouter())
        assert result.router == "stub"


class TestEvaluationCli:
    def test_the_cli_writes_a_report(self, tmp_path):
        from copyforge_ai import evaluation

        out = tmp_path / "eval.json"
        code = evaluation.main(
            ["--out", str(out), "--drafts", str(load_settings().data_dir)]
        )
        assert code == 0
        assert out.exists()
        payload = json.loads(out.read_text())
        assert payload["passed"]

    def test_the_cli_fails_when_there_is_nothing_to_evaluate(self, tmp_path):
        from copyforge_ai import evaluation

        code = evaluation.main(["--drafts", str(tmp_path / "empty-dir")])
        assert code == 1
