# RRK Mock Set 6: Resume Under Fire, Hands-On SQL and Python, Home-Turf Designs

**Role:** Data & Analytics Lead, Google Cloud Consulting (Singapore)
**Format:** one timed interview. This interviewer has your resume open and probes its claims line by line, then makes you write SQL and Python rather than review it, then asks you to design the two things you've actually built: a customer 360 and a chat-with-data platform.
**Why a sixth set:** Sets 1 to 5 review code but never ask you to write it; the brief says "brush up on hands-on SQL and Python". None of them rehearses defending a resume number under three levels of probing, which is how a behavioural RRK actually goes. And none uses your strongest designs.
**How to use:** 60-minute timer. For Block 3, write the SQL and Python by hand or in a scratch editor before reading the solutions.

> **Public repo.** No employer or customer names. Figures marked *(resume)* are on the public resume. Figures in an *illustrative* line are placeholders with the right shape: make them real or cut them.

| Min | Block | Type | Topic |
|---|---|---|---|
| 0-3 | 0 | Opening | Most significant technical achievement |
| 3-14 | 1 | Behavioural | Three resume claims probed three levels deep |
| 14-26 | 2 | Technical | Customer 360 and identity resolution across online and offline |
| 26-41 | 3 | Hands-on | Write two SQL queries and one Python function, narrating |
| 41-49 | 4 | Consulting | "GenAI everywhere" with no data foundation; a customer architect who disagrees |
| 49-55 | 5 | Practice | A budget decision you owned; dashboards nobody uses |
| 55-60 | 6 | Close | "Why you over someone with five years of GCP?" |

---

## Block 0 (0-3 min): Opening

**Q:** "What's your most significant technical achievement, and why that one?"

**Model answer**
> "The real-time logistics data platform at a large e-commerce group *(resume)*. Not because of the scale, though it was a hundred million events a day *(resume)* through Kafka and Flink into ClickHouse and HBase *(resume)*. Because of what it changed. `///` Before it, last-mile decisions were made on yesterday's data. After it, twenty million insights a day *(resume)* reached dispatchers and routing systems while the parcels were still moving. `///` The hard part wasn't the throughput. It was correctness under disorder: driver telemetry arrives late and out of order, and a routing decision made on a duplicate or a stale location is worse than no decision. So the design centred on event-time processing, idempotent sinks and a reconciliation path, and I'd defend every one of those choices today. `///` Why that one: it's the project where I learned that a data platform's value is measured at the point of decision, not at the point of storage. Everything I've built since starts from that."

**Follow-up:** "What would you do differently now?" → "Start the operating model earlier. The platform was live for two quarters before the dispatch teams owned their own metrics. That gap is where adoption stalls."

---

## Block 1 (3-14 min): Behavioural, resume under fire

The interviewer picks three lines from your resume and goes three levels deep on each. The skill is the same every time: **state the number, give the baseline and the method, name your part, admit the edge.** Never inflate when pushed; shrink to what you can defend.

### Claim 1: "Databricks lakehouse processing 10B+ rows daily"

**Level 1:** "What does 10 billion rows a day actually mean? Ingested, processed, scanned?"
> "Rows processed through the medallion layers per day across finance, supply chain, retail and e-commerce *(resume)*: raw ingestion plus the bronze-to-silver-to-gold transformations, counted from job metrics. Ingested alone is lower, about [illustrative: 2 to 3 billion]; the multiplier is the transformation layers. I'd rather you hear the honest decomposition than the headline."

**Level 2:** "What broke at that scale?"
> "Small files and skew, mostly. Point-of-sale data arrives in hundreds of thousands of small files a day; without compaction the metadata layer slowed every query. And the largest stores skewed joins by an order of magnitude. Fixes: scheduled compaction, partitioning by date and store band rather than store, and salting the hot keys in the heaviest joins. The lesson I carry: at scale, the file layout *is* the architecture."

**Level 3:** "What's the cost of running that, and what did you do about it?"
> "Budget of three million *(resume)* across platform, licences and the team. The biggest lever was separating always-on from burst: scheduled jobs on committed capacity, ad-hoc on autoscaling with limits. [Illustrative: compute cost per processed row fell about 30% in the year.] The number I watched weekly was cost per domain per day, with a named owner for each."

### Claim 2: "Month-end financial close from 5 days to 2 hours"

**Level 1:** "Five days to two hours of what, exactly?"
> "The time from the last ledger posting to finance signing off the consolidated close pack. Five days was the finance team's historical average over the previous year; two hours is the median since go-live, measured from the pipeline's completion timestamp to the sign-off in the workflow tool."

**Level 2:** "That's a finance process change, not a data change. What was your part?"
> "Fair, and both are true. The finance team changed their process; what made it possible was three platform decisions I made: reconciliation inside the pipeline so differences surfaced at load, not at review; finance owning the metric definitions in one semantic layer; and a publish gate so a pack couldn't be produced from incomplete data. My team built it. Those calls were mine."

**Level 3:** "What went wrong along the way?"
> "The first month-end on the new platform, a currency-rate table was a day stale and two subsidiaries' numbers were off. Dual-run caught it before sign-off. We added a freshness check on every reference table that day. I'd have had that check from the start if I'd listed reference data as a failure mode, and now I do."

### Claim 3: "Chat-with-Data, Text-to-SQL GenAI platform, rollout to non-technical teams"

**Level 1:** "Did people actually use it?"
> "Yes, and not uniformly. [Illustrative: about 150 weekly active users after six months, concentrated in two business functions; adoption in a third function stalled.] The ones who adopted had a semantic layer we'd already governed; the one that stalled had three definitions of the same metric, and the assistant exposed that rather than caused it."

**Level 2:** "How did you know the answers were right?"
> "A golden question set, [illustrative: around 300 questions] with known answers, run on every prompt or model change, scored on exact-match for numbers and on a rubric for narrative. Below a threshold, the change didn't ship. In production, every generated query was logged with the result, and a sample was reviewed weekly by the data team. Guardrails: the model only saw the semantic layer, never raw tables; row-level security applied to the user's identity, not the service account; and anything touching personal data was blocked at the query layer."

**Level 3:** "What would you not do again?"
> "Launch to a function whose metrics weren't governed yet. We spent a quarter being blamed for inconsistencies that were already there. Now the readiness gate is: one definition per metric, before the assistant gets access."

**Rules for this block:** every answer under 60 seconds; shrink the claim before they make you; "my team built it, these calls were mine"; one honest miss per claim.

---

## Block 2 (14-26 min): Technical, customer 360 and identity resolution

**Q:** "A retail group has loyalty data, e-commerce accounts, app events and in-store transactions, many without a loyalty card. They want one view of the customer for segmentation and marketing activation, under PDPA. Design it."

**Model answer**
> "**Restate:** one governed identity per real person across online and offline, good enough for segmentation and activation, with consent respected. Two questions: what share of in-store transactions carry any identifier at all, card, phone, e-receipt? And what's the activation path, marketing platforms, in-store, app? If unanswered, I'll assume about half of in-store is identifiable and activation is through a marketing platform and the app.
>
> **Options for matching.** A: deterministic only, exact matches on loyalty ID, email, phone. High precision, low coverage; a large share of customers stay fragmented. B: probabilistic matching across name, address, device, payment token, with a score threshold. Higher coverage, needs governance of false merges. C: **deterministic first, probabilistic second, with a human-reviewable confidence band.** Recommend C. A false merge in marketing is embarrassing; a false merge under a data-subject request is a breach.
>
> **Draw it.** Sources land raw and immutable in BigQuery: loyalty, e-commerce, app events via streaming, POS by store feed. Standardisation: phone formats, email casing, address parsing, hashed payment tokens, with consent flags carried as first-class columns from the source. Identity resolution runs as a batch graph: deterministic links first, then probabilistic scoring for the remainder; above the high threshold auto-merge, in the band flag for review, below leave separate. Output is a persistent customer key with a link table that keeps every source identifier and the reason for each link, so a merge is reversible. On top: the 360 profile table, segment tables and feature tables for the propensity models, served to the marketing platform by a reverse-ETL job and to the app by a low-latency store. Governance: policy tags on every personal column, a consent-aware view layer so marketing only sees opted-in customers, erasure that walks the link table to every source, and a regional dataset.
>
> **Failure path.** The false merge: two people in one household sharing a phone. Prevention: never merge on a single soft attribute, require two independent signals, and keep the merge reversible via the link table. Detection: a monitor on merge-rate anomalies and a sample review each week.
>
> **Operating model.** Marketing owns the segment definitions. The data team owns the identity graph and its quality. Legal owns the consent rules, encoded, not interpreted. **Measure:** match rate by source, false-merge rate from the review sample, segment reach, activation lift against control, and time to fulfil an erasure request."

**Follow-up A:** "How do you set the probabilistic threshold?" → "Label a sample by hand, a few thousand pairs, plot precision against recall across thresholds, and choose the high threshold at the precision marketing and legal accept, typically very high, with the review band below it. Re-label quarterly because the population drifts."

**Follow-up B:** "Marketing wants to use it tomorrow. Legal wants six months of review." → "Both are right about something. Ship the deterministic-only graph for opted-in customers now, which legal can approve quickly because nothing is inferred, and run the probabilistic layer in shadow with a review sample until legal has seen its error rate. Marketing gets reach that grows; legal gets evidence."

---

## Block 3 (26-41 min): Hands-on SQL and Python

Narrate as you write: say the shape of the answer before the first line, name the edge case you're handling, and say what you'd test.

### 3a. SQL 1 (5 min): latest state per order, deletes removed

Table `raw.orders_changes(order_id STRING, op STRING, status STRING, amount NUMERIC, updated_at TIMESTAMP, log_pos INT64)`. `op` is `I`, `U` or `D`. Return the current state of every live order. Ties on `updated_at` are broken by `log_pos`.

**Solution**
```sql
WITH ranked AS (
  SELECT
    order_id, op, status, amount, updated_at,
    ROW_NUMBER() OVER (
      PARTITION BY order_id
      ORDER BY updated_at DESC, log_pos DESC
    ) AS rn
  FROM `raw.orders_changes`
  WHERE DATE(updated_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 400 DAY)  -- partition prune
)
SELECT order_id, status, amount, updated_at
FROM ranked
WHERE rn = 1
  AND op <> 'D';
```

**Narration:** "Shape: rank changes per order by recency, keep the top one, then drop orders whose latest event is a delete. The edge cases: ties, handled by log position; and an order that was deleted and then re-inserted, which this handles correctly because the latest event wins. I filter on the partition column so this doesn't scan history. I'd test with: one order with three updates, one with a delete last, one deleted then re-inserted, and two events with identical timestamps."

**Follow-up:** "Rewrite it with QUALIFY." →
```sql
SELECT order_id, status, amount, updated_at
FROM `raw.orders_changes`
WHERE DATE(updated_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 400 DAY)
QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC, log_pos DESC) = 1
  AND op <> 'D';
```

### 3b. SQL 2 (5 min): sessionisation

Table `app.events(user_id STRING, event_ts TIMESTAMP, page STRING)`. A session ends after 30 minutes of inactivity. Return, per user, the number of sessions and the average session length in minutes.

**Solution**
```sql
WITH gaps AS (
  SELECT
    user_id, event_ts,
    TIMESTAMP_DIFF(
      event_ts,
      LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts),
      MINUTE
    ) AS mins_since_prev
  FROM `app.events`
),
flagged AS (
  SELECT
    user_id, event_ts,
    IF(mins_since_prev IS NULL OR mins_since_prev > 30, 1, 0) AS new_session
  FROM gaps
),
sessions AS (
  SELECT
    user_id, event_ts,
    SUM(new_session) OVER (PARTITION BY user_id ORDER BY event_ts) AS session_no
  FROM flagged
),
per_session AS (
  SELECT
    user_id, session_no,
    TIMESTAMP_DIFF(MAX(event_ts), MIN(event_ts), MINUTE) AS session_mins
  FROM sessions
  GROUP BY user_id, session_no
)
SELECT
  user_id,
  COUNT(*)          AS sessions,
  AVG(session_mins) AS avg_session_mins
FROM per_session
GROUP BY user_id;
```

**Narration:** "Classic gap-and-island. Four steps: compute the gap from the previous event with LAG; flag a new session when the gap is null or over 30; running sum of the flags gives a session number; aggregate. Edge cases: a single-event session has length zero, which is correct but I'd confirm the business wants that; a user with events exactly 30 minutes apart stays in one session, which depends on the strict versus inclusive definition, so I'd ask. On ten billion events this runs fine because every window is partitioned by user; the thing to watch is a hot user, like a bot, skewing one partition."

**Follow-up:** "A bot user has 50 million events. What happens?" → "One partition does all the work and the query stalls on one slot. I'd cap or exclude users above a plausible event count in a first pass, and treat them as a separate analysis."

### 3c. Python (5 min): latest version per key from an out-of-order stream

Write `latest_by_key(events)` where `events` is an iterable of dicts `{"id": str, "version": int, "payload": dict}`, arriving out of order with duplicates. Return a dict of `id` to the event with the highest version. Must be O(n) and must not load the iterable into a list.

**Solution**
```python
from typing import Iterable, Dict, Any

Event = Dict[str, Any]

def latest_by_key(events: Iterable[Event]) -> Dict[str, Event]:
    """Keep the highest-version event per id.

    Streams the input once; O(n) time, O(distinct ids) memory.
    Equal versions are treated as duplicates and the first seen is kept.
    Events missing 'id' or 'version' are skipped and counted, not raised.
    """
    latest: Dict[str, Event] = {}
    skipped = 0
    for e in events:
        try:
            key, ver = e["id"], int(e["version"])
        except (KeyError, TypeError, ValueError):
            skipped += 1
            continue
        current = latest.get(key)
        if current is None or ver > current["version"]:
            latest[key] = e
    if skipped:
        # in production this is a metric and a dead-letter write, not a print
        print(f"skipped {skipped} malformed events")
    return latest
```

**Narration:** "One pass, a dict keyed by id, replace only on a strictly higher version. Strict comparison means an exact duplicate is a no-op, which is the idempotency property. Malformed events are skipped and counted rather than raising, because one bad record shouldn't kill a batch; in production the count is a metric and the record goes to a dead-letter table. Memory is bounded by distinct ids, not by events. Tests: out-of-order versions, exact duplicate, missing field, version as a string. If the id space itself doesn't fit in memory, this becomes a keyed stateful operation in Dataflow or a MERGE in BigQuery, same logic, different engine."

**Follow-up:** "What if two events have the same version but different payloads?" → "That's a producer bug, not something I'd resolve silently. I'd detect it, count it, and route both to a dead-letter path for the producer to fix. Guessing which is right is how you get a confident wrong answer."

---

## Block 4 (41-49 min): Consulting

**Q1:** "A CEO has told the board they'll have 'GenAI across the business' in six months. Their data is in eleven systems with no common definitions. The CIO asks you for a text-to-SQL assistant as the first deliverable. What do you say?"

**Model answer**
> "I'd start by agreeing with the ambition and separating it from the first deliverable. `///` A text-to-SQL assistant over eleven systems with no common definitions will give confident, inconsistent answers, and the first time it tells the CFO two different revenue numbers, the GenAI programme loses the board. I've seen exactly that happen *(the Block 1 chat-with-data story)*. So I'd say: the assistant is the right second step, and here's the first.
>
> **Options.** A: build the assistant now over the raw systems; fast demo, slow disaster. B: spend six months on a data foundation first; right, but the CEO's date passes with nothing visible. C: **pick one business domain where a GenAI outcome matters, govern its twenty most-used metrics in a semantic layer in eight weeks, and launch the assistant over that domain only, with the foundation work continuing behind it.** Recommend C. The board sees a working assistant by month three, on numbers that are right, and every further domain is a repeat of the pattern.
>
> **The guardrails I'd insist on before any launch:** the model sees only the semantic layer; row-level security on the user's identity; a golden question set with a pass threshold; every query logged and sampled for review; personal data blocked at the query layer; and a human owner for every metric it can answer about.
>
> **What I'd tell the CEO directly:** the six-month promise is achievable for one domain done properly, not eleven systems done badly, and the second is the one that ends careers. **Measure:** weekly active users, answer accuracy against the golden set, and the count of 'which number is right' escalations, which should be near zero."

**Q2:** "The customer's lead architect disagrees with you. They want the assistant to query raw tables directly, because the semantic layer 'slows everything down'. They've been there twelve years. How do you handle it?"
> "First, take the objection seriously in front of their team; twelve years means they know things I don't. Then separate the two claims. 'Slows everything down' is testable: I'd propose we measure latency both ways on their top twenty questions. 'Query raw directly' is a correctness and security claim, and there I'd hold the line with evidence, not seniority: show the three definitions of margin in their raw tables and ask which one the CEO should get. Then offer a path that respects their concern: the semantic layer is the governed path, and for the analysts who need raw, that stays available with their existing access. If we still disagree, I'd name it as a decision for the sponsor, with both positions written down fairly, and I'd commit fully to whichever they choose. What I wouldn't do is win the argument and lose the architect; we need them for the next five years of this."

---

## Block 5 (49-55 min): Practice and leadership

**Q1:** "You've owned a three-million-dollar budget *(resume)*. Walk me through one decision you made with it, with the trade-off."

**Model answer (fill privately; this is the shape)**
> "The decision: [illustrative: renewing the platform licence on a committed-spend contract versus staying pay-as-you-go]. The trade-off: commitment bought [illustrative: a 25% lower unit rate] and risked paying for capacity we didn't use. I modelled it from twelve months of actual usage, not the vendor's projection, sized the commitment to the steady floor, about [illustrative: 70%] of average usage, and kept the burst on demand. I also used the negotiation to get [illustrative: enablement credits and a dedicated architect], which mattered more to the team than the rate. The result: [illustrative: unit cost down, under-utilisation never above 5%]. What I'd do differently: I committed for a year; eighteen months would have been a better rate and the usage was predictable enough to take it."

**Q2:** "You delivered fifty-plus executive dashboards *(resume)*. How many were actually used?"
> "Fewer than fifty, and I'd rather tell you that than pretend. [Illustrative: after a year, about 30 had weekly executive use; a dozen were used monthly; the rest were retired.] We measured it: weekly active viewers per dashboard, reviewed quarterly, and anything with no executive views in a quarter was flagged to its owner and retired if nobody objected. The lesson changed how we take requests: no dashboard without a named decision it supports and a named owner who'll be asked in a quarter whether it did. The number I'm actually proud of isn't fifty; it's that the ones left are the ones the executive team opens on Monday morning."

**Follow-up:** "What's your philosophy on adoption?" → "Adoption is a deliverable, not a hope. Every data product has a named user, a decision it serves and a usage metric, before we build it. If I can't name the user, I don't build it."

---

## Block 6 (55-60 min): Close

**Q:** "Why should we hire you over someone with five years of Google Cloud production experience?"
> "If the job were operating BigQuery, you should hire them. `///` The job is leading the largest data and AI programmes in the region for enterprises who are mostly not on Google Cloud yet, and getting them there without breaking their businesses. That's three skills: knowing what breaks in enterprise data platforms at scale, which I've learned across three clouds and fifteen years; leading senior architects and a thirty-person organisation through transformation; and sitting across from a CFO and being believed. `///` The platform specifics I close in two quarters, with certification in the first; I've done that move twice before. The other three take fifteen years, and I'm bringing them on day one. `///` And I'd want that five-year GCP engineer on my team. That's the player-coach model: I don't need to be the best BigQuery operator in the room; I need to be the person who makes sure the room delivers."

**Your questions (pick two)**
1. "Which resume claim of mine did you find least convincing, and what would convince you?"
2. "What does the practice's best architect do that the others don't?"
3. "If I'm successful, what will the first customer I work with need most from me?"

---

## Scoring (0 to 2 per line, 8 per block, 48 total for blocks 0 to 5)

| Line | 0 | 1 | 2 |
|---|---|---|---|
| Structure | Jumped to a solution | Some clarifying | Restated, clarified, stated assumptions, then options |
| Judgement | Component list or "it depends" | Options, weak pick | 2 to 3 options, trade-offs, a clear recommendation |
| Evidence and numbers | Vague | Some figures | Defensible numbers with baseline, method and your role |
| Enterprise scope | Single project | Mentions operations | Ownership, adoption, rollback, decommission, cost |

**Block 3 is scored differently:** 2 for a correct query or function, 2 for narrating the shape before writing, 2 for naming edge cases and tests unprompted, 2 for the scale follow-up.

**Targets:** 36 or more of 48 is ready. 27 to 35: repeat the weakest two blocks. Under 27: restudy `ROUND_1_RRK_TOPIC_DEEP_DIVE.md` first.

**Hard fails for this round:** inflating a resume number when probed; SQL without a partition filter or without handling ties; Python that loads the iterable into a list; agreeing to text-to-SQL over raw tables; claiming all fifty dashboards were used.
