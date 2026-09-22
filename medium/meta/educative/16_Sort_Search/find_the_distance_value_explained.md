# Find the Distance Value Between Two Arrays - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/find-the-distance-value-between-two-arrays

## The Problem
```
Given two integer arrays arr1 and arr2, and an integer d, return the
distance value between the two arrays.

The distance value is the number of elements arr1[i] such that there is
NOT any element arr2[j] where |arr1[i] - arr2[j]| <= d.

Examples:
    arr1=[4,5,8], arr2=[10,9,1,8], d=2 -> 2
    (4 and 5 are far from all in arr2; 8 is too close to itself)
    arr1=[1,4,2,3], arr2=[-4,-3,6,10,20,15], d=3 -> 2

Constraints:
- 1 <= len(arr1), len(arr2) <= 500
- 0 <= d <= 100
- -1000 <= arr1[i], arr2[i] <= 1000
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
For each a in arr1, check if any b in arr2 has |a - b| <= d.
If yes, a is "close" (don't count). If no, a is "far" (count).
Return the count of "far" elements.
```

### Step 2: The Trick
> "KEY INSIGHT: After sorting arr2, for each a in arr1, we only need to check
> the SINGLE closest b. If the closest b is > d away, all b are > d away.
>
> Concretely: find first b in sorted arr2 with b >= a-d. If b exists and
> b <= a+d, there's a close element. Otherwise, all b are > d away."

### Step 3: Why this works
> "After sorting, if smallest b >= a-d is > a+d, then no b is in [a-d, a+d].
> All b are either < a-d (which means |a - b| > d) or > a+d (which means
> |a - b| > d). So all b are > d away."

### Step 4: Algorithm
> "1. Sort arr2.
> 2. For each a in arr1:
>    a. idx = bisect_left(arr2, a - d). Find first b >= a-d.
>    b. If idx < len(arr2) and arr2[idx] <= a+d: skip a (close element exists).
>    c. Else: count a.
> 3. Return count."

### Step 5: Edge cases
> "- Empty arr1: return 0.
> - Empty arr2: all arr1 elements are far (return len(arr1)).
> - d=0: only count a with no exact match in arr2."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to count elements in arr1 that are 'far' from all elements in arr2,
> where 'far' means distance > d."

**Key Insight:**
> "Sort arr2. For each a in arr1, find the first b in sorted arr2 with b >= a-d.
> If that b is <= a+d, there's a close element. Otherwise, count a."

**Algorithm:**
> "1. Sort arr2.
> 2. For each a in arr1:
>    a. idx = bisect_left(arr2, a - d). Find first b >= a-d.
>    b. If idx < len(arr2) and arr2[idx] <= a+d: skip (close element exists).
>    c. Else: count a.
> 3. Return count."

**Why this works:**
> "After sorting, the closest arr2 element to a is either the largest b <= a
> or the smallest b >= a. If both are > d away, all b are > d away. By
> checking the first b >= a-d, we cover the second case. If that b > a+d,
> nothing's in the danger zone."

**Edge cases:**
- Empty arr1: return 0.
- Empty arr2: return len(arr1) (all far).
- d=0: Only count a with no exact match in arr2.

**Complexity:**
- Time:  O(n log m + m log m) where n = len(arr1), m = len(arr2).
- Space: O(1) extra.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Sort + bisect (BEST - Memorize!)
```python
def find_the_distance_value_1(arr1, arr2, d):
    arr2.sort()
    count = 0
    import bisect
    for a in arr1:
        idx = bisect.bisect_left(arr2, a - d)
        if idx < len(arr2) and arr2[idx] <= a + d:
            continue
        count += 1
    return count
```

### Way 2: Verbose
### Way 3: Brute force O(n*m)
### Way 4: all() with generator
### Way 5: Set lookup
### Way 6: Counter for O(1) average lookup
### Way 7: Manual binary search
### Way 8: bisect_right count
### Way 9: Sort + early exit
### Way 10: enumerate
### Way 11: Class-based
### Way 12: Inline sorted
### Way 13: numpy vectorized
### Way 14: Generator-based
### Way 15: Set with range check
### Way 16: Two-pointer concept
### Way 17: any/all
### Way 18: List comprehension
### Way 19: Closest b check
### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Standard           | Way 1    | Clean + fast |
| Small d            | Way 5/6  | Set lookup   |
| numpy available    | Way 13   | Vectorized   |
| Conceptual         | Way 3    | Brute force  |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Sort + bisect (Way 1) | O(n log m + m log m) | O(1) | Best general |
| Brute force (Way 3) | O(n*m) | O(1) | Easy but slow |
| Set lookup (Way 5) | O(n*d + m) | O(m) | When d is small |
| numpy (Way 13) | O(n*m) | O(n*m) | Vectorized |

---

## Walkthrough Example

```
arr1 = [4, 5, 8]
arr2 = [10, 9, 1, 8]
d = 2

Sort arr2: [1, 8, 9, 10]

For each a in arr1:

  a = 4:
    bisect_left([1, 8, 9, 10], 4-2=2) = 1. arr2[1]=8.
    Check: 8 <= 4+2=6? 8 > 6, so NOT in danger zone.
    Count a = 4. ✓

  a = 5:
    bisect_left([1, 8, 9, 10], 5-2=3) = 1. arr2[1]=8.
    Check: 8 <= 5+2=7? 8 > 7, so NOT in danger zone.
    Count a = 5. ✓

  a = 8:
    bisect_left([1, 8, 9, 10], 8-2=6) = 1. arr2[1]=8.
    Check: 8 <= 8+2=10? 8 <= 10, so IN danger zone.
    Skip a = 8. ✓

Count = 2.
```

---

## Best Answer to Memorize

```python
def find_the_distance_value(arr1, arr2, d):
    import bisect
    arr2.sort()
    count = 0
    for a in arr1:
        idx = bisect.bisect_left(arr2, a - d)
        if idx < len(arr2) and arr2[idx] <= a + d:
            continue
        count += 1
    return count
```

**~7 lines. O(n log m + m log m) time. O(1) space. Interview-ready!**

---

## Key Insights

### Why sort arr2?
> "After sorting, we can find the closest b >= a-d using binary search in
> O(log m). Brute force is O(m) per element."

### Why check first b >= a-d?
> "If first b >= a-d is also <= a+d, then b is in the danger zone [a-d, a+d]
> and a is too close to b. If first b > a+d, then no b is in the danger zone."

### Why is checking one element enough?
> "If the smallest b >= a-d is > a+d, then ALL b are either < a-d or > a+d.
> In both cases, |a - b| > d. So checking one element suffices."

### Brute force vs optimized?
> "Brute force: O(n*m) — check all pairs.
> Optimized: O(n log m + m log m) — sort once, binary search per element.
> Optimization worth it when n or m is large."

### Why not sort both?
> "We sort arr2 once. Sorting arr1 isn't needed since we iterate it once."

---

## Test Cases

| arr1 | arr2 | d | Expected | Notes |
|------|------|---|----------|-------|
| [4,5,8] | [10,9,1,8] | 2 | 2 | Standard |
| [1,4,2,3] | [-4,-3,6,10,20,15] | 3 | 2 | Standard |
| [5] | [1,10] | 2 | 1 | Single |
| [] | [1,2,3] | 1 | 0 | Empty arr1 |
| [1,2,3] | [] | 0 | 3 | Empty arr2 |
| [1,2,3] | [1,2,3] | 0 | 0 | All exact |
| [1,2,3] | [100,200,300] | 10 | 3 | All far |
| [1,2,3] | [4,5,6] | 0 | 3 | No exact |
| [-5,-3,0] | [-1,1,2] | 2 | 1 | Negatives |
| [1,5,10,15,20] | [3,7,12,18] | 2 | 1 | Larger |

---

## Common Pitfalls

1. **Forgetting to sort arr2**: Binary search requires sorted input.
2. **Off-by-one in bisect**: Use `bisect_left(arr2, a-d)` for "first >= a-d".
3. **Not checking both bounds**: The danger zone is [a-d, a+d] (inclusive both ends).
4. **Sorting arr2 in the loop**: Sort once outside the loop.
5. **Empty arr2 not handled**: With numpy, would crash on `np.min`.

---

## Why This Problem Matters

> "Tests:
> 1. Binary search on sorted array.
> 2. Range-based check (danger zone concept).
> 3. Multiple approaches: brute force vs optimized.
> 4. Foundation for: closest pair, range queries."

---

## Beyond This Problem: Related Patterns

### 1. Two Sum Closest (LC 16)
```python
# Find pair with sum closest to target. Sort + two pointers.
```

### 2. K-diff Pairs in Array (LC 532)
```python
# Count pairs with abs difference == k.
```

### 3. Contains Duplicate III (LC 220)
```python
# Within k indices AND value difference <= t.
```

### 4. Closest Pair of Points
```python
# Different - 2D points. Divide and conquer.
```

---

## Connection to Binary Search

This problem uses the "lower bound" pattern:

```
For sorted array arr2:
- bisect_left(arr2, x) gives first index where arr2[idx] >= x.
- This is the SMALLEST element >= x.

We want: smallest b >= a-d.
        = bisect_left(arr2, a-d).

Then check if this b is in danger zone (b <= a+d).
```

This is a fundamental binary search pattern. Master it!

---

## Quick Checklist

When given a similar problem:
- [ ] What metric? (|a - b| <= d here)
- [ ] What does "close" mean? (within d here)
- [ ] Which array to sort? (arr2 — fixed once)
- [ ] What's the danger zone? ([a-d, a+d] here)
- [ ] Need both bounds check? (yes — first b >= a-d AND that b <= a+d)
- [ ] Handle empty arrays? (yes)

---

## Mathematical Formulation

For each a in arr1, define:
```
close(a) = exists b in arr2: |a - b| <= d
         = exists b in arr2: a-d <= b <= a+d

After sorting arr2:
  Let idx = bisect_left(arr2, a-d).
  If idx < len(arr2) and arr2[idx] <= a+d: close(a) is True.

count = sum(1 for a in arr1 if NOT close(a))
```

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 1385 - Find the Distance Value Between Two Arrays](https://leetcode.com/problems/find-the-distance-value-between-two-arrays/)
