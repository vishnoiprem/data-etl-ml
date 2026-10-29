"""
Remove K Digits
Medium | 30 min

Given string num representing a non-negative integer and an integer k,
remove k digits from the number so that the new number is the smallest
possible. Return the new number as a string (no leading zeros, except
when the result is "0").

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/remove-k-digits

Examples:
    num="1432219", k=3 -> "1219"  (remove 4, 3, 2)
    num="10200", k=1   -> "200"   (remove 1)
    num="10", k=2      -> "0"     (remove both)
    num="112", k=1     -> "11"    (remove 1)
    num="9", k=1       -> "0"     (remove the only digit)
    num="1234567", k=3 -> "1234"  (remove last 3)
    num="10", k=1      -> "0"     (remove 1, leaving "0")

Constraints:
- 1 <= num.length <= 10^3
- 0 <= k <= num.length
- num consists of digits only (no leading zeros except "0" itself).

KEY INSIGHT:
Greedy monotonic stack. Iterate digits; while k > 0 and stack top > current
digit: pop stack (remove that digit, decrement k). Push current digit.
After loop, if k > 0, remove last k digits from stack.
Remove leading zeros. Return "0" if empty.

Time:  O(n) — each digit pushed and popped at most once.
Space: O(n) — stack.
"""


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT REMOVE K DIGITS:

1. UNDERSTAND THE PROBLEM:
   "Remove k digits to make the smallest number."

2. KEY OBSERVATION:
   "For each digit, we want a SMALLER digit to its left if possible.
   If a digit is BIGGER than the next digit, removing it makes the number smaller.
   Example: 1[4]3 -> 13 (smaller than 14 by removing 4)."

3. GREEDY INSIGHT:
   "When scanning left-to-right, if the current digit is smaller than
   the previous digit (on top of stack), we should REMOVE the previous
   (bigger) digit. This is locally optimal and globally optimal."

4. MONOTONIC STACK:
   "Maintain a stack of digits that are non-decreasing from bottom to top.
   When we see a smaller digit, pop the larger digits on top of the stack
   (each pop removes one digit, decrement k).
   At end, if k > 0, remove from the top (last k digits are largest)."

5. EDGE CASES:
   - "10", k=1: remove '1', result "0".
   - "10", k=2: remove both, result "0".
   - All same digits: pop from anywhere, result same.
   - All increasing (12345): can't reduce by popping larger, pop from end.
   - Leading zeros: must strip.
   - Empty result: return "0".

6. COMPLEXITY:
   +----------+--------+--------+
   | Approach | Time   | Space  |
   +----------+--------+--------+
   | Stack    | O(n)   | O(n)   |
   | DP       | O(n*k) | O(n*k) |
   +----------+--------+--------+

7. WHY STACK > DP:
   - Each digit pushed once and popped at most once.
   - Linear time.
   - DP would consider all subsets of k digits to remove, O(n choose k).
"""


# =============================================================================
# WAY 1: Monotonic stack (BEST - Memorize!)
# =============================================================================
def remove_k_digits_1(num, k):
    """Greedy monotonic stack. Pop larger digits when smaller comes."""
    stack = []
    for digit in num:
        while k > 0 and stack and stack[-1] > digit:
            stack.pop()
            k -= 1
        stack.append(digit)
    # If k > 0, remove from end.
    if k > 0:
        stack = stack[:-k]
    # Strip leading zeros.
    result = "".join(stack).lstrip("0")
    return result if result else "0"


# =============================================================================
# WAY 2: Stack with explicit variable names
# =============================================================================
def remove_k_digits_2(num, k):
    """Same as Way 1 with clearer variable names."""
    stack = []
    remaining = k
    for digit in num:
        while remaining > 0 and stack and stack[-1] > digit:
            stack.pop()
            remaining -= 1
        stack.append(digit)
    final_stack = stack[: len(stack) - remaining]
    result = "".join(final_stack).lstrip("0")
    return result or "0"


# =============================================================================
# WAY 3: Stack with explicit pop count
# =============================================================================
def remove_k_digits_3(num, k):
    """Track pops explicitly with cleaner control flow."""
    stack = []
    for d in num:
        while k and stack and stack[-1] > d:
            stack.pop()
            k -= 1
        stack.append(d)
    result = "".join(stack[:-k] if k else stack).lstrip("0")
    return result or "0"


# =============================================================================
# WAY 4: Use deque for stack
# =============================================================================
def remove_k_digits_4(num, k):
    """Use collections.deque as stack."""
    from collections import deque
    stack = deque()
    for d in num:
        while k > 0 and stack and stack[-1] > d:
            stack.pop()
            k -= 1
        stack.append(d)
    if k > 0:
        for _ in range(k):
            stack.pop()
    result = "".join(stack).lstrip("0")
    return result or "0"


# =============================================================================
# WAY 5: Index-based zero strip
# =============================================================================
def remove_k_digits_5(num, k):
    """Same as Way 1 but using index iteration for leading zero removal."""
    stack = []
    for c in num:
        while k and stack and stack[-1] > c:
            stack.pop()
            k -= 1
        stack.append(c)
    if k:
        stack = stack[:-k]
    # Remove leading zeros via index.
    i = 0
    while i < len(stack) and stack[i] == "0":
        i += 1
    return "".join(stack[i:]) if i < len(stack) else "0"


# =============================================================================
# WAY 6: Class OOP
# =============================================================================
class RemoveKDigits:
    def __init__(self, num, k):
        self.num = num
        self.k = k

    def solve(self):
        stack = []
        k = self.k
        for d in self.num:
            while k and stack and stack[-1] > d:
                stack.pop()
                k -= 1
            stack.append(d)
        if k:
            stack = stack[:-k]
        result = "".join(stack).lstrip("0")
        return result or "0"


def remove_k_digits_6(num, k):
    return RemoveKDigits(num, k).solve()


# =============================================================================
# WAY 7: Brute force subsets (slow but correct, O(C(n,k)))
# =============================================================================
def remove_k_digits_7(num, k):
    """
    Generate all subsets of size len(num) - k by choosing k positions
    to remove. Compare using string with leading zeros preserved
    (so "0200" < "1000" lex) and strip at the end.
    """
    from itertools import combinations

    if k >= len(num):
        return "0"
    if k == 0:
        return num.lstrip("0") or "0"
    n = len(num)
    best = None
    for remove_idx in combinations(range(n), k):
        remove_set = set(remove_idx)
        # Build result WITHOUT stripping leading zeros for comparison.
        result = "".join(d for i, d in enumerate(num) if i not in remove_set)
        if best is None or result < best:
            best = result
    return (best or "").lstrip("0") or "0"


# =============================================================================
# WAY 8: Functional with reduce
# =============================================================================
def remove_k_digits_8(num, k):
    """Use functools.reduce to build the stack state."""
    from functools import reduce

    def helper(state, digit):
        stack, remaining = state
        stack = list(stack)
        while remaining > 0 and stack and stack[-1] > digit:
            stack.pop()
            remaining -= 1
        stack.append(digit)
        return (stack, remaining)

    stack, remaining = reduce(helper, num, ([], k))
    if remaining > 0:
        stack = stack[:-remaining]
    result = "".join(stack).lstrip("0")
    return result or "0"


# =============================================================================
# WAY 9: String list with char append
# =============================================================================
def remove_k_digits_9(num, k):
    """Same as Way 1, slightly different style."""
    stack = []
    for c in num:
        while k and stack and stack[-1] > c:
            stack.pop()
            k -= 1
        stack.append(c)
    final = stack[:-k] if k else stack
    # Strip leading zeros.
    res = "".join(final).lstrip("0")
    return res if res else "0"


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def remove_k_digits_10(num, k):
    """
    THE ONE TO MEMORIZE.

    Greedy monotonic stack. Pop larger digits when smaller arrives.
    After processing, remove remaining k from the end.
    Strip leading zeros; return "0" if empty.

    Time:  O(n).
    Space: O(n).
    """
    stack = []
    for digit in num:
        while k and stack and stack[-1] > digit:
            stack.pop()
            k -= 1
        stack.append(digit)
    # If k still > 0, drop from end.
    if k:
        stack = stack[:-k]
    # Strip leading zeros.
    result = "".join(stack).lstrip("0")
    return result if result else "0"


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Monotonic stack (BEST)", remove_k_digits_1),
        ("Way 2: Explicit variable names", remove_k_digits_2),
        ("Way 3: Stack list-based", remove_k_digits_3),
        ("Way 4: Deque stack", remove_k_digits_4),
        ("Way 5: Index-based zero strip", remove_k_digits_5),
        ("Way 6: Class OOP", remove_k_digits_6),
        ("Way 7: Recursive greedy window", remove_k_digits_7),
        ("Way 8: Functional reduce", remove_k_digits_8),
        ("Way 9: String list with append", remove_k_digits_9),
        ("Way 10: Final cleanest", remove_k_digits_10),
    ]

    test_cases = [
        # (num, k, expected)
        ("1432219", 3, "1219"),
        ("10200", 1, "200"),
        ("10", 2, "0"),
        ("112", 1, "11"),
        ("9", 1, "0"),
        ("1234567", 3, "1234"),
        ("1002001", 2, "1"),  # remove 1, then a 0
        ("112", 2, "1"),
        ("1234", 0, "1234"),
    ]

    print("=" * 70)
    print("REMOVE K DIGITS - 10 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/remove-k-digits")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for num, k, expected in test_cases:
            try:
                result = func(num, k)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: num={num!r}, k={k}, expected={expected!r}, got={result!r}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: num={num!r}, k={k}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)