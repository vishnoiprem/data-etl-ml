# Palindromic Substrings

## Problem
Given a string `s`, count the number of palindromic substrings
(contiguous palindromes).

## Approach: Expand Around Center

### Key Insight
Every palindrome has a **center**. There are `2n - 1` possible
centers in a string of length `n`:
- `n` centers are single characters (odd-length palindromes)
- `n - 1` centers are gaps between characters (even-length palindromes)

From each center, expand outward while the substring remains a
palindrome, counting each palindrome we find.

### Algorithm
```python
count = 0
for center in range(n):
    count += expand(center, center)        # odd-length
    count += expand(center, center + 1)    # even-length

def expand(left, right):
    c = 0
    while left >= 0 and right < n and s[left] == s[right]:
        c += 1
        left -= 1
        right += 1
    return c
```

## Walkthrough: `s = "abba"`

Centers (i, i) odd, (i, i+1) even:

| Center | Expansions found           | Count |
|--------|----------------------------|-------|
| 0      | "a"                        | 1     |
| 0,1    | "bb"                       | 1     |
| 1      | "b"                        | 1     |
| 1,2    | "b" (mismatch with 'a')    | 0     |
| 2      | "b"                        | 1     |
| 2,3    | "bb"                       | 1     |
| 3      | "a"                        | 1     |

Total = **6** ✓
Palindromes: `a, b, b, a, bb, abba`.

## Walkthrough: `s = "aaa"`

| Center | Expansions           | Count |
|--------|----------------------|-------|
| 0      | "a", "aaa"           | 2     |
| 0,1    | "aa"                 | 1     |
| 1      | "a", "aa"            | 2     |
| 1,2    | "aa"                 | 1     |
| 2      | "a"                  | 1     |

Total = 2+1+2+1+1 = **6** ✓

## Complexity
- **Time:** `O(n²)` — each center expands at most `O(n)` times
- **Space:** `O(1)` — only constant extra memory

## Alternative: 2D DP
`dp[i][j]` = `True` if `s[i:j+1]` is a palindrome.
```
dp[i][j] = (s[i] == s[j]) and (j - i < 3 or dp[i+1][j-1])
```
Counts: `O(n²)` time, `O(n²)` space. More general but uses more memory.

## Edge Cases
- Empty string → 0
- Single character → 1
- All same character → `n(n+1)/2` palindromes
