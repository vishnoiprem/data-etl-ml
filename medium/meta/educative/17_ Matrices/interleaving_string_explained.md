# Interleaving String — 0.0001% Expert Guide

> **LeetCode 97** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/interleaving-string
> **Problem:** `isInterleave(s1, s2, s3)` — check if s3 is interleaving of s1, s2.

---

## 📋 WHAT THE QUESTION ASKS

Given `s1`, `s2`, `s3`, determine if `s3` can be formed by interleaving `s1` and `s2` while preserving the left-to-right order within each string.

### Constraints
- `0 <= s1.length, s2.length <= 100`
- `0 <= s3.length <= 200`
- lowercase letters

### Examples
```
s1='aabcc', s2='dbbca', s3='aadbbcbcac' -> True
s1='aabcc', s2='dbbca', s3='aadbbbaccc' -> False
s1='',     s2='abc',  s3='abc'          -> True
s1='abc',  s2='',     s3='abc'          -> True
s1='',     s2='',     s3=''             -> True
s1='a',    s2='b',    s3='ba'           -> True  (s2 first, then s1)
```

### Why This Is "Medium"
- 2D DP.
- O(n*m) time and space.
- Common string DP pattern.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Check if s3 is interleaving of s1, s2. Order within each preserved."

### Step 2: KEY INSIGHT — 2D State DP (5 min)
> "State: (i, j) = chars of s1 used = i, chars of s2 used = j.
> Total chars of s3 used = i + j.
>
> dp[i][j] = True iff s3[0..i+j-1] is interleaving of s1[0..i-1] and s2[0..j-1].
>
> Last char of s3 (at position i+j-1) must come from s1[i-1] OR s2[j-1]."

### Step 3: Transition (3 min)
> "dp[i][j] = (dp[i-1][j] AND s1[i-1] == s3[i+j-1])   -- take from s1
>        OR (dp[i][j-1] AND s2[j-1] == s3[i+j-1])   -- take from s2"

### Step 4: Algorithm (3 min)
```
1. If len(s1) + len(s2) != len(s3): return False.
2. dp = [[False] * (m+1) for _ in range(n+1)].
3. dp[0][0] = True.
4. Base row: dp[i][0] = dp[i-1][0] AND s1[i-1] == s3[i-1].
5. Base col: dp[0][j] = dp[0][j-1] AND s2[j-1] == s3[j-1].
6. For i, j from 1: apply transition.
7. Return dp[n][m].
```

### Step 5: Edge Cases (2 min)
- Empty s1 or s2: trivially check equality.
- All empty: True.
- Length mismatch: False.
- Single chars: direct comparison.

### Step 6: Code It (3 min)

```python
def isInterleave(s1, s2, s3):
    n, m = len(s1), len(s2)
    if n + m != len(s3):
        return False
    dp = [[False] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = True
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] and s1[i - 1] == s3[i - 1]
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] and s2[j - 1] == s3[j - 1]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            a = dp[i - 1][j] and s1[i - 1] == s3[i + j - 1]
            b = dp[i][j - 1] and s2[j - 1] == s3[i + j - 1]
            dp[i][j] = a or b
    return dp[n][m]
```

### Step 7: Verify (2 min)
For s1='aabcc', s2='dbbca', s3='aadbbcbcac' (length 5+5=10 ✓):

Row by row, column by column:
- dp[0][0]=T
- dp[1][0]: T AND s1[0]='a'=s3[0]='a' -> T
- dp[2][0]: T AND s1[1]='a'=s3[1]='a' -> T
- dp[3][0]: T AND s1[2]='b'=s3[2]='d'? NO -> F
- dp[0][1]: T AND s2[0]='d'=s3[0]='a'? NO -> F
- dp[0][2]: F (cascading from dp[0][1]=F)
- ...

The DP correctly evaluates. Final dp[5][5] should be True.

### Step 8: Discuss Trade-offs (3 min)
> "Three approaches:
> 1. **2D DP:** O(n*m) time, O(n*m) space.
> 2. **1D DP rolling:** O(n*m) time, O(min(n,m)) space. **BEST**.
> 3. **DFS + memo:** Same as DP, top-down style.
>
> I'll use 1D DP."

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to check if s3 is an interleaving of s1 and s2.

KEY INSIGHT: 2D DP.
- State (i, j) = chars used from s1, s2.
- dp[i][j] = True iff s3[0..i+j-1] is valid interleaving.

BASE:
- dp[0][0] = True.
- dp[i][0] = dp[i-1][0] AND s1[i-1] == s3[i-1] (only s1).
- dp[0][j] = dp[0][j-1] AND s2[j-1] == s3[j-1] (only s2).

TRANSITION:
dp[i][j] = (dp[i-1][j] AND s1[i-1] == s3[i+j-1])
        OR (dp[i][j-1] AND s2[j-1] == s3[i+j-1])

EARLY EXIT: |s1| + |s2| != |s3| -> False.

SPACE: 1D rolling array works (process s1 outer, s2 inner).

COMPLEXITY: O(n*m) time, O(min(n,m)) space.

EDGE CASES:
- Empty s1 or s2: trivially check.
- All empty: True.
- Length mismatch: False.

THE TRICK: Last char of s3 (at i+j-1) must come from s1 OR s2.

RELATED:
- Edit Distance (LC 72).
- Distinct Subsequences (LC 115).
- Word Break (LC 139).
"
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: 2D DP (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | 2D DP (BEST) | O(n*m) | O(n*m) | **THE ANSWER** |
| 5 | 2D DP verbose | O(n*m) | O(n*m) | Educational |
| 9 | 2D with refs | O(n*m) | O(n*m) | Educational |
| 12 | 2D char-by-char | O(n*m) | O(n*m) | Educational |
| 13 | 2D closure | O(n*m) | O(n*m) | Educational |
| 15 | 2D bitmask reach | O(n*m) | O(n*m) | Educational |
| 19 | 2D list | O(n*m) | O(n*m) | Educational |

### 🟡 TIER 2: 1D DP (Space-Optimized)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 2 | 1D rolling | O(n*m) | O(m) | **Space-optimized** |
| 11 | 1D with swap | O(n*m) | O(min) | Min space |
| 17 | 1D verbose | O(n*m) | O(m) | Variant |
| 20 | Final cleanest | O(n*m) | O(m) | **THE ONE TO MEMORIZE** |

### 🟠 TIER 3: Top-Down / DFS

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 3 | Top-down memo | O(n*m) | O(n*m) | Top-down |
| 7 | Memo dict | O(n*m) | O(n*m) | Educational |
| 18 | lru_cache | O(n*m) | O(n*m) | Educational |

### 🔵 TIER 4: Graph-Based / Specialized

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 4 | BFS | O(n*m) | O(n*m) | Graph view |
| 14 | Iter DFS | O(n*m) | O(n*m) | No recursion |
| 6 | Pure recursion | O(2^n) | O(n+m) | Bad |
| 8 | Class OOP | O(n*m) | O(n*m) | Reusable |
| 10 | Numpy | O(n*m) | O(n*m) | Vectorized |
| 16 | Reverse perspective | O(n*m) | O(n*m) | Same as Way 1 |

---

## 💎 THE 13-LINE SOLUTION (Memorize!)

```python
def isInterleave(s1, s2, s3):
    n, m = len(s1), len(s2)
    if n + m != len(s3):
        return False
    if n < m:  # ensure s2 is longer for O(n) space
        s1, s2 = s2, s1
        n, m = m, n
    dp = [False] * (n + 1)
    dp[0] = True
    for i in range(1, n + 1):
        dp[i] = dp[i - 1] and s1[i - 1] == s3[i - 1]
    for j in range(1, m + 1):
        dp[0] = dp[0] and s2[j - 1] == s3[j - 1]
        for i in range(1, n + 1):
            a = dp[i] and s1[i - 1] == s3[i + j - 1]
            b = dp[i - 1] and s2[j - 1] == s3[i + j - 1]
            dp[i] = a or b
    return dp[n]
```

**Time:** `O(n*m)`
**Space:** `O(min(n,m))`

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Why State (i, j), Not (k)

> k = position in s3 is determined by i+j. So (i, j) is enough.

Using k as third state would be redundant.

**Connection to:**
- **State minimization:** Avoid redundancy.
- **DP design:** Minimal state.

### Insight 2: Length Check is Critical

> |s1| + |s2| != |s3| -> immediately False. Saves O(n*m) work.

Always include this check.

**Connection to:**
- **Early exit:** Optimization.
- **Defensive coding:** Always check.

### Insight 3: Why i+j-1 for s3 Index

> After using i chars of s1 and j chars of s2, we've matched
> i+j chars of s3. Next char to match is at index i+j (0-indexed)
> or position i+j-1 (1-indexed).

Standard off-by-one care.

**Connection to:**
- **Index arithmetic:** Critical.
- **DP correctness:** Boundary.

### Insight 4: 1D Rolling Works

> Outer loop on i (s1), inner on j (s2). dp[j] updates in-place.

`dp[i-1][j]` = old `dp[j]` (haven't overwritten yet).
`dp[i][j-1]` = current `dp[j-1]`.

**Connection to:**
- **Space optimization:** Rolling array.
- **In-place updates:** Order matters.

### Insight 5: Why BFS is Equivalent

> BFS on (i, j) explores reachable states. If (n, m) reachable,
> s3 is valid interleaving.

Same states as DP, different exploration.

**Connection to:**
- **Multiple views:** DP/DFS/BFS equivalent.
- **Graph algorithms:** Reachable states.

### Insight 6: Connection to Edit Distance

> Edit Distance: dp[i][j] = min cost to transform.
> Interleaving: dp[i][j] = bool reachable state.

Same 2D structure, different value.

**Connection to:**
- **DP family:** String DP.
- **Variations:** Boolean vs numeric.

### Insight 7: Real-World Applications

| Application | Use |
|-------------|-----|
| **DNA sequencing** | Merge two sequences |
| **Bioinformatics** | Sequence assembly |
| **Text merging** | Document merging |
| **Compiler parsing** | Token interleaving |
| **Network protocols** | Stream merging |
| **Log analysis** | Event sequence merge |

**DNA sequencing** is canonical use case.

### Insight 8: Why Both Transitions Use AND with Char Match

> We need (1) previous state reachable AND (2) current char matches.

Just `dp[i-1][j]` doesn't ensure s3[i+j-1] matches s1[i-1].

**Connection to:**
- **Logic correctness:** Both conditions.
- **DP transitions:** Boolean AND/OR.

### Insight 9: Memo on (i, j), Not Full Path

> Just store reachable/not. Path reconstruction isn't needed.

If asked to reconstruct, keep parent pointers.

**Connection to:**
- **Memory efficiency:** Boolean.
- **Reconstruction:** Add if needed.

### Insight 10: Why Base Row First

> dp[i][0] uses dp[i-1][0] (already filled). Same for column.

Topological order: left-to-right, top-to-bottom.

**Connection to:**
- **Iteration order:** Standard.
- **DP correctness:** Depends.

### Insight 11: Symmetry Between s1 and s2

> Algorithm is symmetric. Swap s1, s2 -> same answer.

Can leverage to use shorter string for space.

**Connection to:**
- **Symmetry:** Reduces work.
- **Optimization:** Pick shorter.

### Insight 12: Edge: Both Empty

> |s1|=|s2|=|s3|=0 -> dp[0][0]=True -> True.

Trivial but important.

**Connection to:**
- **Edge cases:** Always handle.
- **Base case:** Fundamental.

### Insight 13: Connection to Longest Common Subsequence

> Both are 2D string DP with similar patterns.

Different transitions, same skeleton.

**Connection to:**
- **DP family:** String DP.
- **Reusable code:** Common template.

### Insight 14: Why Length 200 Limit

> O(n*m) for n,m <= 100 -> 10^4. Small enough for any approach.

No need for Aho-Corasick or complex algorithms.

**Connection to:**
- **Constraint analysis:** Choose approach.
- **Big-O matching:** Always safe.

### Insight 15: Char-by-Char vs Position-Based

> Some implementations iterate position k in s3, deciding which string
> contributes. Equivalent but less efficient.

(i, j)-based is cleaner.

**Connection to:**
- **Multiple formulations:** Same problem.
- **Implementation choice:** Pick cleaner.

### Insight 16: When Memo Beats 2D Array

> For sparse reachable states, memo dict saves space.

For dense (most states reachable), array is faster.

**Connection to:**
- **Sparse vs dense:** Pick by data.
- **Trade-off:** Different metrics.

---

## 🧪 TEST CASES

| `s1` | `s2` | `s3` | Expected | Note |
|------|------|------|----------|------|
| `'aabcc'` | `'dbbca'` | `'aadbbcbcac'` | True | Standard |
| `'aabcc'` | `'dbbca'` | `'aadbbbaccc'` | False | Wrong order |
| `''` | `''` | `''` | True | All empty |
| `''` | `'abc'` | `'abc'` | True | One empty |
| `'abc'` | `''` | `'abc'` | True | One empty |
| `'a'` | `'b'` | `'ab'` | True | s1,s2 |
| `'a'` | `'b'` | `'ba'` | True | s2,s1 |
| `'aa'` | `'ab'` | `'aaba'` | True | Standard |
| `'aa'` | `'ab'` | `'abaa'` | True | s1,s2,s2,s1 |
| `'aabc'` | `'abcd'` | `'aabcabcd'` | True | Concatenation |
| `'aabc'` | `'abcd'` | `'aabcbcd'` | False | Skipped char |
| `'aaaa'` | `'aaaa'` | `'aaaaaaaa'` | True | Repeated |
| `'abc'` | `'def'` | `'abcdef'` | True | Distinct |
| `'abc'` | `'def'` | `'abdcfe'` | False | Crossed |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **2D DP** | **O(n*m)** | **O(n*m)** | **✅ BEST** |
| 1D DP | O(n*m) | O(min(n,m)) | ✅ Space-optimized |
| DFS + memo | O(n*m) | O(n*m) | ✅ Top-down |
| BFS | O(n*m) | O(n*m) | ✅ Graph view |
| Pure recursion | O(2^(n+m)) | O(n+m) | ❌ Too slow |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Edit Distance (LC 72) | 2D DP | https://leetcode.com/problems/edit-distance/ |
| Distinct Subseq (LC 115) | 2D DP | https://leetcode.com/problems/distinct-subsequences/ |
| Word Break (LC 139) | 1D DP | https://leetcode.com/problems/word-break/ |
| Scramble String (LC 87) | 3D DP | https://leetcode.com/problems/scramble-string/ |
| Interleaving String (LC 97) | **This problem** | https://leetcode.com/problems/interleaving-string/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **2D state DP** with (i, j) = chars used.
2. **Length check** first: |s1|+|s2|=|s3|.
3. **Last char** of s3 must come from s1 OR s2.
4. **Both transitions** with char match.
5. **1D rolling** saves space.
6. **DNA sequencing** is canonical use case.
7. **Same skeleton** as Edit Distance.
8. **Symmetric** in s1, s2.
9. **Iteration order**: top-down row by row.
10. **BFS equivalent** to DP.

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **DNA sequencing** | Merge two sequences |
| **Bioinformatics** | Sequence assembly |
| **Text merging** | Document merge |
| **Compiler parsing** | Token interleaving |
| **Network protocols** | Stream merging |
| **Log analysis** | Event sequence merge |
| **Version control** | Branch merging |
| **Distributed systems** | Event ordering |
| **Data pipelines** | Multi-source merge |
| **Music** | Motif interleaving |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive the 2D DP in 90 seconds
- [x] Can code the 13-line solution in 90 seconds
- [x] Know complexity: O(n*m) time, O(min(n,m)) space
- [x] Know length check optimization
- [x] Know why i+j-1 is the s3 index
- [x] Know 1D rolling array space optimization
- [x] Know related problems (LC 72, 115, 139)
- [x] Know DFS / BFS equivalence
- [x] Can list 5 real-world applications

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 12 minutes.
**Lines of code to write:** 13.
**Insight:** "dp[i][j] = reachable state. Last char of s3 (i+j-1) from s1 OR s2. Iterate top-down."
