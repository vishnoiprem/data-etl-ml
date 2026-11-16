"""The model layer — the stub, the Ollama backend, and the selection."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from copyforge_ai.llm import (
    LLMError,
    OllamaRouter,
    StubRouter,
    get_default_router,
)


class TestStubRouter:
    def test_it_returns_text_for_a_framework_prompt(self):
        prompt = (
            "Write one Problem–Agitate–Solve block for the article below.\n\n"
            "Framework: Problem–Agitate–Solve — Name the pain.\n\n"
            "Article context:\nOur pipeline finished but the numbers were wrong.\n"
        )
        out = StubRouter().complete(prompt)
        assert out.strip()
        assert len(out.split()) > 10

    def test_it_is_deterministic(self):
        prompt = "Framework: Curiosity Gap — Open on an oddity.\n\nArticle context:\nA thing happened.\n"
        router = StubRouter()
        assert router.complete(prompt) == router.complete(prompt)

    def test_two_different_drafts_produce_different_blocks(self):
        prompt = (
            "Framework: Problem–Agitate–Solve — Name the pain.\n\n"
            "Article context:\n{context}\n"
        )
        router = StubRouter()
        one = router.complete(prompt.format(context="The billing job failed on Tuesday."))
        two = router.complete(prompt.format(context="The Kubernetes cluster drained its disk."))
        assert one != two

    def test_an_empty_prompt_returns_empty(self):
        assert StubRouter().complete("") == ""

    def test_an_unknown_framework_returns_empty(self):
        assert StubRouter().complete("Framework: Not A Framework — x") == ""

    def test_the_block_covers_every_slot(self):
        from copyforge_ai.frameworks import get_framework

        framework = get_framework("pas")
        prompt = f"Framework: {framework.name} — {framework.summary}\n\nArticle context:\nSomething happened here.\n"
        out = StubRouter().complete(prompt)
        # Three slots → three paragraphs.
        assert len([p for p in out.split("\n\n") if p.strip()]) == len(framework.slots)

    def test_it_does_not_launder_machine_filler(self):
        """The stub must not copy a filler phrase into a new block."""
        prompt = (
            "Framework: Contrarian Open — Disagree with the consensus.\n\n"
            "Article context:\n"
            "In today's fast-paced world, data teams are under pressure.\n"
            "A specific second paragraph about a 4-minute pipeline.\n"
        )
        out = StubRouter().complete(prompt).lower()
        assert "fast-paced world" not in out

    def test_a_list_slot_produces_a_list(self):
        from copyforge_ai.frameworks import get_framework

        framework = get_framework("problem_list")
        prompt = f"Framework: {framework.name} — {framework.summary}\n\nArticle context:\nSomething happened.\n"
        out = StubRouter().complete(prompt)
        assert out.strip().startswith("-")

    def test_it_writes_about_the_title_not_the_opening_sentence(self):
        """The title names the subject; the first sentence names the situation.

        Sourcing every slot from the opening sentence produced blocks
        that restated the article's own intro — a "Concrete Example"
        whose example was the intro, which is structurally valid and
        semantically empty.
        """
        prompt = (
            "Framework: Concrete Example — Show one real instance.\n\n"
            "Article title: Fifteen Years of Data Engineering: What Actually Scales\n\n"
            "Article context:\n"
            "Data engineering has changed a lot over fifteen years. There are "
            "many things to think about.\n"
        )
        out = StubRouter().complete(prompt)
        assert "data engineering" in out.lower()
        assert "there are many things to think about" not in out.lower()

    def test_the_title_wins_over_the_context(self):
        prompt = (
            "Framework: Contrarian Open — Disagree with the consensus.\n\n"
            "Article title: Cost Control in Batch Pipelines\n\n"
            "Article context:\nThe pipeline finished but the numbers were wrong.\n"
        )
        out = StubRouter().complete(prompt)
        assert "cost control" in out.lower()

    def test_the_subject_is_a_noun_phrase(self):
        """A title is not a noun phrase; it is a sentence about a subject."""
        from copyforge_ai.llm import _subject

        # A duration is part of the subject — the fifteen years IS the
        # claim, so the number must survive.
        assert _subject("Fifteen Years of Data Engineering: What Actually Scales") == (
            "Fifteen Years of Data Engineering"
        )
        # Framing is not: the genre word and the item count describe the
        # packaging, not the subject.
        assert _subject("A Guide to Data Engineering") == "Data Engineering"
        assert _subject("10 Tips for Data Engineering") == "Data Engineering"
        assert _subject("Five Mistakes in Pipeline Design") == "Pipeline Design"
        # A plain title is left alone.
        assert _subject("Scaling Data Pipelines") == "Scaling Data Pipelines"

    def test_it_has_a_name(self):
        assert StubRouter().name == "stub"


class TestOllamaRouter:
    def test_it_has_a_name(self):
        assert OllamaRouter().name == "ollama"

    def test_an_unreachable_server_raises(self):
        router = OllamaRouter(host="http://127.0.0.1:9")
        with pytest.raises(LLMError):
            router.complete("ping")

    def test_json_raises_when_there_is_no_json(self):
        router = OllamaRouter(host="http://127.0.0.1:9")
        with pytest.raises(LLMError):
            router.json("ping")

    def test_it_defaults_to_a_local_host(self):
        assert OllamaRouter().host == "http://localhost:11434"


class TestSelection:
    def test_the_default_is_the_stub(self):
        with patch.dict(os.environ, {}, clear=True):
            assert isinstance(get_default_router(), StubRouter)

    def test_an_unreachable_ollama_falls_back_to_the_stub(self):
        env = {
            "COPYFORGE_LLM_PROVIDER": "ollama",
            "COPYFORGE_OLLAMA_HOST": "http://127.0.0.1:9",
        }
        with patch.dict(os.environ, env, clear=True):
            assert isinstance(get_default_router(), StubRouter)

    def test_the_provider_is_read_from_the_environment(self):
        env = {"COPYFORGE_LLM_PROVIDER": "ollama", "COPYFORGE_OLLAMA_HOST": "http://127.0.0.1:9"}
        with patch.dict(os.environ, env, clear=True):
            # Unreachable → stub, but the provider *was* honoured.
            assert get_default_router().name == "stub"

    def test_a_blank_provider_falls_back_to_the_stub(self):
        with patch.dict(os.environ, {"COPYFORGE_LLM_PROVIDER": "  "}, clear=True):
            assert isinstance(get_default_router(), StubRouter)

    def test_an_unknown_provider_falls_back_to_the_stub(self):
        with patch.dict(os.environ, {"COPYFORGE_LLM_PROVIDER": "openai"}, clear=True):
            assert isinstance(get_default_router(), StubRouter)

    def test_the_router_satisfies_the_protocol(self):
        from copyforge_ai.llm import LLMRouter

        assert isinstance(StubRouter(), LLMRouter)
        assert isinstance(OllamaRouter(), LLMRouter)
