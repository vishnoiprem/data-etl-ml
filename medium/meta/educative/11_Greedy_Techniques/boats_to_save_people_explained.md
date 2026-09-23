# Boats to Save People — 10 Solutions + Interview Thinking

## Problem
Each boat carries **at most 2 people** whose total weight is at most `limit`.
Return the **minimum number of boats** required to evacuate everyone.

Reference: LeetCode #881 / Educative Grokking — "Boats to Save People".

---

## Interview Thinking (10 Steps)

### 1. Understand
"Each boat can carry at most 2 people, and the total weight on a boat must
not exceed `limit`. I need to find the **minimum** number of boats to
rescue everyone."

### 2. Observe — Key Insight
**Pair the heaviest person with the lightest person who can fit with them.**
This is optimal because:
- The heaviest person *must* get on *some* boat.
- If the lightest person can share that boat, we save a whole boat.
- If not, no one else can pair with the heaviest, so they go alone.

### 3. Pattern Recognition
**Two-pointer after sorting.** Lightest at left, heaviest at right.
Converge inward, pairing whenever possible.

### 4. Edge Cases
- **Single person** → 1 boat.
- **All weights ≤ limit/2** → pairs of 2 → `n/2` boats.
- **All weights > limit/2** → no two can share → `n` boats.
- **Empty input** → 0 boats.

### 5. Tricky Detail
The loop invariant: each iteration, the heaviest unprocessed person is
guaranteed to need a boat. We decrement `right` *first*, then try to pair
the heaviest with the lightest. This avoids the off-by-one trap where
`left == right` would cause a double-count.

### 6. Algorithm
```
sort(people)
left, right = 0, n - 1
boats = 0
while left <= right:
    right -= 1
    boats += 1
    if left <= right and people[left] + people[right + 1] <= limit:
        left += 1
return boats
```

### 7. Why Greedy Works (Proof Sketch)
**Exchange argument**: Consider any optimal solution. Look at the
heaviest person H. They're on some boat. If a light person L is with them,
swapping L with the globally lightest person W (if W can fit) preserves
validity and doesn't increase the boat count. So an optimal solution
exists where the heaviest pairs with the lightest possible partner. By
iterating this argument, we recover our greedy order.

### 8. Complexity
- **Time:** `O(n log n)` for the sort, `O(n)` for the two-pointer scan.
- **Space:** `O(1)` extra (or `O(n)` for the sorted copy).

### 9. Code Structure
```python
def rescue_boats(people, limit):
    p = sorted(people)
    left, right = 0, len(p) - 1
    boats = 0
    while left <= right:
        right -= 1            # heaviest always gets on a boat
        boats += 1
        if left <= right and p[left] + p[right + 1] <= limit:
            left += 1         # pair with lightest if possible
    return boats
```

### 10. Mental Trace
`[3, 2, 2, 1], limit=3` → sorted `[1, 2, 2, 3]`:
- Iter 1: right=2, boats=1. Check: `1 + 3 > 3` → no pair.
- Iter 2: right=1, boats=2. Check: `1 + 2 ≤ 3` → pair, left=1.
- Iter 3: right=0, boats=3. `left=1 > right=0` → no pair.
- **Answer: 3 boats** → `{3}`, `{1, 2}`, `{2}` ✓

`[1, 2, 3, 4], limit=5` → sorted `[1, 2, 3, 4]`:
- Iter 1: right=2, boats=1. `1 + 4 = 5 ≤ 5` → pair, left=1.
- Iter 2: right=0, boats=2. `left=1 > right=0` → no pair.
- **Answer: 2 boats** → `{1, 4}`, `{2, 3}` ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time            | Notes |
|----|---------------------------------------|-----------------|-------|
| 1  | Two-pointer (CANONICAL)               | O(n log n)      | ★★★★★ |
| 2  | Two-pointer without input mutation    | O(n log n)      | safe for input |
| 3  | Counting sort / bucket                | O(n + W)        | W = max weight |
| 4  | Counter-based greedy                  | O(n log n)      | elegant, uses `Counter` |
| 5  | Binary search for partner             | O(n log² n)     | uses `used[]` array |
| 6  | Recursive two-pointer                 | O(n log n)      | educational |
| 7  | Two-pointer explicit-break            | O(n log n)      | alternative style |
| 8  | Deque-based two-pointer               | O(n log n)      | clean & concise |
| 9  | Numpy-vectorized                      | O(n log n)      | uses `np.sort` |
| 10 | Simplified two-pointer                | O(n log n)      | minimal style |

---

## Recommended Interview Answer
**Solution 1** — the canonical two-pointer approach. Clean, optimal, and
interview-friendly:

```python
def rescue_boats(people, limit):
    p = sorted(people)
    left, right = 0, len(p) - 1
    boats = 0
    while left <= right:
        right -= 1
        boats += 1
        if left <= right and p[left] + p[right + 1] <= limit:
            left += 1
    return boats
```

---

## Common Pitfalls
1. **Incrementing boats before decrementing `right`** — leads to off-by-one
   when `left == right` after pairing. Always decrement `right` first.
2. **Mutating the input** — `people.sort()` modifies the caller's list;
   prefer `sorted(people)` if mutation is undesired.
3. **Forgetting the empty-input case** — `[]` should return `0`, not `1`.
4. **Reading the wrong index when pairing** — after `right -= 1`, the
   partner to check is at `right + 1`, not `right`.
5. **Conflating two-pointer with greedy** — the algorithm is *both*; the
   sort enables the two-pointer, and the two-pointer implements the greedy.
