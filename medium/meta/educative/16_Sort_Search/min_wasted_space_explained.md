# Minimum Space Wasted from Packaging - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-space-wasted-from-packaging

## The Problem
```
You have n packages to place into boxes (one package per box). m suppliers,
each offering boxes of various sizes (infinite supply per size). A package
fits in a box if box_size >= package_size.

Choose ONE supplier to minimize total wasted space (sum of box - package
across all packages). Return minimum waste mod 10^9+7, or -1 if no
supplier can fit all packages.

Examples:
    packages=[2,3,5], boxes=[[3,5,7]] -> 1
    (2->3 w=1, 3->3 w=0, 5->5 w=0)

Constraints:
- 1 <= n, m <= 50
- 1 <= packages[i] <= 10^3
- 1 <= boxes[j].length <= 30
- sum(boxes[j].length) <= 10^5
- 1 <= boxes[j][k] <= 10^3
- Boxes within a supplier are distinct.
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
For each supplier independently:
- Can they fit the largest package? If not, skip.
- If yes, what's the total wasted space when optimally packing?

Answer: For each package, use the SMALLEST box that fits.
Sum (box - package) across all packages.

Return the minimum across suppliers.
```

### Step 2: The Trick
> "KEY INSIGHT: For each supplier, the optimal packing is to assign each
> package to the SMALLEST box ≥ its size. Since boxes have INFINITE SUPPLY,
> the assignment is INDEPENDENT per package — no 1-to-1 constraint.
>
> Why smallest box? Any larger box wastes more space, with no benefit.
> (A larger box doesn't help a smaller package — it would still need an
> even larger box.)"

### Step 3: Find smallest box ≥ package
> "Boxes are sorted. Use binary search (bisect_left) to find first box
> where box >= package. O(log k) per package."

### Step 4: Why this is optimal
> "Greedy choice: for each package, pick smallest fitting box.
>
> Correctness: Suppose we use a larger box for package p. Switching to the
> smaller box:
> - Reduces waste for p.
> - Doesn't affect other packages (infinite supply, so boxes aren't consumed).
> So strictly better. By induction, greedy is optimal."

### Step 5: Algorithm
> "1. Sort packages.
> 2. For each supplier:
>    a. Sort boxes.
>    b. If max(box) < max(package): skip (can't fit).
>    c. For each package, binary search for smallest box >= package.
>    d. Sum the waste.
> 3. Return min waste, or -1 if no supplier works."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to find the supplier with minimum total wasted space when packing
> packages into boxes, where each supplier offers boxes of different sizes
> with infinite supply."

**Key Insight:**
> "For each supplier independently, the optimal strategy is to use the
> smallest box that fits each package. Since boxes have infinite supply,
> the assignment is independent per package — no need to worry about
> consuming boxes."

**Algorithm:**
> "1. Sort packages.
> 2. For each supplier:
>    a. Sort their boxes.
>    b. Skip if max(box) < max(package).
>    c. For each package, binary search (bisect_left) for smallest box >= pkg.
>    d. Sum (box - pkg) as waste.
> 3. Return min waste, or -1 if no supplier works."

**Why this works:**
> "Using a smaller box reduces waste without hurting other packages. So
> smallest fitting box is optimal. Binary search gives O(log k) per package."

**Edge cases:**
- No supplier can fit max package: return -1.
- All packages same size: only one binary search matters per supplier.
- Empty packages or suppliers: edge cases per constraints.

**Complexity:**
- Time:  O(n log n + m * (k log k + n log k)) where k = max box count per supplier.
- Space: O(1) extra (sorting is in-place).

---

## The 20 Implementations (Simple to Complex)

### Way 1: Sort + bisect (BEST - Memorize!)
```python
def min_wasted_space_1(packages, boxes):
    MOD = 10**9 + 7
    packages.sort()
    best = float('inf')
    for s_boxes in boxes:
        s_boxes = sorted(s_boxes)
        if s_boxes[-1] < packages[-1]:
            continue
        waste = 0
        for pkg in packages:
            idx = bisect.bisect_left(s_boxes, pkg)
            waste += s_boxes[idx] - pkg
        best = min(best, waste)
    return best % MOD if best != float('inf') else -1
```

### Way 2: Manual binary search
### Way 3: bisect_right
### Way 4: Two-pointer concept
### Way 5: sortedcontainers
### Way 6: Pre-sort all suppliers
### Way 7: Class-based
### Way 8: numpy searchsorted
### Way 9: Recursive
### Way 10: One-pass
### Way 11: functools.reduce
### Way 12: map()
### Way 13: LRU cache
### Way 14: enumerate
### Way 15: Linear scan (no bisect)
### Way 16: Cache by package size
### Way 17: any/all early exit
### Way 18: Most concise
### Way 19: Pre-compute bisect indices
### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Standard           | Way 1    | Clean + fast |
| Many suppliers     | Way 6    | Pre-sort     |
| numpy available    | Way 8    | Vectorized   |
| Conceptual         | Way 15   | Linear scan  |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Sort + bisect (Way 1) | O(n*m*log(k)) | O(1) | Best |
| numpy (Way 8) | O(n*m*log(k)) | O(n) | Vectorized |
| Linear scan (Way 15) | O(n*m*k) | O(1) | Worst case |
| Recursive (Way 9) | O(n*k) | O(n) | Exponential |

---

## Walkthrough Example

```
packages = [2, 3, 5]
boxes = [[3, 5, 7], [4, 6], [5, 8, 10]]

Supplier 1: [3, 5, 7]
  Sorted: [3, 5, 7]. Max = 7 >= 5. ✓
  pkg 2: bisect_left([3,5,7], 2) = 0. Box 3. Waste = 1.
  pkg 3: bisect_left([3,5,7], 3) = 0. Box 3. Waste = 0.
  pkg 5: bisect_left([3,5,7], 5) = 1. Box 5. Waste = 0.
  Total = 1.

Supplier 2: [4, 6]
  Sorted: [4, 6]. Max = 6 >= 5. ✓
  pkg 2: bisect_left([4,6], 2) = 0. Box 4. Waste = 2.
  pkg 3: bisect_left([4,6], 3) = 0. Box 4. Waste = 1.
  pkg 5: bisect_left([4,6], 5) = 1. Box 6. Waste = 1.
  Total = 4.

Supplier 3: [5, 8, 10]
  Sorted: [5, 8, 10]. Max = 10 >= 5. ✓
  pkg 2: Box 5. Waste = 3.
  pkg 3: Box 5. Waste = 2.
  pkg 5: Box 5. Waste = 0.
  Total = 5.

Best = 1 (Supplier 1).
```

```
Example with no fitting supplier:
packages = [10]
boxes = [[5], [6]]

Supplier 1: [5]. Max = 5 < 10. SKIP.
Supplier 2: [6]. Max = 6 < 10. SKIP.
No supplier works. Return -1.
```

---

## Best Answer to Memorize

```python
def min_wasted_space(packages, boxes):
    MOD = 10**9 + 7
    import bisect
    packages.sort()
    best = float('inf')
    for s_boxes in boxes:
        s_boxes = sorted(s_boxes)
        if s_boxes[-1] < packages[-1]:
            continue
        waste = 0
        for pkg in packages:
            idx = bisect.bisect_left(s_boxes, pkg)
            waste += s_boxes[idx] - pkg
        best = min(best, waste)
    return best % MOD if best != float('inf') else -1
```

**~10 lines. O(n log n + m*n*log(k)) time. O(1) space. Interview-ready!**

---

## Key Insights

### Why greedy (smallest box)?
> "Using a smaller box strictly reduces waste without affecting other
> packages (infinite supply). So for each package, smallest fitting box
> is optimal."

### Why binary search?
> "Boxes are sorted. We want first box >= package. Use bisect_left in O(log k)."

### Why infinite supply matters?
> "Without infinite supply, we'd need to track which boxes are used. With
> infinite supply, each package's assignment is independent. Just pick
> smallest fitting box each time."

### Why check max(box) < max(package)?
> "If the supplier's largest box can't fit our largest package, no other
> box can either. Skip the supplier early."

### Why mod 10^9 + 7?
> "Waste can be very large. The problem asks for modulo to prevent
> overflow. Apply mod only at the end (intermediate values fit in Python int)."

---

## Test Cases

| packages | boxes | Expected | Notes |
|----------|-------|----------|-------|
| [2,3,5] | [[3,5,7]] | 1 | 2->3, 3->3, 5->5 |
| [2,3,5] | [[3,5],[4,6]] | 1 | S1 wins |
| [2,3,5] | [[4,7],[5,8],[6,9]] | 5 | S1 and S2 tied |
| [5] | [[10]] | 5 | Single |
| [5] | [[3],[7],[10]] | 2 | 5->7 best |
| [10] | [[5],[6]] | -1 | None fits |
| [1..5] | [[2,4,6],[5,10]] | 3 | S1 wins |
| [3,5,7] | [[3,5,7]] | 0 | Exact fit |
| [5,5] | [[7]] | 4 | Two same packages |
| [10,20] | [[15,25],[12],[10,20]] | 0 | S3 wins |

---

## Common Pitfalls

1. **Confusing bisect_left vs bisect_right**: Use `bisect_left(arr, x)` for first index where arr[idx] >= x.
2. **Not sorting**: Both packages and boxes must be sorted.
3. **Off-by-one in max check**: `s_boxes[-1] < packages[-1]` (not `>=`).
4. **Forgetting the modulo**: Apply mod at the end.
5. **Returning 0 for no supplier**: Return -1 if no supplier fits.
6. **Modifying original**: We sort the input arrays in place. Use deep copy if needed.

---

## Why This Problem Matters

> "Tests:
> 1. Greedy with infinite supply.
> 2. Binary search for lower bound.
> 3. Sorting + searching combined.
> 4. Modular arithmetic.
> 5. Multiple supplier optimization."

---

## Beyond This Problem: Related Patterns

### 1. Assign Cookies (LC 455)
```python
# Similar greedy matching, but 1-to-1 (no infinite supply).
```

### 2. Minimum Number of Refueling Stops (LC 871)
```python
# Greedy with priority queue. Different context.
```

### 3. Capacity To Ship Packages Within D Days (LC 1011)
```python
# Binary search on answer. Different pattern.
```

### 4. Book Allocation Problem
```python
# Binary search on max pages per student.
```

---

## Connection to Greedy + Binary Search

This problem combines two patterns:

```
GREEDY:
For each package, pick smallest fitting box.
Works because: smaller box = less waste, no negative side effects.

BINARY SEARCH:
Find smallest box >= package in sorted array.
Standard lower_bound search.
```

Combined: O(n log k) per supplier, where k = number of boxes.

---

## Quick Checklist

When given a similar problem:
- [ ] Is supply infinite? (yes → greedy works)
- [ ] Are items/packages fixed? (yes → sort once)
- [ ] What's the metric? (waste = box - package here)
- [ ] Need to track consumption? (no — infinite supply)
- [ ] How to find "smallest fit"? (binary search on sorted array)
- [ ] Return value modulo? (apply at end)

---

## Mathematical Formulation

For one supplier with sorted boxes `b_1 < b_2 < ... < b_k`:

```
waste(supplier) = sum_{p in packages} (smallest b_i >= p) - p
                = sum_{p in packages} b_{f(p)} - p
where f(p) = smallest i such that b_i >= p

answer = min over suppliers of waste(supplier)
       = -1 if no supplier can fit max(package)
```

This is O(n log k) per supplier.

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 1689 - Minimum Space Wasted From Packaging](https://leetcode.com/problems/minimum-space-wasted-from-packaging/)
