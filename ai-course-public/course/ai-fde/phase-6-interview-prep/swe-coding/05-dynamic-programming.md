# SWE Coding Sub-Lesson 5 — Dynamic Programming (memoization, tabulation, state compression)

> **Dynamic programming is the fifth most common SWE coding pattern.** 10-15% of LeetCode medium-hard problems are DP problems. The FDE signal: a candidate who can identify the optimal substructure + the overlapping subproblems, write either top-down (memoization) or bottom-up (tabulation), and compress the state to O(1) space — is showing they can design efficient algorithms. **This sub-lesson covers 3 sub-patterns: memoization, tabulation, state compression.**

---

## Why DP is the FDE signal

The 3 things the interviewer is testing:

1. **Can you recognize the pattern?** DP is for problems with optimal substructure + overlapping subproblems. The 3 sub-patterns (memoization, tabulation, state compression) cover 80% of DP problems.
2. **Can you write both top-down and bottom-up?** Top-down (recursive + cache) is more intuitive; bottom-up (iterative) is more efficient. The candidate who can write both is showing depth.
3. **Can you compress the state?** Many DP problems only need the last 2 states (or last K states). The candidate who reduces O(n) space to O(1) is showing mastery.

**The FDE pattern:** clarify → brute force → identify subproblems → code → test. DP is the same as the other patterns, but the "optimize" step is recognizing the recursive structure.

---

## Sub-pattern 1: Memoization (Top-Down)

**The pattern:** recursive + cache. O(n) time typically, O(n) space for the cache + recursion stack.

**When to use:** clear recursive structure, easy to add caching, recursion depth is manageable.

**The template:**

```python
from functools import lru_cache

def dp_memo(n: int) -> int:
    @lru_cache(maxsize=None)
    def helper(state):
        if base_case(state):
            return base_value
        if state in cache:
            return cache[state]
        result = combine(helper(subproblem1), helper(subproblem2))
        cache[state] = result
        return result
    return helper(initial_state)
```

**Sample problem 1: Climbing Stairs**

> You are climbing a staircase. It takes n steps to reach the top. Each time you can climb 1 or 2 steps. How many distinct ways can you climb to the top?

```python
def climb_stairs(n: int) -> int:
    @lru_cache(maxsize=None)
    def helper(i):
        if i <= 1:
            return 1
        return helper(i - 1) + helper(i - 2)
    return helper(n)
```

**Time:** O(n). **Space:** O(n).

**Sample problem 2: House Robber**

> You are a robber. Each house has some money. You can't rob two adjacent houses. What's the maximum money you can rob?

```python
def rob(nums: list[int]) -> int:
    @lru_cache(maxsize=None)
    def helper(i):
        if i < 0:
            return 0
        return max(helper(i - 1), helper(i - 2) + nums[i])
    return helper(len(nums) - 1)
```

**Time:** O(n). **Space:** O(n).

**The 3 edge cases:** empty input, single house, all same money.

---

## Sub-pattern 2: Tabulation (Bottom-Up)

**The pattern:** iterative + array. O(n) time typically, O(n) space (or O(1) with state compression).

**When to use:** clear iterative structure, want to avoid recursion depth limits, want to optimize space.

**The template:**

```python
def dp_tabulation(n: int) -> int:
    dp = [base_value] * (n + 1)
    for i in range(1, n + 1):
        dp[i] = combine(dp[i - 1], dp[i - 2])
    return dp[n]
```

**Sample problem 1: Climbing Stairs (tabulation)**

```python
def climb_stairs_tabulation(n: int) -> int:
    if n <= 1:
        return 1
    dp = [0] * (n + 1)
    dp[0] = 1
    dp[1] = 1
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    return dp[n]
```

**Time:** O(n). **Space:** O(n).

**Sample problem 2: Coin Change**

> Given an array of coin denominations and a target amount, return the fewest number of coins needed to make up that amount. If impossible, return -1.

```python
def coin_change(coins: list[int], amount: int) -> int:
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    for i in range(1, amount + 1):
        for coin in coins:
            if coin <= i and dp[i - coin] + 1 < dp[i]:
                dp[i] = dp[i - coin] + 1
    return dp[amount] if dp[amount] != float('inf') else -1
```

**Time:** O(amount × len(coins)). **Space:** O(amount).

**The 3 edge cases:** amount = 0, no valid combination, single coin denomination.

---

## Sub-pattern 3: State Compression

**The pattern:** keep only the last 2 (or K) states. O(1) space.

**When to use:** DP[i] only depends on DP[i-1] and DP[i-2] (or last K states).

**The template:**

```python
def dp_compressed(n: int) -> int:
    prev2 = base_value_0
    prev1 = base_value_1
    for i in range(2, n + 1):
        current = combine(prev1, prev2)
        prev2 = prev1
        prev1 = current
    return prev1
```

**Sample problem 1: Climbing Stairs (compressed)**

```python
def climb_stairs_compressed(n: int) -> int:
    if n <= 1:
        return 1
    prev2, prev1 = 1, 1
    for _ in range(2, n + 1):
        current = prev1 + prev2
        prev2 = prev1
        prev1 = current
    return prev1
```

**Time:** O(n). **Space:** O(1).

**Sample problem 2: House Robber (compressed)**

```python
def rob_compressed(nums: list[int]) -> int:
    if not nums:
        return 0
    prev2, prev1 = 0, 0
    for num in nums:
        current = max(prev1, prev2 + num)
        prev2 = prev1
        prev1 = current
    return prev1
```

**Time:** O(n). **Space:** O(1).

**The 3 edge cases:** empty input, single house, all same money.

---

## The 4-step framework for DP problems

The 4 steps to solve any DP problem:

1. **Identify the state.** What changes between subproblems? (e.g., `i` in climbing stairs, `i` and `is_robbed` in house robber)
2. **Identify the base case.** What's the smallest subproblem? (e.g., `i = 0` → 1 way, `i = 1` → 1 way)
3. **Identify the recurrence.** How do you combine subproblems? (e.g., `dp[i] = dp[i-1] + dp[i-2]`)
4. **Identify the order.** Top-down (memoization) or bottom-up (tabulation)? Can you compress the state?

**The FDE answer:** "The state is `i` (the step number). The base case is `i = 0` (1 way) and `i = 1` (1 way). The recurrence is `dp[i] = dp[i-1] + dp[i-2]`. I can compress the state to O(1) space because `dp[i]` only depends on the last 2 states."

---

## The 5 most common DP problems

The 5 problems that cover 80% of DP interviews:

1. **Climbing Stairs** (Fibonacci) — covered above.
2. **House Robber** (1D DP, max of two choices) — covered above.
3. **Coin Change** (unbounded knapsack) — covered above.
4. **Longest Increasing Subsequence** (2D DP, patience sorting) — see below.
5. **Edit Distance** (2D DP, string alignment) — see below.

**Sample problem 4: Longest Increasing Subsequence**

> Given an array of integers, find the length of the longest strictly increasing subsequence.

```python
def length_of_lis(nums: list[int]) -> int:
    if not nums:
        return 0
    dp = [1] * len(nums)
    for i in range(1, len(nums)):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp)
```

**Time:** O(n²). **Space:** O(n). Can be optimized to O(n log n) with patience sorting.

**Sample problem 5: Edit Distance**

> Given two strings, return the minimum number of operations (insert, delete, replace) to convert `word1` to `word2`.

```python
def edit_distance(word1: str, word2: str) -> int:
    m, n = len(word1), len(word2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if word1[i - 1] == word2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[m][n]
```

**Time:** O(m × n). **Space:** O(m × n). Can be compressed to O(min(m, n)).

---

## The 5 anti-patterns for DP

1. **Jumping to code without identifying the state.** "I'll just start coding" is a junior answer. The state is the signal.
2. **Skipping the base case.** The base case is what stops the recursion. Without it, infinite loop.
3. **Not recognizing the recurrence.** The recurrence is the heart of DP. The candidate who can't name it is signaling they don't understand DP.
4. **Not compressing the state.** The candidate who uses O(n) space when O(1) is possible is showing they don't know the trade-offs.
5. **Not naming the complexity.** "O(n) time, O(1) space" is the FDE answer. "It's fast" is a junior answer.

---

## The 5 SWE coding etiquette rules for DP

1. **Clarify the problem first.** "What's the constraint on n? Are the numbers positive? Should I handle the empty case?" The questions are the signal.
2. **State the brute force.** "The naive solution is O(2^n) (recursive). Can I do better with DP?" The brute force is the floor.
3. **Identify the state + recurrence.** "The state is `i`. The recurrence is `dp[i] = dp[i-1] + dp[i-2]`." The state + recurrence is the signal.
4. **Walk through the code out loud.** "I start with dp[0] = 1, dp[1] = 1. For i = 2 to n, dp[i] = dp[i-1] + dp[i-2]." The walkthrough is the signal.
5. **Test with edge cases.** "If n = 0, I return 1. If n = 1, I return 1. If n = 2, I return 2." The edge cases are the signal.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "What's the time + space complexity?" | "O(n) time, O(1) space with state compression. Without compression, it's O(n) space." |
| 2. "How would you test this?" | "3 cases: empty input, single element, all duplicates. The edge cases are the canary." |
| 3. "How would you scale this to 1B records?" | "External sort + map-reduce. Or a streaming algorithm with O(1) memory. The trade-off is accuracy vs memory." |

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../practical-coding/README.md` | The AI-assisted coding round (the new norm) |
| `../system-design/README.md` | The 9 patterns (DP underpins Pattern 7: real-time collaborative systems) |
| `../swe-coding/01-arrays.md` | The 2 pointers / sliding window / prefix sum patterns |

---

## The thesis

**Dynamic programming is the fifth most common SWE coding pattern.** The candidate who can identify the optimal substructure + the overlapping subproblems, write either top-down or bottom-up, and compress the state to O(1) space — is showing they can design efficient algorithms.

**The 3 sub-patterns (memoization, tabulation, state compression) cover 80% of DP problems.** The 5 sample problems (climbing stairs, house robber, coin change, LIS, edit distance) are the muscle memory. Practice them out loud, time yourself at 25 minutes per problem, and rehearse with an AI assistant.

**General prep gets you past the resume screen. SWE coding prep gets you past the classic LeetCode round at Anthropic, OpenAI, Palantir, and AWS FDE.**