# Day 31 — Algorithms: Dynamic Programming
**Module 21** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

**Dynamic programming** = recursion + memoization. The two flavors:
- **Top-down:** recursive function, cache results in a hash map or array.
- **Bottom-up:** iterative, fill a table from base case up.

DP is for problems where the answer to a sub-problem is reused many times. The **recurrence** is the heart of DP — find it and the rest is bookkeeping.

---

## 2. Technical concepts (20 min)

### The 5-step DP framework

1. **Define the state.** What does `dp[i]` (or `dp[i][j]`) represent?
2. **Find the recurrence.** How does `dp[i]` relate to smaller states?
3. **Set base cases.** What's `dp[0]`?
4. **Choose top-down vs bottom-up.**
5. **Optimize space.** Often you only need the last 1–2 rows.

### When to suspect DP
- "Count the number of ways..."
- "Min/max cost to..."
- "Is it possible to..."
- The naive solution is exponential and you see overlapping subproblems.

### Common 1D patterns

| Problem | State | Recurrence |
|---|---|---|
| Climbing Stairs | `dp[i]` = ways to reach step `i` | `dp[i] = dp[i-1] + dp[i-2]` |
| Coin Change | `dp[i]` = min coins for amount `i` | `dp[i] = min(dp[i-c]+1 for c in coins)` |
| House Robber | `dp[i]` = max robbed from first `i` | `dp[i] = max(dp[i-1], dp[i-2]+nums[i])` |
| LIS | `dp[i]` = LIS ending at `i` | `dp[i] = max(dp[j]+1 for j<i if nums[j]<nums[i])` |
| Word Break | `dp[i]` = can break `s[:i]` | `dp[i] = any(dp[i-len(w)] for w in words if s[i-len(w):i]==w)` |

### Common 2D patterns

| Problem | State | Recurrence |
|---|---|---|
| LCS | `dp[i][j]` = LCS of `s1[:i]`, `s2[:j]` | `dp[i][j] = dp[i-1][j-1]+1 if s1[i]==s2[j] else max(dp[i-1][j], dp[i][j-1])` |
| Edit Distance | `dp[i][j]` = min edits | 3 cases (insert/delete/replace) |
| Knapsack 0/1 | `dp[i][w]` = max value with capacity `w` using first `i` items | include or exclude item `i` |
| Matrix path | `dp[i][j]` = paths from `(0,0)` to `(i,j)` | `dp[i][j] = dp[i-1][j] + dp[i][j-1]` |

### Space optimization
- `dp[i]` only needs `dp[i-1]` and `dp[i-2]`. Use 2 vars.
- `dp[i][j]` only needs the previous row. Use 1D `dp[j]` updated right-to-left.
- 90% of 2D DP can be reduced to 1D.

### Memoization
```python
from functools import lru_cache

@lru_cache(maxsize=None)
def dp(i):
    if i < 0: return 0
    return dp(i-1) + dp(i-2)
```

---

## 3. Coding (30 min)

Solve **3 problems**, ~10 min each.

### Problem 1: Climbing Stairs

```python
def climb_stairs(n: int) -> int:
    if n < 2: return 1
    a, b = 1, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b
```

- **Time:** O(n). **Space:** O(1).
- **Sample:** `n=3` → `3` (111, 12, 21).

### Problem 2: Coin Change

```python
def coin_change(coins: list[int], amount: int) -> int:
    INF = float("inf")
    dp = [0] + [INF] * amount
    for i in range(1, amount + 1):
        for c in coins:
            if c <= i and dp[i - c] + 1 < dp[i]:
                dp[i] = dp[i - c] + 1
    return dp[amount] if dp[amount] != INF else -1
```

- **Time:** O(amount × len(coins)). **Space:** O(amount).
- **Sample:** `coins=[1,5,10,25], amount=30` → `2` (5+25).

### Problem 3: Longest Common Subsequence

```python
def lcs(s1: str, s2: str) -> int:
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    return dp[m][n]
```

- **Time:** O(m·n). **Space:** O(m·n) → O(min(m, n)) with rolling array.
- **Sample:** `"abcde", "ace"` → `3`.

---

## 4. Debugging & tests (20 min)

### Bug 1: climbing_stairs returns wrong for n=1
**Fix:** `if n < 2: return 1`. Both `n=0` and `n=1` have 1 way.

### Bug 2: coin_change returns INF for impossible amount
**Fix:** return `-1` if `dp[amount] == INF`. Don't return `float('inf')`.

### Bug 3: lcs off-by-one in the table
**Symptom:** `lcs("a", "")` returns 1.
**Fix:** table is `(m+1) × (n+1)`; access `s1[i-1]` not `s1[i]`. The 0-th row/col is the empty-string case.

### Bug 4: bottom-up state ordering wrong
**Symptom:** House Robber gives wrong answer.
**Fix:** make sure you process `dp[i]` before using `dp[i-1]`. Forward iteration.

### Tests
```python
def test_climb_stairs():
    assert climb_stairs(1) == 1
    assert climb_stairs(2) == 2
    assert climb_stairs(3) == 3
    assert climb_stairs(5) == 8

def test_coin_change():
    assert coin_change([1, 5, 10, 25], 30) == 2
    assert coin_change([2], 3) == -1
    assert coin_change([1], 0) == 0
    assert coin_change([186, 419, 83, 408], 6249) == 20  # famous LeetCode gotcha: large coins force a slow greedy; DP must run to completion

def test_lcs():
    assert lcs("abcde", "ace") == 3
    assert lcs("abc", "abc") == 3
    assert lcs("abc", "def") == 0
    assert lcs("", "abc") == 0
```

---

## 5. Mock interview practice (20 min)

**Q1 — "How do you know it's DP?"**
> "Number of ways" or "min/max cost" + overlapping subproblems. The brute force is exponential; the DP is polynomial.

**Q2 — "Top-down vs bottom-up?"**
> Top-down: cleaner code, only computes needed states, recursion overhead. Bottom-up: faster, no stack, easier to space-optimize.

**Q3 — "How do you space-optimize LCS?"**
> `dp[i][j]` only needs the previous row. Use a 1D array and iterate `j` from right to left so you don't overwrite `dp[j-1]`.

**Q4 — "What's the difference between 0/1 knapsack and unbounded knapsack?"**
> 0/1: each item once. Unbounded: unlimited copies. Unbounded uses inner loop over capacity (forward); 0/1 uses inner loop over capacity (backward).

**Q5 — "DP on strings — when do you use 2D vs 1D?"**
> 2D when both strings vary (LCS, edit distance). 1D when one is fixed (word break, decode ways).

---

## 6. Success criteria check
- [ ] I can write the 5-step framework.
- [ ] I can name 3 1D and 3 2D patterns.
- [ ] I can space-optimize LCS to O(min(m,n)).
- [ ] I can solve Coin Change in < 10 min.

## 7. Grade yourself 0–10
| Area | Score |
|---|---|
| Correctness | /10 |
| Code quality | /10 |
| Debugging | /10 |
| Performance | /10 |
| Testing | /10 |
| Communication | /10 |
| **Total** | **/60** |

## 8. Coding assignment
**Edit Distance** — minimum number of operations (insert, delete, replace) to convert `word1` to `word2`.

### Rubric (0–10)
- 0: doesn't compile
- 4: brute force recursion (exponential)
- 5: top-down with memo
- 7: bottom-up 2D
- 9: bottom-up 2D with correct recurrence
- 10: space-optimized to 1D

### Solution
```python
def edit_distance(w1: str, w2: str) -> int:
    m, n = len(w1), len(w2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1): dp[i][0] = i
    for j in range(n + 1): dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if w1[i-1] == w2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(
                    dp[i-1][j],    # delete
                    dp[i][j-1],    # insert
                    dp[i-1][j-1],  # replace
                )
    return dp[m][n]
```

**Time: 90 min**
