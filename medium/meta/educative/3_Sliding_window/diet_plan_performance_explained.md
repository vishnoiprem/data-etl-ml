# Diet Plan Performance — 10 Solutions + Interview Thinking

## Problem
Given an array `calories`, an integer `k`, and bounds `lower`/`upper`,
for each consecutive k-day window:
- If sum > upper: lose 1 point.
- If sum < lower: gain 1 point.
- Otherwise: no change.

Return the total points.

Reference: LeetCode #1176 / Educative Grokking — "Diet Plan Performance".

---

## Interview Talking Points

Lead with the **invariant**: "Sliding window of size k, track running
sum, score each window, accumulate."

Note: comparing the SUM (not average) to bounds.

---

## 10-Step Thinking Process

### 1. Understand
"For each window of size k, score based on sum vs. bounds. Total points."

### 2. Key Insight
Sliding window. The sum of each window of size k is computed in O(1)
using a running sum.

### 3. Pattern Recognition
- Fixed-size sliding window
- Running sum
- Per-window scoring

### 4. Edge Cases
- `k == n`: single window.
- `k == 1`: each day.
- All in range: 0.
- All above upper: -(n - k + 1) points.

### 5. Tricky Detail — Score Function

A clean way to express the score:
```
points = (sum < lower) - (sum > upper)
```
This adds 1 if too low, subtracts 1 if too high, 0 otherwise. Each
boolean is 0/1, and the difference is -1/0/1.

### 6. Algorithm
```
cur = sum(calories[:k])
points = score(cur)
for i in range(k, n):
    cur += calories[i] - calories[i - k]
    points += score(cur)
return points
```

### 7. Why It Works
Each window is visited once. The running sum is updated in O(1) per
step (subtract outgoing, add incoming). Total O(n).

### 8. Complexity
- **Time**: O(n).
- **Space**: O(1).

### 9. Code Structure
1. Compute initial sum.
2. Score initial window.
3. Slide and score.

### 10. Mental Trace
`calories = [6, 5, 0, 0]`, `k=2`, `lower=1`, `upper=5`:
- Initial: sum = 6 + 5 = 11. > 5: -1. points = -1.
- i=2 (0): cur = 11 + 0 - 6 = 5. In [1,5]: 0. points = -1.
- i=3 (0): cur = 5 + 0 - 5 = 0. < 1: +1. points = 0.
- Returns 0. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time    | Space | Notes |
|----|---------------------------------------|---------|-------|-------|
| 1  | Sliding window + score func (BEST)    | O(n)    | O(1)  | canonical |
| 2  | Same with inline scoring              | O(n)    | O(1)  | cleaner |
| 3  | Prefix sums                           | O(n)    | O(n)  | alternative |
| 4  | accumulate                            | O(n)    | O(n)  | functional |
| 5  | Brute force                           | O(nk)   | O(1)  | educational |
| 6  | numpy                                 | O(n)    | O(n)  | vectorized |
| 7  | Deque-based                           | O(n)    | O(k)  | overkill |
| 8  | Recursive                             | O(n)    | O(n)  | educational |
| 9  | Slicing brute                         | O(nk)   | O(k)  | slow |
| 10 | Boolean math trick                    | O(n)    | O(1)  | clever |

---

## Recommended Interview Answer

**Solution 1** — clean, optimal:

```python
def diet_plan(calories, k, lower, upper):
    cur = sum(calories[:k])
    points = 0

    def score(s):
        if s > upper:
            return -1
        if s < lower:
            return 1
        return 0

    points += score(cur)
    for i in range(k, len(calories)):
        cur += calories[i] - calories[i - k]
        points += score(cur)
    return points
```

Or using boolean math:

```python
def diet_plan(calories, k, lower, upper):
    cur = sum(calories[:k])
    points = (cur < lower) - (cur > upper)
    for i in range(k, len(calories)):
        cur += calories[i] - calories[i - k]
        points += (cur < lower) - (cur > upper)
    return points
```

---

## Common Pitfalls

1. **Comparing average instead of sum** — bounds are on the SUM.
2. **Off-by-one in initial window** — `calories[:k]`.
3. **Wrong number of windows** — there are `n - k + 1` windows.
4. **Confusing direction of comparison** — `< lower` is bad (gain),
   `> upper` is bad (lose).
5. **Forgetting to handle k == n** — still works; just one window.

---

## Talking Points — Interview Cheat Sheet

If asked "why sliding window?":
> "Each window differs from the previous by exactly one element
> (subtract one, add one). So we update the sum in O(1) instead of
> O(k) recomputation."

If asked "what if k is variable?":
> "Different problem. For 'each consecutive k days for variable k',
> we'd need to track multiple windows or use a different structure."

If asked "could we use prefix sums?":
> "Yes. Compute prefix[i] = sum(calories[0..i-1]). Then window
> sum = prefix[i] - prefix[i-k]. Each query is O(1) after O(n)
> preprocessing."

If asked "what's the boolean math trick?":
> "`(cur < lower) - (cur > upper)` evaluates to +1 (too low),
> -1 (too high), or 0 (in range). Each boolean is 0 or 1 in Python,
> so the difference is -1, 0, or 1."

---

## Related Problems

- **Sliding Window Maximum** — different objective.
- **Maximum Average Subarray** — different scoring.
- **Subarray Sum Equals K** — different constraint.
- **K Radius Subarray Averages** (LC #2091) — averages within k
  distance.

---

## Variants

- **Different bounds per day**: precompute bounds array, score with
  per-window bounds.
- **Cumulative score over time**: just accumulate as we go.
- **Longest streak in range**: track longest window where all
  windows are in range.