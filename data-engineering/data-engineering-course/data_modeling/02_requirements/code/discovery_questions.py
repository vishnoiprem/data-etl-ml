"""Bank of discovery questions for data modeling interviews.

The 5W+H framework, expanded into 50+ specific questions. Most
interviewers will answer 5–8 of these in the first 5 minutes; the
candidate's job is to *pick* the right 5–8, not to ask all 50.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""

from __future__ import annotations

from typing import Dict, List

# Each entry is a (category, question) pair.
DISCOVERY_QUESTIONS: List[Dict[str, str]] = [
    # ---- WHO: consumers ------------------------------------------------
    {"category": "who", "question": "Who are the primary consumers of "
        "this warehouse? Analytics, data science, ops, finance, ML?"},
    {"category": "who", "question": "Will the warehouse be queried by "
        "humans (BI tools, notebooks) or by services (ML feature "
        "store, automation)?"},
    {"category": "who", "question": "Is there an existing data team who "
        "owns this today, or is this greenfield?"},
    {"category": "who", "question": "Do we need to support self-service "
        "for non-technical stakeholders?"},

    # ---- WHAT: use cases ----------------------------------------------
    {"category": "what", "question": "What are the top 3–5 questions the "
        "warehouse must answer on day one?"},
    {"category": "what", "question": "What's the *most important* metric? "
        "What's the second?"},
    {"category": "what", "question": "Do we need to support funnel "
        "analysis? Cohort analysis? Retention curves?"},
    {"category": "what", "question": "Do we need sessionization (rolling "
        "events into sessions)?"},
    {"category": "what", "question": "Do we need to support A/B test "
        "analysis (exposures, treatment assignment)?"},
    {"category": "what", "question": "Are there any must-have derived "
        "metrics (e.g. LTV, churn risk)?"},

    # ---- WHEN: freshness / time ---------------------------------------
    {"category": "when", "question": "What's the freshness requirement? "
        "Real-time, hourly, daily, weekly?"},
    {"category": "when", "question": "How is 'now' defined? Server time, "
        "user-local time, event time?"},
    {"category": "when", "question": "Do we need to support late-arriving "
        "data (events that come in hours or days after the event)?"},
    {"category": "when", "question": "What's the longest reasonable "
        "query window? (Day, week, quarter, year, all-time?)"},
    {"category": "when", "question": "Do we need point-in-time correctness "
        "(e.g. what did the user look like 6 months ago)?"},
    {"category": "when", "question": "Is there a backfill scenario (we "
        "just switched from system A to system B)?"},

    # ---- WHERE: sources ------------------------------------------------
    {"category": "where", "question": "What are the source systems? "
        "OLTP DB? Event stream? Third-party APIs? File drops?"},
    {"category": "where", "question": "Are there PII / regulatory "
        "constraints on any of the source data?"},
    {"category": "where", "question": "Is the source schema stable, or "
        "does it change frequently?"},
    {"category": "where", "question": "Are source systems replicated "
        "(CDC, change data capture) or do we batch-extract?"},
    {"category": "where", "question": "Do we have a data lake or a "
        "warehouse today, or are we building from scratch?"},

    # ---- WHY: priority -------------------------------------------------
    {"category": "why", "question": "Why is this warehouse being built "
        "now? What changed?"},
    {"category": "why", "question": "What's the cost of getting it "
        "wrong? (Compliance? Lost revenue? Slow decisions?)"},
    {"category": "why", "question": "Which team is the biggest internal "
        "customer? What do they care about most?"},
    {"category": "why", "question": "Are there any recent incidents "
        "where bad data caused real damage?"},

    # ---- HOW: metrics definition --------------------------------------
    {"category": "how", "question": "How is the headline metric "
        "defined, exactly? (e.g. is DAU unique-logged-in or unique-"
        "active-in-any-way?)"},
    {"category": "how", "question": "How is revenue defined? Gross, "
        "net, recognized, collected?"},
    {"category": "how", "question": "How are cancellations / refunds "
        "treated? (Reverse the original event? Add a new event?)"},
    {"category": "how", "question": "How are users de-duplicated across "
        "devices?"},
    {"category": "how", "question": "How are bots / internal users "
        "filtered out?"},
    {"category": "how", "question": "How are timezones handled? UTC "
        "everywhere, or user-local?"},
    {"category": "how", "question": "What currency / unit conventions "
        "are used (USD cents vs dollars)?"},
    {"category": "how", "question": "Are there known data quality "
        "issues in the source we should design around?"},

    # ---- SCALE: volume -------------------------------------------------
    {"category": "scale", "question": "How many events / rows per day "
        "do we expect at peak? At steady state?"},
    {"category": "scale", "question": "How many distinct users / "
        "customers do we have today? In 12 months?"},
    {"category": "scale", "question": "How many products / SKUs / "
        "categories?"},
    {"category": "scale", "question": "What's the storage budget? "
        "How long do we keep the raw data? The warehouse data?"},
    {"category": "scale", "question": "What's the query concurrency "
        "we expect to support?"},

    # ---- HISTORICAL: how things change --------------------------------
    {"category": "historical", "question": "Which entities change "
        "over time and which don't? (Users: yes. Currencies: yes. "
        "Countries: rarely.)"},
    {"category": "historical", "question": "Do we need to track the "
        "history of changes (SCD Type 2) or just the current value?"},
    {"category": "historical", "question": "If a user changes their "
        "country, do we re-attribute historical events to the new "
        "country?"},
    {"category": "historical", "question": "How do we handle deleted "
        "records? Soft delete? Hard delete with audit log?"},

    # ---- EDGE CASES ---------------------------------------------------
    {"category": "edge", "question": "What happens when the source "
        "system is down for an hour?"},
    {"category": "edge", "question": "What happens when the same event "
        "arrives twice?"},
    {"category": "edge", "question": "What happens when an event "
        "arrives out of order?"},
    {"category": "edge", "question": "What happens when a user has "
        "two sessions open at the same time?"},
    {"category": "edge", "question": "What happens when a user deletes "
        "their account? Do we keep their events?"},
    {"category": "edge", "question": "What happens when a new "
        "dimension value appears (e.g. new country, new product "
        "category)?"},
    {"category": "edge", "question": "What's the recovery story if "
        "we discover the warehouse has been wrong for a month?"},
    {"category": "governance", "question": "Who owns the metric "
        "definitions? (Marketing, product, finance all want MAU "
        "to be different things.)"},
]


def by_category() -> Dict[str, List[str]]:
    """Group the questions by category.

    >>> out = by_category()
    >>> "who" in out and "what" in out
    True
    >>> all(isinstance(v, list) for v in out.values())
    True
    """
    grouped: Dict[str, List[str]] = {}
    for entry in DISCOVERY_QUESTIONS:
        grouped.setdefault(entry["category"], []).append(entry["question"])
    return grouped


def pick_top(n: int = 8, seed: int = 42) -> List[Dict[str, str]]:
    """Pick a deterministic sample of ``n`` discovery questions.

    The point of this helper is for practice: you can hit it before
    a mock interview and get a random-feeling but reproducible
    subset to drill on.

    Args:
        n: how many questions to return.
        seed: deterministic seed.

    Returns:
        A list of dicts with keys 'category' and 'question'.
    """
    import random

    rng = random.Random(seed)
    pool = list(DISCOVERY_QUESTIONS)
    rng.shuffle(pool)
    return pool[:n]
