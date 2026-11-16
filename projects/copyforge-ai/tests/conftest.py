"""Shared fixtures for the CopyForge test suite.

Everything here is hermetic: no network, no Ollama, no API key.
"""

from __future__ import annotations

import pytest

from copyforge_ai.llm import StubRouter


@pytest.fixture
def router() -> StubRouter:
    """The deterministic writer backend."""
    return StubRouter()


#: A draft that is deliberately weak — it opens with filler, states no
#: thesis, offers no evidence, and ends with nothing.
WEAK_DRAFT = """---
title: "Scaling Data Pipelines"
---

# Scaling Data Pipelines

In today's fast-paced world, data teams are under increasing pressure to scale their pipelines. This article will explore the topic of pipeline reliability.

## The Challenge

Data pipelines can be difficult to maintain. There are many moving parts and things go wrong. It is important to note that reliability matters.

## Common Approaches

Many teams choose to add more infrastructure. Others choose to monitor more closely. Each approach has trade-offs that should be considered carefully by engineering leaders.

## Conclusion

In conclusion, scaling pipelines is an ongoing journey. We hope this article was useful.
"""


#: A draft that already carries the structures CopyForge inserts.
STRONG_DRAFT = """---
title: "Scaling Data Pipelines"
---

# Scaling Data Pipelines

Two teams run the same pipeline on the same 4 TB of data. One of them
finishes in 9 minutes. The other takes 3 hours. The difference is one
setting nobody wrote down.

## The failure nobody logs

Your pipeline did not fail. It finished. That is the problem: a run that
takes 3 hours and returns the right answer looks identical to a run that
takes 9 minutes, until someone needs the answer before lunch.

The result was a 6x gap between two teams with the same code, and the
cause was a concurrency limit set to 1 in a config file nobody owned.

## What actually happened

We measured it. The slow team was running with a thread pool of 4
against a warehouse with 64 available slots. The fast team had already
raised it to 48.

## The objection worth taking seriously

That said, raising the pool is not free. It costs memory, and a warehouse
with 64 slots is not a warehouse you get on every plan.

## What to do

Start with one thing: check the concurrency limit against the warehouse
tier you are paying for. It takes ten minutes and the answer is either a
fix or a clean bill of health.

So: in the last month, how many times did you find out something was
wrong from someone other than your own process?
"""


@pytest.fixture
def weak_draft() -> str:
    return WEAK_DRAFT


@pytest.fixture
def strong_draft() -> str:
    return STRONG_DRAFT
