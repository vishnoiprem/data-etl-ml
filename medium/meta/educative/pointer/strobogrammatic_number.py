"""
Strobogrammatic Number - 10 Ways
=================================
Given a string num representing an integer, return whether it appears the
same when rotated 180 degrees (viewed upside down).

Valid pairs (digit -> upside-down equivalent):
    0 <-> 0
    1 <-> 1
    6 <-> 9
    8 <-> 8
    9 <-> 6

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/strobogrammatic-number

Examples:
    "69"    -> True
    "962"   -> False
    "818"   -> True
    "0"     -> True
    "101"   -> True
    "906"   -> False (9 maps to 6 at index 0, but the original index 2 is 6 which maps to 9)

Constraints:
- 1 <= num.length <= 50
- num contains only digits.

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Determine if num is strobogrammatic — looks the same when rotated 180°."

2. KEY INSIGHT:
   "Two-pointer from both ends. For each pair (i, j), num[i] must rotate
    to num[j] AND num[j] must rotate to num[i]. Use a valid-pair map:
    {0:0, 1:1, 6:9, 8:8, 9:6}."

3. PATTERN RECOGNITION:
   "Two-pointer convergent with pairwise mapping check."

4. EDGE CASES:
   - Single digit (0, 1, 8) -> True.
   - Other single digits (2-7 except 8, 9) -> False.
   - Empty string -> True (vacuously).
   - Even length: every pair must match.
   - Odd length: middle char must be self-mapped (0, 1, 8).

5. TRICKY DETAIL:
   "If num[i] is NOT in the valid map (e.g., '2', '3'), it's automatically
    not strobogrammatic. Don't just check if the pair matches — also check
    that each digit has a valid rotation."

6. ALGORITHM:
   "MAP = {'0':'0','1':'1','6':'9','8':'8','9':'6'}
    i, j = 0, n-1
    while i <= j:
        if num[i] not in MAP or MAP[num[i]] != num[j]: return False
        i += 1; j -= 1
    return True"

7. WHY TWO-POINTERS:
   "Each position must mirror its counterpart. Single linear scan
    from both ends suffices — O(n)."

8. COMPLEXITY:
   "Time: O(n).
    Space: O(1) (or O(k) for the map, k=5)."

9. CODE STRUCTURE:
   "Define rotation map.
    Walk pointers from both ends.
    Check both: num[i] is in map AND map[num[i]] == num[j]."

10. MENTAL TRACE:
    "69": i=0, j=1. map['6']='9', num[1]='9'. Match. i=1, j=0. i>j, exit. True ✓
    "962": i=0, j=2. map['9']='6', num[2]='2'. '2' != '6'. False ✓
    "101": i=0, j=2. map['1']='1', num[2]='1'. Match. i=1, j=1. map['0']='0', num[1]='0'. Match. i=2, j=0. Exit. True ✓
"""


# Solution 1: Canonical two-pointer with map (BEST)
def is_strobo_v1(num):
    MAP = {"0": "0", "1": "1", "6": "9", "8": "8", "9": "6"}
    i, j = 0, len(num) - 1
    while i <= j:
        if num[i] not in MAP or MAP[num[i]] != num[j]:
            return False
        i += 1
        j -= 1
    return True


# Solution 2: Two-pointer with set of valid digits
def is_strobo_v2(num):
    if not num:
        return True
    VALID = set("01689")
    PAIRS = {"0": "0", "1": "1", "6": "9", "8": "8", "9": "6"}
    for i in range(len(num) // 2 + 1):
        if num[i] not in VALID or num[-1 - i] not in VALID:
            return False
        if PAIRS[num[i]] != num[-1 - i]:
            return False
    return True


# Solution 3: Mirror the string and compare
def is_strobo_v3(num):
    MAP = {"0": "0", "1": "1", "6": "9", "8": "8", "9": "6"}
    rotated = []
    for ch in num:
        if ch not in MAP:
            return False
        rotated.append(MAP[ch])
    return "".join(rotated[::-1]) == num


# Solution 4: Using reversed zip with map check
def is_strobo_v4(num):
    PAIRS = {"0": "0", "1": "1", "6": "9", "8": "8", "9": "6"}
    n = len(num)
    for i in range(n):
        if num[i] not in PAIRS:
            return False
    # Reverse-pair check
    rotated = "".join(PAIRS[c] for c in num)
    return rotated[::-1] == num


# Solution 5: Brute force — try all valid digit combos
def is_strobo_v5(num):
    PAIRS = {"0": "0", "1": "1", "6": "9", "8": "8", "9": "6"}
    n = len(num)
    # Generate all valid pairings of length n
    def gen(length):
        if length == 0:
            return [""]
        if length == 1:
            return ["0", "1", "8"]
        inner = gen(length - 2)
        result = []
        for s in inner:
            for outer in ["00", "11", "69", "88", "96"]:
                result.append(outer[0] + s + outer[1])
        return result
    return num in gen(n)


# Solution 6: Two-pointer with explicit while
def is_strobo_v6(num):
    PAIRS = {"0": "0", "1": "1", "6": "9", "8": "8", "9": "6"}
    i, j = 0, len(num) - 1
    while i < j:
        if num[i] not in PAIRS or PAIRS[num[i]] != num[j]:
            return False
        i += 1
        j -= 1
    if i == j:  # middle char
        if num[i] not in PAIRS or PAIRS[num[i]] != num[i]:
            return False
    return True


# Solution 7: Using translate (but checking all digits are in MAP first)
def is_strobo_v7(num):
    VALID = set("01689")
    if any(c not in VALID for c in num):
        return False
    MAP = str.maketrans({"0": "0", "1": "1", "6": "9", "8": "8", "9": "6"})
    rotated = num.translate(MAP)
    return rotated[::-1] == num


# Solution 8: Using all() with zip
def is_strobo_v8(num):
    PAIRS = {"0": "0", "1": "1", "6": "9", "8": "8", "9": "6"}
    n = len(num)
    if n % 2 == 1 and num[n // 2] not in {"0", "1", "8"}:
        return False
    return all(PAIRS.get(num[i]) == num[n - 1 - i] for i in range(n // 2))


# Solution 9: Recursive
def is_strobo_v9(num):
    PAIRS = {"0": "0", "1": "1", "6": "9", "8": "8", "9": "6"}
    def helper(i, j):
        if i > j:
            return True
        if num[i] not in PAIRS or PAIRS[num[i]] != num[j]:
            return False
        return helper(i + 1, j - 1)
    return helper(0, len(num) - 1)


# Solution 10: Functional with reduce
def is_strobo_v10(num):
    from functools import reduce
    PAIRS = {"0": "0", "1": "1", "6": "9", "8": "8", "9": "6"}
    if not num:
        return True
    n = len(num)
    pairs = list(zip(num, reversed(num)))
    def check(acc, p):
        if not acc:
            return acc
        a, b = p
        if a not in PAIRS or PAIRS[a] != b:
            return False
        return True
    return reduce(check, pairs[:n // 2 + 1 if n % 2 == 1 else n // 2], True)


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (canonical 2ptr)",      is_strobo_v1),
        ("V2 (valid set)",           is_strobo_v2),
        ("V3 (mirror+compare)",      is_strobo_v3),
        ("V4 (reversed zip)",        is_strobo_v4),
        ("V5 (brute gen)",           is_strobo_v5),
        ("V6 (explicit while)",      is_strobo_v6),
        ("V7 (translate)",           is_strobo_v7),
        ("V8 (all+zip)",             is_strobo_v8),
        ("V9 (recursive)",           is_strobo_v9),
        ("V10 (reduce)",             is_strobo_v10),
    ]

    test_cases = [
        # (input, expected)
        ("69",     True),
        ("962",    False),
        ("818",    True),
        ("0",      True),
        ("101",    True),
        ("906",    False),
        ("1",      True),
        ("8",      True),
        ("2",      False),
        ("11",     True),
        ("609",    False),
        ("619",    True),
        ("88",     True),
        ("6",      False),
        ("9",      False),
        ("",       True),
        ("25",     False),
        ("8008",   True),
        ("96",     True),
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
                    print(f"  X {name} [{idx}]: {s!r} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: ERROR on {s!r}: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")
    print("\n=== INTERVIEW THINKING ===")
    print("""
1. UNDERSTAND:  Is num strobogrammatic?
2. INSIGHT:     Two-pointer; for each pair, check num[i] rotates to num[j].
3. PATTERN:     Convergent two-pointer with pair mapping.
4. EDGE:        Single digit 0/1/8 -> True; other singles -> False; middle of odd len must self-map.
5. TRICKY:      num[i] must be in valid map; otherwise auto-fail.
6. ALGORITHM:   i,j = 0, n-1; while i<=j: check pair; advance.
7. PROOF:       Each digit either self-maps (0,1,8) or maps to a distinct partner (6,9).
8. COMPLEXITY:  O(n) time, O(1) space.
9. CODE:        Define MAP; walk pointers; check both direction.
10. TRACE:      "69" -> map['6']='9'==num[1]='9' -> True. "962" -> map['9']='6'!=num[2]='2' -> False.
""")
