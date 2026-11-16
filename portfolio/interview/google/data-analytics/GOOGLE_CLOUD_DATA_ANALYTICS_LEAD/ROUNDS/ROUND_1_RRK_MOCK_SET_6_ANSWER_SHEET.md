# Mock Set 6: Spoken Answer Sheet

**Companion to** `ROUND_1_RRK_MOCK_SET_6_60MIN.md` (the full model answers) and `ROUND_1_RRK_SPOKEN_DELIVERY.md` (the notation).
**What this is:** the answers as I would actually say them, at spoken length, with pause and stop marks. Read one aloud with a timer. Every block answer is under two minutes; every probe answer is under forty seconds.

Notation: `//` short pause, `///` long pause, **bold** stress, `⏹` stop and let them probe.

> **Public repo.** No employer or customer names. *(resume)* marks a public resume figure. *Illustrative* figures must become real or be cut.

---

## Block 0: Most significant technical achievement (90 s)

The real-time logistics data platform at a large e-commerce group *(resume)*. `//` Not because of the scale `//` though it was a hundred million events a day *(resume)* through Kafka and Flink. `//` Because of what it **changed**. `///`

Before it, last-mile decisions ran on yesterday's data. `//` After it, twenty million insights a day *(resume)* reached dispatchers and routing systems `//` while the parcels were still moving. `///`

The hard part wasn't throughput. `//` It was correctness under **disorder**. `//` Driver telemetry arrives late and out of order `//` and a routing decision on a duplicate or a stale location `//` is worse than no decision. `//` So the design centred on event-time processing `//` idempotent sinks `//` and a reconciliation path. `///`

Why that one: `//` it's where I learned that a platform's value is measured at the point of **decision** `//` not the point of storage. `//` ⏹

**"Differently now?"** Start the operating model earlier. `//` The platform was live two quarters before the dispatch teams owned their own metrics. `//` That gap is where adoption stalls. ⏹

---

## Block 1: Resume probes (each under 60 s)

### "10B+ rows daily. Ingested, processed, or scanned?"
Processed through the medallion layers per day `//` counted from job metrics. `//` Ingested alone is lower `//` about [2 to 3 billion, *illustrative*]. `//` The multiplier is the transformation layers. `//` I'd rather you hear the decomposition than the headline. ⏹

### "What broke at that scale?"
Small files and skew. `//` Point-of-sale arrives as hundreds of thousands of small files a day `//` and without compaction the metadata layer slowed every query. `//` The largest stores skewed joins by an order of magnitude. `//` Fixes: scheduled compaction `//` partitioning by date and store band `//` salting the hot keys. `///` The lesson: at scale `//` the file layout **is** the architecture. ⏹

### "What did it cost?"
Three million *(resume)* across platform, licences and team. `//` The biggest lever: separating always-on from burst. `//` Scheduled jobs on committed capacity `//` ad hoc on autoscaling with limits. `//` [Cost per processed row down about 30% in a year, *illustrative*.] `//` The weekly number: cost per domain per day `//` with an owner for each. ⏹

### "Five days to two hours of what?"
Last ledger posting to finance signing off the consolidated pack. `//` Five days was their average over the prior year. `//` Two hours is the median since go-live `//` pipeline completion timestamp to sign-off in the workflow tool. ⏹

### "That's a finance process change. What was your part?"
Fair `//` both are true. `//` Three platform decisions made it possible: `//` reconciliation **inside** the pipeline, so differences surfaced at load `//` finance owning the definitions in one semantic layer `//` and a publish gate, so a pack couldn't be built from incomplete data. `///` My team built it. `//` Those calls were mine. ⏹

### "What went wrong?"
First month-end on the new platform `//` a currency table was a day stale `//` two subsidiaries were off. `//` Dual-run caught it before sign-off. `//` We added freshness checks on every reference table that day. `///` I'd have had that from the start if I'd listed reference data as a failure mode. `//` Now I do. ⏹

### "Chat-with-data. Did people use it?"
Yes `//` and not uniformly. `//` [About 150 weekly actives after six months, in two functions; a third stalled, *illustrative*.] `//` The adopters had a governed semantic layer. `//` The one that stalled had three definitions of the same metric `//` and the assistant **exposed** that rather than caused it. ⏹

### "How did you know the answers were right?"
A golden question set `//` [about 300, *illustrative*] `//` run on every prompt or model change `//` exact match on numbers. `//` Below threshold, it didn't ship. `//` Every generated query logged and sampled weekly. `//` Guardrails: the model saw only the semantic layer `//` row-level security on the **user's** identity `//` personal data blocked at the query layer. ⏹

### "What wouldn't you do again?"
Launch to a function whose metrics weren't governed yet. `//` We spent a quarter being blamed for inconsistencies that were already there. `//` The readiness gate now: `//` one definition per metric `//` first. ⏹

---

## Block 2: Customer 360 under PDPA (2 min)

Restating: `//` one governed identity per real person `//` across online and offline `//` good enough for segmentation and activation `//` with consent respected. `///` Two questions: `//` what share of in-store transactions carry any identifier? `//` And what's the activation path? `//` Unanswered, I'll assume about half of in-store is identifiable `//` and activation is a marketing platform plus the app. `///`

Three ways to match. `//` **Deterministic only**: exact on loyalty ID, email, phone. High precision, low coverage. `//` **Probabilistic**: name, address, device, payment token, with a score. More coverage, false merges need governance. `//` **Both, in order**: deterministic first, probabilistic second, with a reviewable confidence band. `//` I recommend the third `//` **because** a false merge in marketing is embarrassing `//` and a false merge under a data-subject request is a breach. `///`

Left to right. `//` Sources land raw and immutable in BigQuery. `//` Standardisation: phone formats, email casing, address parsing, hashed payment tokens `//` consent flags as first-class columns. `//` Identity resolution as a batch graph: deterministic links, then probabilistic scores `//` above the high threshold auto-merge `//` in the band, flag for review `//` below, stay separate. `//` Output: a persistent customer key **and a link table** `//` every source identifier and the reason for each link `//` so a merge is reversible. `//` On top: the profile, segments, feature tables `//` reverse-ETL to marketing, a low-latency store for the app. `//` Governance: policy tags on every personal column `//` a consent-aware view so marketing sees only opt-ins `//` erasure that walks the link table to every source `//` regional dataset. `///`

The failure that matters: `//` two people in one household sharing a phone. `//` Never merge on one soft attribute `//` require two independent signals `//` keep it reversible. `///`

Marketing owns segment definitions. `//` Data owns the graph. `//` Legal owns consent rules, encoded, not interpreted. `//` Measure: match rate by source `//` false-merge rate from the review sample `//` activation lift against control `//` time to fulfil erasure. ⏹

**"Setting the threshold?"** Hand-label a few thousand pairs `//` plot precision against recall `//` choose the high threshold at the precision marketing and legal accept `//` review band below. `//` Re-label quarterly. ⏹

**"Marketing wants it tomorrow, legal wants six months."** Ship deterministic-only for opted-in customers now `//` legal approves fast because nothing is inferred. `//` Run probabilistic in shadow with a review sample `//` until legal has seen its error rate. `//` Marketing gets reach that grows. `//` Legal gets evidence. ⏹

---

## Block 3: Hands-on (narrate the shape before writing)

### SQL 1: latest live state per order
"Rank per order by recency `//` keep the top `//` drop orders whose latest event is a delete. `//` Ties by log position. `//` Partition filter so it doesn't scan history."

```sql
SELECT order_id, status, amount, updated_at
FROM `raw.orders_changes`
WHERE DATE(updated_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 400 DAY)
QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id
                           ORDER BY updated_at DESC, log_pos DESC) = 1
  AND op <> 'D';
```

"Tests: three updates `//` delete last `//` delete then reinsert `//` identical timestamps." ⏹

### SQL 2: sessionisation
"Gap and island. `//` LAG for the gap `//` flag when null or over thirty `//` running sum gives the session number `//` aggregate."

```sql
WITH gaps AS (
  SELECT user_id, event_ts,
         TIMESTAMP_DIFF(event_ts,
           LAG(event_ts) OVER (PARTITION BY user_id ORDER BY event_ts), MINUTE) AS mins_since_prev
  FROM `app.events`),
flagged AS (
  SELECT user_id, event_ts,
         IF(mins_since_prev IS NULL OR mins_since_prev > 30, 1, 0) AS new_session
  FROM gaps),
sessions AS (
  SELECT user_id, event_ts,
         SUM(new_session) OVER (PARTITION BY user_id ORDER BY event_ts) AS session_no
  FROM flagged),
per_session AS (
  SELECT user_id, session_no,
         TIMESTAMP_DIFF(MAX(event_ts), MIN(event_ts), MINUTE) AS session_mins
  FROM sessions GROUP BY user_id, session_no)
SELECT user_id, COUNT(*) AS sessions, AVG(session_mins) AS avg_session_mins
FROM per_session GROUP BY user_id;
```

"Edge cases: a single-event session is zero minutes, I'd confirm that's wanted `//` exactly thirty minutes stays in one session, strict versus inclusive, I'd ask. `//` Partitioned by user, so it scales. `//` The risk is a hot user." ⏹

**"A bot with fifty million events?"** One partition does all the work `//` and the query stalls on one slot. `//` Cap or exclude users above a plausible count in a first pass `//` analyse them separately. ⏹

### Python: latest version per key, out-of-order stream, O(n), no list
"One pass `//` dict by id `//` replace only on a strictly higher version `//` so an exact duplicate is a no-op. `//` That's the idempotency property."

```python
def latest_by_key(events):
    latest, skipped = {}, 0
    for e in events:
        try:
            key, ver = e["id"], int(e["version"])
        except (KeyError, TypeError, ValueError):
            skipped += 1          # metric + dead-letter in production
            continue
        cur = latest.get(key)
        if cur is None or ver > cur["version"]:
            latest[key] = e
    return latest
```

"Malformed events are counted and skipped, not raised `//` one bad record shouldn't kill a batch. `//` Memory is bounded by distinct ids. `//` If the id space doesn't fit, same logic as keyed state in Dataflow or a MERGE in BigQuery." ⏹

**"Same version, different payloads?"** A producer bug. `//` Detect, count, dead-letter both. `//` Guessing is how you get a confident wrong answer. ⏹

---

## Block 4: Consulting

### "GenAI across the business" in six months, eleven systems, text-to-SQL first (2 min)
I'd agree with the ambition `//` and separate it from the first deliverable. `///` Text-to-SQL over eleven ungoverned systems gives confident, inconsistent answers `//` and the first time it hands the CFO two revenue numbers `//` the programme loses the board. `//` I've seen exactly that. `///`

Three options. `//` Build over raw now: fast demo, slow disaster. `//` Six months of foundation first: right, but the date passes with nothing visible. `//` **Or**: pick one domain where a GenAI outcome matters `//` govern its twenty most-used metrics in a semantic layer in eight weeks `//` launch the assistant over that domain only `//` foundation continuing behind it. `//` I recommend the third `//` **because** the board sees a working assistant by month three `//` on numbers that are right `//` and every further domain repeats the pattern. `///`

Before any launch: `//` the model sees only the semantic layer `//` row-level security on the user `//` a golden question set with a pass threshold `//` every query logged and sampled `//` personal data blocked at the query layer `//` a human owner per metric. `///`

To the CEO directly: `//` six months is achievable for one domain done properly `//` not eleven systems done badly `//` and the second is the one that ends careers. ⏹

### The twelve-year architect wants raw tables (60 s)
Take it seriously in front of their team `//` twelve years means they know things I don't. `//` Then separate the two claims. `//` "Slows everything down" is testable: `//` measure latency both ways on their top twenty questions. `//` "Raw directly" is a correctness and security claim `//` and there I hold the line with evidence, not seniority: `//` show the three definitions of margin in their raw tables `//` and ask which one the CEO should get. `///` Offer a path that respects them: `//` the semantic layer is the governed path `//` analysts who need raw keep their access. `//` If we still disagree, it's a sponsor decision with both positions written fairly `//` and I commit fully either way. `///` I won't win the argument and lose the architect. `//` We need them for the next five years. ⏹

---

## Block 5: Practice and leadership

### A decision with the three-million budget (90 s, *shape, fill privately*)
The decision: [committed-spend licence versus pay-as-you-go, *illustrative*]. `//` The trade-off: commitment bought [about a 25% lower unit rate] `//` and risked paying for capacity we didn't use. `///` I modelled it from twelve months of **actual** usage `//` not the vendor's projection `//` sized the commitment to the steady floor, about [70%] of average `//` kept burst on demand. `//` And used the negotiation for [enablement credits and a dedicated architect] `//` which mattered more to the team than the rate. `///` Result: [unit cost down, under-utilisation never above 5%]. `//` Differently: `//` I committed for a year. `//` Eighteen months would have got a better rate `//` and the usage was predictable enough to take it. ⏹

### Fifty-plus dashboards. How many were used? (60 s)
Fewer than fifty `//` and I'd rather tell you that than pretend. `//` [After a year, about thirty had weekly executive use `//` a dozen monthly `//` the rest retired, *illustrative*.] `//` We measured weekly active viewers per dashboard `//` reviewed quarterly `//` anything with no executive views in a quarter went to its owner and was retired if nobody objected. `///` It changed intake: `//` no dashboard without a named decision `//` and a named owner who'll be asked in a quarter whether it worked. `///` The number I'm proud of isn't fifty. `//` It's that the ones left are the ones the executive team opens on Monday morning. ⏹

**"Philosophy on adoption?"** Adoption is a deliverable, not a hope. `//` Named user, named decision, usage metric, before we build. `//` If I can't name the user `//` I don't build it. ⏹

---

## Block 6: "Why you over five years of GCP?" (75 s)

If the job were operating BigQuery `//` hire them. `///` The job is leading the largest data and AI programmes in the region `//` for enterprises mostly not on Google Cloud yet `//` and getting them there without breaking their businesses. `//` That's three skills. `//` Knowing what breaks in enterprise platforms at scale `//` learned across three clouds and fifteen years. `//` Leading senior architects and a thirty-person organisation *(resume)* through transformation. `//` And sitting across from a CFO `//` and being believed. `///` The platform specifics I close in two quarters `//` certification in the first `//` I've made that move twice. `//` The other three take fifteen years `//` and I bring them on day one. `///` And I'd want that five-year GCP engineer on my team. `//` I don't need to be the best BigQuery operator in the room. `//` I need to make sure the room delivers. ⏹

**Questions to ask:** "Which of my resume claims did you find least convincing `//` and what would convince you?" `///` "What does the practice's best architect do that the others don't?"

---

## Timing check

| Block | Target | Words here |
|---|---|---|
| 0 | 90 s | ~190 |
| 1, each probe | 40-60 s | 60-110 |
| 2 | 2 min | ~330, cut the governance list if running long |
| 4 Q1 | 2 min | ~260 |
| 4 Q2 | 60 s | ~150 |
| 5 Q1 | 90 s | ~170 |
| 5 Q2 | 60 s | ~150 |
| 6 | 75 s | ~170 |

Record each one. Listen only for: fillers, numbers said without a pause, and whether you stopped at `⏹` or kept going.
