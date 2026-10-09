# Appendix: System Design Concepts

> **Lessons 1-18 of Appendix · 18 lessons · 2 videos · ~2 hours**

A reference library of the must-know concepts that show up across every
system design interview. Read these alongside the modules — they are
the *vocabulary* the modules use.

| # | Concept | Where it's used in this course |
|---|---|---|
| 1 | System Design Glossary | every module |
| 2 | Top Engineering Blogs | reading list |
| 3 | Caching | URL Shortener, Typeahead, YouTube, Rate Limiter |
| 4 | CDNs | YouTube, Netflix, TikTok, Twitch |
| 5 | Web Protocol Questions | every module |
| 6 | APIs | every module |
| 7 | Load Balancing | URL Shortener, Instagram, Twitter |
| 8 | CAP Theorem | KV Store, Message Queue, Dropbox |
| 9 | SQL vs NoSQL | every module |
| 10 | Database Sharding | KV Store, Distributed LRU, S3 |
| 11 | Replication | KV Store, Message Queue, Dropbox |
| 12 | Consistent Hashing | Distributed LRU, KV Store, Dropbox |
| 13 | Asynchronous Processing | Webhooks, Job Scheduler, Crawler, Export |
| 14 | Encryption | WhatsApp, Dropbox |
| 15 | Authentication & Authorization | every module |
| 16 | Cloud Architecture | every module |
| 17 | Availability | every module |
| 18 | Reliability | every module |

Each concept below is a 5-minute read. They are dense on purpose — the
goal is to give you a working mental model, not a textbook.

---

## 1. System Design Glossary

| Term | Meaning |
|---|---|
| **QPS** | Queries per second. |
| **RPS** | Requests per second. Same as QPS for HTTP. |
| **p50 / p95 / p99** | Latency percentiles — 50% / 95% / 99% of requests are faster. |
| **SLO / SLA** | Service-level objective / agreement. E.g. "p99 < 200ms". |
| **Hot key** | A key receiving disproportionate traffic. |
| **Backpressure** | Telling upstream to slow down. |
| **Fanout** | Spreading one write to many destinations. |
| **Idempotency** | Same operation twice = same effect as once. |
| **Quorum** | Majority of replicas agree. |
| **TTL** | Time-to-live; how long cached data stays valid. |
| **Cascade failure** | One component's failure triggers others' failure. |
| **Back-of-envelope** | A rough estimate done in your head. |
| **Hot path** | The most performance-critical code path. |
| **Cold storage** | Slow, cheap storage for rarely-accessed data. |
| **Cold start** | Time for a serverless / new node to be ready. |

---

## 2. Top Engineering Blogs

These are the blogs that publish the most useful system design
post-mortems. Read them; they are the de-facto interview prep.

- **High Scalability** — case studies of large systems
- **The Morning Paper** — paper summaries by Adrian Colyer
- **AWS Architecture Blog** — real workloads, deep dives
- **Netflix Tech Blog** — chaos engineering, streaming
- **Uber Engineering** — geospatial, marketplace
- **Stripe Engineering** — payments, idempotency
- **Discord Engineering** — real-time at scale
- **Cloudflare Blog** — edge, security
- **Dropbox Tech** — sync, dedup
- **GitHub Engineering** — code hosting at scale
- **Papers We Love** — distributed systems papers
- **Designing Data-Intensive Applications** (book) — the bible

---

## 3. Caching

The single biggest performance lever. Read once, apply everywhere.

- **Where to cache**: in-memory (LRU), Redis/Memcached (distributed),
  CDN (geographic), browser.
- **Cache invalidation**: TTL, write-through, event-driven
  invalidation, cache-aside.
- **Stampede protection**: lock + single-flight on miss; serve stale
  while revalidating.
- **Negative caching**: cache "not found" for a short TTL.
- **Locality**: pin hot data to the same shard/region as the requester.

Used in: URL Shortener, Typeahead, YouTube, Rate Limiter.

---

## 4. CDNs

Content Delivery Networks put content close to users.

- **Pull CDN**: edge fetches from origin on first request, then caches.
- **Push CDN**: you upload to CDN; origin is bypassed.
- **Cache key**: usually full URL including query string.
- **Cache invalidation**: purge by URL, prefix, or tag.
- **Origin shield**: an extra hop in front of origin to absorb stampedes.

Used in: YouTube, Netflix, TikTok, Twitch.

---

## 5. Web Protocol Questions

Interviewers may ask "what happens when you type google.com?"

1. Browser parses URL.
2. Browser checks cache, OS cache, router cache, ISP cache for IP.
3. DNS lookup: resolver → root → TLD → authoritative.
4. TCP handshake (SYN, SYN-ACK, ACK).
5. TLS handshake (ClientHello, ServerHello, certificate verify,
   key exchange).
6. HTTP request sent.
7. Server processes, returns response.
8. Browser parses, renders, executes scripts.

Know the timing budgets and where latency is added.

---

## 6. APIs

| Style | Pros | Cons |
|---|---|---|
| **REST** | simple, cacheable, well-understood | over/under-fetching, chatty |
| **GraphQL** | flexible, one endpoint | complexity, caching, N+1 |
| **gRPC** | fast, schema, streaming | not human-readable |
| **WebSocket** | bidirectional, low overhead | stateful, hard to scale |
| **SSE** | server-push, simple | one-way, no IE |

Stateful vs stateless: prefer stateless for horizontal scaling. Cookies
vs tokens: tokens (JWT) for APIs.

---

## 7. Load Balancing

L4 (TCP) vs L7 (HTTP). L7 can do path-based routing, header rewriting,
WAF.

Algorithms: round-robin, least-connections, consistent-hash, weighted,
power-of-two-choices.

Health checks: active (ping) vs passive (track 5xx rate).

Used in: URL Shortener, Instagram, Twitter.

---

## 8. CAP Theorem

In a distributed system during a network partition, you choose
**Consistency** or **Availability**. (Every system has Partition
tolerance — that's the assumption.)

- **CP** (consistency): MongoDB, HBase, etcd. Refuse writes if can't
  reach quorum.
- **AP** (availability): Cassandra, DynamoDB, Riak. Accept writes;
  reconcile later.
- **CA** (no partition): single-node systems; not realistic at scale.

Don't conflate CAP with ACID.

---

## 9. SQL vs NoSQL

| | SQL | NoSQL |
|---|---|---|
| Schema | rigid | flexible |
| Scaling | vertical, then sharding | horizontal native |
| Joins | yes | usually no |
| Transactions | ACID | eventual / per-row |
| Examples | Postgres, MySQL | Cassandra, MongoDB, DynamoDB |

Rule of thumb: start with Postgres. Move to NoSQL when you have
specific reasons (keyspace, write volume, schema flexibility).

---

## 10. Database Sharding

Split one logical DB into N physical DBs.

- **Shard key**: the field used to route (e.g. `user_id`).
- **Strategies**: range, hash, directory.
- **Hot shard**: a single shard gets all the traffic. Avoid with
  good key choice or virtual shards.
- **Cross-shard queries**: expensive; design schema to avoid them.
- **Resharding**: hard. Pre-shard with more shards than you need.

Used in: KV Store, Distributed LRU, S3.

---

## 11. Replication

Copy data across nodes.

- **Synchronous**: write waits for replicas. Strong consistency, higher
  latency.
- **Asynchronous**: write hits primary, replicates later. Faster, but
  possible data loss on primary failure.
- **Multi-leader**: write to any replica, conflicts resolved later.
  Good for geo.
- **Leaderless** (Dynamo-style): any replica accepts writes; reads need
  R of W replicas to agree.

---

## 12. Consistent Hashing

A hashing scheme where adding/removing a node moves ~1/N of keys
(rather than most of them).

- Hash nodes and keys onto a ring.
- Each key belongs to the next N nodes clockwise (N = replication
  factor).
- Virtual nodes per physical node smooth out the distribution.

Used in: Distributed LRU, KV Store, Dropbox, Cassandra, DynamoDB.

---

## 13. Asynchronous Processing

Decouple request time from work time.

- **Queues**: SQS, Kafka, RabbitMQ. Producer puts; consumer pulls.
- **Pub/Sub**: one event, many subscribers. Kafka topics, SNS, Pub/Sub.
- **Streams**: ordered, replayable log. Kafka, Kinesis.
- **Workers**: long-running processes that consume queues.
- **Idempotency**: required because retries happen.

Used in: Webhooks, Job Scheduler, Crawler, Export, Doc Processing.

---

## 14. Encryption

- **In transit**: TLS (HTTPS, mTLS for service-to-service).
- **At rest**: disk-level encryption (LUKS, AWS EBS) + per-record
  encryption for sensitive fields.
- **End-to-end**: only sender and receiver can decrypt. WhatsApp
  Signal protocol. Keys negotiated out-of-band.
- **Key management**: HSMs, KMS. Rotate regularly.
- **Hashing vs encryption**: hashing is one-way (passwords); encryption
  is two-way.

---

## 15. Authentication & Authorization

- **Authentication (AuthN)**: who are you? (password, OAuth, SAML,
  WebAuthn)
- **Authorization (AuthZ)**: what can you do? (RBAC, ABAC, scopes)
- **Tokens**: JWT (stateless, signed), opaque session tokens (stateful,
  revocable).
- **OAuth 2.0**: delegated auth. OIDC = OAuth + identity.
- **mTLS**: certificates as identity for service-to-service.

---

## 16. Cloud Architecture

- **Regions & AZs**: deploy across AZs for HA; regions for DR.
- **VPC / subnets**: network isolation.
- **Managed services**: prefer them for stateful infra (DBs, queues);
  build for stateless logic.
- **Cost**: data egress, idle resources, over-provisioned DBs.
- **12-factor app**: stateless processes, config in env, logs as event
  streams, disposability.

---

## 17. Availability

Availability = Uptime / (Uptime + Downtime). "Five 9s" = 99.999% = 5
min/year downtime.

- **Redundancy**: no single point of failure.
- **Failover**: active-passive (slow failover, simple) vs
  active-active (no failover, complex).
- **Graceful degradation**: serve a reduced experience when
  components fail.
- **Health checks**: liveness (restart me if I fail) vs readiness
  (route traffic to me only if I'm ready).

---

## 18. Reliability

A reliable system stays correct under failure.

- **Idempotency**: retries are safe.
- **Retries with backoff**: exponential + jitter.
- **Circuit breakers**: stop calling a failing dependency; recover
  after a cooldown.
- **Bulkheads**: isolate pools so one slow dep doesn't exhaust all
  threads.
- **Timeouts**: every network call needs a timeout. Always.
- **Chaos engineering**: Netflix's Chaos Monkey; randomly kill things
  to find weaknesses.
- **Observability**: metrics, logs, traces. If you can't see it, you
  can't fix it.
