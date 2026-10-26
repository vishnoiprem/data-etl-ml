# Day 28 — Algorithms: Sliding Window & Two Pointers
**Module 21** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

Two patterns that turn O(n²) into O(n):

- **Sliding window:** maintain a window `[l, r]` over a string/array. Expand right, contract left. Each index enters and leaves at most once → O(n).
- **Two pointers:** two indices sweep the array, often from opposite ends, often after sorting. Each step prunes half the search space.

Both are about **invariants**: maintain a property as you move.

---

## 2. Technical concepts (20 min)

### Sliding window template
```python
def sliding_window(s):
    l = 0
    state = init_state()  # e.g., Counter
    best = 0
    for r in range(len(s)):
        state.add(s[r])           # expand
        while not valid(state):   # shrink until valid
            state.remove(s[l])
            l += 1
        best = max(best, r - l + 1)
    return best
```

- **State:** what you need to know about the window (e.g., char counts).
- **Valid:** a condition (e.g., no repeats).
- **Two flavors:**
  - **Longest** window: shrink when invalid, record max.
  - **Shortest** window: shrink while still valid, record min.

### Two pointers template
```python
def two_pointers(arr, target):
    arr.sort()  # often required
    l, r = 0, len(arr) - 1
    while l < r:
        s = arr[l] + arr[r]
        if s == target:
            return [l, r]
        if s < target:
            l += 1
        else:
            r -= 1
    return None
```

- **When to use:** sorted input, "pair/triplet sum", "partition".

### Common pitfalls
- Off-by-one in window: `[l, r]` inclusive vs `[l, r)` half-open.
- Forgetting to **update state** on shrink.
- Sorting when input is already sorted (wasted O(n log n)).
- Confusing "longest with at most K" vs "longest with exactly K" (trick: at_most(K) - at_most(K-1) = exactly).

---

## 3. Coding (30 min)

Solve **3 problems**, ~10 min each.

### Problem 1: Longest Substring Without Repeating Chars

```python
def length_of_longest_substring(s: str) -> int:
    last: dict[str, int] = {}
    l = 0
    best = 0
    for r, ch in enumerate(s):
        if ch in last and last[ch] >= l:
            l = last[ch] + 1
        last[ch] = r
        best = max(best, r - l + 1)
    return best
```

- **Time:** O(n). **Space:** O(min(n, alphabet)).
- **Sample:** `"abcabcbb"` → `3` (`"abc"`).

### Problem 2: Container With Most Water

Given heights of vertical lines, find the max area of water a container can hold.

```python
def max_area(heights: list[int]) -> int:
    l, r = 0, len(heights) - 1
    best = 0
    while l < r:
        area = (r - l) * min(heights[l], heights[r])
        best = max(best, area)
        if heights[l] < heights[r]:
            l += 1
        else:
            r -= 1
    return best
```

- **Time:** O(n). **Space:** O(1).
- **Sample:** `[1,8,6,2,5,4,8,3,7]` → `49`.
- **Key insight:** move the smaller side; the larger side can't be the bottleneck.

### Problem 3: Minimum Window Substring

Given strings `s` and `t`, find the smallest substring of `s` containing all chars of `t`.

```python
def min_window(s: str, t: str) -> str:
    from collections import Counter
    need = Counter(t)
    have: dict[str, int] = {}
    required = len(need)
    satisfied = 0
    l = 0
    best = (0, float("inf"))
    for r, ch in enumerate(s):
        have[ch] = have.get(ch, 0) + 1
        if ch in need and have[ch] == need[ch]:
            satisfied += 1
        while satisfied == required:
            if r - l < best[1] - best[0]:
                best = (l, r)
            out = s[l]
            have[out] -= 1
            if out in need and have[out] < need[out]:
                satisfied -= 1
            l += 1
    return "" if best[1] == float("inf") else s[best[0]:best[1] + 1]
```

- **Time:** O(|s| + |t|). **Space:** O(|t|).
- **Sample:** `s="ADOBECODEBANC", t="ABC"` → `"BANC"`.

---

## 4. Debugging & tests (20 min)

### Bug 1: forgot to update state on shrink
**Symptom:** min_window returns a window that no longer contains `t`.
**Fix:** always do `have[out] -= 1` and re-check `satisfied`.

### Bug 2: last[ch] check doesn't account for window
**Symptom:** A naive version that doesn't check `last[ch] >= l` returns the wrong answer for `s="abba"`. With the buggy version, when we see the second `a` at index 3, we jump `l` back to `0` (where the first `a` is), but the first `a` is no longer in the window. Correct answer is `2` (e.g. `"ab"` or `"bb"`).
**Fix:** `if ch in last and last[ch] >= l`. The old index is outside the current window — only jump `l` if the old index is still in the window.

### Bug 3: max_area only moves the smaller side
**Symptom:** swap the conditional, area is wrong.
**Fix:** move the **smaller** height. Always. The math: if you move the larger, area can't increase.

### Bug 4: off-by-one in min_window
**Symptom:** substring is one char short.
**Fix:** return `s[best[0]:best[1] + 1]` (inclusive right), not `s[best[0]:best[1]]`.

### Tests
```python
def test_longest_substring():
    assert length_of_longest_substring("abcabcbb") == 3
    assert length_of_longest_substring("bbbbb") == 1
    assert length_of_longest_substring("") == 0
    assert length_of_longest_substring("abba") == 2  # classic gotcha

def test_max_area():
    assert max_area([1,8,6,2,5,4,8,3,7]) == 49
    assert max_area([1, 1]) == 1
    assert max_area([]) == 0

def test_min_window():
    assert min_window("ADOBECODEBANC", "ABC") == "BANC"
    assert min_window("a", "a") == "a"
    assert min_window("a", "aa") == ""
```

---

## 5. Mock interview practice (20 min)

**Q1 — "Why is sliding window O(n)?"**
> Each index enters the window once (when r expands) and leaves once (when l shrinks). 2n operations = O(n).

**Q2 — "How do you handle 'at most K' vs 'exactly K'?"**
> Exactly K = at_most(K) - at_most(K-1). Same trick for sliding window.

**Q3 — "When do you shrink first vs record first?"**
> Longest: shrink-while-invalid, record-after. Shortest: shrink-while-still-valid, record-before.

**Q4 — "Two pointers on unsorted input — work?"**
> Only if the comparison is positional (e.g., Dutch National Flag on colors). Otherwise, sort first.

**Q5 — "Why not just sort + binary search?"**
> You can. But sliding window gives O(n), binary search gives O(n log n), and sliding window preserves order.

---

## 6. Success criteria check
- [ ] I can implement sliding window in < 10 min.
- [ ] I can name 3 invariants a window can maintain.
- [ ] I can solve 3Sum in < 15 min.
- [ ] I can list 2 window flavors (longest vs shortest).

## 7. Grade yourself 0–10
| Area | Score |
|---|---|
| Correctness | /10 |
| Code quality | /10 |
| Debugging | /10 |
| Performance | /10 |
| Testing | /10 |
| Communication | /10 |
| **Total** | **/60** |

## 8. Coding assignment
**Longest Repeating Character Replacement** — given string `s` and integer `k`, you can change at most `k` characters. Find the longest substring you can make with all same chars.

### Rubric (0–10)
- 0: doesn't compile
- 4: works for `k=0`
- 6: handles `k > 0`
- 8: O(n) with sliding window + Counter
- 10: replaces Counter with a max-frequency tracker

### Solution
```python
def character_replacement(s: str, k: int) -> int:
    counts: dict[str, int] = {}
    l = 0
    best = 0
    max_freq = 0
    for r, ch in enumerate(s):
        counts[ch] = counts.get(ch, 0) + 1
        max_freq = max(max_freq, counts[ch])
        # If window too big, shrink
        while (r - l + 1) - max_freq > k:
            counts[s[l]] -= 1
            l += 1
        best = max(best, r - l + 1)
    return best
```

**Time: 90 min**
