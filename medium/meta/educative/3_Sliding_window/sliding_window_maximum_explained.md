# Sliding Window Maximum — 10 Solutions + Interview Thinking

## Problem
Given an array `nums` and integer `k`, slide a window of size `k` across
the array. Return the maximum of each window.

Reference: LeetCode #239 / Educative Grokking — "Sliding Window Maximum".

---

## Interview Talking Points

Lead with the **monotonic deque**: "We maintain indices of elements in
decreasing order. The front is always the window's max."

Then mention why we store INDICES (not values): to detect when the
front element has left the window.

---

## 10-Step Thinking Process

### 1. Understand
"For each window of size `k` in `nums`, output its maximum."

### 2. Key Insight
Use a **monotonic deque** (decreasing values). For each new element:
- Pop indices from the back while their values are ≤ new value.
- Append new index.
- Pop from front if out of window.
- Front is the current max.

### 3. Pattern Recognition
- **Monotonic deque** — classic data structure for sliding window
  extrema.
- Indices in the deque are always in **decreasing order of values**.

### 4. Edge Cases
- `k == 1` → return `nums` itself.
- `k == n` → return `[max(nums)]`.
- Empty `nums` → `[]`.
- All same values → `[v] * (n - k + 1)`.

### 5. Tricky Detail — Why Indices, Not Values

If we only store values, we can't tell when the max is out of window.
Storing indices lets us check `dq[0] <= right - k` (out of window).

### 6. Algorithm
```
dq = deque()  # stores indices; values at dq are in decreasing order
result = []
for right in range(n):
    while dq and nums[dq[-1]] <= nums[right]:
        dq.pop()
    dq.append(right)
    if dq[0] <= right - k:
        dq.popleft()
    if right >= k - 1:
        result.append(nums[dq[0]])
return result
```

### 7. Why It Works
- Each new element either:
  - Popped (it was ≤ something larger later), or
  - Appended (it's the new max candidate).
- Older indices are removed when out of window.
- The front index always points to the largest value in the current
  window.

### 8. Complexity
- **Time**: O(n) — each index is pushed and popped at most once.
- **Space**: O(k) for the deque.

### 9. Code Structure
1. Initialize deque.
2. For each `right`:
   a. Pop smaller from back.
   b. Append right.
   c. Remove front if out of window.
   d. If window full, output `nums[dq[0]]`.

### 10. Mental Trace
`nums = [1, 3, -1, -3, 5, 3, 6, 7]`, `k = 3`:

| right | val | dq (indices) | dq (values)    | window | result |
|-------|-----|--------------|----------------|--------|--------|
| 0     | 1   | [0]          | [1]            | -      | -      |
| 1     | 3   | [1]          | [3]            | -      | -      |
| 2     | -1  | [1, 2]       | [3, -1]        | 0..2   | 3      |
| 3     | -3  | [1, 2, 3]    | [3, -1, -3]    | 1..3   | 3, 3   |
| 4     | 5   | [4]          | [5]            | 2..4   | 3,3,5  |
| 5     | 3   | [4, 5]       | [5, 3]         | 3..5   | 3,3,5,5|
| 6     | 6   | [6]          | [6]            | 4..6   | 3,3,5,5,6 |
| 7     | 7   | [7]          | [7]            | 5..7   | 3,3,5,5,6,7 |

Result: `[3, 3, 5, 5, 6, 7]`. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time    | Space | Notes |
|----|---------------------------------------|---------|-------|-------|
| 1  | Monotonic deque (BEST)                | O(n)    | O(k)  | canonical |
| 2  | Heap with lazy deletion               | O(n log n) | O(k) | over-engineered |
| 3  | Brute force O(nk)                     | O(nk)   | O(1)  | educational |
| 4  | SortedList (lib)                      | O(n log k) | O(k) | fallback to V1 |
| 5  | Self-balancing BST (V1 fallback)      | O(n)    | O(k)  | placeholder |
| 6  | Block DP (left/right max arrays)      | O(n)    | O(n)  | alternative |
| 7  | Segment tree                          | O(n log n) | O(n) | overkill |
| 8  | Track max index, rescan on eviction   | O(n) amortized | O(1) | tricky |
| 9  | Recursive                             | O(n)    | O(k)  | educational |
| 10 | numpy                                 | O(n)    | O(n)  | vectorized |

---

## Recommended Interview Answer

**Solution 1** — clean, optimal, idiomatic:

```python
from collections import deque

def max_sliding_window(nums, k):
    if not nums or k == 0:
        return []
    dq = deque()
    result = []
    for right in range(len(nums)):
        while dq and nums[dq[-1]] <= nums[right]:
            dq.pop()
        dq.append(right)
        if dq[0] <= right - k:
            dq.popleft()
        if right >= k - 1:
            result.append(nums[dq[0]])
    return result
```

---

## Common Pitfalls

1. **Popping with `<` instead of `<=`** — popping with strict less
   works, but `<=` ensures equal elements don't all stay. Either is
   fine for correctness, but `<=` keeps deque size smaller.
2. **Not removing out-of-window front** — front stays stale.
3. **Storing values instead of indices** — can't detect window exit.
4. **Using `max()` inside the loop** — O(k) per step, total O(nk).
5. **Off-by-one in `right >= k - 1`** — window is full when
   `right = k - 1` (indices `0..k-1`).

---

## Talking Points — Interview Cheat Sheet

If asked "what's a monotonic deque?":
> "A deque where elements are in a specific order (increasing or
> decreasing). For sliding window max, we maintain decreasing values.
> New elements push out smaller ones at the back, and old elements
> leave from the front when out of window."

If asked "why not use a heap?":
> "A heap gives O(log k) per operation and needs lazy deletion for
> out-of-window elements. The deque gives O(1) amortized because each
> index enters and exits exactly once."

If asked "what if the array is too big for memory?":
> "Process in chunks. For each chunk, carry over the deque state and
> the relevant portion of the previous chunk."

If asked "what about sliding window minimum?":
> "Same approach but with increasing order in the deque. Front is the
> minimum."

---

## Related Problems

- **Sliding Window Minimum** — same template, reversed.
- **Min Stack** — different structure, similar idea (maintaining
  monotonic order).
- **Largest Rectangle in Histogram** (LC #84) — uses monotonic stack,
  related concept.
- **Trapping Rain Water** (LC #42) — different problem, but uses
  similar two-pointer / monotonic stack ideas.

---

## Variants

- **Minimum**: maintain INCREASING order in deque.
- **Top-K per window**: keep top K in deque, similar logic.
- **Median per window**: use two heaps (small max-heap + large
  min-heap).
- **Online streaming**: process elements as they arrive, output
  window max on demand.