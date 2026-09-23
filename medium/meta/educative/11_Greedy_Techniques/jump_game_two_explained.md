# Jump Game II — 0.0001% Expert Guide

> **LeetCode 45** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/jump-game-ii
> **Problem:** `jump(nums)` — minimum jumps to reach last index.

---

## 📋 WHAT THE QUESTION ASKS

Given array `nums` where `nums[i]` is the maximum jump length from position `i`, find the minimum number of jumps to reach the last index. Start at index 0. Always reachable by assumption.

### Constraints
- `1 <= nums.length <= 10^3`
- `0 <= nums[i] <= 10^3`
- Always reachable.

### Examples
```
nums=[2,3,1,1,4]    -> 2   (0 -> 1 -> 4)
nums=[2,3,0,1,4]    -> 2
nums=[1,2,3]        -> 2
nums=[0]            -> 0
nums=[2,0,0]        -> 1
nums=[5,0,0,0,0]    -> 1
nums=[1,1,1,1]      -> 3
```

---

## 🧠 HOW TO THINK — STEP BY STEP

### Step 1: Understand the Problem
> "Min jumps from index 0 to last index."

### Step 2: Key Insight — BFS Layers
> "Each layer = set of indices reachable in K jumps.
> Number of jumps = number of layers until last index."

### Step 3: Greedy Two-Pointer Variables
> "cur_end: farthest index reachable with current jumps.
> farthest: farthest index reachable with one more jump.
> When i == cur_end, increment jumps and update cur_end."

### Step 4: Algorithm
```
jumps = 0, cur_end = 0, farthest = 0.
For i in 0..n-2:
  farthest = max(farthest, i + nums[i]).
  if i == cur_end: jumps++; cur_end = farthest.
Return jumps.
```

### Step 5: Edge Cases
- n=1: 0 (already at end).
- nums[0] >= n-1: 1 (direct).
- Always reachable (no i > cur_end case).

### Step 6: Code It
```python
def jump(nums):
    n = len(nums)
    if n <= 1:
        return 0
    jumps = cur_end = farthest = 0
    for i in range(n - 1):
        farthest = max(farthest, i + nums[i])
        if i == cur_end:
            jumps += 1
            cur_end = farthest
    return jumps
```

### Step 7: Trade-offs
- Greedy BFS-layers: O(n) time, O(1) space. **BEST**.
- BFS with queue: O(n) time, O(n) space.
- DP: O(n^2) time, O(n) space.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT

```
"I need min jumps to last index. nums[i] = max jump at i."

KEY INSIGHT: Greedy BFS-layers. Each layer = indices reachable in K jumps.
- cur_end: farthest reachable with current jumps.
- farthest: farthest reachable with one more jump.

Iterate i=0..n-2: update farthest; if i == cur_end: jumps++, cur_end = farthest.

COMPLEXITY: O(n) time, O(1) space.

EDGE CASES: n=1 -> 0. Always reachable by assumption.

WHY GREEDY = OPTIMAL:
- Within layer, pick farthest to maximize next layer.
- Minimizes jumps.

THE TRICK: "Layer = positions reachable with K jumps. Count layer boundaries."

ALTERNATE: BFS with queue (O(n) space), DP (O(n^2)).

RELATED: Jump Game (LC 55), Jump Game III (LC 1306), Jump Game IV (LC 1345).
"""
```

---

## 💎 THE 8-LINE SOLUTION

```python
def jump(nums):
    n = len(nums)
    if n <= 1:
        return 0
    jumps = cur_end = farthest = 0
    for i in range(n - 1):
        farthest = max(farthest, i + nums[i])
        if i == cur_end:
            jumps += 1
            cur_end = farthest
    return jumps
```

**Time:** `O(n)` | **Space:** `O(1)`

---

## 🤖 KEY INSIGHTS

1. **BFS-layers** = jumps. Each boundary crossed = 1 jump.
2. **cur_end, farthest** two variables.
3. **O(n) time, O(1) space** — optimal.
4. **Greedy beats DP** — don't need exact paths.
5. **Loop to n-2** — don't jump from last.
6. **Network routing** is canonical use.
7. **Same skeleton** as Jump Game (LC 55).
8. **Layer = positions reachable with K jumps.**
9. **Farthest within layer maximizes next layer coverage.**
10. **Always reachable** assumption simplifies.

---

## 🧪 TEST CASES

| `nums` | Expected | Note |
|--------|----------|------|
| `[2,3,1,1,4]` | 2 | Standard |
| `[2,3,0,1,4]` | 2 | With zeros |
| `[1,2,3]` | 2 | Small |
| `[0]` | 0 | Single |
| `[2,0,0]` | 1 | Direct reach |
| `[5,0,0,0,0]` | 1 | Single big jump |
| `[1,1,1,1]` | 3 | All ones |
| `[10,0,...0]` | 1 | Reach all |

---

## 📊 COMPLEXITY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Greedy** | **O(n)** | **O(1)** | **✅ BEST** |
| BFS | O(n) | O(n) | ✅ Educational |
| DP | O(n^2) | O(n) | ❌ Slow |

---

## 🔗 RELATED

- Jump Game (LC 55) — bool greedy
- Jump Game III (LC 1306) — bidirectional
- Jump Game IV (LC 1345) — BFS same-value
- Video Stitching (LC 1024) — similar greedy

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Insight:** "BFS-layers: cur_end = farthest in layer. farthest = max reach in next. When i == cur_end, take a jump."