"""
Valid Parentheses
Easy | 15 min

Given a string of parentheses, check if they form a valid sequence.

Conditions:
- Every opening bracket must be closed by the same type
- Brackets must be closed in correct order

Constraints:
- 1 <= s.length <= 10^3
- Only contains: ( ) [ ] { }

Examples:
    "()" -> True
    "()[]{}" -> True
    "(]" -> False
    "([)]" -> False
    "{[]}" -> True

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/valid-parentheses
"""

from collections import deque
from functools import reduce


# =============================================================================
# WAY 1: Basic Stack (BEST - Memorize!)
# =============================================================================
# THINKING: "Push opening brackets. When closing, check top of stack."
def is_valid_1(s):
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}

    for char in s:
        if char in mapping:
            if stack and stack[-1] == mapping[char]:
                stack.pop()
            else:
                return False
        else:
            stack.append(char)

    return not stack


# =============================================================================
# WAY 2: With closing set
# =============================================================================
def is_valid_2(s):
    stack = []
    closing = {')', '}', ']'}
    pairs = {')': '(', '}': '{', ']': '['}

    for char in s:
        if char in closing:
            if not stack or stack[-1] != pairs[char]:
                return False
            stack.pop()
        else:
            stack.append(char)

    return len(stack) == 0


# =============================================================================
# WAY 3: Replace approach (clever!)
# =============================================================================
def is_valid_3(s):
    while '()' in s or '[]' in s or '{}' in s:
        s = s.replace('()', '').replace('[]', '').replace('{}', '')
    return len(s) == 0


# =============================================================================
# WAY 4: List as stack with explicit checks
# =============================================================================
def is_valid_4(s):
    stack = []
    for char in s:
        if char in '({[':
            stack.append(char)
        elif char == ')' and (not stack or stack.pop() != '('):
            return False
        elif char == '}' and (not stack or stack.pop() != '{'):
            return False
        elif char == ']' and (not stack or stack.pop() != '['):
            return False
    return not stack


# =============================================================================
# WAY 5: Using zip-based mapping
# =============================================================================
def is_valid_5(s):
    stack = []
    pairs = dict(zip('({[', ')}]'))

    for char in s:
        if char in '({[':
            stack.append(char)
        elif stack and stack[-1] == pairs.get(char):
            stack.pop()
        else:
            return False

    return not stack


# =============================================================================
# WAY 6: Counter-based
# =============================================================================
def is_valid_6(s):
    stack = []
    for char in s:
        if char in '([{':
            stack.append(char)
        else:
            if not stack:
                return False
            top = stack.pop()
            if char == ')' and top != '(':
                return False
            if char == '}' and top != '{':
                return False
            if char == ']' and top != '[':
                return False
    return not stack


# =============================================================================
# WAY 7: One-liner with reduce
# =============================================================================
def is_valid_7(s):
    pairs = {')': '(', '}': '{', ']': '['}
    try:
        result = reduce(
            lambda stack, c: stack[:-1] if c in pairs and stack and stack[-1] == pairs[c]
            else stack + [c] if c not in pairs
            else None,
            s,
            []
        )
        return result == []
    except:
        return False


# =============================================================================
# WAY 8: With try/except
# =============================================================================
def is_valid_8(s):
    stack = []
    pairs = {'(': ')', '{': '}', '[': ']'}

    try:
        for char in s:
            if char in pairs:
                stack.append(char)
            else:
                if stack.pop() not in pairs:
                    return False
    except (IndexError, KeyError):
        return False

    return not stack


# =============================================================================
# WAY 9: Using enumerate
# =============================================================================
def is_valid_9(s):
    stack = []
    open_chars = set('({[')
    close_map = {'(': ')', '{': '}', '[': ']'}

    for i, char in enumerate(s):
        if char in open_chars:
            stack.append(char)
        elif stack:
            top = stack.pop()
            if close_map[top] != char:
                return False
        else:
            return False

    return len(stack) == 0


# =============================================================================
# WAY 10: Most compact
# =============================================================================
def is_valid_10(s):
    stack = []
    pairs = {')': '(', ']': '[', '}': '{'}
    for c in s:
        if c in pairs:
            if not stack or stack.pop() != pairs[c]:
                return False
        else:
            stack.append(c)
    return not stack


# =============================================================================
# WAY 11: With early exit
# =============================================================================
def is_valid_11(s):
    stack = []
    pairs = {')': '(', '}': '{', ']': '['}

    for char in s:
        if char in '({[':
            stack.append(char)
        elif not stack or stack[-1] != pairs[char]:
            return False
        else:
            stack.pop()

    return len(stack) == 0


# =============================================================================
# WAY 12: Using Stack class
# =============================================================================
class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        return self.items.pop() if self.items else None

    def is_empty(self):
        return len(self.items) == 0

    def peek(self):
        return self.items[-1] if self.items else None


def is_valid_12(s):
    stack = Stack()
    pairs = {')': '(', '}': '{', ']': '['}

    for char in s:
        if char in pairs.values():
            stack.push(char)
        elif char in pairs:
            if stack.is_empty() or stack.pop() != pairs[char]:
                return False

    return stack.is_empty()


# =============================================================================
# WAY 13: With explicit checks for each bracket
# =============================================================================
def is_valid_13(s):
    stack = []
    for c in s:
        if c == '(' or c == '{' or c == '[':
            stack.append(c)
        elif c == ')':
            if not stack or stack[-1] != '(':
                return False
            stack.pop()
        elif c == '}':
            if not stack or stack[-1] != '{':
                return False
            stack.pop()
        elif c == ']':
            if not stack or stack[-1] != '[':
                return False
            stack.pop()
    return len(stack) == 0


# =============================================================================
# WAY 14: Using collections.deque
# =============================================================================
def is_valid_14(s):
    stack = deque()
    pairs = {')': '(', '}': '{', ']': '['}

    for char in s:
        if char in pairs.values():
            stack.append(char)
        elif char in pairs:
            if not stack or stack.pop() != pairs[char]:
                return False

    return len(stack) == 0


# =============================================================================
# WAY 15: With helper function
# =============================================================================
def is_valid_15(s):
    def matches(opening, closing):
        return (opening == '(' and closing == ')') or \
               (opening == '{' and closing == '}') or \
               (opening == '[' and closing == ']')

    stack = []
    for char in s:
        if char in '({[':
            stack.append(char)
        elif stack and matches(stack.pop(), char):
            continue
        else:
            return False

    return not stack


# =============================================================================
# WAY 16: Generator-based
# =============================================================================
def is_valid_16(s):
    stack = []
    pairs = {')': '(', '}': '{', ']': '['}
    gen = (c for c in s)

    for char in gen:
        if char in '({[':
            stack.append(char)
        elif not stack or stack.pop() != pairs.get(char):
            return False

    return not stack


# =============================================================================
# WAY 17: Push expected closer (elegant!)
# =============================================================================
def is_valid_17(s):
    pairs = {'(': ')', '{': '}', '[': ']'}
    stack = []

    for c in s:
        if c in pairs:
            stack.append(pairs[c])  # Push what we expect
        elif stack and stack[-1] == c:
            stack.pop()
        else:
            return False

    return not stack


# =============================================================================
# WAY 18: With explicit closing set
# =============================================================================
def is_valid_18(s):
    stack = []
    pairs = {')': '(', '}': '{', ']': '['}
    closing = set(pairs.keys())

    for c in s:
        if c in closing:
            if stack and stack[-1] == pairs[c]:
                stack.pop()
            else:
                return False
        else:
            stack.append(c)

    return len(stack) == 0


# =============================================================================
# WAY 19: Most elegant push-expected
# =============================================================================
def is_valid_19(s):
    pairs = {'(': ')', '{': '}', '[': ']'}
    stack = []

    for c in s:
        if c in pairs:
            stack.append(pairs[c])
        elif stack and stack[-1] == c:
            stack.pop()
        else:
            return False

    return not stack


# =============================================================================
# WAY 20: Cleanest with all helpers
# =============================================================================
def is_valid_20(s):
    pairs = {')': '(', ']': '[', '}': '{'}
    stack = []

    for c in s:
        if c in pairs:
            if not stack or stack.pop() != pairs[c]:
                return False
        else:
            stack.append(c)

    return not stack


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to verify that brackets are properly matched and ordered."

Key Insight:
"This is a classic stack problem because the LAST opening bracket must
be closed FIRST. The LIFO behavior of a stack perfectly matches this
requirement."

Algorithm:
"1. For each character:
   - If it's an opening bracket, push it on the stack
   - If it's a closing bracket, check if it matches the top of the stack
   - If matches, pop. If not, return False.
2. At the end, the stack should be empty for valid input."

Why this works:
"The stack keeps track of which opening brackets are waiting to be closed.
The top of the stack is always the most recent unclosed bracket, which
must match the next closing bracket we encounter."

Edge cases:
- Single bracket: invalid (no pair)
- All opening: invalid (stack not empty at end)
- All closing: invalid (stack underflow)
- Empty string: valid (stack is empty)

COMPLEXITY:
+-----------+--------+----------+
| Approach  | Time   | Space    |
+-----------+--------+----------+
| Stack     | O(n)   | O(n)     |
+-----------+--------+----------+
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Basic Stack", is_valid_1),
        ("Way 2: With closing set", is_valid_2),
        ("Way 3: Replace approach", is_valid_3),
        ("Way 4: List as stack", is_valid_4),
        ("Way 5: Zip mapping", is_valid_5),
        ("Way 6: Counter-based", is_valid_6),
        ("Way 7: One-liner reduce", is_valid_7),
        ("Way 8: Try/except", is_valid_8),
        ("Way 9: Enumerate", is_valid_9),
        ("Way 10: Most compact", is_valid_10),
        ("Way 11: Early exit", is_valid_11),
        ("Way 12: Stack class", is_valid_12),
        ("Way 13: Explicit checks", is_valid_13),
        ("Way 14: deque", is_valid_14),
        ("Way 15: Helper function", is_valid_15),
        ("Way 16: Generator", is_valid_16),
        ("Way 17: Push expected", is_valid_17),
        ("Way 18: Explicit closing", is_valid_18),
        ("Way 19: Most elegant", is_valid_19),
        ("Way 20: Cleanest", is_valid_20),
    ]

    test_cases = [
        ("()", True),
        ("()[]{}", True),
        ("(]", False),
        ("([)]", False),
        ("{[]}", True),
        ("", True),
        ("(", False),
        (")", False),
        ("(((((", False),
        (")))))", False),
        ("{[()]}", True),
        ("{[(])}", False),
    ]

    print("=" * 70)
    print("VALID PARENTHESES - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/valid-parentheses")
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
                status = "✓" if result == expected else "✗"
                if not all_test_pass and status == "✗":
                    print(f"  {status} {name}: '{s}' -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  ✗ {name}: ERROR on '{s}' - {e}")
        print(f"  {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS! 🎉")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
