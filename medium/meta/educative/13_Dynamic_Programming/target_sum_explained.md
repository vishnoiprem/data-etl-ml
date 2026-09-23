# Target Sum — 0.0001% Expert Guide

> **LeetCode 494** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/target-sum
> **Problem:** `findTargetSumWays(nums, target)` — count +/− assignments summing to target.

---

## 📋 WHAT THE QUESTION ASKS

Given `nums[]` and `target`, assign `+` or `-` to each element. Return the number of assignments where the signed sum equals `target`.

### Constraints
- `1 <= nums.length <= 20`
- `0 <= nums[i] <= 1000`
- `0 <= sum(nums) <= 1000`
- `-1000 <= target <= 1000`

### Examples
```
nums=[1,1,1,1,1], target=3     -> 5
  (3 positive, 2 negative choices)
nums=[1,0], target=1           -> 2
  ((+1,+0) and (+1,-0) both give 1)
nums=[1,2,7,9,9,9], target=3   -> 3
  ({7,9} subsets, 3 different 9's to pick)
nums=[1,2,3], target=0         -> 2
  ((+1,+2,-3) and (-1,-2,+3))
```

### Why This Is "Medium"
- Reduction to subset-sum via algebra.
- DP on subset sums.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Count +/− sign assignments whose weighted sum equals target."

### Step 2: KEY INSIGHT — Algebraic Reduction (5 min)
> "Let P = positively-signed indices, N = negatively-signed.
>   sum(P) − sum(N) = target   ... (1)
>   sum(P) + sum(N) = total    ... (2)
>
> Adding (1) and (2): 2·sum(P) = target + total
> So sum(P) = (target + total) / 2
>
> Now: count subsets P of nums with sum(P) = (target + total) / 2."

This is the classic **subset sum counting** problem.

### Step 3: Algorithm (3 min)
```
1. Compute total = sum(nums).
2. If (target + total) is odd or < 0, return 0.
3. s = (target + total) // 2.
4. Subset-sum DP:
   dp[0] = 1.
   For each x in nums:
     For j from s down to x:
       dp[j] += dp[j - x]
5. Return dp[s].
```

### Step 4: Edge Cases (2 min)
- `target > total`: impossible (return 0).
- `target < -total`: impossible (return 0).
- `target + total` is odd: no integer s exists.
- nums has zeros: each zero doubles answer (2^k for k zeros).

### Step 5: Code It (3 min)

```python
def findTargetSumWays(nums, target):
    total = sum(nums)
    if (target + total) % 2 != 0 or target + total < 0:
        return 0
    s = (target + total) // 2
    dp = [1] + [0] * s
    for x in nums:
        for j in range(s, x - 1, -1):
            dp[j] += dp[j - x]
    return dp[s]
```

### Step 6: Verify (2 min)
For [1, 1, 1, 1, 1], target=3:
- total = 5. s = (3+5)/2 = 4.
- Subsets summing to 4: {1,1,1,1} (5 ways to leave out one).
- dp[4] = 5. ✓

### Step 7: Discuss Trade-offs (3 min)
> "Three approaches:
> 1. **Subset-sum DP:** O(n × S). Best.
> 2. **DFS with memo:** O(n × total). Same complexity.
> 3. **Brute force 2^n:** Too slow for n=20.
>
> I'll use subset-sum DP."

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to count +/− assignments whose signed sum is target.

KEY INSIGHT: Algebraic reduction to subset sum.
Let P = positive group, N = negative group.
  sum(P) − sum(N) = target
  sum(P) + sum(N) = total
=> sum(P) = (target + total) / 2

So I count subsets of nums summing to (target + total) / 2.

ALGORITHM:
1. total = sum(nums).
2. If (target + total) odd or negative, return 0.
3. s = (target + total) // 2.
4. dp[0]=1. For x in nums: for j from s down to x: dp[j] += dp[j-x].
5. Return dp[s].

COMPLEXITY: O(n × S) time, O(S) space, S = (target+total)/2.

EDGE CASES:
- target outside [-total, total]: 0.
- Odd target+total: 0.
- Zeros in nums: each zero doubles count.

THE TRICK: Treat ± assignments as partitioning nums into P and N,
then algebra gives the exact sum P must achieve.
"
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Subset-Sum DP (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | 1D DP (BEST) | O(nS) | O(S) | **THE ANSWER** |
| 2 | 2D DP | O(nS) | O(nS) | Educational |
| 5 | Counter | O(nS) | O(S) | Sparse-aware |
| 7 | DP compact | O(nS) | O(S) | **THE ONE TO MEMORIZE** |
| 9 | Class OOP | O(nS) | O(S) | Reusable |
| 12 | DP explicit | O(nS) | O(S) | Educational |
| 14 | defaultdict | O(nS) | O(S) | Sparse variant |
| 17 | DP roll | O(nS) | O(S) | Educational |
| 20 | Final cleanest | O(nS) | O(S) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: DFS / Memoization

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 3 | DFS lru_cache | O(nS) | O(S) | Top-down |
| 10 | Recursive no memo | O(2^n) | O(n) | Brute |
| 13 | DFS dict memo | O(nS) | O(S) | Educational |
| 19 | Memo closure | O(nS) | O(S) | Educational |

### 🟠 TIER 3: BFS / Other

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 6 | DFS iterative | O(nS) | O(S) | Iterative |
| 11 | Numpy | O(nS) | O(S) | Vectorized |
| 15 | 2D tuple keys | O(n·S) | O(n·S) | Educational |
| 16 | BFS states | O(nS) | O(S) | Educational |

### 🔴 TIER 4: Brute Force / Meet-in-Middle

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 4 | Brute 2^n | O(2^n) | O(n) | Tiny n |
| 8 | Meet-in-middle | O(2^(n/2)) | O(2^(n/2)) | Alternative |
| 18 | itertools brute | O(2^n) | O(n) | Educational |

---

## 💎 THE 8-LINE SOLUTION (Memorize!)

```python
def findTargetSumWays(nums, target):
    total = sum(nums)
    if (target + total) % 2 != 0 or target + total < 0:
        return 0
    s = (target + total) // 2
    dp = [1] + [0] * s
    for x in nums:
        for j in range(s, x - 1, -1):
            dp[j] += dp[j - x]
    return dp[s]
```

**Time:** `O(n × S)` where `S = (target+total)/2`
**Space:** `O(S)`

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Algebra Reveals Structure

> Two equations, two unknowns: a system that solves analytically.

Many DP problems hide behind simple algebra. Always look for it first.

**Connection to:**
- **Problem reduction:** Algebra before DP.
- **Pattern recognition:** Standard equations → standard DP.

### Insight 2: From "Assignment" to "Subset"

> ± assignments are equivalent to partitioning into two groups.

Subset problems are well-studied. Reduce to use that toolkit.

**Connection to:**
- **Problem transformation:** Different views.
- **Standard algorithms:** Reuse known solutions.

### Insight 3: Negative S is Impossible

> If (target + total) < 0 or odd, no valid assignment exists.

Early return saves O(nS) work in many cases.

**Connection to:**
- **Edge cases:** Always check feasibility first.
- **Pruning:** Cut impossible branches.

### Insight 4: Zeros Double the Count

> Each zero in nums doubles the count of ways.

Subset-sum DP handles this naturally (no work but new combination).

**Connection to:**
- **Counting with identical items:** Doubling.
- **Permutation considerations:** Same value, different placements.

### Insight 5: Why Reverse Iteration

> `for j from s down to x` ensures each element used at most once.

If we iterate forward, we'd use the same element multiple times (unbounded).

**Connection to:**
- **0/1 vs unbounded knapsack:** Different iteration.
- **DP convention:** Always decide bounded vs unbounded.

### Insight 6: Meet-in-Middle for Larger N

> For n=20-40, meet-in-middle (2^(n/2)) beats DP.

When n exceeds DP's comfortable range, divide and conquer.

**Connection to:**
- **Algorithmic tradeoffs:** Asymptotic vs practical.
- **Problem size:** Choose by n.

### Insight 7: Connection to Partition Equal Subset Sum

> Same subset-sum DP, different framing.

The reduction is the same; the constraints determine target sum.

**Connection to:**
- **Problem family:** Subset-sum variants.
- **Cross-problem skills:** Reuse code.

### Insight 8: BFS vs DFS Equivalence

> Both explore (i, cur_sum) states. DFS with memo or BFS — same complexity.

DFS with memo is recursive (clearer); BFS is iterative.

**Connection to:**
- **Search algorithms:** Equivalent for many problems.
- **Implementation choice:** Pick by convention.

### Insight 9: Why DP Beats Brute

> n=20: brute 2^20 = 10^6. n=30: 10^9. Borderline.

For n=20, brute might pass, but DP is more reliable.

**Connection to:**
- **Asymptotic safety:** DP scales.
- **Competitions:** Always use optimal.

### Insight 10: Connection to Coin Change Variants

> Same DP skeleton counts combinations.

Coin Change: minimum coins. Target Sum: count ways. Different value, same structure.

**Connection to:**
- **DP family:** Knapsack variants.
- **Skeleton reuse:** Adapt DP template.

### Insight 11: Real-World Applications

| Application | Use |
|-------------|-----|
| **Portfolio rebalancing** | Long/short positions |
| **Statistical testing** | Sum of signed deviations |
| **Inventory adjustments** | +increase/-decrease |
| **Chemistry** | Oxidation states |
| **Game theory** | Wins minus losses |
| **Survey analysis** | Net scores |

**Portfolio rebalancing** (long/short positions summing to target) is canonical.

### Insight 12: When Brute Force Wins

> n=20, brute 2^20 ≈ 10^6 operations. Fast enough!

For small n, brute is simpler and may suffice in interviews.

**Connection to:**
- **Pragmatic choices:** Don't over-engineer.
- **n limits:** Check before DP.

### Insight 13: Why Iterate Inner Loop in Reverse

> Each x used at most once per subset. Reverse ensures this.

Forward iteration = use multiple times (unbounded).

**Connection to:**
- **Knapsack variants:** 0/1 vs unbounded.
- **DP iteration order:** Critical.

### Insight 14: Connection to Last Stone Weight II

> LC 1049: minimize |sum(P) - sum(N)|. Same subset-sum skeleton.

Different objective (minimize |target|) but same DP structure.

**Connection to:**
- **Problem family:** Partition problems.
- **Code reuse:** Adapt skeleton.

---

## 🧪 TEST CASES

| `nums` | `target` | Expected | Note |
|--------|----------|----------|------|
| `[1,1,1,1,1]` | 3 | 5 | Standard LC |
| `[1]` | 1 | 1 | Single positive |
| `[1,0]` | 1 | 2 | Zero doubles |
| `[0,0,0,0,0]` | 0 | 32 | 2^5 |
| `[1,2,3]` | 0 | 2 | ± pair |
| `[1,2,3]` | 6 | 1 | All positive |
| `[100]` | -100 | 1 | All negative |
| `[2,7,4,3,1]` | 5 | 2 | {7,4}, {7,3,1} |
| `[1,2,7,9,9,9]` | 3 | 3 | {7,9}×3 |
| `[]` | 0 | 1 | Empty positive |
| `[]` | 1 | 0 | Empty can't hit |
| `[5,2,1,3]` | 4 | 0 | Odd → 0 |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Subset-sum DP** | **O(nS)** | **O(S)** | **✅ BEST** |
| DFS memo | O(nS) | O(S) | ✅ Top-down |
| Meet-in-middle | O(2^(n/2)) | O(2^(n/2)) | ✅ For large n |
| Brute force | O(2^n) | O(n) | ❌ Slow for n>25 |

S = (target + total) / 2.

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Partition Equal Subset Sum (LC 416) | Subset-sum DP | https://leetcode.com/problems/partition-equal-subset-sum/ |
| Last Stone Weight II (LC 1049) | Subset-sum | https://leetcode.com/problems/last-stone-weight-ii/ |
| Subset Sum (gfg) | DP | Classic |
| Target Sum (LC 494) | **This problem** | https://leetcode.com/problems/target-sum/ |
| Number of Ways to Form Target | 2D DP | Variant |

---

## 🎓 EXPERT TAKEAWAYS

1. **Algebra first, then DP** — equations often reveal structure.
2. **Reduce to subset-sum** for ± assignment problems.
3. **Check feasibility** — odd sum, negative s → 0.
4. **Reverse iteration** for 0/1 knapsack.
5. **O(n × S)** dominates for n≤20.
6. **Portfolio rebalancing** is canonical use case.
7. **Same skeleton as LC 416, 1049**.
8. **Zeros double** the count.
9. **Brute 2^n** works for n=20 but DP is safer.
10. **Meet-in-middle** for n=30-40.

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Portfolio rebalancing** | Long/short positions |
| **Statistical testing** | Signed deviations |
| **Inventory adjustment** | +increase/-decrease |
| **Chemistry** | Oxidation states |
| **Game theory** | Net wins |
| **Survey analysis** | Net scores |
| **Bioinformatics** | Differential expression |
| **Finance** | Hedging strategies |
| **Optimization** | Penalty/bonus |
| **Combinatorics** | Signed sums |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive the algebraic reduction in 60 seconds
- [x] Can code the 8-line solution in 90 seconds
- [x] Know complexity: O(n × S) time, O(S) space
- [x] Know why this reduces to subset-sum
- [x] Know edge cases (odd sum, zeros, target out of range)
- [x] Can compare with brute force and meet-in-middle
- [x] Know related problems (LC 416, 1049)
- [x] Can list 5 real-world applications
- [x] Know DFS memo as alternative

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 10 minutes.
**Lines of code to write:** 8.
**Insight:** "Algebra gives sum(P) = (target+total)/2. Count subsets summing to that. Subset-sum DP in O(n × S)."