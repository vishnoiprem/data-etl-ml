# 32 — Twitch-style Live Streaming + Chat

> **Lesson 32 of the System Design course — Media Streaming & Content Delivery**

A working design + implementation of a Twitch-style live-streaming
service: start/end a live stream, browse by game, post and read
chat, and consume chat over **Server-Sent Events**. Viewer count
is tracked via heartbeat — a viewer is "live" while their last
heartbeat is within the timeout window.

The video *bytes* path is out of scope; the same CDN/edge story
from the YouTube/Netflix lesson applies (HLS segments, low-latency
LL-HLS for sub-second glass-to-glass). The interesting design
question for Twitch is the **chat fanout**: how do you deliver a
chat message to 100 K concurrent subscribers in well under a
second, across many shards.

---

## 1. Requirements

### Functional
- **Create user**.
- **Start a stream** (`user_id`, `title`, `game`).
- **End a stream**.
- **Get a stream** (metadata + current viewer count).
- **List streams** (optionally filtered by `game`, by live state).
- **Post a chat message** to a live stream.
- **Get chat log** for a stream (recent N messages).
- **Subscribe to chat** over Server-Sent Events (SSE).
- **Viewer heartbeat** → live viewer count.

### Non-functional
- **Live viewer count** must reflect changes within `HEARTBEAT_TIMEOUT_S`
  (default 30s). A viewer who stops heartbeating drops off the count.
- **Chat fanout** must deliver a posted message to all subscribers
  in well under a second.
- **Read-heavy** with extreme fanout: 1 broadcaster, 100 K viewers,
  ~50 chat/sec across the stream.
- **Eventual consistency** for chat log and viewer count is fine —
  we don't need cross-shard linearizability for either.

### Out of scope
- Video *bytes* (assumed served by HLS/LL-HLS through a CDN).
- Real-time transcoding, ABR ladder, DVR.
- Authentication, follows, subscriptions, donations, ads.
- Moderation, bans, rate limits — production would have all of
  these; we model the data path only.

---

## 2. Capacity estimation

| Metric | Value |
|---|---|
| DAU | 35 M |
| Concurrent viewers (peak) | 6 M |
| Concurrent live streams (peak) | 100 K |
| Chat messages / day | 30 B → ~350 K /sec avg, ~3 M /sec peak |
| Subscribers per stream (top streams) | 100 K+ |
| Heartbeats / day | 500 B → ~6 M /sec avg, ~30 M /sec peak |
| Stream metadata per stream | ~500 B |
| Chat retention | 30 days, then archived |

The lesson: viewer count and chat are *hot* (write-heavy at peak),
and chat fanout is the dominant cost. A 100 K-subscriber stream
that pushes 50 chat/sec is moving 5 M push events / sec through
its fanout layer. The right design shards by stream_id and runs
a long-lived subscriber per shard.

---

## 3. High-level design

```
   viewer ──►  ┌────────────────────────────────────────────┐
                │  Ingest edge (WebSocket / HTTP)            │
                └────┬───────────┬─────────────┬────────────┘
                     │           │             │
                     │ heartbeat │ GET chat    │ SSE chat
                     ▼           ▼             ▼
                ┌────────┐  ┌──────────┐  ┌─────────────────┐
                │Viewer  │  │ Chat log │  │ Chat fanout     │
                │ service│  │ (KV log) │  │ (pub/sub)       │
                │(hb+ts) │  │          │  │ stream_id → sub │
                └────┬───┘  └────┬─────┘  └────┬────────────┘
                     │           │             │
                     └───────────┴─────────────┘
                                 │
                          ┌──────▼──────┐
                          │ Stream meta │
                          │  (KV)       │
                          └──────┬──────┘
                                 │
                          ┌──────▼──────┐
                          │ Game index  │
                          │ game → [s]  │
                          └─────────────┘

   broadcaster ──► [ ingest server ] ──► origin / CDN (HLS / LL-HLS)
                     │                          ▲
                     │                          │
                  viewer ──────── CDN edge ──────┘
                              (segments)
```

- **Ingest edge**: receives the broadcaster's RTMP / WHIP stream,
  transcodes, and writes HLS segments to origin. Viewers fetch
  segments from the CDN.
- **App tier**: stateless Flask replicas, one per shard, sharded
  by `stream_id`. The chat fanout layer is co-located with the
  app tier.
- **Stream metadata DB**: sharded KV (KeyValueStore). One record
  per stream.
- **Chat log**: capped per-stream log (10 K messages) in memory
  for low-latency reads; archived to cold storage for replay.
- **Viewer service**: `stream_id → {viewer_id: last_hb_ts}`. A
  periodic evictor removes stale heartbeats; the count is the
  map size.
- **Chat fanout**: an in-process pub/sub keyed by `stream_id`. A
  posted message is pushed to all subscriber queues; SSE handlers
  drain those queues and write `text/event-stream` frames.

---

## 4. API

| Method | Path | Body / Query | Returns |
|---|---|---|---|
| `POST` | `/api/users` | `{"name": "..."}` | `{"user_id": ..., "name": ...}` |
| `POST` | `/api/streams` | `{"user_id": ..., "title": "...", "game": "..."}` | stream metadata |
| `POST` | `/api/streams/<id>/end` | — | updated stream (live: false) |
| `GET`  | `/api/streams/<id>` | — | stream + current viewer count |
| `GET`  | `/api/streams?game=G&include_ended=...` | filter | list of streams |
| `POST` | `/api/streams/<id>/chat` | `{"user_id": ..., "body": "..."}` | chat message |
| `GET`  | `/api/streams/<id>/chat?limit=N` | `?limit=N` | last N chat messages |
| `GET`  | `/api/streams/<id>/chat/sse` | — | SSE stream: `hello`, `chat`, `end` events |
| `POST` | `/api/streams/<id>/heartbeat` | `{"viewer_id": ...}` | `{"viewers": N, "peak_viewers": P}` |
| `GET`  | `/api/streams/<id>/viewers` | — | `{"viewers": N}` |
| `GET`  | `/metrics` | — | counters + histograms |
| `GET`  | `/health` | — | `{"ok": true}` |
| `GET`  | `/` | — | service index |

Notes:
- SSE format follows the spec: `event: <name>\ndata: <json>\n\n`.
  A `: keepalive` comment is sent every 15s when idle.
- `end_stream` sends an `end` SSE event to all subscribers, so
  the client closes the connection cleanly.

---

## 5. Data model

### stream
```
stream:<id> = {
  "stream_id":     int,
  "user_id":       int,           # broadcaster
  "title":         str,
  "game":          str,           # lowercased
  "created_at":    float,
  "ended_at":      float | null,
  "live":          bool,
  "peak_viewers":  int,
}
```

### user
```
user:<id> = {"user_id": int, "name": str, "created_at": float}
```

### chat log (in-memory, capped at 10K)
```
chat:<stream_id> = [
  {"msg_id": int, "stream_id": int, "user_id": int, "body": str, "created_at": float},
  ...
]
```

### viewer map (in-memory, by stream)
```
viewers:<stream_id> = {viewer_id: last_hb_ts, ...}
```

### chat fanout (in-memory, by stream)
```
subs:<stream_id> = {sub_id: queue.Queue, ...}
```

---

## 6. Stream lifecycle

### Start
```
1. Validate (user exists, title and game non-empty).
2. Generate snowflake stream_id.
3. Persist stream record (live: true, ended_at: null).
4. Return metadata.
```

### End
```
1. Load stream, mark live: false, set ended_at.
2. Persist.
3. Close all SSE subscribers for the stream with an `end` event.
4. Return metadata.
```

The subscriber close matters: without it, every viewer is
"connected" forever and the chat fanout queue grows unbounded.

---

## 7. Chat fanout

The dominant cost in Twitch is delivering one chat message to N
subscribers. The path:

```
POST /api/streams/<id>/chat  ──►  service.post_chat()
                                     │
                                     ├─► persist (capped log)
                                     │
                                     └─► _fanout(stream_id, msg)
                                            │
                                            └─► for each subscriber queue:
                                                 q.put_nowait(msg)         # drop on Full
```

The SSE handler does the inverse:

```
GET /api/streams/<id>/chat/sse  ──►  service.subscribe()
                                          │
                                          └─► returns (sub_id, queue.Queue)
                                                    │
        ┌───────────────────────────────────────────┘
        ▼
   loop:
     q.get(timeout=1.0)            # blocks up to 1s
       has message  ──► emit "event: chat\ndata: <json>\n\n"
       {"__end__": T} ──► emit "event: end\ndata: {...}\n\n"; return
       timeout       ──► if 15s passed, emit ": keepalive\n\n"
```

**Key design choices:**

- **Drop on full, not block.** A slow consumer (mobile on bad
  network) cannot backpressure the entire fanout for the stream.
  We drop the message for that subscriber; they'll reconnect and
  re-read the recent log via `GET /chat?limit=100`.
- **15-second keepalive.** Proxies (nginx, Cloudflare) close idle
  connections. A comment-only SSE frame keeps the socket warm.
- **Per-stream subscribe cap (50 K).** Each subscriber holds a
  queue. Without a cap, a single stream can OOM a shard.
- **One fanout layer per process.** In production this maps to
  one shard, so all subscribers of a stream are co-located.
  A viewer is routed to the right shard by `stream_id mod N`.

### What we'd do in production
- Replace the in-process queue with a dedicated broker (Redis
  Streams, Kafka, NATS) per shard.
- The SSE handler is replaced with WebSockets for true
  bidirectional chat (typing indicators, reactions).
- Subscriber caps are enforced by the broker, not the app.

---

## 8. Viewer count via heartbeat

A viewer is "live" if their last heartbeat is within
`HEARTBEAT_TIMEOUT_S` (30s by default). The client sends a
heartbeat every ~5s while watching.

```
heartbeat(stream_id, viewer_id):
  viewers[stream_id][viewer_id] = now
  evict_stale_viewers(stream_id, now)   # drop anyone with ts < now - 30s
  return {viewers: len(...), peak_viewers: ...}
```

`peak_viewers` is the all-time high for the stream — Twitch shows
this next to the live count, and it's a key ranking signal for
the game directory.

### Why heartbeat, not connect/disconnect?
- Mobile viewers have unreliable connections; the WebSocket drops
  silently and never reconnects.
- A poll-based heartbeat from the player tells us "this viewer
  is actually watching *right now*", not "this viewer has a
  page open in a background tab".

### Stale-eviction cost
`evict_stale_viewers` is O(|viewers|) per heartbeat. For 100 K
viewers on a stream at 5s heartbeat intervals that's 20 K
ops/sec just for eviction — fine. For multi-million viewer
streams (a few huge events a year), we'd shard the viewer map
by viewer_id and use a bucketed heartbeat (write to a
`{stream_id, bucket_id, count}` key).

---

## 9. Failure modes

| Failure | What happens | Mitigation |
|---|---|---|
| **Streamer ends stream mid-chat** | All SSE clients see `event: end`; they close. | `end_stream` iterates subscribers, sends sentinel. |
| **SSE client disconnects** | Subscriber queue leaks. | `app.py` finally block calls `unsubscribe`. |
| **Slow SSE consumer** | Subscriber queue fills (max 1000). | `put_nowait` raises `Full` → we drop the message for that subscriber. |
| **Subscriber cap reached** | New SSE connection returns 503. | Stream is too hot for this shard; rebalance. |
| **Heartbeat storm** | Eviction is O(N) per beat. | Bound N with sharded viewer map or bucketed counters. |
| **Chat log fills (10K)** | Oldest messages silently dropped. | Cold archive every 30 days. |
| **Broadcaster's RTMP drops** | Stream stays "live" forever; viewers see frozen video. | Ingest edge pings a "stream_health" key; app evicts if no ping in 60s. |
| **Game index miss** | `?game=foo` returns empty. | Game index is a separate KV; rebuild on schedule. |
| **Single shard hot** (a single huge stream) | One shard sees all viewers/chat. | Shard by `stream_id`; in extreme cases, run multiple replicas and load-balance SSE within the shard. |

---

## 10. Tradeoffs

### SSE vs WebSockets for chat
- **SSE (what we model)**: server-to-client only, works over plain
  HTTP, trivial to debug with `curl`, perfect for chat reads.
- **WebSockets**: bidirectional, lower per-message overhead,
  needed for typing indicators, reactions, follow alerts.

Real Twitch uses WebSockets. We use SSE because it's a single
HTTP call and the lesson is about fanout, not protocol.

### In-process pub/sub vs broker
- **In-process (what we model)**: zero infra, perfect for
  tests and a single shard. Doesn't cross processes.
- **Broker (Redis Streams, Kafka, NATS)**: scales across shards,
  survives a process restart, can replay from offset.

For this course, in-process is right. The replacement story is
a 50-line change in `_fanout` and `subscribe`.

### Drop-on-full vs block-on-full
- **Drop-on-full (what we model)**: never block the producer;
  the slow client reconnects and reads the recent log.
- **Block-on-full**: preserves every message, but a single
  stuck client back-pressures the entire stream.

Drop-on-full is correct for chat. For *DMs* (where every
message matters) you'd want block + durable storage.

### Polling heartbeat vs WebSocket ping
- **HTTP heartbeat (what we model)**: works through any proxy,
  trivial to scale (just a KV write), slightly more bytes.
- **WebSocket ping**: lower overhead, but ties heartbeat to
  the same socket as chat — one connection drops, both fail.

We use HTTP heartbeat so a chat-disconnect doesn't lose the
viewer's "live" status.

### Cap chat log at 10K vs unlimited
- **Capped (what we model)**: bounded memory, the recent
  conversation is always there, old messages are archived.
- **Unlimited**: every chat message is in memory until stream
  ends — multi-day streams OOM the shard.

Cap.

---

## 11. Code map

```
32_twitch/
├── design/README.md            # this file
├── code/
│   ├── __init__.py
│   ├── service.py              # TwitchService (no HTTP, pure logic)
│   └── app.py                  # Flask wrapper (incl. SSE endpoint)
└── tests/
    ├── __init__.py
    ├── test_service.py         # ≥5 unit tests on TwitchService
    └── test_app.py             # ≥4 HTTP tests
```

- `TwitchService` owns: streams, chat logs, viewer map, in-process
  chat pub/sub. Pure Python; takes `KeyValueStore` so persistence
  is swappable.
- `app.py` is the Flask wrapper. All endpoints are thin: parse,
  delegate, return JSON — except the SSE endpoint, which is a
  long-lived generator that drains a subscriber queue and emits
  `text/event-stream` frames.
- The chat fanout layer is in-process. A 50-line swap to
  Redis Streams or NATS would make it horizontally scalable.
- Viewer heartbeats and the in-memory `viewers:<stream_id>` map
  are the source of truth for "live" state.
