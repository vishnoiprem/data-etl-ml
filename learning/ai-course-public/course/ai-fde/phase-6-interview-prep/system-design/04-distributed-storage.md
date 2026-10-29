# System Design Sub-Lesson 4 — Distributed Data Storage & Partitioning (the canonical Pattern 4 walkthrough)

> **Distributed data storage is the fourth most common system design pattern.** 10-15% of system design questions involve sharding + replication (user data, time-series, multi-tenant data, sharded Postgres). The FDE signal: a candidate who names the sharding key AND the cross-shard query strategy AND the failure mode — is showing they can own a distributed system. **This sub-lesson walks through the canonical distributed storage design.**

---

## Why distributed storage is the FDE signal

The 4 things the interviewer is testing:

1. **Can you read the requirements?** Distributed = data is sharded across N nodes; queries are routed by sharding key. The requirement drives the design (sharding key choice, cross-shard queries, replication).
2. **Can you pick the right sharding strategy?** Hash-based (consistent hashing) for even distribution; range-based (by user_id or tenant_id) for range queries; geographic for data sovereignty.
3. **Can you handle cross-shard queries?** Cross-shard queries are slow (network round-trips). The candidate who denormalizes into a read store is showing they understand the trade-off.
4. **Can you handle shard death?** A shard dies (hardware failure, network partition). The candidate who names the read replica fallback is showing they understand the failure mode.

**The FDE pattern:** clarify → decompose → design → tradeoffs. Same as the other patterns, but the design is sharding-focused.

---

## The canonical distributed storage design (worked example)

### The prompt

> "Design a distributed data storage system: a multi-tenant user data store for a SaaS application. 10K tenants, 10M users total, 1TB of data, 10K QPS reads, 100 QPS writes. Each tenant should only see their own data. The system should survive a single shard failure."

### Step 1: Clarify (5-7 minutes)

**The 5 questions:**

1. **What's the user?** Tenants (companies) accessing their own data; SaaS app (internal) serving the data.
2. **What's the scale?** 10K tenants, 10M users, 1TB, 10K QPS reads, 100 QPS writes.
3. **What's the constraint?** Per-tenant data isolation; cost < $1000/month; survive 1 shard failure; < 100ms P95 latency.
4. **What's the failure mode?** Shard dies; tenant queries the wrong shard; cross-shard query is slow.
5. **What's the timeline?** MVP in 4 weeks; full scale in 8 weeks.

### Step 2: Decompose (10-12 minutes)

**The 3 lists:**

**Entities:**
- Tenant (id, name, plan, created_at)
- User (id, tenant_id, email, name, created_at)
- UserProfile (user_id, key, value)
- UserEvent (id, user_id, event_type, timestamp)

**Services:**
- TenantService (CRUD for tenants)
- UserService (CRUD for users, sharded by tenant_id)
- ProfileService (CRUD for profiles, sharded by user_id)
- EventService (append-only events, sharded by user_id)

**Flows:**
- Tenant queries users → UserService routes to shard by tenant_id → returns users
- User updates profile → ProfileService routes to shard by user_id → updates profile
- User triggers event → EventService routes to shard by user_id → appends event

### Step 3: Design (15-20 minutes)

**The sharding strategy:**

- **Users table:** sharded by `tenant_id` (the most common query is "list all users in a tenant")
- **UserProfile table:** sharded by `user_id` (the most common query is "get profile by user_id")
- **UserEvent table:** sharded by `user_id` with time-based partitioning (the most common query is "list events for user_id in the last 30 days")

**The replication strategy:**

- **Primary + 1 read replica per shard** (survive 1 shard failure)
- **Replication:** synchronous (for strong consistency) or asynchronous (for low latency)

**The cross-shard query strategy:**

- **For "list all tenants with > 1000 users":** denormalize into a read store (Elasticsearch) with a daily batch job
- **For "count events across all users":** use a streaming aggregation (Kafka + Flink) with a 1-hour window

**The data model (3-5 tables per shard):**

```
users (per shard, sharded by tenant_id) (
  id BIGSERIAL PRIMARY KEY,
  tenant_id INT NOT NULL,
  email VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE(tenant_id, email)
)

user_profiles (per shard, sharded by user_id) (
  user_id BIGINT PRIMARY KEY,
  profile_data JSONB NOT NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
)

user_events (per shard, sharded by user_id, partitioned by month) (
  id BIGSERIAL,
  user_id BIGINT NOT NULL,
  event_type VARCHAR(50) NOT NULL,
  event_data JSONB,
  timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
  PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);

tenants (replicated, not sharded) (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  plan VARCHAR(50) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
)
```

**The scale model:**

- **QPS:** 10K reads/sec (sharded: 1K reads/sec per shard across 10 shards); 100 writes/sec
- **Storage:** 1TB total (100GB per shard across 10 shards)
- **Bandwidth:** 10K QPS × 1KB = 10MB/sec
- **Cost:** $1000/month (10 shards × $50 + 10 read replicas × $30 + Elasticsearch $200 + Kafka $100 + S3 $100)

### Step 4: Tradeoffs (5-7 minutes)

**The 3 tradeoffs:**

1. **Hash-based sharding vs range-based sharding.** Hash-based is even distribution but no range queries. Range-based is uneven (hot keys) but supports range queries. Pick hash-based for user_id (even distribution); pick range-based for timestamp (range queries).
2. **Synchronous replication vs asynchronous replication.** Synchronous is strong consistency but higher latency. Asynchronous is low latency but eventual consistency. Pick synchronous for the primary (strong consistency); pick asynchronous for the read replica (low latency).
3. **Elasticsearch for cross-shard queries vs denormalize into Postgres.** Elasticsearch is more flexible but adds operational complexity. Denormalize is simpler but limited. Pick Elasticsearch for ad-hoc queries; pick denormalize for known queries.

**The closing line:** "For 10K tenants with 10M users at 1TB, I'd use Postgres sharded by tenant_id (10 shards × 100GB), with 1 read replica per shard for failure survival, Elasticsearch for cross-shard queries, and Kafka + Flink for streaming aggregations. The cost is $1000/month, under the $1000/month ceiling. The failure mode is shard death; the fallback is the read replica with a 5s timeout."

---

## The 5 most common distributed storage questions

The 5 questions that cover 90% of distributed storage system design:

1. **"Design a multi-tenant user data store"** — covered by the canonical example above.
2. **"Design a time-series database"** — same pattern, with time-based partitioning + downsampling.
3. **"Design a sharded Postgres for 1TB+"** — same pattern, with hash-based sharding + read replicas.
4. **"Design a Cassandra-style wide-column store"** — same pattern, with consistent hashing + eventual consistency.
5. **"Design a DynamoDB-style key-value store"** — same pattern, with consistent hashing + quorum reads/writes.

**The pattern:** distributed storage = sharding (hash/range) + replication (primary + replica) + cross-shard query strategy (denormalize/Elasticsearch) + failure handling (read replica). The variations are the sharding key (tenant_id vs user_id vs timestamp), the consistency model (strong vs eventual), and the cross-shard query strategy (denormalize vs Elasticsearch).

---

## The 5 anti-patterns for distributed storage

1. **Naming a technology in the first 5 minutes.** The framework says: clarify, decompose, design, tradeoffs. The technology comes in step 3.
2. **Skipping the sharding key choice.** The candidate who doesn't justify the sharding key is signaling they don't understand the data access patterns.
3. **Skipping the cross-shard query strategy.** The candidate who doesn't address cross-shard queries is signaling they haven't thought about the read patterns.
4. **Skipping the failure mode.** The candidate who doesn't mention shard death + read replica fallback is signaling they don't operate the system.
5. **Skipping the cost calculation.** "It would cost $X/month" without the math is hand-waving. The cost model is the FDE signal.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "How do you rebalance shards?" | "Consistent hashing minimizes rebalancing. For range-based, use virtual nodes. For hash-based, use a coordinator service to map keys to shards." |
| 2. "How do you handle a hot tenant?" | "Split the tenant across multiple shards (per-tenant sharding). Or use a separate read replica for the hot tenant." |
| 3. "How do you survive 2 simultaneous shard failures?" | "Add 2 read replicas per shard (3 total). Use Raft consensus for the primary. Cost: 3x storage + 3x compute." |

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../decomposition/README.md` | The 4-step framework (clarify → decompose → design → tradeoffs) |
| `../swe-coding/04-trees-graphs.md` | The DFS / BFS patterns (for cross-shard queries) |
| `../system-design/README.md` | The 9 patterns cheat sheet (Pattern 4: distributed storage) |

---

## The thesis

**Distributed storage is the fourth most common system design pattern.** The candidate who names the sharding key AND the cross-shard query strategy AND the failure mode — is showing they can own a distributed system.

**The 4-step framework (clarify → decompose → design → tradeoffs) is the muscle memory.** The 5 worked examples (multi-tenant, time-series, sharded Postgres, Cassandra, DynamoDB) are the patterns. Practice them out loud, time yourself at 60 minutes per question, and rehearse with an AI assistant.

**General prep gets you past the resume screen. System design prep gets you past the centerpiece round at Anthropic, OpenAI, AWS FDE, Databricks, and Scale AI.**