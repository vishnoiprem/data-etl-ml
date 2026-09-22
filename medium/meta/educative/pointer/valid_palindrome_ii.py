"""
Valid Palindrome II
Easy | 15 min

Given a string s, return true if the string can be a palindrome
after deleting AT MOST one character.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/valid-palindrome-ii

Examples:
    "aba"  -> True   (already palindrome)
    "abca"  -> True  (delete 'b' or 'c')
    "abc"   -> False
    "a"     -> True
    "ab"    -> True   (delete one char)
    "abca"  -> True
    "deeee" -> True   (already palindrome)

Constraints:
- 1 <= s.length <= 10^5
- s consists of lowercase English letters.

KEY INSIGHT:
Two pointers from both ends. When mismatch found, we have ONE chance
to skip. Either skip left char or right char. Try BOTH recursively
on a palindrome check. If either passes, return True.

Time:  O(n) — single pass with at most one extra check.
Space: O(1) iterative, O(n) for recursion stack.
"""


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT VALID PALINDROME II:

1. UNDERSTAND THE PROBLEM:
   "Can we make the string a palindrome by deleting AT MOST one character?"

2. KEY OBSERVATION:
   "Normal palindrome check: two pointers from both ends, compare.
   If we find a mismatch, we have ONE chance to skip:
     - Skip the left character, OR
     - Skip the right character.
   If either of those substrings is a palindrome, we win."

3. GREEDY + RECURSION:
   "Walk from both ends. On first mismatch, branch: try skip-left
   OR skip-right. Both are O(n) palindrome checks. If either succeeds,
   the answer is True."

4. WHY ONLY ONE MISMATCH ALLOWED:
   "After one skip, the rest must be a perfect palindrome.
   We don't get a second chance."

5. EDGE CASES:
   - Empty string: True.
   - Single char: True.
   - Two chars: True (delete one).
   - Already palindrome: True.
   - All same chars: True.
   - Three distinct chars: False.

6. COMPLEXITY:
   +----------+--------+--------+
   | Approach | Time   | Space  |
   +----------+--------+--------+
   | Two ptr  | O(n)   | O(1)   |
   | Brute    | O(n^2) | O(n)   |
   +----------+--------+--------+

7. WHY TWO POINTERS > BRUTE:
   - Single pass with O(1) extra work per char.
   - Brute (try deleting every char) is O(n^2).
"""


# =============================================================================
# WAY 1: Two-pointer with skip-once helper (BEST - Memorize!)
# =============================================================================
def valid_palindrome_ii_1(s):
    """
    Two pointers from both ends. On mismatch, try skipping left or right.
    Either branch passing means answer is True.
    """
    def is_palindrome_range(left, right):
        while left < right:
            if s[left] != s[right]:
                return False
            left += 1
            right -= 1
        return True

    left, right = 0, len(s) - 1
    while left < right:
        if s[left] != s[right]:
            return (is_palindrome_range(left + 1, right) or
                    is_palindrome_range(left, right - 1))
        left += 1
        right -= 1
    return True


# =============================================================================
# WAY 2: Recursive two-pointer
# =============================================================================
def valid_palindrome_ii_2(s):
    """Recursive helper. is_pal(left, right, skipped)."""

    def is_pal(left, right, skipped):
        if left >= right:
            return True
        if s[left] == s[right]:
            return is_pal(left + 1, right - 1, skipped)
        if skipped:
            return False
        return is_pal(left + 1, right, True) or is_pal(left, right - 1, True)

    return is_pal(0, len(s) - 1, False)


# =============================================================================
# WAY 3: Iterative without helper function
# =============================================================================
def valid_palindrome_ii_3(s):
    """Inline palindrome check. No helper function."""
    left, right = 0, len(s) - 1
    while left < right:
        if s[left] != s[right]:
            # Try skip-left: check s[left+1..right] is palindrome.
            l, r = left + 1, right
            while l < r:
                if s[l] != s[r]:
                    break
                l += 1
                r -= 1
            else:
                return True
            # Try skip-right.
            l, r = left, right - 1
            while l < r:
                if s[l] != s[r]:
                    return False
                l += 1
                r -= 1
            return True
        left += 1
        right -= 1
    return True


# =============================================================================
# WAY 4: Brute force - try deleting every character
# =============================================================================
def valid_palindrome_ii_4(s):
    """Try deleting each character (or none) and check palindrome."""
    def is_pal(t):
        return t == t[::-1]

    if is_pal(s):
        return True
    for i in range(len(s)):
        candidate = s[:i] + s[i + 1 :]
        if is_pal(candidate):
            return True
    return False


# =============================================================================
# WAY 5: Class OOP
# =============================================================================
class PalindromeChecker:
    def __init__(self, s):
        self.s = s

    def check(self):
        s = self.s

        def is_range(left, right):
            while left < right:
                if s[left] != s[right]:
                    return False
                left += 1
                right -= 1
            return True

        left, right = 0, len(s) - 1
        while left < right:
            if s[left] != s[right]:
                return is_range(left + 1, right) or is_range(left, right - 1)
            left += 1
            right -= 1
        return True


def valid_palindrome_ii_5(s):
    return PalindromeChecker(s).check()


# =============================================================================
# WAY 6: Lambda/functional approach
# =============================================================================
def valid_palindrome_ii_6(s):
    """Use a helper closure with nonlocal-like state via list."""

    def check(left, right, skipped):
        if left >= right:
            return True
        if s[left] == s[right]:
            return check(left + 1, right - 1, skipped)
        if skipped:
            return False
        return check(left + 1, right, True) or check(left, right - 1, True)

    return check(0, len(s) - 1, False)


# =============================================================================
# WAY 7: Use reversed() comparison for range check
# =============================================================================
def valid_palindrome_ii_7(s):
    """Use slicing comparison (slower but readable)."""
    left, right = 0, len(s) - 1
    while left < right:
        if s[left] != s[right]:
            skip_left = s[left + 1 : right + 1]
            skip_right = s[left:right]
            return skip_left == skip_left[::-1] or skip_right == skip_right[::-1]
        left += 1
        right -= 1
    return True


# =============================================================================
# WAY 8: Memoization of mismatches (educational)
# =============================================================================
def valid_palindrome_ii_8(s):
    """Memoize which (left, right) pairs we've checked."""

    def is_pal(l, r):
        while l < r:
            if s[l] != s[r]:
                return False
            l += 1
            r -= 1
        return True

    def check(left, right, can_skip):
        if left >= right:
            return True
        if s[left] == s[right]:
            return check(left + 1, right - 1, can_skip)
        if not can_skip:
            return False
        return is_pal(left + 1, right) or is_pal(left, right - 1)

    return check(0, len(s) - 1, True)


# =============================================================================
# WAY 9: Single-skip with while loop (no recursion)
# =============================================================================
def valid_palindrome_ii_9(s):
    """Iterative with single skip using a flag variable."""
    left, right = 0, len(s) - 1
    skipped = False
    while left < right:
        if s[left] != s[right]:
            if skipped:
                return False
            # Try skip-right first.
            if s[left] == s[right - 1]:
                right -= 1
                skipped = True
            elif s[left + 1] == s[right]:
                left += 1
                skipped = True
            else:
                return False
        else:
            left += 1
            right -= 1
    return True


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def valid_palindrome_ii_10(s):
    """
    THE ONE TO MEMORIZE.

    Two pointers from both ends. On first mismatch, branch: try skipping
    left OR right. Either branch being palindrome = True.

    Time:  O(n).
    Space: O(1).
    """
    def is_range(left, right):
        while left < right:
            if s[left] != s[right]:
                return False
            left += 1
            right -= 1
        return True

    left, right = 0, len(s) - 1
    while left < right:
        if s[left] != s[right]:
            return is_range(left + 1, right) or is_range(left, right - 1)
        left += 1
        right -= 1
    return True


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Two-pointer skip helper (BEST)", valid_palindrome_ii_1),
        ("Way 2: Recursive two-pointer", valid_palindrome_ii_2),
        ("Way 3: Iterative no helper", valid_palindrome_ii_3),
        ("Way 4: Brute force", valid_palindrome_ii_4),
        ("Way 5: Class OOP", valid_palindrome_ii_5),
        ("Way 6: Functional closure", valid_palindrome_ii_6),
        ("Way 7: Slice comparison", valid_palindrome_ii_7),
        ("Way 8: Memoization-style", valid_palindrome_ii_8),
        ("Way 9: Single-skip flag", valid_palindrome_ii_9),
        ("Way 10: Final cleanest", valid_palindrome_ii_10),
    ]

    test_cases = [
        # (s, expected)
        ("aba", True),
        ("abca", True),
        ("abc", False),
        ("a", True),
        ("ab", True),
        ("deeee", True),
        ("eeccccbabaaabohpbohgbhc", False),
        ("racecar", True),
        ("raceecar", True),  # delete 'e'
        ("abcdef", False),
        ("abccba", True),
        ("abcbxa", True),  # delete 'x' → "abcba"
        ("", True),
        ("  ", True),  # both spaces
    ]

    print("=" * 70)
    print("VALID PALINDROME II - 10 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/valid-palindrome-ii")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for s, expected in test_cases:
            try:
                result = func(s)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: s={s!r}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: s={s!r}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)