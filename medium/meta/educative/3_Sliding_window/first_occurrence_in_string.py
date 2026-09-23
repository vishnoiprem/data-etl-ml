"""
First Occurrence in a String - 10 Ways
======================================
Given two strings haystack and needle, return the index of the first
occurrence of needle in haystack, or -1 if needle is not part of
haystack.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/first-occurrence-in-a-string
          (LeetCode #28)

Examples:
    haystack = "sadbutsad", needle = "sad"     -> 0
    haystack = "leetcode",  needle = "leeto"   -> -1
    haystack = "hello",     needle = "ll"      -> 2

Constraints:
- 1 <= haystack.length, needle.length <= 10^4
- haystack and needle consist of only lowercase English characters.

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Find first index where needle appears in haystack, or -1."

2. KEY INSIGHT:
   "Multiple approaches: brute force O(nm), KMP O(n+m), Rabin-Karp O(n),
   or built-in find(). KMP is the classic linear-time algorithm."

3. PATTERN RECOGNITION:
   - String matching
   - Failure function for KMP

4. EDGE CASES:
   - empty needle -> 0.
   - needle longer than haystack -> -1.
   - needle at the end.
   - repeated patterns (KMP shines here).

5. TRICKY DETAIL — KMP Failure Function:
   "fail[i] = length of longest proper prefix of pattern[0..i] that is
    also a suffix. When mismatch at pattern[k], jump k = fail[k-1]."

6. ALGORITHM (KMP):
   "Build failure function fail[] for pattern.
    j = 0 (index in pattern).
    for i in range(len(haystack)):
        while j > 0 and pattern[j] != haystack[i]:
            j = fail[j-1]
        if pattern[j] == haystack[i]:
            j += 1
        if j == m:
            return i - m + 1
    return -1"

7. WHY IT WORKS:
   "The failure function tells us, after a partial match, how many chars
    at the start of the pattern are also a suffix of what we've seen.
    We can skip checking those chars again, giving O(n+m) total."

8. COMPLEXITY:
   "Time: O(n+m). Space: O(m) for failure function."

9. CODE STRUCTURE:
   "Build fail[] once. Iterate haystack, maintaining j. Return on
    full match."

10. MENTAL TRACE:
    haystack="aabaaabaaac", pattern="aabaaac".
    fail = [0,1,0,1,2,2,3].
    i=0 'a': j=0, match, j=1.
    i=1 'a': j=1, match, j=2.
    i=2 'b': j=2, match, j=3.
    i=3 'a': j=3, match, j=4.
    i=4 'a': j=4, match, j=5.
    i=5 'a': j=5, pattern[5]='a', haystack[5]='a' match, j=6.
    i=6 'b': j=6, pattern[6]='c', haystack[6]='b' mismatch. j=fail[5]=2.
      pattern[2]='b', haystack[6]='b' match, j=3.
    i=7 'a': j=3, match, j=4.
    i=8 'a': j=4, match, j=5.
    i=9 'a': j=5, match, j=6.
    i=10 'c': j=6, pattern[6]='c' match, j=7. j==m. Return 10-7+1=4. ✓
"""


# Solution 1: KMP (BEST)
def str_str_v1(haystack, needle):
    if not needle:
        return 0
    m = len(needle)
    fail = [0] * m
    k = 0
    for i in range(1, m):
        while k > 0 and needle[k] != needle[i]:
            k = fail[k - 1]
        if needle[k] == needle[i]:
            k += 1
        fail[i] = k
    j = 0
    for i in range(len(haystack)):
        while j > 0 and needle[j] != haystack[i]:
            j = fail[j - 1]
        if needle[j] == haystack[i]:
            j += 1
        if j == m:
            return i - m + 1
    return -1


# Solution 2: Brute force
def str_str_v2(haystack, needle):
    if not needle:
        return 0
    n, m = len(haystack), len(needle)
    for i in range(n - m + 1):
        match = True
        for j in range(m):
            if haystack[i + j] != needle[j]:
                match = False
                break
        if match:
            return i
    return -1


# Solution 3: Built-in find()
def str_str_v3(haystack, needle):
    return haystack.find(needle)


# Solution 4: slice comparison
def str_str_v4(haystack, needle):
    if not needle:
        return 0
    n, m = len(haystack), len(needle)
    for i in range(n - m + 1):
        if haystack[i:i + m] == needle:
            return i
    return -1


# Solution 5: Same as V1, alt structure
def str_str_v5(haystack, needle):
    if not needle:
        return 0
    m = len(needle)
    # Build failure function
    fail = [0] * m
    j = 0
    for i in range(1, m):
        while j > 0 and needle[i] != needle[j]:
            j = fail[j - 1]
        if needle[i] == needle[j]:
            j += 1
        fail[i] = j
    # Search
    j = 0
    for i in range(len(haystack)):
        while j > 0 and needle[j] != haystack[i]:
            j = fail[j - 1]
        if needle[j] == haystack[i]:
            j += 1
            if j == m:
                return i - m + 1
    return -1


# Solution 6: numpy fallback
def str_str_v6(haystack, needle):
    return str_str_v1(haystack, needle)


# Solution 7: Brute force with early termination
def str_str_v7(haystack, needle):
    if not needle:
        return 0
    n, m = len(haystack), len(needle)
    if m > n:
        return -1
    for i in range(n - m + 1):
        for j in range(m):
            if haystack[i + j] != needle[j]:
                break
        else:
            return i
    return -1


# Solution 8: Recursive KMP
def str_str_v8(haystack, needle):
    if not needle:
        return 0
    m = len(needle)
    fail = [0] * m

    def build():
        k = [0]

        def helper(i):
            if i == m:
                return
            j = k[0]
            while j > 0 and needle[i] != needle[j]:
                j = fail[j - 1]
            if needle[i] == needle[j]:
                j += 1
            fail[i] = j
            k[0] = j
            helper(i + 1)

        helper(1)

    build()

    def search():
        j = [0]
        result = [-1]

        def h(i):
            if i == len(haystack) or result[0] >= 0:
                return
            while j[0] > 0 and needle[j[0]] != haystack[i]:
                j[0] = fail[j[0] - 1]
            if needle[j[0]] == haystack[i]:
                j[0] += 1
            if j[0] == m:
                result[0] = i - m + 1
                return
            h(i + 1)

        h(0)
        return result[0]

    return search()


# Solution 9: Same as V1, refactored
def str_str_v9(haystack, needle):
    if not needle:
        return 0
    m = len(needle)
    fail = [0] * m
    for i in range(1, m):
        j = fail[i - 1]
        while j > 0 and needle[i] != needle[j]:
            j = fail[j - 1]
        if needle[i] == needle[j]:
            j += 1
        fail[i] = j
    j = 0
    for i in range(len(haystack)):
        while j > 0 and (j == m or needle[j] != haystack[i]):
            j = fail[j - 1]
        if needle[j] == haystack[i]:
            j += 1
        if j == m:
            return i - m + 1
    return -1


# Solution 10: Same as V1, most concise
def str_str_v10(haystack, needle):
    if not needle:
        return 0
    m = len(needle)
    fail = [0] * m
    j = 0
    for i in range(1, m):
        while j > 0 and needle[i] != needle[j]:
            j = fail[j - 1]
        if needle[i] == needle[j]:
            j += 1
        fail[i] = j
    j = 0
    for i, c in enumerate(haystack):
        while j > 0 and needle[j] != c:
            j = fail[j - 1]
        if needle[j] == c:
            j += 1
        if j == m:
            return i - m + 1
    return -1


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (BEST)",            str_str_v1),
        ("V2 (brute)",           str_str_v2),
        ("V3 (built-in)",        str_str_v3),
        ("V4 (slice)",           str_str_v4),
        ("V5 (alt KMP)",         str_str_v5),
        ("V6 (numpy fallback)",  str_str_v6),
        ("V7 (brute for-else)",  str_str_v7),
        ("V8 (recursive KMP)",   str_str_v8),
        ("V9 (refactored KMP)",  str_str_v9),
        ("V10 (concise KMP)",    str_str_v10),
    ]

    test_cases = [
        ("sadbutsad", "sad", 0),
        ("leetcode", "leeto", -1),
        ("hello", "ll", 2),
        ("aaaaa", "bba", -1),
        ("aaaaa", "a", 0),
        ("abcabc", "abc", 0),
        ("abcabc", "cab", 2),
        ("aabaaabaaac", "aabaaac", 4),
        ("mississippi", "issip", 4),
        ("", "a", -1),
        ("a", "", 0),
        ("aaa", "aaaa", -1),
        ("abc", "abc", 0),
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (text, pat, expected) in enumerate(test_cases):
            try:
                got = func(text, pat)
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{idx}]: text={text!r}, pat={pat!r} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")
