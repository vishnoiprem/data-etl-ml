# Edit Distance (Levenshtein Distance)

## Problem
Given two strings `word1` and `word2`, return the minimum number of
operations required to convert `word1` into `word2`, where allowed
operations are:
- Insert a character
- Delete a character
- Replace a character

## Approach: 2D Dynamic Programming

### State
`dp[i][j]` = minimum operations to transform `word1[:i]` into `word2[:j]`.

### Transitions
Consider the last characters `word1[i-1]` and `word2[j-1]`:

- **Match** (`word1[i-1] == word2[j-1]`): No extra operation needed.
  `dp[i][j] = dp[i-1][j-1]`

- **Mismatch** (3 options, take the minimum + 1):
  - **Replace** `word1[i-1]` with `word2[j-1]`: `dp[i-1][j-1] + 1`
  - **Delete** `word1[i-1]`: `dp[i-1][j] + 1`
  - **Insert** `word2[j-1]` after `word1[i-1]`: `dp[i][j-1] + 1`

```
dp[i][j] = dp[i-1][j-1]                                    if match
         = 1 + min(dp[i-1][j-1], dp[i-1][j], dp[i][j-1])  otherwise
```

### Base Cases
- `dp[i][0] = i` (delete all `i` characters from `word1` to get empty string)
- `dp[0][j] = j` (insert all `j` characters to get `word2`)

### Answer
`dp[m][n]` where `m = len(word1)`, `n = len(word2)`.

## Walkthrough: `word1 = "horse"`, `word2 = "ros"`

```
       ""   r   o   s
   ""   0   1   2   3
   h    1   1   2   3
   o    2   2   1   2
   r    3   2   2   2
   s    4   3   3   2
   e    5   4   4   3
```

Answer: `dp[5][3] = 3` ✅

Operations: `horse -> rorse (replace h→r) -> rose (delete r) -> ros (delete e)`.

## Complexity
- **Time:** `O(m * n)` where `m = len(word1)`, `n = len(word2)`
- **Space:** `O(m * n)` (can be reduced to `O(min(m, n))` using rolling array)

## Edge Cases
- Both strings empty → 0
- One string empty → length of other
- Identical strings → 0
