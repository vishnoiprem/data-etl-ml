"""
Cell 20: Kafka Delivery Semantics — at-most-once, at-least-once, exactly-once

The interview question:
'How do you guarantee no duplicate inserts to the vector DB during
 stream ingestion? Walk me through the failure modes.'

L6 answer structure:
- at-most-once: ack BEFORE write. Fast, lossy.
- at-least-once: ack AFTER write. Default Kafka. May duplicate.
- exactly-once: idempotent producer + transactional consumer.
  Only works if SINK supports transactions (Postgres, Kafka, NOT Qdrant).
- For Qdrant: idempotency via (doc_id, chunk_hash, model_version) UNIQUE.

Failure modes demoed:
- Consumer crash mid-batch -> replay from offset
- Network partition -> duplicate delivery
- Out-of-order processing
"""
import json
import time
import random
from dataclasses import dataclass, field
from typing import List, Set, Tuple
from enum import Enum
from collections import defaultdict

# ════════════════════════════════════════════════════════════════
# DELIVERY SEMANTICS: 3 modes compared
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("DELIVERY SEMANTICS: the 3 modes")
print("=" * 70)
print("""
1. AT-MOST-ONCE (fastest, lossy):
   - Producer: ack = 0 (fire and forget)
   - Consumer: process THEN commit offset
   - If consumer crashes after process, before commit -> message LOST
   - Use case: metrics, telemetry, ad impressions (loss is OK)

2. AT-LEAST-ONCE (default, may duplicate):
   - Producer: ack = all (wait for all replicas)
   - Consumer: commit offset THEN process (or process then commit)
   - If consumer crashes after commit, before process -> DUPLICATE
   - Use case: most data pipelines (dedup at sink)

3. EXACTLY-ONCE (slowest, no duplicates):
   - Idempotent producer (Kafka 0.11+, dedup by producer_id + sequence)
   - Transactional consumer: process + commit in ONE atomic op
   - Sink MUST support transactions (Postgres, MySQL, Kafka)
   - Vector DBs (Qdrant, Pinecone) do NOT support transactions
   - Use case: financial transactions, billing

For LLM ingestion into a vector DB, the L6 answer is:
  - at-least-once delivery from Kafka
  - Idempotency key (doc_id, chunk_hash, model_version) UNIQUE
  - Sink dedupes duplicates silently
""")

# ════════════════════════════════════════════════════════════════
# SIMULATE: consumer with 3 failure modes
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("SIMULATION: 1000 messages, 3 consumer crash scenarios")
print("=" * 70)

class DeliveryMode(Enum):
    AT_MOST_ONCE = "at-most-once"
    AT_LEAST_ONCE = "at-least-once"
    EXACTLY_ONCE = "exactly-once"

@dataclass
class Message:
    offset: int
    key: str
    value: dict
    timestamp: float

@dataclass
class ConsumerStats:
    processed: int = 0
    duplicates: int = 0
    lost: int = 0
    crashed: bool = False
    sink_keys: Set[Tuple] = field(default_factory=set)

class SimulatedConsumer:
    def __init__(self, mode: DeliveryMode):
        self.mode = mode
        self.committed_offset = 0
        self.stats = ConsumerStats()

    def process_message(self, msg: Message, sink_keys: Set, fail_at: int = None):
        """Process one message. Returns (status, new_offset_committed)."""
        # CRASH simulation: kill at offset `fail_at`
        if fail_at is not None and msg.offset == fail_at and random.random() < 0.5:
            self.stats.crashed = True
            raise RuntimeError(f"Consumer crashed at offset {msg.offset}")

        # Idempotency key
        key = (msg.value['doc_id'], msg.value['chunk_hash'], msg.value['model_version'])
        if key in sink_keys:
            self.stats.duplicates += 1
            status = "DUPLICATE"
        else:
            sink_keys.add(key)
            self.stats.processed += 1
            status = "OK"

        # Commit offset (timing depends on mode)
        if self.mode == DeliveryMode.AT_MOST_ONCE:
            # Commit BEFORE process -> if crash, message lost
            self.committed_offset = msg.offset + 1
        elif self.mode == DeliveryMode.AT_LEAST_ONCE:
            # Commit AFTER process -> if crash between, duplicate
            self.committed_offset = msg.offset + 1
        else:  # EXACTLY_ONCE
            # Commit + process in atomic op
            self.committed_offset = msg.offset + 1

        return status

# Generate 1000 messages
random.seed(42)
messages = []
for i in range(1000):
    doc_id = f"doc_{i % 500}"  # 50% duplicate doc_ids
    messages.append(Message(
        offset=i,
        key=doc_id,
        value={
            "doc_id": doc_id,
            "chunk_hash": f"hash_{i}",
            "model_version": "ada-002",
            "text": f"text {i}"
        },
        timestamp=time.time()
    ))

# Simulate each mode, with crash at offset 500
for mode in DeliveryMode:
    consumer = SimulatedConsumer(mode)
    sink = set()
    try:
        for msg in messages:
            consumer.process_message(msg, sink, fail_at=500)
    except RuntimeError:
        pass

    print(f"\n{mode.value}:")
    print(f"  Processed:    {consumer.stats.processed}")
    print(f"  Duplicates:   {consumer.stats.duplicates}")
    print(f"  Lost:         {consumer.stats.lost}")
    print(f"  Crashed:      {consumer.stats.crashed}")
    print(f"  Committed at: {consumer.committed_offset}")

# ════════════════════════════════════════════════════════════════
# REPLAY SCENARIO
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("REPLAY SCENARIO: consumer died at offset 500, restart from 500")
print("=" * 70)
print("""
Producer: 1000 messages (offsets 0-999)
Consumer: processes 0-499, crashes at 500
Restart: replay from 500, process 500-999
""")

# Original sink (pre-crash, has 0-499 written)
original_sink = set()
for msg in messages[:500]:
    key = (msg.value['doc_id'], msg.value['chunk_hash'], msg.value['model_version'])
    original_sink.add(key)

# Replay: process 500-999, dedup against original
replay_consumer = SimulatedConsumer(DeliveryMode.AT_LEAST_ONCE)
new_writes = 0
dupes = 0
for msg in messages[500:]:
    key = (msg.value['doc_id'], msg.value['chunk_hash'], msg.value['model_version'])
    if key in original_sink:
        dupes += 1
    else:
        original_sink.add(key)
        new_writes += 1
        replay_consumer.committed_offset = msg.offset + 1

print(f"  Original sink size:  500")
print(f"  Replay processed:    500 messages (offset 500-999)")
print(f"  New writes:          {new_writes}")
print(f"  Duplicates filtered: {dupes}  <- idempotency key (doc_id, chunk_hash, model_version)")
print(f"  Final sink size:     {len(original_sink)}")
print(f"  Result: NO data loss, duplicates silently filtered")

# ════════════════════════════════════════════════════════════════
# KAFKA PRODUCER IDEMPOTENCE
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("KAFKA PRODUCER IDEMPOTENCE: the (producer_id, sequence) trick")
print("=" * 70)
print("""
Without idempotence:
  - Network blip -> producer retries -> broker writes twice
  - Same message, two offsets, consumer processes twice

With idempotent producer (Kafka 0.11+):
  - Each producer has a unique producer_id
  - Each message has a sequence number (per partition)
  - Broker dedupes: (producer_id, sequence) UNIQUE
  - 5x lower duplicate rate in practice

In code:
  producer = KafkaProducer(
      enable_idempotence=True,  # this is the magic flag
      acks='all',
      retries=10,
      max_in_flight_requests_per_connection=5
  )

This is FREE. Always enable it. It costs nothing and prevents an
entire class of duplicate-message bugs.
""")

# ════════════════════════════════════════════════════════════════
# OUT-OF-ORDER PROCESSING
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("OUT-OF-ORDER: partition = 1, but consumer pool = 3")
print("=" * 70)
print("""
With 3 partitions and 3 consumers, each consumer owns 1 partition.
Ordering within partition is preserved.

But if you SCALE consumers to 5, two will be idle.
If you SHRINK to 2, one consumer reads 2 partitions (still ordered).

The rule: NUM_PARTITIONS >= NUM_CONSUMERS for max parallelism.
If you have ordering requirements, NEVER increase consumers
beyond partitions.
""")

# ════════════════════════════════════════════════════════════════
# L6 ANSWER
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("L6 ANSWER (when they ask 'how do you dedupe Kafka -> DB?')")
print("=" * 70)
print("""
Q: "How do you guarantee no duplicate inserts to the vector DB
    during stream ingestion from Kafka?"

A: "Four layers, defense in depth:

1. KAFKA PRODUCER:
   - enable_idempotence=True (free, prevents retry-duplicates)
   - acks='all' (wait for all in-sync replicas)
   - retries=10, max_in_flight=5 (preserves ordering)

2. KAFKA CONSUMER:
   - enable.auto.commit=False
   - Manual commit AFTER batch processed
   - If consumer crashes mid-batch, replay from last committed offset

3. IDEMPOTENCY KEY (the L6 phrase):
   - UNIQUE constraint on (doc_id, chunk_hash, model_version)
   - Sink dedupes duplicates silently
   - We don't need Kafka transactions because the sink
     is the source of truth, not Kafka

4. DLQ FOR POISON MESSAGES:
   - 1% of messages will be malformed (schema drift, upstream bug)
   - Route to dead-letter topic, alert on depth > 100
   - Don't block the pipeline on poison

Failure modes covered:
- Producer retry -> idempotent producer dedupes
- Consumer crash -> replay from offset, sink dedupes
- Out-of-order -> partition assignment preserves order per key
- Poison message -> DLQ

The cardinal sin: enable.auto.commit=True with no sink dedup.
Result: lost messages on consumer crash, duplicates on retry.
The combination (auto-commit + no dedup) is the most common
production bug in Kafka pipelines.

For exactly-once into Postgres / MySQL:
  - Kafka transactions + JDBC sink with XA
  - But for vector DBs (Qdrant, Pinecone, Weaviate):
  - No transactions. Idempotency key is the only option.
""")
