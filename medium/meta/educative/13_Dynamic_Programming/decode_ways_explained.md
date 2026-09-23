# Decode Ways

## Problem
Count the number of ways to decode a digit string into letters:
- `'1'` → `'A'`, `'2'` → `'B'`, ..., `'26'` → `'Z'`.
- `'0'` and leading zeros are invalid.

## Approach: 1D DP

### State
`dp[i]` = number of ways to decode the prefix `s[:i]`.

### Transitions
At each position `i`, we can decode the last 1 or 2 digits:
- **Single digit** at position `i-1`: valid if it's not `'0'`.
- **Two-digit** number `s[i-2:i]`: valid if it's between 10 and 26 (inclusive).

```python
if s[i-1] != '0':
    dp[i] += dp[i-1]
if 10 <= int(s[i-2:i]) <= 26:
    dp[i] += dp[i-2]
```

### Base Cases
- `dp[0] = 1` (empty string → one way)
- `dp[1] = 1` if `s[0] != '0'`, else `0`
- If the string starts with `'0'` → return 0 immediately.

### Answer
`dp[n]`.

## Walkthrough: `"231012"`

```
i : 0  1  2  3  4  5  6
s :    2  3  1  0  1  2
dp: 1  1  2  3  ?  ?  ?
```

- `i=1` (s='2'): single '2' valid. dp[1] = 1.
- `i=2` (s='23'): single '3' → +dp[1]=1; two '23' valid → +dp[0]=1. dp[2]=2.
- `i=3` (s='231'): single '1' → +dp[2]=2; two '31' invalid. dp[3]=2.

Wait, the expected answer is 4, but my trace gives 2 at i=3. Let me re-check.

Actually, looking at the example in the problem: there are 4 decodings of "231012". Let me re-trace more carefully:

"231012":
- B,C,J,A,B (2,3,10,1,2)
- B,C,J,L (2,3,10,12)
- W,J,A,B (23,10,1,2)
- W,J,L (23,10,12)

So 4 ways. Let me redo the DP:

```
i=0: dp[0] = 1
i=1: s='2', single digit '2' valid → dp[1] = dp[0] = 1
i=2: s='23', single '3' → +dp[1]=1; two '23' (≤26) → +dp[0]=1; dp[2]=2
i=3: s='231', single '1' → +dp[2]=2; two '31' (>26) skip; dp[3]=2
i=4: s='2310', single '0' invalid; two '10' (10≤26) → +dp[2]=2; dp[4]=2
i=5: s='23101', single '1' → +dp[4]=2; two '01' invalid; dp[5]=2
i=6: s='231012', single '2' → +dp[5]=2; two '12' (12≤26) → +dp[4]=2; dp[6]=4 ✓
```

So `dp[6] = 4`. The earlier mistake: I was tracking s[i] instead of s[i-1].

## Complexity
- **Time:** `O(n)` — single pass
- **Space:** `O(n)` (can be reduced to `O(1)` with two variables)

## Edge Cases
- Empty string → 0
- String starting with `'0'` → 0
- `"10"` → 1 (decodes to `"J"`)
- `"100"` → 0 (no valid decoding)
- `"110"` → 1 (decodes as `"1,10"`)
- `"27"` → 1 (only `"2,7"`)
