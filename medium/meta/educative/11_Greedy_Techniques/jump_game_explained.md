# Jump Game - 10 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/jump-game

## The Problem
```
Given an array nums where nums[i] is the max jump length from position i,
determine if you can reach the last index.

Examples:
    [2,3,1,1,4] -> True (0->1->4)
    [3,2,1,0,4] -> False (stuck at index 3)

Constraints:
- 1 <= nums.length <= 10^4
- 0 <= nums[i] <= 10^5
```

## How I Think (The Mental Process)

### Step 1: Understand
```
Starting at index 0, we can jump up to nums[i] steps from each index.
Can we reach the last index?
```

### Step 2: The Trick
> "KEY INSIGHT: Greedy furthest-reach.
>
> Track the FURTHEST reachable position as we scan.
> At each index i, if i > furthest, we're stuck -> return False.
> Otherwise, update furthest = max(furthest, i + nums[i]).
> If we complete the scan without getting stuck, return True."

### Step 3: Why this works
> "The furthest-reach invariant: at any point, we know that all positions up
> to 'furthest' are reachable. If we ever reach an index beyond this, it's
> impossible. Otherwise, our greedy update gives the maximum reach."

### Step 4: Algorithm
> "1. furthest = 0.
> 2. For each i from 0 to n-1:
>    - if i > furthest: return False.
>    - furthest = max(furthest, i + nums[i]).
> 3. Return True."

### Step 5: Edge cases
> "- Single element: return True (already at the end).
> - nums[0] == 0 and n > 1: stuck at start.
> - nums[0] >= n-1: jump directly to end."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to determine if I can reach the last index of an array given variable jump lengths."

**Key Insight:**
> "Greedy: track the furthest reachable position. If we ever reach an index beyond it, we're stuck."

**Algorithm:**
> "1. furthest = 0.
> 2. For i in 0..n-1:
>    - if i > furthest: return False.
>    - furthest = max(furthest, i + nums[i]).
> 3. Return True."

**Why this works:**
> "At each step, we maintain the invariant that all indices <= furthest are reachable. If we encounter an unreachable index, the answer is no. The greedy update gives the best possible extension."

**Edge cases:**
- Single element: True.
- Zero at start with multiple elements: False.

**Complexity:**
- Time:  O(n). Single pass.
- Space: O(1) for greedy; O(n) for DP.

---

## The 10 Implementations (Simple to Complex)

### Way 1: Greedy furthest (BEST - Memorize!)
```python
def can_jump(nums):
    furthest = 0
    n = len(nums)
    for i in range(n):
        if i > furthest:
            return False
        furthest = max(furthest, i + nums[i])
    return True
```

### Way 2: Greedy target (reverse scan)
### Way 3: DP forward
### Way 4: Recursive with memo
### Way 5: BFS
### Way 6: lru_cache decorator
### Way 7: Brute force recursion
### Way 8: Class-based
### Way 9: numpy vectorized
### Way 10: Final cleanest

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Standard           | Way 1    | O(n) O(1)    |
| Conceptual clarity | Way 2    | Reverse scan |
| Need all paths     | Way 4    | Memoization  |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Greedy furthest (Way 1) | O(n) | O(1) | Best |
| Greedy target (Way 2) | O(n) | O(1) | Reverse |
| DP forward (Way 3) | O(n^2) | O(n) | Slower |
| Recursive memo (Way 4) | O(n^2) | O(n) | Slow |
| BFS (Way 5) | O(n^2) | O(n) | Overkill |

---

## Walkthrough Example

```
nums = [2, 3, 1, 1, 4]

i=0, nums[0]=2, furthest = max(0, 0+2) = 2
i=1, nums[1]=3, furthest = max(2, 1+3) = 4
i=2, nums[2]=1, furthest = max(4, 2+1) = 4
i=3, nums[3]=1, furthest = max(4, 3+1) = 4
i=4, nums[4]=4, furthest = max(4, 4+4) = 8

All i <= furthest. Return True.

nums = [3, 2, 1, 0, 4]

i=0, nums[0]=3, furthest = max(0, 3) = 3
i=1, nums[1]=2, furthest = max(3, 3) = 3
i=2, nums[2]=1, furthest = max(3, 3) = 3
i=3, nums[3]=0, furthest = max(3, 3) = 3
i=4: 4 > furthest=3, return False.
```

---

## Best Answer to Memorize

```python
def canJump(nums):
    furthest = 0
    for i, x in enumerate(nums):
        if i > furthest:
            return False
        furthest = max(furthest, i + x)
    return True
```

**~5 lines. O(n) time. O(1) space. Interview-ready!**

---

## Key Insights

### Why O(n)?
> "Single pass. Each index is processed once."

### Why O(1) space?
> "Only 'furthest' variable is needed. No memoization or DP table."

### What about Jump Game II (min jumps)?
> "Different problem. Use BFS or DP. This problem is just reachable/not."

### Why not BFS?
> "Overkill. Greedy is optimal and simpler."

---

## Test Cases

| nums | Expected | Notes |
|------|---------|-------|
| [2,3,1,1,4] | True | Standard |
| [3,2,1,0,4] | False | Stuck at zero |
| [0] | True | Single |
| [1,0] | True | Direct reach |
| [0,1] | False | Start stuck |
| [2,0,0] | True | Two jumps |

---

## Common Pitfalls

1. **Off-by-one**: Check `i > furthest`, not `i >= furthest`.
2. **Update order**: Update furthest only AFTER the check.
3. **Edge case**: nums[0] = 0 with n > 1 should return False.
4. **Single element**: Always True (already there).

---

## Why This Problem Matters

> "Tests:
> 1. Greedy invariant maintenance.
> 2. Recognizing O(1) space DP-like pattern.
> 3. Foundation for: Jump Game II (min jumps), etc."

---

## Beyond This Problem: Related Patterns

### 1. Jump Game II (LC 45) - Minimum jumps
```python
# BFS or greedy with level tracking.
```

### 2. Jump Game III (LC 1306) - Bidirectional
```python
# Can jump forward OR backward by nums[i].
```

### 3. Video Stitching (LC 1024)
```python
# Similar greedy interval coverage.
```

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 55 - Jump Game](https://leetcode.com/problems/jump-game/)