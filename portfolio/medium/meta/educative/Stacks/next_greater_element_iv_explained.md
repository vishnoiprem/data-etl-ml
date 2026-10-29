# Next Greater Element IV - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/next-greater-element-iv

## The Problem
```
Given a 0-indexed array nums of non-negative integers. For each nums[i],
find its SECOND greater element - nums[j] such that:
- j > i
- nums[j] > nums[i]
- It is the SECOND such occurrence (j is the 2nd index > i where nums[j] > nums[i])

Note: "exactly one index k where i<k<j and nums[k] > nums[i]"
makes the 2nd greater unique (vs 1st which has 0 such k between).

Examples:
    [5, 4, 3, 2, 1]      -> [-1, -1, -1, -1, -1]  (all decreasing)
    [1, 2, 3, 4, 5]      -> [3, 4, 5, -1, -1]      (increasing)
    [2, 4, 0, 9, 6]      -> [9, 6, 6, -1, -1]      (LeetCode 2454)
    [3, 1, 5, 0, 9, 4, 6] -> [9, 9, 6, 4, -1, -1, -1]

Constraints:
- 1 <= nums.length <= 10^5
- 0 <= nums[i] <= 10^9
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
nums = [2, 4, 0, 9, 6]

For each i, find 2nd index j > i where nums[j] > nums[i]:
- i=0 (2): strictly greater at j=1, 3, 4 (values 4, 9, 6). 2nd = 9. ✓
- i=1 (4): strictly greater at j=3, 4 (9, 6). 2nd = 6. ✓
- i=2 (0): strictly greater at j=3, 4. 2nd = 6. ✓
- i=3 (9): no. -1.
- i=4 (6): no. -1.

Result: [9, 6, 6, -1, -1]
```

### Step 2: The Trick
> "Use TWO stacks to track TWO stages of waiting:
> - s1: indices awaiting their 1st greater
> - s2: indices that got 1st greater, now awaiting 2nd
> When new value v arrives:
>   1. v resolves s2 entries (v > top means v is their 2nd greater)
>   2. v promotes s1 entries to s2 (v > top means v is their 1st greater)
>   3. Push current index to s1"

### Step 3: Why Two Stacks?
> "An index can be in 3 states:
> - not in any stack (haven't been processed)
> - in s1 (waiting for 1st greater)
> - in s2 (waiting for 2nd greater)
> - resolved (got 2nd greater)
>
> s2 entry's '2nd greater' must come AFTER s1 entry's '1st greater'.
> The two-stack structure naturally enforces ordering."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to find for each element its SECOND greater element - the 2nd
> index j > i where nums[j] > nums[i]."

**Key Insight:**
> "TWO STACKS to track two stages of waiting!
> - s1: indices looking for their 1st greater
> - s2: indices that got 1st greater, looking for 2nd
>
> Process new value v:
> 1. v > s2 top means v is 2nd greater for s2 top. RESOLVE.
> 2. v > s1 top means v is 1st greater for s1 top. PROMOTE to s2.
> 3. Push current index to s1."

**Algorithm:**
> "1. Initialize res = [-1] * n, s1 = [], s2 = []
> 2. For each i, value v:
>    a. While s2 non-empty AND v > nums[s2.top]:
>       - res[s2.pop()] = v
>    b. While s1 non-empty AND v > nums[s1.top]:
>       - Move popped index to s2 (in reverse to maintain decreasing order)
>    c. s1.append(i)
> 3. Return res"

**Why two-stack works:**
> "When an index is promoted from s1 to s2, it just got its 1st greater.
> For its 2nd greater, we need another value AFTER the 1st greater that
> is bigger than the original. The s2 stack maintains these in decreasing
> order so we efficiently find the 2nd greater for them."

**Edge cases:**
- All decreasing: nothing promoted, all -1
- All increasing: each gets a 2nd greater
- Mixed: handled naturally

---

## The 20 Implementations (Simple to Complex)

### Way 1: Two stacks (BEST - Memorize!)
```python
def secondGreaterElement(nums):
    n = len(nums)
    res = [-1] * n
    s1, s2 = [], []
    for i, v in enumerate(nums):
        while s2 and v > nums[s2[-1]]:
            res[s2.pop()] = v
        temp = []
        while s1 and v > nums[s1[-1]]:
            temp.append(s1.pop())
        while temp:
            s2.append(temp.pop())
        s1.append(i)
    return res
```

### Way 2: Same with explicit tuples
### Way 3: With deque
### Way 4: Brute force O(n^2)
### Way 5: Same two-stack (verbose)
### Way 6: With state tracking
### Way 7: Same as Way 1 - lists instead of deques
### Way 8: With counters in tuples

### Way 9-12: Variations
- Way 9: Cleaner variable names
- Way 10: Explicit states
- Way 11: Index-only
- Way 12: Most elegant

### Way 13-16: Specialized
- Way 13: Intermediate tracking
- Way 14: With helper function
- Way 15: Most concise
- Way 16: Verbose comments

### Way 17-20: Variations
- Way 17: With deque
- Way 18: Iterative states
- Way 19: With value tracking
- Way 20: Final cleanest

---

## Decision Tree

```
+------------------+--------------+--------------+
| Scenario         | Best         | Why          |
+------------------+--------------+--------------+
| Most efficient   | Two stacks   | O(n)         |
| Educational      | Brute force  | Simple       |
+------------------+--------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Two-stack | O(n) | O(n) |
| Brute force | O(n²) | O(1) |

---

## Walkthrough Example

```
nums = [2, 4, 0, 9, 6]

i=0 (2): s1=[], s2=[]. push 0 to s1. s1=[0]
i=1 (4):
  - s2 empty, skip resolve
  - s1=[0], 4 > 2, pop 0 to temp. temp=[0]. push to s2 in reverse: s2=[0].
  - push 1 to s1. s1=[1]
i=2 (0):
  - s2=[0], 0 > 2? No. Don't resolve.
  - s1=[1], 0 > 4? No. Don't promote.
  - push 2 to s1. s1=[1, 2]
i=3 (9):
  - s2=[0], 9 > 2? Yes. resolve. res[0]=9. s2=[].
  - s1=[1,2], top=2. 9 > 0? Yes. pop to temp. temp=[2]. top=1. 9 > 4? Yes. pop. temp=[2,1].
  - Push to s2 in reverse: s2=[1, 2]. (Maintaining decreasing order)
  - push 3 to s1. s1=[3]
i=4 (6):
  - s2=[1,2], top=2. 6 > 0? Yes. resolve. res[2]=6. s2=[1].
  - s2 top=1. 6 > 4? Yes. resolve. res[1]=6. s2=[].
  - s1=[3], 6 > 9? No.
  - push 4 to s1. s1=[3, 4]
i=5 (nothing left)

Result: [9, 6, 6, -1, -1] ✓
```

## Best Answer to Memorize

```python
def secondGreaterElement(nums):
    n = len(nums)
    res = [-1] * n
    s1, s2 = [], []
    for i, v in enumerate(nums):
        while s2 and v > nums[s2[-1]]:
            res[s2.pop()] = v
        temp = []
        while s1 and v > nums[s1[-1]]:
            temp.append(s1.pop())
        while temp:
            s2.append(temp.pop())
        s1.append(i)
    return res
```

**13 lines. O(n) time. Clean. Interview-ready!**

## Key Insights

### Why TWO stacks?
> "Each element progresses through states: NOT STARTED -> WAITING FOR 1st
> -> WAITING FOR 2nd -> RESOLVED. Two stacks let us efficiently find
> 2nd greater values without re-scanning."

### Why reverse order when promoting?
> "When we promote from s1 to s2, we're inserting in the middle. To
> maintain s2 in DECREASING order (so next pop is the right one),
> we collect promotions in temp and push them back reversed."

### Why NOT just count?
> "Counting alone loses ORDER information. The 'exactly one k between'
> definition requires knowing which greater comes immediately after
> the 1st - order matters!"

## Test Cases

| nums | Expected | Why |
|------|----------|-----|
| [5,4,3,2,1] | [-1,-1,-1,-1,-1] | Decreasing |
| [1,2,3,4,5] | [3,4,5,-1,-1] | Increasing |
| [2,4,0,9,6] | [9,6,6,-1,-1] | LeetCode 2454 |
| [3,1,5,0,9,4,6] | [9,9,6,4,-1,-1,-1] | Mixed |
| [1] | [-1] | Single |
| [3,3,3] | [-1,-1,-1] | All equal |
| [0,0,0,0] | [-1,-1,-1,-1] | All zero |

## Common Pitfalls

1. **Wrong promotion order**: Must reverse to maintain decreasing order in s2
2. **Using >= instead of >**: Equal values shouldn't trigger promotion
3. **Forgetting to process s2 first**: Should resolve 2nd greater BEFORE promoting
4. **Wrong index management**: Use index, not value, for stack storage

## Why This Problem Matters

> "Tests:
> 1. Multi-stage stack processing (CRITICAL)
> 2. Maintaining monotonic order during promotions
> 3. Multiple stacks for state tracking
> 4. Pattern similar to: 1st greater, k-th greater
> 5. Edge case: equal values (use strict inequality)"
