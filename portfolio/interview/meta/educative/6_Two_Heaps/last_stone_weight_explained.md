# Last Stone Weight — 0.0001% Expert Guide

> **LeetCode 1046** | **Difficulty:** Easy | **Avg Solve Time:** 15 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/last-stone-weight
> **Problem:** Smash two heaviest stones until one or none remains.

---

## 📋 WHAT THE QUESTION ASKS

We have a collection of stones with positive integer weights. Each turn:
1. Pick the **two heaviest** stones (weights x ≤ y).
2. Smash them:
   - If `x == y`: both destroyed.
   - If `x < y`: stone x destroyed, y becomes `y - x`.

Return the weight of the last remaining stone (0 if none).

### Constraints
- `1 <= stones.length <= 30`
- `1 <= stones[i] <= 1000`

### Examples
```
[2,7,4,1,8,1] -> 1
    (8,7) → 1; [1,4,1,2,1]
    (4,2) → 2; [1,1,1,2]
    (2,1) → 1; [1,1,1]
    (1,1) → 0; [1]
    → answer 1
[1]            -> 1
[2,2]          -> 0
```

### Why This Is "Easy"
- Classic max-heap / priority queue problem.
- O(n log n) time.
- Foundation for "process top-K" heap problems.

---

## 🧠 HOW TO THINK — STEP BY STEP

### Step 1: Understand the Problem
> "Repeatedly smash the two heaviest. Return final weight."

### Step 2: Key Insight — Need Top-2 Repeatedly
> "Every turn we need the two largest elements. After smashing, we may
> need to re-insert a new stone (smaller). This is the textbook use
> case for a max-heap (priority queue)."

### Step 3: Max-Heap Algorithm
> "1. Build max-heap from stones (negate values for Python's min-heap).
>  2. While heap has 2+ elements:
>       y = pop max; x = pop max.
>       If y > x: push (y - x).
>  3. Return heap top if non-empty, else 0."

### Step 4: Why Negate in Python?
> "Python's `heapq` is a MIN-heap. To get MAX-heap behavior,
> negate values: push -x, pop -heap[0]."

### Step 5: Algorithm
```
1. heap = [-s for s in stones]; heapq.heapify(heap).
2. While len(heap) > 1:
     y = -heapq.heappop(heap); x = -heapq.heappop(heap).
     if y > x: heapq.heappush(heap, -(y - x)).
3. Return -heap[0] if heap else 0.
```

### Step 6: Edge Cases
- Single stone: return it.
- Two equal stones: return 0.
- All same weight: depends on count parity.

### Step 7: Code It
```python
def lastStoneWeight(stones):
    import heapq
    heap = [-s for s in stones]
    heapq.heapify(heap)
    while len(heap) > 1:
        y = -heapq.heappop(heap)
        x = -heapq.heappop(heap)
        if y > x:
            heapq.heappush(heap, -(y - x))
    return -heap[0] if heap else 0
```

### Step 8: Verify
For [2,7,4,1,8,1]:
- heap = [-8,-7,-4,-1,-2,-1] (negated).
- pop -8 (y=8); pop -7 (x=7); push -1.
- heap = [-4,-2,-1,-1,-1].
- pop -4 (y=4); pop -2 (x=2); push -2.
- heap = [-2,-1,-1,-1].
- pop -2 (y=2); pop -1 (x=1); push -1.
- heap = [-1,-1,-1].
- pop -1 (y=1); pop -1 (x=1); no push.
- heap = [-1].
- Return -(-1) = 1. ✓

### Step 9: Trade-offs
- Max-heap: O(n log n) time, O(n) space. **BEST**.
- Sort each iteration: O(n² log n) — slower.
- Recursive: O(n² log n) — sorting each call.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT

```
"I need to smash the two heaviest stones until one or none remains."

KEY INSIGHT: We always need the TWO LARGEST elements. After smash, we
may insert a smaller stone. This is a max-heap (priority queue) problem.

ALGORITHM:
1. Build max-heap from stones (negate for Python min-heap).
2. While 2+ stones:
     y = pop max; x = pop max.
     if y > x: push (y - x).
3. Return heap top or 0.

COMPLEXITY: O(n log n) time, O(n) space.

EDGE CASES:
- Single stone: return it.
- Two equal: return 0.

WHY MAX-HEAP:
- O(log n) per push/pop.
- Always gives us top-2 in O(log n) total.
- Re-sorting would be O(n log n) per round → O(n² log n).

WHY NEGATE:
- Python's heapq is MIN-heap.
- Negate values: push -x, pop -heap[0].

VARIANT: K-th largest / smallest patterns.

RELATED:
- Kth Largest Element (LC 215)
- Top K Frequent Elements (LC 347)
- K Closest Points (LC 973)
- Heap Sort
"""
```

---

## 💎 THE 6-LINE SOLUTION (Memorize!)

```python
def lastStoneWeight(stones):
    import heapq
    heap = [-s for s in stones]
    heapq.heapify(heap)
    while len(heap) > 1:
        y = -heapq.heappop(heap)
        x = -heapq.heappop(heap)
        if y > x:
            heapq.heappush(heap, -(y - x))
    return -heap[0] if heap else 0
```

**Time:** `O(n log n)` | **Space:** `O(n)`

---

## 🤖 KEY INSIGHTS

1. **Max-heap (priority queue)** — natural fit for top-K problems.
2. **Negation trick** — Python heapq is min-heap.
3. **O(n log n) total** — n operations × log n per heap op.
4. **Push back difference** — new stone might still be "heavy".
5. **0 or 1 stone at end** — return heap top or 0.
6. **Two-pointer not ideal** — needs sorted access after each smash.
7. **Sort each iter is slow** — O(n² log n).
8. **Counter approach** — possible for small weight range, but complex.
9. **Recursive** — works but stack overflow risk.
10. **Foundation** — generalizes to "merge K stones" type problems.

---

## 🧪 TEST CASES

| `stones` | Expected | Note |
|----------|----------|------|
| `[2,7,4,1,8,1]` | `1` | Classic |
| `[1]` | `1` | Single |
| `[2,2]` | `0` | Equal pair |
| `[1,2,3]` | `0` | Triplet |
| `[3,3,3]` | `3` | Triple |
| `[1,1,1,1,1]` | `1` | Odd count |
| `[10,4,2,10]` | `2` | Two pairs |
| `[1,3,5,7,9]` | `1` | Sequential |
| `[5]` | `5` | Single |
| `[9,3,2,10]` | `0` | All cancel |

---

## 📊 COMPLEXITY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Max-heap (negate)** | **O(n log n)** | **O(n)** | **✅ BEST** |
| Sort each iter | O(n² log n) | O(n) | ❌ Slower |
| Manual heap | O(n log n) | O(n) | ✅ Educational |
| Recursive | O(n² log n) | O(n) | ⚠️ Stack risk |
| Counter | O(n²) | O(n) | ❌ Inefficient |

---

## 🔗 RELATED

- Kth Largest Element (LC 215)
- Top K Frequent (LC 347)
- K Closest Points (LC 973)
- Heap Sort pattern
- Priority Queue family

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Insight:** "Max-heap (negate for Python min-heap). Pop two largest, smash, push diff. O(n log n) total."
