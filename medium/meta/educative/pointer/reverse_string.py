"""
Reverse String
Easy | 15 min

Given a character array s, reverse it in-place using O(1) extra memory.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/reverse-string

Examples:
    ["h","e","l","l","o"] -> ["o","l","l","e","h"]
    ["H","a","n","n","a","h"] -> ["h","a","n","n","a","H"]
    ["a"] -> ["a"]
    [] -> []

Constraints:
- 1 <= s.length <= 1000
- Each s[i] is a printable ASCII character.
- Must be in-place, O(1) extra memory.

KEY INSIGHT:
Two pointers from both ends. Swap s[left] and s[right].
Move inward until pointers meet. Each element moves at most once.

Time:  O(n) — single pass.
Space: O(1) — in-place.
"""


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT REVERSE STRING:

1. UNDERSTAND THE PROBLEM:
   "Reverse a character array IN-PLACE with O(1) extra memory."

2. KEY OBSERVATION:
   "To reverse, the i-th char from left should become the i-th char from right.
   Position i swaps with position n-1-i. We swap in pairs."

3. TWO-POINTER GREEDY:
   "left starts at 0, right starts at n-1.
   While left < right:
     swap s[left] and s[right].
     left++; right--.
   When left >= right, we're done (middle element stays if odd length)."

4. WHY IN-PLACE WORKS:
   "Each swap correctly positions TWO characters.
   After n/2 swaps, all characters are in their final positions."

5. EDGE CASES:
   - Empty: nothing to do.
   - Single char: nothing to swap.
   - Two chars: one swap.
   - Even length: n/2 swaps.
   - Odd length: (n-1)/2 swaps, middle stays.

6. COMPLEXITY:
   +----------+--------+--------+
   | Approach | Time   | Space  |
   +----------+--------+--------+
   | Two ptr  | O(n)   | O(1)   |
   | New arr  | O(n)   | O(n)   |
   | Reversed | O(n)   | O(n)   |
   +----------+--------+--------+

7. WHY TWO POINTERS:
   - In-place: O(1) extra.
   - Single pass: each char touched twice (or once at middle).
   - Simple to implement and reason about.
"""


# =============================================================================
# WAY 1: Two-pointer in-place (BEST - Memorize!)
# =============================================================================
def reverse_string_1(s):
    """
    Two pointers from both ends. Swap inward.
    O(1) extra memory.
    """
    left, right = 0, len(s) - 1
    while left < right:
        s[left], s[right] = s[right], s[left]
        left += 1
        right -= 1
    return s


# =============================================================================
# WAY 2: Pythonic tuple swap
# =============================================================================
def reverse_string_2(s):
    """Same as Way 1 but with explicit variables for clarity."""
    start = 0
    end = len(s) - 1
    while start < end:
        start_char = s[start]
        end_char = s[end]
        s[start] = end_char
        s[end] = start_char
        start += 1
        end -= 1
    return s


# =============================================================================
# WAY 3: For loop with range
# =============================================================================
def reverse_string_3(s):
    """Use for loop with half range."""
    n = len(s)
    for i in range(n // 2):
        s[i], s[n - 1 - i] = s[n - 1 - i], s[i]
    return s


# =============================================================================
# WAY 4: Recursive in-place
# =============================================================================
def reverse_string_4(s):
    """Recursive: swap outer pair, recurse on inner."""

    def helper(left, right):
        if left >= right:
            return
        s[left], s[right] = s[right], s[left]
        helper(left + 1, right - 1)

    helper(0, len(s) - 1)
    return s


# =============================================================================
# WAY 5: While loop with half range
# =============================================================================
def reverse_string_5(s):
    """While loop with i < n//2."""
    n = len(s)
    i = 0
    while i < n // 2:
        s[i], s[n - 1 - i] = s[n - 1 - i], s[i]
        i += 1
    return s


# =============================================================================
# WAY 6: Use list slicing + write back (NOT in-place, educational)
# =============================================================================
def reverse_string_6(s):
    """Reverse slice, then write back. NOT in-place but simple."""
    n = len(s)
    rev = s[::-1]
    for i in range(n):
        s[i] = rev[i]
    return s


# =============================================================================
# WAY 7: Stack-based (extra space, educational)
# =============================================================================
def reverse_string_7(s):
    """Use stack. Push all, then pop. O(n) space."""
    stack = list(s)
    for i in range(len(s)):
        s[i] = stack.pop()
    return s


# =============================================================================
# WAY 8: Class OOP
# =============================================================================
class StringReverser:
    def __init__(self, s):
        self.s = s

    def reverse(self):
        left, right = 0, len(self.s) - 1
        while left < right:
            self.s[left], self.s[right] = self.s[right], self.s[left]
            left += 1
            right -= 1
        return self.s


def reverse_string_8(s):
    return StringReverser(s).reverse()


# =============================================================================
# WAY 9: XOR swap (no temp variable, educational)
# =============================================================================
def reverse_string_9(s):
    """XOR swap. Avoids temp variable. Caveat: i != j for safety."""
    left, right = 0, len(s) - 1
    while left < right:
        # Python: chr XOR ord - need to use ord() to handle chars.
        s[left] = chr(ord(s[left]) ^ ord(s[right]))
        s[right] = chr(ord(s[left]) ^ ord(s[right]))
        s[left] = chr(ord(s[left]) ^ ord(s[right]))
        left += 1
        right -= 1
    return s


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def reverse_string_10(s):
    """
    THE ONE TO MEMORIZE.

    Two pointers from both ends. Swap inward until pointers meet.
    Python's tuple swap makes it clean.

    Time:  O(n).
    Space: O(1).
    """
    left, right = 0, len(s) - 1
    while left < right:
        s[left], s[right] = s[right], s[left]
        left += 1
        right -= 1
    return s


# =====================================================
# Solutions 11-20
# =====================================================


# Solution 11: Using reversed() builtin
def reverse_string_11(s):
    s[:] = reversed(s)
    return s


# Solution 12: Reverse slice assignment
def reverse_string_12(s):
    s[:] = s[::-1]
    return s


# Solution 13: List comprehension (build new list)
def reverse_string_13(s):
    n = len(s)
    for i in range(n // 2):
        s[i], s[n - 1 - i] = s[n - 1 - i], s[i]
    return s


# Solution 14: While loop (manual two-pointer)
def reverse_string_14(s):
    i, j = 0, len(s) - 1
    while i < j:
        s[i], s[j] = s[j], s[i]
        i += 1
        j -= 1
    return s


# Solution 15: For-loop with reversed indices
def reverse_string_15(s):
    n = len(s)
    for i in range(n - 1, -1, -1):
        s.append(s[i])
        # But we already appended s[i] which is wrong order — this needs different approach
    # Actually, simpler: build reversed then replace
    s[:] = [s[i] for i in range(n - 1, -1, -1)]
    return s


# Solution 16: Use list() with reversed
def reverse_string_16(s):
    s[:] = list(reversed(s))
    return s


# Solution 17: Pop and insert (slow)
def reverse_string_17(s):
    out = []
    while s:
        out.append(s.pop())
    s.extend(out)
    return s


# Solution 18: Numpy
def reverse_string_18(s):
    try:
        import numpy as np
        s[:] = list(np.array(s)[::-1])
        return s
    except ImportError:
        s.reverse()
        return s


# Solution 19: Recursive swap
def reverse_string_19(s):
    def helper(lo, hi):
        if lo >= hi:
            return
        s[lo], s[hi] = s[hi], s[lo]
        helper(lo + 1, hi - 1)
    helper(0, len(s) - 1)
    return s


# Solution 20: Single-pass from middle, swap symmetric pairs
def reverse_string_20(s):
    mid = len(s) // 2
    for i in range(mid):
        s[i], s[-1 - i] = s[-1 - i], s[i]
    return s


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Two-pointer (BEST)", reverse_string_1),
        ("Way 2: Tuple swap explicit", reverse_string_2),
        ("Way 3: For loop half", reverse_string_3),
        ("Way 4: Recursive", reverse_string_4),
        ("Way 5: While half", reverse_string_5),
        ("Way 6: Slice + write", reverse_string_6),
        ("Way 7: Stack-based", reverse_string_7),
        ("Way 8: Class OOP", reverse_string_8),
        ("Way 9: XOR swap", reverse_string_9),
        ("Way 10: Final cleanest", reverse_string_10),
        ("Way 11: reversed()", reverse_string_11),
        ("Way 12: Slice [::-1]", reverse_string_12),
        ("Way 13: For-loop half", reverse_string_13),
        ("Way 14: While two-ptr", reverse_string_14),
        ("Way 15: Reorder reverse", reverse_string_15),
        ("Way 16: list(reversed)", reverse_string_16),
        ("Way 17: Pop and append", reverse_string_17),
        ("Way 18: numpy", reverse_string_18),
        ("Way 19: Recursive swap", reverse_string_19),
        ("Way 20: Mid-symmetric", reverse_string_20),
    ]

    def run_test(name, func, inp, expected):
        """Run a single test, copying input so we don't mutate original."""
        s_copy = list(inp)
        result = func(s_copy)
        if result != expected:
            return False, f"got={result}, expected={expected}"
        return True, ""

    test_cases = [
        # (input, expected)
        (["h", "e", "l", "l", "o"], ["o", "l", "l", "e", "h"]),
        (["H", "a", "n", "n", "a", "h"], ["h", "a", "n", "n", "a", "H"]),
        (["a"], ["a"]),
        (["a", "b"], ["b", "a"]),
        ([], []),
        (["a", "b", "c"], ["c", "b", "a"]),
        (["1", "2", "3", "4"], ["4", "3", "2", "1"]),
        (list("hello"), list("olleh")),
        (list("abcde"), list("edcba")),
    ]

    print("=" * 70)
    print("REVERSE STRING - 10 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/reverse-string")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for inp, expected in test_cases:
            try:
                ok, msg = run_test(name, func, inp, expected)
                if not ok:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: inp={inp}, {msg}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: inp={inp}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)