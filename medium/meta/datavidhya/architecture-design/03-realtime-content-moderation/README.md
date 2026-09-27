# Real-Time Content Moderation Pipeline

**Difficulty:** HARD
**Companies:** Meta, Twitter/X, Google, Pinterest, TikTok
**Tags:** system-design, ml, streaming, computer-vision, nlp, safety

---

## 1. Problem Statement

> 500M+ pieces of content per day — text posts, images, videos. Harmful content
> must be caught within 10 seconds of posting, before it goes viral. We use ML
> models for text, image, and video classification, but borderline cases need
> human review. Too many false positives censor legitimate speech; too many
> false negatives let harmful content reach millions. Design the pipeline.

### Hard Parts
- Sub-10-second latency across multi-modal (text, image, video frame) inference
- 50K pieces/sec at peak
- Severe classes (CSAM, terrorism) must have < 0.1% false negative
- Borderline cases need human review (10K reviewers globally, 200+ items/shift)
- Feedback loop from human decisions into model retraining
- Appeal workflow for users to challenge auto-removals

### Scale & Constraints

| Dimension | Value |
|---|---|
| Throughput | 500M+ content pieces/day, 50K/sec peak |
| Latency | < 10 sec end-to-end (ingest → decision) |
| FN target (severe) | < 0.1% (CSAM, terrorism, child safety) |
| FP target | < 5% overall |
| Reviewers | 10K globally, 200+ items per shift |
| Modalities | Text (ms), Image (100ms), Video (s/frame) |

---

## 2. The 5-Step Approach

### Step 1 — Clarify Requirements
- **Severe-content priority:** child safety, terrorism, immediate threats → instant auto-remove
- **Borderline content:** routed to human queue with priority
- **Appeals:** user can request second-look; routed to senior reviewers
- **Feedback:** human labels feed back into nightly model retraining
- **Auditability:** every decision + every model version traceable for legal

### Step 2 — High-Level Architecture

```
User uploads content
       │
       ▼
   API Gateway ──▶ content_id + payload hash + URL
       │
       ▼
   Content Ingestion ──▶ Kafka: content.raw
       │
       ▼
   ┌─────────────── Multi-Modal Inference Fan-Out ───────────────┐
   │   text classifier  │  image classifier  │  video frame     │
   │   (fastText/BERT)   │  (CNN/ViT)         │  analyzer (CNN)  │
   └────────────────────┬─────────────────────┬──────────────────┘
                        ▼                     ▼
                 Score Aggregator ──▶ Confidence Router
                        │
       ┌────────────────┼────────────────────────────┐
       ▼                ▼                            ▼
  AUTO_REMOVE       HUMAN_REVIEW               AUTO_APPROVE
  (severe, FNs)     (borderline, appeal)       (low risk)
       │                │
       │                ▼
       │         Reviewer Queue
       │         - priority-ranked
       │         - reviewer assignment (skill + workload)
       │         - SLA timer
       │
       ▼
   Audit Log
       │
       ▼
   Feedback → Nightly Retrain → Model Registry → Canary Deploy
```

### Step 3 — Data Flow & Routing

**Three-class routing by confidence + class severity:**

| Class Severity | High Confidence | Borderline | Low Confidence |
|---|---|---|---|
| **SEVERE** (CSAM, terror) | Auto-remove + report | Auto-remove + flag for spot-check | Human review (priority 0) |
| **HARMFUL** (hate, harassment) | Auto-remove | Human review (priority 1) | Auto-approve |
| **BORDERLINE** (politics, NSFW) | Human review (priority 2) | Human review (priority 2) | Auto-approve |
| **SAFE** (everything else) | Auto-approve | Auto-approve | Auto-approve |

### Step 4 — Scale the Design

| Concern | Approach |
|---|---|
| 50K/sec throughput | Async fan-out per modality; GPU pool with autoscaling |
| Video frame analysis | Extract I-frames at 1 fps; run inference on first suspicious frame only |
| Reviewer load balancing | Skill-based assignment (CSAM-trained reviewers only for CSAM); geographic timezone match |
| Severe class FN | Ensemble of 3+ models + conservative threshold + always-route borderline to humans |
| False-positive cost | Use calibrator (Platt / isotonic) to set per-class thresholds |
| Feedback loop | Nightly batch retraining; weekly full eval; auto-rollback on regression |

### Step 5 — Non-Functional

- **Latency:** P50 = 1.5s, P99 = 8s end-to-end (text 100ms, image 200ms, video 6s)
- **Reliability:** Queue-based with DLQ for inference failures; never drop severe-class items
- **Observability:** Per-class precision/recall daily; reviewer disagreement rate; appeal overturn rate
- **Security/Privacy:** Reviewer can't see user identity; content encrypted at rest; access logged
- **Auditability:** Decision = (model_version, score, threshold, timestamp, features_used_hash)
- **Compliance:** NCMEC reporting for CSAM; transparency reports quarterly

---

## 3. Critical Design Decisions

### 3.1 Multi-Modal Inference Fan-Out
- Each modality has its own async worker (text/image/video)
- A **score aggregator** waits for all modalities, then decides
- For severe classes, the WORST score across modalities wins → reduces FN
- For safe classes, the BEST score wins → reduces FP

### 3.2 Human-in-the-Loop Queue
- Items pre-sorted by priority (severe > harmful > borderline > appeal)
- Reviewer assignment: round-robin within skill group + workload-balancing
- **SLA timers:** priority 0 = 5 min, priority 1 = 30 min, priority 2 = 4 hr
- **Reviewer disagreement** triggers senior review + model flag

### 3.3 Feedback Loop
- All human decisions labeled with confidence + reviewer_id + timestamp
- Nightly: extract labels → label store → trigger retraining job
- **Shadow deployment** for new models: predictions logged but not actioned
- **Canary** at 5% traffic for 24h, auto-promote if metrics hold

### 3.4 Appeal Workflow
- User submits appeal → re-queues with priority 3 + appeal flag
- Routed to **different reviewer** than original (avoid self-approval bias)
- Two-reviewer agreement required for appeal reversal on severe classes
- Decision + rationale shown to user

### 3.5 Severe Class Defense (CSAM, Terrorism)
- **Hash matching** (PhotoDNA, industry hash list) for known CSAM — instant block
- **Conservative ensemble:** 3 specialized models vote; if ANY flags → remove
- **NCMEC report** generated automatically for CSAM detections
- **No appeals allowed** for severe class (per law)

---

## 4. Folder Layout

```
03-realtime-content-moderation/
├── README.md
├── docs/design-decisions.md
├── diagrams/
│   ├── architecture.mermaid
│   ├── routing-decision.mermaid
│   └── human-loop.mermaid
├── sql/
│   ├── schema.sql                  # content, decisions, review_queue, appeals
│   ├── queue_assignment.sql        # reviewer workload balancing
│   └── moderation_metrics.sql      # precision/recall dashboards
├── python/
│   ├── scoring_aggregator.py       # multi-modal score combination
│   ├── confidence_router.py        # auto-remove / human / auto-approve
│   ├── reviewer_queue.py           # priority queue, SLA timers
│   ├── appeal_workflow.py          # appeals routing
│   └── feedback_loop.py            # human labels → retraining
├── pyspark/
│   ├── ingest_content.py
│   ├── decision_audit.py           # long-term storage of all decisions
│   ├── reviewer_metrics.py         # per-reviewer throughput + agreement
│   └── training_dataset.py         # build labeled dataset for retrain
├── config/
│   ├── class_severity.json
│   ├── model_registry.json
│   └── reviewer_skills.json
├── sample_data/
│   ├── content.jsonl
│   └── human_labels.jsonl
└── tests/
    ├── test_router.py
    ├── test_reviewer_queue.py
    └── test_feedback_loop.py
```

---

## 5. How to Run End-to-End

```bash
# 1. Generate sample content
python python/scoring_aggregator.py --demo

# 2. Route through confidence router
python python/confidence_router.py --input sample_data/content.jsonl

# 3. Simulate human review
python python/reviewer_queue.py --simulate

# 4. Feedback loop simulation
python python/feedback_loop.py --labels sample_data/human_labels.jsonl
```

---

## 6. Interview Talking Points

1. **Multi-modal fan-out** — text, image, video run in parallel; aggregator waits for worst case
2. **Severity-based routing** — severe classes take no chances; borderline goes to humans
3. **Hash matching first** — known CSAM is blocked in < 50ms before ML runs
4. **Human-in-the-loop SLA** — priority queues + reviewer skills + timezone balancing
5. **Feedback loop** — human labels retrain models nightly; shadow + canary deployment
6. **Appeals** — different reviewer required, two-reviewer rule for severe class
7. **Auditability** — every decision traceable for legal/regulatory compliance
8. **Cost story** — humans only see borderline content; safe content auto-approved
