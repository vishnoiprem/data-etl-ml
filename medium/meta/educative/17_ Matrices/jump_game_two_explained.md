# Jump Game II — 0.0001% Expert Guide

> **LeetCode 45** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/jump-game-ii
> **Problem:** `jump(nums)` — minimum jumps to reach last index.

---

## 📋 WHAT THE QUESTION ASKS

Given an array `nums` where `nums[i]` is the maximum jump length from position `i`, find the minimum number of jumps to reach the last index. You start at index 0. You may assume the last index is always reachable.

### Constraints
- `1 <= nums.length <= 10^3`
- `0 <= nums[i] <= 10^3`
- Always reachable.

### Examples
```
nums=[2,3,1,1,4]    -> 2   (0 -> 1 -> 4)
nums=[2,3,0,1,4]    -> 2   (0 -> 1 -> 4)
nums=[1,2,3]        -> 2   (0 -> 1 -> 2)
nums=[0]            -> 0   (already at end)
nums=[2,0,0]        -> 1   (0 -> 2)
nums=[5,0,0,0,0]    -> 1   (0 -> 5)
nums=[1,1,1,1]      -> 3   (0 -> 1 -> 2 -> 3)
```

### Why This Is "Medium"
- Greedy BFS-layer insight.
- O(n) time, O(1) space.
- Classic interview problem.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Min jumps from index 0 to index n-1. nums[i] = max jump length at i."

### Step 2: KEY INSIGHT — BFS Layers (5 min)
> "Each 'layer' = set of indices reachable in K jumps.
> - cur_end: farthest index reachable with current jumps.
> - farthest: farthest index reachable with one more jump.
>
> Iterate i=0..n-2:
>   farthest = max(farthest, i + nums[i]).
>   If i == cur_end: jumps++, cur_end = farthest."

### Step 3: Why Greedy is Optimal (3 min)
> "Within a layer, jumping to the position with farthest reach
> maximizes the next layer's coverage. So we always take the next
> layer's farthest position when forced to jump."

### Step 4: Algorithm (3 min)
```
1. jumps = 0, cur_end = 0, farthest = 0.
2. For i in 0..n-2:
     farthest = max(farthest, i + nums[i]).
     if i == cur_end:
       jumps += 1
       cur_end = farthest
3. Return jumps.
```

### Step 5: Edge Cases (2 min)
- Single element (n=1): 0.
- Already at end (n=0... but not allowed): 0.
- All same: n // (val+1) jumps approx.
- Big jump at start: 1 jump.

### Step 6: Code It (3 min)

```python
def jump(nums):
    n = len(nums)
    if n <= 1:
        return 0
    jumps = 0
    cur_end = 0
    farthest = 0
    for i in range(n - 1):
        farthest = max(farthest, i + nums[i])
        if i == cur_end:
            jumps += 1
            cur_end = farthest
    return jumps
```

### Step 7: Verify (2 min)
For `[2,3,1,1,4]`:
```
i=0: farthest=max(0,2)=2. i(0) != cur_end(0). Wait, cur_end starts at 0!
     i(0) == cur_end(0). jumps=1, cur_end=2.
i=1: farthest=max(2,4)=4. i(1) != cur_end(2).
i=2: farthest=max(4,3)=4. i(2) != cur_end(2).
     (We don't update cur_end unless i == cur_end.)
i=3: farthest=max(4,4)=4. i(3) == cur_end(2)? No, 3 != 2.
```
Hmm, but expected=2. Let me retrace:

Actually cur_end starts at 0.
- i=0: farthest = max(0, 0+2) = 2. i(0) == cur_end(0). jumps=1, cur_end=2.
- i=1: farthest = max(2, 1+3) = 4. i(1) != cur_end(2).
- i=2: farthest = max(4, 2+1) = 4. i(2) != cur_end(2).
- i=3: farthest = max(4, 3+1) = 4. i(3) != cur_end(2).

Loop ends. jumps=1.

Wait, expected was 2. Let me recount the algorithm.

For `[2,3,1,1,4]`:
- Layer 1 (1 jump): reach from index 0. Reach = [0+2] = [2]. So end is index 2.
- Layer 2 (2 jumps): from [0..2], reach = max(0+2, 1+3, 2+1) = [2, 4, 3]. End is index 4.
- Done (reached last).

But my algorithm returned 1. The issue: when i=0 reaches cur_end(0), we set cur_end=2. But for layer 2 we need to know farthest=4 (set during iteration). After updating cur_end to 2 at i=0, we continue iterating i=1, 2, 3. At i=3, farthest=4, but we never trigger another jump.

The bug: we need to trigger the next jump when reaching the OLD cur_end, but we need to continue iterating to fill farthest. After the for loop ends, we might not have triggered the final jump.

Let me fix: the loop should run n-1 times, and we count jumps when i == cur_end. But we don't count the last layer if it directly reaches the end.

Actually wait. Let me re-examine. With `[2,3,1,1,4]`:
- At i=0: cur_end=0, farthest=2. Since i==cur_end, jumps=1, cur_end=farthest=2.
- At i=1: cur_end=2, farthest=4. i(1) != cur_end(2).
- At i=2: cur_end=2, farthest=4. i(2) == cur_end(2). jumps=2, cur_end=4.
- Loop ends at i=3.

YES! I missed it. jumps=2 ✓.

My verification was wrong above. The algorithm is correct.

### Step 8: Discuss Trade-offs (3 min)
> "Three approaches:
> 1. **Greedy BFS-layers:** O(n) time, O(1) space. **BEST**.
> 2. **BFS with queue:** O(n) time, O(n) space.
> 3. **DP:** O(n^2) time, O(n) space. Too slow.
>
> I'll use greedy."

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need min jumps to reach the last index. Each nums[i] is max jump length."

KEY INSIGHT: Greedy BFS-layers. Each "layer" is the set of indices
reachable with the current number of jumps.
- cur_end: farthest index reachable with `jumps` jumps.
- farthest: farthest index reachable with `jumps+1` jumps.

Iterate i=0..n-2:
  farthest = max(farthest, i + nums[i]).
  if i == cur_end: jumps++; cur_end = farthest.

ALGORITHM:
1. jumps=0, cur_end=0, farthest=0.
2. For i in 0..n-2: update farthest; if i==cur_end: jumps++, cur_end=farthest.
3. Return jumps.

COMPLEXITY: O(n) time, O(1) space.

EDGE CASES:
- Single element: 0.
- All reachable by assumption.

WHY GREEDY = OPTIMAL:
- Each jump MUST be taken at layer boundary.
- Farthest position in layer maximizes next layer's coverage.
- Minimizes jumps.

THE TRICK:
- "Layer" = indices reachable with K jumps.
- Jump count = number of layer boundaries crossed.

ALTERNATE: BFS with explicit queue. Same time, more space.
DP: O(n^2), too slow.

RELATED:
- Jump Game (LC 55): can we reach end? Bool greedy.
- Jump Game III (LC 1306): can move both directions.
- Jump Game IV (LC 1345): BFS with same-value jumps.
- Jump Game V (LC 1340): harder.
"""
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Greedy BFS-Layers (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | Greedy BFS layers | O(n) | O(1) | **THE ANSWER** |
| 2 | Greedy BFS explicit | O(n) | O(1) | Variant |
| 3 | Greedy single var | O(n) | O(1) | Variant |
| 8 | Greedy clear comments | O(n) | O(1) | Educational |
| 9 | Class OOP | O(n) | O(1) | Reusable |
| 12 | Greedy layer | O(n) | O(1) | Variant |
| 14 | Iterative min | O(n) | O(1) | Variant |
| 15 | Layer-based | O(n) | O(1) | Educational |
| 16 | While loop | O(n) | O(1) | Educational |
| 19 | Functional layers | O(n) | O(1) | Functional |
| 20 | Final cleanest | O(n) | O(1) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: BFS with Explicit Queue

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 4 | BFS queue | O(n) | O(n) | Educational |
| 18 | BFS set | O(n) | O(n) | Educational |

### 🟠 TIER 3: Pointer Range

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 5 | Slow/fast pointers | O(n) | O(1) | Educational |
| 10 | Range expansion | O(n) | O(1) | Educational |

### 🔵 TIER 4: DP

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 6 | DP bottom-up | O(n^2) | O(n) | Educational |
| 7 | DP top-down memo | O(n^2) | O(n) | Top-down |
| 11 | DP forward | O(n^2) | O(n) | Educational |
| 13 | Recursive no memo | O(2^n) | O(n) | Brute |
| 17 | DP sweep | O(n^2) | O(n) | Variant |

---

## 💎 THE 8-LINE SOLUTION (Memorize!)

```python
def jump(nums):
    n = len(nums)
    if n <= 1:
        return 0
    jumps = 0
    cur_end = 0
    farthest = 0
    for i in range(n - 1):
        farthest = max(farthest, i + nums[i])
        if i == cur_end:
            jumps += 1
            cur_end = farthest
    return jumps
```

**Time:** `O(n)`
**Space:** `O(1)`

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: BFS-Layers View

> Treat the array as a graph where edges go i -> i+1..i+nums[i].
> BFS layers = "jumps".
> Layer K = all nodes reachable with exactly K jumps.
> Number of jumps = number of layers until we reach last index.

**Connection to:**
- **BFS:** Graph traversal.
- **Levels:** Distance from start.

### Insight 2: Why Greedy Works

> At each layer boundary, we MUST jump.
> The best position to be at is the one that gives maximum
> reach for the NEXT layer.
> That's `farthest` computed during current layer.

**Connection to:**
- **Greedy optimality:** Max coverage.
- **Layered BFS:** Local = global.

### Insight 3: Two Variables — cur_end, farthest

> cur_end tracks "where current jump ends".
> farthest tracks "where next jump will end".
> They are different because we don't know the next layer until
> we've explored the current layer.

**Connection to:**
- **State machine:** 2 vars.
- **Layered BFS:** Frontier.

### Insight 4: Why Iterate to n-2

> We don't need to "jump from" the last index.
> Once at last index, we're done.
> Loop range(n-1) avoids redundant logic.

**Connection to:**
- **Edge optimization:** Avoid last.
- **Standard:** Range up to n-2.

### Insight 5: Single Jump Case

> If nums[0] >= n-1, then farthest after i=0 is >= n-1.
> We jump once (when i=0==cur_end=0) and cur_end becomes n-1 or more.
> Loop continues but i never reaches new cur_end (since i goes up to n-2).
> Return 1.

**Connection to:**
- **Edge case:** Trivial.
- **Greedy:** Works.

### Insight 6: Real-World Applications

| Application | Use |
|-------------|-----|
| **Network routing** | Min hops to destination |
| **Game design** | Min moves to win |
| **Logistics** | Min transfers |
| **Telecom** | Min relay hops |
| **Transport** | Min connections |
| **Optimization** | Layered BFS |

**Network routing** is canonical.

### Insight 7: Why Not Just "Maximum nums[i] in Window"

> Greedy on max alone fails: e.g., [5,1,1,1,1].
> From index 0 we can reach index 4 directly (1 jump).
> But if we greedily pick max within window, we might pick wrong index.

**Connection to:**
- **Pitfall:** Wrong greedy.
- **Correct:** Layered.

### Insight 8: Connection to Jump Game (LC 55)

> LC 55: can we reach end? Bool greedy.
> LC 45: min jumps to reach end? Count layers.
> Same skeleton, different tracking.

**Connection to:**
- **Problem family:** Jump variants.
- **Reusable:** Same structure.

### Insight 9: Why DP is Slower

> DP: dp[i] = min(dp[j] + 1) for j < i, j+nums[j] >= i. O(n^2).
> Greedy: O(n). 
> Greedy wins because we don't need exact paths.

**Connection to:**
- **Greedy optimality:** Sufficient info.
- **DP overkill:** Too slow.

### Insight 10: Why Reachability Assumption Helps

> Always reachable → we never get stuck at i > cur_end.
> This makes greedy safe to assume "i always within cur_end".

**Connection to:**
- **Invariant:** Guaranteed reachable.
- **Greedy safety:** No edge failure.

### Insight 11: Layer Count = Jumps

> Each layer boundary crossed = 1 jump.
> Total jumps = number of boundaries until we reach n-1.

**Connection to:**
- **Counting:** Layer boundaries.
- **BFS:** Distance = layers.

### Insight 12: Why Loop to n-2 Specifically

> i in [0, n-2] covers all "from" indices.
> i = n-1 is the destination — we don't jump FROM it.

**Connection to:**
- **Range:** Source indices only.
- **Optimization:** Skip destination.

### Insight 13: Time Complexity is Linear

> Single pass through array.
> O(1) work per index.
> Total: O(n).

**Connection to:**
- **Optimal:** Can't do better.
- **Linear:** Best possible.

### Insight 14: Space is Constant

> Only 3 integer variables.
> No array allocations.
> O(1) space.

**Connection to:**
- **Memory:** Constant.
- **Optimal:** Best possible.

### Insight 15: Alternative BFS

> BFS with queue: process nodes level by level.
> Each level = 1 jump.
> Same time, O(n) space.

**Connection to:**
- **BFS:** Explicit.
- **Trade-off:** Space vs clarity.

### Insight 16: Top-Down DP Equivalence

> Bottom-up DP = top-down DFS with memo.
> Both O(n^2).
> Greedy beats both.

**Connection to:**
- **DP family:** Two styles.
- **Greedy:** Faster.

### Insight 17: When Brute Recursion Fails

> Exponential without memo.
> For n=100, infeasible.
> DP or greedy needed.

**Connection to:**
- **Brute:** Too slow.
- **DP/greedy:** Needed.

### Insight 18: Connection to BFS Distance

> In graph BFS, distance = levels.
> Here, jumps = levels.
> Same concept.

**Connection to:**
- **Graph theory:** BFS distance.
- **Reusable:** Concept.

### Insight 19: Edge Case n=1

> Single element = already at end.
> Return 0 (no jumps).

**Connection to:**
- **Edge case:** Trivial.
- **Always handle:** n=1.

### Insight 20: Why Range(n-1) Not Range(n)

> Loop variable i is "from" index.
> Last index can't be a "from" (we're done).
> So iterate to n-2 (inclusive).

**Connection to:**
- **Edge:** Avoid last.
- **Standard:** n-1 iterations.

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
| `[10,0,0,0,0,0,0,0,0,0]` | 1 | Reach all |
| `[2,3,1,1,4,1,1,1]` | 3 | Mid-size |
| `[0,1]` | 1 | Edge: start can't move |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Greedy BFS-layers** | **O(n)** | **O(1)** | **✅ BEST** |
| BFS queue | O(n) | O(n) | ✅ Educational |
| DP | O(n^2) | O(n) | ❌ Slow |
| Brute recursion | O(2^n) | O(n) | ❌ Too slow |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Jump Game (LC 55) | Bool greedy | https://leetcode.com/problems/jump-game/ |
| Jump Game II (LC 45) | **This problem** | https://leetcode.com/problems/jump-game-ii/ |
| Jump Game III (LC 1306) | Bidirectional | https://leetcode.com/problems/jump-game-iii/ |
| Jump Game IV (LC 1345) | BFS same-value | https://leetcode.com/problems/jump-game-iv/ |
| Jump Game V (LC 1340) | Hard | https://leetcode.com/problems/jump-game-v/ |
| Video Stitching (LC 1024) | Similar greedy | https://leetcode.com/problems/video-stitching/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **BFS-layers** = jumps. Each layer boundary crossed = 1 jump.
2. **cur_end, farthest** two variables.
3. **O(n) time, O(1) space** — optimal.
4. **Greedy beats DP** for this problem.
5. **Loop to n-2** (don't jump from last index).
6. **Network routing** is canonical use case.
7. **Same skeleton** as Jump Game (LC 55).
8. **Always reachable** assumption simplifies logic.
9. **Layer = positions reachable with K jumps.**
10. **Farthest within layer maximizes next layer coverage.**

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Network routing** | Min hops |
| **Game design** | Min moves to win |
| **Logistics** | Min transfers |
| **Telecom** | Min relay hops |
| **Transport** | Min connections |
| **Video stitching** | Min clips |
| **Optimization** | Layered BFS |
| **Graph algorithms** | BFS distance |
| **Cache eviction** | Layered access |
| **Robotics** | Path planning |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive the BFS-layers greedy in 60 seconds
- [x] Can code the 8-line solution in 60 seconds
- [x] Know complexity: O(n) time, O(1) space
- [x] Know why cur_end and farthest
- [x] Know why loop to n-2
- [x] Know why greedy beats DP
- [x] Know related Jump problems (LC 55, 1306, 1345, 1340)
- [x] Know reachability assumption
- [x] Can list 5 real-world applications

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 15 minutes.
**Lines of code to write:** 8.
**Insight:** "BFS-layers: each layer = positions reachable in K jumps. cur_end = farthest in layer. farthest = max reach in next layer. When i == cur_end, take a jump."
