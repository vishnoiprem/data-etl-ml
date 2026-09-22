"""
Merge Strings Alternately - 10 Ways
===================================
Given two strings word1 and word2, merge them by interleaving characters in
alternating order starting with word1. If one string is longer, append the
remaining characters.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/merge-strings-alternately

Examples:
    "abc", "pqr"   -> "apbqcr"
    "ab",  "pqrs"  -> "apbqrs"
    "abcd","pq"    -> "apbqcd"

Constraints:
- 1 <= word1.length, word2.length <= 100
- Consists of lowercase English letters

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Interleave chars from word1 and word2 starting with word1's first char.
    Append remaining chars from the longer string."

2. KEY INSIGHT:
   "Two-pointer: i walks word1, j walks word2. At each step, append one
    from each until one is exhausted; then append the rest."

3. PATTERN RECOGNITION:
   "Two-pointer with sequential output. Walk both pointers at same rate
    until one runs out, then drain the other."

4. EDGE CASES:
   - Equal length -> simple interleave.
   - word1 empty -> return word2.
   - word2 empty -> return word1.
   - Both empty -> "".
   - word1 much longer -> drain word1 after word2 exhausted.

5. TRICKY DETAIL:
   "Always start with word1. If word1 is exhausted first, word2's
    remaining is appended (not interleaved further)."

6. ALGORITHM:
   "i, j = 0, 0; result = []
    while i < len(word1) and j < len(word2):
        result.append(word1[i]); i += 1
        result.append(word2[j]); j += 1
    if i < len(word1): result += word1[i:]
    if j < len(word2): result += word2[j:]
    return ''.join(result)"

7. WHY TWO-POINTERS:
   "Single linear pass through both strings. No look-ahead needed.
    Each pointer advances at most once per step."

8. COMPLEXITY:
   "Time: O(n + m) where n = len(word1), m = len(word2).
    Space: O(n + m) for the result."

9. CODE STRUCTURE:
   "Two while loops: alternating, then drain."

10. MENTAL TRACE:
    "abc", "pqr":
    i=0, j=0: result += 'a','p'; i=1, j=1
    i=1, j=1: result += 'b','q'; i=2, j=2
    i=2, j=2: result += 'c','r'; i=3, j=3
    Both exhausted. Result: "apbqcr" ✓
"""


# Solution 1: Canonical two-pointer with append (BEST)
def merge_alt_v1(word1, word2):
    result = []
    i, j = 0, 0
    while i < len(word1) and j < len(word2):
        result.append(word1[i])
        result.append(word2[j])
        i += 1
        j += 1
    while i < len(word1):
        result.append(word1[i])
        i += 1
    while j < len(word2):
        result.append(word2[j])
        j += 1
    return "".join(result)


# Solution 2: Using zip + leftover
def merge_alt_v2(word1, word2):
    result = []
    for a, b in zip(word1, word2):
        result.append(a)
        result.append(b)
    # Add leftover from the longer string
    if len(word1) > len(word2):
        result.append(word1[len(word2):])
    elif len(word2) > len(word1):
        result.append(word2[len(word1):])
    return "".join(result)


# Solution 3: Using itertools.zip_longest
def merge_alt_v3(word1, word2):
    from itertools import zip_longest
    result = []
    for a, b in zip_longest(word1, word2, fillvalue=""):
        result.append(a)
        result.append(b)
    return "".join(result)


# Solution 4: Using zip + concatenation
def merge_alt_v4(word1, word2):
    inter = "".join(a + b for a, b in zip(word1, word2))
    return inter + word1[len(word2):] + word2[len(word1):]


# Solution 5: Using a generator + slice
def merge_alt_v5(word1, word2):
    n, m = len(word1), len(word2)
    parts = []
    for i in range(min(n, m)):
        parts.append(word1[i])
        parts.append(word2[i])
    if n > m:
        parts.append(word1[m:])
    elif m > n:
        parts.append(word2[n:])
    return "".join(parts)


# Solution 6: Recursive
def merge_alt_v6(word1, word2):
    if not word1:
        return word2
    if not word2:
        return word1
    return word1[0] + word2[0] + merge_alt_v6(word1[1:], word2[1:])


# Solution 7: Stack-based
def merge_alt_v7(word1, word2):
    s1 = list(word1)
    s2 = list(word2)
    result = []
    while s1 and s2:
        result.append(s1.pop(0))
        result.append(s2.pop(0))
    result.extend(s1)
    result.extend(s2)
    return "".join(result)


# Solution 8: Two-pointer with explicit slice merging
def merge_alt_v8(word1, word2):
    n, m = len(word1), len(word2)
    if n == 0:
        return word2
    if m == 0:
        return word1
    inter = "".join([word1[i] + word2[i] for i in range(min(n, m))])
    return inter + word1[min(n, m):] + word2[min(n, m):]


# Solution 9: One-liner with zip_longest and join
def merge_alt_v9(word1, word2):
    from itertools import zip_longest
    return "".join(a + b for a, b in zip_longest(word1, word2, fillvalue=""))


# Solution 10: Using reduce
def merge_alt_v10(word1, word2):
    from functools import reduce
    pairs = list(zip(word1, word2))
    merged = reduce(lambda acc, ab: acc + ab[0] + ab[1], pairs, "")
    leftover = word1[len(pairs):] + word2[len(pairs):]
    return merged + leftover


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (canonical 2ptr)",     merge_alt_v1),
        ("V2 (zip + leftover)",     merge_alt_v2),
        ("V3 (zip_longest)",        merge_alt_v3),
        ("V4 (zip + concat)",       merge_alt_v4),
        ("V5 (loop with min)",      merge_alt_v5),
        ("V6 (recursive)",          merge_alt_v6),
        ("V7 (stack pop(0))",       merge_alt_v7),
        ("V8 (slice merging)",      merge_alt_v8),
        ("V9 (zip_longest one-liner)", merge_alt_v9),
        ("V10 (reduce)",            merge_alt_v10),
    ]

    test_cases = [
        # (word1, word2, expected)
        ("abc", "pqr",    "apbqcr"),
        ("ab",  "pqrs",   "apbqrs"),
        ("abcd","pq",     "apbqcd"),
        ("",    "abc",    "abc"),
        ("abc", "",       "abc"),
        ("",    "",       ""),
        ("a",   "b",      "ab"),
        ("ab",  "cd",     "acbd"),
        ("wxyz","abc",    "waxbycz"),
        ("abc", "wxyz",   "awbxcyz"),
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (w1, w2, expected) in enumerate(test_cases):
            try:
                got = func(w1, w2)
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{idx}]: ({w1!r}, {w2!r}) -> {got!r} (expected {expected!r})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")
    print("\n=== INTERVIEW THINKING ===")
    print("""
1. UNDERSTAND:  Interleave word1, word2 starting with word1.
2. INSIGHT:     Two-pointer; alternate until one runs out; drain other.
3. PATTERN:     Sequential two-pointer with single output buffer.
4. EDGE:        Empty strings; one much longer than the other.
5. TRICKY:      Always start with word1; never interleave after one runs out.
6. ALGORITHM:   while i<n and j<m: append w1[i], w2[j]; drain leftovers.
7. PROOF:       Each char appears exactly once, in the right order.
8. COMPLEXITY:  O(n+m) time, O(n+m) space.
9. CODE:        Two while loops; append from both, then drain.
10. TRACE:      "abc","pqr" -> "apbqcr"; "ab","pqrs" -> "apbqrs".
""")
