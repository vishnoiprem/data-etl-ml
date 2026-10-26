# Concepts Map — which system demonstrates which idea

> Cross-reference: appendix concepts vs. modules. Use this when
> studying a single concept (e.g. caching) and want to see it
> implemented end-to-end.

| Concept | Modules |
|---|---|
| **Caching** | URL Shortener, Typeahead, YouTube, Instagram, Reddit |
| **CDN / Edge** | YouTube, Netflix, TikTok, Twitch |
| **Sharding** | KV Store, Distributed LRU, S3 Storage, Message Queue |
| **Replication** | KV Store, Message Queue, Distributed Storage |
| **Consistent hashing** | Distributed LRU, KV Store, Dropbox |
| **Pub/Sub** | Message Queue, Webhooks, Async Jobs |
| **Fanout (write)** | Twitter, Instagram, Newsfeed, Slack |
| **Fanout (read)** | Newsfeed, Reddit (homepage) |
| **Hybrid fanout** | Twitter (celebrities), Newsfeed (ranker fallback) |
| **Rate limiting** | Rate Limiter + used as a library in many |
| **Idempotency** | Webhooks, URL Shortener (alias), Job Scheduler |
| **Exactly-once / at-least-once** | Message Queue, Webhooks |
| **Batching** | LLM Batching, Metrics, Job Scheduler |
| **Circuit breaker** | Weather App |
| **CRDT / OT-lite** | Google Docs |
| **WebSocket / SSE** | Messenger, WhatsApp, ChatGPT, Voice AI, Twitch chat |
| **Long polling** | Messenger, Notifications |
| **Ranking** | Newsfeed, Reddit hot-score, TikTok For You |
| **RAG** | AI Support |
| **Agent loops** | Claude Code |
| **Streaming** | ChatGPT, Voice AI |
| **Multipart upload** | File Uploader, Dropbox |
| **Content-addressed storage** | Dropbox (chunked, dedup), S3 (ETag) |
| **Distributed locks** | Ticketmaster, Hotel Booking, Parking Garage, Job Scheduler |
| **State machine** | Uber Eats (order), Doc Processing, Chess, User Data Export |
| **CRUD + REST** | Every module |
| **Microservices** | (Course meta: each system is its own service) |
| **Observability** | Every module (metrics + health) |
| **Backpressure** | Message Queue, Rate Limiter |
| **At-least-once delivery** | Message Queue, Webhooks |
| **End-to-end encryption (concept)** | WhatsApp |
| **OAuth / token auth (concept)** | Messenger, Slack, AI Support |
| **Eventual consistency** | Instagram (feed), Reddit (votes), Twitter (timeline) |
| **Strong consistency** | Ticketmaster (seats), Hotel Booking, Parking Garage |
| **Saga / 2PC (concept)** | Uber Eats (order state machine as mini-saga) |
| **Bloom filter** | URL Shortener (optional extension), Web Crawler (URL dedup) |
| **Trie / FST** | Typeahead |
| **Sliding window** | Rate Limiter, Metrics, YouTube trending |
| **Token bucket** | Rate Limiter |
| **Hot key mitigation** | URL Shortener (coalescing), Twitter (celebrity) |
| **Graceful degradation** | Newsfeed (ranker down → chrono), YouTube (CDN miss) |
| **Read replica** | URL Shortener, Instagram, YouTube |
| **Write-ahead log** | Message Queue (log per partition) |
| **Leader election (concept)** | Message Queue (per-partition leader), Job Scheduler |
| **Multi-AZ / multi-region** | (Course-level concept, covered in design docs) |
| **Cache stampede protection** | URL Shortener, Typeahead |
| **Lazy loading** | Instagram, Twitter |
| **Eager loading** | Instagram (fanout-on-write) |

This isn't exhaustive — the point is that the same ~30 concepts
show up across many systems. **Master the concept once, apply it
everywhere.**
