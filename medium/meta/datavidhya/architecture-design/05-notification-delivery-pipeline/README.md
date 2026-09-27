# Notification Delivery & Engagement Analytics Pipeline

**Difficulty:** MEDIUM
**Companies:** Meta, Spotify, Uber, Pinterest, Airbnb
**Tags:** system-design, attribution, streaming, ml, big-data

---

## 1. Problem Statement

> We send over a billion notifications a day — push, email, SMS, in-app.
> I need a pipeline that tracks the full lifecycle: sent → delivered → opened →
> clicked → converted. If a user opens the app within 30 minutes of a push
> notification, we attribute that to the notification. We also need to detect
> notification fatigue — when a user is getting too many and about to
> unsubscribe. Design the analytics pipeline.

### Hard Parts
- **1B+ notifications/day** across 4 channels
- **30-min attribution window** — late-arriving events still need to be matched
- **Multi-channel dedup** — same message via push + email = count once
- **Notification fatigue** — predict churn/unsubscribe before it happens
- **Privacy** — email pixel tracking can be disabled
- **A/B testing** — different copy/timing/channel/frequency variants

### Scale & Constraints

| Dimension | Value |
|---|---|
| Throughput | 1B+ notifications/day |
| Latency | Delivery + open metrics within 5 min |
| Attribution window | 30 min push → app open |
| Channels | Push (iOS/Android), Email, SMS, In-app |
| Privacy | No email pixel for users who disabled tracking |

---

## 2. The 5-Step Approach

### Step 1 — Clarify Requirements
- **Consumers:** Marketing, Growth, ML (notification ranking), Eng (delivery health)
- **Decision loops:**
  - Fatigue → frequency cap adjustment
  - A/B test winners → ramp-up traffic
  - Channel performance → channel mix optimization
- **Engagement metrics:** send → delivered → opened → clicked → converted
- **Privacy:** Honor per-user channel preferences; respect pixel opt-out

### Step 2 — High-Level Architecture

```
Notification Send Service (per channel)
       │
       ▼
   Kafka: notification.sent ───────────────┐
       │                                    │
       ▼                                    ▼
   Delivery Provider ──── Kafka: notification.delivered
       │
       ▼
   User Device ──── Kafka: notification.opened / .clicked
       │
       ▼
   ┌─────────── Stream Processing (Flink) ───────────┐
   │  Multi-channel dedup (notification_group_id)    │
   │  Attribution join (push open within 30 min)      │
   │  Fatigue scorer (frequency cap eligibility)     │
   │  Real-time dashboard rollup                     │
   └───────────────┬──────────────────────────────────┘
                   ▼
        Lakehouse: notification_facts (Iceberg)
                   │
   ┌───────────────┼─────────────────┐
   ▼               ▼                 ▼
Dashboards     ML Training      A/B Test
(Superset)   (send-time,        Platform
              channel mix)      (Problem 1)
```

### Step 3 — Data Model

**Core entities:**

```
notification_id        STRING  (unique per send)
notification_group_id  STRING  (dedup key across channels)
user_id                STRING
channel                STRING  ('push'|'email'|'sms'|'in_app')
notification_type      STRING  ('marketing'|'transactional'|'system')
template_id            STRING
campaign_id            STRING
variant_id             STRING
sent_ts                TIMESTAMP
delivered_ts           TIMESTAMP (nullable)
opened_ts              TIMESTAMP (nullable)
clicked_ts             TIMESTAMP (nullable)
converted_ts           TIMESTAMP (nullable)
dismissed_ts           TIMESTAMP (nullable)
unsubscribed_ts        TIMESTAMP (nullable)
attribution_window_end TIMESTAMP (sent_ts + 30min)
```

### Step 4 — Scale the Design

| Concern | Approach |
|---|---|
| 1B+ events/day | Kafka partitioned by user_id; Iceberg partitions by day |
| Multi-channel dedup | Shared `notification_group_id`; Flink keyed state |
| Attribution join | Stream-stream join on (user_id, 30-min window) |
| Fatigue scoring | Rolling-window per-user counters in Flink state |
| Email pixel privacy | Two delivery paths: tracking-pixel vs server-side confirm |
| A/B testing | Same assignment service as Problem 1 (orthogonal layers) |

### Step 5 — Non-Functional

- **Latency:** 5-min freshness for delivery + open metrics
- **Reliability:** At-least-once Kafka; idempotent sinks
- **Privacy:** Per-user pixel opt-out flag; suppress tracking-pixel events
- **Cost:** Email tracking pixels free; SMS conversion tracking expensive → limit

---

## 3. Critical Design Decisions

### 3.1 Multi-Channel Dedup
When a notification is sent via push + email simultaneously:
- Same `notification_group_id` is attached to both sends
- Flink keyed state tracks per-group max engagement
- Attribution uses group_id, not notification_id

### 3.2 Attribution Logic
Push notification sent at T. App open at T+15min from same user on same device.
→ That app open is attributed to the push notification.
→ Mark `attribution_source = notification_id`.

Implementation: stream-stream join in Flink
- Stream A: notification.sent events (keyed by user_id)
- Stream B: app_open events (keyed by user_id)
- Join window: 30 min after each sent_ts

### 3.3 Fatigue Detection
For each user, compute rolling windows:
- Notifications sent in last 24h
- Open rate in last 7 days
- Dismiss + unsubscribe in last 7 days

ML model: predict probability of (next_unsubscribe | features) in next 7 days.
If probability > 0.5 → drop marketing notifications; keep transactional.

### 3.4 A/B Testing
Uses Problem 1's experiment assignment service. Variants:
- Copy: short vs long
- Timing: morning vs evening
- Channel: push-only vs push+email vs sms
- Frequency: 5/wk vs 3/wk

Same statistical engine — sequential mSPRT, CUPED, guardrails.

### 3.5 Email Pixel Privacy
- Per-user `tracking_pixel_enabled` flag
- Two email templates: tracking-enabled (with pixel) vs tracking-disabled
- Tracking-disabled emails still log delivery + clicks via server-side confirm
- No pixel event recorded for opted-out users

---

## 4. Folder Layout

```
05-notification-delivery-pipeline/
├── README.md
├── docs/design-decisions.md
├── diagrams/
│   ├── architecture.mermaid
│   ├── attribution.mermaid
│   └── fatigue-loop.mermaid
├── sql/
│   ├── schema.sql
│   ├── attribution_query.sql
│   ├── fatigue_metrics.sql
│   └── channel_performance.sql
├── python/
│   ├── multi_channel_dedup.py
│   ├── attribution_engine.py
│   ├── fatigue_scorer.py
│   └── ab_test_router.py
├── pyspark/
│   ├── ingest_notification_events.py
│   ├── build_facts.py
│   ├── channel_mix_optimizer.py
│   └── fatigue_training_dataset.py
├── config/
│   ├── notification_templates.json
│   └── fatigue_thresholds.json
├── sample_data/
│   ├── notifications.jsonl
│   └── app_opens.jsonl
└── tests/
    ├── test_dedup.py
    ├── test_attribution.py
    └── test_fatigue.py
```

---

## 5. How to Run End-to-End

```bash
# 1. Generate sample notifications + app opens
python python/attribution_engine.py --demo

# 2. Multi-channel dedup
python python/multi_channel_dedup.py --input sample_data/notifications.jsonl

# 3. Run attribution
python python/attribution_engine.py --input sample_data/notifications.jsonl

# 4. Compute fatigue scores
python python/fatigue_scorer.py --user-id user_42
```

---

## 6. Interview Talking Points

1. **Notification lifecycle** — sent → delivered → opened → clicked → converted
2. **Multi-channel dedup** — group_id links channels; engagement counted once
3. **Attribution window** — 30 min is the industry standard; explain why
4. **Fatigue as ML problem** — rolling features + classifier; not just a hard cap
5. **Email pixel privacy** — separate paths for opted-in vs opted-out users
6. **A/B testing reuse** — same assignment service, same statistical engine
7. **Real-time dashboard** — 5-min rollup window via Flink → Iceberg → Trino
8. **Cost story** — SMS tracking is expensive; only attribute high-value events
