# Lesson 7 — Quiz: Feature Stores & ML Data Infrastructure

> **Type:** Quiz · Module 6 · Feature Stores & ML Data Infrastructure
> Self-check on the seven lessons. Answers at the bottom.

---

## Section A — Conceptual

**Q1.** The training/serving skew problem is caused by:
- A) Different hardware between training and serving
- B) Features computed differently in the offline and online paths
- C) The model being too old
- D) Insufficient training data

**Q2.** A feature store's offline store is optimised for:
- A) Sub-50ms reads
- B) Point-in-time correct historical data
- C) Random access by entity_id
- D) Streaming writes

**Q3.** Point-in-time joins exist primarily to prevent:
- A) Schema drift
- B) Future information leaking into the past in training data
- C) Slow training
- D) Feature redundancy

**Q4.** A "champion-challenger" deployment means:
- A) Two models, one in shadow mode for backup
- B) Two models receiving parallel traffic, compared on outcomes
- C) One model with two versions, A/B tested weekly
- D) Two models, one for offline one for online

**Q5.** The most expensive feature store tier (per request, per feature) is roughly:
- A) Open-source Feast
- B) Tecton (managed)
- C) Cloud built-ins (AWS/GCP/Azure)
- D) They are roughly the same cost

**Q6.** Population Stability Index (PSI) > 0.25 typically means:
- A) Distribution is stable, no action
- B) Small shift, watch
- C) Significant drift, retrain
- D) Test set is contaminated

**Q7.** The cleanest fix for prompt injection in production is:
- A) Harder system prompt
- B) Smaller LLM
- C) Adversarial eval set + output filtering, run on every PR
- D) Removing the system prompt

**Q8.** The "silent feature regression" trap refers to:
- A) Feature store going down
- B) A feature's values changing scale/meaning without schema change, breaking the model silently
- C) Feature engineering taking too long
- D) Failure to retrain

---

## Section B — Scenario

**Q9.** You are deploying an LLM-based customer-support bot. List 6 things you must version and 4 things you must monitor.

**Q10.** A recommender model has been in production 6 months. The team wants to retrain. What do they need to ensure reproducibility?

**Q11.** Your online feature store is showing p95 latency of 200ms, far above the 50ms SLA. List 4 diagnostic steps.

**Q12.** A stakeholder says: "Can't we skip the feature store and just give the model a SQL query?" Reply in 3 points.

---

## Section C — Practical

**Q13.** Write the feature definition (Feast or Tecton style) for `user_avg_session_duration_30d`. Include entity, TTL, freshness SLA, owner.

**Q14.** Sketch the architecture for serving a fraud-detection model with online features where freshness SLA = 5 seconds.

**Q15.** Describe the eval set design for a chatbot over policy docs: how many queries, what categories, what adversarial coverage?

---

## Section D — Open

**Q16.** Pick a real or imagined incident where a feature store broke (drift, skew, outage). What was the user impact? How did you detect? What was the fix?

---

## Answer Key

<details>
<summary>A1</summary>

**B** — Different feature logic in offline vs online paths is the classic source of skew. The model trains on one set of values and serves on another.
</details>

<details>
<summary>A2</summary>

**B** — Offline store is for training data; point-in-time correctness and bulk reads are its job. Sub-50ms reads is the online store.
</details>

<details>
<summary>A3</summary>

**B** — Without point-in-time joins, training data includes future feature values, inflating metrics and producing models that look great offline and fail online.
</details>

<details>
<summary>A4</summary>

**B** — Champion is the production model; challenger gets parallel traffic in shadow / canary / A/B; you promote only when challenger beats champion on guardrails.
</details>

<details>
<summary>A5</summary>

**B** — Tecton is roughly 3–10× the cost of self-hosted or cloud built-ins. You pay for managed governance and operations.
</details>

<details>
<summary>A6</summary>

**C** — PSI > 0.25 is the standard threshold for "significant drift, retrain." < 0.1 is stable, 0.1–0.25 is small shift.
</details>

<details>
<summary>A7</summary>

**C** — Adversarial eval (must-pass injection set on every PR) plus output filtering. Harder prompts alone are not reliable.
</details>

<details>
<summary>A8</summary>

**B** — A feature's *values* changed (scale, semantics) without a schema change, so the model silently degrades. The fix is per-feature distribution monitoring.
</details>

<details>
<summary>A9</summary>

A model answer:

**Must version:**
1. Prompt (system + user + few-shots)
2. RAG config (chunk size, embedding model, top-k, reranker threshold)
3. Knowledge base snapshot (versioned like code)
4. Tool schemas
5. Routing logic (which LLM for which query type)
6. Eval set (queries + expected behaviour)

**Must monitor:**
1. Faithfulness / hallucination rate (LLM-as-judge or human eval)
2. Citation accuracy
3. Cost per query, total $ / day
4. p50 / p95 / p99 latency
5. User feedback (thumbs) and trending
6. Prompt-injection attempts and pass rate
7. Off-topic / refusal rate
8. PII / sensitive topics triggers
</details>

<details>
<summary>A10</summary>

A model answer:

1. **Code**: git commit hash of the training script.
2. **Config**: hyperparameter snapshot, hash-stored.
3. **Data**: DVC / lakeFS / Delta version of the training dataset, with snapshot timestamp.
4. **Feature definitions**: version of `user_avg_session_duration_30d`, `user_clicks_30d`, etc.
5. **Labels**: label set version (especially if human-labelled).
6. **Environment**: container image hash, dependency lock file.
7. **Random seeds**: for any RNG-driven steps.
8. **Hardware**: GPU type / count (affects determinism).

All of these get logged to MLflow / W&B as a run. Six months later, you reproduce the model exactly.
</details>

<details>
<summary>A11</summary>

A model answer:

1. **Profile the network hop.** Is the API → feature store hop the slow point? Add an in-process cache for hot entities.
2. **Profile the feature store itself.** Are you hitting Redis / DynamoDB hot keys? Check partition distribution, add jitter.
3. **Check batch vs single.** Are you doing 50 single-key fetches serially? Batch into one mget; cuts 50 → 1 round trip.
4. **Check feature fan-out.** Are you fetching features that aren't actually used by the model? Drop them.
5. **Add request coalescing in the API layer.** Same `user_id` arrives 5 times in 10ms — serve one fetch to all five.
</details>

<details>
<summary>A12</summary>

A model answer:

> Three reasons to keep the feature store even when SQL "looks" sufficient:
>
> 1. **Online latency.** A SQL query at request time is 200ms–2s of analytics compute. A feature store is <50ms. For fraud / recommendation / ranking, that's the whole SLA.
> 2. **Point-in-time correctness.** SQL joins today on today. Feature store handles "as of 2024-03-15" correctly. Without it, training silently leaks.
> 3. **Discoverability and ownership.** Without a registry, every model reinvents `user_lifetime_value` slightly differently. The feature store publishes features once, with an owner. The SQL approach has no contract.
>
> The SQL approach is fine for offline analytics. For ML serving, you want the store.

</details>

<details>
<summary>A13</summary>

A model answer (Feast style):

```python
from feast import FeatureView, Field, FileSource
from feast.types import Float32
from datetime import timedelta

sessions_source = FileSource(
    path="s3://lake/events/sessions/",
    timestamp_field="event_ts",
)

@feature_view(
    name="user_avg_session_duration_30d",
    entities=["user_id"],
    schema=[Field(name="avg_session_duration_seconds", dtype=Float32)],
    source=sessions_source,
    ttl=timedelta(days=30),
    online=True,
    owner="growth-platform",
    freshness_sla="5m",
    description="Average session duration per user over the last 30 days",
)
def user_avg_session_duration_30d(user_id, ts):
    return f"""
        SELECT user_id, event_ts,
               AVG(duration_seconds) as avg_session_duration_seconds
        FROM events
        WHERE event_type = 'session_end'
          AND event_ts >= ts - INTERVAL 30 DAY
        GROUP BY user_id, event_ts
    """
```
</details>

<details>
<summary>A14</summary>

A model answer:

```
   transaction event (Kafka, every event)
        │
        ▼
   Flink (sub-second transform)
        │
        ├──► Redis (online, last-write-wins on entity_id)
        │
        └──► Parquet (offline, batched every 1m)
                     │
                     └─► CDC → Redis (catches any misses)

   request: { "transaction_id": "..." }
        │
        ▼
   API
        │
        ├──► Redis lookup (entity_id from cardholder)
        │     ◄── features at p95 < 30ms
        │
        ├──► Model inference
        │
        └──► Response (allow / review / decline)
```

Key points: streaming transform, Redis as online, Parquet as offline-of-truth with CDC catch-up, idempotent writes keyed on entity+timestamp.
</details>

<details>
<summary>A15</summary>

A model answer:

- **200 general queries** — hand-curated, balanced across topics, with expected source document for retrieval eval.
- **50 hard queries** — multi-hop, edge cases, ambiguous phrasing.
- **30 freshness queries** — questions about things that changed yesterday / last week; verify the freshness SLA.
- **20 freshness queries off-policy** — questions about things that *should* be off-limits (HR, draft policies).
- **50 guardrail queries** — prompt injection, PII requests, off-topic, edge cases that should trigger refusal.

Total ~350 examples, refreshed quarterly. The guardrail set must pass on every PR; the rest run nightly.

</details>

<details>
<summary>A16</summary>

This is a personal reflection. Pick any incident. The question to focus on:

- **Detection speed** — how long from breakage to alert?
- **Root-cause layer** — was it the data, the model, the serving infra, or the eval?
- **Fix propagation** — was the fix local (this model) or systemic (this pattern)?

Without instrumentation, you can't fix what you can't see. The MLOps / LLMOps discipline exists to ensure you see.

</details>

---

*End of Module 6. Move to [Module 7 — AI on Cloud Platforms](../07-ai-on-cloud-platforms/README.md).*