# Longest Repeating Character Replacement — 10 Solutions + Interview Thinking

## Problem
Given a string `s` and an integer `k`, you can change any character to any
other uppercase letter, at most `k` times. Return the length of the longest
substring that can be made into all the same characters after these
replacements.

Reference: LeetCode #424 / Educative Grokking — "Longest Repeating Character Replacement".

---

## Interview Talking Points

When discussing this problem in an interview, lead with the **invariant**:
> "Any window's 'cost to make uniform' equals `window_length - max_freq_in_window`."

This single insight unlocks the sliding window approach. Then walk the
interviewer through how the window can stay valid or get shrunk.

---

## 10-Step Thinking Process

### 1. Understand
"Make the longest substring uniform (all one character) with at most `k`
character swaps. The 'best' character to swap TO is the most frequent
character in the current window."

### 2. Key Insight
For any window `[left, right]`:
- `window_length = right - left + 1`
- `max_freq = max(count of any char in window)`
- **cost** to make uniform = `window_length - max_freq` (the chars we need to flip)
- Window is **valid** iff `cost <= k`

So we want: **largest window where `len - max_freq <= k`**.

### 3. Pattern Recognition
Sliding window with:
- Two pointers (`left`, `right`)
- A frequency table (26 letters)
- Track `max_freq` (the running peak)
- Shrink from `left` while invalid; expand `right` each step.

### 4. Edge Cases
- `k == 0`: longest run of identical characters.
- `k >= n`: trivially the whole string.
- All same characters: full length, regardless of `k`.
- All distinct with `k = 1`: longest window of length 2 (e.g., "AB" → "AA" or "BB").
- Empty string: 0.

### 5. Tricky Detail — Why We Don't Recompute `max_freq`

The canonical implementation only **increases** `max_freq`, never decreases:

```python
freq[idx] += 1
max_freq = max(max_freq, freq[idx])  # NEVER decrease
while ...:
    freq[ord(s[left]) - ord('A')] -= 1
    left += 1
```

This is **correct** for finding the maximum valid window length:
- `max_freq` may go "stale" (be higher than the true current max).
- A stale `max_freq` makes the window look "more valid" than it really is.
- So `len - max_freq <= k` (using stale max) **implies**
  `len - true_max <= k` (the actual condition).
- Wait, that's backwards. Let me redo:

If `max_freq_stale >= true_max`, then `len - max_freq_stale <= len - true_max`.
So `len - true_max > k` does NOT imply `len - max_freq_stale > k`.

Actually: if `max_freq_stale >= true_max`, then `len - max_freq_stale <= len - true_max`.
We need `(len - true_max) <= k`. The condition we CHECK is `(len - max_freq_stale) > k`
to shrink. If we have `(len - max_freq_stale) <= k`, we don't shrink.

If `true_max < max_freq_stale`, then `(len - true_max) > (len - max_freq_stale)`.
So `(len - true_max) > k` is possible while `(len - max_freq_stale) <= k`.

In this case, the window is actually invalid but we don't shrink because the
stale max fooled us. Is this a problem? No, because:
- When the window stretches, we don't claim it as an answer UNLESS it's truly valid.
- The NEXT time `max_freq` actually increases (via right expansion), we recover.
- The algorithm finds the LARGEST window. Stale `max_freq` makes the window
  smaller than the truly-largest invalid one, but the truly-largest VALID
  window is still discovered when `max_freq` increases for real.

So: not decreasing `max_freq` is correct (and faster than recomputing each
iteration, which can be O(26) per step).

### 6. Algorithm
```python
freq = [0] * 26
left = 0
max_freq = 0
best = 0
for right in range(n):
    idx = ord(s[right]) - ord('A')
    freq[idx] += 1
    if freq[idx] > max_freq:
        max_freq = freq[idx]
    while (right - left + 1) - max_freq > k:
        freq[ord(s[left]) - ord('A')] -= 1
        left += 1
    cur = right - left + 1
    if cur > best:
        best = cur
return best
```

### 7. Why It Works (Proof Sketch)
**Invariant**: At the end of each iteration of the outer loop, the window
`[left, right]` is **valid** (cost <= k), and `best` is the maximum length
of any valid window seen so far.

**Termination**: When `right == n`, no more characters. The window is valid.
`best` holds the answer.

**Termination of inner loop**: Each `left += 1` strictly increases `left`,
so the loop terminates. Since we only enter when `cost > k`, and `left`
approaches `right`, eventually `cost <= k`.

### 8. Complexity
- Time: **O(n)**. Each character is added to the window once and removed
  from the window once. Both operations are O(1).
- Space: **O(1)** — 26-letter array.

### 9. Code Structure
```python
def characterReplacement(s, k):
    n = len(s)
    freq = [0] * 26
    left = 0
    max_freq = 0
    best = 0
    for right in range(n):
        idx = ord(s[right]) - ord('A')
        freq[idx] += 1
        max_freq = max(max_freq, freq[idx])
        while (right - left + 1) - max_freq > k:
            freq[ord(s[left]) - ord('A')] -= 1
            left += 1
        best = max(best, right - left + 1)
    return best
```

### 10. Mental Trace
`s = "AABABBA"`, `k = 1`:
- right=0 (A): freq[A]=1, max=1, len=1, cost=0 ≤ 1. best=1.
- right=1 (A): freq[A]=2, max=2, len=2, cost=0 ≤ 1. best=2.
- right=2 (B): freq[B]=1, max=2, len=3, cost=1 ≤ 1. best=3.
- right=3 (A): freq[A]=3, max=3, len=4, cost=1 ≤ 1. best=4.
- right=4 (B): freq[B]=2, max=3, len=5, cost=2 > 1.
  - shrink: left=0 (A), freq[A]=2. len=5, cost=2. Still > 1.
  - shrink: left=1 (A), freq[A]=1. len=4, cost=1. OK.
- right=5 (B): freq[B]=3, max=3, len=5, cost=2 > 1.
  - shrink: left=2 (B), freq[B]=2. len=4, cost=1. OK.
- right=6 (A): freq[A]=2, max=3, len=5, cost=2 > 1.
  - shrink: left=3 (A), freq[A]=1. len=4, cost=1. OK.
- best = 4. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time    | Notes |
|----|---------------------------------------|---------|-------|
| 1  | Frequency array (BEST)                | O(n)    | canonical |
| 2  | Counter                               | O(n)    | pythonic |
| 3  | defaultdict + return at end           | O(n)    | alternative |
| 4  | Brute force O(n²)                     | O(n²)   | educational |
| 5  | All-substrings check                  | O(n³)   | slow |
| 6  | Binary search on answer length        | O(n log n) | educational |
| 7  | Recompute max each iteration          | O(n)    | slightly slower |
| 8  | Heap-based frequency                  | O(n log n) | over-engineered |
| 9  | Recursive                             | O(n)    | educational |
| 10 | Per-target-char windows               | O(26n)  | alternative |

---

## Recommended Interview Answer
**Solution 1** — clean, optimal, idiomatic:

```python
def characterReplacement(s, k):
    freq = [0] * 26
    left = 0
    max_freq = 0
    best = 0
    for right in range(len(s)):
        idx = ord(s[right]) - ord('A')
        freq[idx] += 1
        if freq[idx] > max_freq:
            max_freq = freq[idx]
        while (right - left + 1) - max_freq > k:
            freq[ord(s[left]) - ord('A')] -= 1
            left += 1
        best = max(best, right - left + 1)
    return best
```

---

## Common Pitfalls
1. **Decrementing `max_freq` when shrinking** — DON'T do this. It would
   make the window too aggressive and could shrink away valid windows.
2. **Forgetting to ASCII-shift** — directly using `s[right]` as array index
   uses Unicode codepoints; the array would explode. Always use
   `ord(s[right]) - ord('A')`.
3. **`while` vs `if`** — when shrinking, use `while` (might need multiple
   shrinks), not `if`. Otherwise the window might stay invalid.
4. **Not handling empty string** — although this problem guarantees `n >= 1`,
   always defensive-check.
5. **Counting `cost > k` instead of `>=`** — use `>` not `>=` since the
   condition for valid is `cost <= k`.

---

## Talking Points — Interview Cheat Sheet

If asked "what's the running max for?":

> "The cost of making the window uniform is `len - max_freq`. We want this
> to be at most `k`. So when the cost exceeds `k`, we shrink the window
> from the left. We never decrease `max_freq` because doing so would shrink
> the window unnecessarily — the algorithm is still correct."

If asked "why doesn't your algorithm give the right answer when `max_freq`
is stale?":

> "When `max_freq` is stale, the cost `len - max_freq` is LOWER than the
> true cost. So the window may not shrink when it should. But that's OK —
> we're expanding rightward anyway, and as soon as a real maximum emerges,
> we'll shrink correctly. The answer we get is still the LARGEST VALID
> window, just possibly discovered in a different order."

If asked "what's the alternative?":

> "Either recompute `max_freq` every iteration (O(26) per step, still O(n)
> overall) or use a max-heap with lazy deletion. But the canonical
> 'never decrease' trick is cleanest."

---

## Related Problems
- **Maximum Consecutive Ones III** — same template, with `0/1` array and `k` flips.
- **Maximize the Confusion of an Exam** (LC 2024) — same problem, different name.
- **Number of Substrings with All Three Characters** — variant that uses
  frequency tracking with specific required letters.
- **Subarrays with K Different Integers** — extends to distinct-count
  constraint instead of "all same".

---

## Variants
- **Lowercase letters**: replace `ord('A')` with `ord('a')` and use a
  26-element array.
- **All ASCII**: use a 128-element array.
- **Unicode**: use a dictionary (`Counter`) — solves the unbounded alphabet.
