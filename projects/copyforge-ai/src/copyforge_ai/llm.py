"""The model layer: a local Ollama backend with a deterministic stub.

The model writes the *words*. It does not decide where the words go —
that is the planner's job, and it is plain Python. Keeping those two
apart is what makes the output reproducible and the tests hermetic.

Two backends:

``StubRouter``
    Deterministic. It parses the framework's slots out of the prompt and
    assembles a real block from them, using the framework's worked
    example as the register. This is what CI runs against and what the
    demo uses. It is not a mock that returns "" — it produces copy that
    is actually usable, so the offline path is worth exercising.

``OllamaRouter``
    Optional. Talks to a local Ollama server. Used when
    ``COPYFORGE_LLM_PROVIDER=ollama`` and the server answers.

``get_default_router``
    Reads the environment *first* and picks explicitly. It never
    constructs a client and waits for it to fail — the failure would
    then land on the first article rather than at startup.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMRouter(Protocol):
    """The minimal interface the writer needs from a language model."""

    name: str

    def complete(self, prompt: str, system: str = "", max_tokens: int = 512) -> str:
        """Return free text for a prompt."""
        ...


class LLMError(RuntimeError):
    """Raised when a router cannot fulfil a request."""


# --------------------------------------------------------------------------- #
# Stub router
# --------------------------------------------------------------------------- #


class StubRouter:
    """A deterministic stand-in for a real model.

    It reads ``Label: value`` pairs out of the prompt — the convention
    the rest of this repo's routers use — and assembles a block from the
    framework's slots. Because the framework slug and the article
    context are in the prompt, two different drafts produce two
    different blocks: the stub is deterministic, not constant.
    """

    name = "stub"

    def complete(self, prompt: str, system: str = "", max_tokens: int = 512) -> str:
        framework_slug = self._extract(prompt, "Framework")
        context = self._extract(prompt, "Article context")
        title = self._extract(prompt, "Article title")

        if not framework_slug:
            return ""

        framework = _framework_from_prompt(framework_slug)
        if framework is None:
            return ""

        topic = _topic_from(context, title)
        lines: list[str] = []

        for slot in framework.slots:
            lines.append(_slot_line(slot.role, topic, context))

        body = "\n\n".join(lines)

        # A block must not be a wall of text. Break the last slot into
        # its own paragraph if it is long.
        if len(body.split()) > 120:
            parts = body.split("\n\n")
            body = "\n\n".join(parts[:2] + [" ".join(parts[2:]).strip()]) if len(parts) > 2 else body

        return body

    @staticmethod
    def _extract(prompt: str, label: str, default: str = "") -> str:
        """Pull ``Label: value`` out of a prompt, case-insensitively."""
        pattern = rf"^{re.escape(label)}\s*:\s*(.+?)\s*$"
        match = re.search(pattern, prompt, re.IGNORECASE | re.MULTILINE)
        return match.group(1).strip() if match else default


def _slug_from(text: str) -> str:
    """The framework slug from a prompt line.

    The prompt says ``Framework: Problem–Agitate–Solve — Name the pain``.
    The slug is the framework's name with punctuation normalised.
    """
    head = text.split("—")[0].split(" - ")[0].strip()
    return re.sub(r"[^a-z0-9]+", "_", head.lower()).strip("_")


def _framework_from_prompt(text: str):
    """The framework a prompt is asking for, or None.

    Matching on the *name* rather than a parsed slug is deliberate:
    framework names contain en-dashes and hyphens ("Before–After–Bridge",
    "Objection Sandwich"), and a normaliser that mangles those would
    silently drop half the library. So the name is matched against the
    library's names first, and only then against the slugs.
    """
    from .frameworks import FRAMEWORKS

    head = text.split("—")[0].split(" - ")[0].strip()
    if not head:
        return None

    for framework in FRAMEWORKS:
        if framework.name.lower() == head.lower():
            return framework

    slug = _slug_from(head)
    for framework in FRAMEWORKS:
        if framework.slug == slug:
            return framework

    return None


def _is_filler(sentence: str) -> bool:
    """Whether a sentence is one of the phrases the scorer penalises."""
    from .frameworks import AI_PHRASES

    lowered = sentence.lower()
    return any(phrase in lowered for phrase in AI_PHRASES)


def _title_topic(context: str, title: str = "") -> str:
    """The article's subject, taken from its title.

    The first sentence of a draft is usually the author's framing of
    the *problem*, not the subject of the piece — "Data engineering has
    changed a lot over fifteen years" describes the topic's situation,
    not the topic. Slotting that phrase into every block produces
    structurally valid, semantically empty copy: a "Concrete Example"
    whose example is the article's own opening sentence.

    The title names the subject directly, so it is the better basis.
    """
    if title:
        return title.strip().rstrip(".")
    for line in context.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            if heading and not _is_filler(heading):
                return heading.rstrip(".")
    return ""


def _topic_from(context: str, title: str = "") -> str:
    """A topic phrase for the stub to write about.

    It prefers the article's title — the subject of the piece — and
    falls back to the first sentence of the author's prose, which is
    the author's own framing of what the piece is about and so a
    better basis for a stub block than anything the stub could invent.

    It also skips the phrases the scorer penalises, because the stub
    must not *introduce* the machine-filler it is supposed to be
    removing. Copying "In today's fast-paced world" into a new block
    would make the article worse.
    """
    if not context and not title:
        return "the problem"

    subject = _title_topic(context, title)
    if subject:
        return subject

    for line in context.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("["):
            continue
        first = stripped.split(". ")[0].strip().rstrip(".")
        if len(first) <= 12:
            continue
        if _is_filler(first):
            # The sentence is filler — skip to the next one rather
            # than laundering it into a new block.
            continue
        return first
    return "the problem"


def _subject(topic: str) -> str:
    """The topic as a noun phrase, for slots that need one.

    "Fifteen Years of Data Engineering: What Actually Scales" reads
    badly in the middle of a sentence ("a team running Fifteen Years of
    Data Engineering…"), so the trailing clause is dropped and a
    leading *scenery* quantifier is stripped off. What is left names
    the subject in the author's own words.

    Scenery versus substance is the whole question here, and the
    distinction is not "does it start with a number" — it is "is the
    number the point".

    * "Fifteen Years of Data Engineering" — the fifteen years **is**
      the claim. The article is about a span of time, and dropping
      "Fifteen Years" turns it into a generic piece about data
      engineering. Keep the number.
    * "A Guide to Data Engineering" / "10 Tips for Data Engineering" —
      the quantifier is framing; the subject is what follows. Drop it.

    A duration ("years", "months", "decades") is part of the subject.
    A count of things ("10 Tips", "Five Mistakes") is framing, because
    the tips are the subject, not the ten.
    """
    cleaned = topic.strip().rstrip(".")
    if ":" in cleaned:
        cleaned = cleaned.split(":", 1)[0].strip()

    # "What Actually Scales" / "How To Build One" — a question-shaped
    # title leads with a question word, not with the subject.
    words = cleaned.split()
    if words and words[0].lower().rstrip(",") in {
        "what", "how", "why", "when", "where", "which", "who",
    }:
        words = words[1:]
    cleaned = " ".join(words).strip()

    # A leading article is framing in every case: "A Guide to X" and
    # "The Complete Guide to X" are both about X.
    cleaned = re.sub(r"^(?:a|an|the)\s+", "", cleaned, flags=re.IGNORECASE).strip()

    # "Guide to X" / "Introduction to X" — the genre word is framing,
    # and the preposition after it belongs to the genre, not the
    # subject.
    cleaned = re.sub(
        r"^(?:complete\s+|complete\s+)?(?:guide|introduction|primer|overview|"
        r"walkthrough|tutorial|cheat\s*sheet|playbook|deep\s*dive|reference)\s+"
        r"(?:to|for|on|into|about)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()

    # "10 Tips for Data Engineering" / "Five Mistakes in X" — a count
    # of *items* frames the subject; the items are not the subject.
    item_count = re.match(
        r"^(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|twelve|"
        r"twenty|hundred)\s+"
        r"(?:tips?|tricks?|lessons?|mistakes?|ways?|reasons?|rules?|steps?|"
        r"questions?|examples?|patterns?|habits?|principles?)\b\s*"
        r"(?:to|for|in|of|about)?\s*",
        cleaned,
        re.IGNORECASE,
    )
    if item_count:
        cleaned = cleaned[item_count.end() :].strip()

    return cleaned or topic


def _slot_line(role: str, topic: str, context: str) -> str:
    """The stub's copy for one slot.

    Each role has its own shape, because the role is the point: a
    "problem" slot that reads like a "promise" slot is a broken block.

    The subject is threaded through the roles that name what the
    article is about, so a block about career history does not talk
    about checklists and pipelines.
    """
    subject = _subject(topic)

    if role == "problem":
        return (
            f"You already know the shape of this problem. {subject} is the "
            f"kind of thing that works fine right up until it does not, and "
            f"then it fails quietly."
        )
    if role == "agitate":
        return (
            "What it actually costs is harder to see than what it does. "
            "Every hour lost here is an hour nobody can account for, and "
            "the cost lands on someone else's quarter."
        )
    if role == "solution":
        return (
            "This guide is the checklist for catching it — the specific "
            "checks that separate a setup that holds up from one that "
            "happens to hold up today."
        )
    if role == "observation":
        return (
            f"Two teams approach {subject} the same way. One of them ships. "
            f"The other spends its best month explaining why the work was "
            f"not ready."
        )
    if role == "tension":
        return (
            "The difference between them is not effort, skill, or budget. "
            "It is one decision nobody wrote down."
        )
    if role == "consensus":
        return (
            f"The standard advice is that {subject} is a solved problem, "
            f"handled by whichever tool is most popular this quarter."
        )
    if role == "counter":
        return (
            "That advice is right most of the time, and wrong in a way "
            "that only shows up under load — which is the only condition "
            "that matters."
        )
    if role == "before":
        return (
            f"Today it is manual: a checklist, a spreadsheet, and a "
            f"quarterly cleanup that nobody looks forward to. {subject} is "
            f"handled the same way it was handled five years ago."
        )
    if role == "after":
        return (
            "The same work becomes a step in a pipeline that runs on "
            "every change and reports its own failures."
        )
    if role == "bridge":
        return (
            "The bridge is moving the check from a review stage into the "
            "step that produces the result."
        )
    if role == "attribution":
        return (
            "A team that had the same problem documented what changed for "
            "them, in their own words and numbers."
        )
    if role == "result":
        return (
            "The result was not a faster run — it was the first week in "
            "months where nobody had to ask whether the numbers were right."
        )
    if role == "objection":
        return (
            "The objection worth taking seriously: this is more machinery "
            "to maintain, and machinery is what you are trying to avoid."
        )
    if role == "answer":
        return (
            "That is fair, and it is the reason this does not work for "
            "every team. It works where the manual cost has already "
            "outgrown the manual."
        )
    if role == "reaffirm":
        return (
            "So the claim stands: the check is worth making, and it is "
            "worth making at the point the work happens rather than "
            "afterwards."
        )
    if role == "implication":
        return (
            f"So what does this mean for {subject}? It means the check has "
            f"to live where the work happens."
        )
    if role == "action":
        return (
            "Start with one thing: find the step where a mistake would be "
            "invisible, and put a check immediately after it. That single "
            "change surfaces most of what the rest of this guide covers."
        )
    if role == "item":
        return (
            "- The output looks right and nobody can say why\n"
            "- Two people check the same thing and disagree\n"
            "- The problem is found by the customer, not by the process"
        )
    if role == "scenario":
        return (
            f"A team working on {subject} hit the same wall: the numbers "
            f"were plausible and wrong at the same time, and the only way "
            f"to find out was to look."
        )
    if role == "ask":
        return (
            "Take one real example from your own setup and run it through "
            "the checks above. It takes ten minutes and the answer is "
            "either a fix or a clean bill of health."
        )
    if role == "friction":
        return (
            "Ten minutes of reading, and no change to anything until you "
            "decide there is one."
        )
    if role == "question":
        return (
            "So: in the last month, how many times did you find out "
            "something was wrong from someone other than your own process?"
        )
    return ""


# --------------------------------------------------------------------------- #
# Ollama router
# --------------------------------------------------------------------------- #


class OllamaRouter:
    """Optional local model backend via an Ollama server.

    Only used when explicitly requested via ``COPYFORGE_LLM_PROVIDER=ollama``.
    If the server is not reachable the caller falls back to the stub.
    """

    name = "ollama"

    def __init__(self, model: str = "qwen2.5:7b-instruct", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host.rstrip("/")
        self.tokens_used = 0

    def _post(self, path: str, payload: dict[str, Any], timeout: float = 120.0) -> dict:
        import httpx

        try:
            response = httpx.post(f"{self.host}{path}", json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            raise LLMError(f"Ollama request to {self.host}{path} failed: {exc}") from exc

    def complete(self, prompt: str, system: str = "", max_tokens: int = 512) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        data = self._post(
            "/api/chat",
            {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.7},
            },
        )
        content = data.get("message", {}).get("content", "")
        self.tokens_used += int(data.get("eval_count", 0) or 0)
        return content.strip()

    def json(self, prompt: str, schema_hint: str = "", max_tokens: int = 512) -> dict:
        system = (
            "Respond with a single JSON object and nothing else."
            + (f" The object should contain: {schema_hint}." if schema_hint else "")
        )
        raw = self.complete(prompt, system=system, max_tokens=max_tokens)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise LLMError(f"Ollama did not return a JSON object: {raw[:200]!r}")
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise LLMError(f"Ollama returned invalid JSON: {exc}") from exc


# --------------------------------------------------------------------------- #
# Selection
# --------------------------------------------------------------------------- #


def get_default_router() -> LLMRouter:
    """Pick the router from the environment.

    The environment is read *first* and the provider matched explicitly.
    We never try to construct a hosted client and wait for it to fail on
    the first request — the failure would land on the first article
    rather than at startup.
    """
    provider = os.environ.get("COPYFORGE_LLM_PROVIDER", "").strip().lower()

    if provider == "ollama":
        router = OllamaRouter(
            model=os.environ.get("COPYFORGE_OLLAMA_MODEL", "qwen2.5:7b-instruct"),
            host=os.environ.get("COPYFORGE_OLLAMA_HOST", "http://localhost:11434"),
        )
        try:
            router.complete("ping", max_tokens=1)
        except LLMError:
            return StubRouter()
        return router

    return StubRouter()
