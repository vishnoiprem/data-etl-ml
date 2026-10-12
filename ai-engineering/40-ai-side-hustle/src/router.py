"""
router.py -- Pluggable LLM router.

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


# ---------------------------------------------------------------- stubs

_LONG_EBOOK_TEMPLATE = """\
# {{title}}

## Chapter 1 -- The Setup

Most people overthink the start. Here's the minimum viable version.

Most beginners spend the first month choosing tools. That's a mistake. Tools change. The fundamentals don't.

The minimum viable version of {{topic}} looks like:

- Pick one problem to solve (not three).
- Pick one tool to use (not the best one, the one you'll actually open).
- Do the thing for 30 days.
- Review what worked, what didn't, what to change.
- Repeat, with one small improvement per cycle.

That's the whole game. The rest of this book is elaboration on the same idea.

The reason this works is that the first month is not about producing output. It's about building the muscle. The output comes later, when the muscle is strong enough to bear weight. Most people quit in month one because they expected output before the muscle was ready. They thought "I've been doing this for two weeks, why don't I have anything to show?" The answer is: because that's not how muscles work. You don't deadlift 300 pounds on day one. You deadlift 95, then 135, then 185, then 225. After six months, 300.

The same is true for {{topic}}. Day one is a single rep. Day thirty is maybe five pounds heavier. Day ninety is when you start to see the curve.

The mistake most people make is treating day one like it should feel like day ninety. It doesn't. Day one feels pointless. Day thirty feels barely better. Day ninety is when the compounding kicks in. The reason most people never see day ninety is they don't survive day thirty.

So the only goal of this chapter is to convince you to survive the first thirty days. If you can do that, the rest of this book is unnecessary. If you can't, no amount of strategy will save you.

## Chapter 2 -- The Work

Three habits that compound: write daily, ship weekly, review monthly.

**Write daily.** Twenty minutes is enough. The point isn't output, it's the practice of putting thoughts into words. If you can't articulate a problem in a paragraph, you don't understand it yet.

Here's a useful test: at the end of each day, write one paragraph about what you worked on. Not for an audience, not for posterity, just for yourself. If you can't, you didn't actually understand the work. The act of writing forces clarity. After thirty days of this, you will be able to explain your work to anyone in under five minutes. That is a superpower.

**Ship weekly.** A bad first draft is worth more than a perfect plan. Pick the smallest thing that could possibly be useful, finish it, and put it in front of one real person. Their reaction is data; your assumptions are not.

The key word here is "real." A friend who will tell you it's great is not a real person. A real person is someone who will not lie to spare your feelings. Find three of them by month two. The first will be hard to find; the second and third will be referrals from the first.

**Review monthly.** Block 90 minutes on the last Friday of the month. What shipped? What didn't? What surprised you? What's the one thing to do differently next month? Write the answers down.

The review is the most skipped step. It's the most important. Without it, you are running on autopilot. You will repeat your month-one mistakes in month-six. With it, you compound.

## Chapter 3 -- The Payoff

Twelve months from now, you'll be in the top 5% if you actually do the work. The catch: most won't. That's the opportunity.

Why do most people quit? Not because the work is hard. Because the feedback loop is slow. The first month feels like nothing is happening. The second month still feels slow. By month three, you have something, but it's still small. The compounding starts around month four, and by month six, you realize you're now ahead of everyone who said they'd start "next month."

The hardest part is surviving the first three months. The way you survive them is by having a feedback loop you trust: write daily, ship weekly, review monthly. The numbers don't lie.

Here is a useful reframe: the goal of the first three months is not to make money. The goal is to gather enough signal to know whether to continue. If after three months you have zero users and zero revenue, you probably picked the wrong thing. Pivot. If you have one user who pays you and emails you back, you picked the right thing. Double down.

## Chapter 4 -- The Common Traps

**Trap 1: Tool-switching.** Every time you switch tools, you lose a week re-learning. Pick one. Use it for 90 days before evaluating.

**Trap 2: Audience-watching.** You don't have an audience yet. Stop optimizing for them. Optimize for the one person you can help this week.

**Trap 3: Pricing-paralysis.** If you can't decide on a price, pick $19. The point isn't the money. The point is the signal of someone paying you. You can raise the price later.

**Trap 4: Done-itis.** Finishing the first version is not the goal. Finishing the first *useful* version is. Ship when it's embarrassing; iterate from there.

**Trap 5: Public-perfectionism.** Hiding until it's "ready" is the slowest path. Ship early, ship often, let the public see the mess. The people who like you for the polished version will leave when you stumble. The people who like you for the work will stay.

**Trap 6: Comparing-up.** Comparing yourself to the leader in your space is demoralizing and useless. Compare yourself to yourself from 30 days ago. That's the only comparison that matters.

## Chapter 5 -- The 90-Day Plan

Week 1-2: Set up. Pick the tool. Pick the topic. Do the thing every day for 14 days. Don't publish anything yet.

Week 3-4: First ship. Publish something small. Get one real user. Listen to their feedback. Fix the worst gap.

Week 5-8: Compound. Publish weekly. Talk to one user per week. Track what they say. The pattern becomes visible by week 6.

Week 9-12: Scale (a little). If the thing is working, do more of what worked. If it's not, kill it. Both are wins.

The hardest week is week 4. By then the novelty is gone and you don't yet have evidence the work matters. The work matters in week 8. The work pays in week 12. The trick is surviving weeks 4-7 with no evidence. The only thing that gets you through is the daily write and the weekly ship. They are evidence you are still doing the work.

## Appendix A -- Resources

- Book: Show Your Work -- Austin Kleon
- Book: The Mom Test -- Rob Fitzpatrick
- Book: Company of One -- Paul Jarvis
- Tool: a plain text file you actually open
- Habit: one Pomodoro a day

## Appendix B -- Common Questions

**Q: How long until I see results?**
A: 4-12 weeks if you ship weekly. 12-24 weeks if you ship monthly. Never if you ship never.

**Q: What's the #1 tool?**
A: The one you'll actually use. Discipline beats tooling.

**Q: What if I miss a day?**
A: Don't miss two. The streak matters less than the recovery.

**Q: Should I quit my job?**
A: Not until you've done this for 90 days on the side and have signal that it works.

**Q: How do I find my first user?**
A: Go where they already are. Help one person for free. They'll tell two people.

## Conclusion

You don't need more information. You need 30 days of doing the thing. The book is the easy part. The doing is the work. Start tomorrow morning. Or tonight. Either is fine.

If you do this and it works, email me. I want to hear about it.

If you do this and it doesn't work, email me anyway. I want to hear what you learned.

Either way, the book is a small thing. The doing is the big thing. Go.
"""


# ---------------------------------------------------------------- router

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
        if "merch copywriter" in s or "print-on-demand" in s or "merch" in s:
            return self._stub_merch_text(prompt)
        if "outreach" in p or "cold email" in p or "subject:" in p:
            return self._stub_saas_copy(prompt)
        return self._stub_generic(prompt)

    def json(self, prompt: str, schema_hint: str = "", max_tokens: int = 1024) -> dict:
        hint = schema_hint.lower()
        if "keyword" in hint or "difficulty" in hint:
            return self._stub_keyword_json(prompt)
        if '"merch"' in hint or "slogan" in hint:
            return self._stub_merch_json(prompt)
        if '"ideas"' in hint or ("idea" in hint and "saas" in hint):
            return self._stub_idea_json(prompt)
        if "product" in hint or "title" in hint:
            return self._stub_product_json(prompt)
        p = prompt.lower()
        if "keyword" in p or "difficulty" in p:
            return self._stub_keyword_json(prompt)
        if "merch" in p or "slogan" in p:
            return self._stub_merch_json(prompt)
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
            f"A: 4-12 weeks if you ship weekly.\n\n"
            f"**Q: What's the #1 tool?**\n"
            f"A: The one you'll actually use. Discipline beats tooling.\n\n"
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
        """A 5-chapter eBook stub. ~1,500 words / ~5 pages."""
        title = StubRouter._extract(prompt, "Title") or "The Short Guide"
        topic = StubRouter._extract(prompt, "Topic") or "the work"
        return _LONG_EBOOK_TEMPLATE.format(title=title, topic=topic)

    @staticmethod
    def _stub_merch_text(prompt: str) -> str:
        topic = StubRouter._extract(prompt, "Topic") or "your topic"
        return (
            f"# {topic} -- Merch Concept\n\n"
            f"Slogan: Ship {topic} or die trying.\n"
            f"Format: t-shirt, mug, sticker\n"
            f"Designer brief: Bold sans-serif, single color, "
            f"icon of a rocket + the slogan below."
        )

    @staticmethod
    def _stub_merch_json(prompt: str) -> dict:
        topic = StubRouter._extract(prompt, "Topic") or "your topic"
        return {
            "merch": [
                {"slogan": f"Powered by {topic}", "format": "t-shirt",
                 "audience": f"{topic} enthusiasts",
                 "designer_brief": "Bold retro type, single color, no clipart."},
                {"slogan": f"{topic.title()} and chillin'", "format": "mug",
                 "audience": "tech workers",
                 "designer_brief": "Hand-lettered wordmark, two-color, mug wrap."},
                {"slogan": f"404: {topic} not found", "format": "sticker",
                 "audience": "developers",
                 "designer_brief": "3-inch die-cut, glossy vinyl, glitch-style type."},
            ]
        }

    @staticmethod
    def _stub_generic(prompt: str) -> str:
        return "OK"

    @staticmethod
    def _stub_keyword_json(prompt: str) -> dict:
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
