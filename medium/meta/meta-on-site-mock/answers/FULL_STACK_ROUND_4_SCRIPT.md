# Round 4: Full Stack — RAG Trace Reviewer Tool
## The 60-Minute Spoken Answer (with code, timing, and what to say out loud)

**Today's interview prep.** The framework you pasted is the structure. This file is the words.

---

## 0-8 min: API contract (write this on the whiteboard first)

### What to say (90 seconds, no notes)

> "Before I write any code, I want to lock the API contract. The reason: every design decision downstream depends on this — the SQL index, the React cache key, the optimistic update path. If I get the contract wrong, I rewrite everything.
>
> The endpoint is `GET /traces`. The query parameters are: `day`, `prompt_version`, `min_latency_ms`, `max_latency_ms`, `limit`, and `cursor`. I'll sort by `created_at DESC, trace_id DESC` — the secondary key on `trace_id` is what makes pagination stable when multiple traces have the same timestamp.
>
> Filters are server-side because they affect the full dataset, not just the currently loaded page. If I filtered client-side, the user would only see what's in their viewport, which is wrong.
>
> The cursor is opaque, base64-encoded JSON. The client should never parse it. That gives me the freedom to change the pagination scheme later — switch to `(score, trace_id)` for relevance-sorted views — without breaking clients."

### What to draw on the whiteboard

```
GET /traces
  ?day=2026-10-17
  &prompt_version=v2
  &min_latency_ms=200
  &max_latency_ms=1000
  &limit=50
  &cursor=eyJjcmVhdGVkX2F0IjoiLi4uIiwidHJhY2VfaWQiOiIuLi4ifQ==

Response:
{
  "items": [
    {
      "trace_id": "tr_1001",
      "created_at": "2026-10-17T09:00:00Z",
      "prompt_version": "v2",
      "latency_ms": 420,
      "feedback": "up"
    }
  ],
  "next_cursor": "opaque_cursor",
  "has_more": true
}
```

### The SQL (write this on the second whiteboard panel)

```sql
SELECT
    trace_id,
    created_at,
    prompt_version,
    latency_ms,
    feedback
FROM rag_traces
WHERE created_at >= :day_start
  AND created_at < :day_end
  AND (:prompt_version IS NULL OR prompt_version = :prompt_version)
  AND (:min_latency IS NULL OR latency_ms >= :min_latency)
  AND (:max_latency IS NULL OR latency_ms <= :max_latency)
  AND (
      :cursor_created_at IS NULL
      OR created_at < :cursor_created_at
      OR (
          created_at = :cursor_created_at
          AND trace_id < :cursor_trace_id
      )
  )
ORDER BY created_at DESC, trace_id DESC
LIMIT :limit_plus_one;

CREATE INDEX idx_trace_page
ON rag_traces(created_at DESC, trace_id DESC);
```

### The OFFSET vs cursor line (use this verbatim)

> "Why not OFFSET? Two reasons. First, performance: OFFSET becomes progressively more expensive because the database still has to walk past skipped rows. With keyset pagination, every page is an indexed lookup, O(log N) instead of O(N). Second, stability: when new rows arrive between requests, OFFSET shifts the page boundary — a row that was on page 1 last fetch might be on page 2 this fetch. Keyset uses the last seen sort key, so boundaries are stable."

### The `limit + 1` trick (mention this even if they don't ask)

> "I fetch `limit + 1` rows. If I get 51 for a limit of 50, I know `has_more = true` and the 51st row's `(created_at, trace_id)` becomes my next cursor. No separate COUNT query needed."

---

## 8-25 min: React table + virtualization

### What to say (60 seconds)

> "For 1,000 logical rows I don't need 1,000 DOM nodes. Each `<tr>` is ~5KB of layout. 1,000 rows = 5MB. React's reconciliation churns. Scrolling stutters.
>
> I'll use `react-window` or TanStack Virtual. The principle: render only what's visible in the viewport plus a small overscan buffer — about 10 rows above and below. For a viewport showing 20 rows, I render ~40. DOM cost goes from 5MB to 200KB.
>
> The L6 sentence: virtualization optimizes DOM rendering. It does not reduce API payload size, so I still paginate from the backend. The two are different concerns."

### The code (live, on the laptop)

```tsx
import { FixedSizeList, ListChildComponentProps } from "react-window";

type Trace = {
  trace_id: string;
  created_at: string;
  prompt_version: string;
  latency_ms: number;
  feedback?: "up" | "down" | null;
};

const Row = ({ index, style, data }: ListChildComponentProps) => (
  <div style={style}>
    <TraceRow trace={data[index]} onFeedback={...} />
  </div>
);

<FixedSizeList
  height={600}
  itemCount={rows.length}
  itemSize={48}
  itemData={rows}
  overscanCount={10}
>
  {Row}
</FixedSizeList>
```

### Data fetching with infinite query

```tsx
const tracesQuery = useInfiniteQuery({
  queryKey: ["traces", filters],
  queryFn: async ({ pageParam }) => {
    const params = new URLSearchParams();
    params.set("day", filters.day);
    if (filters.promptVersion) params.set("prompt_version", filters.promptVersion);
    if (filters.minLatency) params.set("min_latency_ms", filters.minLatency);
    if (filters.maxLatency) params.set("max_latency_ms", filters.maxLatency);
    if (pageParam) params.set("cursor", pageParam);

    const res = await fetch(`/api/traces?${params}`);
    if (!res.ok) throw new Error("Failed to load traces");
    return res.json();
  },
  initialPageParam: null as string | null,
  getNextPageParam: lastPage =>
    lastPage.has_more ? lastPage.next_cursor : undefined,
});

const rows = tracesQuery.data?.pages.flatMap(page => page.items) ?? [];
```

### The infinite scroll trigger (the part most candidates forget)

```tsx
const Row = ({ index, style, data }) => {
  const isLast = index === data.length - 1;
  useEffect(() => {
    if (isLast && tracesQuery.hasNextPage && !tracesQuery.isFetchingNextPage) {
      tracesQuery.fetchNextPage();
    }
  }, [isLast]);
  return <div style={style}>...</div>;
};
```

---

## 25-35 min: filters

### What to say (60 seconds, three rules)

> "Three rules for filters.
>
> First, filters belong in the query key. So `queryKey: ['traces', filters]`. When `filters` changes, TanStack Query sees a new key and refetches from page 1. The cursor state is automatically dropped because the `useInfiniteQuery` hook re-initializes when the key changes.
>
> Second, debounce text-like filters. Dropdowns like prompt version can refetch immediately. The user has explicitly chosen a value — they're not typing.
>
> Third, when filters change, cursor state must reset. That's automatic with the query key pattern, but I'll mention it explicitly so the interviewer knows I thought about it."

### The debounce pattern

```tsx
const [draft, setDraft] = useState("");
const [applied, setApplied] = useState("");

useEffect(() => {
  const t = setTimeout(() => setApplied(draft), 300);
  return () => clearTimeout(t);
}, [draft]);
```

> "Draft updates on every keystroke. Applied updates 300ms after the last keystroke. The `filters` object uses `applied`. Result: one API call per typing burst, not one per keystroke."

---

## 35-48 min: optimistic feedback (the L6 moment)

### What to say (45 seconds)

> "User clicks thumbs up. Do I wait for the backend?
>
> No. I update the UI optimistically, send the mutation in the background, and rollback if it fails. The five steps are: cancel stale reads, snapshot previous state, update cache immediately, rollback on error, then reconcile with the server."

### The full code (write this on the laptop, not whiteboard)

```tsx
const feedbackMutation = useMutation({
  mutationFn: async ({ traceId, rating }: {
    traceId: string; rating: "up" | "down";
  }) => {
    const res = await fetch(`/api/traces/${traceId}/feedback`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rating }),
    });
    if (!res.ok) throw new Error("Feedback failed");
    return res.json();
  },

  onMutate: async ({ traceId, rating }) => {
    // 1. Cancel any in-flight refetch
    await queryClient.cancelQueries({ queryKey: ["traces"] });

    // 2. Snapshot current state
    const previous = queryClient.getQueriesData({ queryKey: ["traces"] });

    // 3. Optimistic update
    queryClient.setQueriesData(
      { queryKey: ["traces"] },
      (old: any) => old ? {
        ...old,
        pages: old.pages.map((page: any) => ({
          ...page,
          items: page.items.map((trace: Trace) =>
            trace.trace_id === traceId
              ? { ...trace, feedback: rating }
              : trace
          ),
        })),
      } : old
    );

    return { previous };
  },

  onError: (_err, _vars, context) => {
    // 4. Rollback
    context?.previous.forEach(([key, data]) => {
      queryClient.setQueryData(key, data);
    });
  },

  onSettled: () => {
    // 5. Reconcile
    queryClient.invalidateQueries({ queryKey: ["traces"] });
  },
});
```

### The follow-up they will ask: "What if the user clicks up, then down, quickly?"

> "I need to avoid stale mutation responses overwriting newer intent. Three options:
>
> First, serialize feedback mutations per trace. A `Map<traceId, Promise>` chains mutations for the same trace. The second click waits for the first to settle before firing.
>
> Second, attach a client sequence number. The server rejects older writes.
>
> Third, idempotent upsert with a last-write-version field. The server stores the version and rejects any write with a version older than what's stored.
>
> The simplest is option one — a per-trace mutex. I mention the others to show I considered the trade-offs."

---

## 48-55 min: detail drawer

### What to say (45 seconds)

> "I would not load all detail payloads in the list endpoint. The table returns lightweight row data — id, timestamp, prompt version, latency, feedback status. The full prompt, retrieved chunks, evidence JSON, model response, latency breakdown, and token usage load only when the user opens the detail drawer.
>
> This is an important full-stack performance decision. A list endpoint with 50 rows of detail data is 50x the payload of a list with 50 rows of summary data. Most of the time, the user is scrolling, not opening detail. Don't pay the cost upfront."

### The code

```tsx
const [openTraceId, setOpenTraceId] = useState<string | null>(null);

const detailQuery = useQuery({
  queryKey: ["trace", openTraceId],
  queryFn: async () => {
    const res = await fetch(`/api/traces/${openTraceId}`);
    return res.json();
  },
  enabled: openTraceId !== null,    // only fetch when drawer is open
});
```

### The detail panel contents (mention, don't write)

The detail view shows:

- Trace ID, user query
- Prompt version + template hash
- Retrieved chunks with similarity scores
- Evidence JSON (the L6 sentence: "the tool surfaces groundedness, not just feedback")
- Model response
- Latency breakdown (preprocess / retrieve / rerank / generate / postprocess)
- Token usage + cost
- Feedback history
- Grounded / validation status

> "The detail view is also where engineers do their actual work. The table is the entry point. The detail view is where they read the response, check the retrieved evidence, and decide if the model was grounded. This is the panel that turns a feedback tool into a **gold-set generation tool** for offline eval."

### The corrected-answer correction (L6 line, use this)

> "One thing I want to be careful about: thumbs down alone does not create gold truth. Human-reviewed feedback can become candidate evaluation data **after quality checks** — at least one additional reviewer confirming the corrected answer is actually correct. We don't want a model trained on wrong labels."

---

## 55-60 min: production readiness (5 minutes, no code)

### What to say (60 seconds, list only)

> "I'd make four things production-ready:
>
> First, pagination and indexes for backend performance. The keyset index I drew earlier handles 1B rows at 50ms p95.
>
> Second, virtualization so rendering stays smooth. We covered that.
>
> Third, optimistic updates with rollback and race handling. We covered that.
>
> Fourth, clear loading, empty, error, retry, and permission states. The empty state matters more than people think — 'no traces match these filters' is different from 'no traces yet'.
>
> Tests: API tests for cursor boundaries and filter combinations, React tests for optimistic rollback, an end-to-end Playwright test for the full review flow."

---

## The 8-step memory hook (memorize this)

```
API → Cursor → Virtualize → Filter → Optimistic → Rollback → Detail → Test
```

If you can code and explain those eight cleanly, you're in very good shape.

---

## The closing line (use this verbatim, then stop)

> "The design is cursor pagination for stable, indexed access; virtualization for 1,000-row rendering performance; server-side filters with proper query-key invalidation; optimistic updates with snapshot rollback and per-trace mutation serialization; lazy-loaded detail drawer; and explicit empty, error, and loading states. The tool doubles as a gold-set generator for offline eval, which is where the long-term value lives."

Then stop. Let them drill in. They will pick one of:
- Race conditions (you covered it: per-trace mutex)
- Filter performance (you covered it: query key)
- What happens when the cache is stale (you covered it: onSettled reconciliation)
- Permission states (mention RBAC, server-side filter, audit log)

---

## Pre-interview checklist (do this in the next hour)

1. **Read this file out loud once.** Not to memorize — to hear your own voice saying the words.
2. **Open the repo, run `python3 build_notebook.py` once.** Confirm the cells still execute.
3. **Practice the 8-step hook three times in front of a mirror.** API → Cursor → Virtualize → Filter → Optimistic → Rollback → Detail → Test. The hook is your lifeline if your mind goes blank.
4. **Re-read the per-trace mutex answer.** It's the one follow-up that catches candidates cold.

---

## What this file is NOT

This is not a script to recite. Reciting gets you 6/10. The L6 wins the room by **naming the trade-offs the interviewer hasn't heard yet** — opaque cursors, per-trace mutex, query-key invalidation, the corrected-answer quality bar. These are the sentences that signal "I've built this before."

Practice the structure. Speak the trade-offs. The code is the proof.
