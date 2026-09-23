# Find K Pairs with Smallest Sums — 0.0001% Expert Guide

> **LeetCode 373** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/find-k-pairs-with-smallest-sums
> **Problem:** Find K pairs (u, v) with smallest sums.

---

## 📋 WHAT THE QUESTION ASKS

You are given two integer arrays `nums1` and `nums2` sorted in non-decreasing order, and an integer `k`. Find the `k` pairs `(u, v)` with the smallest sums (u from nums1, v from nums2). Return them in any order.

### Constraints
- `1 <= nums1.length, nums2.length <= 10^5`
- Sorted in non-decreasing order.
- `1 <= k <= 10^4`

### Examples
```
[1,7,11], [2,4,6], k=3  -> [[1,2],[1,4],[1,6]]
[1,1,2], [1,2,3], k=2   -> [[1,1],[1,1]]
[1,2], [3], k=3         -> [[1,3],[2,3]]
```

### Why This Is "Medium"
- Heap-based K-way merge variant.
- O(k log k) time, O(k) space.
- Visited set for non-redundant expansion.

---

## 🧠 HOW TO THINK — STEP BY STEP

### Step 1: Understand the Problem
> "Two sorted arrays. Find K pairs (a, b) with smallest a+b sum."

### Step 2: Key Insight — Heap of Size k
> "Treat each pair (i, j) as a candidate. Sum = nums1[i] + nums2[j].
> Top K smallest sums can be enumerated via heap."

### Step 3: Heap Initialization — First k of nums1
> "Top K sums must include at least one element from nums1[0..k-1].
> Beyond k, sums are too large to be in top K.
> Initialize: (nums1[i]+nums2[0], i, 0) for i in 0..min(k-1, n1-1)."

### Step 4: Algorithm
```
1. heap = [(nums1[i]+nums2[0], i, 0) for i in range(min(k, n1))].
2. While heap and result size < k:
     s, i, j = heappop(heap).
     Append (nums1[i], nums2[j]) to result.
     If j+1 < n2: push (nums1[i]+nums2[j+1], i, j+1).
3. Return result.
```

### Step 5: Why Only First k of nums1
> "If we use nums1[k], the smallest sum from nums1[k] is nums1[k]+nums2[0].
> This is >= nums1[k-1]+nums2[0] (since nums1 is sorted).
> Top K must come from first K elements of nums1 (with any nums2[j])."

### Step 6: Edge Cases
- k=0: return [].
- One array of size 1: at most n pairs.
- All same elements: same pairs repeated.

### Step 7: Code It
```python
def kSmallestPairs(nums1, nums2, k):
    import heapq
    if not nums1 or not nums2 or k == 0:
        return []
    heap = [(nums1[i] + nums2[0], i, 0) for i in range(min(k, len(nums1)))]
    heapq.heapify(heap)
    result = []
    while heap and len(result) < k:
        s, i, j = heapq.heappop(heap)
        result.append([nums1[i], nums2[j]])
        if j + 1 < len(nums2):
            heapq.heappush(heap, (nums1[i] + nums2[j + 1], i, j + 1))
    return result
```

### Step 8: Verify
For [1,7,11], [2,4,6], k=3:
- heap = [(3,0,0), (11,1,0), (17,2,0)].
- Pop (3,0,0): result=[[1,2]]; push (5,0,1). heap=[(5,0,1),(11,1,0),(17,2,0)].
- Pop (5,0,1): result=[[1,2],[1,4]]; push (7,0,2). heap=[(7,0,2),(11,1,0),(17,2,0)].
- Pop (7,0,2): result=[[1,2],[1,4],[1,6]]. Done. ✓

### Step 9: Trade-offs
- Heap (first k): O(k log k) time, O(k) space. **BEST**.
- Heap (visited set): O(k log k) time, O(k) space, more general.
- Brute sort: O(n*m log(n*m)) — slow.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT

```
"I need to find K pairs (u, v) with smallest sums from two sorted arrays."

KEY INSIGHT: Treat pair (i, j) as node. Sum = nums1[i]+nums2[j].
Initialize heap with first min(k, n1) pairs using nums2[0].
Pop smallest, advance j, push next.

ALGORITHM:
1. heap = [(nums1[i]+nums2[0], i, 0) for i in range(min(k, n1))].
2. While heap and result size < k:
     Pop (s, i, j).
     Append (nums1[i], nums2[j]).
     If j+1 < n2: push (nums1[i]+nums2[j+1], i, j+1).
3. Return result.

COMPLEXITY: O(k log k) time, O(k) space.

EDGE CASES:
- k=0: return [].
- k > total pairs: return all.

WHY ONLY FIRST K OF NUMS1:
- Top K sums use only first K elements of nums1.
- Beyond K, sums are too large.

WHY VISITED SET (alternative):
- Push (i+1, j) AND (i, j+1) when popping.
- Avoid duplicates via set.

RELATED:
- Kth Smallest in M Sorted Lists
- Kth Smallest in Sorted Matrix (LC 378)
- Smallest Number Range (LC 632)
- Heap-based K-way enumeration
"""
```

---

## 💎 THE 8-LINE SOLUTION (Memorize!)

```python
def kSmallestPairs(nums1, nums2, k):
    import heapq
    if not nums1 or not nums2 or k == 0:
        return []
    heap = [(nums1[i] + nums2[0], i, 0) for i in range(min(k, len(nums1)))]
    heapq.heapify(heap)
    result = []
    while heap and len(result) < k:
        s, i, j = heapq.heappop(heap)
        result.append([nums1[i], nums2[j]])
        if j + 1 < len(nums2):
            heapq.heappush(heap, (nums1[i] + nums2[j + 1], i, j + 1))
    return result
```

**Time:** `O(k log k)` | **Space:** `O(k)`

---

## 🤖 KEY INSIGHTS

1. **Treat (i, j) as node** — sum = nums1[i] + nums2[j].
2. **First k of nums1 init** — beyond K, sums too large.
3. **Advance j only** — natural progression.
4. **O(k log k) total** — K pops × log k per op.
5. **O(k) heap space** — bounded by k.
6. **Visited set variant** — push (i+1, j) and (i, j+1).
7. **`heapq.nsmallest`** — Pythonic alternative for brute.
8. **Brute sort** — works but slow O(n*m log(n*m)).
9. **Order doesn't matter** — return pairs in any order.
10. **Foundation** — generalizes to K-way enumeration.

---

## 🧪 TEST CASES

| nums1 | nums2 | k | Expected | Note |
|-------|-------|---|----------|------|
| `[1,7,11]` | `[2,4,6]` | 3 | `[[1,2],[1,4],[1,6]]` | Classic |
| `[1,1,2]` | `[1,2,3]` | 2 | `[[1,1],[1,1]]` | Duplicates |
| `[1,2]` | `[3]` | 3 | `[[1,3],[2,3]]` | Limited |
| `[1,2,3]` | `[1,2,3]` | 3 | `[[1,1],[1,2],[2,1]]` | Mixed |
| `[1,1,1]` | `[1,1,1]` | 4 | `[[1,1],[1,1],[1,1],[1,1]]` | All same |

---

## 📊 COMPLEXITY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Heap first k** | **O(k log k)** | **O(k)** | **✅ BEST** |
| Heap visited | O(k log k) | O(k) | ✅ Alternative |
| Brute sort | O(n*m log(n*m)) | O(n*m) | ❌ Slow |
| `heapq.nsmallest` | O(n*m log k) | O(k) | ⚠️ Worse than heap |

---

## 🔗 RELATED

- Kth Smallest in M Sorted Lists
- Kth Smallest in Sorted Matrix (LC 378)
- Smallest Number Range (LC 632)
- Heap-based K-way enumeration

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Insight:** "Heap with first k of nums1 init. Pop, advance j, push next. O(k log k) total."
