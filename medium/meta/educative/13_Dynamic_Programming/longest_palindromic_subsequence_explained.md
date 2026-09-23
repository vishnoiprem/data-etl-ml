# Longest Palindromic Subsequence — 0.0001% Expert Guide

> **LeetCode 516** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/longest-palindromic-subsequence
> **Problem:** `longestPalindromeSubseq(s)` — length of longest palindromic subsequence.

---

## 📋 WHAT THE QUESTION ASKS

Given a string `s`, return the length of the longest subsequence that is a palindrome.

A subsequence is formed by deleting zero or more characters without changing order.

### Constraints
- `1 <= s.length <= 1000`
- `s` consists of lowercase English letters.

### Examples
```
s="bbbab"           -> 4  (the whole string "bbbb")
s="cbbd"            -> 2  ("bb")
s="abcba"           -> 5  (whole string)
s="racecar"         -> 7  (whole string)
s="abcdefgfedcba"   -> 13 (whole string)
s="a"               -> 1
s=""                -> 0
```

### Why This Is "Medium"
- 2D interval DP.
- O(n²) time and space.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Find the longest subsequence that's also a palindrome."

### Step 2: KEY INSIGHT — Interval DP (5 min)
> "dp[i][j] = length of longest palindromic subsequence in s[i..j].
> - Base: dp[i][i] = 1.
> - Transition:
>   - If s[i] == s[j]: dp[i][j] = dp[i+1][j-1] + 2.
>   - Else: dp[i][j] = max(dp[i+1][j], dp[i][j-1]).
>
> Iterate by INCREASING SUBSTRING LENGTH so dp[i+1][j-1] is ready."

### Step 3: Why This Transition Works (3 min)
> "If s[i] == s[j]: these are outer chars of a palindrome. Extend
> inner LPS by 2.
> Else: we drop either s[i] or s[j], take the longer."

### Step 4: Algorithm (3 min)
```
1. Initialize dp[i][i] = 1 for all i.
2. For length from 2 to n:
     For each i, j = i + length - 1:
       If s[i] == s[j]: dp[i][j] = (dp[i+1][j-1] + 2) if length > 2 else 2.
       Else: dp[i][j] = max(dp[i+1][j], dp[i][j-1]).
3. Return dp[0][n-1].
```

### Step 5: Edge Cases (2 min)
- Empty string: 0.
- Single char: 1.
- All same: n.
- No matching pairs (e.g., "abc"): 1.

### Step 6: Code It (3 min)

```python
def longest_palindromic_subseq(s):
    n = len(s)
    if n == 0:
        return 0
    dp = [[0] * n for _ in range(n)]
    for i in range(n):
        dp[i][i] = 1
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                dp[i][j] = 2 if length == 2 else dp[i + 1][j - 1] + 2
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])
    return dp[0][n - 1]
```

### Step 7: Verify (2 min)
For "bbbab":
- dp[4][4] = 1.
- length=2: dp[0][1] (b,b match) = 2, dp[1][2] (b,b) = 2, dp[2][3] (b,a) = 1, dp[3][4] (a,b) = 1.
- length=3: dp[0][2] (b,b,b) = max(dp[1][2], dp[0][1])+2? No, b==b, dp[0][2] = dp[1][1] + 2 = 3. dp[1][3] (b,b,a) = max(dp[2][3], dp[1][2]) = max(1, 2) = 2. dp[2][4] (b,a,b) = b==b, dp[3][3]+2 = 1+2 = 3.
- length=4: dp[0][3] (b,b,b,a) = max(dp[1][3], dp[0][2]) = max(2, 3) = 3. dp[1][4] (b,b,a,b) = max(dp[2][4], dp[1][3]) = max(3, 2) = 3.
- length=5: dp[0][4] = max(dp[1][4], dp[0][3]) = max(3, 3) = 3.
Wait, expected = 4.

Let me re-check. "bbbab": the LPS is "bbbb" of length 4 (drop the 'a').

Let me retrace:
- length=2:
  - dp[0][1] = "bb". s[0]='b', s[1]='b', match. length=2 so dp[0][1] = 2.
  - dp[1][2] = "bb". 2.
  - dp[2][3] = "ba". No match. max(dp[3][3], dp[2][2]) = max(1,1) = 1.
  - dp[3][4] = "ab". No match. max(dp[4][4], dp[3][3]) = 1.
- length=3:
  - dp[0][2] = "bbb". s[0]='b'=s[2]='b'. dp[0][2] = dp[1][1] + 2 = 1+2 = 3.
  - dp[1][3] = "bba". s[1]='b' != s[3]='a'. max(dp[2][3], dp[1][2]) = max(1, 2) = 2.
  - dp[2][4] = "bab". s[2]='b' != s[4]='b' wait s[4]='b' so match. dp[2][4] = dp[3][3]+2 = 1+2 = 3.
- length=4:
  - dp[0][3] = "bbba". s[0]='b' != s[3]='a'. max(dp[1][3], dp[0][2]) = max(2, 3) = 3.
  - dp[1][4] = "bbab". s[1]='b' != s[4]='b'. Wait! s[1]='b', s[4]='b'. Match. dp[1][4] = dp[2][3] + 2 = 1+2 = 3. Hmm but my expected is 4.
- length=5:
  - dp[0][4] = "bbbab". s[0]='b' != s[4]='b'. Wait s[4]='b'. So s[0]==s[4]. Match. dp[0][4] = dp[1][3]+2 = 2+2 = 4. ✓

OK so my expected = 4 is correct. The LPS of "bbbab" is "bbbb" of length 4.

### Step 8: Discuss Trade-offs (3 min)
> "Three approaches:
> 1. **2D DP:** O(n²). Best.
> 2. **1D DP (rolling):** O(n²) time, O(n) space.
> 3. **LCS view:** LPS(s) = LCS(s, reverse(s)). Use LCS code.
>
> I'll use 2D DP."

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to find the longest subsequence of s that's a palindrome.

KEY INSIGHT: 2D interval DP.
- dp[i][j] = LPS length in s[i..j].
- Base: dp[i][i] = 1.
- Transition:
  - If s[i] == s[j]: dp[i][j] = dp[i+1][j-1] + 2.
  - Else: dp[i][j] = max(dp[i+1][j], dp[i][j-1]).

ALGORITHM:
1. Initialize dp[i][i] = 1.
2. For length from 2 to n:
     For i, j = i+length-1:
       If s[i] == s[j]: dp[i][j] = (dp[i+1][j-1] + 2)
       Else: dp[i][j] = max(dp[i+1][j], dp[i][j-1])
3. Return dp[0][n-1].

COMPLEXITY: O(n²) time, O(n²) space.

EDGE CASES:
- Empty: 0.
- Single char: 1.
- All same: n.

THE TRICK: Iterate by SUBSTRING LENGTH so dp[i+1][j-1] is ready.

ALTERNATE: LPS(s) = LCS(s, reverse(s)). Same problem, different framing.
"
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: 2D DP (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | 2D DP by length (BEST) | O(n²) | O(n²) | **THE ANSWER** |
| 5 | Diagonal traversal | O(n²) | O(n²) | Educational |
| 8 | Class OOP | O(n²) | O(n²) | Reusable |
| 9 | 2D DP explicit | O(n²) | O(n²) | Educational |
| 13 | Gap-based | O(n²) | O(n²) | Educational |
| 14 | Reverse iter | O(n²) | O(n²) | Educational |
| 16 | 2D backward | O(n²) | O(n²) | Educational |
| 19 | Reversed length | O(n²) | O(n²) | Educational |
| 20 | Final cleanest | O(n²) | O(n²) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: 1D DP / LCS View (Space-Optimized)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 2 | LCS view (full 2D) | O(n²) | O(n²) | Reuse LCS code |
| 6 | 1D DP rolling | O(n²) | O(n) | **Space-optimized** |
| 11 | LCS 2-row | O(n²) | O(n) | Space-optimized |
| 17 | 1D prev tracking | O(n²) | O(n) | Variant |

### 🟠 TIER 3: Memoization / DFS

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 3 | Top-down memo | O(n²) | O(n²) | Top-down |
| 7 | Memo dict | O(n²) | O(n²) | Educational |
| 10 | Pure recursion | O(2^n) | O(n) | Bad |
| 15 | Memo closure | O(n²) | O(n²) | Educational |
| 18 | lru_cache | O(n²) | O(n²) | Educational |

### 🔵 TIER 4: Specialized

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 4 | Brute combinations | O(2^n) | O(n) | Tiny n |
| 12 | Numpy | O(n²) | O(n²) | Vectorized |

---

## 💎 THE 13-LINE SOLUTION (Memorize!)

```python
def longest_palindromic_subseq(s):
    n = len(s)
    if n == 0:
        return 0
    dp = [[0] * n for _ in range(n)]
    for i in range(n):
        dp[i][i] = 1
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j]:
                dp[i][j] = 2 if length == 2 else dp[i + 1][j - 1] + 2
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1])
    return dp[0][n - 1]
```

**Time:** `O(n²)`
**Space:** `O(n²)`

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Iteration Order is Critical

> Interval DP must iterate by SUBSTRING LENGTH so dependencies are ready.

Forgetting this gives wrong (often correct-looking) results.

**Connection to:**
- **DP iteration order:** Make sure dependencies are met.
- **Common mistakes:** #1 DP bug.

### Insight 2: LPS = LCS Trick

> LPS(s) = LCS(s, reverse(s)).

Subsequence that's a palindrome = common subsequence between s and its reverse.

**Connection to:**
- **Problem reduction:** Cross-problem.
- **Code reuse:** Same LCS code.

### Insight 3: Why Length-Loop Works

> dp[i+1][j-1] depends on a SHORTER substring (i+1 to j-1 is length 2 less).

If we iterate length=2, 3, ..., n, the shorter lengths are processed first.

**Connection to:**
- **Bottom-up correctness:** Iterative refinement.
- **Order of evaluation:** Length-based.

### Insight 4: 1D Rolling Array Works

> When iterating from right-to-left on i, dp[j-1] still has the OLD value.

That's dp[i+1][j-1] from the previous i iteration.

**Connection to:**
- **Space optimization:** 1D for 2D DP.
- **Tricky details:** Variable naming.

### Insight 5: Connection to Longest Common Subsequence

> LPS is a special case of LCS with the reverse string.

Same DP structure, different inputs.

**Connection to:**
- **Problem family:** LCS variants.
- **Code reuse:** Common template.

### Insight 6: Why s[i] != s[j] Drops One

> If outer chars don't match, at least one of them isn't in the palindrome.

Either s[i] is dropped (dp[i+1][j]) or s[j] is dropped (dp[i][j-1]).

**Connection to:**
- **Subproblem decomposition:** Drop one.
- **Recurrence derivation:** Standard pattern.

### Insight 7: Length = 2 Special Case

> When length = 2 and s[i] == s[j], dp[i][j] = 2 (no inner substring).

This avoids indexing dp[i+1][j-1] when j = i+1.

**Connection to:**
- **Edge cases:** Always handle.
- **Index arithmetic:** Boundary.

### Insight 8: Real-World Applications

| Application | Use |
|-------------|-----|
| **DNA sequencing** | Palindromic subsequences |
| **Text similarity** | Common + palindromic |
| **Bioinformatics** | Genetic palindromes |
| **Pattern matching** | Symmetric patterns |
| **Cryptography** | Palindromic keys |
| **Data compression** | Self-similar blocks |

**DNA palindromic subsequences** are canonical in bioinformatics.

### Insight 9: When 2D Beats 1D

> For DPS / reconstruct, 2D needed (need dp[i+1][j-1] later).

For just the answer, 1D suffices.

**Connection to:**
- **Memory vs clarity:** Trade-off.
- **Application needs:** Reconstruction?

### Insight 10: Connection to Min Insertions

> Min insertions to make string palindrome = n - LPS(s).

Same DP, different interpretation.

**Connection to:**
- **Dual problems:** Max-min duality.
- **Reformulations:** Common.

### Insight 11: Why Empty is 0, Single is 1

> Base cases match the recursive definition.

Empty has no subsequence. Single char has itself.

**Connection to:**
- **Base cases:** Always check.
- **Mathematical rigor:** Definitions match.

### Insight 12: Connection to Edit Distance

> Same 2D interval structure.

Edit distance, LPS, LCS — all use interval DP.

**Connection to:**
- **DP family:** Interval DP.
- **Shared skeleton:** Reusable code.

### Insight 13: When to Use Recursive vs Iterative

> Iterative: cleaner, no stack. Recursive: more natural for some.

Both O(n²). Pick by preference.

**Connection to:**
- **Style choice:** No correctness difference.
- **Readability:** Match audience.

### Insight 14: Why Not Bottom-Up from i, j

> Bottom-up by (i, j) doesn't naturally order by length.

Length-based iteration is cleaner.

**Connection to:**
- **Iteration order:** Critical for DP.
- **Code clarity:** Standard convention.

---

## 🧪 TEST CASES

| `s` | Expected | Note |
|-----|----------|------|
| `"bbbab"` | 4 | LPS = "bbbb" |
| `"cbbd"` | 2 | "bb" |
| `"abcba"` | 5 | Whole |
| `"a"` | 1 | Single |
| `""` | 0 | Empty |
| `"abcde"` | 1 | Any single char |
| `"aaaa"` | 4 | All same |
| `"racecar"` | 7 | Whole |
| `"abcdefgfedcba"` | 13 | Whole |
| `"ab"` | 1 | Either |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **2D DP** | **O(n²)** | **O(n²)** | **✅ BEST** |
| 1D DP | O(n²) | O(n) | ✅ Space-optimized |
| LCS view | O(n²) | O(n²) | ✅ Reuse code |
| Brute | O(2^n) | O(n) | ❌ Too slow |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Longest Common Subseq (LC 1143) | 2D DP | https://leetcode.com/problems/longest-common-subsequence/ |
| Min Insertions Palindrome | LPS variant | https://leetcode.com/problems/minimum-insertion-steps-to-make-a-string-palindrome/ |
| Longest Palindromic Substring | Manacher | https://leetcode.com/problems/longest-palindromic-substring/ |
| Count Different Palindromic Subseq (LC 730) | Interval DP | https://leetcode.com/problems/count-different-palindromic-subsequences/ |
| Longest Palindromic Subseq (LC 516) | **This problem** | https://leetcode.com/problems/longest-palindromic-subsequence/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **Iterate by length** so dp[i+1][j-1] is ready.
2. **LPS = LCS(s, reverse(s))** — alternate view.
3. **2D DP, O(n²) time and space**.
4. **Length = 2 special case** for s[i]==s[j].
5. **DNA palindromes** are canonical use case.
6. **Same skeleton as Edit Distance, LCS**.
7. **1D variant** saves space.
8. **Min insertions = n - LPS**.
9. **Edge cases: empty=0, single=1**.
10. **For both directions** of iteration (i, j).

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **DNA sequencing** | Palindromic subsequences |
| **Text similarity** | Common + palindromic |
| **Bioinformatics** | Genetic palindromes |
| **Pattern matching** | Symmetric patterns |
| **Cryptography** | Palindromic keys |
| **Data compression** | Self-similar blocks |
| **Music** | Palindromic motifs |
| **Genomics** | Self-complementary |
| **String algorithms** | Symmetric subsequence |
| **Sequence analysis** | Palindromic patterns |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive the 2D DP in 90 seconds
- [x] Can code the 13-line solution in 90 seconds
- [x] Know complexity: O(n²) time, O(n²) space
- [x] Know why iterate by length
- [x] Know length=2 special case
- [x] Know LCS view alternate
- [x] Know 1D rolling variant
- [x] Know related problems (LC 1143, 730)
- [x] Can list 5 real-world applications

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 12 minutes.
**Lines of code to write:** 13.
**Insight:** "dp[i][j] = LPS length in s[i..j]. If s[i]==s[j]: dp[i+1][j-1]+2. Else: max(dp[i+1][j], dp[i][j-1]). Iterate by length."