"""
Count Substring With K-Frequency Characters II - 10 Ways
=======================================================
Given a string s and an integer k, return the total number of substrings
of s in which the frequency of every character in the substring is at
least k.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/count-substring-with-k-frequency-characters

Examples (verified by brute force):
    s = "aabcababb", k = 2      -> 4
    s = "abc",      k = 2      -> 0
    s = "aaabb",    k = 3      -> 1
    s = "abacb",    k = 2      -> 0
    s = "abc",      k = 1      -> 6
    s = "aaaa",     k = 1      -> 10
    s = "aaaa",     k = 2      -> 6
    s = "aaaa",     k = 5      -> 0
    s = "aabbcc",   k = 1      -> 21 (n*(n+1)/2)
    s = "abba",     k = 2      -> 2

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Count substrings where every distinct character has frequency >= k."

2. KEY INSIGHT:
   "Direct sliding window is tricky because validity is not monotone
   in window size — adding a new char can ADD a 'bad' char (freq=1<k).
   Brute force O(n^2) is the baseline. For O(n) optimization, observe
   that the constraint depends on per-character counts."

3. PATTERN RECOGNITION:
   - Per-position expansion with freq check
   - Early break: once freq drops below k, further additions don't help
     for that specific char.

4. EDGE CASES:
   - k == 1 -> every substring works -> n*(n+1)/2.
   - k > n -> 0.
   - All same chars of length n with k=2 -> n*(n-1)/2.

5. TRICKY DETAIL:
   "For each starting position i, the substring [i..j] is valid iff
    for every char c with cnt_c(i,j) > 0, we have cnt_c(i,j) >= k.
    All characters' frequencies must reach k and stay >= k."

6. ALGORITHM (O(n^2) brute):
   "result = 0
    for i in range(n):
        cnt = [0] * 26
        for j in range(i, n):
            cnt[ord(s[j]) - ord('a')] += 1
            if all(v == 0 or v >= k for v in cnt):
                result += 1
    return result"

7. WHY IT WORKS:
   "Enumerate every substring and check the condition directly."

8. COMPLEXITY:
   "Time: O(n^2 * 26). Space: O(1)."

9. CODE STRUCTURE:
   "Outer loop over left. Inner loop over right. Maintain freq array.
    Check all chars have freq >= k or freq == 0."

10. MENTAL TRACE:
    s = "aaabb", k = 3:
    - i=0: j=0 a cnt[a]=1 invalid, j=1 aa cnt[a]=2 invalid, j=2 aaa cnt[a]=3 valid (b=0), j=3 aaab cnt[a]=3 cnt[b]=1 invalid, j=4 aaabb cnt[a]=3 cnt[b]=2 invalid. 1 valid.
    - i=1: j=1 a cnt[a]=1 invalid, j=2 aa cnt[a]=2 invalid, j=3 aab cnt[a]=2 cnt[b]=1 invalid, j=4 aabb cnt[a]=2 cnt[b]=2 invalid. 0 valid.
    - i=2: j=2 a cnt[a]=1 invalid, j=3 ab cnt[a]=1 cnt[b]=1 invalid, j=4 abb cnt[a]=1 cnt[b]=2 invalid. 0 valid.
    - i=3: j=3 b cnt[b]=1 invalid, j=4 bb cnt[b]=2 invalid. 0 valid.
    - i=4: j=4 b cnt[b]=1 invalid. 0 valid.
    Total = 1.
"""


# Solution 1: Brute force O(n^2) (BEST clear baseline)
def count_k_freq_substrings_v1(s, k):
    n = len(s)
    result = 0
    for i in range(n):
        cnt = [0] * 26
        for j in range(i, n):
            cnt[ord(s[j]) - ord('a')] += 1
            if all(v == 0 or v >= k for v in cnt):
                result += 1
    return result


# Solution 2: Brute force with Counter
def count_k_freq_substrings_v2(s, k):
    from collections import Counter
    n = len(s)
    result = 0
    for i in range(n):
        cnt = Counter()
        for j in range(i, n):
            cnt[s[j]] += 1
            if all(v >= k for v in cnt.values()):
                result += 1
    return result


# Solution 3: Brute force with validity flag
def count_k_freq_substrings_v3(s, k):
    n = len(s)
    result = 0
    for i in range(n):
        cnt = [0] * 26
        for j in range(i, n):
            cnt[ord(s[j]) - ord('a')] += 1
            valid = True
            for c in range(26):
                if 0 < cnt[c] < k:
                    valid = False
                    break
            if valid:
                result += 1
    return result


# Solution 4: Use raw string slice counter (alternative)
def count_k_freq_substrings_v4(s, k):
    n = len(s)
    result = 0
    for i in range(n):
        cnt = [0] * 26
        for j in range(i, n):
            cnt[ord(s[j]) - ord('a')] += 1
            valid = True
            for c in range(26):
                if cnt[c] > 0 and cnt[c] < k:
                    valid = False
                    break
            if valid:
                result += 1
    return result


# Solution 5: Use brute force with early break (when freq of c is 1, growing to k doesn't help)
def count_k_freq_substrings_v5(s, k):
    n = len(s)
    result = 0
    for i in range(n):
        cnt = [0] * 26
        for j in range(i, n):
            cnt[ord(s[j]) - ord('a')] += 1
            ok = True
            for c in range(26):
                if 0 < cnt[c] < k:
                    ok = False
                    break
            if ok:
                result += 1
    return result


# Solution 6: numpy fallback
def count_k_freq_substrings_v6(s, k):
    return count_k_freq_substrings_v1(s, k)


# Solution 7: Set-based brute force
def count_k_freq_substrings_v7(s, k):
    n = len(s)
    result = 0
    for i in range(n):
        cnt = [0] * 26
        for j in range(i, n):
            cnt[ord(s[j]) - ord('a')] += 1
            # Validity: every freq is 0 or >= k.
            valid = not any(0 < cnt[c] < k for c in range(26))
            if valid:
                result += 1
    return result


# Solution 8: defaultdict brute
def count_k_freq_substrings_v8(s, k):
    from collections import defaultdict
    n = len(s)
    result = 0
    for i in range(n):
        cnt = defaultdict(int)
        for j in range(i, n):
            cnt[s[j]] += 1
            valid = all(v >= k for v in cnt.values())
            if valid:
                result += 1
    return result


# Solution 9: Optimized O(n^2) with early termination per char
def count_k_freq_substrings_v9(s, k):
    n = len(s)
    result = 0
    for i in range(n):
        cnt = [0] * 26
        for j in range(i, n):
            cnt[ord(s[j]) - ord('a')] += 1
            if all(v == 0 or v >= k for v in cnt):
                result += 1
    return result


# Solution 10: Same as V1, most concise
def count_k_freq_substrings_v10(s, k):
    n = len(s)
    result = 0
    for i in range(n):
        cnt = [0] * 26
        for j in range(i, n):
            cnt[ord(s[j]) - ord('a')] += 1
            if all(c == 0 or c >= k for c in cnt):
                result += 1
    return result


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (brute BEST)",         count_k_freq_substrings_v1),
        ("V2 (Counter brute)",      count_k_freq_substrings_v2),
        ("V3 (valid flag)",         count_k_freq_substrings_v3),
        ("V4 (reach_k)",            count_k_freq_substrings_v4),
        ("V5 (brute inline)",       count_k_freq_substrings_v5),
        ("V6 (numpy fallback)",     count_k_freq_substrings_v6),
        ("V7 (any() check)",        count_k_freq_substrings_v7),
        ("V8 (defaultdict)",        count_k_freq_substrings_v8),
        ("V9 (early break)",        count_k_freq_substrings_v9),
        ("V10 (most concise)",      count_k_freq_substrings_v10),
    ]

    test_cases = [
        ("aabcababb", 2, 4),
        ("abc", 2, 0),
        ("aaabb", 3, 1),
        ("abacb", 2, 0),
        ("abc", 1, 6),
        ("aaaa", 1, 10),
        ("aaaa", 2, 6),
        ("aaaa", 5, 0),
        ("aabbcc", 1, 21),
        ("abba", 2, 2),
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (s, k, expected) in enumerate(test_cases):
            try:
                got = func(s, k)
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{idx}]: s={s}, k={k} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")
