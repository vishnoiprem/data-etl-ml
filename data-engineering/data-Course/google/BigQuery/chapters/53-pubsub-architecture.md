# 9.1 — Pub/Sub Architecture

> **Section 9 · Pub/Sub & Streaming · Lecture 9.1 · 5:20**

## 🎯 What you will learn

- The Pub/Sub model: topics, subscriptions, publishers, and pullers
- Push vs pull subscriptions, and when to use each
- Message ordering, exactly-once delivery, and dead-letter topics
- The Pub/Sub → BigQuery streaming path
- Quotas, cost, and monitoring

---

## 🧠 Concept

Pub/Sub is a messaging service. Publishers send messages to a **topic**; consumers read them
from a **subscription**.

```
Producers ──publish──▶ [ Topic ] ──push──▶ Subscriber endpoint
                            │
                            └──pull──▶ Puller → BigQuery / Dataflow / GCS
```

| Object | Purpose |
|--------|---------|
| **Topic** | A named channel for messages |
| **Subscription** | A queue attached to a topic; each subscription gets its own copy |
| **Message** | `data` (bytes) + `attributes` (key-value metadata) |
| **Publisher** | The client that sends messages |
| **Puller** | The client that receives messages |
| **Push subscription** | Pub/Sub delivers via HTTP to your endpoint |
| **Pull subscription** | Your client pulls and acknowledges messages |
| **Ordering key** | Messages with the same key are delivered in order |
| **Dead-letter topic** | Where un-acknowledged messages go after max delivery attempts |
| **Snapshot** | A point-in-time copy of a subscription's backlog |

💡 **One topic, many subscriptions.** Each team subscribes independently — the analytics
consumer and the fraud consumer each see every message without interfering.

---

## 🛠️ Hands-On

### 1. Create a topic and subscription

```bash
gcloud pubsub topics create retailmart.events \
  --project=YOUR_PROJECT_ID

gcloud pubsub subscriptions create retailmart.events-sub \
  --topic=retailmart.events \
  --ack-deadline=60 \
  --message-retention-duration=7d \
  --expiration-policy="" \
  --project=YOUR_PROJECT_ID
```

```bash
# Dead-letter topic
gcloud pubsub topics create retailmart.events-dlq --project=YOUR_PROJECT_ID

gcloud pubsub subscriptions create retailmart.events-sub \
  --topic=retailmart.events \
  --dead-letter-topic=retailmart.events-dlq \
  --max-delivery-attempts=5 \
  --project=YOUR_PROJECT_ID
```

💡 **Always configure a dead-letter topic.** Without it, a poison message retries forever and
blocks the subscription.

### 2. Publish a message

```bash
gcloud pubsub topics publish retailmart.events \
  --message='{"event_id":"e001","user_id":"u001","event_type":"purchase","amount":42.5}' \
  --attribute="source=web" \
  --attribute="sent_at=$(date -u +%s)" \
  --project=YOUR_PROJECT_ID
```

### 3. Publish from Python

```python
from google.cloud import pubsub_v1

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path("YOUR_PROJECT_ID", "retailmart.events")

future = publisher.publish(
    topic_path,
    b'{"event_id":"e001","user_id":"u001","event_type":"purchase"}',
    source="web",
    sent_at="2026-01-15T10:00:00Z",
)
message_id = future.result()   # blocks
print(f"Published {message_id}")
```

### 4. Pull from a subscription

```python
from google.cloud import pubsub_v1

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path("YOUR_PROJECT_ID", "retailmart.events-sub")

def callback(message: pubsub_v1.subscriber.message.Message):
    try:
        event = message.data.decode("utf-8")
        process(event)
        message.ack()
    except Exception as exc:
        log.error("Failed: %s", exc)
        message.nack()   # redeliver


future = subscriber.subscribe(subscription_path, callback=callback)
future.result()   # blocks forever
```

### 5. Pull with the synchronous client (batching, for tests)

```python
subscriber = pubsub_v1.SubscriberClient()
response = subscriber.pull(
    request={"subscription": subscription_path, "max_messages": 10},
    timeout=30,
)

ack_ids = []
for received in response.received_messages:
    print(received.message.data.decode())
    ack_ids.append(received.ack_id)

subscriber.acknowledge(request={"subscription": subscription_path, "ack_ids": ack_ids})
```

### 6. Message ordering with ordering keys

```python
# Publish with an ordering key
publisher.publish(
    topic_path,
    b'{"event_id":"e002"}',
    ordering_key="customer-42",   # all events for this customer arrive in order
)
```

```bash
gcloud pubsub topics publish retailmart.events \
  --message='{"event_id":"e002"}' \
  --ordering-key=customer-42
```

💡 **Ordering keys are a per-key ordering guarantee, not a global one.** Messages for
`customer-42` are ordered relative to each other; different keys are unordered. Ordering keys
reduce throughput, so use them only where you truly need it.

### 7. Exactly-once delivery

```bash
gcloud pubsub subscriptions create retailmart.events-sub-eod \
  --topic=retailmart.events \
  --exactly-once-delivery \
  --message-retention-duration=7d \
  --project=YOUR_PROJECT_ID
```

```python
subscriber = pubsub_v1.SubscriberClient()
subscriber.subscribe(
    subscription_path,
    callback=callback,
    flow_control=pubsub_v1.subscriber.flowcontrol.FlowControl(max_messages=100),
)
```

💡 **Exactly-once delivery is only meaningful within Pub/Sub.** It deduplicates redeliveries
of the same message, but it does not make your BigQuery write idempotent — you still need
deduplication on the consumer side.

### 8. Push subscription to a Cloud Run endpoint

```bash
gcloud pubsub subscriptions create retailmart.events-push \
  --topic=retailmart.events \
  --push-endpoint=https://YOUR_PROJECT_ID.cloudfunctions.net/ingest \
  --push-auth-service-account=pubsub-push@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --project=YOUR_PROJECT_ID
```

```python
# Cloud Run / Cloud Function receiver
import base64
import json
from flask import Flask, request

app = Flask(__name__)

@app.route("/", methods=["POST"])
def receive():
    envelope = request.get_json()
    for message in envelope.get("message", {}).get("data", []) or [envelope["message"]["data"]]:
        pass  # real payload handling

    data = base64.b64decode(envelope["message"]["data"]).decode("utf-8")
    event = json.loads(data)
    insert_to_bigquery(event)

    return "", 204   # 2xx = ack
```

💡 **A 2xx response acknowledges the message. Any non-2xx triggers redelivery** with
exponential backoff. Return errors honestly — do not return 200 for work you did not do.

### 9. Push to BigQuery directly (the simplest streaming path)

```bash
gcloud pubsub subscriptions create retailmart.events-to-bq \
  --topic=retailmart.events \
  --push-endpoint=https://bigquery.googleapis.com/bigquery/v2/projects/YOUR_PROJECT_ID/datasets/retailmart/tables/raw_events:stream \
  --push-auth-service-account=pubsub-bq-writer@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --project=YOUR_PROJECT_ID
```

💡 **This needs no code at all.** Pub/Sub pushes each message straight into a BigQuery table as
a row. It is the fastest path to a streaming BigQuery table, and the table must have a schema
matching the JSON payload.

```sql
CREATE TABLE `YOUR_PROJECT_ID.retailmart.raw.events` (
  event_id   STRING    NOT NULL,
  user_id    STRING,
  event_type STRING,
  amount     NUMERIC,
  event_ts   TIMESTAMP,
  ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
OPTIONS (
  description = "Raw clickstream events streamed from Pub/Sub",
  partition_expiration_days = 730
);
```

### 10. Dead-letter handling

```sql
-- Inspect the DLQ
SELECT
  JSON_VALUE(message.data, '$.event_id') AS event_id,
  publish_time,
  attributes
FROM `YOUR_PROJECT_ID.retailmart.events-dlq`
ORDER BY publish_time DESC
LIMIT 100;
```

```python
# Replay a DLQ message back to the topic
from google.cloud import pubsub_v1

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path("YOUR_PROJECT_ID", "retailmart.events")

for row in client.query(
    "SELECT message FROM `YOUR_PROJECT_ID.retailmart.events-dlq` LIMIT 100"
).result():
    publisher.publish(topic_path, row.message.encode("utf-8"))
```

### 11. Seeding a subscription from a BigQuery table

```sql
-- Export a BigQuery table into a Pub/Sub topic
EXPORT DATA OPTIONS(
  uri = 'gs://YOUR_PROJECT_ID-bq-course/pubsub/orders_*.json',
  format = 'NEWLINE_DELIMITED_JSON'
) AS
SELECT
  TO_JSON_STRING(STRUCT(order_id, customer_id, order_date, total_amount)) AS data
FROM `YOUR_PROJECT_ID.retailmart.curated.orders`
WHERE order_date = DATE '2026-01-01';
```

```bash
# Load the exported messages back into the topic
gcloud pubsub topics publish retailmart.events \
  --message-from-file=gs://YOUR_PROJECT_ID-bq-course/pubsub/orders_20260101_*.json
```

### 12. Monitoring

```bash
# Subscription backlog
gcloud pubsub subscriptions describe retailmart.events-sub \
  --project=YOUR_PROJECT_ID \
  --format="value(num_undelivered_messages)"

# Monitor the pull rate
gcloud monitoring time-series list \
  --filter='metric.type="pubsub.googleapis.com/subscription/num_undelivered_messages"' \
  --project=YOUR_PROJECT_ID
```

```python
# From Python
subscription = subscriber.get_subscription(request={"subscription": subscription_path})
print(f"Backlog: {subscription.num_undelivered_messages}")
print(f"Ack deadline: {subscription.ack_deadline_seconds}s")
```

---

## 🛠️ Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Resource exhausted: Quota exceeded for quota metric 'Publish requests'` | Publish rate limit | Batch, or request a quota increase |
| `Deadline exceeded` on pull | No messages available | Increase the timeout; check the publisher |
| Messages redelivered forever | Callback raises before `ack()` | Wrap in try/except and `nack()` deliberately |
| `400 Invalid argument: Invalid schema` on BigQuery push | Payload does not match the table schema | Align the schema or reshape the payload |
| Subscription expires | Default 31-day inactivity | Set `--expiration-policy=""` for long-lived subscriptions |
| Out-of-order events | No ordering key | Publish with `ordering_key` |
| Duplicate rows in BigQuery | At-least-once delivery | Deduplicate on `event_id` at query time |
| `403 Permission denied` on publish | Missing `roles/pubsub.publisher` | Grant the role to the service account |

---

## 💡 Production Notes

- **Set `--expiration-policy=""`** on subscriptions you intend to keep — they expire after 31
  days of inactivity by default.
- **Always configure a dead-letter topic and `max-delivery-attempts`.**
- **Set `--ack-deadline` to match your processing time** (60s is a reasonable default; a consumer
  that takes longer gets redelivered while still working).
- **BigQuery's streaming buffer is not query-cached.** Recent events are always scanned.
- **Deduplicate by event ID.** Pub/Sub is at-least-once; your table will have duplicates unless
  you design for it.
- **Use push subscriptions to BigQuery** for the simplest streaming ingestion. Use Dataflow when
  you need state, windowing, or joins.
- **Monitor `num_undelivered_messages`.** A growing backlog is the earliest sign of a broken
  consumer.
- **Batch publishes.** One HTTP call with 1,000 messages is far cheaper than 1,000 calls.

---

## 🔑 Key Takeaways

- Topics fan out to subscriptions; each subscriber gets its own copy.
- Push for simplicity and low latency; pull for control and high throughput.
- **Always set a dead-letter topic, `max-delivery-attempts`, and `expiration-policy=""`.**
- Ordering keys give per-key ordering, at a throughput cost.
- Exactly-once delivery is a Pub/Sub feature; your sink still needs to be idempotent.
- **Pub/Sub → BigQuery push subscription** needs no code — just a matching table schema.

---

## 📚 Practice Exercises

1. **Topic topology.** Design the topic and subscription layout for a platform with three teams
   (analytics, fraud, notifications) and two data sources. Produce a diagram and the `gcloud`
   commands.

2. **Ordering analysis.** Explain how to guarantee per-customer event ordering end to end:
   producer → Pub/Sub → Dataflow → BigQuery. Where can ordering break?

3. **DLQ runbook.** Write a runbook: detect a DLQ backlog, diagnose the cause, replay safely,
   and confirm the fix. Include the exact commands.

4. **Cost model.** Model Pub/Sub + BigQuery streaming cost for 400M events/day at 500 bytes
   each. Compare streaming inserts against a batch load of the same data. Write the
   recommendation.

5. **Quota plan.** Determine the publish and pull quotas you need, and write the request for a
   quota increase with a justification.

---

## 📖 Further Reading

- Pub/Sub overview — https://cloud.google.com/pubsub/docs/overview
- Pub/Sub → BigQuery streaming — https://cloud.google.com/pubsub/docs/pubsub-push-to-bigquery
- Exactly-once delivery — https://cloud.google.com/pubsub/docs/exactly-once-delivery
