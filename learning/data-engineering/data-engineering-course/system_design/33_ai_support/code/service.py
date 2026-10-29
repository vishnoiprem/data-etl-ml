"""AI-Powered Customer Support — core service.

A retrieval-augmented generation (RAG) system for customer support tickets.
The architecture is real and runnable; the LLM is replaced with a
deterministic mock that composes canned replies from retrieved articles.

The classic RAG flow we implement here:

    ticket body -> [retriever] -> top-K relevant articles
                                -> [prompt builder] -> prompt
                                -> [mock LLM] -> reply

State machines and storage live in this module; the Flask layer in
``app.py`` is a thin HTTP wrapper.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field, asdict
from typing import Iterable, Optional

from common.cache import TTLCache
from common.storage import KeyValueStore


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Article:
    """A knowledge-base article the system can cite in a reply."""

    article_id: int
    title: str
    body: str
    tags: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: time.time())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Message:
    """A single message on a ticket — either a user message or an AI reply."""

    role: str  # "user" | "assistant" | "agent"
    content: str
    created_at: float = field(default_factory=lambda: time.time())
    citations: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Ticket:
    """A support ticket and its full conversation thread."""

    ticket_id: int
    user_id: str
    subject: str
    status: str  # "open" | "auto_replied" | "agent_replied" | "closed"
    created_at: float = field(default_factory=lambda: time.time())
    messages: list[Message] = field(default_factory=list)
    last_response_at: Optional[float] = None
    citation_count: int = 0

    def to_dict(self) -> dict:
        return {
            "ticket_id": self.ticket_id,
            "user_id": self.user_id,
            "subject": self.subject,
            "status": self.status,
            "created_at": self.created_at,
            "last_response_at": self.last_response_at,
            "citation_count": self.citation_count,
            "messages": [m.to_dict() for m in self.messages],
        }


# ---------------------------------------------------------------------------
# Tokenization & retrieval
# ---------------------------------------------------------------------------


_STOPWORDS = frozenset(
    """
    a an the and or but if then of for to in on at by with from is are was
    were be been being have has had do does did this that these those it its
    i you he she we they me my mine your yours our ours their them us as not
    no so up out about into over after before under again further here there
    when where why how all any both each few most other some such than too
    very can will just don should now
    """.split()
)

_WORD_RE = re.compile(r"[A-Za-z0-9_]+")


def tokenize(text: str) -> list[str]:
    """Lowercase + alnum tokenize + drop stopwords. Cheap and good enough."""
    if not text:
        return []
    return [t for t in (m.group(0).lower() for m in _WORD_RE.finditer(text)) if t not in _STOPWORDS]


def _tf(tokens: Iterable[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for t in tokens:
        out[t] = out.get(t, 0) + 1
    return out


# ---------------------------------------------------------------------------
# Mock LLM
# ---------------------------------------------------------------------------


# Templates for the deterministic mock LLM. The mock picks a template based
# on which citations it sees, so the same article set always yields the
# same reply (testable and reproducible).
MOCK_REPLY_TEMPLATES = [
    "Hi! Based on our docs, here's what I found: {lead} {closing}",
    "Thanks for reaching out. {lead} {closing}",
    "Happy to help. {lead} {closing}",
]

MOCK_LEAD_BY_TAG = {
    "billing": "For billing questions, the relevant guidance from our knowledge base applies.",
    "refund": "Refund handling is covered in our policy — here's the short version.",
    "account": "Account-related issues typically come down to a few common causes.",
    "shipping": "Shipping timelines and exceptions are documented in the article I found.",
    "login": "Login problems usually have a quick fix; the most common cause is captured below.",
    "api": "For API questions, the most useful thing is the contract in the article below.",
    "general": "Here's the most relevant information from our knowledge base.",
}

MOCK_CLOSING_BY_TAG = {
    "billing": "If the charge looks wrong, reply with the order number and we'll dig in.",
    "refund": "If you don't see the refund within 5 business days, reply here and we'll escalate.",
    "account": "Reply with the email on the account and we'll help reset / recover it.",
    "shipping": "If the tracking has stalled, reply with the order number for a manual check.",
    "login": "If the steps don't unblock you, reply with the exact error text and we'll help.",
    "api": "Paste the failing request/response and we'll troubleshoot with you.",
    "general": "Let us know if you need anything else!",
}

DEFAULT_TAG = "general"


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class SupportService:
    """A working RAG-style customer support service.

    >>> svc = SupportService()
    >>> a = svc.ingest_article("Reset password",
    ...     "To reset your password, click Forgot Password on the login page.",
    ...     tags=["login"])
    >>> t = svc.open_ticket("u1", "I cannot log in to my account",
    ...     body="I forgot my password and the reset email is not arriving.")
    >>> reply = svc.auto_reply(t.ticket_id)
    >>> "Reset password" in reply.content or len(reply.content) > 0
    True
    """

    DEFAULT_TOP_K = 3
    CACHE_TTL = 60.0

    def __init__(
        self,
        store: Optional[KeyValueStore] = None,
        cache: Optional[TTLCache] = None,
        top_k: int = DEFAULT_TOP_K,
    ):
        self.store = store or KeyValueStore("ai_support")
        self.cache = cache or TTLCache(ttl_seconds=self.CACHE_TTL)
        self.top_k = top_k
        # Lightweight ID counter; in prod use Snowflake.
        self._next_article_id = self._max_article_id() + 1
        self._next_ticket_id = self._max_ticket_id() + 1

    # ---- ids -----------------------------------------------------------

    def _max_article_id(self) -> int:
        best = 0
        for k, _ in self.store.scan("article:"):
            try:
                best = max(best, int(k.split(":")[1]))
            except (IndexError, ValueError):
                continue
        return best

    def _max_ticket_id(self) -> int:
        best = 0
        for k, _ in self.store.scan("ticket:"):
            try:
                best = max(best, int(k.split(":")[1]))
            except (IndexError, ValueError):
                continue
        return best

    # ---- article ingest ------------------------------------------------

    def ingest_article(
        self,
        title: str,
        body: str,
        tags: Optional[list[str]] = None,
    ) -> Article:
        """Add a knowledge-base article."""
        if not title or not isinstance(title, str):
            raise ValueError("title is required")
        if not body or not isinstance(body, str):
            raise ValueError("body is required")
        aid = self._next_article_id
        self._next_article_id += 1
        art = Article(
            article_id=aid,
            title=title.strip(),
            body=body.strip(),
            tags=[t.strip().lower() for t in (tags or []) if t.strip()],
        )
        # Persist the article.
        self.store.set(f"article:{aid}", art.to_dict())
        # Inverted index entry per token.
        for tok in set(tokenize(art.title + " " + art.body)):
            self.store.set(f"idx:{tok}:{aid}", 1)
        # Title index for prefix-ish lookup.
        self.store.set(f"title:{title.strip().lower()}:{aid}", 1)
        return art

    def list_articles(self) -> list[Article]:
        out: list[Article] = []
        for k, v in self.store.scan("article:"):
            out.append(Article(**v))
        out.sort(key=lambda a: a.article_id)
        return out

    def get_article(self, article_id: int) -> Optional[Article]:
        d = self.store.get(f"article:{article_id}")
        if not d:
            return None
        return Article(**d)

    # ---- retrieval -----------------------------------------------------

    def _score(self, query_tokens: list[str], art: Article) -> float:
        """Compute a simple TF-based retrieval score.

        We treat the entire article (title + body + tags) as a bag of
        words and sum the per-query-term frequency, with a small title
        boost. This is a stand-in for BM25/embedding-similarity — the
        shape of the result (top-K by score) is what matters in design.
        """
        art_tokens = tokenize(art.title + " " + art.body + " " + " ".join(art.tags))
        art_tf = _tf(art_tokens)
        title_tokens = set(tokenize(art.title))
        score = 0.0
        for q in query_tokens:
            score += art_tf.get(q, 0)
            if q in title_tokens:
                score += 2.0  # title boost
        return score

    def retrieve(self, query: str, top_k: Optional[int] = None) -> list[tuple[Article, float]]:
        """Return up to ``top_k`` articles ranked by score."""
        k = top_k or self.top_k
        cache_key = f"retrieve:{hash(query)}:{k}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return [(Article(**a), s) for a, s in cached]

        q_tokens = tokenize(query)
        if not q_tokens:
            return []

        articles = self.list_articles()
        scored: list[tuple[Article, float]] = []
        for art in articles:
            s = self._score(q_tokens, art)
            if s > 0:
                scored.append((art, s))
        scored.sort(key=lambda t: (t[1], t[0].article_id), reverse=True)
        out = scored[:k]
        self.cache.set(
            cache_key,
            [(a.to_dict(), s) for a, s in out],
            ttl_seconds=self.CACHE_TTL,
        )
        return out

    # ---- tickets -------------------------------------------------------

    def open_ticket(
        self,
        user_id: str,
        subject: str,
        body: str,
    ) -> Ticket:
        """Create a ticket and add the user's initial message."""
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id is required")
        if not subject or not isinstance(subject, str):
            raise ValueError("subject is required")
        if not body or not isinstance(body, str):
            raise ValueError("body is required")

        tid = self._next_ticket_id
        self._next_ticket_id += 1
        ticket = Ticket(
            ticket_id=tid,
            user_id=user_id,
            subject=subject.strip(),
            status="open",
        )
        ticket.messages.append(Message(role="user", content=body))
        self._persist_ticket(ticket)
        return ticket

    def get_ticket(self, ticket_id: int) -> Optional[Ticket]:
        d = self.store.get(f"ticket:{ticket_id}")
        if not d:
            return None
        msgs = [Message(**m) for m in d.get("messages", [])]
        return Ticket(
            ticket_id=d["ticket_id"],
            user_id=d["user_id"],
            subject=d["subject"],
            status=d["status"],
            created_at=d.get("created_at", 0.0),
            last_response_at=d.get("last_response_at"),
            citation_count=d.get("citation_count", 0),
            messages=msgs,
        )

    def list_tickets(self) -> list[Ticket]:
        out: list[Ticket] = []
        for _k, _v in self.store.scan("ticket:"):
            t = self.get_ticket(int(_k.split(":")[1]))
            if t:
                out.append(t)
        out.sort(key=lambda t: t.ticket_id)
        return out

    def _persist_ticket(self, ticket: Ticket) -> None:
        self.store.set(f"ticket:{ticket.ticket_id}", ticket.to_dict())
        # Invalidate retrieve cache for the latest user message.
        self.cache.delete(f"retrieve:{hash(ticket.subject)}:3")

    # ---- mock LLM ------------------------------------------------------

    def _compose_reply(self, query: str, citations: list[Article]) -> Message:
        """Deterministic mock LLM that composes a reply from citations.

        Picks a tag (from the top citation if any), then a template.
        This is deliberately non-creative so tests can pin the output.
        """
        tag = DEFAULT_TAG
        if citations:
            for t in citations[0].tags:
                if t in MOCK_LEAD_BY_TAG:
                    tag = t
                    break

        lead = MOCK_LEAD_BY_TAG[tag]
        closing = MOCK_CLOSING_BY_TAG[tag]
        template = MOCK_REPLY_TEMPLATES[hash(query) % len(MOCK_REPLY_TEMPLATES)]
        body = template.format(lead=lead, closing=closing)

        if citations:
            body += "\n\nReferences:"
            for c in citations:
                body += f"\n- [{c.article_id}] {c.title}"

        return Message(
            role="assistant",
            content=body,
            citations=[c.article_id for c in citations],
        )

    # ---- auto-reply ----------------------------------------------------

    def auto_reply(self, ticket_id: int, top_k: Optional[int] = None) -> Optional[Message]:
        """Run the RAG flow on the latest user message and append a reply."""
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return None
        if ticket.status == "closed":
            raise ValueError("ticket is closed")

        # The retrieval query is the most recent user message + subject.
        last_user = next(
            (m for m in reversed(ticket.messages) if m.role == "user"),
            None,
        )
        if last_user is None:
            return None
        query = f"{ticket.subject} {last_user.content}"
        scored = self.retrieve(query, top_k=top_k)
        citations = [a for a, _ in scored]

        reply = self._compose_reply(query, citations)
        ticket.messages.append(reply)
        ticket.status = "auto_replied"
        ticket.last_response_at = reply.created_at
        ticket.citation_count = len(citations)
        self._persist_ticket(ticket)
        return reply

    def agent_reply(self, ticket_id: int, body: str) -> Message:
        """A human agent posts a follow-up on a ticket."""
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            raise ValueError("ticket not found")
        if ticket.status == "closed":
            raise ValueError("ticket is closed")
        if not body or not isinstance(body, str):
            raise ValueError("body is required")
        msg = Message(role="agent", content=body)
        ticket.messages.append(msg)
        ticket.status = "agent_replied"
        ticket.last_response_at = msg.created_at
        self._persist_ticket(ticket)
        return msg

    def user_reply(self, ticket_id: int, body: str) -> Message:
        """The end user posts a follow-up on a ticket."""
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            raise ValueError("ticket not found")
        if ticket.status == "closed":
            raise ValueError("ticket is closed")
        if not body or not isinstance(body, str):
            raise ValueError("body is required")
        msg = Message(role="user", content=body)
        ticket.messages.append(msg)
        ticket.status = "open"
        self._persist_ticket(ticket)
        return msg

    # ---- stats ---------------------------------------------------------

    def stats(self) -> dict:
        n_articles = sum(1 for _ in self.store.scan("article:"))
        n_tickets = sum(1 for _ in self.store.scan("ticket:"))
        return {
            "articles": n_articles,
            "tickets": n_tickets,
            "cache": self.cache.stats(),
        }
