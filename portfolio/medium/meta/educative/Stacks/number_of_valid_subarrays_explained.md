# Number of Valid Subarrays - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/number-of-valid-subarrays

## The Problem
```
Given an integer array nums, count contiguous subarrays where the first
element is <= every other element in the subarray.
(The first element must be the MINIMUM of the subarray.)

Examples:
    [1, 4, 2, 5, 3] -> 11
    [1, 2, 3]       -> 6   (all increasing -> all subarrays valid)
    [3, 2, 1]       -> 3   (only single-element subarrays valid)

Constraints:
- 1 <= nums.length <= 1000
- 0 <= nums[i] <= 10^5
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
nums = [1, 4, 2, 5, 3]

For each starting index i, count subarrays nums[i:j+1] where nums[i] is the min.

i=0 (1): [1], [1,4], [1,4,2], [1,4,2,5], [1,4,2,5,3] -> all valid (1 is min)
        Count: 5

i=1 (4): [4] valid. [4,2]: 2<4 invalid. 
        Count: 1

i=2 (2): [2], [2,5], [2,5,3] all valid (2 is min)
        Count: 3

i=3 (5): [5] valid. [5,3]: 3<5 invalid.
        Count: 1

i=4 (3): [3] valid.
        Count: 1

Total: 5+1+3+1+1 = 11
```

### Step 2: The Trick
> "For each i, valid subarrays extend from i to (but not including) the
> NEXT SMALLER element. So count for i = next_smaller[i] - i.
> Use a MONOTONIC STACK to find next_smaller for each index in O(n)."

### Step 3: Why Stack?
> "Monotonic INCREASING stack of indices. When we see a smaller value,
> we pop larger values - they just found their 'next smaller'.
> After processing all, leftover indices have no smaller to the right."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to count subarrays where the first element is the minimum.
> For each starting index i, valid subarrays extend rightward until we
> hit something smaller than nums[i]."

**Key Insight:**
> "The count of valid subarrays starting at index i equals
> `next_smaller_index - i`, where next_smaller_index is the first index
> to the right with a value smaller than nums[i]. If no smaller exists,
> the count is `n - i` (extends to the end)."

**Algorithm:**
> "1. For each index i, find `next_smaller[i]`:
>    - The first j > i where nums[j] < nums[i]
>    - Or n if no such j exists
> 2. Sum up (next_smaller[i] - i) for all i.
>
> Step 1 uses a monotonic INCREASING stack:
>    - Push index i when stack empty or nums[stack[-1]] <= nums[i]
>    - When seeing smaller, pop top and set next_smaller[top] = i"

**Why this works:**
> "When a smaller element arrives at index i, it 'resolves' all larger
> indices on top of the stack - they get next_smaller = i. The stack
> maintains increasing values so the FIRST smaller element popped is the
> CLOSEST smaller."

**Edge cases:**
- All increasing: count = n*(n+1)/2 (every subarray valid)
- All decreasing: count = n (only single-element subarrays)
- All equal: count = n*(n+1)/2 (all elements are minimum simultaneously)

---

## The 20 Implementations (Simple to Complex)

### Way 1: Monotonic Stack (BEST - Memorize!)
```python
def validSubarrays(nums):
    n = len(nums)
    next_smaller = [n] * n
    stack = []

    for i in range(n):
        while stack and nums[stack[-1]] > nums[i]:
            next_smaller[stack.pop()] = i
        stack.append(i)

    return sum(next_smaller[i] - i for i in range(n))
```

### Way 2: With explicit sum
### Way 3: Brute force O(n^2)
### Way 4: With deque
### Way 5: enumerate-based
### Way 6: With helper function for next_smaller
### Way 7: reduce-based
### Way 8: Explicit count loop

### Way 9-12: More variations
- Way 9: Most compact
- Way 10: Try-except
- Way 11: List comprehension (same as 1)
- Way 12: Brute with min calculation

### Way 13-16: Specialized
- Way 13: Reverse iteration
- Way 14: With class
- Way 15: Most elegant
- Way 16: Explicit sum loop

### Way 17-20: Variations
- Way 17: Recursive
- Way 18: Most compact stack
- Way 19: Helper counting
- Way 20: Final cleanest

---

## Decision Tree

```
+------------------+-------------+--------------+
| Scenario         | Best        | Why          |
+------------------+-------------+--------------+
| Most efficient   | Monotonic   | O(n)         |
| Educational      | Brute       | Simple       |
| Functional       | reduce      | No mutation  |
+------------------+-------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Monotonic | O(n) | O(n) |
| Brute | O(n^2) | O(1) |
| Recursive | O(n^2) | O(n) |

---

## Walkthrough Example

```
nums = [1, 4, 2, 5, 3]

i=0, num=1: stack empty, push 0. stack=[0]
i=1, num=4: nums[0]=1, 1<4 not >, push 1. stack=[0,1]
i=2, num=2:
  nums[1]=4, 4>2, pop 1, next_smaller[1]=2
  nums[0]=1, 1>2? No. push 2. stack=[0,2]
i=3, num=5: nums[2]=2, 2<5, push 3. stack=[0,2,3]
i=4, num=3:
  nums[3]=5, 5>3, pop 3, next_smaller[3]=4
  nums[2]=2, 2>3? No. push 4. stack=[0,2,4]
End: stack=[0,2,4], no more pops

next_smaller = [5, 2, 5, 4, 5]

count = (5-0) + (2-1) + (5-2) + (4-3) + (5-4)
      = 5 + 1 + 3 + 1 + 1 = 11 ✓
```

## Best Answer to Memorize

```python
def validSubarrays(nums):
    n = len(nums)
    next_smaller = [n] * n
    stack = []

    for i in range(n):
        while stack and nums[stack[-1]] > nums[i]:
            next_smaller[stack.pop()] = i
        stack.append(i)

    return sum(next_smaller[i] - i for i in range(n))
```

**11 lines. O(n) time. Clean. Interview-ready!**

## Key Insights

### Why "next_smaller[i] - i"?
> "For subarrays starting at i, we can extend right until we hit a smaller
> element. The moment nums[j] < nums[i], nums[i] is no longer the min.
> So valid subarrays at i have right endpoints in [i, j).
> Count = j - i (where j is next_smaller or n if none)."

### Why INCREASING Stack (with > check on pop)?
> "We want to find the NEXT smaller, not the previous smaller.
> When a smaller value arrives, it represents the next smaller for all
> larger values on the stack. They get popped and recorded."

### Why NOT use "less than or equal" (<=) check?
> "If we pop on <=, equal values would 'cancel' and we'd lose them.
> We want STRICTLY smaller to be 'next smaller'.
> Example: [2,2,2] should count all subarrays (6).
> With <= check: index 0 popped when index 1's 2 arrives, next_smaller[0]=1.
> But subarray [0:3] starting with 2 IS valid (all 2's are min).
> So use strict > (pop on strictly greater)."
> "Wait! Let me re-check. With > check on [2,2,2]:
> i=0: push 0. i=1, num=2: nums[0]=2, NOT >2 (equal). push 1. i=2: push 2.
> next_smaller = [3,3,3]
> count = 3+2+1 = 6 ✓"

## Test Cases

| nums | Expected | Why |
|------|----------|-----|
| [1, 4, 2, 5, 3] | 11 | Standard |
| [3, 1, 4] | 4 | Decreasing then increasing |
| [1, 2, 3] | 6 | All increasing |
| [3, 2, 1] | 3 | All decreasing |
| [2, 2, 2] | 6 | All equal (all subarrays valid) |
| [5, 4, 3, 2, 1] | 5 | Decreasing |
| [1, 1, 1, 1] | 10 | n*(n+1)/2 |

## Common Pitfalls

1. **Using <= instead of > in pop**: Loses equal-value cases
2. **Wrong direction of stack search**: Need "next smaller to right"
3. **Off-by-one in count**: next_smaller[i] - i is correct (i itself is 1)
4. **Mutating nums**: Stack approach should use read-only indices

## Why This Problem Matters

> "Tests:
> 1. 'Next smaller element' pattern (CRITICAL skill)
> 2. Monotonic stack usage
> 3. Counting problem with stack aid
> 4. Strict vs non-strict inequalities
> 5. Sum of distances pattern"
