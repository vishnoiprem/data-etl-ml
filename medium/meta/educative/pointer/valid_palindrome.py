"""
Valid Palindrome - 20 Ways
============================
A phrase is a palindrome if, after converting all uppercase letters to lowercase
and removing all non-alphanumeric characters, it reads the same forward and
backward. Determine if a string s is a palindrome.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/valid-palindrome

Examples:
    "A man, a plan, a canal: Panama" -> True
    "race a car" -> False
    " " -> True (empty after filtering)

Constraints:
- 1 <= s.length <= 2 * 10^5
- s consists only of printable ASCII characters

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Determine if s is a palindrome, ignoring case and non-alphanumeric chars."

2. KEY INSIGHT:
   "Use two pointers from BOTH ends. Skip non-alphanumeric chars.
    Compare lowercase version of each pair."

3. PATTERN RECOGNITION:
   "Two-pointer converging from both ends. O(n) time, O(1) extra space."

4. EDGE CASES:
   - Empty / single char -> True.
   - All non-alphanumeric -> True (filtered string is empty).
   - Mixed case -> case-insensitive.
   - Punctuation in middle -> skip both sides.

5. TRICKY DETAIL:
   "c.isalnum() is ASCII-safe; c.lower() makes it case-insensitive.
    Python's str methods work on Unicode but for this problem ASCII range suffices."

6. ALGORITHM:
   "i, j = 0, len(s) - 1
    while i < j:
        while i < j and not s[i].isalnum(): i += 1
        while i < j and not s[j].isalnum(): j -= 1
        if i >= j: break
        if s[i].lower() != s[j].lower(): return False
        i += 1; j -= 1
    return True"

7. WHY TWO-POINTERS:
   "Each comparison advances both pointers. Total work: O(n).
    We don't need the filtered string in memory."

8. COMPLEXITY:
   "Time: O(n) — single pass.
    Space: O(1) extra (or O(n) for a filtered copy)."

9. CODE STRUCTURE:
   "left, right = 0, n - 1
    while left < right:
        skip non-alnum on both sides
        compare s[left].lower() == s[right].lower()
        move pointers
    return True"

10. MENTAL TRACE:
    s = "A man, a plan, a canal: Panama"
    Left=0 'A', Right=29 'a' -> match
    Skip non-alnum on both sides repeatedly...
    Eventually all pairs match -> True
"""


# Solution 1: Canonical two-pointer (BEST)
def is_palindrome_v1(s):
    left, right = 0, len(s) - 1
    while left < right:
        while left < right and not s[left].isalnum():
            left += 1
        while left < right and not s[right].isalnum():
            right -= 1
        if left < right:
            if s[left].lower() != s[right].lower():
                return False
            left += 1
            right -= 1
    return True


# Solution 2: Filter then compare
def is_palindrome_v2(s):
    filtered = [c.lower() for c in s if c.isalnum()]
    return filtered == filtered[::-1]


# Solution 3: Filter as string, then compare
def is_palindrome_v3(s):
    filtered = "".join(c.lower() for c in s if c.isalnum())
    return filtered == filtered[::-1]


# Solution 4: Two-pointer with explicit ASCII check
def is_palindrome_v4(s):
    left, right = 0, len(s) - 1
    while left < right:
        cl = s[left]
        cr = s[right]
        if not cl.isalnum():
            left += 1
            continue
        if not cr.isalnum():
            right -= 1
            continue
        if cl.lower() != cr.lower():
            return False
        left += 1
        right -= 1
    return True


# Solution 5: Two-pointer with ord() and range checks (ASCII-only)
def is_palindrome_v5(s):
    def alpha_num(c):
        o = ord(c)
        return (ord('a') <= o <= ord('z')) or (ord('A') <= o <= ord('Z')) or (ord('0') <= o <= ord('9'))

    def lower(c):
        o = ord(c)
        if ord('A') <= o <= ord('Z'):
            return chr(o + 32)
        return c

    left, right = 0, len(s) - 1
    while left < right:
        if not alpha_num(s[left]):
            left += 1
        elif not alpha_num(s[right]):
            right -= 1
        elif lower(s[left]) != lower(s[right]):
            return False
        else:
            left += 1
            right -= 1
    return True


# Solution 6: Stack-based
def is_palindrome_v6(s):
    stack = [c.lower() for c in s if c.isalnum()]
    for c in stack[::-1]:
        if stack.pop(0) != c:
            return False
    return True


# Solution 7: Deque-based (O(1) popleft)
def is_palindrome_v7(s):
    from collections import deque
    d = deque(c.lower() for c in s if c.isalnum())
    while len(d) > 1:
        if d.popleft() != d.pop():
            return False
    return True


# Solution 8: Recursive
def is_palindrome_v8(s):
    s = [c.lower() for c in s if c.isalnum()]
    def helper(left, right):
        if left >= right:
            return True
        if s[left] != s[right]:
            return False
        return helper(left + 1, right - 1)
    return helper(0, len(s) - 1)


# Solution 9: Built-in reversed comparison
def is_palindrome_v9(s):
    filtered = "".join(c.lower() for c in s if c.isalnum())
    return filtered == "".join(reversed(filtered))


# Solution 10: Generator-based comparison
def is_palindrome_v10(s):
    def gen():
        for c in (ch.lower() for ch in s if ch.isalnum()):
            yield c
    chars = list(gen())
    return chars == list(reversed(chars))


# Solution 11: For-loop with zip (forward vs reversed)
def is_palindrome_v11(s):
    filtered = [c.lower() for c in s if c.isalnum()]
    return all(a == b for a, b in zip(filtered, reversed(filtered)))


# Solution 12: Iterative two-pointer with while helpers
def is_palindrome_v12(s):
    n = len(s)
    left, right = 0, n - 1
    while left < right:
        while left < right and not s[left].isalnum():
            left += 1
        if left >= right:
            break
        while left < right and not s[right].isalnum():
            right -= 1
        if s[left].lower() != s[right].lower():
            return False
        left += 1
        right -= 1
    return True


# Solution 13: Functional reduce
def is_palindrome_v13(s):
    from functools import reduce
    filtered = [c.lower() for c in s if c.isalnum()]
    return reduce(lambda acc, c: acc and c[0] == c[1], zip(filtered, reversed(filtered)), True)


# Solution 14: List-comprehension with palindrome property
def is_palindrome_v14(s):
    filtered = [c.lower() for c in s if c.isalnum()]
    L = len(filtered)
    return all(filtered[i] == filtered[L - 1 - i] for i in range(L // 2))


# Solution 15: Manual reverse via slicing
def is_palindrome_v15(s):
    filtered = "".join(c.lower() for c in s if c.isalnum())
    L = len(filtered)
    return all(filtered[i] == filtered[L - 1 - i] for i in range(L // 2))


# Solution 16: Two-pointer with single-pass index
def is_palindrome_v16(s):
    # Use a list comprehension first
    cleaned = [c.lower() for c in s if c.isalnum()]
    n = len(cleaned)
    for i in range(n // 2):
        if cleaned[i] != cleaned[n - 1 - i]:
            return False
    return True


# Solution 17: Class-based
class PalindromeChecker:
    def __init__(self, s):
        self.s = s

    def is_palindrome(self):
        cleaned = [c.lower() for c in self.s if c.isalnum()]
        return cleaned == cleaned[::-1]


def is_palindrome_v17(s):
    return PalindromeChecker(s).is_palindrome()


# Solution 18: Using regex
import re
def is_palindrome_v18(s):
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', s).lower()
    return cleaned == cleaned[::-1]


# Solution 19: Two-pointer using ord arithmetic for ASCII
def is_palindrome_v19(s):
    left, right = 0, len(s) - 1
    while left < right:
        cl = ord(s[left])
        while left < right and not (48 <= cl <= 57 or 65 <= cl <= 90 or 97 <= cl <= 122):
            left += 1
            cl = ord(s[left])
        cr = ord(s[right])
        while left < right and not (48 <= cr <= 57 or 65 <= cr <= 90 or 97 <= cr <= 122):
            right -= 1
            cr = ord(s[right])
        if left >= right:
            break
        # Normalize to lowercase ASCII
        if cl >= 65 and cl <= 90:
            cl += 32
        if cr >= 65 and cr <= 90:
            cr += 32
        if cl != cr:
            return False
        left += 1
        right -= 1
    return True


# Solution 20: Dual-iteration with accumulate
def is_palindrome_v20(s):
    cleaned = [c.lower() for c in s if c.isalnum()]
    return all(
        a == b
        for a, b in zip(cleaned, reversed(cleaned))
    )


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (canonical 2-pointer)",     is_palindrome_v1),
        ("V2 (filter+reverse list)",     is_palindrome_v2),
        ("V3 (filter str+reverse)",      is_palindrome_v3),
        ("V4 (explicit ASCII skip)",     is_palindrome_v4),
        ("V5 (ord alpha check)",         is_palindrome_v5),
        ("V6 (stack)",                   is_palindrome_v6),
        ("V7 (deque)",                   is_palindrome_v7),
        ("V8 (recursive)",               is_palindrome_v8),
        ("V9 (joined reversed)",         is_palindrome_v9),
        ("V10 (generator)",              is_palindrome_v10),
        ("V11 (zip vs reversed)",        is_palindrome_v11),
        ("V12 (while helpers)",          is_palindrome_v12),
        ("V13 (reduce)",                 is_palindrome_v13),
        ("V14 (comprehension check)",    is_palindrome_v14),
        ("V15 (slice mirror check)",     is_palindrome_v15),
        ("V16 (single-pass index)",      is_palindrome_v16),
        ("V17 (class)",                  is_palindrome_v17),
        ("V18 (regex)",                  is_palindrome_v18),
        ("V19 (ord arithmetic)",         is_palindrome_v19),
        ("V20 (zip all)",                is_palindrome_v20),
    ]

    test_cases = [
        ("basic true",  "A man, a plan, a canal: Panama",       True),
        ("basic false", "race a car",                            False),
        ("empty filter"," ",                                     True),
        ("single char", "a",                                     True),
        ("single non-alnum", "!",                                True),
        ("simple palindrome", "racecar",                        True),
        ("not palindrome", "hello",                              False),
        ("mixed case", "AaBbAa",                                 True),
        ("with numbers", "12321",                               True),
        ("with numbers false", "1231",                          False),
        ("mixed alnum", "1a2b2a1",                             True),
        ("two punct", ".,",                                      True),
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for case_name, s, expected in test_cases:
            try:
                got = func(s)
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{case_name}]: {s!r} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{case_name}]: ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")
    print("\n=== INTERVIEW THINKING ===")
    print("""
1. UNDERSTAND:  Is s a palindrome, ignoring case and non-alnum?
2. INSIGHT:     Two pointers from both ends; skip non-alnum; compare lowercase.
3. PATTERN:     Convergent two-pointer, O(n) time, O(1) extra space.
4. EDGE:        Empty filter -> True; single char -> True.
5. TRICKY:      Python isalnum() works on Unicode; ASCII ord() check faster.
6. ALGORITHM:   Skip non-alnum both sides; lowercase compare; advance.
7. PROOF:       Each comparison advances both pointers. Total O(n).
8. COMPLEXITY:  O(n) time, O(1) extra (or O(n) for filtered copy).
9. CODE:        while left<right; skip; compare lower.
10. TRACE:      "A man..." -> 'A' == 'a' lower; ... eventually all match -> True.
""")
