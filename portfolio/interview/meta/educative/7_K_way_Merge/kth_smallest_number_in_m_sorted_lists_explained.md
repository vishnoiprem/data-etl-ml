# Kth Smallest Number in M Sorted Lists — 0.0001% Expert Guide

> **Educative** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/kth-smallest-number-in-m-sorted-lists
> **Problem:** Find K-th smallest across M sorted arrays.

---

## 📋 WHAT THE QUESTION ASKS

Given M sorted integer arrays, find the K-th smallest number among all the arrays combined.

### Constraints
- M can be up to thousands.
- Each list sorted in non-decreasing order.
- K up to total number of elements.

### Examples
```
[[2,6,8],[3,6,7],[1,2,3]], K=5 -> 3
    Combined: 1,2,2,3,3,6,6,7,8 → 5th = 3
[[1,5,9],[2,6,10],[3,7,11]], K=4 -> 5
    Combined: 1,2,3,5,6,7,9,10,11 → 4th = 5
```

### Why This Is "Medium"
- Generalization of K-th smallest to M lists.
- Heap-based solution gives O(K log M).
- Binary search alternative gives O(N log V).

---

## 🧠 HOW TO THINK — STEP BY STEP

### Step 1: Understand the Problem
> "Find K-th smallest among M sorted arrays combined."

### Step 2: Key Insight — Pop K-1 Times
> "Same as K-way merge, but stop early.
> Maintain min-heap of M heads. Pop K-1 times.
> The K-th pop is the answer."

### Step 3: Why This Works
> "The heap always gives the smallest unseen element.
> After K-1 pops, the heap top is the K-th smallest overall."

### Step 4: Algorithm (Heap)
```
1. heap = [(lst[0], i, 0) for i, lst in enumerate(lists)].
2. for _ in range(K-1):
     val, i, j = heappop(heap).
     if j+1 < len(lists[i]): heappush((lists[i][j+1], i, j+1)).
3. Return heap top's val.
```

### Step 5: Alternative — Binary Search
> "Binary search on value range.
> For each mid, count elements <= mid across all lists.
> If count >= K, answer is in [lo, mid]; else in [mid+1, hi]."

### Step 6: Edge Cases
- K=1: smallest of all heads.
- K=total: largest of all tails.
- Empty lists: skip in heap init.

### Step 7: Code It (Heap)
```python
def kthSmallest(lists, K):
    import heapq
    heap = []
    for i, lst in enumerate(lists):
        if lst:
            heapq.heappush(heap, (lst[0], i, 0))
    for _ in range(K - 1):
        if not heap:
            return None
        val, i, j = heapq.heappop(heap)
        if j + 1 < len(lists[i]):
            heapq.heappush(heap, (lists[i][j+1], i, j+1))
    return heapq.heappop(heap)[0] if heap else None
```

### Step 8: Verify
For [[2,6,8],[3,6,7],[1,2,3]], K=5:
- heap = [(2,0,0),(3,1,0),(1,2,0)].
- Pop 1: (1,2,0); push (2,2,1). heap=[(2,0,0),(2,2,1),(3,1,0)].
- Pop 2: (2,0,0); push (6,0,1). heap=[(2,2,1),(3,1,0),(6,0,1)].
- Pop 3: (2,2,1); push (3,2,2). heap=[(3,1,0),(3,2,2),(6,0,1)].
- Pop 4: (3,1,0); push (6,1,1). heap=[(3,2,2),(6,0,1),(6,1,1)].
- Top is (3,2,2). Answer: 3. ✓

### Step 9: Trade-offs
- Heap: O(K log M) time, O(M) space. **BEST when K small**.
- Collect+sort: O(N log N) — works when K=N.
- Binary search: O(N log V) — works when K is large or unbounded.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT

```
"I need to find K-th smallest across M sorted lists."

KEY INSIGHT: Same as K-way merge, stop early.
Min-heap of M heads. Pop K-1 times. K-th pop is answer.

ALGORITHM:
1. Init heap with first of each list.
2. Repeat K-1 times:
     Pop smallest, advance its list, push next.
3. Return heap top.

COMPLEXITY: O(K log M) time, O(M) space.

EDGE CASES:
- K=1: just min of all heads.
- Empty list: skip in init.

WHY HEAP:
- Smallest unseen is always among heap tops.
- O(log M) per pop/push.

ALTERNATIVE: Binary search on value range.
For each mid, count elements <= mid. Adjust bounds.

WHEN K IS LARGE:
- Heap O(K log M) might be expensive.
- Binary search O(N log V) could be better.

RELATED:
- Kth Smallest in Sorted Matrix (LC 378)
- Kth Largest Element (LC 215)
- Smallest Number Range (LC 632)
- K-way merge family
"""
```

---

## 💎 THE 8-LINE SOLUTION (Memorize!)

```python
def kthSmallest(lists, K):
    import heapq
    heap = []
    for i, lst in enumerate(lists):
        if lst:
            heapq.heappush(heap, (lst[0], i, 0))
    for _ in range(K - 1):
        if not heap:
            return None
        val, i, j = heapq.heappop(heap)
        if j + 1 < len(lists[i]):
            heapq.heappush(heap, (lists[i][j + 1], i, j + 1))
    return heapq.heappop(heap)[0] if heap else None
```

**Time:** `O(K log M)` | **Space:** `O(M)`

---

## 🤖 KEY INSIGHTS

1. **Heap pop K-1 times** — K-th pop is answer.
2. **O(K log M) total** — K operations, log M per heap op.
3. **Tie-breaker (idx, j)** — `(val, i, j)` tuple.
4. **No need to merge all** — early termination saves work.
5. **O(M) heap space** — only k candidates tracked.
6. **Binary search alternative** — O(N log V).
7. **Collect+sort fallback** — O(N log N).
8. **Same as K-way merge** — but stop at K.
9. **`heapq.merge`** — Python streaming merge.
10. **Range query** — generalized problem (e.g., sum of K smallest).

---

## 🧪 TEST CASES

| `lists` | K | Expected | Note |
|---------|---|----------|------|
| `[[2,6,8],[3,6,7],[1,2,3]]` | 5 | `3` | Mixed |
| `[[1,5,9],[2,6,10],[3,7,11]]` | 4 | `5` | Interleaved |
| `[[1,2,3]]` | 2 | `2` | Single list |
| `[[1],[2],[3]]` | 1 | `1` | K=1 |
| `[[1],[2],[3]]` | 3 | `3` | K=total |
| `[[5,10,15],[3,6,9,12,18]]` | 4 | `9` | Mixed sizes |
| `[[-5,-2,1],[0,3,7]]` | 3 | `0` | Negatives |
| `[[1,3,5],[2,4,6]]` | 5 | `5` | Even K |

---

## 📊 COMPLEXITY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Heap pop K times** | **O(K log M)** | **O(M)** | **✅ BEST when K small** |
| Binary search | O(N log V) | O(1) | ✅ When K large |
| Collect + sort | O(N log N) | O(N) | ✅ Always works |
| heapq.merge stream | O(K log M) | O(K) | ✅ Equivalent |

---

## 🔗 RELATED

- Kth Smallest in Sorted Matrix (LC 378)
- Smallest Number Range (LC 632)
- Kth Largest (LC 215)
- K-way merge family

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Insight:** "Min-heap of M heads. Pop K-1 times. K-th pop is answer. O(K log M) total."
