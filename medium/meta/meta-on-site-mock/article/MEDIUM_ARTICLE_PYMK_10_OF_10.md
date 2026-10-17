---
title: "The Meta L6 PYMK Question: An Interview Transcript With the 5 Drill-Downs That Filter Candidates"
subtitle: "A real conversation. Real pushback. Real answers that get you 10/10."
description: "How to answer the PYMK question at Meta L6 AI-Native Data Engineer on-site. Three transcripts (6/10, 8/10, 10/10), the validator code that prevents hallucination, the SQL that filters weak candidates, and the 5 follow-up questions the interviewer always asks."
author: "Prem Vishnoi"
date: 2026-10-17
canonical_url: ""
cover_image: "pymk_transcript_cover.png"
tags: ["meta", "interview", "data-engineering", "pymk", "llm", "system-design"]
---

# The Meta L6 PYMK Question: An Interview Transcript

A 6/10 candidate, an 8/10 candidate, and the 10/10 candidate who got the offer — answering the same Meta L6 PYMK question, getting pushed back by the interviewer, recovering or not.

The 5 drill-downs the interviewer always hits. The validator code that separates 8/10 from 10/10. The honest-gaps pattern that signals "I've shipped this, not just read about it."

## Table of contents

- [The question](#the-question)
- [Transcript 1: the 6/10 candidate](#transcript-1-the-610-candidate)
- [Transcript 2: the 8/10 candidate](#transcript-2-the-810-candidate)
- [Transcript 3: the 10/10 candidate](#transcript-3-the-1010-candidate)
- [The 5 drill-downs](#the-5-drill-downs)
- [What separates 6/10 from 10/10](#what-separates-610-from-1010)
- [How to practice](#how-to-practice)

---

## The question

> Design a People-You-May-Know feed with AI-generated explanations like "You both worked at Meta." No hallucination. 500 million users. Support historical friendship queries. Bounded fanout for celebrities.

The question is testing four things at once:

1. Can you model a temporal graph at scale (time travel)?
2. Can you generate explanations that are grounded in evidence, not invented by the LLM?
3. Can you control fanout when a single user has 50M followers?
4. Can you wire it together without a privacy violation at 2am?

Most candidates solve #1 with "SCD2" and stop there. The L6 answer solves all four.

---

## Transcript 1: the 6/10 candidate

**Candidate:** Okay, so I'd use a graph database like Neo4j to store friendships. Then I'd run a recommendation algorithm on the graph to find users you might know. For the AI explanations, I'd use an LLM to generate the text.

**Interviewer:** Walk me through how the LLM knows two people worked at the same company.

**Candidate:** I'd put the user's work history in the prompt and ask the LLM to find shared employers.

**Interviewer:** So the LLM decides the facts.

**Candidate:** Yes.

**Interviewer:** What stops it from inventing a company that isn't in the work history?

**Candidate:** I'd tell the prompt not to hallucinate.

**Interviewer:** That's not a defense. Prompts fail. What's the production mechanism?

**Candidate:** I could use a smaller model to verify the output.

**Interviewer:** Verification is also generation. Different model, same problem. Walk me through time travel. If a user asks "were these two friends on January 15th?" — what query runs?

**Candidate:** I'd add a timestamp to each friendship record. Then I could query for the relationship as of that date.

**Interviewer:** How exactly?

**Candidate:** `WHERE created_at <= '2026-01-15' AND (ended_at IS NULL OR ended_at > '2026-01-15')` or something like that.

**Interviewer:** "Or something like that" is a 6/10 answer. We'll move on.

**Why this is 6/10:** Vocabulary without architecture. The candidate uses "graph database" (L47) and "recommendation algorithm" (L47) but can't draw the boxes. They trust the LLM with the facts at L55 ("Yes.") when asked if the LLM decides the facts. They can't write the time-travel SQL — at L71 the candidate says "or something like that" instead of the predicate. Every answer ends in a softener: "or something like that" (L73), "I could use" (L63), "I'd tell the prompt" (L59).

---

## Transcript 2: the 8/10 candidate

**Candidate:** I'd separate the system into three layers. The graph layer stores friendships as SCD2 records with a canonical pair key — `(user_id_low, user_id_high)` so the index is symmetric. The candidate layer runs offline over GraphX or similar, computing the top 100 candidates per active user. The explanation layer pre-computes reasons with the LLM, but only against structured evidence.

**Interviewer:** What does "only against structured evidence" mean concretely?

**Candidate:** I build a JSON evidence object — `{"shared_companies": ["Meta"], "overlap_period": [...], "mutual_friend_count": 5}`. The prompt is locked: "Use only values present in evidence. If not present, output unknown." I never let the LLM decide the facts.

**Interviewer:** So the LLM only verbalizes. Good. Time travel. SQL.

**Candidate:** `SELECT 1 FROM friendships WHERE user_id_low = LEAST(:a, :b) AND user_id_high = GREATEST(:a, :b) AND valid_from <= :as_of AND (valid_to > :as_of OR valid_to IS NULL)`. The canonical key makes the index symmetric, so the query is index-served.

**Interviewer:** A worked at Meta 2018-2020. B worked at Meta 2021-2023. They share a company. Should the system suggest they connect?

**Candidate:** Yes, same employer.

**Interviewer:** They never overlapped. They probably never met. Suggesting them is a wrong explanation.

**Candidate:** ...I could add a date check.

**Interviewer:** What does the date check look like?

**Candidate:** `a.start_date < b.end_date AND b.start_date < a.end_date`, with `COALESCE` for current jobs.

**Interviewer:** Now do you see why the overlap matters?

**Candidate:** Yes. Without it, the explanation "you both worked at Meta" is technically true but semantically false. The user will lose trust after one bad suggestion.

**Why this is 8/10:** The candidate has the architecture right. The LLM-only-verbalizes principle at L85 is correct. The time-travel SQL at L89 is index-served by the canonical key. They miss the overlap on the first pass at L93 ("Yes, same employer.") but recover at L101 with the right predicate. They have the **principle** ("semantically false" at L105) even when they don't have the SQL memorized — and the principle is what the interviewer is testing. The recovery is what separates 8/10 from 6/10. The miss on the first pass is what keeps them from 10/10.

---

## Transcript 3: the 10/10 candidate

**Candidate:** I'll separate the system into three layers — graph history, candidate generation, and online serving with grounded explanations. Let me draw the boxes first, then I'll show you the code that prevents hallucination.

**Interviewer:** Go.

**Candidate:** [draws on whiteboard]

```
                    ┌──────────────────────────────────┐
                    │  LAYER 1: GRAPH (offline)        │
                    │  TAO SCD2 ──► Spark GraphX ──►   │
                    │  candidate set (~100/user)       │
                    └──────────────┬───────────────────┘
                                   │
                    ┌──────────────▼───────────────────┐
                    │  LAYER 2: REASONS (offline)      │
                    │  evidence_json + LLM template    │
                    │  NEVER free LLM generation       │
                    └──────────────┬───────────────────┘
                                   │
                    ┌──────────────▼───────────────────┐
                    │  LAYER 3: SERVING (online)       │
                    │  ZippyDB + privacy filter + audit│
                    │  NO LLM at request time          │
                    └──────────────────────────────────┘
```

The LLM runs only offline, only against structured evidence, and only in a way I can validate deterministically. Let me show you the validator, because that's where most candidates lose the room.

**Interviewer:** Show me.

**Candidate:** [writes on the laptop]

```python
def validate_and_serve(evidence: dict, generated: str) -> str:
    """Reject ungrounded claims. Fall back to a template that can't lie."""
    if "worked at" in generated.lower():
        for company in evidence.get("shared_companies", []):
            if company.lower() in generated.lower():
                return generated
        log_to_audit(evidence, generated, reason="ungrounded_company")
        return f"You have {evidence['mutual_friend_count']} mutual connections."

    if "mutual" in generated.lower():
        nums = re.findall(r'\d+', generated)
        if nums and int(nums[0]) == evidence.get("mutual_friend_count", 0):
            return generated
        log_to_audit(evidence, generated, reason="ungrounded_count")
        return f"You have {evidence['mutual_friend_count']} mutual connections."

    return generated
```

**Interviewer:** Walk me through what this catches.

**Candidate:** If the LLM says "You both worked at Google" but evidence only has Meta, the validator catches the missing company and falls back to a deterministic template. The fallback says "You have 5 mutual connections" — it cannot hallucinate because the number is pulled from the evidence, not generated. The audit log records every rejected claim. Daily, I check the rejection rate. If it spikes, I look at the prompt or the evidence pipeline.

**Interviewer:** What if the LLM says "worked at Meta and Google"?

**Candidate:** The for loop finds Meta in evidence, returns the generated text. The hallucinated "Google" still ships. The validator is per-claim, not whole-output. The honest answer is: this is a known gap. I'd add a per-entity extractor that strips all named entities from the output and verifies each one is in evidence. That's a follow-up; I haven't shipped that yet.

**Interviewer:** That's the right answer. Honest. Now the time-travel question. A and B were friends. The friendship event arrived late on January 17th, but the actual friendship was created on January 14th. Someone asks on January 16th "were they friends?" What do you return?

**Candidate:** They were friends. The as-of query uses `valid_from`, which is set from the event timestamp, not the processing timestamp. The watermark on the ingestion pipeline allows up to 7 days of lateness — Flink reads `event_time`, not `processing_time`. So the late event still has `valid_from = 2026-01-14`, and the as-of query for January 16th returns true.

**Interviewer:** What if the watermark closed? What if it's now January 30th and the late event arrives?

**Candidate:** Then it goes to a reconciliation job, not the live query path. The reconciliation updates the SCD2 table, but any as-of query that ran between January 17th and January 30th would have returned false. The user sees the correct answer for the present, and we accept the past miss because the watermark closed. We log it as a "late event" so we can size the reconciliation job.

**Interviewer:** Why 7 days for the watermark?

**Candidate:** It's a trade-off. Smaller watermark means more events go to reconciliation, but the live query result is more trustworthy. Larger watermark means the live query handles more events, but you risk serving data that's actually stale. Seven days is the standard at Meta scale because the Kafka retention is 14 days and you want a buffer. I'd revisit it if the late-event rate climbs above 1%.

**Interviewer:** Celebrity fanout. 50M followers. Walk me through.

**Candidate:** Above a degree threshold — I'd start with 5,000 — I switch from push to pull. The friendship event is recorded in the SCD2 store, but it's not fanned out to 50M candidate sets. When any of the celebrity's connections opens the app, the PYMK service does a single RocksDB lookup: "is this user connected to a high-degree node?" If yes, the celebrity is added to the candidate list at read time. The cost is bounded — one lookup per request, not 50M writes per event.

**Interviewer:** Where did 5,000 come from?

**Candidate:** I made it up. The real number is whatever your fanout worker can sustain. At Meta, the candidate-set write rate per user is bounded by the size of the active-user pool, and a single user with more than ~5,000 friends would consume more than 1% of the total write capacity on each friend-add. That's the operational ceiling. You'd find your real number by looking at the p99 fanout-worker latency and finding the degree at which it crosses your SLO.

**Interviewer:** Privacy. A blocks B. The block is in Kafka. Lag is 3 seconds. A opens PYMK during those 3 seconds. What does A see?

**Candidate:** A should not see B. Even if the cache is warm and Kafka hasn't propagated. The serving path does an authoritative privacy check on every request. It's a single RocksDB point lookup at the head of the response builder, <1ms. If the candidate is blocked, it gets filtered out before the response is built.

**Interviewer:** Why not trust the cache?

**Candidate:** Because the cost of a privacy violation is unbounded. It's a regulatory incident, a user trust violation, and a PR event. The cost of a 1ms lookup per request is bounded and small. The trade-off is obvious.

**Interviewer:** Last question. Walk me through what happens when you ship a new prompt version.

**Candidate:** Four layers, all required. First, every prompt has a version and every trace records the version. Second, the eval set runs in CI on every PR — block the merge if Recall@8 drops, judge score drops, or hallucination rate climbs. Third, a 1% shadow canary for 24 hours before promotion. Fourth, a 7-day watch with auto-rollback on regression. The eval set is the test suite, the judge is the linter, the canary is the staging environment. Without all four, you're shipping LLM changes on hope, not measurement.

**Interviewer:** When is LLM-as-judge trustworthy enough to ship without human review?

**Candidate:** When its calibration curve is documented, its agreement with humans is measured, and its blind spots are known. Until all three, I ship changes behind a 1% canary, period. I don't trust the judge alone.

**Interviewer:** Good. Questions for me?

---

## The 5 drill-downs

The interviewer will hit one of these five. Below is what the 10/10 candidate actually says in transcript 3 — internalize the *shape*, not the script. Read each one, then close the tab and say it back in your own words. If you can say it without sounding like you're reciting, you're ready.

### 1. "How do you stop the LLM from inventing facts?"

Show the validator. Be honest about its gaps. Have a follow-up plan.

The honest answer: "It's per-claim, not whole-output. The known gap is named-entity hallucination. Here's the fix: a per-entity extractor that strips all entities from the output and verifies each one is in evidence. That's a follow-up; I haven't shipped it yet."

### 2. "A and B worked at the same company but never overlapped. Suggest them?"

Date overlap. The whole system hinges on this predicate.

```sql
SELECT a.user_id, b.user_id, a.company_id
FROM work_history a
JOIN work_history b
  ON a.company_id = b.company_id
 AND a.user_id < b.user_id
 AND a.start_date < COALESCE(b.end_date, CURRENT_DATE)
 AND b.start_date < COALESCE(a.end_date, CURRENT_DATE);
```

The principle: "Without it, the explanation 'you both worked at Meta' is technically true but semantically false. The user will lose trust after one bad suggestion."

### 3. "Late event, watermark closed, what happens?"

Reconciliation job, log it, size the worker.

The answer: "Flink reads `event_time`, not `processing_time`. The late event has `valid_from = 2026-01-14` and the as-of query for January 16th returns true. If the watermark has closed, the late event goes to a reconciliation job, not the live query path. The user sees the correct answer for the present, and we log it as 'late event' so we can size the reconciliation worker."

### 4. "Celebrity with 50M followers. Walk me through."

Push vs pull by degree threshold. Name the operational ceiling, not a magic number.

The answer: "Above a degree threshold, I switch from push to pull. The threshold is whatever the fanout worker can sustain — find it by looking at p99 fanout-worker latency and finding the degree at which it crosses your SLO. A single user with more than ~5,000 friends would consume more than 1% of total write capacity on each friend-add. That's the operational ceiling."

### 5. "Block hasn't propagated. User sees the blocked candidate. Now what?"

Authoritative serving-time check. Cost of violation is unbounded, cost of prevention is 1ms.

The answer: "The serving path does an authoritative privacy check on every request. Single RocksDB point lookup at the head of the response builder, <1ms. If the candidate is blocked, it's filtered out before the response is built. I don't trust the cache because the cost of a privacy violation is unbounded — regulatory incident, user trust violation, PR event. The cost of a 1ms lookup is bounded and small."

---

## What separates 6/10 from 10/10

Five concrete differences, each with a line citation from the transcripts above.

### 1. The validator is shown, not described

- **6/10** (L59): "I'd tell the prompt not to hallucinate." — a request, not a defense.
- **10/10** (L145-163): writes the `validate_and_serve` function, then names its known gap at L171: "this is per-claim, not whole-output... that's a follow-up; I haven't shipped that yet."

The difference: the 10/10 *runs the code in their head* and tells you what's missing. That's the **honest-gaps pattern**: state what you haven't shipped, with the next step. It's the single strongest signal that you've built the system, not read about it.

### 2. The numbers come with their derivation

- **6/10** (L67): "I'd add a timestamp to each friendship record." — no number, no schema.
- **10/10** (L175): "the watermark on the ingestion pipeline allows up to 7 days of lateness" — then at L183 names the *why*: "Kafka retention is 14 days and you want a buffer."

The difference: a 10/10 answer never gives a magic number. It gives the number *and the operational reasoning that produced it*. When the interviewer pushes on the number (L187: "Where did 5,000 come from?"), the 10/10 says "I made it up" and immediately tells you how to find the real one.

### 3. The drill-downs are answered with the underlying trade-off, not the rule

- **8/10** (L101): gives the right SQL but only after being told to.
- **10/10** (L191): "a single user with more than ~5,000 friends would consume more than 1% of the total write capacity on each friend-add. That's the operational ceiling."

The 10/10 doesn't recite the rule. They derive it from first principles: write capacity is bounded, the fanout worker has a rate, the threshold is the degree at which the rate breaks the SLO.

### 4. The cadence is concrete

Read the 6/10 transcript out loud. Notice the hedging: "or something like that" (L73), "I could add a date check" (L97), "I'd tell the prompt not to" (L59). Every sentence ends in a softener.

Now read the 10/10 transcript. Sentences are short. Numbers are specific. Each sentence is either a claim, a number, or a trade-off — never a softener. **The cadence is the signal.** It's not what you say, it's how often you hedge.

### 5. The closing line is a punchlist, not a paragraph

The 10/10 closes at L203 with nine clauses separated by periods, each one a system property:

> "Grounded, bounded, auditable. SCD2 with canonical key. Overlap-aware evidence. Deterministic claim validation. Pull-based fanout. Serving-time privacy. Eval in CI, canary before promotion, auto-rollback on regression."

Then they stop talking. The interviewer chooses the next drill-down. The punchlist works because each clause is a *noun phrase* — no verbs, no softeners, no explanation. A 6/10 closing monologue has verbs and hedges; a 10/10 closing has noun phrases and silence.

---

## How to practice

1. **Read the three transcripts out loud.** Not to memorize — to hear how the 10/10 candidate talks. Time yourself: the 10/10 transcript (L113-209) is ~12 minutes spoken. The 6/10 transcript is ~3 minutes. If your answer is closer to 3 minutes, you're not going deep enough.

2. **Practice the 5 drill-downs.** For each, set a 60-second timer and answer without looking. If you can't, the gap is in the underlying trade-off, not the script.

3. **Run the code.** The full runnable code (4 layers, SCD2 schema, work-overlap SQL, validator, celebrity fanout math) is in `cell_17_pymk.py` of the [github.com/vishnoiprem/data-etl-ml](https://github.com/vishnoiprem/data-etl-ml/tree/main/medium/meta/meta-on-site-mock) repo. It runs on a fresh laptop in 90 seconds.

4. **Read the validator out loud once.** The LLM verbalizes. The validator decides what ships. The audit log records every rejection. Three sentences, one rhythm.

The architecture gets you the interview. The validator gets you the offer.
