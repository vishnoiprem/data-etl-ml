# Partition Labels — 0.0001% Expert Guide

> **LeetCode 763** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/partition-labels
> **Problem:** `partitionLabels(s)` — partition s into max parts where each char appears in only one part.

---

## 📋 WHAT THE QUESTION ASKS

Given a string `s`, partition it into as many parts as possible so that each letter appears in **at most one part**. Return the sizes of these partitions.

### Constraints
- `1 <= s.length <= 500`
- `s` consists of lowercase English letters.

### Examples
```
"ababcbacadefegdehijhklij" -> [9, 7, 8]
    partitions: "ababcbaca", "defegde", "hijhklij"
"eccbbbbdec"               -> [10]
"abc"                       -> [1, 1, 1]
"abac"                      -> [3, 1]
```

### Why This Is "Medium"
- Greedy reasoning: cut when safe, EARLIEST safe cut = max parts.
- Last-occurrence tracking is the key insight.
- O(n) time, O(1) space (26-letter map).

---

## 🧠 HOW TO THINK — STEP BY STEP

### Step 1: Understand the Problem
> "Split s into max number of parts such that each character appears in only ONE part. Return sizes."

### Step 2: Key Insight — Earliest Safe Cut
> "A cut at position i is SAFE iff no character in s[0..i] appears beyond position i.
> The earliest such cut maximizes later opportunities."

### Step 3: Greedy with Last-Occurrence Map
> "Precompute last[c] = last index of char c in s.
> Walk through s. Maintain 'current partition's end' = max(last[c]) over chars seen.
> When we REACH this end, the current partition is finished."

### Step 4: Algorithm
```
1. last[c] = last index of c (in O(n)).
2. start = end = 0; result = [].
3. For i in 0..n-1:
     end = max(end, last[s[i]]).
     if i == end:
         result.append(end - start + 1)
         start = end + 1.
4. Return result.
```

### Step 5: Why Greedy = Optimal
> "If we cut at the EARLIEST safe position, we leave maximum room for subsequent partitions.
> Earliest safe position = i where i == max(last[c] for c in seen-so-far).
> Maximum number of safe cuts = maximum number of partitions."

### Step 6: Edge Cases
- Each char unique: n partitions of size 1.
- All same char: 1 partition of size n.
- Two chars interleaved: 1 partition.

### Step 7: Code It
```python
def partitionLabels(s):
    last = {c: i for i, c in enumerate(s)}
    result = []
    start = end = 0
    for i, c in enumerate(s):
        end = max(end, last[c])
        if i == end:
            result.append(end - start + 1)
            start = end + 1
    return result
```

### Step 8: Verify
For "ababcbacadefegdehijhklij":
- last['a']=8, last['b']=5, last['c']=7, ...
- i=0, c='a': end=max(0,8)=8. i!=8.
- i=1, c='b': end=max(8,5)=8. i!=8.
- ...
- i=8, c='a': end=8. i==8 → result=[9]. start=9.
- ...continues for "defegde" and "hijhklij".

### Step 9: Trade-offs
- Last-occurrence greedy: O(n) time, O(1) space (26 keys). **BEST**.
- rfind-based: O(n²) time without preprocessing.
- Counter-based: O(n) time, O(1) space but slower constants.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT

```
"I need to partition s into max parts with each char in only one part."

KEY INSIGHT: Precompute last[c] = last index of c.
Walk through s. Maintain current partition end = max(last[c]) for chars seen.
When i reaches end, partition is complete.

ALGORITHM:
1. last = {c: i for i, c in enumerate(s)}.
2. start = end = 0; result = [].
3. For i, c in enumerate(s):
     end = max(end, last[c]).
     if i == end:
         result.append(end - start + 1)
         start = end + 1.
4. Return result.

COMPLEXITY: O(n) time, O(1) space (26-letter alphabet).

EDGE CASES:
- n=1: single partition.
- All same char: 1 partition.
- All unique chars: n partitions of size 1.

WHY GREEDY = OPTIMAL:
- Earliest safe cut maximizes remaining string length.
- More remaining = more future partitions possible.

WHY LAST OCCURRENCE:
- A char's partition MUST include its last occurrence.
- max(last[c]) = rightmost required boundary among seen chars.

RELATED:
- Merge Intervals (LC 56)
- Max Non-Overlapping Substrings (similar pattern)
- String partitioning family
"""
```

---

## 💎 THE 9-LINE SOLUTION (Memorize!)

```python
def partitionLabels(s):
    last = {c: i for i, c in enumerate(s)}
    result = []
    start = end = 0
    for i, c in enumerate(s):
        end = max(end, last[c])
        if i == end:
            result.append(end - start + 1)
            start = end + 1
    return result
```

**Time:** `O(n)` | **Space:** `O(1)` (26 keys)

---

## 🤖 KEY INSIGHTS

1. **Precompute last occurrence** — single pass O(n).
2. **Greedy expand right boundary** — max of last[c] for seen.
3. **Earliest safe cut** maximizes number of partitions.
4. **Alphabet size 26** — O(1) space (bounded by alphabet).
5. **Cut condition `i == end`** — single equality check.
6. **Counter approach** works but slower constants.
7. **`rfind` dynamic** works but O(n²) without preprocessing.
8. **Single pass + preprocess** beats multi-pass for big strings.
9. **Output is sizes**, not the actual partition strings.
10. **Unique partitions only** — each char appears in ≤ 1 part.

---

## 🧪 TEST CASES

| Input | Expected | Note |
|-------|----------|------|
| `"ababcbacadefegdehijhklij"` | `[9, 7, 8]` | Classic example |
| `"eccbbbbdec"` | `[10]` | All one part |
| `"abc"` | `[1, 1, 1]` | All unique |
| `"abac"` | `[3, 1]` | 'a','b' span |
| `"a"` | `[1]` | Single char |
| `"aa"` | `[2]` | Two same |
| `"abcabc"` | `[6]` | Entire string |
| `"abcdef"` | `[1, 1, 1, 1, 1, 1]` | All unique |

---

## 📊 COMPLEXITY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Last-occurrence greedy** | **O(n)** | **O(1)** (26 keys) | **✅ BEST** |
| Counter technique | O(n) | O(1) | ✅ Alternative |
| rfind dynamic | O(n²) | O(1) | ❌ Slow |
| Brute force set | O(n²) | O(1) | ❌ Slow |

---

## 🔗 RELATED

- Merge Intervals (LC 56)
- Max Number of Non-Overlapping Substrings
- String Partition Problems
- Greedy + Hash Map combination pattern

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Insight:** "Precompute last occurrence. Expand partition right to max last-seen. Cut at i == end. Earliest safe cut = max partitions."
