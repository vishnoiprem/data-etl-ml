# Minimum Window Subsequence — 10 Solutions + Interview Thinking

## Problem
Given strings `s1` and `s2`, find the shortest substring of `s1` such that
`s2` is a subsequence of it. Return `""` if no such substring exists.

Reference: LeetCode #727 / Educative Grokking — "Minimum Window Subsequence".

---

## Interview Talking Points

Lead with the **two-phase scan**: "Forward scan finds a window where s2
is a subsequence. Greedy backward scan shrinks to the minimum window."

Then explain that this differs from "Minimum Window Substring"
(LC #76): there, EVERY char must appear; here, ORDER matters.

---

## 10-Step Thinking Process

### 1. Understand
"Find the shortest substring of `s1` such that `s2` appears as a
subsequence (preserving order)."

### 2. Key Insight
For each starting index `i` in `s1` matching `s2[0]`:
1. **Forward scan**: find smallest `end` such that `s2` is a subsequence
   of `s1[i..end]`.
2. **Backward greedy shrink**: walk back from `end`, matching `s2`
   chars from last to first. The new `start` is the position of the
   last `s2[0]` match found.

Track the smallest window.

### 3. Pattern Recognition
Two-pointer with subsequence matching. Different from "Minimum Window
Substring" because we don't need EVERY char — we need them IN ORDER.

### 4. Edge Cases
- `len(s2) > len(s1)` → `""`.
- `s2 == ""` → `""`.
- `s2` not a subsequence of `s1` at all → `""`.
- `s1 == s2` → `s1`.
- Single chars match → that single char.

### 5. Tricky Detail — The Backward Shrink

When shrinking from the end:
- Match `s2[m-1]` going backwards. Each match moves `k` down.
- We don't update `start` when `s1[start] == s2[k]` matching the LAST
  pending char. Instead, we always decrement `start` once per iteration,
  then check if the move matches.

The trick: each `s1[start]` decrement is independent. When `s1[start]`
matches `s2[k]`, we decrement `k` (effectively locking that position).
When `k` reaches `-1`, we've found all of `s2`. The valid start is
the position immediately after our last decrement.

### 6. Algorithm
```
i = 0
best = ""
while i < len(s1):
    if s1[i] != s2[0]: i += 1; continue
    # Forward scan
    j = i; k = 0
    while j < n and k < m:
        if s1[j] == s2[k]: k += 1
        j += 1
    if k < m: break  # No more windows
    end = j - 1
    # Backward shrink
    k = m - 1
    start = end
    while k >= 0 and start >= 0:
        if s1[start] == s2[k]: k -= 1
        start -= 1
    start += 1
    window = s1[start:end + 1]
    if not best or len(window) < len(best):
        best = window
    i = start + 1
return best
```

### 7. Why It Works
For each start that matches `s2[0]`, we find the smallest window.
The greedy shrink from the end ensures we find the LATEST possible
position for each `s2[k]`, leaving `s2[0]` at its latest valid position.
This minimizes the window for this particular start. We track the
overall minimum.

### 8. Complexity
- **Time**: O(n·m) worst case (each start triggers forward scan O(n),
  backward shrink O(m); done O(n) times).
- **Space**: O(1) (in addition to the result).

### 9. Code Structure
1. Edge case check.
2. Outer loop: find each `s1[i] == s2[0]`.
3. Forward scan: find `end`.
4. Backward shrink: find `start`.
5. Update best; advance `i`.

### 10. Mental Trace
`s1 = "abcdebdde"`, `s2 = "bde"`:

- i=0 'a': no match. i=1.
- i=1 'b': matches `s2[0]='b'`.
- Forward scan from i=1:
  - j=1 'b'='b', k=1. j=2.
  - j=2 'c'≠'d'. j=3.
  - j=3 'd'='d', k=2. j=4.
  - j=4 'e'='e', k=3. j=5.
  - Loop ends (k=3=m). end=4.
- Backward shrink from end=4:
  - k=2 'e'. start=4. s1[4]='e'='e', k=1. start=3.
  - k=1 'd'. start=3. s1[3]='d'='d', k=0. start=2.
  - k=0 'b'. start=2. s1[2]='c'≠'b'. start=1.
  - k=0. start=1. s1[1]='b'='b', k=-1. start=0.
  - Loop ends (k<0). start=start+1=1.
- Window = s1[1..4] = "bcde" len 4. ✓
- best = "bcde". i = start+1 = 2.
- i=2 'c': no match. ... (skip ahead)
- i=5 'b': matches. Forward scan gives end=8. Window = "bdde" len 4. Best stays "bcde".

Return "bcde". ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time    | Space | Notes |
|----|---------------------------------------|---------|-------|-------|
| 1  | Forward+backward shrink (BEST)        | O(n·m)  | O(1)  | canonical |
| 2  | Clean two-pointer                     | O(n·m)  | O(1)  | readable |
| 3  | DP forward pass                       | O(n·m)  | O(m)  | alternative |
| 4  | DP from end (matrix)                  | O(n·m)  | O(n·m) | overkill |
| 5  | Two-pointer with rescan               | O(n·m)  | O(1)  | iterative |
| 6  | Brute force O(n²·m)                   | O(n²·m) | O(1)  | educational |
| 7  | Recursive                             | O(n·m)  | O(n)  | call stack |
| 8  | Forward only (no greedy shrink)       | O(n·m)  | O(1)  | suboptimal |
| 9  | Per-end scan                          | O(n·m)  | O(1)  | alt iter |
| 10 | One-pass two-pointer                  | O(n·m)  | O(1)  | variant |

---

## Recommended Interview Answer

**Solution 1** — clean, optimal:

```python
def min_window_subsequence(s1, s2):
    if not s1 or not s2 or len(s2) > len(s1):
        return ""
    n, m = len(s1), len(s2)
    best = ""
    i = 0
    while i < n:
        if s1[i] != s2[0]:
            i += 1
            continue
        # Forward scan
        j = i
        k = 0
        while j < n and k < m:
            if s1[j] == s2[k]:
                k += 1
            j += 1
        if k < m:
            break
        end = j - 1
        # Backward shrink
        k = m - 1
        start = end
        while k >= 0 and start >= 0:
            if s1[start] == s2[k]:
                k -= 1
            start -= 1
        start += 1
        window = s1[start:end + 1]
        if not best or len(window) < len(best):
            best = window
        i = start + 1
    return best
```

---

## Common Pitfalls

1. **Confusing with LC #76 (Minimum Window Substring)** — subsequence,
   not substring. Order matters for `s2`.
2. **Forgetting the backward shrink** — without it, you get the
   SHORTEST END but the LONGEST START, which isn't minimal.
3. **Off-by-one in `start + 1` after the loop** — easy to miss.
4. **Not advancing `i` past the start** — could loop forever.
5. **Returning first occurrence** — sometimes multiple windows of
   equal length; we should return the FIRST found for consistency.

---

## Talking Points — Interview Cheat Sheet

If asked "how does this differ from minimum window substring?":
> "In substring, every char of `t` must appear in the window,
> regardless of order. In subsequence, the chars of `t` must appear in
> the SAME order. So subsequence imposes extra structure."

If asked "what's the greedy shrink for?":
> "After forward scan finds the smallest `end` such that `s2` is a
> subsequence, we walk back from `end`, matching `s2` chars from last
> to first. This finds the LATEST possible `start`. The result is the
> smallest window for this particular start position."

If asked "what's the time complexity?":
> "O(n·m). For each of O(n) start positions, we do an O(n) forward
> scan and an O(m) backward shrink. The `i` advancement prevents
> redoing work."

If asked "what about a DP solution?":
> "We could precompute `match[i][j]` = earliest end index where
> `s2[j..]` can be matched starting from `s1[i]`. Then for each
> `s1[i] == s2[0]`, the window ends at `match[i+1][1] - 1`. Faster in
> practice but more complex."

---

## Related Problems

- **Minimum Window Substring** (LC #76) — different: substring vs
  subsequence.
- **Is Subsequence** (LC #392) — simpler: just check if `t` is
  subsequence of `s`.
- **Number of Matching Subsequences** (LC #792) — counts subsequences
  of `s` for many `t`s.
- **Shortest Common Supersequence** — different problem (build
  shortest string with both as subsequence).

---

## Variants

- **Minimum Window Substring with subsequence**: only require chars in
  order, not all of them.
- **Count windows**: how many windows have `s2` as subsequence.
- **Multiple subsequences**: find windows covering several `s2`s.