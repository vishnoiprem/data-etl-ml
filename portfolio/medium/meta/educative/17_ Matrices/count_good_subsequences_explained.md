# Count the Number of Good Subsequences — 0.0001% Expert Guide

> **LeetCode 2539** (or similar) | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/count-the-number-of-good-subsequences
> **Problem:** `countGoodSubsequences(s)` — count of good subsequences mod 10^9+7.

---

## 📋 WHAT THE QUESTION ASKS

Count "good" subsequences of `s` where each character's frequency is the same. Return the count mod `10^9 + 7`.

A good subsequence is non-empty with all character frequencies equal.

### Constraints
- `1 <= s.length <= 10^4`
- Lowercase English letters

### Examples
```
s='aab'   -> 6   (a, b, a-pos0, a-pos1, ab-pos0, ab-pos1)
s='abc'   -> 7   (all 2^3 - 1 = 7 non-empty)
s='a'     -> 1
s='ab'    -> 3   (a, b, ab)
s='aabb'  -> 11
s='abcabc' -> 33
```

### Why This Is "Medium"
- Combinatorial insight.
- Modular arithmetic.
- Single O(K * alphabet) pass.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (2 min)
> "Count non-empty subsequences where all char frequencies are equal."

### Step 2: KEY INSIGHT — k-uniform Decomposition (5 min)
> "A good subsequence is k-uniform: each USED char appears k times.
> For each k >= 1, count subsequences with this property, then sum."

### Step 3: Why Product Formula (3 min)
> "For a given k, each character independently chooses:
> - Not used (1 way), OR
> - Used k times (C(cnt[c], k) ways).
>
> Total ways for k = prod over chars of (1 + C(cnt[c], k)).
> Subtract 1 for empty subsequence."

### Step 4: Algorithm (3 min)
```
1. freq = Counter(s). max_k = max(freq.values()).
2. ans = 0.
3. For k in 1..max_k:
     prod = 1
     For cnt in freq.values():
       prod = (prod * (1 + C(cnt, k))) mod M
     ans = (ans + prod - 1) mod M
4. Return ans.
```

### Step 5: Edge Cases (2 min)
- Empty s: 0.
- Single char: 1.
- All same char 'a' repeated n: sum of (1 + C(n,k)) - 1 = 2^n - 1.

### Step 6: Code It (3 min)

```python
def countGoodSubsequences(s):
    MOD = 10**9 + 7
    from collections import Counter
    from math import comb
    freq = Counter(s)
    if not freq:
        return 0
    max_k = max(freq.values())
    ans = 0
    for k in range(1, max_k + 1):
        prod = 1
        for cnt in freq.values():
            prod = (prod * (1 + comb(cnt, k))) % MOD
        ans = (ans + prod - 1) % MOD
    return ans
```

### Step 7: Verify (2 min)
For 'aab': freq={a:2, b:1}. max_k=2.
- k=1: (1+C(2,1))*(1+C(1,1)) - 1 = 3*2 - 1 = 5.

Wait, expected=6. Hmm — let me recount. Actually, 'aab' has subsequences: 'a'(pos0), 'a'(pos1), 'aa', 'b', 'ab'(skip b), 'ab'(skip last a). 

Actually 'ab' from 'aab': skip pos 0 → 'ab', skip pos 1 → 'ab'. Both yield 'ab'. But we're counting distinct position-tuples, not distinct strings.

So 'a': C(2,1)=2 ways. 'b': C(1,1)=1 way. 'ab': C(2,1)*C(1,1)=2 ways. Total k=1: 5.

k=2: 'aa' C(2,2)=1 way. 'bb'? b has count 1 < 2. So can't pick b. For subset of chars {a}: 1 way. For subset {b}: 0. For {a,b}: 0. Total: 1.

Sum: 5+1=6 ✓

(Actually my formula gives 5 for k=1, plus 0 for k=2 = 5. But brute gives 6. Let me recheck.)

Actually let me recompute k=2 for 'aab':
- (1 + C(2,2)) * (1 + C(1,2)) - 1 = (1+1) * (1+0) - 1 = 2*1 - 1 = 1.

So total = 5 + 1 = 6 ✓

### Step 8: Discuss Trade-offs (3 min)
> "Two approaches:
> 1. **Closed-form formula:** O(K * 26). **BEST**.
> 2. **Brute bitmask:** O(2^n * n). For small n only.
>
> I'll use the formula."

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to count subsequences where all character frequencies are equal.
Return mod 10^9 + 7."

KEY INSIGHT: k-uniform decomposition.
A good subsequence has each used char appearing k times, for some k >= 1.

For each k:
- Each char independently: NOT used (1 way) OR used k times (C(cnt[c], k) ways).
- Per-k count = prod over chars of (1 + C(cnt[c], k)) - 1 (subtract empty).

ALGORITHM:
1. freq = Counter(s). max_k = max(freq.values()).
2. For k in 1..max_k:
     prod = 1
     For cnt in freq.values():
       prod = (prod * (1 + C(cnt, k))) % M
     ans = (ans + prod - 1) % M
3. Return ans.

COMPLEXITY: O(K * alphabet_size) where K = max char count.

EDGE CASES:
- Empty: 0.
- Single char: 1.
- All same 'a'*n: 2^n - 1 (sum of C(n,k) = 2^n - 1).

THE TRICK:
- (1 + C(cnt, k)) captures 'not used' (1) and 'used k times' (C(cnt, k)).
- Product = independent choices per char.
- Subtract 1 for empty subsequence.

RELATED:
- Subsequence counting.
- Inclusion-exclusion.
- Combinatorial DP.
"""

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Combinatorial Formula (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | Standard formula | O(K*S) | O(S) | **THE ANSWER** |
| 2 | Pre-compute comb | O(K*S) | O(S) | Variant |
| 3 | DP subsets | O(K*S) | O(S) | Variant |
| 5 | Per char positions | O(K*S) | O(S) | Variant |
| 6 | Class OOP | O(K*S) | O(S) | Reusable |
| 7 | Iterative comb | O(K*S) | O(S) | Educational |
| 8 | Explicit variable | O(K*S) | O(S) | Variant |
| 13 | Same as 1 | O(K*S) | O(S) | Duplicate |
| 14 | Reduce | O(K*S) | O(S) | Functional |
| 15 | Modulo wrap | O(K*S) | O(S) | Variant |
| 16 | Sorted freq | O(K*S) | O(S) | Educational |
| 17 | comb helper | O(K*S) | O(S) | Educational |
| 18 | Pre-compute table | O(K*S) | O(K*S) | Memoization |
| 19 | Counter.values | O(K*S) | O(S) | Educational |
| 20 | Final cleanest | O(K*S) | O(S) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: Brute Force / Recursion

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 4 | Brute bitmask | O(2^n * n) | O(n) | Small n |
| 11 | Brute recursion | O(2^n * n) | O(n) | Small n |

### 🟠 TIER 3: Subset Enumeration

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 10 | Memoized comb | O(K*S) | O(K*S) | Memoized |
| 12 | Subset iteration | O(2^S * K) | O(K) | Educational |

### 🔵 TIER 4: Specialized

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 9 | Numpy | O(K*S) | O(S) | Vectorized |

---

## 💎 THE 10-LINE SOLUTION (Memorize!)

```python
def countGoodSubsequences(s):
    MOD = 10**9 + 7
    from collections import Counter
    from math import comb
    freq = Counter(s)
    if not freq:
        return 0
    max_k = max(freq.values())
    ans = 0
    for k in range(1, max_k + 1):
        prod = 1
        for cnt in freq.values():
            prod = (prod * (1 + comb(cnt, k))) % MOD
        ans = (ans + prod - 1) % MOD
    return ans
```

**Time:** `O(K * S)` where K = max char count, S = unique chars.
**Space:** `O(S)`

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: k-uniform Decomposition

> Split by k (frequency value). Each char's frequency in subsequence
> is either 0 or k. Two choices per char = product.

**Connection to:**
- **Combinatorial decomposition:** Sum over cases.
- **Standard pattern:** Frequency analysis.

### Insight 2: Why (1 + C(cnt, k))

> 1 = "not used" choice. C(cnt, k) = "use exactly k copies".
> Sum of these two = binary choice per char.

**Connection to:**
- **Inclusion:** Two cases.
- **Standard trick:** 1 + something.

### Insight 3: Subtract 1 for Empty

> Product counts empty subsequence (all "not used").
> Subtract 1 to exclude.

**Connection to:**
- **Edge case:** Empty subsequence.
- **Standard:** Always subtract.

### Insight 4: Why Max_k

> For char with count n, k can be 1..n.
> For all chars, k <= max(counts).
> So loop k up to max(freq.values()).

**Connection to:**
- **Bound analysis:** Tight bound.
- **Loop limits:** Always compute.

### Insight 5: Connection to Sum of Powers

> For 'a'*n, sum_{k=1..n} C(n,k) = 2^n - 1.
> Our formula gives sum of (1 + C(n,k)) - 1 = sum of C(n,k) = 2^n - 1.

Sanity check.

**Connection to:**
- **Mathematical identity:** Binomial sum.
- **Verification:** Always check edge.

### Insight 6: Modular Subtraction

> `(prod - 1) % MOD` may be negative if prod == 0.
> Use `(prod - 1 + MOD) % MOD` to be safe.

**Connection to:**
- **Python modulo:** Can be negative.
- **Defensive:** Always add MOD.

### Insight 7: Real-World Applications

| Application | Use |
|-------------|-----|
| **Inventory** | Uniform stock combos |
| **Sampling** | Balanced samples |
| **Test design** | Balanced question pools |
| **Bioinformatics** | Uniform sequence coverage |
| **Cryptography** | Balanced keys |
| **Combinatorial games** | Balanced configurations |

**Inventory** is the canonical use case.

### Insight 8: Why Brute is O(2^n)

> 2^n subsequences. Each checked for uniform freq.
> For n = 10000, infeasible.

Formula approach: O(K * 26).

**Connection to:**
- **Exponential:** Brute is bad.
- **Efficiency:** Formula wins.

### Insight 9: Comb Computation

> Python's `math.comb(cnt, k)` handles large values natively.
> For very large n, may need modular inverse.

**Connection to:**
- **Standard library:** Use it.
- **Big numbers:** Python handles.

### Insight 10: Independent Choices

> Each char's choice (used k times or not) is INDEPENDENT.
> Total = product.

**Connection to:**
- **Probability:** Independent events.
- **Counting:** Multiplication rule.

### Insight 11: Empty Product

> If no chars in s, prod = 1 (empty product).
> ans = 0 (subtracted from total).

Edge case handled.

**Connection to:**
- **Identity:** Empty product = 1.
- **Mathematical convention:** Always.

### Insight 12: Why Sum Over k

> Different k values give disjoint sets of subsequences.
> (A subsequence has UNIQUE frequency value.)
> So sum is correct (no double counting).

**Connection to:**
- **Disjoint sets:** Sum is valid.
- **Partition:** k is a parameter.

### Insight 13: When freq Dict is Better

> For sparse alphabets, dict is faster than array.
> For dense alphabets, array is faster.

For lowercase (26), either works.

**Connection to:**
- **Data structure:** Match usage.
- **Performance:** Match access pattern.

### Insight 14: Why Not Generate Subsequences

> Generating all 2^n subsequences is too slow.
> Combinatorial formula is closed-form.

**Connection to:**
- **Combinatorics:** Closed-form beats enumeration.
- **Standard approach:** Use math.

### Insight 15: Connection to Subset Sum

> Same general pattern: each char has independent choices,
> count valid configurations.

**Connection to:**
- **Problem family:** Counting valid subsets.
- **Combinatorial:** Standard.

### Insight 16: Reduce for Functional Style

> `functools.reduce(lambda a, c: ..., values, 1)` for product.
> Cleaner than explicit loop.

**Connection to:**
- **Functional programming:** Reduce.
- **Python idioms:** Standard.

---

## 🧪 TEST CASES

| `s` | Expected | Note |
|-----|----------|------|
| `'aab'` | 6 | Standard |
| `'abc'` | 7 | 2^3 - 1 |
| `'aaaa'` | 15 | 2^4 - 1 |
| `'aabb'` | 11 | Mixed |
| `'a'` | 1 | Single |
| `'aa'` | 3 | Two same |
| `'ab'` | 3 | Two distinct |
| `'aabbcc'` | 33 | Three pairs |
| `'abcabc'` | 33 | Three doubles |
| `'xyz'` | 7 | 2^3 - 1 |
| `'aaaaaa'` | 63 | 2^6 - 1 |
| `''` | 0 | Empty |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Formula** | **O(K*S)** | **O(S)** | **✅ BEST** |
| Brute bitmask | O(2^n * n) | O(n) | ❌ Too slow |
| Recursion | O(2^n) | O(n) | ❌ Too slow |

K = max char count, S = unique chars (≤26).

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Number of Good Subsets (LC 1994) | Bitmask DP | https://leetcode.com/problems/the-number-of-good-subsets/ |
| Subsets II (LC 90) | Backtracking | https://leetcode.com/problems/subsets-ii/ |
| Distinct Subseq (LC 115) | 2D DP | https://leetcode.com/problems/distinct-subsequences/ |
| Subsequence counting | Combinatorics | Various |

---

## 🎓 EXPERT TAKEAWAYS

1. **k-uniform decomposition**: split by frequency.
2. **(1 + C(cnt, k))** = binary choice per char.
3. **Product** = independent choices.
4. **Subtract 1** for empty.
5. **Sum over k** = disjoint cases.
6. **Inventory** is canonical use case.
7. **2^n - 1** for single char.
8. **Math.comb** handles big values.
9. **Modulo** subtraction needs care.
10. **O(K * 26)** beats brute force.

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Inventory** | Uniform stock combos |
| **Sampling** | Balanced samples |
| **Test design** | Balanced pools |
| **Bioinformatics** | Uniform coverage |
| **Cryptography** | Balanced keys |
| **Combinatorial games** | Balanced configs |
| **Data sampling** | Stratified sampling |
| **Caching** | Uniform distribution |
| **Load balancing** | Uniform assignment |
| **Statistics** | Balanced designs |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive the formula in 90 seconds
- [x] Can code the 10-line solution in 60 seconds
- [x] Know complexity: O(K * S) time, O(S) space
- [x] Know why (1 + C(cnt, k))
- [x] Know why subtract 1
- [x] Know why sum over k
- [x] Know related problems
- [x] Know modulo subtraction caveat
- [x] Can list 5 real-world applications

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 15 minutes.
**Lines of code to write:** 10.
**Insight:** "k-uniform: each char either 0 times or k times. Product (1 + C(cnt, k)) - 1. Sum over k."
