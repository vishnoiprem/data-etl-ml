# Number of People Aware of a Secret

## Problem
On day 1, one person discovers a secret. After a delay of `delay` days,
each person who knows the secret shares it with **one new person per day**.
Each person forgets the secret `forget` days after learning it. Return
the number of people aware of the secret at the end of day `n`,
modulo `10^9 + 7`.

## Approach: Bottom-Up DP

### Key Insight
Instead of tracking every individual, track only how many people **first
learn** the secret on each day.

Let `dp[d]` = number of new people who discover the secret on day `d`.
- `dp[1] = 1` (the initial discoverer).
- For day `d`, the new learners come from people who learned the secret
  on a previous day `d0` such that:
  - `d0 + delay ≤ d` (they've started sharing by day `d`)
  - `d0 + forget > d` (they still remember the secret on day `d`)
- That is, `d - forget + 1 ≤ d0 ≤ d - delay`.

### Number Aware at End of Day `n`
A person who learned on day `d0` is still aware on day `n` iff
`d0 + forget > n`, i.e., `d0 ≥ n - forget + 1`.

So the answer is:
```
sum(dp[d] for d in [n - forget + 1, n])
```

## Algorithm
1. Initialize `dp[1] = 1`, rest zero.
2. For `day` from 2 to `n`:
   - `start = max(1, day - forget + 1)`
   - `end = day - delay`
   - If `end ≥ start`: `dp[day] = sum(dp[start..end]) % MOD`.
3. Return `sum(dp[start..n]) % MOD` where `start = max(1, n - forget + 1)`.

## Walkthrough: `n=6, delay=2, forget=4`

| day | dp[day] | Reason |
|-----|---------|--------|
| 1   | 1       | Initial discoverer |
| 2   | 0       | delay=2, no one is sharing yet |
| 3   | 1       | Person from day 1 starts sharing → shares with 1 |
| 4   | 1       | Person from day 1 still sharing; day 1 person forgets today |
| 5   | 1       | Person from day 3 shares; day 3 person forgets in 2 days |
| 6   | 2       | Day 3 and day 4 people each share with 1 new person |

Aware at end of day 6: people who learned on days 3, 4, 5, 6 (forget on day 7+)
= dp[3] + dp[4] + dp[5] + dp[6] = 1 + 1 + 1 + 2 = **5** ✅

## Complexity
- **Time:** `O(n * forget)` naive, but with prefix sums we can do `O(n)`.
  For n ≤ 1000 the simple sum is fine.
- **Space:** `O(n)` for the `dp` array.

## Edge Cases
- `delay = forget - 1`: sharing window is exactly 1 day.
- Large `n`: modulo `10^9 + 7` prevents overflow.
