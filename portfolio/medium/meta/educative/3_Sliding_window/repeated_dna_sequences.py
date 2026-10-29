"""
Repeated DNA Sequences - 10 Ways
=================================
The DNA sequence is composed of a series of nucleotides abbreviated as
'A', 'C', 'G', 'T'. A gene is a substring of length 10.

Given a string s representing a DNA sequence, return all the 10-letter-
long sequences (substrings) that occur more than once. The order of the
returned sequences does not matter.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/repeated-dna-sequences
          (LeetCode #187)

Examples:
    s = "AAAAACCCCCAAAAACCCCCCAAAAAGGGTTT"
      -> ["AAAAACCCCC", "CCCCCAAAAA"]
    s = "AAAAAAAAAAAAA"
      -> ["AAAAAAAAAA"]

Constraints:
- 0 <= s.length <= 10^5
- s[i] is 'A', 'C', 'G', or 'T'.

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Find all 10-character substrings that appear more than once in s."

2. KEY INSIGHT:
   "Fixed-size sliding window of length 10. Use a hashmap to count
    occurrences. Return substrings with count > 1."

3. PATTERN RECOGNITION:
   "Hashmap + fixed window + filter at end (or eagerly)."

4. EDGE CASES:
   - s shorter than 10 -> [].
   - s of length exactly 10 -> [] (only one occurrence).
   - All same character repeated -> one big string repeated.

5. TRICKY DETAIL:
   "Encoding: we could encode each 10-char sequence as a 20-bit int
    (2 bits per nucleotide: A=00, C=01, G=10, T=11) and slide a window
    on the int. Saves memory vs. string slicing."

6. ALGORITHM:
   "seen = {}
    result = set()
    for i in range(len(s) - 9):
        sub = s[i:i+10]
        if sub in seen:
            result.add(sub)
        else:
            seen.add(sub)
    return list(result)"

7. WHY IT WORKS:
   "Each 10-char substring is checked. If we've seen it before, it
    occurs at least twice. Add to result (set to dedupe)."

8. COMPLEXITY:
   "Time: O(n * 10) for substring slicing, but can be O(n) with rolling hash.
    Space: O(n * 10) for the substrings in worst case (but usually less)."

9. CODE STRUCTURE:
   "Iterate over starting indices. Extract substring. Update seen."

10. MENTAL TRACE:
    s = "AAAAACCCCCAAAAACCCCCCAAAAAGGGTTT"
    Substrings of length 10:
    i=0: AAAAACCCCC (count 1)
    i=1: AAAACCCCC A (count 1)
    ...
    i=10: AAAAACCCCC (count 2 -> add to result)
    i=15: CCCCCAAAAA (count 2 -> add to result)
    ...
    Result: ["AAAAACCCCC", "CCCCCAAAAA"]
"""


# Solution 1: Hashset with slice (BEST - simple)
def find_repeated_dna_v1(s):
    if len(s) < 10:
        return []
    seen = set()
    result = set()
    for i in range(len(s) - 9):
        sub = s[i:i + 10]
        if sub in seen:
            result.add(sub)
        else:
            seen.add(sub)
    return list(result)


# Solution 2: Counter (count occurrences)
def find_repeated_dna_v2(s):
    if len(s) < 10:
        return []
    from collections import Counter
    cnt = Counter()
    for i in range(len(s) - 9):
        cnt[s[i:i + 10]] += 1
    return [sub for sub, c in cnt.items() if c > 1]


# Solution 3: Hashset, add to result only on second sighting
def find_repeated_dna_v3(s):
    if len(s) < 10:
        return []
    seen = set()
    result = set()
    for i in range(len(s) - 9):
        sub = s[i:i + 10]
        if sub in seen:
            result.add(sub)
        seen.add(sub)
    return list(result)


# Solution 4: Rolling hash with int encoding (2 bits per char)
def find_repeated_dna_v4(s):
    if len(s) < 10:
        return []
    # Encode A=0, C=1, G=2, T=3
    char_map = {'A': 0, 'C': 1, 'G': 2, 'T': 3}
    # Initial hash from first 10 chars
    h = 0
    for i in range(10):
        h = (h << 2) | char_map[s[i]]
    seen = {h}
    result = set()
    mask = (1 << 20) - 1  # 20 bits = 10 chars * 2 bits
    for i in range(10, len(s)):
        # Slide: remove leftmost 2 bits, add new 2 bits
        h = ((h << 2) & mask) | char_map[s[i]]
        if h in seen:
            result.add(s[i - 9:i + 1])  # Recover substring for output
        else:
            seen.add(h)
    return list(result)


# Solution 5: One-step slice + dict
def find_repeated_dna_v5(s):
    if len(s) < 10:
        return []
    seen = {}
    for i in range(len(s) - 9):
        sub = s[i:i + 10]
        if sub in seen:
            seen[sub] += 1
        else:
            seen[sub] = 1
    return [k for k, v in seen.items() if v > 1]


# Solution 6: defaultdict + filter
def find_repeated_dna_v6(s):
    if len(s) < 10:
        return []
    from collections import defaultdict
    cnt = defaultdict(int)
    for i in range(len(s) - 9):
        cnt[s[i:i + 10]] += 1
    return [k for k, v in cnt.items() if v > 1]


# Solution 7: List comprehension approach
def find_repeated_dna_v7(s):
    if len(s) < 10:
        return []
    subs = [s[i:i + 10] for i in range(len(s) - 9)]
    seen = set()
    repeats = set()
    for sub in subs:
        if sub in seen:
            repeats.add(sub)
        else:
            seen.add(sub)
    return list(repeats)


# Solution 8: Brute force with all-pairs comparison
def find_repeated_dna_v8(s):
    if len(s) < 10:
        return []
    n = len(s)
    result = set()
    for i in range(n - 9):
        sub_i = s[i:i + 10]
        for j in range(i + 1, n - 9):
            if sub_i == s[j:j + 10]:
                result.add(sub_i)
                break
    return list(result)


# Solution 9: Group by substring, take those with len > 1
def find_repeated_dna_v9(s):
    if len(s) < 10:
        return []
    groups = {}
    for i in range(len(s) - 9):
        sub = s[i:i + 10]
        groups.setdefault(sub, []).append(i)
    return [sub for sub, indices in groups.items() if len(indices) > 1]


# Solution 10: Recursive (educational)
def find_repeated_dna_v10(s):
    if len(s) < 10:
        return []
    seen = set()
    result = set()

    def helper(i):
        nonlocal seen, result
        if i > len(s) - 10:
            return
        sub = s[i:i + 10]
        if sub in seen:
            result.add(sub)
        else:
            seen.add(sub)
        helper(i + 1)

    helper(0)
    return list(result)


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (hashset BEST)",           find_repeated_dna_v1),
        ("V2 (Counter)",                find_repeated_dna_v2),
        ("V3 (hashset, dedupe)",        find_repeated_dna_v3),
        ("V4 (rolling hash int)",       find_repeated_dna_v4),
        ("V5 (dict counts)",            find_repeated_dna_v5),
        ("V6 (defaultdict)",            find_repeated_dna_v6),
        ("V7 (list comp)",              find_repeated_dna_v7),
        ("V8 (brute O(n^2))",           find_repeated_dna_v8),
        ("V9 (group by index)",         find_repeated_dna_v9),
        ("V10 (recursive)",             find_repeated_dna_v10),
    ]

    # We compare results as sets since order doesn't matter.
    test_cases = [
        # (input, expected_set)
        ("AAAAACCCCCAAAAACCCCCCAAAAAGGGTTT", {"AAAAACCCCC", "CCCCCAAAAA"}),
        ("AAAAAAAAAAAAA", {"AAAAAAAAAA"}),
        ("", set()),
        ("ACGTACGTAC", set()),  # length 9 < 10
        # s=ACGTACGTACGTACGT, length 16. Substrings of length 10:
        #  i=0: ACGTACGTAC, i=1: CGTACGTACG, i=2: GTACGTACGT,
        #  i=3: TACGTACGTA, i=4: ACGTACGTAC, i=5: CGTACGTACG, i=6: GTACGTACGT
        # Repeats: ACGTACGTAC (i=0,4), CGTACGTACG (i=1,5), GTACGTACGT (i=2,6)
        ("ACGTACGTACGTACGT", {"ACGTACGTAC", "CGTACGTACG", "GTACGTACGT"}),
        ("AAAAACCCCCAAAAACCCCC", {"AAAAACCCCC"}),
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (s, expected) in enumerate(test_cases):
            try:
                got = set(func(s))
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{idx}]: {s[:30]!r}... -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")