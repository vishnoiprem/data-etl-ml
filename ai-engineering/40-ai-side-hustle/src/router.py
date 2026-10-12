"""
router.py — Pluggable LLM router.

Same pattern as 39-revenue-pipeline, but the stub here generates
diverse output (SEO articles, SaaS landing copy, eBook chapters) so
the demo shows real, readable content rather than placeholder text.
"""

from __future__ import annotations

import json
import re
from typing import Protocol


class LLMRouter(Protocol):
    def complete(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str: ...
    def json(self, prompt: str, schema_hint: str = "", max_tokens: int = 1024) -> dict: ...


class StubRouter:
    """Offline router. Returns template-based content for demos/tests."""

    name = "stub"

    def complete(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str:
        s = (system or "").lower()
        p = prompt.lower()
        if "seo writer" in s or "seo article" in s or "blog post" in s:
            return self._stub_seo_article(prompt)
        if "saas copywriter" in s or "landing page" in s or "marketing copy" in s:
            return self._stub_saas_copy(prompt)
        if "ebook author" in s or "nonfiction author" in s or "ebook" in s:
            return self._stub_ebook(prompt)
        if "outreach" in p or "cold email" in p or "subject:" in p:
            return self._stub_saas_copy(prompt)
        return self._stub_generic(prompt)

    def json(self, prompt: str, schema_hint: str = "", max_tokens: int = 1024) -> dict:
        hint = schema_hint.lower()
        if "keyword" in hint or "difficulty" in hint:
            return self._stub_keyword_json(prompt)
        # The SaaS-idea schema uses the key "ideas"; the schema_hint
        # contains `"ideas":` so check that exact substring.
        if '"ideas"' in hint or ("idea" in hint and "saas" in hint):
            return self._stub_idea_json(prompt)
        if "product" in hint or "title" in hint:
            return self._stub_product_json(prompt)
        p = prompt.lower()
        if "keyword" in p or "difficulty" in p:
            return self._stub_keyword_json(prompt)
        if "niche" in p and "idea" in p:
            return self._stub_idea_json(prompt)
        if "topic" in p and "product" in p:
            return self._stub_product_json(prompt)
        return {"text": self._stub_generic(prompt)}

    # ---------- internal stubs ----------
    @staticmethod
    def _extract(prompt: str, label: str, default: str = "") -> str:
        """Pull `Label: value` from the prompt (case-insensitive)."""
        m = re.search(rf"(?im)^{re.escape(label)}\s*:\s*(.+)$", prompt)
        return m.group(1).strip() if m else default

    @staticmethod
    def _stub_seo_article(prompt: str) -> str:
        kw = StubRouter._extract(prompt, "Keyword") or "your topic"
        title = StubRouter._extract(prompt, "Title") or f"The Ultimate Guide to {kw.title()}"
        return (
            f"# {title}\n\n"
            f"## What is {kw}?\n"
            f"{kw.capitalize()} is the practice of doing a specific thing well. "
            f"Most people get it wrong because they skip the basics. This guide "
            f"walks through the fundamentals, the common pitfalls, and the exact "
            f"workflow the pros use.\n\n"
            f"## Why {kw} matters in 2026\n"
            f"Three reasons: (1) costs are down, (2) demand is up, (3) the tooling "
            f"finally works. If you're not doing {kw} yet, you're leaving money on "
            f"the table.\n\n"
            f"## Step-by-step\n"
            f"1. **Audit your baseline.** Measure where you are today.\n"
            f"2. **Pick one lever.** Don't boil the ocean.\n"
            f"3. **Ship a v0.** A bad first attempt beats a perfect plan.\n"
            f"4. **Measure and iterate.** Weekly check-ins.\n"
            f"5. **Double down on what works.** Kill what doesn't.\n\n"
            f"## Common mistakes\n"
            f"- Skipping the audit.\n- Boiling the ocean.\n- Waiting too long "
            f"to ship.\n- Refusing to measure.\n- Refusing to kill.\n\n"
            f"## FAQ\n"
            f"**Q: How long until I see results?**\n"
            f"A: 4–12 weeks if you ship weekly.\n\n"
            f"**Q: What's the #1 tool?**\n"
            f"A: The one you'll actually use. Discipline > tooling.\n\n"
            f"## Conclusion\n"
            f"{kw.capitalize()} is a skill, not a secret. Apply the steps above "
            f"and you'll be ahead of 90% of people who 'plan to start soon.'"
        )

    @staticmethod
    def _stub_saas_copy(prompt: str) -> str:
        idea = StubRouter._extract(prompt, "Idea") or "your idea"
        return (
            f"Headline: Ship {idea} in a weekend, not a quarter.\n"
            f"Subhead: The fastest way to validate, launch, and charge for {idea}.\n\n"
            f"Section 1: The problem\n"
            f"Every team knows they need {idea}, but the existing tools are slow, "
            f"expensive, or both. You waste weeks wiring things together instead "
            f"of shipping.\n\n"
            f"Section 2: How it works\n"
            f"1. Sign up (no credit card).\n"
            f"2. Connect your data in 60 seconds.\n"
            f"3. Get results the same day.\n\n"
            f"Section 3: Pricing\n"
            f"- Free: 1 project, 100 events/mo.\n"
            f"- Pro ($19/mo): unlimited projects, 10k events/mo, priority support.\n"
            f"- Team ($99/mo): everything in Pro + 5 seats + SSO.\n\n"
            f"Section 4: CTA\n"
            f"Start free. Upgrade when you outgrow it."
        )

    @staticmethod
    def _stub_ebook(prompt: str) -> str:
        title = StubRouter._extract(prompt, "Title") or "The Short Guide"
        return (
            f"# {title}\n\n"
            f"## Chapter 1 — The Setup\n"
            f"Most people overthink the start. Here's the minimum viable version.\n\n"
            f"## Chapter 2 — The Work\n"
            f"Three habits that compound: write daily, ship weekly, review monthly.\n\n"
            f"## Chapter 3 — The Payoff\n"
            f"Twelve months from now, you'll be in the top 5% if you actually do "
            f"the work. The catch: most won't. That's the opportunity.\n\n"
            f"## Appendix — Resources\n"
            f"- Book: Show Your Work — Austin Kleon\n"
            f"- Tool: a plain text file you actually open\n"
            f"- Habit: one Pomodoro a day\n"
        )

    @staticmethod
    def _stub_generic(prompt: str) -> str:
        return "OK"

    @staticmethod
    def _stub_keyword_json(prompt: str) -> dict:
        # Try to extract a seed keyword
        seed = StubRouter._extract(prompt, "Seed") or StubRouter._extract(prompt, "Topic") or "ai"
        return {
            "keywords": [
                {"keyword": f"best {seed} tools 2026", "volume": 1200, "difficulty": 22,
                 "intent": "commercial", "cpc_usd": 4.20},
                {"keyword": f"{seed} for beginners", "volume": 850, "difficulty": 15,
                 "intent": "informational", "cpc_usd": 1.10},
                {"keyword": f"how to use {seed}", "volume": 2400, "difficulty": 35,
                 "intent": "informational", "cpc_usd": 2.50},
                {"keyword": f"{seed} vs alternative", "volume": 480, "difficulty": 18,
                 "intent": "comparison", "cpc_usd": 3.10},
                {"keyword": f"cheap {seed} alternative", "volume": 320, "difficulty": 12,
                 "intent": "commercial", "cpc_usd": 5.80},
            ]
        }

    @staticmethod
    def _stub_idea_json(prompt: str) -> dict:
        niche = StubRouter._extract(prompt, "Niche") or "developers"
        return {
            "ideas": [
                {"name": f"{niche.title()}Audit", "one_liner":
                 f"An automated weekly audit for {niche} teams.", "mvp_weeks": 1,
                 "tam_usd": 50_000_000, "price_usd": 19, "moat": "data flywheel"},
                {"name": f"StandupBot", "one_liner":
                 f"Async standups for distributed {niche} teams.", "mvp_weeks": 1,
                 "tam_usd": 20_000_000, "price_usd": 9, "moat": "Slack-native UX"},
                {"name": f"{niche.title()}Hound", "one_liner":
                 f"AI copilot that finds {niche} bugs before they ship.", "mvp_weeks": 2,
                 "tam_usd": 80_000_000, "price_usd": 29, "moat": "model fine-tuned on bugs"},
            ]
        }

    @staticmethod
    def _stub_product_json(prompt: str) -> dict:
        topic = StubRouter._extract(prompt, "Topic") or "productivity"
        return {
            "products": [
                {"title": f"The {topic.title()} Playbook", "format": "ebook",
                 "price_usd": 19, "page_count": 42, "hook": f"Everything I learned about {topic} in 90 days."},
                {"title": f"{topic.title()} Notion Bundle", "format": "template",
                 "price_usd": 12, "page_count": 0, "hook": f"10 plug-and-play {topic} dashboards."},
                {"title": f"{topic.title()} Cheat Sheet (Printable)", "format": "printable",
                 "price_usd": 7, "page_count": 4, "hook": f"Pin it to your wall. Do the {topic} thing."},
            ]
        }


class AnthropicRouter:
    name = "anthropic"

    def __init__(self, model: str = "claude-3-5-haiku-20241022") -> None:
        try:
            import anthropic  # type: ignore
        except ImportError as e:
            raise ImportError("AnthropicRouter requires `pip install anthropic`") from e
        self._client = anthropic.Anthropic()
        self._model = model

    def complete(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str:
        msg = self._client.messages.create(
            model=self._model, max_tokens=max_tokens,
            system=system or "You are a helpful assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text  # type: ignore[index]

    def json(self, prompt: str, schema_hint: str = "", max_tokens: int = 1024) -> dict:
        text = self.complete(
            prompt + (f"\n\nRespond with JSON matching: {schema_hint}" if schema_hint else
                      "\n\nRespond with valid JSON only."),
            system="You output strictly valid JSON.",
            max_tokens=max_tokens,
        )
        text = re.sub(r"^```(?:json)?\s*", "", text.strip())
        text = re.sub(r"\s*```$", "", text.strip())
        return json.loads(text)


class OpenAIRouter:
    name = "openai"

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        try:
            import openai  # type: ignore
        except ImportError as e:
            raise ImportError("OpenAIRouter requires `pip install openai`") from e
        self._client = openai.OpenAI()
        self._model = model

    def complete(self, prompt: str, system: str = "", max_tokens: int = 1024) -> str:
        resp = self._client.chat.completions.create(
            model=self._model, max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system or "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        return resp.choices[0].message.content or ""

    def json(self, prompt: str, schema_hint: str = "", max_tokens: int = 1024) -> dict:
        resp = self._client.chat.completions.create(
            model=self._model, max_tokens=max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You output strictly valid JSON."},
                {"role": "user", "content": prompt + (
                    f"\n\nSchema: {schema_hint}" if schema_hint else "")},
            ],
        )
        return json.loads(resp.choices[0].message.content or "{}")


def get_default_router() -> LLMRouter:
    try:
        return AnthropicRouter()
    except Exception:  # noqa: BLE001
        pass
    try:
        return OpenAIRouter()
    except Exception:  # noqa: BLE001
        pass
    return StubRouter()
