# Longest Common Subsequence — 0.0001% Expert Guide

> **LeetCode 1143** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/longest-common-subsequence
> **Problem:** `longestCommonSubsequence(str1, str2)` — length of LCS.

---

## 📋 WHAT THE QUESTION ASKS

Given two strings, find the length of the longest common subsequence (LCS).

A subsequence preserves order but allows skipping characters. Return 0 if none.

### Constraints
- `1 <= str1.length, str2.length <= 500`
- Lowercase English letters

### Examples
```
s1='abcde', s2='ace' -> 3   (the subsequence "ace")
s1='abc', s2='abc' -> 3
s1='abc', s2='def' -> 0
s1='', s2='abc' -> 0
s1='bl', s2='yby' -> 1   (just "b")
s1='ezupk', s2='ubmrapg' -> 2   ("up")
s1='aggtab', s2='gxtxayb' -> 4   ("gtab")
```

### Why This Is "Medium"
- Classic 2D DP.
- O(n*m) time and space.
- Foundation for Edit Distance, LPS.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Longest sequence appearing in both, in order."

### Step 2: KEY INSIGHT — 2D DP (5 min)
> "dp[i][j] = LCS length of s1[0..i-1] and s2[0..j-1].
>
> Base: dp[0][*] = 0, dp[*][0] = 0.
>
> Transition:
> - If s1[i-1] == s2[j-1]: dp[i][j] = dp[i-1][j-1] + 1.
> - Else: dp[i][j] = max(dp[i-1][j], dp[i][j-1]).
>
> Match: extend the diagonal.
> Mismatch: skip one char from either string."

### Step 3: Why Match = dp[i-1][j-1] + 1 (3 min)
> "If chars match, we can extend the LCS of s1[0..i-2], s2[0..j-2]
> by appending this char. Length + 1."

### Step 4: Algorithm (3 min)
```
1. dp = [[0] * (m+1) for _ in range(n+1)].
2. For i in 1..n:
     For j in 1..m:
       If s1[i-1] == s2[j-1]: dp[i][j] = dp[i-1][j-1] + 1.
       Else: dp[i][j] = max(dp[i-1][j], dp[i][j-1]).
3. Return dp[n][m].
```

### Step 5: Edge Cases (2 min)
- Empty string: 0.
- Equal strings: length.
- All different: 0.
- Subset relation: shorter length.

### Step 6: Code It (3 min)

```python
def longestCommonSubsequence(s1, s2):
    n, m = len(s1), len(s2)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[n][m]
```

### Step 7: Verify (2 min)
For s1='abcde', s2='ace':
```
       ''  a  c  e
   ''   0  0  0  0
   a    0  1  1  1
   b    0  1  1  1
   c    0  1  2  2
   d    0  1  2  2
   e    0  1  2  3
```
dp[5][3] = 3 ✓ (matches "ace")

### Step 8: Discuss Trade-offs (3 min)
> "Three approaches:
> 1. **2D DP:** O(n*m) time, O(n*m) space. **BEST**.
> 2. **1D DP rolling:** O(n*m) time, O(min(n,m)) space.
> 3. **DFS + memo:** Top-down, same complexity.
>
> I'll use 1D rolling for interviews."

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need the LCS length of two strings.

KEY INSIGHT: 2D DP. dp[i][j] = LCS of s1[0..i-1] and s2[0..j-1].

BASE: dp[0][*] = dp[*][0] = 0.

TRANSITION:
- If s1[i-1] == s2[j-1]: dp[i][j] = dp[i-1][j-1] + 1.
- Else: dp[i][j] = max(dp[i-1][j], dp[i][j-1]).

ALGORITHM:
1. dp = [[0] * (m+1) for _ in range(n+1)].
2. Iterate i, j. Apply transition.
3. Return dp[n][m].

COMPLEXITY: O(n*m) time, O(n*m) space (or O(min(n,m)) rolling).

EDGE CASES:
- Empty: 0.
- Equal: length.
- No common: 0.

THE TRICK:
- Match → extend diagonal.
- Mismatch → skip one (max of two directions).

SPACE-OPTIMIZED:
1D rolling array. Track prev_diag (= dp[i-1][j-1] before update).
For j: save temp = dp[j], then update dp[j] based on s1[i-1] vs s2[j-1],
then prev_diag = temp.

RELATED:
- Edit Distance (LC 72): 3-way transition.
- Longest Common Substring: reset on mismatch.
- LPS(s) = LCS(s, reverse(s)).
- Distinct Subsequences (LC 115).
"
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: 2D DP (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | Standard 2D DP | O(n*m) | O(n*m) | **THE ANSWER** |
| 5 | 2D verbose base | O(n*m) | O(n*m) | Educational |
| 9 | Diagonal iter | O(n*m) | O(n*m) | Educational |
| 10 | Reverse iter | O(n*m) | O(n*m) | Educational |
| 11 | Same as 1 | O(n*m) | O(n*m) | Duplicate |
| 13 | Explicit if-else | O(n*m) | O(n*m) | Educational |
| 16 | Refs DP | O(n*m) | O(n*m) | Educational |
| 18 | Smaller outer | O(n*m) | O(n*m) | Cache-friendly |
| 19 | 2D explicit init | O(n*m) | O(n*m) | Educational |

### 🟡 TIER 2: 1D DP Rolling (Space-Optimized)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 2 | 1D rolling | O(n*m) | O(m) | **Space-optimized** |
| 6 | 1D with swap | O(n*m) | O(min) | Min space |
| 12 | Double buffer | O(n*m) | O(m) | Variant |
| 20 | Final cleanest | O(n*m) | O(m) | **THE ONE TO MEMORIZE** |

### 🟠 TIER 3: Memoization / DFS

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 3 | Top-down memo | O(n*m) | O(n*m) | Top-down |
| 4 | Memo dict | O(n*m) | O(n*m) | Educational |
| 8 | Closure memo | O(n*m) | O(n*m) | Educational |
| 15 | Closure pre-fill | O(n*m) | O(n*m) | Educational |

### 🔵 TIER 4: Specialized

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 7 | Class OOP | O(n*m) | O(n*m) | Reusable |
| 14 | Numpy | O(n*m) | O(n*m) | Vectorized |
| 17 | Pure recursion | O(2^(n+m)) | O(n+m) | Bad |

---

## 💎 THE 8-LINE SOLUTION (Memorize!)

```python
def longestCommonSubsequence(s1, s2):
    n, m = len(s1), len(s2)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[n][m]
```

**Time:** `O(n*m)`
**Space:** `O(n*m)` or `O(min(n,m))` with rolling.

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Match → Diagonal Extension

> When chars match: dp[i][j] = dp[i-1][j-1] + 1.
> We extend LCS by appending this char.

**Connection to:**
- **DP recurrence:** Diagonal.
- **Standard pattern:** LCS, Edit Distance.

### Insight 2: Mismatch → Max of Two Skips

> When chars mismatch: skip s1[i-1] OR skip s2[j-1].
> Take the better option.

**Connection to:**
- **Choice:** Two paths.
- **Max:** Combine options.

### Insight 3: LPS = LCS Trick

> Longest Palindromic Subsequence = LCS(s, reverse(s)).

Cross-problem reduction.

**Connection to:**
- **Problem reduction:** Same algorithm.
- **Code reuse:** Adapt.

### Insight 4: Rolling Array with prev_diag

> 1D DP. Save dp[j] before update = dp[i-1][j] = "above".
> Save dp[j-1] = "left". prev_diag = dp[i-1][j-1] = "above-left".

**Connection to:**
- **Space optimization:** Standard trick.
- **Index tracking:** Critical.

### Insight 5: Why Swap Strings

> When |s1| << |s2|, swap so dp array is smaller (O(|s1|) space).

**Connection to:**
- **Optimization:** Always minimal.
- **Practical:** Save memory.

### Insight 6: Connection to Edit Distance

> Edit Distance: dp[i][j] = 3-way min (delete, insert, replace).
> LCS: dp[i][j] = 2-way max (match, skip).

Same skeleton, different transitions.

**Connection to:**
- **DP family:** String DP.
- **Reusable code:** Common skeleton.

### Insight 7: Real-World Applications

| Application | Use |
|-------------|-----|
| **Diff (Unix)** | Show file differences |
| **DNA sequencing** | Sequence alignment |
| **Plagiarism detection** | Document similarity |
| **Version control** | File merge |
| **Spell checking** | Word similarity |
| **Bioinformatics** | Genetic matching |

**Unix diff** is the canonical use case.

### Insight 8: Why Iterate by Row

> dp[i][j] needs dp[i-1][j-1], dp[i-1][j], dp[i][j-1].
> All "above" or "current row left" — both already computed.

**Connection to:**
- **Iteration order:** Top-down row by row.
- **DP correctness:** Standard.

### Insight 9: Subsequence vs Substring

> Substring = contiguous. Subsequence = any order.
> Substring needs reset on mismatch. Subsequence doesn't.

**Connection to:**
- **Different problems:** Different recurrence.
- **Common confusion:** Easy to mix.

### Insight 10: How to Reconstruct the LCS

> Trace back from dp[n][m]. If chars match, record and move diagonally.
> Else, move to the larger of dp[i-1][j] or dp[i][j-1].

**Connection to:**
- **Reconstruction:** Standard pattern.
- **Path recovery:** Using dp table.

### Insight 11: Memoization Equivalence

> Bottom-up 2D DP = top-down DFS with memo.
> Same complexity. Pick by preference.

**Connection to:**
- **Two paradigms:** Same result.
- **Pick by style:** Top-down or bottom-up.

### Insight 12: Why Diagonal Order Works

> Iterate cells in order where i+j is constant.
> For each cell, all 3 dependencies are earlier in order.

**Connection to:**
- **Topological order:** Valid iteration.
- **Educational:** Other valid orders.

### Insight 13: Reverse Iteration

> Iterate from (n-1, m-1) backward: dp[i][j] uses dp[i+1][*].
> Reverse indexing in dp.

**Connection to:**
- **Alternative order:** Valid.
- **Educational:** Different view.

### Insight 14: Connection to Distinct Subsequences

> LC 115: count distinct subsequences of s2 in s1.
> Similar 2D DP, different transition.

**Connection to:**
- **Problem variants:** Closely related.
- **Reusable:** Same skeleton.

### Insight 15: When 1D Suffices

> For just the LENGTH, 1D suffices.
> For RECONSTRUCTION, need full 2D.

**Connection to:**
- **Memory:** Trade-off.
- **Application:** Match need.

### Insight 16: Multiple LCS May Exist

> We return length. There may be multiple LCS sequences.
> For enumeration, BFS/DFS from dp.

**Connection to:**
- **Combinatorics:** Multiple answers.
- **DP:** Returns length, not sequence.

---

## 🧪 TEST CASES

| `s1` | `s2` | Expected | Note |
|------|------|----------|------|
| `'abcde'` | `'ace'` | 3 | Standard |
| `'abc'` | `'abc'` | 3 | Equal |
| `'abc'` | `'def'` | 0 | No common |
| `''` | `'abc'` | 0 | Empty |
| `'abc'` | `''` | 0 | Empty |
| `'bl'` | `'yby'` | 1 | `b` |
| `'ezupk'` | `'ubmrapg'` | 2 | `up` |
| `'aggtab'` | `'gxtxayb'` | 4 | `gtab` |
| `'aaaa'` | `'aa'` | 2 | Subset |
| `'abcba'` | `'abcbcba'` | 5 | `abcba` |
| `'a'` | `'a'` | 1 | Single |
| `'ab'` | `'ba'` | 1 | Crossed |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **2D DP** | **O(n*m)** | **O(n*m)** | **✅ BEST** |
| 1D DP | O(n*m) | O(min(n,m)) | ✅ Space-optimized |
| Memoization | O(n*m) | O(n*m) | ✅ Top-down |
| Brute | O(2^(n+m)) | O(n+m) | ❌ Too slow |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Edit Distance (LC 72) | 2D DP 3-way | https://leetcode.com/problems/edit-distance/ |
| Distinct Subseq (LC 115) | 2D DP | https://leetcode.com/problems/distinct-subsequences/ |
| Longest Common Substring | 2D DP reset | https://leetcode.com/problems/longest-common-substring/ |
| Shortest Common Superseq | 2D DP | https://leetcode.com/problems/shortest-common-supersequence/ |
| LPS (LC 516) | LCS trick | https://leetcode.com/problems/longest-palindromic-subsequence/ |
| LCS (LC 1143) | **This problem** | https://leetcode.com/problems/longest-common-subsequence/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **2D DP** is optimal: O(n*m) time.
2. **Match extends diagonal**, mismatch takes max.
3. **Roll array** saves space: O(min(n,m)).
4. **LPS = LCS(s, reverse(s))** — cross-connection.
5. **Unix diff** is canonical use case.
6. **Same skeleton** as Edit Distance.
7. **Subsequence ≠ substring** — different recurrences.
8. **Multiple LCS** may exist; length is unique.
9. **Reconstruction** needs full 2D table.
10. **Empty strings** → 0.

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Unix diff** | File differences |
| **DNA sequencing** | Sequence alignment |
| **Plagiarism** | Document similarity |
| **Version control** | File merge |
| **Spell checking** | Word similarity |
| **Bioinformatics** | Genetic matching |
| **Text mining** | Common patterns |
| **Recommender systems** | Sequential similarity |
| **Music** | Motif matching |
| **Time series** | Pattern alignment |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive the 2D DP in 60 seconds
- [x] Can code the 8-line solution in 60 seconds
- [x] Know complexity: O(n*m) time, O(n*m) space
- [x] Know match → diagonal, mismatch → max
- [x] Know LPS = LCS trick
- [x] Know 1D rolling with prev_diag
- [x] Know related problems (LC 72, 115, 516)
- [x] Know swap for min(n,m) space
- [x] Can list 5 real-world applications

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 10 minutes.
**Lines of code to write:** 8.
**Insight:** "dp[i][j] = LCS of s1[0..i-1], s2[0..j-1]. Match: dp[i-1][j-1]+1. Mismatch: max(skip i, skip j)."
