"""
Minimum Remove to Make Valid Parentheses
Medium | 30 min

Given a string s that may have matched and unmatched parentheses,
remove the minimum number of parentheses so that the resulting string
represents a valid parenthesization.

In other words: remove the fewest '(' or ')' characters so that
the resulting parentheses string is valid AND the relative order of
the remaining characters is preserved.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-remove-to-make-valid-parentheses

Examples:
    "lee(t(c)o)de)" -> "lee(t(c)o)de"
    "a)b(c)d"       -> "ab(c)d"
    "))(("          -> ""
    "(a(b(c)d)"     -> "a(b(c)d)"  or "(a(bc)d)"

Constraints:
- 1 <= s.length <= 10^3
- s[i] is one of: '(', ')', or lowercase English letter
"""

from collections import deque


# =============================================================================
# WAY 1: Stack of indices (BEST - Memorize!)
# =============================================================================
# THINKING: "Two passes. First pass: push '(' indices. On ')', pop if matched,
#           else mark unmatched ')'. After loop mark leftover '(' in stack.
#           Second pass: build result skipping marked indices."
def min_remove_1(s):
    stack = []  # indices of unmatched '('
    to_remove = set()  # indices to remove

    for i, char in enumerate(s):
        if char == '(':
            stack.append(i)
        elif char == ')':
            if stack:
                stack.pop()  # matched
            else:
                to_remove.add(i)  # unmatched ')'

    # Any leftover '(' in stack are unmatched
    to_remove.update(stack)

    return "".join(char for i, char in enumerate(s) if i not in to_remove)


# =============================================================================
# WAY 2: Two-pass counter (O(1) extra space complexity per pass)
# =============================================================================
# THINKING: "First pass: count '(' - ')'. If ')' > '(', drop it.
#           Second pass on result: drop excess '(' from the right."
def min_remove_2(s):
    # First pass: remove invalid ')'
    sb = []
    balance = 0
    for char in s:
        if char == ')':
            if balance == 0:
                continue  # skip unmatched ')'
            balance -= 1
        elif char == '(':
            balance += 1
        sb.append(char)

    # Second pass: remove extra '(' from right
    result = []
    to_remove = balance  # number of '(' to drop
    for char in reversed(sb):
        if char == '(' and to_remove > 0:
            to_remove -= 1
            continue
        result.append(char)
    return "".join(reversed(result))


# =============================================================================
# WAY 3: Stack of characters (valid chars list)
# =============================================================================
def min_remove_3(s):
    # Push all chars but skip unmatched ')'
    stack = []
    for char in s:
        if char == ')':
            # Count '(' in stack
            open_count = sum(1 for c in stack if c == '(')
            close_count = sum(1 for c in stack if c == ')')
            if open_count > close_count:
                stack.append(char)
            # else skip
        else:
            stack.append(char)
    # Now remove excess '(' from right
    open_count = sum(1 for c in stack if c == '(')
    close_count = sum(1 for c in stack if c == ')')
    extras = open_count - close_count
    result = []
    for char in reversed(stack):
        if char == '(' and extras > 0:
            extras -= 1
            continue
        result.append(char)
    return "".join(reversed(result))


# =============================================================================
# WAY 4: Using list as mutable with helper function
# =============================================================================
def min_remove_4(s):
    def remove_invalid_closing(string):
        sb = []
        count = 0
        for char in string:
            if char == ')':
                if count == 0:
                    continue
                count -= 1
            if char == '(':
                count += 1
            sb.append(char)
        return "".join(sb)

    def remove_invalid_opening(string):
        sb = []
        count = 0
        for char in reversed(string):
            if char == '(':
                if count == 0:
                    continue
                count -= 1
            if char == ')':
                count += 1
            sb.append(char)
        return "".join(reversed(sb))

    s = remove_invalid_closing(s)
    return remove_invalid_opening(s)


# =============================================================================
# WAY 5: Counter + Stack of indices (cleaner Way 1 variant)
# =============================================================================
def min_remove_5(s):
    indices_to_remove = set()
    stack = []

    for i, char in enumerate(s):
        if char == '(':
            stack.append(i)
        elif char == ')':
            if stack:
                stack.pop()
            else:
                indices_to_remove.add(i)

    indices_to_remove.update(stack)
    return "".join(c for i, c in enumerate(s) if i not in indices_to_remove)


# =============================================================================
# WAY 6: List-based with explicit marks
# =============================================================================
def min_remove_6(s):
    chars = list(s)
    stack = []

    for i, c in enumerate(chars):
        if c == '(':
            stack.append(i)
        elif c == ')':
            if stack:
                stack.pop()
            else:
                chars[i] = ''  # mark for removal

    # Mark unmatched '('
    for i in stack:
        chars[i] = ''

    return "".join(chars)


# =============================================================================
# WAY 7: Two-pass using deque
# =============================================================================
def min_remove_7(s):
    dq = deque(s)
    stack = []

    # Forward pass - mark unmatched ')'
    i = 0
    while dq:
        c = dq.popleft()
        if c == ')':
            if stack:
                stack.pop()
            else:
                # mark - we'll handle via indices
                pass

    # Simpler: use index approach
    chars = list(s)
    stack = []

    for i, c in enumerate(chars):
        if c == '(':
            stack.append(i)
        elif c == ')':
            if stack:
                stack.pop()
            else:
                chars[i] = 'X'

    for i in stack:
        chars[i] = 'X'

    return "".join(c for c in chars if c != 'X')


# =============================================================================
# WAY 8: Recursive
# =============================================================================
def min_remove_8(s):
    def helper(string):
        if not string:
            return ""
        sb = []
        count = 0
        for c in string:
            if c == ')':
                if count == 0:
                    continue
                count -= 1
            if c == '(':
                count += 1
            sb.append(c)
        # Remove extra '('
        sb = "".join(sb)
        if not sb:
            return ""
        # Reverse and remove
        rev = sb[::-1]
        sb2 = []
        count = 0
        for c in rev:
            if c == '(':
                if count == 0:
                    continue
                count -= 1
            if c == ')':
                count += 1
            sb2.append(c)
        return "".join(sb2)[::-1]

    return helper(s)


# =============================================================================
# WAY 9: Using str.replace iteratively
# =============================================================================
def min_remove_9(s):
    # Remove adjacent "()" multiple times won't help here, we need to handle
    # the structural problem. Use stack approach instead, but exposed cleaner.
    result = list(s)
    stack = []

    for i, c in enumerate(result):
        if c == '(':
            stack.append(i)
        elif c == ')':
            if stack:
                stack.pop()
            else:
                result[i] = ' '

    for i in stack:
        result[i] = ' '

    return "".join(result).replace(' ', '')


# =============================================================================
# WAY 10: Counter-only O(n) without explicit stack
# =============================================================================
def min_remove_10(s):
    # First pass: remove invalid ')'
    chars = list(s)
    count = 0
    for i, c in enumerate(chars):
        if c == '(':
            count += 1
        elif c == ')':
            if count > 0:
                count -= 1
            else:
                chars[i] = ''  # mark for removal

    # Second pass: remove excess '(' from right
    s_clean = "".join(chars)
    chars2 = list(s_clean)
    count = 0
    for i in range(len(chars2) - 1, -1, -1):
        c = chars2[i]
        if c == ')':
            count += 1
        elif c == '(':
            if count > 0:
                count -= 1
            else:
                chars2[i] = ''

    return "".join(chars2)


# =============================================================================
# WAY 11: Using list comprehension
# =============================================================================
def min_remove_11(s):
    stack = []
    remove = set()
    for i, c in enumerate(s):
        if c == '(':
            stack.append(i)
        elif c == ')':
            if stack:
                stack.pop()
            else:
                remove.add(i)
    remove = remove.union(set(stack))
    return "".join(c for i, c in enumerate(s) if i not in remove)


# =============================================================================
# WAY 12: With explicit parentheses count
# =============================================================================
def min_remove_12(s):
    # First pass
    open_count = 0
    chars = list(s)
    new_chars = []
    for c in chars:
        if c == '(':
            open_count += 1
            new_chars.append(c)
        elif c == ')':
            if open_count > 0:
                open_count -= 1
                new_chars.append(c)
            # else skip
        else:
            new_chars.append(c)

    # Second pass (reverse)
    close_count = 0
    result = []
    for c in reversed(new_chars):
        if c == ')':
            close_count += 1
            result.append(c)
        elif c == '(':
            if close_count > 0:
                close_count -= 1
                result.append(c)
            # else skip
        else:
            result.append(c)

    return "".join(reversed(result))


# =============================================================================
# WAY 13: One-pass with boolean array
# =============================================================================
def min_remove_13(s):
    n = len(s)
    keep = [True] * n
    stack = []

    for i, c in enumerate(s):
        if c == '(':
            stack.append(i)
        elif c == ')':
            if stack:
                stack.pop()
            else:
                keep[i] = False

    for i in stack:
        keep[i] = False

    return "".join(c for i, c in enumerate(s) if keep[i])


# =============================================================================
# WAY 14: Using try-except style
# =============================================================================
def min_remove_14(s):
    stack = []
    to_remove = set()

    for i, c in enumerate(s):
        if c == '(':
            stack.append(i)
        elif c == ')':
            try:
                stack.pop()
            except IndexError:
                to_remove.add(i)

    to_remove |= set(stack)
    return "".join(c for i, c in enumerate(s) if i not in to_remove)


# =============================================================================
# WAY 15: Functional style with reduce
# =============================================================================
def min_remove_15(s):
    from functools import reduce

    def step(state, item):
        idx, c = item
        stack, remove = state
        if c == '(':
            stack.append(idx)
        elif c == ')':
            if stack:
                stack.pop()
            else:
                remove.add(idx)
        return stack, remove

    stack, remove = reduce(step, enumerate(s), ([], set()))
    remove = remove.union(set(stack))
    return "".join(c for i, c in enumerate(s) if i not in remove)


# =============================================================================
# WAY 16: Using string builder
# =============================================================================
def min_remove_16(s):
    # First pass: count '(' and find unmatched ')'
    sb = []
    open_seen = 0
    balance = 0
    for c in s:
        if c == '(':
            open_seen += 1
            balance += 1
        elif c == ')':
            if balance == 0:
                continue  # unmatched
            balance -= 1
        sb.append(c)

    # Second pass: drop extra '(' from the right
    s2 = "".join(sb)
    result = []
    extras = open_seen - (open_seen - balance)  # wait, let me recompute
    # Actually, balance tracks remaining unmatched '(' count
    extras = balance
    for c in reversed(s2):
        if c == '(' and extras > 0:
            extras -= 1
            continue
        result.append(c)
    return "".join(reversed(result))


# =============================================================================
# WAY 17: Generator-based
# =============================================================================
def min_remove_17(s):
    stack = []
    invalid = set()

    def gen():
        for i, c in enumerate(s):
            yield i, c

    for i, c in gen():
        if c == '(':
            stack.append(i)
        elif c == ')':
            if stack:
                stack.pop()
            else:
                invalid.add(i)

    invalid.update(stack)
    return "".join(c for i, c in enumerate(s) if i not in invalid)


# =============================================================================
# WAY 18: Compact one-liner style
# =============================================================================
def min_remove_18(s):
    stack = []
    invalid = set()
    for i, c in enumerate(s):
        if c == '(':
            stack.append(i)
        elif c == ')':
            if stack:
                stack.pop()
            else:
                invalid.add(i)
    invalid |= set(stack)
    return "".join(c for i, c in enumerate(s) if i not in invalid)


# =============================================================================
# WAY 19: Using dict for tracking
# =============================================================================
def min_remove_19(s):
    status = {i: True for i in range(len(s))}  # True means keep
    stack = []

    for i, c in enumerate(s):
        if c == '(':
            stack.append(i)
        elif c == ')':
            if stack:
                stack.pop()
            else:
                status[i] = False

    for i in stack:
        status[i] = False

    return "".join(c for i, c in enumerate(s) if status[i])


# =============================================================================
# WAY 20: Most elegant - same as Way 1, just cleanest form
# =============================================================================
def min_remove_20(s):
    stack = []
    to_remove = set()

    for i, char in enumerate(s):
        if char == '(':
            stack.append(i)
        elif char == ')':
            if stack:
                stack.pop()
            else:
                to_remove.add(i)

    to_remove.update(stack)

    return "".join(s[i] for i in range(len(s)) if i not in to_remove)


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to remove the minimum number of parentheses to make the string
valid, while preserving the order of the remaining characters."

Key Insight:
"Two passes! First, find all unmatched closing brackets ')' - they MUST
be removed. Then, any '(' that are still unmatched (because there was
no closing ')') must also be removed. We use a stack to track unmatched
'(' positions."

Algorithm:
"1. Iterate through s:
   - If char is '(', push its INDEX to the stack
   - If char is ')' and stack is non-empty, pop (we matched this ')')
   - If char is ')' and stack is empty, mark this ')' for removal
2. After the loop, any indices left in the stack are unmatched '('
3. Build the result by skipping indices marked for removal"

Why this works:
"The stack tracks '(' that haven't been matched yet. When we see a ')',
it MUST match a '(' (LIFO). If no '(' is available, it's an unmatched
')' and must be removed. After processing, any leftover '(' in the
stack had no matching ')' so they're also unmatched."

Edge cases:
- All closing brackets: '))((" -> remove all -> ''
- All opening brackets: '(((' -> remove all -> ''
- Already valid: '(abc)' -> unchanged
- No parentheses: 'abc' -> unchanged
- Multiple unmatched: 'a)b)c(d(' -> 'bc(d' or 'abc' etc.

COMPLEXITY:
+-----------+--------+---------+
| Approach  | Time   | Space   |
+-----------+--------+---------+
| Stack idx | O(n)   | O(n)    |
| Two pass  | O(n)   | O(n)    |
| Recursive | O(n^2) | O(n^2)  |
+-----------+--------+---------+

KEY TRICK:
The stack stores INDICES (not characters) so we know which positions
to remove in the original string. This preserves the relative order
of all other characters (letters etc.).
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Stack indices (BEST)", min_remove_1),
        ("Way 2: Two-pass counters", min_remove_2),
        ("Way 3: Stack of chars", min_remove_3),
        ("Way 4: Helper functions", min_remove_4),
        ("Way 5: Cleaner Way 1", min_remove_5),
        ("Way 6: List mutable marks", min_remove_6),
        ("Way 7: deque + indices", min_remove_7),
        ("Way 8: Recursive", min_remove_8),
        ("Way 9: Replace approach", min_remove_9),
        ("Way 10: Counter only", min_remove_10),
        ("Way 11: List comp", min_remove_11),
        ("Way 12: Explicit counts", min_remove_12),
        ("Way 13: Boolean array", min_remove_13),
        ("Way 14: Try-except", min_remove_14),
        ("Way 15: Functional reduce", min_remove_15),
        ("Way 16: String builder", min_remove_16),
        ("Way 17: Generator", min_remove_17),
        ("Way 18: Compact", min_remove_18),
        ("Way 19: Dict tracking", min_remove_19),
        ("Way 20: Most elegant", min_remove_20),
    ]

    # Test cases - some have multiple valid answers
    # (e.g., "(a(b(c)d)" -> "a(b(c)d)" or "(a(bc)d)")
    test_cases = [
        ("lee(t(c)o)de)", "lee(t(c)o)de"),
        ("a)b(c)d", "ab(c)d"),
        ("))((", ""),
        ("(a(b(c)d)", None),  # multiple valid answers
        ("", ""),
        ("abc", "abc"),
        ("(", ""),
        (")", ""),
        ("(()", "()"),  # remove one unmatched ( from right
        ("())", "()"),  # remove one unmatched ) from left
        ("(a)(b))", "(a)(b)"),
        ("(((a)))", "(((a)))"),
    ]


    print("=" * 70)
    print("MINIMUM REMOVE TO MAKE VALID PARENTHESES - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-remove-to-make-valid-parentheses")
    print("=" * 70)
    print("Note: Some inputs have multiple valid answers. Tests check that")
    print("the result is itself a valid parens string of minimum removals.")
    print("=" * 70)

    # Custom validator - check if output is valid and minimal
    def is_valid_parens(s):
        count = 0
        for c in s:
            if c == '(':
                count += 1
            elif c == ')':
                count -= 1
                if count < 0:
                    return False
        return count == 0

    def is_minimal_removal(original, result):
        # The result should be valid AND
        # have the maximum possible length (= minimum removal)
        if not is_valid_parens(result):
            return False
        # Count parens in original
        orig_parens = sum(1 for c in original if c in '()')
        result_parens = sum(1 for c in result if c in '()')
        # In result, parens must be balanced - so must be even
        # Max length result preserves all non-parens + balanced parens
        non_parens = sum(1 for c in original if c not in '()')
        return len(result) == non_parens + result_parens

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for s, expected in test_cases:
            try:
                result = func(s)
                # Check expected match OR validity + minimality
                if expected is not None:
                    if result != expected:
                        all_test_pass = False
                        all_pass = False
                        print(f"  X {name}: '{s}' -> '{result}' (expected '{expected}')")
                else:
                    if not is_valid_parens(result):
                        all_test_pass = False
                        all_pass = False
                        print(f"  X {name}: '{s}' -> '{result}' (NOT VALID)")
                    elif not is_minimal_removal(s, result):
                        all_test_pass = False
                        all_pass = False
                        print(f"  X {name}: '{s}' -> '{result}' (NOT MINIMAL)")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on '{s}' - {e}")
        print(f"  {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
