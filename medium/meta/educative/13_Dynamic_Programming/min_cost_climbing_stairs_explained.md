# Min Cost Climbing Stairs

## Problem
You can start at step 0 or step 1 (no initial cost). Each step `i` has a
cost `cost[i]` you pay when landing on it. From any step you may jump
1 or 2 steps forward. Return the minimum cost to reach the position
just past the last stair.

## Approach: 1D Dynamic Programming

### State
`dp[i]` = minimum cost to land on step `i`.

### Transitions
You reach step `i` from either `i-1` or `i-2`:
```
dp[i] = cost[i] + min(dp[i-1], dp[i-2])
```

### Base Cases
- `dp[0] = cost[0]`
- `dp[1] = cost[1]`

### Answer
To reach the "top" (one past the last stair), you can jump from step
`n-1` or `n-2` without paying any additional cost. So:
```
answer = min(dp[n-1], dp[n-2])
```

## Walkthrough: `[1, 100, 1, 1, 1, 100, 1, 1, 100, 1]`

dp:
```
1  100  2    3    3    103   4    5    104  6
```

The two minimum-cost paths:
- 0 → 2 → 4 → 6 → 8 → 9 (or 10): pays 1+1+1+1+1 = 5
- 1 → 3 → 5 → 7 → 9 (or 10): pays 100+1+100+1+1 = 203

Wait, that's not right. Let me retrace.

Optimal: start at step 0, then jump to step 2 (cost 1), to step 4 (cost 1),
to step 6 (cost 1), to step 8 (cost 1), to step 10 (cost 1) — but step 10
doesn't exist. From step 8 jump to the top (no cost), from step 9 jump to
the top.

Actually, the optimal path: 0 → 2 (cost 1) → 4 (cost 1) → 6 (cost 1) → top.
Total = 1 + 1 + 1 = 3? Or 1 + 1 + 1 + 1 = 4? Let me re-check.

Actually `cost = [1, 100, 1, 1, 1, 100, 1, 1, 100, 1]`, n=10.

Starting at step 0 (cost 1):
- 0 → 2: paid 1, dp[2] = 1 + min(dp[1]=100, dp[0]=1) = 1 + 1 = 2
- 0 → 2 → 4: dp[4] = 1 + min(dp[3], dp[2]) = 1 + min(3, 2) = 3
- 0 → 2 → 4 → 6: dp[6] = 1 + min(dp[5]=103, dp[4]=3) = 1 + 3 = 4
- 0 → 2 → 4 → 6 → 8: dp[8] = 100 + min(dp[7]=5, dp[6]=4) = 104
- 0 → 2 → 4 → 6 → top: pay up to step 6 = 4, then jump to top

Starting at step 1 (cost 100):
- 1 → 3: dp[3] = 1 + min(dp[2]=2, dp[1]=100) = 1 + 2 = 3
- 1 → 3 → 5: dp[5] = 100 + min(dp[4]=3, dp[3]=3) = 103
- 1 → 3 → 5 → 7: dp[7] = 1 + min(dp[6]=4, dp[5]=103) = 5
- 1 → 3 → 5 → 7 → 9: dp[9] = 1 + min(dp[8]=104, dp[7]=5) = 6
- 1 → 3 → 5 → 7 → top: pay up to step 7 = 5

Answer = min(dp[9]=6, dp[8]=104) = **6** ✓

## Complexity
- **Time:** `O(n)`
- **Space:** `O(n)` (can be reduced to `O(1)` with two variables)

## Edge Cases
- All zero costs → 0
- Two-element array → min of the two
