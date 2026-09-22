"""
Valid Palindrome II
Easy | 15 min

Given a string s, return true if it can be a palindrome after deleting
at most one character.

Reference: https://www.educative.io/interview-prep/coding/valid-palindrome-ii

Examples:
    "aba" -> True (already palindrome)
    "abca" -> True (delete 'b' or 'c')
    "abc" -> False

Constraints:
- 1 <= s.length <= 10^5
- s consists of English letters only
"""


# =============================================================================
# WAY 1: Two-pointer with skip-once helper (BEST - Memorize!)
# =============================================================================
def validPalindrome_1(s):
    """
    KEY INSIGHT: Use two pointers from both ends. When we find a mismatch,
    we can either skip the left char OR the right char. Try both recursively.

    Time:  O(n) - we traverse at most twice
    Space: O(1) for iterative, O(n) for recursion due to call stack
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
            # Try skipping either left or right char
            return (is_palindrome_range(left + 1, right) or
                    is_palindrome_range(left, right - 1))
        left += 1
        right -= 1
    return True


# =============================================================================
# WAY 2: Iterative without helper function
# =============================================================================
def validPalindrome_2(s):
    """Same as Way 1 but inline the palindrome check."""
    left, right = 0, len(s) - 1
    while left < right:
        if s[left] != s[right]:
            # Try skipping left
            l, r = left + 1, right
            skip_left_ok = True
            while l < r:
                if s[l] != s[r]:
                    skip_left_ok = False
                    break
                l += 1
                r -= 1
            if skip_left_ok:
                return True
            # Try skipping right
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
# WAY 3: Recursive approach
# =============================================================================
def validPalindrome_3(s):
    """Pure recursion."""
    def helper(left, right, can_skip):
        if left >= right:
            return True
        if s[left] == s[right]:
            return helper(left + 1, right - 1, can_skip)
        if not can_skip:
            return False
        return (helper(left + 1, right, False) or
                helper(left, right - 1, False))

    return helper(0, len(s) - 1, True)


# =============================================================================
# WAY 4: Greedy with single check
# =============================================================================
def validPalindrome_4(s):
    """Greedy - on mismatch, check if either side is palindrome."""
    def is_palindrome(l, r):
        return s[l:r+1] == s[l:r+1][::-1]

    left, right = 0, len(s) - 1
    while left < right:
        if s[left] != s[right]:
            return is_palindrome(left + 1, right) or is_palindrome(left, right - 1)
        left += 1
        right -= 1
    return True


# =============================================================================
# WAY 5: Brute force - try deleting each character
# =============================================================================
def validPalindrome_5(s):
    """For each char, try removing it and check if palindrome."""
    n = len(s)
    if n <= 1:
        return True

    def is_pal(t):
        return t == t[::-1]

    # Try original
    if is_pal(s):
        return True
    # Try removing each char
    for i in range(n):
        if is_pal(s[:i] + s[i+1:]):
            return True
    return False


# =============================================================================
# WAY 6: Find first mismatch, then decide
# =============================================================================
def validPalindrome_6(s):
    """Find first mismatch, compare the two halves."""
    n = len(s)
    left, right = 0, n - 1
    while left < right and s[left] == s[right]:
        left += 1
        right -= 1
    if left >= right:
        return True
    # Found mismatch at (left, right)
    # Try skipping left
    s1 = s[left+1:right+1]
    if s1 == s1[::-1]:
        return True
    # Try skipping right
    s2 = s[left:right]
    return s2 == s2[::-1]


# =============================================================================
# WAY 7: Using slicing with reverse comparison
# =============================================================================
def validPalindrome_7(s):
    """Slicing-based palindrome check."""
    left, right = 0, len(s) - 1
    while left < right:
        if s[left] != s[right]:
            # Try skipping left
            candidate1 = s[left+1:right+1]
            if candidate1 == candidate1[::-1]:
                return True
            # Try skipping right
            candidate2 = s[left:right]
            return candidate2 == candidate2[::-1]
        left += 1
        right -= 1
    return True


# =============================================================================
# WAY 8: Most concise two-pointer
# =============================================================================
def validPalindrome_8(s):
    """Most concise."""
    l, r = 0, len(s) - 1
    while l < r:
        if s[l] != s[r]:
            return s[l+1:r+1] == s[l+1:r+1][::-1] or s[l:r] == s[l:r][::-1]
        l += 1
        r -= 1
    return True


# =============================================================================
# WAY 9: With explicit helper
# =============================================================================
def is_sub_palindrome(s, l, r):
    """Check if s[l:r+1] is a palindrome."""
    while l < r:
        if s[l] != s[r]:
            return False
        l += 1
        r -= 1
    return True


def validPalindrome_9(s):
    """Use external helper."""
    l, r = 0, len(s) - 1
    while l < r:
        if s[l] != s[r]:
            return is_sub_palindrome(s, l + 1, r) or is_sub_palindrome(s, l, r - 1)
        l += 1
        r -= 1
    return True


# =============================================================================
# WAY 10: Generator-based palindrome check
# =============================================================================
def is_pal_gen(s, l, r):
    """Generator-based palindrome check."""
    return all(s[i] == s[r - (i - l)] for i in range(l, (l + r) // 2 + 1))


def validPalindrome_10(s):
    """Use generator."""
    l, r = 0, len(s) - 1
    while l < r:
        if s[l] != s[r]:
            return is_pal_gen(s, l + 1, r) or is_pal_gen(s, l, r - 1)
        l += 1
        r -= 1
    return True


# =============================================================================
# WAY 11: Bit manipulation (overkill, but illustrative)
# =============================================================================
def validPalindrome_11(s):
    """
    Recursive on substring after skip. Note: after skipping, the remaining
    substring must be a STRICT palindrome (no more skips allowed).
    """
    def helper(l, r):
        # Check if s[l:r+1] is a palindrome (no skips left)
        while l < r:
            if s[l] != s[r]:
                return False
            l += 1
            r -= 1
        return True

    l, r = 0, len(s) - 1
    while l < r:
        if s[l] != s[r]:
            # After skipping, the rest must be a strict palindrome
            return helper(l + 1, r) or helper(l, r - 1)
        l += 1
        r -= 1
    return True


# =============================================================================
# WAY 12: Compare s with reverse, count differences
# =============================================================================
def validPalindrome_12(s):
    """Two-pointer but inline check using reversed comparison."""
    n = len(s)
    # Find first mismatch from left
    l, r = 0, n - 1
    while l < r and s[l] == s[r]:
        l += 1
        r -= 1
    if l >= r:
        return True
    # Mismatch at (l, r). Try deleting s[l] or s[r].
    # Delete s[l]: compare s[l+1:r+1] with its reverse
    a = s[l+1:r+1]
    if a == a[::-1]:
        return True
    # Delete s[r]: compare s[l:r] with its reverse
    b = s[l:r]
    return b == b[::-1]


# =============================================================================
# WAY 13: Using deque
# =============================================================================
def validPalindrome_13(s):
    """Use deque for pop operations."""
    from collections import deque
    dq = deque(s)
    skipped = False
    while len(dq) > 1:
        if dq[0] != dq[-1]:
            if skipped:
                return False
            skipped = True
            # Need to check both possibilities
            # Skip left
            d = deque(dq)
            d.popleft()
            if list(d) == list(reversed(d)):
                return True
            # Skip right
            d = deque(dq)
            d.pop()
            return list(d) == list(reversed(d))
        dq.popleft()
        dq.pop()
    return True


# =============================================================================
# WAY 14: With function pointer
# =============================================================================
def validPalindrome_14(s):
    """Use a sub-function for palindrome check."""
    def check(i, j):
        return s[i:j+1] == s[i:j+1][::-1]

    l, r = 0, len(s) - 1
    while l < r:
        if s[l] != s[r]:
            return check(l + 1, r) or check(l, r - 1)
        l += 1
        r -= 1
    return True


# =============================================================================
# WAY 15: Lambda + any
# =============================================================================
def validPalindrome_15(s):
    """Functional with lambda."""
    def check_range(start, end):
        return all(s[i] == s[end - (i - start)] for i in range(start, (start + end) // 2 + 1))

    l, r = 0, len(s) - 1
    while l < r:
        if s[l] != s[r]:
            return check_range(l + 1, r) or check_range(l, r - 1)
        l += 1
        r -= 1
    return True


# =============================================================================
# WAY 16: Class-based
# =============================================================================
class PalindromeChecker:
    def __init__(self, s):
        self.s = s

    def is_pal(self, l, r):
        while l < r:
            if self.s[l] != self.s[r]:
                return False
            l += 1
            r -= 1
        return True

    def can_be_palindrome(self):
        l, r = 0, len(self.s) - 1
        while l < r:
            if self.s[l] != self.s[r]:
                return self.is_pal(l + 1, r) or self.is_pal(l, r - 1)
            l += 1
            r -= 1
        return True


def validPalindrome_16(s):
    return PalindromeChecker(s).can_be_palindrome()


# =============================================================================
# WAY 17: One-liner using slicing (Pythonic but slow)
# =============================================================================
def validPalindrome_17(s):
    """One-liner using slicing."""
    if s == s[::-1]:
        return True
    n = len(s)
    # Try removing each char
    return any(s[:i] + s[i+1:] == (s[:i] + s[i+1:])[::-1] for i in range(n))


# =============================================================================
# WAY 18: With while-true break
# =============================================================================
def validPalindrome_18(s):
    """While-true with break."""
    l, r = 0, len(s) - 1
    while True:
        if l >= r:
            return True
        if s[l] != s[r]:
            # Try skip left
            l1, r1 = l + 1, r
            while l1 < r1 and s[l1] == s[r1]:
                l1 += 1
                r1 -= 1
            if l1 >= r1:
                return True
            # Try skip right
            l1, r1 = l, r - 1
            while l1 < r1 and s[l1] == s[r1]:
                l1 += 1
                r1 -= 1
            return l1 >= r1
        l += 1
        r -= 1


# =============================================================================
# WAY 19: With single mismatch detected flag
# =============================================================================
def validPalindrome_19(s):
    """Track single mismatch flag."""
    l, r = 0, len(s) - 1
    while l < r:
        if s[l] != s[r]:
            # Found mismatch - try both skips
            for skip_l, skip_r in [(l+1, r), (l, r-1)]:
                cl, cr = skip_l, skip_r
                while cl < cr:
                    if s[cl] != s[cr]:
                        break
                    cl += 1
                    cr -= 1
                else:
                    return True
            return False
        l += 1
        r -= 1
    return True


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def validPalindrome_20(s):
    """
    THE ONE TO MEMORIZE.

    Two-pointer from both ends. On mismatch, try skipping either char.

    Time:  O(n)
    Space: O(1)
    """
    def is_pal(l, r):
        while l < r:
            if s[l] != s[r]:
                return False
            l += 1
            r -= 1
        return True

    l, r = 0, len(s) - 1
    while l < r:
        if s[l] != s[r]:
            return is_pal(l + 1, r) or is_pal(l, r - 1)
        l += 1
        r -= 1
    return True


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to check if a string can become a palindrome by removing at
most one character."

Key Insight:
"Two-pointer from both ends. When we hit a mismatch, we have TWO
choices: skip the left char OR skip the right char. At least one of
these choices must lead to a palindrome (or neither, if the answer is
false)."

Algorithm:
1. l = 0, r = len(s) - 1.
2. While l < r:
   a. If s[l] == s[r]: advance both.
   b. Else: try skipping s[l] (check s[l+1:r+1] palindrome)
            OR skipping s[r] (check s[l:r] palindrome).
3. If we exit the loop, it's already a palindrome.
4. Return True if either skip works.

Edge Cases:
- 1-char string: True.
- 2-char same: True.
- 2-char different: True (can delete one).
- Already palindrome: True.
- No way to make palindrome: False.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Two-ptr   | O(n)   | O(1)   |
| Brute     | O(n^2) | O(n)   |
+-----------+--------+--------+

KEY TRICK:
On mismatch, you have a CHOICE. Try both and OR the results.

RELATED PROBLEMS:
- Valid Palindrome (LC 125): no deletion allowed.
- Palindrome Linked List (LC 234): two-pointer.
- Longest Palindromic Substring (LC 5): Manacher's.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Two-pointer (BEST)", validPalindrome_1),
        ("Way 2: Iterative inline", validPalindrome_2),
        ("Way 3: Recursive", validPalindrome_3),
        ("Way 4: Greedy single check", validPalindrome_4),
        ("Way 5: Brute force", validPalindrome_5),
        ("Way 6: Find first mismatch", validPalindrome_6),
        ("Way 7: Slicing reverse", validPalindrome_7),
        ("Way 8: Most concise", validPalindrome_8),
        ("Way 9: With helper", validPalindrome_9),
        ("Way 10: Generator", validPalindrome_10),
        ("Way 11: Recursive skip", validPalindrome_11),
        ("Way 12: Compare reverse", validPalindrome_12),
        ("Way 13: Deque", validPalindrome_13),
        ("Way 14: Function pointer", validPalindrome_14),
        ("Way 15: Lambda + any", validPalindrome_15),
        ("Way 16: Class OOP", validPalindrome_16),
        ("Way 17: One-liner slicing", validPalindrome_17),
        ("Way 18: While-true break", validPalindrome_18),
        ("Way 19: With skip flag", validPalindrome_19),
        ("Way 20: Final cleanest", validPalindrome_20),
    ]

    test_cases = [
        # (s, expected)
        ("aba", True),
        ("abca", True),
        ("abc", False),
        ("a", True),
        ("aa", True),
        ("ab", True),
        ("", True),
        ("racecar", True),
        ("deeee", True),
        ("eeccccbebaeeabebccceea", False),  # Tricky case
        ("aguokepatgbnvfqmgmlcupuufxoohdfpgjdmysgvhmvffcnqxjjxqncffvmhvgsymdjgpfdhooxfuupuculmgmqfvnbgtapekouga", True),
        ("ebcbbececabbacecbbcbe", True),
        ("abbcda", False),  # Cannot make palindrome by deleting 1
        ("abba", True),  # already palindrome
        ("abcdef", False),  # cannot be palindrome
        ("aab", True),  # delete last 'b' -> 'aa'
    ]

    print("=" * 70)
    print("VALID PALINDROME II - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/interview-prep/coding/valid-palindrome-ii")
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
                    if "race a car" not in s:  # Skip space-containing test
                        print(f"  X {name}: s='{s[:30]}', expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on s='{s[:30]}' - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)