# Maximum Sum Circular Subarray - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/maximum-sum-circular-subarray

## The Problem
```
Given a circular integer array nums, find the maximum sum of a non-empty
subarray. The subarray can wrap from end to beginning.

Examples:
    nums=[1,-2,3,-2] -> 3 (subarray [3])
    nums=[5,-3,5] -> 10 (wrap: [5,5])
    nums=[-3,-2,-3] -> -2

Constraints:
- 1 <= n <= 3 * 10^4
- -3 * 10^4 <= nums[i] <= 3 * 10^4
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
A "circular" subarray means we can wrap from end to beginning.
We need the maximum sum among all such subarrays.
```

### Step 2: The Trick
> "KEY INSIGHT: Two cases.
>
> Case 1: Max subarray doesn't wrap. Use Kadane's.
>
> Case 2: Max subarray wraps. The complement (non-wrapped part) is a
> non-wrapping subarray with MINIMUM sum. So:
> max_wrap = total_sum - min_subarray_sum.
>
> Answer = max(max_no_wrap, max_wrap)."

### Step 3: Edge case
> "If all numbers are negative, min_subarray = total, so max_wrap = 0.
> But we can't pick an empty subarray. Return max_no_wrap (largest negative)."

### Step 4: Algorithm
> "1. Compute Kadane's max for non-wrap.
> 2. Compute Kadane's min for non-wrap.
> 3. If max_no_wrap < 0 (all negative), return max_no_wrap.
> 4. Otherwise return max(max_no_wrap, total - min_no_wrap)."

### Step 5: Kadane's recap
```
cur = max(x, cur + x)
best = max(best, cur)
Same for min, using min instead of max.
```

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to find the maximum sum of a non-empty subarray in a circular array."

**Key Insight:**
> "Two cases: max subarray doesn't wrap (Kadane's), or wraps (total - min subarray). Take max of the two, with an edge case for all-negative arrays."

**Algorithm:**
> "1. Compute Kadane's max (max_no_wrap).
> 2. Compute Kadane's min (min_no_wrap).
> 3. If max_no_wrap < 0, return it.
> 4. Else return max(max_no_wrap, total - min_no_wrap)."

**Why this works:**
> "If max wraps, it includes everything except some middle portion. The middle portion must be the MIN non-wrap subarray."

**Edge cases:**
- All negative: return largest (least negative).
- Single element: return it.
- All positive: return total.

**Complexity:**
- Time:  O(n).
- Space: O(1).

---

## The 20 Implementations (Simple to Complex)

### Way 1: Kadane's max + min (BEST - Memorize!)
```python
def maxSubarraySumCircular(nums):
    total = sum(nums)
    max_ending = max_sofar = nums[0]
    min_ending = min_sofar = nums[0]
    for x in nums[1:]:
        max_ending = max(x, max_ending + x)
        max_sofar = max(max_sofar, max_ending)
        min_ending = min(x, min_ending + x)
        min_sofar = min(min_sofar, min_ending)
    if max_sofar < 0:
        return max_sofar
    return max(max_sofar, total - min_sofar)
```

### Way 2: Verbose (DP arrays)
### Way 3: Kadane's applied twice
### Way 4: Brute force O(n^2)
### Way 5: Doubled array + Kadane
### Way 6: Class-based
### Way 7: numpy vectorized
### Way 8: Kadane's with DP
### Way 9: Helper functions
### Way 10: Functional reduce
### Way 11: One-liner style
### Way 12: itertools sliding window
### Way 13: Prefix sums + deque
### Way 14: Divide and conquer
### Way 15: enumerate + running sum
### Way 16: Single pass inline
### Way 17: accumulate + brute
### Way 18: Tail-recursive style
### Way 19: Deque for max length n
### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+--------------------+----------+----------------+
| Scenario           | Best     | Why            |
+--------------------+----------+----------------+
| Standard           | Way 1    | Kadane + min   |
| O(n^2) ok          | Way 4    | Brute force    |
| Vectorized         | Way 7    | numpy          |
| Pythonic           | Way 20   | Cleanest       |
+--------------------+----------+----------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Kadane max+min (Way 1) | O(n) | O(1) | Best |
| DP arrays (Way 2) | O(n) | O(n) | Verbose |
| Brute (Way 4) | O(n^2) | O(1) | Slow |
| Deque (Way 19) | O(n) | O(n) | Alternative |

---

## Walkthrough Example

```
nums = [5, -3, 5]
total = 7

Kadane's max:
  i=0: cur=5, best=5
  i=1: cur=max(-3, 5-3)=max(-3,2)=2, best=5
  i=2: cur=max(5, 2+5)=7, best=7
  max_no_wrap = 7

Kadane's min:
  i=0: cur=5, best=5
  i=1: cur=min(-3, 5-3)=min(-3,2)=-3, best=-3
  i=2: cur=min(5, -3+5)=min(5,2)=2, best=-3
  min_no_wrap = -3

max_wrap = 7 - (-3) = 10

max(7, 10) = 10. ✓
```

---

## Best Answer to Memorize

```python
def maxSubarraySumCircular(nums):
    total = sum(nums)
    cur_max = best_max = nums[0]
    cur_min = best_min = nums[0]
    for x in nums[1:]:
        cur_max = max(x, cur_max + x)
        best_max = max(best_max, cur_max)
        cur_min = min(x, cur_min + x)
        best_min = min(best_min, cur_min)
    return best_max if best_max < 0 else max(best_max, total - best_min)
```

**~10 lines. O(n) time. O(1) space. Interview-ready!**

---

## Key Insights

### Why total - min?
> "If max subarray wraps, it includes most of the array except a 'hole'.
> The hole is the minimum non-wrapping subarray. So max_wrap = total - min."

### Why check max_sofar < 0?
> "If all numbers are negative, min_no_wrap = total (whole array), so
> max_wrap = 0 (empty). But we can't pick empty. Return max_no_wrap."

### Why Kadane's works for both?
> "Same recurrence: cur = max(x, cur + x). Just track min instead of max."

### Why single pass?
> "We compute both max and min in one loop, tracking 4 variables."

---

## Test Cases

| nums | Expected | Notes |
|------|----------|-------|
| [1,-2,3,-2] | 3 | Standard |
| [5,-3,5] | 10 | Wrap |
| [-3,-2,-3] | -2 | All negative |
| [1] | 1 | Single positive |
| [-1] | -1 | Single negative |
| [0,0,0] | 0 | All zeros |
| [3,-1,2,-1] | 4 | Standard 2 |
| [1,2,3,4,5] | 15 | All positive |
| [-1,-2,-3,-4] | -1 | All neg ascending |
| [5,-2,5] | 10 | Wrap partial |
| [2,-2,2,-2,2] | 4 | Alternating |
| [8,-1,3,4] | 15 | Wrap |
| [1,-2,3,-2,4] | 6 | Wrap example |

---

## Common Pitfalls

1. **Forgetting edge case**: All-negative case gives wrong answer without the check.
2. **Off-by-one in wrap detection**: Wrap must include at least one element from each "end".
3. **Total vs sum(nums)**: total = sum(nums) is required.
4. **Single element**: Special case needed.

---

## Why This Problem Matters

> "Tests:
> 1. Kadane's extension to circular.
> 2. Edge case handling.
> 3. Understanding wrap vs non-wrap.
> 4. Foundation for: House Robber II, circular DP variants."

---

## Beyond This Problem: Related Patterns

### 1. House Robber II (LC 213)
```python
# Same circular structure, different recurrence.
```

### 2. Maximum Sum Subarray (LC 53)
```python
# Non-circular version. Same Kadane's.
```

### 3. Maximum Product Subarray
```python
# Different (product not sum), same structure.
```

---

## Connection to Circular DP

This problem is a classic circular DP:

```
PATTERN:
- Circular array, subarray can wrap.
- Two cases: wraps or doesn't.
- Compute both, take max (with edge case).

EXAMPLES:
- Max Sum Circular Subarray (sum, Kadane's).
- House Robber II (rob/skip, linear DP).
- Gas Station (greedy + circle check).
```

---

## Quick Checklist

When given a similar problem:
- [ ] Is the array circular?
- [ ] Define the two cases (wrap, no-wrap).
- [ ] Compute both candidates.
- [ ] Handle edge case (all-negative, single element).
- [ ] Use Kadane's for max/min subarray.
- [ ] Return max of the two.

---

## Mathematical Formulation

```
max_no_wrap = Kadane_max(nums)
min_no_wrap = Kadane_min(nums)

If max_no_wrap < 0:
    answer = max_no_wrap  # all negative
Else:
    answer = max(max_no_wrap, sum(nums) - min_no_wrap)
```

The wrap case relies on the fact that any wrapping subarray is the
COMPLEMENT of a non-wrapping subarray, so maximizing the wrap is
equivalent to minimizing the complement.

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 918 - Maximum Sum Circular Subarray](https://leetcode.com/problems/maximum-sum-circular-subarray/)
