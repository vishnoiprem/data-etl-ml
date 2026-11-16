"""The evaluation harness: planted anomalies, planted decoys, and the gates."""

from __future__ import annotations

from aws_cost_analyzer.evaluation import (
    ACCEPTANCE,
    build_corpus,
    evaluate,
    render,
)


class TestTheCorpus:
    def test_it_has_one_anomaly_per_detector(self):
        corpus = build_corpus()
        detectors = {a.detector for a in corpus.anomalies}
        assert detectors == {"growth", "access", "lifecycle", "allocation"}

    def test_it_has_decoys(self):
        corpus = build_corpus()
        assert len(corpus.decoys) >= 4

    def test_it_covers_six_months(self):
        corpus = build_corpus()
        periods = {r.period_label for r in corpus.input.records}
        assert len(periods) == 6

    def test_the_decoys_name_their_trap(self):
        corpus = build_corpus()
        notes = " ".join(d.note for d in corpus.decoys)
        assert "seasonal" in notes
        assert "doubled" in notes


class TestTheGates:
    def test_the_whole_evaluation_passes(self):
        result = evaluate()
        assert result.passed, render(result)

    def test_every_anomaly_is_found(self):
        result = evaluate()
        assert result.missed_targets == []

    def test_no_decoy_fires(self):
        result = evaluate()
        assert result.false_positives == []

    def test_the_recall_gates_are_all_one(self):
        result = evaluate()
        for gate in result.gates:
            if gate.name.endswith("_recall"):
                assert gate.actual == 1.0

    def test_the_target_match_gate_requires_an_exact_name(self):
        # "Some S3 bucket grew" scores 1.00 on recall. The target gate
        # is what makes recall meaningful.
        result = evaluate()
        gate = next(g for g in result.gates if g.name == "min_target_match")
        assert gate.actual == 1.0

    def test_the_savings_ratio_gate_is_not_fixture_dependent(self):
        # The tool may not claim more avoidable cost than the measured
        # spend it came from.
        result = evaluate()
        gate = next(g for g in result.gates if g.name == "max_savings_to_measured_ratio")
        assert gate.actual <= 1.0

    def test_every_modelled_figure_has_volume_evidence(self):
        result = evaluate()
        gate = next(g for g in result.gates if g.name == "max_unbacked_modelled")
        assert gate.actual == 0.0

    def test_every_saving_carries_a_basis(self):
        result = evaluate()
        gate = next(g for g in result.gates if g.name == "max_savings_without_basis")
        assert gate.actual == 0.0

    def test_the_tag_filter_gate_is_the_console_translation(self):
        result = evaluate()
        gate = next(g for g in result.gates if g.name == "min_tag_filter_match")
        assert gate.passed
        assert "CONTAINS" in gate.detail

    def test_the_normalizer_gate_is_the_row_count(self):
        result = evaluate()
        gate = next(g for g in result.gates if g.name == "min_ce_normalizer_rows")
        assert gate.passed

    def test_every_acceptance_gate_is_checked(self):
        result = evaluate()
        names = {g.name for g in result.gates}
        assert names == set(ACCEPTANCE)

    def test_a_failing_gate_makes_the_evaluation_fail(self):
        from aws_cost_analyzer.evaluation import GateResult

        result = evaluate()
        result.gates.append(GateResult("fake", 1.0, 0.0, False))
        assert not result.passed


class TestRendering:
    def test_it_shows_each_gate(self):
        text = render(evaluate())
        assert "min_growth_recall" in text
        assert "max_false_positives" in text

    def test_it_states_the_verdict(self):
        text = render(evaluate())
        assert "Acceptance: PASS" in text

    def test_the_result_serialises(self):
        import json

        json.dumps(evaluate().to_dict())
