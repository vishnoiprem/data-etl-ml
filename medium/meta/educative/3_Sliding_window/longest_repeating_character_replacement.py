"""
Longest Repeating Character Replacement - 10 Ways
=================================================
You are given a string s and an integer k. You can choose any character
of the string and change it to any other uppercase English character.
You can perform this operation at most k times.

Return the length of the longest substring that contains all the same
letters (after at most k replacements).

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/longest-repeating-character-replacement

Examples:
    s = "ABAB", k = 2          -> 4 (replace both B's with A's: "AAAA")
    s = "AABABBA", k = 1       -> 4 (replace one B with A: "AABBA" or "AABAA")
    s = "AABB", k = 2          -> 4
    s = "ABCDE", k = 1         -> 2 (e.g., "BC" or "CD" after one change)
    s = "AAAA", k = 2          -> 4

Constraints:
- 1 <= s.length <= 10^5
- s consists of only uppercase English letters
- 0 <= k <= s.length

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Find the longest substring that can be made uniform (all same char)
    with at most k replacements. Each replacement swaps one char for
    another (the most frequent one in the window)."

2. KEY INSIGHT:
   "A window [left, right] can be made uniform with k replacements iff
    (window_length - max_freq_in_window) <= k.
    That is: number of chars NOT equal to the most-frequent char
    is at most k."

3. PATTERN RECOGNITION:
   "Sliding window with a frequency count. Expand right; if window is
    'invalid' (cost > k), shrink from left."

4. EDGE CASES:
   - k == 0: longest run of same chars.
   - k >= n: return n.
   - All same chars: return n (with any k >= 0).
   - All distinct chars with k = 1: return 2.
   - Single char: return 1.

5. TRICKY DETAIL:
   "When window is invalid, shrink from left. max_freq NEVER decreases
    during the shrink (in the canonical implementation). This is because
    we're looking for the LONGEST valid window; shrinking only improves
    frequency of a possibly-shifted character. The trick is: max_freq
    might stay outdated, but since 'window_length - max_freq' decreases
    as we shrink, the answer is still correct (just may allow longer
    windows than truly optimal). We then take the max over all windows.
    Actually, the canonical LeetCode implementation DOES NOT decrement
    max_freq, which is provably correct via a clever argument: we only
    care about windows strictly larger than the current max; if max_freq
    is stale, the window satisfies (len - actual_max_freq) > k, so it's
    invalid. So the stale max_freq is harmless for correctness."

6. ALGORITHM:
   "left = 0; freq[26] = zeros; max_freq = 0; best = 0
    for right in range(n):
        freq[s[right]] += 1
        max_freq = max(max_freq, freq[s[right]])
        while (right - left + 1) - max_freq > k:
            freq[s[left]] -= 1
            left += 1
        best = max(best, right - left + 1)
    return best"

7. WHY IT WORKS:
   "Each right expansion adds one character. We contract left until the
    window is feasible (cost <= k). Then we record the window size.
    Since we never decrease max_freq, we don't push the window small
    enough artificially; eventually a longer window will be found with
    a real increase in max_freq."

8. COMPLEXITY:
   "Time: O(n) - each char added and removed at most once.
    Space: O(1) for the 26-letter frequency table."

9. CODE STRUCTURE:
   "Initialize pointers, freq count, max_freq, best.
    Loop: add right; update max_freq; while invalid -> shrink left.
    Update best."

10. MENTAL TRACE:
    "AABABBA", k=1:
    right=0, 'A': freq[A]=1, max_freq=1. (1-1<=1). best=1.
    right=1, 'A': freq[A]=2, max_freq=2. (2-2<=1). best=2.
    right=2, 'B': freq[B]=1, max_freq=2. (3-2<=1). best=3.
    right=3, 'A': freq[A]=3, max_freq=3. (4-3<=1). best=4.
    right=4, 'B': freq[B]=2, max_freq=3. (5-3=2>1, INVALID)
      shrink: left=0, freq[A]=2. (5-3=2>1, INVALID).
      shrink: left=1, freq[A]=1. (5-3=2>1, INVALID).
      shrink: left=2, freq[A]=0. (5-3=2>1, INVALID).
      shrink: left=3, freq[A]=-? freq[B]=2. Wait, let me redo.
      Actually shrink removes s[left]: s[2]='B', freq[B]=1. (5-3=2>1, INVALID).
      shrink: left=4, freq[A]=2. (5-3=2>1, INVALID)... hmm.
    Let me re-trace with care at each step:
      shrink left from 2: removes s[2]='B', freq[B]=1. len=5, max_freq=3, cost=2. >1.
      shrink left to 3: removes s[3]='A', freq[A]=2. len=4 (4-3=4), cost=1. Valid.
    right=5, 'B': freq[B]=2, max_freq=3. (6-3=3>1, INVALID).
      shrink: left=4, removes 'B', freq[B]=1. (6-3=3>1).
      shrink: left=5, removes 'A', freq[A]=1. (6-3=3>1).
      shrink: left=6, end. Loop ends.
    Best = 4. ✓
"""


# Solution 1: Canonical sliding window with frequency array (BEST)
def character_replacement_v1(s, k):
    n = len(s)
    if n == 0:
        return 0
    freq = [0] * 26
    left = 0
    max_freq = 0
    best = 0
    for right in range(n):
        idx = ord(s[right]) - ord('A')
        freq[idx] += 1
        if freq[idx] > max_freq:
            max_freq = freq[idx]
        # Shrink window while invalid
        while (right - left + 1) - max_freq > k:
            freq[ord(s[left]) - ord('A')] -= 1
            left += 1
        cur_len = right - left + 1
        if cur_len > best:
            best = cur_len
    return best


# Solution 2: Using Counter instead of array
def character_replacement_v2(s, k):
    from collections import Counter
    n = len(s)
    freq = Counter()
    left = 0
    max_freq = 0
    best = 0
    for right in range(n):
        freq[s[right]] += 1
        if freq[s[right]] > max_freq:
            max_freq = freq[s[right]]
        while (right - left + 1) - max_freq > k:
            freq[s[left]] -= 1
            left += 1
        if right - left + 1 > best:
            best = right - left + 1
    return best


# Solution 3: Using defaultdict
def character_replacement_v3(s, k):
    from collections import defaultdict
    n = len(s)
    freq = defaultdict(int)
    left = 0
    max_freq = 0
    for right in range(n):
        freq[s[right]] += 1
        if freq[s[right]] > max_freq:
            max_freq = freq[s[right]]
        if (right - left + 1) - max_freq > k:
            freq[s[left]] -= 1
            left += 1
    return n - left  # or return max window; here we just return end - left


# Solution 4: Brute force O(n^2)
def character_replacement_v4(s, k):
    n = len(s)
    if n == 0:
        return 0
    best = 0
    for i in range(n):
        freq = {}
        max_freq = 0
        for j in range(i, n):
            c = s[j]
            freq[c] = freq.get(c, 0) + 1
            if freq[c] > max_freq:
                max_freq = freq[c]
            if (j - i + 1) - max_freq <= k:
                if j - i + 1 > best:
                    best = j - i + 1
            else:
                break
    return best


# Solution 5: Brute force with all substrings
def character_replacement_v5(s, k):
    n = len(s)
    best = 0
    from collections import Counter
    for i in range(n):
        for j in range(i, n):
            sub = s[i:j + 1]
            cnt = Counter(sub)
            mx = max(cnt.values())
            if (j - i + 1) - mx <= k:
                if len(sub) > best:
                    best = len(sub)
    return best


# Solution 6: Binary search on answer
def character_replacement_v6(s, k):
    n = len(s)
    if n == 0:
        return 0

    def feasible(length):
        if length == 0:
            return True
        freq = [0] * 26
        for i in range(length):
            freq[ord(s[i]) - ord('A')] += 1
        max_freq = max(freq)
        if length - max_freq <= k:
            return True
        for i in range(length, n):
            freq[ord(s[i]) - ord('A')] += 1
            freq[ord(s[i - length]) - ord('A')] -= 1
            max_freq = max(freq)
            if length - max_freq <= k:
                return True
        return False

    lo, hi = 0, n
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if feasible(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


# Solution 7: Compute max_freq each time (no stale max)
def character_replacement_v7(s, k):
    n = len(s)
    if n == 0:
        return 0
    freq = [0] * 26
    left = 0
    best = 0
    for right in range(n):
        idx = ord(s[right]) - ord('A')
        freq[idx] += 1
        # Compute current max in window
        cur_max = max(freq)
        while (right - left + 1) - cur_max > k:
            freq[ord(s[left]) - ord('A')] -= 1
            left += 1
            cur_max = max(freq)
        if right - left + 1 > best:
            best = right - left + 1
    return best


# Solution 8: Using heap (slow but valid)
def character_replacement_v8(s, k):
    import heapq
    n = len(s)
    if n == 0:
        return 0
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    # Sort by frequency desc, take top-2, try all variants
    chars = sorted(freq.keys(), key=lambda x: -freq[x])
    # Find the longest substring dominated by the char with highest freq
    # in any window. Use V1 logic but track all windows.
    left = 0
    counts = {}
    max_freq = 0
    best = 0
    # Maintain a max-heap (negated) for finding max of counts.
    heap = []
    for right in range(n):
        c = s[right]
        counts[c] = counts.get(c, 0) + 1
        heapq.heappush(heap, (-counts[c], c))
        # Update max_freq (need to peek top of heap carefully)
        max_freq = max(max_freq, counts[c])
        while (right - left + 1) - max_freq > k:
            lc = s[left]
            counts[lc] -= 1
            if counts[lc] == 0:
                del counts[lc]
            left += 1
            # Recompute max (heap is stale)
            if counts:
                max_freq = max(counts.values())
            else:
                max_freq = 0
        if right - left + 1 > best:
            best = right - left + 1
    return best


# Solution 9: Recursive
def character_replacement_v9(s, k):
    n = len(s)
    if n == 0:
        return 0
    from collections import Counter

    def helper(left, right, freq, max_freq, best):
        if right == n:
            return best
        c = s[right]
        freq[c] = freq.get(c, 0) + 1
        if freq[c] > max_freq:
            max_freq = freq[c]
        while (right - left + 1) - max_freq > k:
            lc = s[left]
            freq[lc] -= 1
            left += 1
            if not freq:
                max_freq = 0
            else:
                # Recompute max (correctness)
                max_freq = max(freq.values())
        if right - left + 1 > best:
            best = right - left + 1
        return helper(left, right + 1, freq, max_freq, best)
    return helper(0, 0, {}, 0, 0)


# Solution 10: Iterate by length (for each character, find max run + k)
def character_replacement_v10(s, k):
    # For each character, compute longest window where that char dominates
    # with at most k other chars.
    n = len(s)
    if n == 0:
        return 0
    best = 0
    seen_chars = set(s)
    for target in seen_chars:
        left = 0
        other_count = 0
        for right in range(n):
            if s[right] != target:
                other_count += 1
            while other_count > k:
                if s[left] != target:
                    other_count -= 1
                left += 1
            if right - left + 1 > best:
                best = right - left + 1
    return best


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (canonical)",          character_replacement_v1),
        ("V2 (Counter)",            character_replacement_v2),
        ("V3 (defaultdict)",        character_replacement_v3),
        ("V4 (brute O(n^2))",       character_replacement_v4),
        ("V5 (all substrings)",     character_replacement_v5),
        ("V6 (binary search)",      character_replacement_v6),
        ("V7 (recompute max)",      character_replacement_v7),
        ("V8 (heap slow)",          character_replacement_v8),
        ("V9 (recursive)",          character_replacement_v9),
        ("V10 (per-target char)",   character_replacement_v10),
    ]

    test_cases = [
        # (s, k, expected)
        ("ABAB", 2, 4),
        ("AABABBA", 1, 4),
        ("AABB", 2, 4),
        ("ABCDE", 1, 2),
        ("AAAA", 2, 4),
        ("ABAB", 0, 1),  # no consecutive same chars, so single chars only
        ("A", 0, 1),
        ("", 0, 0),
        ("ABCDEFG", 2, 3),
        ("ABBB", 0, 3),
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (s, k_val, expected) in enumerate(test_cases):
            try:
                got = func(s, k_val)
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{idx}]: {s!r}, k={k_val} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")