---
title: "The 8-Step Framework That Got Me Through Meta L6 Round 4 (Building a RAG Trace Reviewer Tool in 60 Minutes)"
subtitle: "API → Cursor → Virtualize → Filter → Optimistic → Rollback → Detail → Test. The full-stack round is a clock, not a blank canvas."
description: "How to design and ship a working RAG trace reviewer tool in a 60-minute Meta L6 full-stack interview. Cursor pagination, virtualized tables, optimistic feedback, and the 8-step answer structure."
author: "Prem Vishnoi"
date: 2026-10-17
canonical_url: ""
cover_image: "trace_reviewer_8_steps.png"
tags: ["meta", "interview", "full-stack", "react", "data-engineering", "system-design"]
---

# The 8-Step Framework That Got Me Through Meta L6 Round 4 (Building a RAG Trace Reviewer Tool in 60 Minutes)

The Meta L6 Full Stack round isn't a coding challenge. It's a clock. You have 60 minutes. The interviewer is scoring you on **how you spend them**. Spend 15 minutes writing a perfect reducer and you've already lost.

I failed this round once because I tried to design a perfect backend. The second time, I used an 8-step framework. The interviewer said "this is exactly what I was looking for" at minute 12 and spent the rest of the time drilling into the trade-offs I'd already named.

This post is that framework. One question. Eight steps. The full system, with the code that got me 10/10.

## The question

> Build an internal tool to review RAG traces and give thumbs up/down feedback.
>
> **Backend:** `GET /traces?day=&prompt_version=&cursor=&limit=`. Use cursor pagination, not OFFSET.
>
> **Frontend:** React table, virtualized list, filters by prompt version and latency. Handle 1,000+ rows efficiently. Add optimistic feedback updates.
>
> Walk me through your design and then implement the important parts.

Four things they're testing: API design, performance at scale, UI correctness, and the speed of your design phase. Most candidates flounder on the design phase and run out of time before the code.

## The 8-step framework

```
┌─────────────────────────────────────────┐
│  0-8 min:  Clarify + design API         │
│  8-25 min: React table + virtualization │
│  25-35 min: Filters                     │
│  35-48 min: Optimistic feedback         │
│  48-55 min: Detail drawer               │
│  55-60 min: Production readiness        │
└─────────────────────────────────────────┘
```

The order matters. Don't design the perfect filter UI before the API contract. Don't write the optimistic update before the basic table works. **The clock is your enemy. Spend it on the highest-leverage decisions first.**

## 0-8 min: clarify and design the API

Open with the design contract. This is the moment that earns you 10/10 or 6/10.

> "I'll first define the API contract and pagination semantics. I'll sort traces by `created_at DESC, trace_id DESC`. I'll use keyset pagination so the next page starts after the last row of the previous page. Filters should be server-side because prompt version, day, and latency affect the full dataset, not only the currently loaded page."

Then write the contract:

```http
GET /traces
  ?day=2026-10-17
  &prompt_version=v2
  &min_latency_ms=200
  &max_latency_ms=1000
  &limit=50
  &cursor=eyJjcmVhdGVkX2F0IjoiLi4uIiwidHJhY2VfaWQiOiIuLi4ifQ==
```

```json
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

The L6 detail that wins the room: **the cursor is opaque, base64-encoded JSON**. The client should never parse it. That gives you freedom to change the pagination scheme later (e.g., switch to `(score, trace_id)` for relevance-sorted views) without breaking clients.

Then the SQL:

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

The `LIMIT :limit_plus_one` trick: fetch one more than the limit. If you get 51 rows for a limit of 50, you know `has_more = true` and the 51st row's `(created_at, trace_id)` is your next cursor. You don't need a separate COUNT query.

### Why not OFFSET?

> "OFFSET becomes progressively more expensive because the database still has to walk past skipped rows. It is also unstable when new rows arrive between requests — page boundaries shift. Keyset pagination uses the last seen sort key and gives stable pagination with indexed access, O(log N) per page instead of O(N)."

That sentence alone is worth 2 points on the rubric.

## 8-25 min: React table + 1,000 rows

> "For 1,000 logical rows I don't need 1,000 DOM nodes. I'll virtualize the list so only visible rows plus overscan are rendered."

The mistake is rendering all 1,000 rows. Each `<tr>` in the DOM is ~5KB of layout. 1,000 rows = 5MB. React's reconciliation churns. Scrolling stutters. The user notices.

The fix is `react-window` or TanStack Virtual. The principle: render only what's visible in the viewport plus a small overscan buffer (~10 rows above and below). For a viewport that shows 20 rows, you render ~40. DOM cost goes from 5MB to 200KB.

```tsx
import { FixedSizeList } from "react-window";

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

The L6 sentence: **"Virtualization optimizes DOM rendering. It does not reduce API payload size, so I still paginate from the backend."** This shows you understand the difference between network cost and rendering cost.

### Data fetching

Use TanStack Query's `useInfiniteQuery`:

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
```

Flatten the pages for the table:

```tsx
const rows = tracesQuery.data?.pages.flatMap(page => page.items) ?? [];
```

The infinite scroll hook:

```tsx
const Row = ({ index, style, data }) => {
  const isLast = index === data.length - 1;
  const fetchMoreRef = useRef(null);

  useEffect(() => {
    if (isLast && tracesQuery.hasNextPage && !tracesQuery.isFetchingNextPage) {
      tracesQuery.fetchNextPage();
    }
  }, [isLast]);

  return <div ref={fetchMoreRef} style={style}>...</div>;
};
```

## 25-35 min: filters

Three rules. Say them out loud.

> "Filters belong in the query key so changing filters invalidates and refetches the correct dataset. For text-like filters I may debounce. For dropdowns like prompt version I can refetch immediately. When filters change, cursor state must reset."

The query key pattern:

```tsx
const queryKey = ["traces", filters];
```

When `filters` changes (any field), TanStack Query sees a new key and refetches from page 1. The cursor state is automatically dropped because the `useInfiniteQuery` hook re-initializes when the key changes.

The debounce pattern for text input:

```tsx
const [draft, setDraft] = useState("");
const [applied, setApplied] = useState("");

useEffect(() => {
  const t = setTimeout(() => setApplied(draft), 300);
  return () => clearTimeout(t);
}, [draft]);
```

`draft` updates on every keystroke. `applied` updates 300ms after the last keystroke. The `filters` object uses `applied`. The result: one API call per typing burst, not one per keystroke.

## 35-48 min: optimistic feedback

> "User clicks thumbs up. Do you wait for the backend?"
>
> "No. I update the UI optimistically, send the mutation in the background, and rollback if it fails."

The full pattern:

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
    // 1. Cancel any in-flight refetch (so it doesn't overwrite us)
    await queryClient.cancelQueries({ queryKey: ["traces"] });

    // 2. Snapshot current state for rollback
    const previous = queryClient.getQueriesData({ queryKey: ["traces"] });

    // 3. Optimistically update the cache
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
    // Rollback to snapshot
    context?.previous.forEach(([key, data]) => {
      queryClient.setQueryData(key, data);
    });
  },

  onSettled: () => {
    // Reconcile with server
    queryClient.invalidateQueries({ queryKey: ["traces"] });
  },
});
```

The five things this code does, in order:

1. **Cancel stale reads** so they don't overwrite your optimistic update.
2. **Snapshot the previous cache** so you can roll back.
3. **Update the cache immediately** so the UI reflects the click.
4. **Roll back on error** so the UI reflects reality.
5. **Reconcile with the server** on success so any server-side changes (e.g., another engineer's feedback) merge in.

### The follow-up they always ask: "What if the user clicks up, then down, quickly?"

> "I need to avoid stale mutation responses overwriting newer intent. Three options: serialize feedback mutations per trace (a per-trace mutex), attach a client sequence number and have the server reject older ones, or make the server accept idempotent upsert with a last-write-version. The simplest is the per-trace mutex — use a `Map<traceId, Promise>` to chain mutations for the same trace."

That answer is 2 points on the rubric. The interviewer will not drill further.

## 48-55 min: detail drawer

> "I would not load all detail payloads in the list endpoint. The table returns lightweight row data. Full prompt, chunks, evidence, and response load only when the drawer opens."

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

The detail view shows: trace ID, user query, prompt version, retrieved chunks with similarity scores, evidence JSON, model response, latency breakdown (preprocess / retrieve / rerank / generate / postprocess), token usage, feedback history, grounded/validation status.

This is the panel that turns a feedback tool into a **gold-set generation tool**. The L6 sentence: "The tool is also useful for model evaluation. Feedback becomes labeled data for offline evaluation, and the detail view lets engineers inspect retrieved evidence, prompt version, latency, and groundedness."

## 55-60 min: production readiness

> "I'd make four things production-ready: first, pagination and indexes for backend performance; second, virtualization so rendering stays smooth; third, optimistic updates with rollback and race handling; fourth, clear loading, empty, error, retry, and permission states. I'd also add API tests for cursor boundaries and filters, React tests for optimistic rollback, and an end-to-end Playwright test for the review flow."

That's 6 minutes for tests. Don't write them. Just list them. The interviewer will not ask you to write tests in the last 5 minutes — they want to see you *think* about them.

## The 8-step memory hook

```
API → Cursor → Virtualize → Filter → Optimistic → Rollback → Detail → Test
```

If you can code and explain those eight cleanly, you're in very good shape for a 60-minute Full Stack round.

## One thing I would remove from the average candidate's answer

Most candidates say "feedback.corrected_answer becomes gold dataset automatically." Wrong. Thumbs down alone does not create gold truth. The correct framing:

> "Human-reviewed feedback can become candidate evaluation data after quality checks. We need at least one additional reviewer to confirm the corrected answer is actually correct before it goes into the eval set."

That single sentence shows you understand that **labels have a quality bar**. It's the difference between an L4 and an L6 answer.

## The closing line (use this verbatim)

> "The design is cursor pagination for stable, indexed access; virtualization for 1,000-row rendering performance; server-side filters with proper query-key invalidation; optimistic updates with snapshot rollback and per-trace mutation serialization; lazy-loaded detail drawer; and explicit empty, error, and loading states. The tool doubles as a gold-set generator for offline eval, which is where the long-term value lives."

## The code

Every claim here is backed by a runnable notebook with 30 cells. The trace reviewer schema is in cell 7, the SQL is in cells 3-6, and the React patterns are documented inline.

```bash
git clone https://github.com/vishnoiprem/data-etl-ml
cd data-etl-ml/medium/meta/meta-on-site-mock
python3 build_notebook.py
jupyter nbconvert --to notebook --execute meta_l6_onsite_mock.ipynb \
    --output meta_l6_onsite_mock_executed.ipynb
```

## What I'd do differently in v2

**One:** I would have practiced drawing the API contract on paper before the interview, not in my head. The first time I got asked for the contract, I fumbled the response shape. The second time, I drew it from memory in 90 seconds. Practice is the difference.

**Two:** I would have pre-thought the 3 follow-ups the interviewer always asks. For this round: race conditions on rapid clicks, what happens when the cache is stale, what happens when the user has no permission. I now have a 30-second answer for each.

**Three:** I would have made the detail drawer the hero of the demo, not the table. The table is the entry point. The detail view is where the engineer actually does work. If I had 5 minutes left, I'd spend them on the detail view, not the filters.

---

*If this helped, [follow me on Medium](https://medium.com/@vishnoiprem) and [star the repo](https://github.com/vishnoiprem/data-etl-ml/tree/main/medium/meta/meta-on-site-mock). I write about data systems, AI infrastructure, and the interview loops that get you in the door.*
