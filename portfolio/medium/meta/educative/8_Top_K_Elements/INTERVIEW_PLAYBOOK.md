# Top K Elements — Playbook, Memory Anchors, and Uses in AI

> Same three-part format as the other folders: **how to think**, **how to remember**, **how these show up in real AI systems**.

---

## PART 1 — How to think

### 1.1 The opener (use it every time)

> "Top-K problems have ONE choice that decides everything: do I want the k *largest* (use a MIN-heap of size K so the smallest of the kept set is at the root, which makes eviction O(1)), or the k *smallest* (use a MAX-heap of size K, same logic)? Everything else is bookkeeping."

### 1.2 The 5-question classifier

| # | Question | Answer |
|---|----------|--------|
| Q1 | What is the **score** of each item? | The element itself, a function of it, or a frequency? |
| Q2 | Am I comparing items **directly** (raw values)? | Min/Max-heap of size K. |
| Q3 | Am I comparing **frequencies**? | Counter + heap of `(count, value)`. |
| Q4 | Is the answer **order-preserving** in the original array? | Pair with index, sort, restore indices. |
| Q5 | Is the "best so far" defined as **MIN of one key × SUM of another**? | Sweep pattern + speed-heap (file 10). |

### 1.3 The two universal templates

```python
# Template A — heap of size K (most common)
import heapq
heap = []
for x in stream:
    if len(heap) < k:
        heapq.heappush(heap, x)
    elif x <opposite> heap[0]:        # opposite = '>' for k-largest
        heapq.heapreplace(heap, x)   # pop min + push in one shot
# heap now holds the k best; sorted(<opposite>) gives output order

# Template B — Counter + heap
from collections import Counter
cnt = Counter(arr)
top_k = heapq.nlargest(k, cnt.keys(), key=cnt.get)
# OR
heap = [(-c, v) for v, c in cnt.items()]
heapq.heapify(heap)
out = [heapq.heappop(heap)[1] for _ in range(k)]
```

The line `elif x <opposite> heap[0]` is the only line that needs to change.

### 1.4 Decision matrix for the 10 problems

| File | Pattern | One-line cue |
|------|---------|--------------|
| `01_introduction_to_top_k.py` | Both templates + quickselect | "Min-heap of size K." |
| `02_kth_largest_element.py` | Min-heap of size K | "Push if bigger than heap's smallest." |
| `03_top_k_frequent_elements.py` | Counter + heap | "Push `(count, val)`, pop K times." |
| `04_kth_largest_in_stream.py` | Min-heap of size K as a class | "Maintain invariant `len(heap)==K`." |
| `05_k_closest_points.py` | Max-heap of size K with NEGATED distance | "Farther than farthest-so-far → evict." |
| `06_reorganize_string.py` | Max-heap + cool-down queue | "Pop biggest, push back only after a step." |
| `07_subsequence_length_k_largest_sum.py` | Sort by value, then by index | "Preserve original order on re-sort." |
| `08_third_maximum_number.py` | Three variables, O(1) memory | "Cascade: shift right when a new max." |
| `09_smallest_range_covering.py` | Heap-of-tuples across k streams | "Track running max, candidate = [min, max]." |
| `10_maximum_performance_team.py` | Sweep by efficiency + speed-heap | "Efficiency is bottleneck; speed is summed." |

### 1.5 Interview script (3 timed phases)

1. **Classify (15 s):** "Score = the value itself, want k largest. Min-heap of size k."
2. **State the state (15 s):** "I'll keep a heap of size k; heap[0] is the smallest of the kept set."
3. **Sketch (30 s):** "For each element, if heap has room push; else if the element beats heap[0], heapreplace. At the end, sorted heap is the answer."

### 1.6 Traps (where candidates lose points)

| Trap | Symptom | Fix |
|------|---------|-----|
| Used MAX-heap for k largest | Eviction becomes O(k), not O(1) | Use a MIN-heap so eviction is `heapreplace`. |
| Forgot to negate for max-heap | Everything pops smallest | Python's `heapq` is min-heap; negate to fake max. |
| `find_kth_largest` returns the wrong index | `k=1` should be max, not min | Test with `k=1` mentally before coding. |
| Reorganise String returns "" when feasible | Cool-down queue mis-sized | Release entry AFTER one step OR when heap is empty. |
| Used a list, sorted it | O(n log n) when O(n log k) suffices | Heap is required whenever k << n. |
| Tied frequencies in wrong order | Wrong answer on ties | Counter on tuples `(count, val)`; Python tie-breaks by value. |
| Sorted performance by speed only | Bottleneck efficiency violated | Sweep by efficiency so the new element is always the team's min. |

---

## PART 2 — How to remember

### 2.1 The "shorthand" — say this whenever a Top-K problem starts

> **"Min-heap of size K, keep the k best, evict via heap[0]."**

It is the whole algorithm in 10 words.

### 2.2 Mnemonic — the 5 mnemonics for the 5 sub-patterns

| Pattern | Mnemonic | One-line image |
|---------|----------|----------------|
| Heap-of-size-K | **"Top shelf"** | The heap is a shelf; new arrivals push old, weak ones off. |
| Counter + heap | **"Vote counter"** | Each item has a vote count; pop the top-voted. |
| Order-preserving subsequence | **"Stage lineup"** | Pick the tallest, then line them back up by index. |
| Cool-down queue (Reorganize) | **"Singer rotation"** | Each singer sings, then sits out one song before returning. |
| Two-heap merge (Smallest Range) | **"Multiple streams"** | Merge k rivers; track the highest bank, try to lower it. |

### 2.3 The 30-second cold-recall drill

Without writing code, state out loud:
1. **Which template** — A (heap of size K) or B (Counter + heap)?
2. **Which direction** — Min or Max?  (Answer: opposite of the desired output.)
3. **What changes inside the loop?** — Push / heapreplace / Counter increment / pair-with-index.

If you can do all three in under 30 seconds, you can write the code.

### 2.4 Memorisation rhythm (15 min/day)

- **Day 1:** Read §1.3, run file 01, hand-trace on `[3,1,5,12,2,11,7], k=3`.
- **Day 2:** Re-derive file 02 from scratch.
- **Day 3:** Re-derive file 03 (Counter + heap).
- **Day 4:** Re-derive file 04 (the class version).
- **Day 5:** Re-derive file 05 (max-heap via negation).
- **Day 6:** Re-derive file 06 (cool-down queue) — this is the trap-richest.
- **Day 7:** Re-derive files 08, 09, 10 (no new concepts, only different keys).
- **Day 8:** Solve a *new* Top-K problem from Educative that isn't in the folder.

By day 8 you have the whole pattern space cold.

---

## PART 3 — How to use these in AI

Top-K heaps are not interview fluff — they back some of the highest-leverage pieces of modern ML infrastructure.

### 3.1 Beam search in sequence generation

Beam search for machine translation, summarisation, or speech recognition is **literally Template A in disguise**:

```python
def beam_search(scores_fn, start, beam_size=5, max_len=50):
    beams = [(0.0, [start])]                              # (cum_logp, tokens)
    for _ in range(max_len):
        all_cands = []
        for cum_logp, seq in beams:
            for tok, p in topk(scores_fn(seq), beam_size):
                all_cands.append((cum_logp + log(p), seq + [tok]))
        beams = sorted(all_cands, reverse=True)[:beam_size]
    return beams[0]
```

This is the heap-of-K pattern running on every token of every generated sentence.

### 3.2 kNN inference

Approximate nearest-neighbour search (FAISS, Annoy, ScaNN) builds a **graph where each node keeps K nearest neighbours** using top-K heaps during graph construction. The training pass is file 02 applied repeatedly.

### 3.3 Top-K retrieval in vector databases

Pinecone, Weaviate, Qdrant, and pgvector all answer "find the K nearest embeddings" using a heap-of-size-K as the inner loop of every query. The same code appears in:

- Recommender systems ("top K items for this user").
- Retrieval-Augmented Generation ("top K chunks for this prompt").
- Reranking ("top K after a cross-encoder").

### 3.4 Distributed Top-K (the Map-Reduce of ML)

When the dataset is too big for one machine, top-K has a textbook distributed algorithm:
1. **Map:** compute local top-K on each shard.
2. **Shuffle:** ship the local top-K's to one node.
3. **Reduce:** compute global top-K from the union.

This is exactly how `tf.nn.top_k`, `torch.topk`, and `numpy.argpartition` work under the hood, and it's the building block of distributed training's gradient-top-K compression.

### 3.5 The Reorganise-String pattern in scheduling

Production schedulers (e.g. training-job queues, model-serving rate limiters) avoid adjacent time-slots for the SAME job type by enforcing a cool-down. The data structure is file 06: max-heap of pending jobs + cool-down buffer.

### 3.6 Two-heap median & percentile estimation

The running median in streaming systems is maintained with TWO heaps:
- A max-heap of the lower half.
- A min-heap of the upper half.
- Median = (max-heap[0] + min-heap[0]) / 2.

This is the foundation of t-digest, HDR histograms, and quantile sketches used by every monitoring system (Prometheus, Datadog, Grafana).

### 3.7 Cap-set / cardinality-limited attention

Multi-head attention with a hard cap on the number of attended tokens (Longformer, BigBird) restricts each query to top-K most relevant keys — and stores them in a min-heap of size K per query. This is file 05 by another name.

### 3.8 Sparse mixture-of-experts routing

Switch Transformer and Mixtral route each token to its top-K experts out of N. The router is a softmax + `torch.topk`. The SAME heap-of-size-K is the inference-time data structure.

---

## TL;DR — what to take away

1. **Two templates** (heap-of-size-K and Counter+heap) and **ten tiny variations** capture every problem in this folder.
2. **"Min-heap of size K, keep the k best, evict via heap[0]"** is the 10-word mental shorthand.
3. The same algorithms run inside beam search, vector databases, kNN, schedulers, streaming quantiles, and sparse attention — once you see the pattern, you see it *everywhere* in production ML.
