# Minimum Cost For Tickets - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-cost-for-tickets

## The Problem
```
Given days (sorted list of travel days) and costs (1-day, 7-day, 30-day
pass costs), find the minimum total cost to cover all travel days.

A pass bought on day d covers days d through d+duration-1.

Examples:
    days=[1,4,6,7,8,20], costs=[2,7,15] -> 11
    days=[1,2,3,4,5,6,7,8,9,10,30,31], costs=[2,7,15] -> 17

Constraints:
- 1 <= days.length <= 365
- 1 <= days[i] <= 365
- days is strictly increasing
- costs.length == 3
- 1 <= costs[i] <= 1000
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
We need to cover travel days with the cheapest combination of passes.
Each pass has a fixed duration and cost. The trick is choosing WHEN to
buy each pass type.
```

### Step 2: The Trick
> "KEY INSIGHT: DP over days.
>
> dp[d] = min cost to cover all travel days from day 1 to day d.
> dp[0] = 0.
>
> For each day d:
> - If d is NOT a travel day: dp[d] = dp[d-1] (no additional cost).
> - If d IS a travel day: try each pass type:
>   - 1-day: dp[d-1] + costs[0]
>   - 7-day: dp[d-7] + costs[1]  (pass bought on day d covers d-6 to d)
>   - 30-day: dp[d-30] + costs[2]"

### Step 3: Why dp[d-7] for 7-day pass?
> "A 7-day pass bought on day d covers days d through d+6. But for dp[d]
> we care about cost UP TO day d. dp[d-7] is the cost before day d-7+1 = d-6,
> so the 7-day pass on day d covers day d-6 to d, and dp[d-7] covers everything
> up to day d-7-1. Wait, let me reconsider.
>
> Actually: a pass on day d covers [d, d+6]. For dp[d] (cost up to day d),
> the pass contributes to days [d, d+6]. Days d-7+1 = d-6 to d-1 are NOT
> covered by THIS pass.
>
> The standard interpretation: a pass on day d means we pay the cost NOW
> (day d) and it covers 7 days starting today. dp[d-7] = min cost to cover
> up to day d-7-1 = day d-8... Hmm, this needs careful thought.
>
> Actually, the convention is: dp[d] = min cost considering days up to d.
> A 7-day pass bought on day d covers days d, d+1, ..., d+6. To use this
> pass, we need dp[d-7] to represent cost for days BEFORE day d-7+1 = d-6,
> i.e., days up to d-7. So dp[d-7] + 7-day-cost = total cost."

### Step 4: Algorithm
> "1. Build travel_set for O(1) lookup.
> 2. dp = [0] * (last_day + 1).
> 3. For d from 1 to last_day:
>    - If d not in travel_set: dp[d] = dp[d-1].
>    - Else: dp[d] = min(dp[d-1] + c[0], dp[max(0, d-7)] + c[1], dp[max(0, d-30)] + c[2]).
> 4. Return dp[last_day]."

### Step 5: Edge cases
> "- Single day: simple min of three passes.
> - All consecutive: 30-day usually best.
> - d-7 or d-30 < 0: clamp to 0 (no prior cost)."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to find the minimum cost to cover all travel days using 1-day, 7-day, or 30-day passes."

**Key Insight:**
> "DP over days. dp[d] = min cost to cover all travel days from 1 to d. For each travel day, try each pass type."

**Algorithm:**
> "1. dp[d] = min cost up to day d.
> 2. For d in 1..last_day:
>    - If not travel day: dp[d] = dp[d-1].
>    - Else: dp[d] = min(dp[d-1] + 1day, dp[d-7] + 7day, dp[d-30] + 30day)."

**Why this works:**
> "On a travel day, we buy a pass covering it. A 7-day pass bought today covers 7 days, so the cost BEFORE this pass was dp[d-7]. Same for 30-day."

**Edge cases:**
- d-7 or d-30 < 0: clamp to 0.
- All consecutive days: 30-day usually wins.
- Single day: 1-day pass.

**Complexity:**
- Time:  O(last_day) = O(365) — fixed horizon.
- Space: O(last_day).

---

## The 20 Implementations (Simple to Complex)

### Way 1: DP with set (BEST - Memorize!)
```python
def mincost_tickets_1(days, costs):
    travel_set = set(days)
    last_day = days[-1]
    dp = [0] * (last_day + 1)
    for d in range(1, last_day + 1):
        if d not in travel_set:
            dp[d] = dp[d - 1]
        else:
            dp[d] = min(
                dp[d - 1] + costs[0],
                dp[max(0, d - 7)] + costs[1],
                dp[max(0, d - 30)] + costs[2]
            )
    return dp[last_day]
```

### Way 2: Verbose
### Way 3: DP + index pointer
### Way 4: Top-down memo
### Way 5: DP over travel days
### Way 6: Class-based
### Way 7: numpy
### Way 8: While loop
### Way 9: Helper min_three
### Way 10: Recursive with memo
### Way 11: lru_cache decorator
### Way 12: Bool array
### Way 13: Functional
### Way 14: Sorted days
### Way 15: Most concise
### Way 16: enumerate
### Way 17: Binary search on days
### Way 18: Tabulation
### Way 19: Dict DP
### Way 20: Final cleanest

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Standard           | Way 1    | DP + set     |
| Top-down           | Way 4    | Memoization  |
| numpy              | Way 7    | Vectorized   |
| Iterative days     | Way 17   | Binary search|
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| DP (Way 1) | O(365) | O(365) | Best |
| Top-down (Way 4) | O(365) | O(365) | Same |
| Iterative (Way 17) | O(n * 30) | O(n) | Alternative |

---

## Walkthrough Example

```
days = [1, 4, 6, 7, 8, 20]
costs = [2, 7, 15]

travel_set = {1, 4, 6, 7, 8, 20}
last_day = 20

Step: Fill dp[1..20].
  d=1: travel. dp[1] = min(dp[0]+2, dp[0]+7, dp[0]+15) = 2.
  d=2: not travel. dp[2] = dp[1] = 2.
  d=3: not travel. dp[3] = dp[2] = 2.
  d=4: travel. dp[4] = min(dp[3]+2, dp[0]+7, dp[0]+15) = min(4, 7, 15) = 4.
  d=5: not travel. dp[5] = 4.
  d=6: travel. dp[6] = min(dp[5]+2, dp[0]+7, dp[0]+15) = min(6, 7, 15) = 6.
  d=7: travel. dp[7] = min(dp[6]+2, dp[0]+7, dp[0]+15) = min(8, 7, 15) = 7.
  d=8: travel. dp[8] = min(dp[7]+2, dp[1]+7, dp[0]+15) = min(9, 9, 15) = 9.
  ...
  d=20: travel. dp[20] = min(dp[19]+2, dp[13]+7, dp[0]+15).
    dp[19]: not travel. dp[19] = dp[18]. dp[18] = dp[17]. ... dp[9] = dp[8] = 9.
    dp[13]: not travel. dp[13] = dp[12] = ... = dp[9] = 9.
    dp[20] = min(9+2, 9+7, 0+15) = min(11, 16, 15) = 11.

Return 11.
```

---

## Best Answer to Memorize

```python
def mincostTickets(days, costs):
    travel_set = set(days)
    last_day = days[-1]
    dp = [0] * (last_day + 1)
    for d in range(1, last_day + 1):
        if d not in travel_set:
            dp[d] = dp[d - 1]
        else:
            dp[d] = min(
                dp[d - 1] + costs[0],
                dp[max(0, d - 7)] + costs[1],
                dp[max(0, d - 30)] + costs[2]
            )
    return dp[last_day]
```

**~12 lines. O(365) time. O(365) space. Interview-ready!**

---

## Key Insights

### Why dp[d-7] and dp[d-30]?
> "A pass bought on day d covers day d and onwards. The cost BEFORE this
> pass was the cost to cover everything up to (but not including) the pass's
> coverage. So dp[d-7] = cost up to 7 days BEFORE day d."

### Why clamp to 0?
> "If d-7 < 0, there's no prior cost (we're at the start). dp[0] = 0."

### Why iterate to last_day?
> "We need dp[last_day] to know the final cost. Iterating up to last_day
> ensures dp[last_day] is computed."

### Why use a set for travel_set?
> "O(1) membership check vs O(n) for list scan."

### What about the alternative state?
> "Iterate over TRAVEL DAYS instead of all days. dp[i] = min cost to cover
> first i travel days. Use binary search to find previous travel days.
> Same complexity, different state representation."

---

## Test Cases

| days | costs | Expected | Notes |
|------|-------|----------|-------|
| [1,4,6,7,8,20] | [2,7,15] | 11 | Standard |
| [1..10,30,31] | [2,7,15] | 17 | Long range |
| [1] | [2,7,15] | 2 | Single |
| [1,2] | [2,7,15] | 4 | Two consecutive |
| [5] | [10,1,100] | 1 | Cheap 7-day |
| [1,4,6,7,8,20] | [3,10,30] | 16 | Different costs |
| [1..7] | [2,7,15] | 7 | All 7-day |
| [1..8] | [2,7,15] | 9 | 8 days |
| [1..15] | [7,20,30] | 30 | 30-day wins |

---

## Common Pitfalls

1. **Off-by-one in dp[d-7]**: Make sure to clamp to 0 when d-7 < 0.
2. **Forgetting non-travel days**: dp[d] = dp[d-1] for non-travel days.
3. **Wrong last_day**: Must be days[-1] (last travel day), not len(days).
4. **Recursion depth**: Top-down can hit recursion limit for large day numbers.
5. **Not handling impossible**: This problem always has a solution (1-day pass).

---

## Why This Problem Matters

> "Tests:
> 1. DP with multiple options per state.
> 2. Bounded horizon (1, 7, 30 days).
> 3. Non-trivial states (travel day vs not).
> 4. Foundation for: bounded knapsack, scheduling problems."

---

## Beyond This Problem: Related Patterns

### 1. Coin Change (LC 322)
```python
# Similar DP structure with bounded choices.
```

### 2. Decode Ways (LC 91)
```python
# Different state but similar bounded horizon.
```

### 3. House Robber (LC 198)
```python
# Two options per state (rob or skip).
```

### 4. Perfect Squares (LC 279)
```python
# Min number of perfect squares summing to n.
```

---

## Connection to Bounded Horizon DP

This problem is a "bounded horizon DP" where the recurrence depends on a
fixed window of past states:

```
PATTERN:
- dp[i] depends on dp[i-1], dp[i-7], dp[i-30] (bounded).
- Initialize dp[0] = 0.
- Iterate i from 1 to last.

EXAMPLES:
- Minimum Cost For Tickets (1, 7, 30 days).
- Stock Buy/Sell with Cooldown (1 day cooldown).
- Job Scheduling with Weights.
```

The bounded horizon enables O(1) transition per state.

---

## Quick Checklist

When given a similar problem:
- [ ] Define the state (dp[d] for days).
- [ ] Identify the recurrence options (1-day, 7-day, 30-day).
- [ ] Handle non-relevant days (dp[d] = dp[d-1] for non-travel).
- [ ] Clamp indices (max(0, d-7)).
- [ ] Initialize dp[0] = 0.
- [ ] Iterate up to the appropriate bound (last_day).

---

## Mathematical Formulation

Let T = days (sorted), C = costs (1-day, 7-day, 30-day):

```
dp[d] = 0 if d == 0
dp[d] = dp[d-1] if d not in T
dp[d] = min(dp[d-1] + C[0], dp[d-7] + C[1], dp[d-30] + C[2]) if d in T
       (with dp[d-7] = 0 if d-7 < 0, etc.)

Answer = dp[days[-1]].
```

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 983 - Minimum Cost For Tickets](https://leetcode.com/problems/minimum-cost-for-tickets/)