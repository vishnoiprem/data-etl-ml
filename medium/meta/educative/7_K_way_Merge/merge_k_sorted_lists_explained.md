# Merge K Sorted Lists — 0.0001% Expert Guide

> **LeetCode 23** | **Difficulty:** Hard | **Avg Solve Time:** 45 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/merge-k-sorted-lists
> **Problem:** Merge k sorted linked lists into one sorted list.

---

## 📋 WHAT THE QUESTION ASKS

You are given an array of `k` linked lists, each sorted in ascending order. Merge all into one sorted linked list and return it.

### Constraints
- `0 <= k <= 10^4`
- `0 <= lists[i].length <= 500`
- `-10^4 <= lists[i][j] <= 10^4`
- Total nodes across all lists <= `10^4`.

### Examples
```
[[1,4,5],[1,3,4],[2,6]] -> [1,1,2,3,4,4,5,6]
[]                       -> []
[[]]                     -> []
```

### Why This Is "Hard"
- Generalization of 2-list merge to k lists.
- Min-heap / divide & conquer decisions.
- O(N log k) with heap, or O(N log k) with divide-conquer.

---

## 🧠 HOW TO THINK — STEP BY STEP

### Step 1: Understand the Problem
> "Merge k sorted linked lists into one sorted list."

### Step 2: Key Insight — Smallest is Among Heads
> "At any point, the NEXT smallest element to add is one of the k head pointers.
> We pick that head, append, advance that list, repeat."

### Step 3: Min-Heap of Size k
> "Maintain a min-heap of size k with current heads.
> Top of heap = next smallest. Pop it, push its successor.
> Each pop/push is O(log k)."

### Step 4: Algorithm
```
1. Initialize heap with first node of each non-empty list.
2. While heap non-empty:
     Pop (val, idx, node).
     Append node to result.
     If node.next: push (node.next.val, idx, node.next).
3. Return result's head.
```

### Step 5: Tie-Breaking
> "Multiple nodes may have the same val.
> Heap compare fails on nodes (no <), so we use (val, idx, node) tuples.
> idx breaks ties."

### Step 6: Edge Cases
- Empty lists: return None.
- Single list: return that list.
- All single-node lists: just heap-pop in sorted order.

### Step 7: Code It
```python
def mergeKLists(lists):
    import heapq
    heap = []
    for i, head in enumerate(lists):
        if head:
            heapq.heappush(heap, (head.val, i, head))
    dummy = ListNode(0)
    cur = dummy
    while heap:
        val, i, node = heapq.heappop(heap)
        cur.next = node
        cur = cur.next
        if node.next:
            heapq.heappush(heap, (node.next.val, i, node.next))
    return dummy.next
```

### Step 8: Verify
For [[1,4,5],[1,3,4],[2,6]]:
- heap = [(1,0,n1),(1,1,n2),(2,2,n3)].
- pop (1,0,n1): result=[1]; push (4,0,n4). heap=[(1,1,n2),(2,2,n3),(4,0,n4)].
- pop (1,1,n2): result=[1,1]; push (3,1,n3'). heap=[(2,2,n3),(3,1,n3'),(4,0,n4)].
- pop (2,2,n3): result=[1,1,2]; push (6,2,n6). heap=[(3,1,n3'),(4,0,n4),(6,2,n6)].
- pop (3,1,n3'): result=[1,1,2,3]; push (4,1,n4'). heap=[(4,0,n4),(4,1,n4'),(6,2,n6)].
- pop (4,0,n4): result=[1,1,2,3,4]; push (5,0,n5). heap=[(4,1,n4'),(5,0,n5),(6,2,n6)].
- pop (4,1,n4'): result=[1,1,2,3,4,4]. heap=[(5,0,n5),(6,2,n6)].
- pop (5,0,n5): result=[1,1,2,3,4,4,5]. heap=[(6,2,n6)].
- pop (6,2,n6): result=[1,1,2,3,4,4,5,6]. ✓

### Step 9: Trade-offs
- Min-heap: O(N log k) time, O(k) space. **BEST**.
- Divide & conquer: O(N log k) time, O(log k) space (recursion).
- Sequential pairwise: O(kN) — slower for large k.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT

```
"I need to merge k sorted linked lists into one sorted list."

KEY INSIGHT: At each step, the next smallest is among the k list heads.
Use a min-heap to track current heads. Pop smallest, advance its list.

ALGORITHM:
1. Push head of each non-empty list into min-heap.
2. While heap non-empty:
     Pop (val, idx, node).
     Append to result.
     Push node.next if exists.
3. Return result.

COMPLEXITY: O(N log k) time, O(k) space.

EDGE CASES:
- Empty: return None.
- Single: return as is.

TIE-BREAKING:
- Multiple heads may have same val.
- Tuple (val, idx, node): idx breaks ties.

WHY HEAP:
- k candidates → smallest in O(log k).
- Avoids O(k) scan per pop.

ALTERNATIVE: Divide and conquer (merge pairs recursively).
Same O(N log k) but O(log k) stack space.

RELATED:
- Merge Sorted Array (LC 88)
- Kth Smallest in M Sorted Lists (LC 378-ish)
- Smallest Number Range (LC 632)
- K-way merge pattern
"""
```

---

## 💎 THE 10-LINE SOLUTION (Memorize!)

```python
def mergeKLists(lists):
    import heapq
    heap = []
    for i, head in enumerate(lists):
        if head:
            heapq.heappush(heap, (head.val, i, head))
    dummy = ListNode(0)
    cur = dummy
    while heap:
        val, i, node = heapq.heappop(heap)
        cur.next = node
        cur = cur.next
        if node.next:
            heapq.heappush(heap, (node.next.val, i, node.next))
    return dummy.next
```

**Time:** `O(N log k)` | **Space:** `O(k)`

---

## 🤖 KEY INSIGHTS

1. **Min-heap of size k** — natural for K-way merge.
2. **Tie-breaker** — `(val, idx, node)` since node comparison fails.
3. **O(N log k) total** — N total nodes, log k per pop/push.
4. **O(k) heap space** — only k heads tracked.
5. **Divide & conquer** alternative — O(N log k) with recursion.
6. **`heapq.merge` iterator** — Python's built-in streaming merge.
7. **Pairwise sequential** — O(kN), simple but slower.
8. **Sort all values** — O(N log N), overkill but works.
9. **Brute pair-min** — O(k²N) worst case.
10. **Generalization** — works for any K sorted sequences, not just lists.

---

## 🧪 TEST CASES

| Input | Expected | Note |
|-------|----------|------|
| `[[1,4,5],[1,3,4],[2,6]]` | `[1,1,2,3,4,4,5,6]` | Classic |
| `[]` | `[]` | Empty |
| `[[]]` | `[]` | Single empty |
| `[[1,2,3]]` | `[1,2,3]` | One list |
| `[[1],[2],[3]]` | `[1,2,3]` | Single nodes |
| `[[-1,0,1],[-2,0,2]]` | `[-2,-1,0,0,1,2]` | Negatives |
| `[[1,5,9],[2,6,10],[3,7,11]]` | `[1,2,3,5,6,7,9,10,11]` | Interleaved |

---

## 📊 COMPLEXITY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Min-heap** | **O(N log k)** | **O(k)** | **✅ BEST** |
| Divide & conquer | O(N log k) | O(log k) stack | ✅ Same time |
| Sequential pairwise | O(kN) | O(1) | ❌ Slower |
| Sort all values | O(N log N) | O(N) | ❌ Slower |
| Brute pair-min | O(k²N) | O(1) | ❌ Slow |

---

## 🔗 RELATED

- Merge Sorted Array (LC 88)
- Smallest Number Range (LC 632)
- Kth Smallest in M Sorted Lists
- K-way merge family

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Insight:** "Min-heap of k heads. Pop smallest, advance list, push next. O(N log k) total. Tie-break with idx."
