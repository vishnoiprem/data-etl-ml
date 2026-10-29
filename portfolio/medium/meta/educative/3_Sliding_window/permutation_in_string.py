"""
Permutation in String - 10 Ways
==============================
Given two strings s1 and s2, return true if s2 contains a permutation
of s1. In other words, return true if one of s1's permutations is a
substring of s2.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/permutation-in-a-string
          (LeetCode #567)

Examples:
    s1 = "ab", s2 = "eidbaooo"             -> True
        ("ba" is a permutation of "ab" appearing in s2)
    s1 = "ab", s2 = "eidboaoo"             -> False
    s1 = "a",   s2 = "leetcab"              -> True
    s1 = "abc", s2 = "bbbca"                -> True
        ("bca" is a permutation)
    s1 = "adc", s2 = "dcda"                 -> True

Constraints:
- 1 <= s1.length, s2.length <= 10^4
- s1 and s2 consist of lowercase English letters

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Check if s2 contains any substring that's a permutation of s1."

2. KEY INSIGHT:
   "A permutation of s1 has the same character counts as s1. So we need
   a fixed-size sliding window over s2 of size |s1|, comparing its
   character counts to s1's counts."

3. PATTERN RECOGNITION:
   - Fixed-size sliding window
   - Character count comparison (Counter diff)

4. EDGE CASES:
   - |s1| > |s2| -> False.
   - empty input.
   - all same chars: must match length.

5. TRICKY DETAIL:
   "Track 'matches' = number of chars where cnt_window[c] == cnt_s1[c].
   When matches == 26 (or unique chars), window is a permutation."

6. ALGORITHM:
   "if len(s1) > len(s2): return False
    s1_count = Counter(s1)
    window_count = Counter(s2[:len(s1)])
    if window_count == s1_count: return True
    for i in range(len(s1), len(s2)):
        window_count[s2[i]] += 1
        window_count[s2[i - len(s1)]] -= 1
        if window_count[s2[i - len(s1)]] == 0:
            del window_count[s2[i - len(s1)]]
        if window_count == s1_count: return True
    return False"

7. WHY IT WORKS:
   "Each iteration represents one fixed window of size |s1|. We slide
   it forward by 1, updating the character counts in O(1) and checking
   equality in O(unique chars) amortized."

8. COMPLEXITY:
   "Time: O(n) where n = |s2|. Space: O(1) (Counter of bounded size)."

9. CODE STRUCTURE:
   "Init window. Slide. Compare. Return result."

10. MENTAL TRACE:
    s1="ab", s2="eidbaooo".
    window = "ei" = {e:1, i:1}. s1 count = {a:1, b:1}. Not equal.
    Slide: window = "id". Different.
    Slide: window = "db". {d:1, b:1}. Not equal.
    Slide: window = "ba". {b:1, a:1}. Equal! True. ✓
"""


# Solution 1: Fixed sliding window with Counter (BEST)
def check_inclusion_v1(s1, s2):
    from collections import Counter
    n, m = len(s1), len(s2)
    if n > m:
        return False
    need = Counter(s1)
    window = Counter(s2[:n])
    if window == need:
        return True
    for i in range(n, m):
        window[s2[i]] += 1
        out = s2[i - n]
        window[out] -= 1
        if window[out] == 0:
            del window[out]
        if window == need:
            return True
    return False


# Solution 2: Optimized with matches counter (26 chars)
def check_inclusion_v2(s1, s2):
    if len(s1) > len(s2):
        return False
    need = [0] * 26
    for c in s1:
        need[ord(c) - ord('a')] += 1
    window = [0] * 26
    for c in s2[:len(s1)]:
        window[ord(c) - ord('a')] += 1
    if window == need:
        return True
    for i in range(len(s1), len(s2)):
        window[ord(s2[i]) - ord('a')] += 1
        out_idx = ord(s2[i - len(s1)]) - ord('a')
        window[out_idx] -= 1
        if window == need:
            return True
    return False


# Solution 3: Optimized with 'matches' counter
def check_inclusion_v3(s1, s2):
    if len(s1) > len(s2):
        return False
    need = [0] * 26
    window = [0] * 26
    for c in s1:
        need[ord(c) - ord('a')] += 1
    for c in s2[:len(s1)]:
        window[ord(c) - ord('a')] += 1
    matches = sum(1 for i in range(26) if window[i] == need[i])
    if matches == 26:
        return True
    for i in range(len(s1), len(s2)):
        in_idx = ord(s2[i]) - ord('a')
        window[in_idx] += 1
        if window[in_idx] == need[in_idx]:
            matches += 1
        elif window[in_idx] == need[in_idx] + 1:
            matches -= 1
        out_idx = ord(s2[i - len(s1)]) - ord('a')
        window[out_idx] -= 1
        if window[out_idx] == need[out_idx]:
            matches += 1
        elif window[out_idx] == need[out_idx] - 1:
            matches -= 1
        if matches == 26:
            return True
    return False


# Solution 4: Brute force O(n * m)
def check_inclusion_v4(s1, s2):
    from collections import Counter
    if len(s1) > len(s2):
        return False
    need = Counter(s1)
    for i in range(len(s2) - len(s1) + 1):
        win = s2[i:i + len(s1)]
        if Counter(win) == need:
            return True
    return False


# Solution 5: defaultdict sliding window
def check_inclusion_v5(s1, s2):
    if len(s1) > len(s2):
        return False
    from collections import defaultdict
    need = defaultdict(int)
    for c in s1:
        need[c] += 1
    window = defaultdict(int)
    for c in s2[:len(s1)]:
        window[c] += 1
    if dict(window) == dict(need):
        return True
    for i in range(len(s1), len(s2)):
        window[s2[i]] += 1
        window[s2[i - len(s1)]] -= 1
        if window[s2[i - len(s1)]] == 0:
            del window[s2[i - len(s1)]]
        if dict(window) == dict(need):
            return True
    return False


# Solution 6: numpy fallback
def check_inclusion_v6(s1, s2):
    return check_inclusion_v1(s1, s2)


# Solution 7: Anagram-style (same as V1)
def check_inclusion_v7(s1, s2):
    from collections import Counter
    if len(s1) > len(s2):
        return False
    need = Counter(s1)
    window = Counter()
    for i, c in enumerate(s2):
        window[c] += 1
        if i >= len(s1):
            out = s2[i - len(s1)]
            window[out] -= 1
            if window[out] == 0:
                del window[out]
        if i >= len(s1) - 1 and window == need:
            return True
    return False


# Solution 8: dict.get sliding window
def check_inclusion_v8(s1, s2):
    if len(s1) > len(s2):
        return False
    need = {}
    for c in s1:
        need[c] = need.get(c, 0) + 1
    window = {}
    for i, c in enumerate(s2):
        window[c] = window.get(c, 0) + 1
        if i >= len(s1):
            out = s2[i - len(s1)]
            window[out] -= 1
            if window[out] == 0:
                del window[out]
        if i >= len(s1) - 1 and window == need:
            return True
    return False


# Solution 9: Same as V2 with cleaner variable names
def check_inclusion_v9(s1, s2):
    if len(s1) > len(s2):
        return False
    need = [0] * 26
    for c in s1:
        need[ord(c) - ord('a')] += 1
    window = [0] * 26
    n = len(s1)
    for i in range(n):
        window[ord(s2[i]) - ord('a')] += 1
    if window == need:
        return True
    for i in range(n, len(s2)):
        window[ord(s2[i]) - ord('a')] += 1
        window[ord(s2[i - n]) - ord('a')] -= 1
        if window == need:
            return True
    return False


# Solution 10: Same as V1, most concise
def check_inclusion_v10(s1, s2):
    from collections import Counter
    n = len(s1)
    if n > len(s2):
        return False
    need = Counter(s1)
    win = Counter(s2[:n])
    if win == need:
        return True
    for i in range(n, len(s2)):
        win[s2[i]] += 1
        out = s2[i - n]
        win[out] -= 1
        if win[out] == 0:
            del win[out]
        if win == need:
            return True
    return False


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (BEST)",          check_inclusion_v1),
        ("V2 (26 array)",      check_inclusion_v2),
        ("V3 (matches)",       check_inclusion_v3),
        ("V4 (brute)",         check_inclusion_v4),
        ("V5 (defaultdict)",   check_inclusion_v5),
        ("V6 (numpy)",         check_inclusion_v6),
        ("V7 (anagram style)", check_inclusion_v7),
        ("V8 (dict.get)",      check_inclusion_v8),
        ("V9 (clean names)",   check_inclusion_v9),
        ("V10 (concise)",      check_inclusion_v10),
    ]

    test_cases = [
        ("ab", "eidbaooo", True),
        ("ab", "eidboaoo", False),
        ("a", "leetcab", True),
        ("abc", "bbbca", True),
        ("adc", "dcda", True),
        ("hello", "ooolleoooleh", False),
        ("ab", "ab", True),
        ("ab", "a", False),
        ("abcd", "dcbaabdc", True),
        ("trinitrophenylmethylnitramine", "trinitrophenylmethylnitramine", True),
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (s1, s2, expected) in enumerate(test_cases):
            try:
                got = func(s1, s2)
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{idx}]: s1={s1!r}, s2={s2!r} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")
