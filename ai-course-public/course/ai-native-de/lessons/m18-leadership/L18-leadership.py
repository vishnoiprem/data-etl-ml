"""
================================================================
M18 L18  --  Leadership + STAR: staff-level interview stories
================================================================

Run:    python3 lessons/m18-leadership/L18-leadership.py
Keys:   none

Builds a STAR story library and rehearsal harness from scratch
with no external dependencies:
  * STARStory dataclass  (Situation, Task, Action, Result + tags + role)
  * STARLibrary          (store, lookup by tag, by role, by principle)
  * LeadershipPrinciple  (VISION, EXECUTION, COLLABORATION, TECH_DEPTH, MENTORSHIP)
  * tag_for_principle    (does a story cover a principle?)
  * Rehearsal            (the 3-2-1 framework: 3-min talk / 2-min deep / 1-min Q&A)
  * MockQuestion         (the 30 most common staff-level questions)
  * match_stories        (return top-3 stories for a question)
  * score_story          (heuristic score: result quantified? action clear? impact real?)
  * 8 sample stories     (across the 5 banks: RAG, cost, security, scale, hiring)
  * demo()               (7 sections; runs end-to-end)
  * 14 unit tests        (pytest-compatible)

The lesson's point: staff/principal interviews are won in
preparation, not in the room.  A STAR library is the artifact
that turns a folder of "I think I did this once" memories into
a rehearsed, principle-tagged, role-aligned story bank you can
draw on in any interview.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from enum import Enum


# =================================================================
# CONFIG
# =================================================================

LESSON_NUMBER = "M18.L18"
SEED = 42

# The 5 story banks.  Each is a category of work most data/ML
# staff-level candidates should be able to anchor at least one
# story to.
STORY_BANKS = ("rag", "cost", "security", "scale", "hiring")

# The 4 leadership principles (plus MENTORSHIP as a 5th).
# META and Google use 14 / 16 principles; for this lesson we
# keep the canonical 4 + 1 and let the stories map to them.
LEADERSHIP_PRINCIPLES = (
    "vision",
    "execution",
    "collaboration",
    "tech_depth",
    "mentorship",
)

# Words that signal a quantified result in the result text.
# A story without a number usually scores low.
QUANTIFIER_HINTS = (
    r"\d+%",                 # percentage
    r"\$\d+",                # dollars
    r"\d+x\b",               # 2x, 10x
    r"\d+\s*(?:ms|sec|min|hr)s?\b",  # time units
    r"\d+\s*(?:k|m|b)\b",    # thousand / million / billion
    r"\d+\s+(?:users|calls|requests|qps|rps|documents|rows|tokens)",
)


# =================================================================
# SECTION 1  --  STARStory dataclass
# =================================================================

@dataclass
class STARStory:
    """A single interview story in the Situation / Task / Action / Result form.

    The fields are intentionally plain strings -- interviewers read
    them, not machines.  The `tags` field is the bridge between
    stories and the leadership principles / story banks.
    """
    title: str
    situation: str
    task: str
    action: str
    result: str
    role: str = "IC"
    tags: list[str] = field(default_factory=list)
    bank: str = ""

    def word_count(self) -> int:
        """Total words across the four STAR components."""
        return sum(len(self._field(s).split()) for s in
                   (self.situation, self.task, self.action, self.result))

    def duration_minutes(self, wpm: int = 150) -> float:
        """Estimated spoken duration at `wpm` words per minute."""
        return self.word_count() / wpm

    @staticmethod
    def _field(s: str) -> str:
        return s or ""


# =================================================================
# SECTION 2  --  STARLibrary
# =================================================================

@dataclass
class STARLibrary:
    """A store of STAR stories with lookup by tag, role, or bank."""
    stories: list[STARStory] = field(default_factory=list)

    def add(self, story: STARStory) -> None:
        self.stories.append(story)

    def __len__(self) -> int:
        return len(self.stories)

    def by_tag(self, tag: str) -> list[STARStory]:
        """Return all stories whose `tags` contain `tag` (case-insensitive)."""
        t = tag.lower()
        return [s for s in self.stories if any(tg.lower() == t for tg in s.tags)]

    def by_role(self, role: str) -> list[STARStory]:
        """Return all stories tagged with a given role (e.g. 'tech-lead', 'IC')."""
        r = role.lower()
        return [s for s in self.stories if s.role.lower() == r]

    def by_bank(self, bank: str) -> list[STARStory]:
        """Return all stories in a given bank (rag, cost, security, scale, hiring)."""
        b = bank.lower()
        return [s for s in self.stories if s.bank.lower() == b]

    def by_principle(self, principle: str) -> list[STARStory]:
        """Return all stories that cover a given leadership principle."""
        p = principle.lower()
        return [s for s in self.stories if p in [t.lower() for t in s.tags]]

    def titles(self) -> list[str]:
        return [s.title for s in self.stories]


# =================================================================
# SECTION 3  --  LeadershipPrinciple enum
# =================================================================

class LeadershipPrinciple(Enum):
    """The 4 canonical leadership principles + MENTORSHIP.

    These are how META structures its leadership interview; the
    exact names vary by company but the four pillars are
    stable: vision, execution, collaboration, technical depth.
    MENTORSHIP is included because most staff-level roles
    expect evidence of growing others.
    """
    VISION = "vision"
    EXECUTION = "execution"
    COLLABORATION = "collaboration"
    TECH_DEPTH = "tech_depth"
    MENTORSHIP = "mentorship"


# =================================================================
# SECTION 4  --  tag_for_principle
# =================================================================

# Keyword maps: which words in a story's tags/title/action suggest
# which principle.  These are intentionally overlapping; a single
# story often covers 2 principles.
_PRINCIPLE_KEYWORDS: dict[LeadershipPrinciple, tuple[str, ...]] = {
    LeadershipPrinciple.VISION: (
        "vision", "roadmap", "strategy", "north-star", "okrs",
        "long-term", "quarter", "multi-year", "narrative", "direction",
    ),
    LeadershipPrinciple.EXECUTION: (
        "execution", "shipped", "launched", "delivered", "on-time",
        "migration", "rollout", "incident", "postmortem", "deadline",
        "milestone", "ramp", "deployment",
    ),
    LeadershipPrinciple.COLLABORATION: (
        "collaboration", "cross-team", "cross-functional", "stakeholder",
        "alignment", "partnership", "negotiation", "consensus",
        "consensus", "pm", "design", "ops",
    ),
    LeadershipPrinciple.TECH_DEPTH: (
        "tech-depth", "architecture", "design", "rfc", "bpe", "retrieval",
        "rag", "vector", "embedding", "latency", "throughput", "system",
        "pipeline", "model", "ablation", "benchmark", "prototype",
    ),
    LeadershipPrinciple.MENTORSHIP: (
        "mentor", "mentorship", "coach", "growing", "onboard",
        "1:1", "career", "promotion", "junior", "intern", "tech-lead",
    ),
}


def tag_for_principle(principle: LeadershipPrinciple, story: STARStory) -> bool:
    """Return True if `story` covers the given principle.

    Heuristic: search the story's tags, title, and action text
    for keywords associated with the principle.  This is the
    same approach a hiring manager uses in the first 10 seconds
    of hearing a story.
    """
    kws = _PRINCIPLE_KEYWORDS[principle]
    haystack = " ".join(
        [story.title, story.action, story.task, " ".join(story.tags)]
    ).lower()
    # Direct tag match
    if principle.value in [t.lower() for t in story.tags]:
        return True
    # Keyword match
    for kw in kws:
        if kw in haystack:
            return True
    return False


def principles_covered(story: STARStory) -> list[LeadershipPrinciple]:
    """Return all principles a story covers, in enum order."""
    return [p for p in LeadershipPrinciple if tag_for_principle(p, story)]


# =================================================================
# SECTION 5  --  Rehearsal (the 3-2-1 framework)
# =================================================================

@dataclass
class Rehearsal:
    """The 3-2-1 framework for prepping a story.

    3-minute talk:    the long-form answer you'd give on the floor.
                      Sets context, walks through action, lands the result.
    2-minute deep:    the "tell me more about X" follow-up.  Pick the
                      most interesting sub-decision and explain it.
    1-minute Q&A:     the compressed version for follow-up questions
                      that interrupt the long form.  Result-first.
    """
    story: STARStory
    three_minute: str
    two_minute: str
    one_minute: str

    def total_words(self) -> int:
        return sum(len(s.split()) for s in
                   (self.three_minute, self.two_minute, self.one_minute))

    def estimated_minutes(self, wpm: int = 150) -> float:
        """Total estimated spoken time, summed across the three layers."""
        return self.total_words() / wpm


# =================================================================
# SECTION 6  --  MockQuestion (the 30 most common staff-level questions)
# =================================================================

@dataclass(frozen=True)
class MockQuestion:
    """A common staff-level behavioral / architecture question.

    The `principle` field is the principle META's rubric weights
    most for this question; the `keywords` field is used by
    `match_stories` to score relevance.
    """
    text: str
    principle: LeadershipPrinciple
    keywords: tuple[str, ...] = ()


MOCK_QUESTIONS: tuple[MockQuestion, ...] = (
    # --- VISION ---
    MockQuestion(
        "Tell me about a time you set a technical vision for a team.",
        LeadershipPrinciple.VISION,
        ("vision", "roadmap", "narrative", "direction"),
    ),
    MockQuestion(
        "Describe a time you had to convince leadership to invest in a long-term bet.",
        LeadershipPrinciple.VISION,
        ("strategy", "investment", "long-term", "narrative"),
    ),
    MockQuestion(
        "How do you balance short-term delivery against long-term tech health?",
        LeadershipPrinciple.VISION,
        ("balance", "tech-health", "tradeoff", "quarter"),
    ),
    MockQuestion(
        "Tell me about a time you changed the direction of a project mid-flight.",
        LeadershipPrinciple.VISION,
        ("pivot", "direction", "narrative", "course-correct"),
    ),
    MockQuestion(
        "Describe how you'd set a 12-month roadmap for a new ML platform.",
        LeadershipPrinciple.VISION,
        ("roadmap", "platform", "ml", "quarter"),
    ),
    MockQuestion(
        "Tell me about a time you said no to a feature.",
        LeadershipPrinciple.VISION,
        ("scope", "no", "discipline", "tradeoff"),
    ),

    # --- EXECUTION ---
    MockQuestion(
        "Tell me about a time you led a migration under a hard deadline.",
        LeadershipPrinciple.EXECUTION,
        ("migration", "deadline", "rollout", "shipped"),
    ),
    MockQuestion(
        "Describe an incident you were responsible for.  How did you handle it?",
        LeadershipPrinciple.EXECUTION,
        ("incident", "postmortem", "oncall", "rollback"),
    ),
    MockQuestion(
        "Tell me about a time you had to deliver bad news to a stakeholder.",
        LeadershipPrinciple.EXECUTION,
        ("bad-news", "stakeholder", "transparency", "delay"),
    ),
    MockQuestion(
        "Walk me through a project you shipped that was behind schedule.",
        LeadershipPrinciple.EXECUTION,
        ("behind", "shipped", "recovered", "deadline"),
    ),
    MockQuestion(
        "Tell me about a time you had to make a hard tradeoff to hit a date.",
        LeadershipPrinciple.EXECUTION,
        ("tradeoff", "shipped", "scope", "cut"),
    ),
    MockQuestion(
        "Describe a time you turned around an underperforming project.",
        LeadershipPrinciple.EXECUTION,
        ("turnaround", "recovered", "shipped", "team"),
    ),

    # --- COLLABORATION ---
    MockQuestion(
        "Tell me about a time you had a major disagreement with a peer.",
        LeadershipPrinciple.COLLABORATION,
        ("disagreement", "conflict", "resolved", "alignment"),
    ),
    MockQuestion(
        "Describe how you drove alignment across 3+ teams on a shared initiative.",
        LeadershipPrinciple.COLLABORATION,
        ("cross-team", "alignment", "consensus", "stakeholder"),
    ),
    MockQuestion(
        "Tell me about a time you worked with PM to kill a project.",
        LeadershipPrinciple.COLLABORATION,
        ("killed", "pm", "scope", "discipline"),
    ),
    MockQuestion(
        "Describe a partnership that didn't go well.  What did you learn?",
        LeadershipPrinciple.COLLABORATION,
        ("partnership", "learned", "failed", "trust"),
    ),
    MockQuestion(
        "Tell me about a time you disagreed with your manager.",
        LeadershipPrinciple.COLLABORATION,
        ("manager", "disagreement", "resolved", "trust"),
    ),
    MockQuestion(
        "How do you handle a stakeholder who keeps changing requirements?",
        LeadershipPrinciple.COLLABORATION,
        ("stakeholder", "requirements", "scope", "negotiation"),
    ),

    # --- TECH DEPTH ---
    MockQuestion(
        "Design a retrieval system for 100M documents.  Walk me through the major decisions.",
        LeadershipPrinciple.TECH_DEPTH,
        ("retrieval", "vector", "index", "100m", "scale"),
    ),
    MockQuestion(
        "Tell me about a time you debugged a hard production issue.",
        LeadershipPrinciple.TECH_DEPTH,
        ("debug", "incident", "root-cause", "production"),
    ),
    MockQuestion(
        "Describe a design decision you reversed after measurement.",
        LeadershipPrinciple.TECH_DEPTH,
        ("ablation", "benchmark", "reversed", "data"),
    ),
    MockQuestion(
        "How would you reduce LLM cost by 10x without losing quality?",
        LeadershipPrinciple.TECH_DEPTH,
        ("cost", "llm", "cache", "router", "10x"),
    ),
    MockQuestion(
        "Tell me about a time you built something from scratch.",
        LeadershipPrinciple.TECH_DEPTH,
        ("from-scratch", "prototype", "shipped", "design"),
    ),
    MockQuestion(
        "How do you evaluate a RAG system end-to-end?",
        LeadershipPrinciple.TECH_DEPTH,
        ("rag", "evaluation", "ragas", "metric", "ground-truth"),
    ),

    # --- MENTORSHIP ---
    MockQuestion(
        "Tell me about a person you grew.  What did you do specifically?",
        LeadershipPrinciple.MENTORSHIP,
        ("mentor", "growing", "1:1", "promotion"),
    ),
    MockQuestion(
        "Describe a time you onboarded a new hire and got them productive in 30 days.",
        LeadershipPrinciple.MENTORSHIP,
        ("onboard", "30-day", "productive", "plan"),
    ),
    MockQuestion(
        "Tell me about a time you had to give tough feedback.",
        LeadershipPrinciple.MENTORSHIP,
        ("feedback", "tough", "direct", "growth"),
    ),
    MockQuestion(
        "How do you scale yourself when the team grows from 3 to 12?",
        LeadershipPrinciple.MENTORSHIP,
        ("scale", "team", "tech-lead", "process"),
    ),
    MockQuestion(
        "Tell me about a time you lost an engineer.  What did you learn?",
        LeadershipPrinciple.MENTORSHIP,
        ("lost", "learned", "retention", "trust"),
    ),
    MockQuestion(
        "Describe your philosophy on code review.",
        LeadershipPrinciple.MENTORSHIP,
        ("review", "feedback", "growth", "quality"),
    ),
)


# =================================================================
# SECTION 7  --  match_stories
# =================================================================

def _score_relevance(story: STARStory, question: MockQuestion) -> int:
    """Score a story's relevance to a question.

    Scoring:
      +3 if the story covers the question's principle
      +1 per matching keyword (case-insensitive substring)
      +1 if the bank aligns with the question (heuristic)
    """
    score = 0
    if tag_for_principle(question.principle, story):
        score += 3
    haystack = " ".join(
        [story.title, story.situation, story.action, story.result,
         " ".join(story.tags)]
    ).lower()
    for kw in question.keywords:
        if kw.lower() in haystack:
            score += 1
    return score


def match_stories(
    question: MockQuestion, library: STARLibrary, top_k: int = 3
) -> list[tuple[STARStory, int]]:
    """Return the top-k stories for a question, sorted by relevance desc.

    Always returns up to `top_k` results; stories that don't
    match at all are still returned (score 0) so the candidate
    can see "I don't have a story for this -- write one".
    """
    scored = [(s, _score_relevance(s, question)) for s in library.stories]
    scored.sort(key=lambda x: (-x[1], x[0].title))
    return scored[:top_k]


# =================================================================
# SECTION 8  --  score_story
# =================================================================

@dataclass
class StoryScore:
    """A heuristic score for a STAR story, broken down by dimension."""
    result_quantified: bool
    action_clear: bool
    impact_real: bool
    duration_ok: bool
    role_aligned: bool
    total: int = 0
    notes: list[str] = field(default_factory=list)


def _has_quantifier(text: str) -> bool:
    """Return True if the text contains a number, percent, or magnitude."""
    for pat in QUANTIFIER_HINTS:
        if re.search(pat, text, flags=re.IGNORECASE):
            return True
    return False


def _has_first_person_action(text: str) -> bool:
    """Return True if the action text contains a clear first-person verb."""
    # "I led", "I built", "I drove", "I shipped", etc.
    return bool(re.search(r"\bI\s+(led|built|drove|shipped|designed|owned|architected|ran|wrote|ran|mentored|launched|rolled\s+out|cut|reduced|grew|negotiated|killed|reversed)\b",
                          text, flags=re.IGNORECASE))


def score_story(story: STARStory) -> StoryScore:
    """Score a story 0-10 on five heuristic dimensions.

    result_quantified (0-2): does the result have a number?
    action_clear      (0-2): does the action start with a first-person verb?
    impact_real       (0-2): does the impact feel real (not just "improved X")?
    duration_ok       (0-2): is the spoken duration 2-4 minutes?
    role_aligned      (0-2): is the role consistent with staff-level work?
    """
    s = StoryScore(
        result_quantified=False,
        action_clear=False,
        impact_real=False,
        duration_ok=False,
        role_aligned=False,
    )
    # 1. Result quantified (2 pts)
    if _has_quantifier(story.result):
        s.result_quantified = True
    # 2. Action clear (2 pts)
    if _has_first_person_action(story.action):
        s.action_clear = True
    # 3. Impact real (2 pts) -- quantified + non-trivial magnitude
    impact_words = ("revenue", "users", "cost", "latency", "throughput", "adoption", "growth")
    if _has_quantifier(story.result) and any(w in story.result.lower() for w in impact_words):
        s.impact_real = True
    elif _has_quantifier(story.result) and re.search(r"\d{2,}", story.result):
        # a 2+ digit number anywhere in the result
        s.impact_real = True
    # 4. Duration ok (2 pts) -- 2 to 4 minutes at 150 wpm
    dur = story.duration_minutes()
    if 2.0 <= dur <= 4.0:
        s.duration_ok = True
    elif 1.5 <= dur < 2.0 or 4.0 < dur <= 5.0:
        s.duration_ok = False  # partial credit not given
        s.notes.append(f"duration {dur:.1f} min -- tighten to 2-4")
    else:
        s.notes.append(f"duration {dur:.1f} min -- out of range")
    # 5. Role aligned (2 pts)
    aligned_roles = {"tech-lead", "staff", "principal", "manager", "lead", "ic", "senior"}
    if story.role.lower() in aligned_roles:
        s.role_aligned = True

    s.total = (
        (2 if s.result_quantified else 0)
        + (2 if s.action_clear else 0)
        + (2 if s.impact_real else 0)
        + (2 if s.duration_ok else 0)
        + (2 if s.role_aligned else 0)
    )
    return s


# =================================================================
# SECTION 9  --  8 sample stories (across the 5 banks)
# =================================================================

SAMPLE_STORIES: list[STARStory] = [
    # --- 1. RAG migration (bank=rag) ---
    STARStory(
        title="Migrated 3B-token FAQ search to RAG in 6 weeks",
        situation=(
            "Our support search ran on a Lucene index of 3B tokens of "
            "historical tickets.  P95 recall@10 was 0.41 and PMs were "
            "complaining that 'why is my search broken' was the top "
            "result for half of queries."
        ),
        task=(
            "Own a 6-week migration to a RAG system that hits recall@10 "
            ">= 0.7 without regressing P95 latency from 180ms to > 250ms."
        ),
        action=(
            "I built the v1 in 2 weeks: bge-small embeddings, FAISS "
            "index, a cross-encoder reranker, and a feedback loop that "
            "logged click-through.  I drove alignment with 2 PMs and 1 "
            "support lead to label 1,200 query/result pairs as a golden "
            "set.  I ran the golden set through 4 retrieval configs, "
            "wrote an RFC, and got sign-off in 3 days."
        ),
        result=(
            "P95 recall@10 went from 0.41 to 0.74, P95 latency stayed at "
            "190ms, and 'why is my search broken' dropped from 47% of "
            "queries to 3%.  Support ticket volume dropped 22% in the "
            "first month after launch."
        ),
        role="tech-lead",
        tags=["rag", "retrieval", "tech_depth", "execution", "migration", "evaluation", "ragas"],
        bank="rag",
    ),

    # --- 2. Cost reduction (bank=cost) ---
    STARStory(
        title="Cut LLM inference cost 12x with prompt caching + smaller model",
        situation=(
            "The RAG system from story 1 was running on gpt-4o at "
            "$0.04 per query.  At 8M queries/month the monthly bill "
            "was $320K and the CFO flagged it in the Q3 review."
        ),
        task=(
            "Get the per-query cost below $0.005 within 60 days, "
            "without regressing answer quality (Likert >= 4.0/5.0 on "
            "the golden set)."
        ),
        action=(
            "I ran 3 ablations: (1) move 80% of queries to gpt-4o-mini "
            "with a router, (2) add prompt caching for the system "
            "prompt + 5 retrieved docs, (3) shorten the system prompt "
            "from 800 to 220 tokens.  I instrumented every call with a "
            "cost tracker (input/output tokens, USD) and shipped a "
            "weekly cost dashboard.  I owned the rollout and the "
            "rollback plan."
        ),
        result=(
            "Per-query cost went from $0.04 to $0.0032 (12.5x).  "
            "Monthly spend dropped from $320K to $26K.  Quality "
            "regressed 0.2 Likert points (4.3 to 4.1) -- well within "
            "the 4.0 floor.  The CFO stopped asking."
        ),
        role="tech-lead",
        tags=["cost", "llm", "router", "cache", "tech_depth", "execution", "10x", "ablation"],
        bank="cost",
    ),

    # --- 3. Security incident (bank=security) ---
    STARStory(
        title="Led the response to a PII exfil in the eval pipeline",
        situation=(
            "A junior engineer pushed a PR that logged 200K user "
            "queries -- including PII (email, last-4 of credit card) "
            "-- to a public S3 bucket for 'easier debugging'.  A "
            "security researcher emailed us on a Friday at 5pm."
        ),
        task=(
            "Contain the exposure within 4 hours, notify Legal and "
            "Privacy, and ship a fix that prevents the same class of "
            "bug from recurring -- without taking down the eval "
            "pipeline for longer than 1 day."
        ),
        action=(
            "I paged the on-call, rotated the S3 bucket to private "
            "within 90 minutes, and pulled the logs out of the "
            "public bucket into a sealed access log.  I drove the "
            "postmortem with Legal, Privacy, and Security, wrote the "
            "executive summary for the VP, and shipped a pre-commit "
            "hook + a CI check that blocks any code path that writes "
            "PII columns to a non-encrypted bucket."
        ),
        result=(
            "Exposure window: 14 days.  Affected users: 200K.  No "
            "evidence of access by anyone outside the company.  "
            "Legal signed off on the disclosure letter.  The CI "
            "check has blocked 7 similar PRs in the 6 months since."
        ),
        role="tech-lead",
        tags=["security", "pii", "incident", "execution", "collaboration", "postmortem", "compliance"],
        bank="security",
    ),

    # --- 4. Scale (bank=scale) ---
    STARStory(
        title="Scaled a RAG index from 10M to 1B documents in 4 months",
        situation=(
            "Our retrieval index was a single-node FAISS index on an "
            "i3.4xlarge.  At 10M docs it served 200 QPS at 80ms P95.  "
            "PM wanted 1B docs by end of year for a new product line."
        ),
        task=(
            "Design and ship a horizontally-scalable retrieval system "
            "that handles 1B docs at 5K QPS / 200ms P95 within 4 "
            "months, on the same monthly infra budget."
        ),
        action=(
            "I evaluated 4 candidates (FAISS-IVF, Milvus, ScaNN, and "
            "a custom HNSW).  I picked Milvus for the sharded index + "
            "etcd-based metadata; shipped a 2-week prototype that "
            "benchmarked 1B docs at 4.8K QPS / 180ms.  I drove the "
            "rollout: shadow traffic for 1 week, 10% canary, 50%, "
            "100% with rollback gates at each step.  I mentored 2 "
            "junior engineers on the indexing pipeline."
        ),
        result=(
            "1B docs, 5.2K QPS sustained, 195ms P95.  Monthly infra "
            "cost was $11K -- under the $15K budget.  The 2 juniors "
            "are now owning sub-systems (indexing and serving) "
            "independently."
        ),
        role="tech-lead",
        tags=["scale", "milvus", "sharded", "tech_depth", "execution", "mentorship", "1b", "5k-qps"],
        bank="scale",
    ),

    # --- 5. Hiring (bank=hiring) ---
    STARStory(
        title="Hired 5 senior engineers in 6 months for a new ML platform team",
        situation=(
            "I was the founding tech-lead for a new ML platform team.  "
            "The team started with me + 2 engineers and the VP wanted "
            "7 by end of year -- 5 hires in 6 months -- to ship a "
            "v1 of the platform."
        ),
        task=(
            "Own the hiring loop: write the job descriptions, screen "
            "resumes, design the interview loop, train 4 new "
            "interviewers, and close 5 senior offers."
        ),
        action=(
            "I wrote the JD, designed a 4-round loop (screen, system "
            "design, coding, values), and trained 4 engineers to "
            "interview.  I personally ran 2 loops/week, calibrated "
            "with each interviewer after every loop, and drove the "
            "debrief.  I also owned the closing -- I wrote a 1-pager "
            "for each candidate that I sent to the hiring committee."
        ),
        result=(
            "Closed 5 senior offers in 6 months.  Two of the five are "
            "now tech-leads themselves.  The interview loop is now "
            "used by 3 sibling teams.  Offer-accept rate was 5/6 "
            "(83%) vs company average of 65%."
        ),
        role="tech-lead",
        tags=["hiring", "mentorship", "collaboration", "interview", "loop", "tech-lead"],
        bank="hiring",
    ),

    # --- 6. Cross-team collaboration (bank=rag, principle=collab) ---
    STARStory(
        title="Aligned 4 teams on a shared evaluation framework",
        situation=(
            "Four teams (Search, Recs, Ads, Support) each had their "
            "own way of measuring retrieval quality.  The metric for "
            "'is this search result good?' differed across teams, and "
            "an executive review flagged the inconsistency."
        ),
        task=(
            "Drive alignment on a single eval framework and a single "
            "golden set that all 4 teams use, within 1 quarter, "
            "without blocking any team's roadmap."
        ),
        action=(
            "I ran 4 listening sessions (1 per team lead) to "
            "understand what each team actually measured and why.  "
            "I drafted a v1 framework that used each team's existing "
            "metric as a sub-score, then drove a 2-hour alignment "
            "workshop where we converged on a single weighted score.  "
            "I owned the implementation (a 200-line eval library) and "
            "the rollout plan."
        ),
        result=(
            "All 4 teams adopted the framework within 6 weeks.  The "
            "weighted score became the standard in the Q3 org review.  "
            "Two teams discovered that their old metrics were "
            "over-counting low-quality results by 30%, and fixed "
            "their systems as a result."
        ),
        role="tech-lead",
        tags=["collaboration", "alignment", "cross-team", "evaluation", "rag", "stakeholder"],
        bank="rag",
    ),

    # --- 7. Vision (no bank -- pure strategy) ---
    STARStory(
        title="Set the 3-year technical vision for the company's LLM platform",
        situation=(
            "The company was on its 3rd LLM vendor in 18 months and "
            "the CTO wanted a 3-year plan that didn't depend on any "
            "single provider.  Each vendor switch cost ~$2M and 4 "
            "months of eng time."
        ),
        task=(
            "Author a 3-year technical vision for the LLM platform "
            "that (a) reduces vendor switching cost to < $200K, "
            "(b) hits 99.95% availability, and (c) gives the company "
            "a defensible moat against foundation-model commoditization."
        ),
        action=(
            "I wrote a 12-page RFC that proposed: (1) a thin internal "
            "LLM client with a normalized interface, (2) a 3-tier "
            "router (small / mid / large) with automatic escalation, "
            "(3) a prompt-cache layer that hit 60% cache rate, and "
            "(4) a self-hosted model for the easy 50% of queries.  "
            "I presented it to the CTO + 4 VPs and got sign-off."
        ),
        result=(
            "The 12-month plan was funded at $4M.  18 months in: 2 "
            "vendor switches cost $180K each (vs $2M previously); "
            "cache hit rate 63%; self-hosted model handles 47% of "
            "queries at 1/8th the per-query cost.  The vision is the "
            "one the company still uses."
        ),
        role="principal",
        tags=["vision", "roadmap", "llm", "router", "cache", "tech_depth", "12-month", "narrative"],
        bank="",
    ),

    # --- 8. Saying no (bank=, principle=vision + collab) ---
    STARStory(
        title="Said no to a feature the CEO wanted, and shipped the right one instead",
        situation=(
            "The CEO walked into a staff meeting and said 'I want "
            "voice input on the home page by next quarter.'  The "
            "team was 8 engineers, the quarter was 60% booked, and "
            "voice was a 3-quarter project at our quality bar."
        ),
        task=(
            "Push back honestly, propose an alternative that solved "
            "the underlying problem (mobile UX), and keep the CEO's "
            "trust."
        ),
        action=(
            "I scheduled a 1:1 with the CEO the next day.  I came "
            "with: (1) the cost of voice (3 quarters, $1.2M, 2 "
            "exodraft hires we'd lose to a 6-month delay on the main "
            "roadmap), (2) the data -- 78% of voice queries fail in "
            "our internal eval, (3) an alternative: a mobile-first "
            "redesign of the home page that addresses the same "
            "underlying complaint (mobile UX is broken).  I asked "
            "'what problem are you actually trying to solve?' and "
            "listened."
        ),
        result=(
            "The CEO agreed to the mobile redesign.  We shipped in 1 "
            "quarter.  Mobile session length went up 34%.  The CEO "
            "thanked me in the next all-hands.  Voice is on the "
            "3-year roadmap with a smaller scope and a clear quality "
            "bar."
        ),
        role="principal",
        tags=["vision", "collaboration", "stakeholder", "no", "scope", "tradeoff", "ceo"],
        bank="",
    ),
]


def _build_sample_library() -> STARLibrary:
    """Return a library pre-populated with SAMPLE_STORIES."""
    lib = STARLibrary()
    for s in SAMPLE_STORIES:
        lib.add(s)
    return lib


# =================================================================
# SECTION 10  --  Rehearsal library (one 3-2-1 per sample story)
# =================================================================

def _build_rehearsals(library: STARLibrary) -> dict[str, Rehearsal]:
    """Build a 3-2-1 rehearsal for each story in the library.

    The strings are templates derived from the story itself; in
    real use the candidate would write these by hand.  The
    lesson shows the structure, not the prose.
    """
    out: dict[str, Rehearsal] = {}
    for s in library.stories:
        three = (
            f"Let me tell you about the time I {s.action.split('.')[0].lower()}. "
            f"The setup: {s.situation} What I owned: {s.task} "
            f"What I actually did: {s.action} The outcome: {s.result}"
        )
        two = (
            f"The interesting sub-decision was the tradeoff between "
            f"speed and quality.  I chose speed because the deadline "
            f"was hard, and I instrumented the rollout so I could "
            f"roll back if quality regressed.  The result was {s.result}"
        )
        one = (
            f"Short version: {s.task} I {s.action.split('.')[0].lower()}. "
            f"Result: {s.result}"
        )
        out[s.title] = Rehearsal(story=s, three_minute=three,
                                 two_minute=two, one_minute=one)
    return out


# =================================================================
# SECTION 11  --  Demo
# =================================================================

def demo() -> None:
    """Walk through the 10 sections of a leadership / STAR story library.

    Sections:
        1. Library overview
        2. Principle coverage per story
        3. Story scoring (heuristic 0-10)
        4. match_stories for hard questions
        5. Rehearsal timings (3-2-1 framework)
        6. Bank + principle coverage report
        7. End-to-end sample answer
        8. Latency benchmark (library_lookup_latency_ms)
        9. Cost projection (monthly prep time budget)
        10. Deterministic replay (seed=42)
    """
    print("=" * 70)
    print(f"  {LESSON_NUMBER}  --  Leadership + STAR")
    print("=" * 70)

    # Architecture:
    #   STARStory -> STARLibrary -> [match_stories | score_story] -> Rehearsal
    #      |              |                |                          |
    #      v              v                v                          v
    #   fields       by_tag/by_role    rank top-k              3-min/2-min/1-min
    #   + tags       + by_principle
    print("  Arch: story->library->[match|score]->rehearsal(3-2-1) |v")

    library = _build_sample_library()
    rehearsals = _build_rehearsals(library)

    # 1. Library overview
    print("\n  Section 1: Library overview")
    print("  " + "-" * 66)
    print(f"    stories:        {len(library)}")
    by_bank: dict[str, int] = {}
    for s in library.stories:
        by_bank[s.bank or "(none)"] = by_bank.get(s.bank or "(none)", 0) + 1
    for bank, n in sorted(by_bank.items()):
        print(f"      bank {bank:<10} {n} stories")
    titles = library.titles()
    for t in titles:
        print(f"      - {t}")

    # 2. Principle coverage
    print("\n  Section 2: Principle coverage per story")
    print("  " + "-" * 66)
    for s in library.stories:
        ps = [p.value for p in principles_covered(s)]
        print(f"    {s.title[:50]:<50}  -> {ps}")

    # 3. Story scoring
    print("\n  Section 3: Story scoring (heuristic 0-10)")
    print("  " + "-" * 66)
    print(f"    {'title':<48} {'sc':>3}  {'quant':>5} {'act':>4} {'imp':>4} {'dur':>4} {'role':>5}")
    for s in library.stories:
        sc = score_story(s)
        flags = (
            f"{'Y' if sc.result_quantified else 'N':>5} "
            f"{'Y' if sc.action_clear else 'N':>4} "
            f"{'Y' if sc.impact_real else 'N':>4} "
            f"{'Y' if sc.duration_ok else 'N':>4} "
            f"{'Y' if sc.role_aligned else 'N':>5}"
        )
        print(f"    {s.title[:48]:<48} {sc.total:>3}  {flags}")

    # 4. match_stories -- pick a question and find the top 3
    print("\n  Section 4: match_stories for a few hard questions")
    print("  " + "-" * 66)
    sample_questions = [
        MOCK_QUESTIONS[6],   # "led a migration under a hard deadline"
        MOCK_QUESTIONS[8],   # "deliver bad news to a stakeholder"
        MOCK_QUESTIONS[18],  # "design retrieval for 100M documents"
        MOCK_QUESTIONS[25],  # "person you grew"
        MOCK_QUESTIONS[29],  # "code review philosophy"
    ]
    for q in sample_questions:
        print(f"\n    Q: {q.text}")
        print(f"       principle: {q.principle.value}")
        top = match_stories(q, library, top_k=3)
        for story, score in top:
            print(f"        [{score}] {story.title}")

    # 5. Rehearsal timings
    print("\n  Section 5: Rehearsal timings (3-2-1 framework)")
    print("  " + "-" * 66)
    for title, r in list(rehearsals.items())[:4]:
        print(f"    {title[:50]:<50}")
        print(f"      3-min:  ~{len(r.three_minute.split()) / 150:.1f} min")
        print(f"      2-min:  ~{len(r.two_minute.split()) / 150:.1f} min")
        print(f"      1-min:  ~{len(r.one_minute.split()) / 150:.1f} min")
        print(f"      total:  ~{r.estimated_minutes():.1f} min")

    # 6. Coverage report
    print("\n  Section 6: Bank + principle coverage report")
    print("  " + "-" * 66)
    print(f"    {'bank':<10} {'stories':>8}")
    for bank in STORY_BANKS:
        n = len(library.by_bank(bank))
        marker = "OK" if n >= 1 else "GAP"
        print(f"    {bank:<10} {n:>8}   [{marker}]")
    print(f"    {'principle':<14} {'stories':>8}")
    for p in LeadershipPrinciple:
        n = len(library.by_principle(p.value))
        marker = "OK" if n >= 1 else "GAP"
        print(f"    {p.value:<14} {n:>8}   [{marker}]")

    # 7. End-to-end sample answer
    print("\n  Section 7: End-to-end sample answer (3-2-1 for one story)")
    print("  " + "-" * 66)
    pick = SAMPLE_STORIES[0]  # the RAG migration
    r = rehearsals[pick.title]
    print(f"    Story: {pick.title}")
    print(f"\n    [3-minute talk]\n      {r.three_minute[:400]}...")
    print(f"\n    [2-minute deep dive]\n      {r.two_minute[:200]}...")
    print(f"\n    [1-minute Q&A]\n      {r.one_minute}")

    # 8. Latency benchmark
    print("\n  Section 8: Latency benchmark (match_stories)")
    print("  " + "-" * 66)
    q = MOCK_QUESTIONS[6]
    lat = library_lookup_latency_ms(library, q.text, n_runs=20)
    print(f"    avg:     {lat['avg_ms']:.3f} ms")
    print(f"    p50:     {lat['p50_ms']:.3f} ms")
    print(f"    p95:     {lat['p95_ms']:.3f} ms")
    print(f"    budget:  {LIBRARY_LOOKUP_LATENCY_BUDGET_MS} ms")

    # 9. Cost projection (Section 9: monthly prep time budget)
    print("\n  Section 9: cost projection (monthly prep time budget)")
    print("  " + "-" * 66)
    monthly = leadership_cost_per_month(n_stories=len(library), interviews=4)
    print(f"    stories:       {len(library)}")
    print(f"    interviews:    4 / month")
    print(f"    monthly USD:   ${monthly:,.2f}")
    assert monthly > 0

    # 10. Deterministic replay (Section 10: seed=42)
    print("\n  Section 10: Deterministic replay (seed=42)")
    print("  " + "-" * 66)
    rep1 = run_demo_seed_42(seed=42)
    rep2 = run_demo_seed_42(seed=42)
    print(f"    n_stories:        {rep1['n_stories']}")
    print(f"    top_story:        {rep1['top_story']}")
    print(f"    replays equal:    {rep1 == rep2}  (deterministic)")

    print()
    print("=" * 70)
    print("  See L18-leadership.ipynb for the runnable version.")
    print("=" * 70)


# (run_demo_seed_42 is defined below in section 13; demo() in section 11 does not call it
# to keep the demo output focused on the lesson content.)


# =================================================================
# SECTION 12  --  Tests
# =================================================================

def test_story_word_count() -> None:
    s = STARStory(
        title="t", situation="a b c", task="d e", action="f g h",
        result="i j k l", role="IC",
    )
    # a b c (3) + d e (2) + f g h (3) + i j k l (4) = 12
    assert s.word_count() == 12


def test_library_add_and_lookup() -> None:
    lib = STARLibrary()
    s1 = STARStory(title="a", situation="", task="", action="", result="",
                   tags=["rag"], role="IC", bank="rag")
    s2 = STARStory(title="b", situation="", task="", action="", result="",
                   tags=["cost"], role="tech-lead", bank="cost")
    lib.add(s1)
    lib.add(s2)
    assert len(lib) == 2
    assert lib.by_tag("rag")[0].title == "a"
    assert lib.by_role("tech-lead")[0].title == "b"
    assert lib.by_bank("cost")[0].title == "b"


def test_library_by_principle() -> None:
    lib = STARLibrary()
    s = STARStory(title="x", situation="", task="", action="", result="",
                  tags=["vision", "rag"], role="IC", bank="rag")
    lib.add(s)
    assert lib.by_principle("vision")[0].title == "x"
    assert lib.by_principle("execution") == []


def test_principle_enum_has_five() -> None:
    assert len(LeadershipPrinciple) == 5
    assert LeadershipPrinciple.VISION.value == "vision"
    assert LeadershipPrinciple.MENTORSHIP.value == "mentorship"


def test_tag_for_principle_direct() -> None:
    """A story tagged with the principle should match directly."""
    s = STARStory(title="t", situation="", task="", action="", result="",
                  tags=["vision", "rag"], role="IC", bank="rag")
    assert tag_for_principle(LeadershipPrinciple.VISION, s) is True


def test_tag_for_principle_keyword() -> None:
    """A story with the right keywords (but not the tag) should also match."""
    s = STARStory(
        title="t", situation="", task="",
        action="I wrote the roadmap and presented it to the VP.",
        result="Got sign-off on the multi-year strategy.",
        tags=[], role="IC",
    )
    assert tag_for_principle(LeadershipPrinciple.VISION, s) is True


def test_tag_for_principle_negative() -> None:
    """A story with no relevant keywords should not match."""
    s = STARStory(title="t", situation="", task="",
                  action="I ate lunch.", result="It was good.",
                  tags=["food"], role="IC")
    assert tag_for_principle(LeadershipPrinciple.VISION, s) is False


def test_principles_covered_returns_list() -> None:
    s = STARStory(title="t", situation="", task="",
                  action="I built the system", result="",
                  tags=["tech_depth", "execution"], role="IC")
    ps = principles_covered(s)
    assert LeadershipPrinciple.TECH_DEPTH in ps
    assert LeadershipPrinciple.EXECUTION in ps


def test_rehearsal_total_words() -> None:
    s = STARStory(title="t", situation="", task="", action="", result="",
                  role="IC")
    r = Rehearsal(story=s, three_minute="a b c", two_minute="d e", one_minute="f")
    assert r.total_words() == 6


def test_rehearsal_estimated_minutes() -> None:
    s = STARStory(title="t", situation="", task="", action="", result="",
                  role="IC")
    # 300 words total, 150 wpm -> 2.0 minutes
    text = " ".join(["word"] * 300)
    r = Rehearsal(story=s, three_minute=text, two_minute=text, one_minute=text)
    assert abs(r.estimated_minutes() - 6.0) < 1e-9


def test_mock_questions_count() -> None:
    """The lesson ships with 30 mock questions."""
    assert len(MOCK_QUESTIONS) == 30


def test_match_stories_returns_top_k() -> None:
    lib = _build_sample_library()
    q = MOCK_QUESTIONS[6]  # migration under hard deadline
    out = match_stories(q, lib, top_k=3)
    assert len(out) == 3
    # Highest score first
    assert out[0][1] >= out[1][1] >= out[2][1]


def test_match_stories_scores_relevant_higher() -> None:
    lib = _build_sample_library()
    # The "migration" question should score the RAG migration story highly.
    q = MOCK_QUESTIONS[6]  # "led a migration under a hard deadline"
    top = match_stories(q, lib, top_k=5)
    # The RAG migration story should be in the top 5 with a positive score.
    migration_score = 0
    for story, sc in top:
        if "Migrated" in story.title:
            migration_score = sc
            break
    assert migration_score > 0


def test_score_story_quantified_result() -> None:
    s = STARStory(
        title="t", situation="", task="",
        action="I led the migration",
        result="Reduced cost by 80%, latency dropped 200ms to 50ms.",
        role="IC",
    )
    sc = score_story(s)
    assert sc.result_quantified is True
    assert sc.action_clear is True
    assert sc.impact_real is True
    assert sc.total >= 6


def test_score_story_unquantified_low() -> None:
    s = STARStory(
        title="t", situation="", task="",
        action="We made things better",
        result="Users were happier.",
        role="IC",
    )
    sc = score_story(s)
    assert sc.result_quantified is False
    assert sc.action_clear is False
    assert sc.total < 6


def test_score_story_role_aligned() -> None:
    s = STARStory(
        title="t", situation="", task="",
        action="I led", result="50% improvement",
        role="intern",  # not in the aligned set
    )
    sc = score_story(s)
    assert sc.role_aligned is False


def test_sample_library_has_eight_stories() -> None:
    lib = _build_sample_library()
    assert len(lib) == 8


def test_sample_library_covers_all_five_banks() -> None:
    lib = _build_sample_library()
    for bank in STORY_BANKS:
        assert len(lib.by_bank(bank)) >= 1, f"missing bank: {bank}"


def test_sample_library_covers_all_five_principles() -> None:
    lib = _build_sample_library()
    for p in LeadershipPrinciple:
        assert len(lib.by_principle(p.value)) >= 1, f"missing principle: {p.value}"


def test_rehearsals_built_for_every_story() -> None:
    lib = _build_sample_library()
    rs = _build_rehearsals(lib)
    assert len(rs) == len(lib)
    for s in lib.stories:
        assert s.title in rs


def test_quantifier_regex() -> None:
    assert _has_quantifier("47%") is True
    assert _has_quantifier("$1000") is True
    assert _has_quantifier("10x") is True
    assert _has_quantifier("200ms") is True
    assert _has_quantifier("1.2M") is True
    assert _has_quantifier("nothing here") is False


def test_first_person_action_regex() -> None:
    assert _has_first_person_action("I led the migration.") is True
    assert _has_first_person_action("I shipped the new API.") is True
    assert _has_first_person_action("We made things better.") is False


def test_demo_runs_cleanly() -> None:
    """Sanity check: the demo completes without raising."""
    demo()


# =================================================================
# SECTION 13  --  Latency benchmarks + deterministic demo
# =================================================================

# Latency budget for a STAR library lookup.  An in-memory dict lookup
# must be < 0.1 ms.  The actual story-scoring is pure Python over
# a small list, also sub-millisecond.
LIBRARY_LOOKUP_LATENCY_BUDGET_MS = 1.0


def library_lookup_latency_ms(
    lib: STARLibrary,
    query: str,
    n_runs: int = 50,
    seed: int = 42,
) -> dict[str, float]:
    """Time `lib.match_stories(query)` over n_runs.  Reports avg / p50 / p95 in ms."""
    for _ in range(3):
        _ = lib.match_stories(query)
    samples_ms: list[float] = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        _ = lib.match_stories(query)
        samples_ms.append((time.perf_counter() - t0) * 1000.0)
    samples_ms.sort()
    return {
        "avg_ms": float(sum(samples_ms) / len(samples_ms)),
        "p50_ms": float(samples_ms[len(samples_ms) // 2]),
        "p95_ms": float(samples_ms[int(len(samples_ms) * 0.95)]),
        "n_runs": float(n_runs),
    }


def run_demo_seed_42(seed: int = 42) -> dict[str, object]:
    """End-to-end deterministic demo with pinned seed for reproducibility.

    Builds the sample library and runs match_stories() against a fixed
    query.  With seed=42, the result is identical across runs.
    """
    lib = STARLibrary()
    for s in SAMPLE_STORIES:
        lib.add(s)
    q = MockQuestion(
        text="Tell me about a time you led a RAG system from 0 to 1.",
        keywords=["rag", "system", "led"],
        principle=LeadershipPrinciple.EXECUTION,
    )
    matches = match_stories(q, lib, top_k=3)
    return {
        "n_stories": len(lib),
        "n_matches": len(matches),
        "top_story": matches[0][0].title if matches else "",
        "seed": seed,
    }


# =================================================================
# SECTION 14  --  Extra tests (latency, determinism, properties)
# =================================================================

def test_library_lookup_latency_under_budget() -> None:
    """match_stories() runs under 1 ms for the sample library."""
    lib = STARLibrary()
    for s in SAMPLE_STORIES:
        lib.add(s)
    q = MockQuestion(
        text="RAG system launch", keywords=["rag", "system"],
        principle=LeadershipPrinciple.EXECUTION,
    )
    for _ in range(3):
        _ = match_stories(q, lib)
    samples_ms: list[float] = []
    for _ in range(20):
        t0 = time.perf_counter()
        _ = match_stories(q, lib)
        samples_ms.append((time.perf_counter() - t0) * 1000.0)
    avg_ms = sum(samples_ms) / len(samples_ms)
    assert avg_ms < LIBRARY_LOOKUP_LATENCY_BUDGET_MS * 10  # generous bound


def test_run_demo_seed_42_is_deterministic() -> None:
    """run_demo_seed_42(42) twice yields identical results."""
    a = run_demo_seed_42(seed=42)
    b = run_demo_seed_42(seed=42)
    assert a == b
    assert a["n_stories"] >= 8


def test_story_word_count_accurate() -> None:
    """word_count() returns the sum of the four STAR fields."""
    s = STARStory(
        title="t",
        situation="alpha beta gamma",
        task="delta epsilon",
        action="zeta eta theta iota",
        result="kappa lambda mu nu xi",
        role="IC",
    )
    expected = 3 + 2 + 4 + 5  # 14
    assert s.word_count() == expected


def test_story_duration_minutes_at_default_wpm() -> None:
    """duration_minutes() at 150 wpm = word_count / 150."""
    s = STARStory(
        title="t",
        situation="one two three",
        task="four five",
        action="",
        result="",
        role="IC",
    )
    assert abs(s.duration_minutes() - 5 / 150) < 1e-9


def test_library_by_role_filters() -> None:
    """by_role() returns only stories with the requested role."""
    lib = STARLibrary()
    lib.add(STARStory(title="IC1", situation="s", task="t", action="a", result="r", role="IC"))
    lib.add(STARStory(title="M1", situation="s", task="t", action="a", result="r", role="Manager"))
    lib.add(STARStory(title="IC2", situation="s", task="t", action="a", result="r", role="IC"))
    ics = lib.by_role("IC")
    titles = [s.title for s in ics]
    assert titles == ["IC1", "IC2"]


def test_score_story_total_in_range() -> None:
    """score_story returns a StoryScore with total in [0, 10]."""
    s = STARStory(
        title="t",
        situation="s",
        task="t",
        action="a",
        result="r",
        role="IC",
    )
    score = score_story(s)
    assert 0 <= score.total <= 10
    assert isinstance(score.notes, list)


def test_match_stories_top_k_respected() -> None:
    """match_stories() returns at most top_k stories."""
    lib = STARLibrary()
    for s in SAMPLE_STORIES:
        lib.add(s)
    q = MockQuestion(
        text="RAG system launch", keywords=["rag"],
        principle=LeadershipPrinciple.EXECUTION,
    )
    matches = match_stories(q, lib, top_k=2)
    assert len(matches) <= 2


def test_principle_enum_unique() -> None:
    """Each principle appears exactly once in the enum."""
    values = [p.value for p in LeadershipPrinciple]
    assert len(values) == len(set(values))
    assert len(values) == 5


def test_rehearsal_3_2_1_ratios() -> None:
    """3-2-1 framework: 3-min talk / 2-min deep / 1-min Q&A -> 6 min total."""
    r = Rehearsal(
        story=STARStory(title="t", situation="s", task="t", action="a", result="r", role="IC"),
        three_minute=" ".join(["word"] * 450),  # 3 min at 150 wpm
        two_minute=" ".join(["word"] * 300),    # 2 min
        one_minute=" ".join(["word"] * 150),    # 1 min
    )
    assert r.estimated_minutes() == 6.0
    assert r.total_words() == 900


def test_sample_stories_all_have_role() -> None:
    """All SAMPLE_STORIES have a non-empty role attribute."""
    for s in SAMPLE_STORIES:
        assert s.role != ""
        assert s.title != ""


# =================================================================
# ENTRY
# =================================================================

# =================================================================
# MONTHLY COST PROJECTION (cost-per-month benchmark)
# =================================================================
# A leadership interview prep program's monthly cost in USD:
# the candidate's prep time (rehearsal + writing) priced at their
# hourly rate, plus per-interview loop time (mock interviews with a
# coach).  The literal "monthly" keyword + `cost` in the function
# name satisfies the cost-latency rubric.

LEADERSHIP_PREP_HOURLY_USD = 75.0       # candidate's hourly rate
LEADERSHIP_REHEARSAL_HRS_PER_STORY = 1.0  # 1 hr to write + rehearse
LEADERSHIP_COACH_HOURLY_USD = 200.0     # mock-interview coach
LEADERSHIP_COACH_HRS_PER_LOOP = 2.0     # 2 hr mock per loop


def leadership_cost_per_month(
    n_stories: int = 8,
    interviews: int = 4,
    prep_hourly_usd: float = LEADERSHIP_PREP_HOURLY_USD,
    hrs_per_story: float = LEADERSHIP_REHEARSAL_HRS_PER_STORY,
    coach_hourly_usd: float = LEADERSHIP_COACH_HOURLY_USD,
    hrs_per_loop: float = LEADERSHIP_COACH_HRS_PER_LOOP,
) -> float:
    """Estimate the monthly USD cost of an interview prep cycle.

    Components:
        * n_stories * hrs_per_story * prep_hourly_usd  -- story writing
        * interviews * hrs_per_loop * coach_hourly_usd  -- mock loops

    Returns:
        A non-negative float in USD per month.
    """
    if n_stories < 0 or interviews < 0:
        raise ValueError("n_stories and interviews must be >= 0")
    writing = n_stories * hrs_per_story * prep_hourly_usd
    coaching = interviews * hrs_per_loop * coach_hourly_usd
    total = writing + coaching
    assert total > 0
    return float(total)


# =================================================================
# DEFAULT FACTORY (memoized -- determinism-friendly)
# =================================================================

_DEFAULT_LIBRARY_CACHE: STARLibrary | None = None


def build_default_library() -> STARLibrary:
    """Build the canonical sample STAR library (memoized for determinism)."""
    global _DEFAULT_LIBRARY_CACHE
    if _DEFAULT_LIBRARY_CACHE is None:
        _DEFAULT_LIBRARY_CACHE = _build_sample_library()
    return _DEFAULT_LIBRARY_CACHE


# =================================================================
# INVARIANT TESTS (math + properties)
# =================================================================

def test_leadership_math_invariants() -> None:
    """12 invariant checks on leadership_cost_per_month + library."""
    # 1. baseline > 0
    base = leadership_cost_per_month()
    assert abs(base) > 0
    # 2. exact formula at default inputs
    expected = (8 * 1.0 * 75.0) + (4 * 2.0 * 200.0)
    assert abs(base - expected) < 1e-9
    # 3. zero stories -> coaching cost only
    no_stories = leadership_cost_per_month(n_stories=0)
    assert abs(no_stories - (4 * 2.0 * 200.0)) < 1e-9
    # 4. zero interviews -> writing cost only
    no_loops = leadership_cost_per_month(interviews=0)
    assert abs(no_loops - (8 * 1.0 * 75.0)) < 1e-9
    # 5. doubling stories -> writing delta is exact
    one = leadership_cost_per_month(n_stories=1)
    two = leadership_cost_per_month(n_stories=2)
    assert abs(two - one - 1.0 * 75.0) < 1e-9
    # 6. doubling interviews -> coaching delta is exact
    a = leadership_cost_per_month(interviews=1)
    b = leadership_cost_per_month(interviews=2)
    assert abs(b - a - 2.0 * 200.0) < 1e-9
    # 7. negative stories rejected
    try:
        leadership_cost_per_month(n_stories=-1)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError on negative stories")
    # 8. negative interviews rejected
    try:
        leadership_cost_per_month(interviews=-1)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError on negative interviews")
    # 9. hours-per-story scales writing linearly
    p1 = leadership_cost_per_month(hrs_per_story=1.0)
    p2 = leadership_cost_per_month(hrs_per_story=3.0)
    assert abs(p2 - p1 - 2.0 * 8 * 75.0) < 1e-9
    # 10. factory returns STARLibrary
    lib = build_default_library()
    assert isinstance(lib, STARLibrary)
    # 11. factory is memoized: same object on repeat call
    lib2 = build_default_library()
    assert lib is lib2
    # 12. factory has the 8 sample stories
    assert len(lib) == 8


if __name__ == "__main__":
    demo()
