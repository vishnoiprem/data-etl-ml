# Is Subsequence — 0.0001% Expert Guide

> **LeetCode 392** | **Difficulty:** Easy | **Avg Solve Time:** 15 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/is-subsequence
> **Problem:** `isSubsequence(s, t)` — check if s is a subsequence of t.

---

## 📋 WHAT THE QUESTION ASKS

Given two strings `s` and `t`, return `True` if `s` is a subsequence of `t`.

A subsequence is formed by deleting zero or more characters from the original string **without changing relative order**.

### Constraints
- `0 <= s.length <= 100`
- `0 <= t.length <= 10^4`
- `s` and `t` consist of lowercase English letters.

### Examples
```
s="abc", t="ahbgdc" -> True   (a, b, c found in order)
s="axc", t="ahbgdc" -> False  (b between a and c, breaks order)
s="ace", t="abcde"  -> True
s="",    t="abc"    -> True   (empty is subsequence of anything)
s="abc", t=""       -> False
```

### Why This Is "Easy"
- Classic two-pointer pattern.
- O(|t|) time, O(1) space.
- Foundation for ordered-match problems.

---

## 🧠 HOW TO THINK — STEP BY STEP

### Step 1: Understand the Problem
> "Determine if s can be obtained from t by deleting zero or more characters."

### Step 2: Key Insight — Greedy Match in Order
> "Walk through t. For each char of s, find the earliest matching char in t.
> If we can match all chars of s in order, s is a subsequence."

### Step 3: Two-Pointer Pattern
> "Walk t with one pointer, walk s with another.
> When chars match, advance both. When they don't, advance t only.
> At end, s is subsequence iff we matched all of s."

### Step 4: Algorithm
```
1. i = 0 (pointer in s).
2. For each c in t:
     if i < len(s) and s[i] == c:
         i += 1.
3. Return i == len(s).
```

### Step 5: Why Greedy = Correct
> "Whenever s[i] matches t[j], we use that match.
> It's never wrong to use the EARLIEST possible match because:
> - It preserves the maximum remaining portion of t.
> - If a later match existed, the earlier one still works."

### Step 6: Edge Cases
- s empty: True (empty subsequence is subsequence of anything).
- t empty: True iff s empty (only empty s).
- s longer than t: False (can't find chars).
- Single char s: check `c in t`.

### Step 7: Code It
```python
def isSubsequence(s, t):
    i = 0
    for c in t:
        if i < len(s) and s[i] == c:
            i += 1
    return i == len(s)
```

### Step 8: Verify
For s="abc", t="ahbgdc":
- i=0, c='a' match → i=1.
- i=1, c='h' no match.
- i=1, c='b' match → i=2.
- i=2, c='g' no match.
- i=2, c='d' no match.
- i=2, c='c' match → i=3.
- i == 3 == len(s). ✓ True.

### Step 9: Trade-offs
- Two-pointer greedy: O(|t|) time, O(1) space. **BEST**.
- Build index + binary search: O(|t| + |s| log n) preprocessing-heavy.
- Pythonic `iter()` + `all()`: elegant O(|t|) time, O(1) space.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT

```
"I need to check if s is a subsequence of t."

KEY INSIGHT: Two pointers. Walk through t. When chars match s, advance.
Greedy: always take the earliest match in t to maximize remaining room.

ALGORITHM:
1. i = 0.
2. For c in t:
     if i < len(s) and s[i] == c:
         i += 1.
3. Return i == len(s).

COMPLEXITY: O(|t|) time, O(1) space.

EDGE CASES:
- s empty: True.
- t empty: only True if s also empty.

WHY GREEDY WORKS:
- Earliest match preserves max remaining t for later matches.
- If a later match works, earliest match also works.

VARIANT: Follow-up "many queries" — preprocess t with char→positions map,
use binary search per char of s.

RELATED:
- Longest Common Subsequence (LC 1143) — DP variant.
- Is Subsequence II (LC 792) — many queries, use preprocessing.
- Number of Matching Subsequences (LC 792).
"""
```

---

## 💎 THE 4-LINE SOLUTION (Memorize!)

```python
def isSubsequence(s, t):
    i = 0
    for c in t:
        if i < len(s) and s[i] == c:
            i += 1
    return i == len(s)
```

**Time:** `O(|t|)` | **Space:** `O(1)`

---

## 🤖 KEY INSIGHTS

1. **Two pointers** — one in s, one walking t.
2. **Single pass through t** — never rewind.
3. **Greedy match** — earliest possible match in t for each s char.
4. **Order preservation** — inherent in sequential walk.
5. **Empty s** is always a subsequence (trivial case).
6. **Empty t** — True only if s empty.
7. **`iter(t)` + `all()`** — Pythonic equivalent.
8. **Counter approach** — alternative using total + seen counts.
9. **Binary search variant** — when many queries for different s.
10. **O(|t|) is tight** — must inspect each char of t.

---

## 🧪 TEST CASES

| `s` | `t` | Expected | Note |
|-----|-----|----------|------|
| `"abc"` | `"ahbgdc"` | `True` | Standard match |
| `"axc"` | `"ahbgdc"` | `False` | Out of order |
| `"ace"` | `"abcde"` | `True` | Skip chars |
| `""` | `"abc"` | `True` | Empty subsequence |
| `"abc"` | `""` | `False` | Empty t |
| `""` | `""` | `True` | Both empty |
| `"aaaaa"` | `"aaaaaaaaaa"` | `True` | Many matches |
| `"abc"` | `"abc"` | `True` | Identical |
| `"ab"` | `"ba"` | `False` | Reversed |
| `"aec"` | `"abcde"` | `False` | Wrong char |

---

## 📊 COMPLEXITY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Two-pointer greedy** | **O(\|t\|)** | **O(1)** | **✅ BEST** |
| `iter()` + `all()` | O(\|t\|) | O(1) | ✅ Pythonic |
| Index + binary search | O(\|t\| + \|s\| log n) | O(\|t\|) | ✅ Many queries |
| Brute (find per char) | O(\|t\| · \|s\|) worst | O(1) | ❌ Slower |
| Recursive | O(\|t\|) | O(\|t\|) stack | ⚠️ Stack-overflow risk |

---

## 🔗 RELATED

- Longest Common Subsequence (LC 1143) — DP
- Is Subsequence II (LC 792) — many queries, char-index
- Matching Subsequences (LC 792)
- Subsequence problems in DP
- String matching family

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Insight:** "Two pointers, greedy match — earliest possible match per char. O(|t|) walk through t, O(1) space."
