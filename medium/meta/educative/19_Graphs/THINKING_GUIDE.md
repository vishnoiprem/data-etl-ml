# Graph Thinking Guide — Spelled-Out Whiteboard Walkthrough

> Most "how to think" guides give you the **destination** (the algorithm). This one gives you the **route** — every silent thought that should happen between reading the problem and writing the code. Read it once, then *imitate the inner monologue* on your next 5 problems.

---

## The problem we'll work through

> **Network Delay Time** (LeetCode 743). n nodes, weighted directed edges `times[i] = [u, v, w]`. Signal starts at `k`. Return the time for all nodes to receive the signal, or -1 if unreachable.

---

## Phase 1 — Read (30 seconds, no code)

What's actually being asked?

> "How long until the SLOWEST node receives the signal?"
> (Because we don't stop until *every* node has it.)
> Equivalently: the **shortest path** from `k` to every other node, and we want the **maximum** of those distances.

What's the input?

> Directed, weighted edges. Non-negative weights are not stated explicitly, but the standard version of this problem says they're positive.

What's the output?

> A single integer (the max) or -1 if any node is unreachable.

---

## Phase 2 — Classify (15 seconds)

Walk through the 4-question decision tree from the playbook:

1. *Does every edge cost the same?*  → No, weights differ.
2. *Non-negative weights?*  → Yes (the default assumption).
3. *Negative weights?*  → No.
4. *Use every edge exactly once?*  → No.

→ **Dijkstra** (min-heap).

**Mental note:** *If the interviewer said "weights can be negative", I'd switch to Bellman-Ford and say so out loud.*

---

## Phase 3 — State the state (10 seconds)

What bookkeeping do I need?

| Variable | Type | Purpose |
|----------|------|---------|
| `graph` | dict of `list[(v, w)]` | adjacency list |
| `dist[i]` | `float('inf')` | best known distance from `k` to `i` |
| `heap` | `[(d, u)]` | worklist, ordered by smallest `d` |

That's it. **Three variables.** Whenever your state has more than 4-5 things, you're probably solving the wrong problem.

---

## Phase 4 — Sketch the loop (30 seconds, aloud)

> "Standard Dijkstra. Pop the smallest `(d, u)` from the heap. If `d` is already worse than `dist[u]`, skip — it's a stale entry. Otherwise relax every edge `(u, v, w)`: if `d + w < dist[v]`, update and push."

**Trick to remember the stale-entry check:** every time we improve `dist[v]`, we push a *new* entry for `v`. The old entry is now worse than the best known. Skipping it keeps the heap clean.

**Trick to remember the answer:** after Dijkstra, the answer is `max(dist[1:])`. If that max is still `inf`, some node was unreachable → return `-1`.

---

## Phase 5 — Trace by hand (2 minutes, the most important part)

Take a tiny example and walk through it.

```
times = [[2,1,1],[2,3,1],[3,4,1]], n = 4, k = 2
```

Adjacency list:

```
2 → [(1,1), (3,1)]
3 → [(4,1)]
1 → []
4 → []
```

Initial state: `dist = [0, inf, 0, inf, inf]` (1-indexed).  Heap: `[(0, 2)]`.

Step 1: pop `(0, 2)`. Relax:
- `2 → 1`: `0 + 1 < inf` → `dist[1] = 1`, push `(1, 1)`.
- `2 → 3`: `0 + 1 < inf` → `dist[3] = 1`, push `(1, 3)`.

Heap: `[(1, 1), (1, 3)]`.   `dist = [0, 1, 0, 1, inf]`.

Step 2: pop `(1, 1)`. Neighbours of 1: none. Skip relax.

Step 3: pop `(1, 3)`. Relax:
- `3 → 4`: `1 + 1 < inf` → `dist[4] = 2`, push `(2, 4)`.

Heap: `[(2, 4)]`.   `dist = [0, 1, 0, 1, 2]`.

Step 4: pop `(2, 4)`. Neighbours: none. Done.

Final `max(dist[1:])` = `max(1, 0, 1, 2)` = **2**. ✓

**What did the trace teach me?** It caught that the answer is `2` (time to reach node 4), not `1` (time to reach node 1 or 3). The MAX is the bottleneck.

**What if a node were unreachable?** It would still be `inf` in `dist`. The `max()` would be `inf` and I'd return `-1`. ✓

---

## Phase 6 — Edge cases (10 seconds)

| Edge case | Behaviour |
|-----------|-----------|
| `n = 1`, `k = 0` | `dist[0] = 0`, `max([])` — careful with the slice. Most implementations return `0`. |
| Empty `times` | Only `k` is reachable; all other nodes are `inf` → return `-1`. |
| Self-loop | No effect on correctness; heap will see `(0, k)` then `(w, k)` again, which loses to `dist[k] = 0`. |
| Duplicate edges | Both get enqueued; the worse one becomes stale and is skipped. |

**What if the interviewer asks for the *path itself*, not just the distance?** Add a `parent[i]` array updated alongside `dist[i]`. Reconstruct by walking `parent` from `goal` back to `start`.

---

## Phase 7 — Code (5 minutes)

Open your editor. Narrate as you write:

> "Imports: heapq, defaultdict. Build graph from `times`. Init `dist = [inf] * (n+1)`, `dist[k] = 0`. Heap starts with `(0, k)`. While heap non-empty: pop `(d, u)`. If `d > dist[u]`: continue. For each `(v, w)` in `graph[u]`, if `d + w < dist[v]`: update and push. After loop: `ans = max(dist[1:])`. Return `ans if ans != inf else -1`."

That's it. ~25 lines including the function signature.

---

## Phase 8 — Complexity (30 seconds, aloud)

> "Each edge is relaxed at most once per improvement, so heap sees at most `E` pushes. Each push/pop is `O(log V)`. Total time: `O((V + E) log V)`. Space: `O(V + E)` for the graph + `O(V)` for dist + heap."

If the interviewer pushes back (*"can you do it in O(V + E)?"*), the only way is if weights are 0 or 1 → **0-1 BFS with a deque** instead. State that as the trade-off.

---

## The 8-step mental loop, generalised

| # | Step | Time | Output |
|---|------|------|--------|
| 1 | **Read** the problem | 30 s | What is being asked? |
| 2 | **Classify** via the 4-question tree | 15 s | Algorithm name |
| 3 | **State the state** | 10 s | The 3-5 variables you'll carry |
| 4 | **Sketch the loop** | 30 s | "Pop, skip-stale, relax" — or whatever the skeleton is |
| 5 | **Trace by hand** | 2 min | Confirms correctness, catches the answer-aggregation mistake |
| 6 | **Edge cases** | 10 s | Empty input, single element, unreachable |
| 7 | **Code** while narrating | 5 min | 20-30 lines |
| 8 | **Complexity** aloud | 30 s | Big-O + one sentence on the trade-off |

Rehearse this loop on **5 problems from different buckets** and the loop becomes automatic. After that, you don't think about the loop — you just run it.

---

## Common failure modes (and where in the loop they happen)

| Failure | Where in the loop | How the loop prevents it |
|---------|-------------------|--------------------------|
| Wrong algorithm chosen | step 2 | 4-question tree forces explicit classification |
| Forgot a state variable | step 3 | Listing them BEFORE coding reveals the gap |
| Code is correct but answer is wrong | step 5 | Trace forces you to see `max(dist)` not `min(dist)` |
| TLE | step 8 | Forces you to confront the complexity and pick a faster alg |
| Interviewer asks a twist | step 6 | Edge cases become the seed for follow-ups |

---

## One-line summary to burn into memory

> **Classify, state the state, trace, then code.**
> The trace is the most important step. Never skip it.
