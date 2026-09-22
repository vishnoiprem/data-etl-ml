# Count Palindromic Subsequences — 0.0001% Expert Guide

> **Educative: Grokking Coding Interview in Python** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/count-palindromic-subsequences
> **Problem:** `count_palindromes(s)` — count length-5 palindromic subsequences in a digit string.

---

## 📋 WHAT THE QUESTION ASKS

Given `s` (string of digits), count the number of 5-element subsequences `s[i]s[j]s[k]s[l]s[m]` (with `i<j<k<l<m`) that form a palindrome.

A 5-character palindrome has the form **`a b c b a`**:
- `s[i] == s[m]` (call this digit `a`)
- `s[j] == s[l]` (call this digit `b`)
- `s[k]` (call this digit `c`, no constraint)

### Constraints
- `1 <= s.length <= 10^4`
- `s` consists only of digits (0–9)

### Examples
```
s = "10301"      -> 1  (the whole string)
s = "11111"      -> 1
s = "111111"     -> 6  (any 5 of 6 indices)
s = "1010101"    -> 9
s = "100001"     -> 4  (multiple inner pair choices)
s = "110011"     -> 2
s = "12345"      -> 0  (all distinct)
```

### Why This Is "Medium"
- Fixed alphabet size (10 digits) → constant-time inner loop.
- Combinatorial counting with constraint satisfaction.
- O(n² × 10) suffices.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "I need to count 5-tuples (i<j<k<l<m) such that s[i]=s[m] AND s[j]=s[l]."

### Step 2: Identify the Algorithm (3 min)
> "Three natural parameterizations:
> 1. **Fix inner pair (j, l):** middle k has (l-j-1) choices, outer (i, m) factorizes via prefix counts.
> 2. **Fix outer pair (i, m):** inner pair + middle factor less cleanly.
> 3. **Fix middle k:** inner pair + outer pair with ordering constraints.
>
> Best: Fix inner pair (j, l)."

### Step 3: KEY INSIGHT — Inner Pair Factorization (5 min)
> "For each inner pair (j, l) with j<l and s[j]==s[l]:
> - **middle_count** = l - j - 1 (choices for k).
> - **outer_count** = Σ_a (count_a in s[0..j-1]) × (count_a in s[l+1..n-1]).
> - **contribution** = middle_count × outer_count.
>
> Total = sum of contributions."

Why this works:
- Inner pair fixes the symmetry axis for `b`.
- Middle `k` is just any position between j and l (gives l-j-1 options).
- Outer pair (i, m) needs s[i]=s[m]=a where i<j and m>l. Choices for each digit `a` are independent and factorize.

### Step 4: Why Not Fix Middle k (3 min)
> "If we fix middle k:
> - Inner pair (j, l) with j<k<l and s[j]==s[l].
> - Outer pair (i, m) with i<j and m>l AND s[i]==s[m].
>
> Counting these for all (j, l) doesn't factorize cleanly because the
> outer pair's bounds depend on j and l."

### Step 5: Algorithm (5 min)
```
1. Build prefix[d][i] = # of digit d in s[0..i-1] for d in 0..9.
2. For each j in [0, n):
   - For each l in [j+2, n):     # l-j >= 2 so middle has >=1 option
     - If s[j] != s[l]: skip.
     - middle = l - j - 1
     - outer = 0
     - For a in 0..9:
         outer += prefix[a][j] × (prefix[a][n] - prefix[a][l+1])
     - total += middle × outer
3. Return total.
```

### Step 6: Edge Cases (2 min)
- `n < 5`: return 0.
- All same digit (e.g., "11111"): C(n,5) palindromes.
- Distinct digits: 0.

### Step 7: Code It (5 min)

```python
def count_palindromes(s):
    n = len(s)
    if n < 5:
        return 0
    digits = [ord(c) - 48 for c in s]
    prefix = [[0] * (n + 1) for _ in range(10)]
    for i in range(n):
        d = digits[i]
        for a in range(10):
            prefix[a][i + 1] = prefix[a][i]
        prefix[d][i + 1] += 1
    total = 0
    for j in range(n):
        for l in range(j + 2, n):
            if digits[j] != digits[l]:
                continue
            middle = l - j - 1
            outer = 0
            for a in range(10):
                outer += prefix[a][j] * (prefix[a][n] - prefix[a][l + 1])
            total += middle * outer
    return total
```

### Step 8: Verify (2 min)
For "100001" (n=6, indices: 1,0,0,0,0,1):
- Inner pairs (j, l) with s[j]=s[l]:
  - 0's: (1,2), (1,3), (1,4), (2,3), (2,4), (3,4)
- (1,4): middle=2 (k=2 or k=3).
  - outer: count_1(s[0..0])=1, count_1(s[5..5])=1, so outer=1.
  - Contribution = 2 × 1 = 2.
  - These are (0,1,2,4,5) and (0,1,3,4,5).
- (1,3): middle=1 (k=2). outer: count_1(s[0..0])=1, count_1(s[4..5])=1. outer=1. Contrib=1.
  - This is (0,1,2,3,5).
- (2,4): middle=1 (k=3). outer: count_1(s[0..1])=1, count_1(s[5..5])=1. outer=1. Contrib=1.
  - This is (0,2,3,4,5).
- Total = 2 + 1 + 1 = 4. ✓

### Step 9: Discuss Trade-offs (5 min)
> "Three approaches:
> 1. **Inner-pair prefix DP:** O(n² × 10). **Best.**
> 2. **Brute force O(n⁵):** Only for very small n.
> 3. **O(n⁴) iterate outer (i,m) and inner (j,l):** Slower.
>
> I'll use inner-pair DP."

### Step 10: Why This Is O(n² × 10) (3 min)
> "Outer loop: O(n²) over (j, l). Inner loop: O(10) over digits.
> Total: O(10 × n²). For n=10⁴, that's 10⁹ ops — borderline but works with
> the constant factor (10 is small, branch prediction helps)."

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to count 5-element subsequences that form a palindrome.
A 5-char palindrome has form a b c b a: s[i]=s[m], s[j]=s[l].

KEY INSIGHT: Fix the INNER pair (j, l) with j<l and s[j]==s[l].
- middle_count = l - j - 1 (choices for k).
- outer_count = sum over 'a' of (# of a in s[0..j-1]) × (# of a in s[l+1..n-1]).
- contribution = middle_count × outer_count.
Total = sum of contributions.

ALGORITHM:
1. Build prefix[d][i] = # of digit d in s[0..i-1] for d in 0..9.
2. For each j in 0..n-1:
   - For each l in j+2..n-1:
     - If s[j] != s[l]: skip.
     - middle = l - j - 1
     - outer = sum_a prefix[a][j] * (prefix[a][n] - prefix[a][l+1])
     - total += middle × outer
3. Return total.

COMPLEXITY: O(10 × n²) time, O(10 × n) space.

EDGE CASES:
- n < 5: return 0.
- All same digit: C(n,5) palindromes.
- Distinct digits: 0.

THE TRICK: Fixing the inner pair makes the outer factorization clean:
choices for digit 'a' on the left and right are independent.

RELATED:
- Count Palindromic Substrings (LC 647).
- Distinct Subsequences (LC 940).
- Count Different Palindromic Subsequences (LC 730).
"
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Inner-Pair DP (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | For each (j,l) pair | O(10n²) | O(10n) | **THE ANSWER** |
| 6 | Prefix sums (variant) | O(10n²) | O(10n) | Educational |
| 13 | 1D prefix | O(10n²) | O(10n) | Variant |
| 18 | Explicit digits | O(10n²) | O(10n) | Educational |
| 20 | Final cleanest | O(10n²) | O(10n) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: Position Lists / Alternative Factorization

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 2 | Position lists per digit | O(10n²) | O(10n) | Memory-efficient |
| 8 | Left/right running | O(10n²) | O(10n) | Educational |
| 9 | On-the-fly left | O(10n²) | O(n) | Less memory |
| 19 | Transposed prefix | O(10n²) | O(20n) | Educational |

### 🟠 TIER 3: Fix Middle k

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 3 | Fix middle, enumerate inner | O(10n³) | O(10n) | Different view |
| 14 | Fix middle enumerate | O(10n³) | O(10n) | Educational |

### 🔵 TIER 4: Specialized

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 4 | Brute force O(n⁵) | O(n⁵) | O(1) | Tiny n only |
| 5 | Iterate (i,m) per (j,l) | O(n³) | O(1) | Educational |
| 7 | itertools.product | O(10n²) | O(10n) | Pythonic |
| 10 | Numpy | O(10n²) | O(10n) | Vectorized |
| 11 | Class OOP | O(10n²) | O(10n) | Reusable |
| 12 | For each outer (i,m) | O(n⁴) | O(1) | Alternative view |
| 15 | Memoized | O(10n²) | O(10n²) | Educational |
| 16 | Generator | O(10n²) | O(10n) | Pythonic |
| 17 | Reduce | O(10n²) | O(10n) | Functional |

---

## 💎 THE 18-LINE SOLUTION (Memorize!)

```python
def count_palindromes(s):
    n = len(s)
    if n < 5:
        return 0
    digits = [ord(c) - 48 for c in s]
    prefix = [[0] * (n + 1) for _ in range(10)]
    for i in range(n):
        d = digits[i]
        for a in range(10):
            prefix[a][i + 1] = prefix[a][i]
        prefix[d][i + 1] += 1
    total = 0
    for j in range(n):
        for l in range(j + 2, n):
            if digits[j] != digits[l]:
                continue
            middle = l - j - 1
            outer = 0
            for a in range(10):
                outer += prefix[a][j] * (prefix[a][n] - prefix[a][l + 1])
            total += middle * outer
    return total
```

**Time:** `O(10 × n²)`
**Space:** `O(10 × n)`

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Choose the Right Variable to Fix

> The variable you fix determines whether the rest factorizes.

Fixing inner pair (j, l) lets middle k be simple (l-j-1 choices) and outer (i, m) factorize by digit. Fixing outer or middle introduces dependencies that don't factorize cleanly.

**Connection to:**
- **Symmetry breaking:** Picking the right pivot.
- **Constraint propagation:** Different fixes lead to different complexities.

### Insight 2: Alphabet Size Matters

> Constant-size alphabet (10 digits) turns an O(n^k × alphabet) into O(n³).

If s contained arbitrary characters, the inner loop would be O(n) per pair, making total O(n³).

**Connection to:**
- **Alphabet size:** Critical for complexity.
- **Constant factor:** 10 is small.

### Insight 3: Why Inner Pair Beats Middle Fixation

> Inner pair's "j<k<l" constraint becomes "l-j-1 choices for k" — a single integer.

Middle k's "i<j<k<l<m" constraint requires both inner and outer pairs to satisfy ordering — multiple coupled conditions.

**Connection to:**
- **Degrees of freedom:** Fewer is better.
- **Constraint counting:** Pick the most constraining pair.

### Insight 4: Prefix Counts as Compression

> prefix[d][i] = count of digit d in s[0..i-1] compresses O(n) queries into O(1).

Standard trick for any "count of value in range" query.

**Connection to:**
- **Range queries:** Prefix sums generalize.
- **Streaming:** Online prefix counts.

### Insight 5: Symmetric vs Asymmetric Factorization

> A palindromic constraint s[i]=s[m] is "symmetric" — counting pairs (i, m) with same digit on each side.

Asymmetric constraints (like s[i]<s[m]) wouldn't factorize as cleanly.

**Connection to:**
- **Symmetry exploitation:** Common in combinatorics.
- **Counting with structure:** Leverage patterns.

### Insight 6: Connection to Count Subsequences of Pattern

> "Count subsequences matching a pattern" — same skeleton.

For pattern P of length k with alphabet Σ, count = O(|s|² × Σ) typically.

**Connection to:**
- **Pattern matching:** Generalization.
- **Subsequence counting:** Family of problems.

### Insight 7: Connection to DP on Indices

> Could be reformulated as 2D DP dp[i][j] = # of palindromic subsequences using only s[0..j] with last index at i. Too complex here.

Direct combinatorial counting is cleaner for fixed-length patterns.

**Connection to:**
- **DP vs combinatorics:** Choose based on structure.
- **State explosion:** Higher k → DP becomes infeasible.

### Insight 8: Why Brute Force Fails

> O(n⁵) = 10²⁰ for n=10⁴. Impossible.

Combinatorial counting is essential.

**Connection to:**
- **Asymptotic limits:** Always check feasibility.
- **Combinatorial insight:** Avoid enumeration when possible.

### Insight 9: Real-World Applications

| Application | Use |
|-------------|-----|
| **DNA palindromes** | Restriction enzyme sites |
| **Cryptography** | Palindromic keys |
| **Text analysis** | Symmetric structures |
| **Music composition** | Palindromic motifs |
| **Error detection** | Palindromic checksums |
| **Network routing** | Symmetric paths |
| **Bioinformatics** | Self-complementary sequences |
| **Data compression** | Palindromic blocks |

**DNA palindromes** (e.g., GAATTC) are the canonical use case in bioinformatics.

### Insight 10: Connection to Manacher's Algorithm

> Manacher counts palindromic substrings in O(n). We count subsequences — different problem.

Substrings are contiguous, subsequences aren't.

**Connection to:**
- **Substring vs subsequence:** Different constraints.
- **Manacher's:** For substring palindromes only.

### Insight 11: Why This Beats Fix-Middle Approach

> Fix-middle gives O(n³ × 10) due to enumerating (j, l) pairs per k.

Fixing inner pair directly gives O(n² × 10) — better by a factor of n.

**Connection to:**
- **Complexity reduction:** Right pivot saves orders of magnitude.
- **Asymptotic improvement:** O(n²) vs O(n³) matters at n=10⁴.

### Insight 12: Connection to Counting Triangles / Quadruples

> Similar structure: count tuples with constraint on certain positions.

The pattern "fix some positions, factor the rest" appears in many combinatorial problems.

**Connection to:**
- **Combinatorial patterns:** Reusable structure.
- **Constraint satisfaction:** Counting valid configurations.

### Insight 13: Why Python's `ord(c) - 48`

> Faster than `int(c)`. Avoids function call overhead.

Micro-optimization but useful in tight loops.

**Connection to:**
- **Performance:** Small wins add up.
- **Python internals:** ord is fast.

### Insight 14: Connection to Edit Distance

> Different problem but similar DP-with-prefix structure.

Edit distance uses 2D DP on prefixes. Here we use 1D prefix per digit.

**Connection to:**
- **String DP family:** Common patterns.
- **Prefix arrays:** Versatile tool.

---

## 🧪 TEST CASES

| `s` | Expected | Note |
|-----|----------|------|
| `"10301"` | 1 | Whole string |
| `"11111"` | 1 | All same |
| `"111111"` | 6 | C(6,5) |
| `"10101"` | 1 | Single palindrome |
| `"1010101"` | 9 | Symmetric |
| `"100001"` | 4 | Multiple inner pairs |
| `"110011"` | 2 | Few |
| `"121121"` | 2 | Few |
| `"12345"` | 0 | Distinct |
| `"0000000"` | 21 | C(7,5) |
| `"99999"` | 1 | All same |
| `"9090909"` | 9 | Same as 1010101 |
| `"11"` | 0 | Too short |
| `""` | 0 | Empty |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Inner-pair prefix DP** | **O(10n²)** | **O(10n)** | **✅ BEST** |
| Fix-middle | O(10n³) | O(10n) | ✅ Correct but slower |
| Brute force | O(n⁵) | O(1) | ❌ Too slow for n=10⁴ |
| O(n⁴) outer | O(n⁴) | O(1) | ❌ Borderline |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Count Palindromic Substrings (LC 647) | Manacher/DP | https://leetcode.com/problems/palindromic-substrings/ |
| Distinct Subsequences (LC 940) | DP | https://leetcode.com/problems/distinct-subsequences/ |
| Count Different Palindromic Subseq (LC 730) | Interval DP | https://leetcode.com/problems/count-different-palindromic-subsequences/ |
| Longest Palindromic Subseq (LC 516) | 2D DP | https://leetcode.com/problems/longest-palindromic-subsequence/ |
| Count Palindromic Subseq (gfg) | Combinatorics | https://www.geeksforgeeks.org/count-palindromic-subsequence-given-string/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **Fix the right pivot** — choosing the inner pair makes the rest factorize.
2. **Constant alphabet** turns O(n^k × alphabet) into O(n^k).
3. **Prefix sums** compress O(n) range queries into O(1).
4. **Inner pair + middle + outer** = clean factorization.
5. **O(10n²) dominates** for fixed alphabet.
6. **DNA palindromes** are the canonical use case.
7. **Symmetric constraints** factorize via pairs.
8. **For n=10⁴, n² × 10 ≈ 10⁹** is borderline; use efficient inner loops.
9. **Edge case: n<5** → 0.
10. **Brute force O(n⁵)** is too slow.

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Bioinformatics** | DNA palindromic sites |
| **Cryptography** | Palindromic keys |
| **Text mining** | Symmetric structures |
| **Sequence analysis** | Palindromic motifs |
| **Compression** | Palindromic blocks |
| **Network routing** | Symmetric paths |
| **Error detection** | Palindromic checksums |
| **Music composition** | Palindromic motifs |
| **Genomics** | Self-complementary sequences |
| **Combinatorial counting** | Constraint enumeration |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive inner-pair formula in 90 seconds
- [x] Can code the 18-line solution in 90 seconds
- [x] Know complexity: O(10 × n²) time, O(10 × n) space
- [x] Know why inner pair (not middle/outer) is the right pivot
- [x] Know prefix sum trick for O(1) range queries
- [x] Know edge cases (n<5, all distinct, all same)
- [x] Can compare with brute force
- [x] Know related problems (LC 647, LC 940, LC 730)
- [x] Can list 5 real-world applications

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 12 minutes.
**Lines of code to write:** 18.
**Insight:** "Fix inner pair (j, l) with s[j]=s[l]. Middle k has l-j-1 choices. Outer (i, m) factorizes: count_a(s[0..j-1]) × count_a(s[l+1..n-1]). Sum over digits a. O(10 × n²)."