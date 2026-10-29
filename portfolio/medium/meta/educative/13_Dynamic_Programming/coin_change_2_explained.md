# Coin Change II — 0.0001% Expert Guide

> **LeetCode 518** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/coin-change-ii
> **Problem:** `change(amount, coins)` — count combinations of coins summing to amount.

---

## 📋 WHAT THE QUESTION ASKS

Given `amount` and `coins[]`, return the number of distinct combinations that sum exactly to `amount`. Order does not matter (combinations, not permutations).

### Constraints
- `1 <= coins.length <= 300`
- `1 <= coins[i] <= 5000`
- All coin values are unique.
- `0 <= amount <= 5000`

### Examples
```
amount=5, coins=[1,2,5]  -> 4
  (5), (2+2+1), (2+1+1+1), (1+1+1+1+1)
amount=3, coins=[2]      -> 0
amount=10, coins=[10]    -> 1
amount=0, coins=[1]      -> 1 (empty combination)
```

### Why This Is "Medium"
- Unbounded knapsack counting.
- Order of loops is THE critical insight.
- O(n × amount) DP.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Count combinations of coins summing to amount. Each coin unlimited."

### Step 2: KEY INSIGHT — Loop Order Matters (5 min)
> "To count COMBINATIONS (not permutations):
> - COINS in OUTER loop, AMOUNTS in INNER.
> - This ensures each coin's contribution is processed once.
>
> To make it UNBOUNDED (reuse coins):
> - AMOUNTS iterate FORWARD (c to amount).
> - Reverse iteration = 0/1 knapsack (each coin once).
>
> dp[i] = # combinations of coins considered so far summing to i."

### Step 3: Why This Works (3 min)
> "When we process coin c, dp[j] adds dp[j-c] which already includes
> contributions from this same coin c. So we can use multiple c's.
>
> Since we process coins one at a time, the order of choice is fixed:
> coin 0 first, then coin 1, etc. This eliminates permutations."

### Step 4: Algorithm (3 min)
```
1. dp[0] = 1 (empty combination).
2. For each c in coins (OUTER):
     For j from c to amount (INNER, forward):
       dp[j] += dp[j - c]
3. Return dp[amount].
```

### Step 5: Edge Cases (2 min)
- amount = 0: return 1 (one empty combination).
- No coins: 1 if amount=0, else 0.
- Impossible amount: 0.
- Single coin = amount: 1.

### Step 6: Code It (3 min)

```python
def change(amount, coins):
    dp = [0] * (amount + 1)
    dp[0] = 1
    for c in coins:
        for j in range(c, amount + 1):
            dp[j] += dp[j - c]
    return dp[amount]
```

### Step 7: Verify (2 min)
For amount=5, coins=[1,2,5]:
- dp = [1, 0, 0, 0, 0, 0]
- Coin 1: dp = [1, 1, 1, 1, 1, 1]
- Coin 2: dp = [1, 1, 2, 2, 3, 3]
- Coin 5: dp = [1, 1, 2, 2, 3, 4]
- Return 4. ✓

### Step 8: Discuss Trade-offs (3 min)
> "Three approaches:
> 1. **1D DP, coins outer:** O(n × A). Combinations.
> 2. **2D DP:** Same complexity, more space.
> 3. **Recursive memo:** Top-down, equivalent.
>
> I'll use 1D DP."

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to count combinations of coins summing to amount.

KEY INSIGHT: Unbounded knapsack with COUNTING.
- dp[i] = # combinations of processed coins summing to i.
- Loop order matters: COINS OUTER, AMOUNTS INNER.
- Amounts iterate FORWARD for unbounded.

ALGORITHM:
1. dp[0] = 1.
2. For each c in coins (OUTER):
     For j from c to amount (INNER forward):
       dp[j] += dp[j - c]
3. Return dp[amount].

COMPLEXITY: O(n × amount) time, O(amount) space.

EDGE CASES:
- amount = 0: return 1 (empty combination).
- No coins: 1 if amount=0, else 0.

WHY COINS OUTER:
Counts combinations. Coins INNER would count permutations.

WHY FORWARD:
Forward = unbounded (reuse coin). Reverse = 0/1 (use once).

THE TRICK: Loop order determines whether you count combinations
or permutations.

RELATED:
- Coin Change (LC 322): min coins.
- Combination Sum IV (LC 377): permutations.
- Climbing Stairs (LC 70).
"
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: 1D DP, Coins Outer (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | 1D DP (BEST) | O(nA) | O(A) | **THE ANSWER** |
| 6 | 1D variant | O(nA) | O(A) | Educational |
| 8 | Class OOP | O(nA) | O(A) | Reusable |
| 11 | Generator-style | O(nA) | O(A) | Educational |
| 15 | Explicit assign | O(nA) | O(A) | Educational |
| 18 | Polynomial view | O(nA) | O(A) | Educational |
| 20 | Final cleanest | O(nA) | O(A) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: 2D DP

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 2 | 2D DP | O(nA) | O(nA) | Educational |
| 7 | 2-row DP | O(nA) | O(A) | Memory-efficient |
| 13 | 2D dict memo | O(nA) | O(nA) | Educational |

### 🟠 TIER 3: Memoization / DFS

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 3 | Top-down lru | O(nA) | O(nA) | Top-down |
| 4 | Pure recursion | O(nA) | O(nA) | Educational |
| 5 | Memo recursive | O(nA) | O(nA) | Top-down |
| 9 | Helper recursion | O(nA) | O(nA) | Educational |
| 14 | Pure DFS | O(nA) | O(nA) | Educational |
| 16 | lru_cache | O(nA) | O(nA) | Educational |
| 17 | Iterative stack | O(nA) | O(nA) | Educational |
| 19 | itertools DP | O(nA) | O(A) | Educational |

### 🔵 TIER 4: Specialized

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 10 | Backtrack brute | O(n^A) | O(A) | Tiny amount |
| 12 | Numpy | O(nA) | O(A) | Vectorized |

---

## 💎 THE 6-LINE SOLUTION (Memorize!)

```python
def change(amount, coins):
    dp = [0] * (amount + 1)
    dp[0] = 1
    for c in coins:
        for j in range(c, amount + 1):
            dp[j] += dp[j - c]
    return dp[amount]
```

**Time:** `O(n × amount)`
**Space:** `O(amount)`

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Loop Order = Combination vs Permutation

> The most common mistake is reversing the loops.

Coins outer → combinations. Coins inner → permutations. Test by counting (1,2) vs (2,1) for amount=3 with coins=[1,2].

**Connection to:**
- **Combinatorics:** Order matters.
- **Test cases:** Always verify with examples.

### Insight 2: Iteration Direction = Bounded vs Unbounded

> Forward (c to amount) = unbounded. Reverse = 0/1 knapsack.

Same DP, different iteration.

**Connection to:**
- **Knapsack family:** 0/1, unbounded, bounded.
- **DP conventions:** Critical to know.

### Insight 3: dp[0] = 1 is the Empty Combination

> Without dp[0]=1, the DP wouldn't bootstrap.

This base case is crucial for counting.

**Connection to:**
- **Base cases:** Always check.
- **Mathematical foundation:** Identity element.

### Insight 4: Why 2D Reduces to 1D

> Since we iterate over coins, dp[i] only depends on current and previous coins.

1D rolling array suffices.

**Connection to:**
- **Space optimization:** Rolling arrays.
- **DP theory:** State dependencies.

### Insight 5: Connection to Polynomial Multiplication

> (1 + x^c + x^(2c) + ...) for each coin c. Coefficient of x^amount = answer.

The DP IS polynomial multiplication. Math explains the algorithm.

**Connection to:**
- **Generating functions:** Elegant view.
- **Math/CS connection:** Same algorithm.

### Insight 6: Real-World Applications

| Application | Use |
|-------------|-----|
| **Currency exchange** | Combinations of bills |
| **Inventory combinations** | Stock combinations |
| **Combinatorial chemistry** | Molecular combinations |
| **Lottery combinations** | Sum to target |
| **Change-making variants** | Ways to make change |
| **Resource allocation** | Combo of resources |

**Currency exchange** is the canonical use case.

### Insight 7: Why dp[0] = 1

> The empty combination sums to 0. There's exactly 1 way to do nothing.

This identity element enables the DP.

**Connection to:**
- **Mathematical identity:** 1 for multiplication.
- **DP base cases:** Critical.

### Insight 8: Itertools.product Analogy

> Brute force: itertools.product for coin choices. Exponential.

DP replaces exponential with polynomial.

**Connection to:**
- **Enumeration:** Brute vs DP.
- **Asymptotic tradeoffs:** O(n^A) → O(n × A).

### Insight 9: Edge Case: amount = 0

> Return 1 (one empty combination), even if no coins.

Counter-intuitive but correct mathematically.

**Connection to:**
- **Edge case testing:** Always include.
- **Mathematical rigor:** Empty set conventions.

### Insight 10: Connection to LC 70 Climbing Stairs

> Climbing Stairs is the same as 1 coin of size 1 + 1 coin of size 2.

Same DP, different problem.

**Connection to:**
- **Problem family:** Counting paths.
- **Skeleton reuse:** Adapt code.

### Insight 11: Top-Down vs Bottom-Up Equivalence

> Both are O(n × A). Top-down uses memoization; bottom-up uses iteration.

For interviews, bottom-up is often cleaner.

**Connection to:**
- **DP styles:** Two paradigms.
- **Implementation choice:** Pick by clarity.

### Insight 12: Why Iterate from c, not 0

> Starting at c ensures we don't access dp[negative].

Range bounds matter for correctness.

**Connection to:**
- **Edge case handling:** Python's negative indexing.
- **Defensive coding:** Always check bounds.

### Insight 13: Connection to Subset Sum

> Subset sum counts 0/1, this counts unbounded. Different iteration.

Same skeleton, different direction.

**Connection to:**
- **Knapsack variants:** Related problems.
- **DP patterns:** Reusable.

### Insight 14: When to Use 2D

> 2D needed for some advanced variants (e.g., bounded knapsack with counts).

For basic counting, 1D suffices.

**Connection to:**
- **Memory tradeoffs:** Space vs simplicity.
- **Algorithm choice:** Match problem.

---

## 🧪 TEST CASES

| `amount` | `coins` | Expected | Note |
|----------|---------|----------|------|
| `5` | `[1,2,5]` | 4 | Standard |
| `3` | `[2]` | 0 | Impossible |
| `10` | `[10]` | 1 | Trivial |
| `0` | `[1]` | 1 | Empty combination |
| `5` | `[1]` | 1 | All 1's |
| `0` | `[]` | 1 | Empty |
| `5` | `[]` | 0 | Impossible |
| `10` | `[1,2,5]` | 10 | Many combos |
| `3` | `[1,2]` | 2 | (1,1,1), (1,2) |
| `4` | `[1,2,3]` | 4 | Multiple |
| `100` | `[1,2,5]` | 541 | Larger |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **1D DP coins outer** | **O(nA)** | **O(A)** | **✅ BEST** |
| 2D DP | O(nA) | O(nA) | ✅ Educational |
| Top-down memo | O(nA) | O(nA) | ✅ Top-down |
| Brute backtrack | O(n^A) | O(A) | ❌ Slow |

A = amount, n = len(coins).

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Coin Change (LC 322) | Unbounded knapsack (min) | https://leetcode.com/problems/coin-change/ |
| Combination Sum IV (LC 377) | Permutations | https://leetcode.com/problems/combination-sum-iv/ |
| Climbing Stairs (LC 70) | Same DP | https://leetcode.com/problems/climbing-stairs/ |
| Ways to Make Change (gfg) | Same | Classic |
| Coin Change II (LC 518) | **This problem** | https://leetcode.com/problems/coin-change-2/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **Loop order matters** — coins outer = combinations.
2. **Forward iteration = unbounded**.
3. **dp[0] = 1** — empty combination identity.
4. **O(n × A)** dominates.
5. **Currency exchange** is canonical use case.
6. **Same skeleton as LC 322, 70**.
7. **Top-down equivalent** with memoization.
8. **Polynomial multiplication** is the math view.
9. **Edge case: amount=0** → 1.
10. **Test (1,2) vs (2,1)** to verify combination vs permutation.

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Currency exchange** | Combinations of bills |
| **Inventory** | Stock combinations |
| **Combinatorial chemistry** | Molecular combos |
| **Lottery** | Sum to target |
| **Change-making** | Ways to make change |
| **Resource allocation** | Resource combos |
| **Cryptography** | Combination counts |
| **Probability** | Combinatorial counting |
| **Optimization** | Counting valid solutions |
| **Network design** | Component combinations |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive the loop order in 60 seconds
- [x] Can code the 6-line solution in 90 seconds
- [x] Know complexity: O(n × A) time, O(A) space
- [x] Know why coins must be outer (combinations vs permutations)
- [x] Know why forward iteration (unbounded vs 0/1)
- [x] Know dp[0] = 1 base case
- [x] Know edge cases (amount=0, no coins)
- [x] Know related problems (LC 322, 377, 70)
- [x] Can list 5 real-world applications

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 10 minutes.
**Lines of code to write:** 6.
**Insight:** "Coins outer + amounts forward = unbounded combinations. dp[j] += dp[j-c] for c in coins outer loop."