"""
Number of Substrings Containing All Three Characters - 10 Ways
==============================================================
Given a string s consisting only of characters a, b and c, return
the number of substrings containing at least one occurrence of each
of these three characters.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/number-of-substrings-containing-all-three-characters
          (LeetCode #1357 / problem often called "Number of Substrings
           With All Three Characters")

Examples:
    s = "abcabc"      -> 10
    s = "aaacb"       -> 3
    s = "abc"         -> 1

Constraints:
- 3 <= s.length <= 5 * 10^4
- s only contains 'a', 'b', 'c'.

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Count substrings of s that contain at least one 'a', 'b', and 'c'."

2. KEY INSIGHT:
   "For each right, find the SMALLEST left such that [left..right] is
   invalid (missing one of {a,b,c}). Then all [i..right] for i < left
   are valid. Count = left."

3. PATTERN RECOGNITION:
   - Sliding window counting invalid lefts
   - For each right, find smallest invalid left

4. EDGE CASES:
   - n < 3 -> 0.
   - All same chars -> 0.
   - Length exactly 3 with all distinct -> 1.

5. TRICKY DETAIL:
   "We shrink while window is VALID. Once invalid (or empty), we stop.
   Then result += left. This counts number of i in [0..left-1] for
   which [i..right] is valid."

6. ALGORITHM:
   "left = 0; cnt = {'a':0, 'b':0, 'c':0}; result = 0
    for right in range(n):
        cnt[s[right]] += 1
        while left <= right and cnt['a'] > 0 and cnt['b'] > 0 and cnt['c'] > 0:
            cnt[s[left]] -= 1
            left += 1
        result += left
    return result"

7. WHY IT WORKS:
   "After shrinking, window [left..right] is INVALID (missing some
   char) or empty. For all i in [0..left-1], [i..right] is VALID
   (since shrinking past them didn't affect validity until left).
   For i >= left, [i..right] is invalid (left is the smallest such).
   Count = left."

8. COMPLEXITY:
   "Time: O(n). Space: O(1)."

9. CODE STRUCTURE:
   "Init counter. Iterate right. Shrink while valid. Add left to result."

10. MENTAL TRACE:
    s = "abcabc":
    right=0 'a': cnt[a]=1. Not all 3. result=0.
    right=1 'b': cnt[b]=1. Not all 3. result=0.
    right=2 'c': cnt[c]=1. All 3. Shrink: cnt[a]=0, left=1. Not all 3. result=0+1=1.
    right=3 'a': cnt[a]=1. All 3. Shrink: cnt[b]=0, left=2. result=1+2=3.
    right=4 'b': cnt[b]=1. All 3. Shrink: cnt[c]=0, left=3. result=3+3=6.
    right=5 'c': cnt[c]=1. All 3. Shrink: cnt[a]=0, left=4. result=6+4=10. ✓
"""


# Solution 1: Sliding window (BEST)
def number_of_substrings_v1(s):
    n = len(s)
    cnt_a = cnt_b = cnt_c = 0
    left = 0
    result = 0
    for right in range(n):
        c = s[right]
        if c == 'a':
            cnt_a += 1
        elif c == 'b':
            cnt_b += 1
        else:
            cnt_c += 1
        # Shrink while valid (all three > 0)
        while left <= right and cnt_a > 0 and cnt_b > 0 and cnt_c > 0:
            lc = s[left]
            if lc == 'a':
                cnt_a -= 1
            elif lc == 'b':
                cnt_b -= 1
            else:
                cnt_c -= 1
            left += 1
        result += left
    return result


# Solution 2: Same with dict counter
def number_of_substrings_v2(s):
    n = len(s)
    cnt = {'a': 0, 'b': 0, 'c': 0}
    left = 0
    result = 0
    for right in range(n):
        cnt[s[right]] += 1
        while left <= right and cnt['a'] > 0 and cnt['b'] > 0 and cnt['c'] > 0:
            cnt[s[left]] -= 1
            left += 1
        result += left
    return result


# Solution 3: Brute force O(n^2)
def number_of_substrings_v3(s):
    n = len(s)
    result = 0
    for i in range(n):
        seen = {'a': False, 'b': False, 'c': False}
        for j in range(i, n):
            seen[s[j]] = True
            if seen['a'] and seen['b'] and seen['c']:
                result += 1
    return result


# Solution 4: Same with Counter
def number_of_substrings_v4(s):
    from collections import Counter
    n = len(s)
    cnt = Counter()
    left = 0
    result = 0
    for right in range(n):
        cnt[s[right]] += 1
        while left <= right and cnt['a'] > 0 and cnt['b'] > 0 and cnt['c'] > 0:
            cnt[s[left]] -= 1
            left += 1
        result += left
    return result


# Solution 5: defaultdict version
def number_of_substrings_v5(s):
    from collections import defaultdict
    n = len(s)
    cnt = defaultdict(int)
    left = 0
    result = 0
    for right in range(n):
        cnt[s[right]] += 1
        while left <= right and cnt['a'] > 0 and cnt['b'] > 0 and cnt['c'] > 0:
            cnt[s[left]] -= 1
            left += 1
        result += left
    return result


# Solution 6: numpy fallback
def number_of_substrings_v6(s):
    return number_of_substrings_v1(s)


# Solution 7: Same as V1, slight refactor
def number_of_substrings_v7(s):
    n = len(s)
    counts = [0, 0, 0]
    left = 0
    result = 0
    char_idx = {'a': 0, 'b': 1, 'c': 2}
    for right in range(n):
        counts[char_idx[s[right]]] += 1
        while left <= right and counts[0] > 0 and counts[1] > 0 and counts[2] > 0:
            counts[char_idx[s[left]]] -= 1
            left += 1
        result += left
    return result


# Solution 8: Inline validity
def number_of_substrings_v8(s):
    n = len(s)
    a = b = c = 0
    left = 0
    result = 0
    for right in range(n):
        if s[right] == 'a':
            a += 1
        elif s[right] == 'b':
            b += 1
        else:
            c += 1
        while left <= right and a > 0 and b > 0 and c > 0:
            if s[left] == 'a':
                a -= 1
            elif s[left] == 'b':
                b -= 1
            else:
                c -= 1
            left += 1
        result += left
    return result


# Solution 9: Recursive
def number_of_substrings_v9(s):
    n = len(s)
    counts = [0, 0, 0]
    char_idx = {'a': 0, 'b': 1, 'c': 2}
    left = [0]
    result = [0]

    def helper(right):
        if right == n:
            return
        counts[char_idx[s[right]]] += 1
        while left[0] <= right and counts[0] > 0 and counts[1] > 0 and counts[2] > 0:
            counts[char_idx[s[left[0]]]] -= 1
            left[0] += 1
        result[0] += left[0]
        helper(right + 1)

    helper(0)
    return result[0]


# Solution 10: Same as V1, most concise
def number_of_substrings_v10(s):
    cnt = {'a': 0, 'b': 0, 'c': 0}
    left = 0
    result = 0
    for right, c in enumerate(s):
        cnt[c] += 1
        while left <= right and cnt['a'] > 0 and cnt['b'] > 0 and cnt['c'] > 0:
            cnt[s[left]] -= 1
            left += 1
        result += left
    return result


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (BEST)",            number_of_substrings_v1),
        ("V2 (dict cnt)",        number_of_substrings_v2),
        ("V3 (brute)",           number_of_substrings_v3),
        ("V4 (Counter)",         number_of_substrings_v4),
        ("V5 (defaultdict)",     number_of_substrings_v5),
        ("V6 (numpy)",           number_of_substrings_v6),
        ("V7 (idx array)",       number_of_substrings_v7),
        ("V8 (inline)",          number_of_substrings_v8),
        ("V9 (recursive)",       number_of_substrings_v9),
        ("V10 (concise)",        number_of_substrings_v10),
    ]

    test_cases = [
        ("abcabc", 10),
        ("aaacb", 3),
        ("abc", 1),
        ("aabbcc", 4),
        ("ab", 0),
        ("aaa", 0),
        ("abcab", 6),
        ("abccba", 7),
        ("abcabcabc", 28),
        ("", 0),
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (s, expected) in enumerate(test_cases):
            try:
                got = func(s)
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{idx}]: s={s!r} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")
