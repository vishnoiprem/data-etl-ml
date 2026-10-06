"""
Remove All Adjacent Duplicates In String
Easy | 15 min

Given a string, repeatedly remove adjacent duplicate letters (pairs).

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/solution-remove-all-adjacent-duplicates-in-string

Examples:
    "abbaca" -> "ca"
    "azbbzyac" -> "ac"
    "aa" -> ""
    "abc" -> "abc"

Constraints:
- 1 <= string.length <= 10^3
- Lowercase English letters only
"""


# =============================================================================
# WAY 1: Basic Stack (BEST - Memorize!)
# =============================================================================
# THINKING: "Pop when we see a duplicate of the top."
def remove_duplicates_1(s):
    stack = []
    for char in s:
        if stack and stack[-1] == char:
            stack.pop()
        else:
            stack.append(char)
    return "".join(stack)


# =============================================================================
# WAY 2: Using list comprehension
# =============================================================================
def remove_duplicates_2(s):
    stack = []
    [stack.pop() if stack and stack[-1] == c else stack.append(c) for c in s]
    return "".join(stack)


# =============================================================================
# WAY 3: With reduce
# =============================================================================
from functools import reduce


def remove_duplicates_3(s):
    return "".join(reduce(
        lambda stack, c: stack[:-1] if stack and stack[-1] == c else stack + [c],
        s, []
    ))


# =============================================================================
# WAY 4: Two-pointer (in-place)
# =============================================================================
def remove_duplicates_4(s):
    chars = list(s)
    write = 0
    for read in range(len(chars)):
        if write > 0 and chars[write - 1] == chars[read]:
            write -= 1
        else:
            chars[write] = chars[read]
            write += 1
    return "".join(chars[:write])


# =============================================================================
# WAY 5: Recursive
# =============================================================================
def remove_duplicates_5(s):
    if not s:
        return ""
    for i in range(len(s) - 1):
        if s[i] == s[i+1]:
            return remove_duplicates_5(s[:i] + s[i+2:])
    return s


# =============================================================================
# WAY 6: Counter-based
# =============================================================================
from collections import Counter


def remove_duplicates_6(s):
    counts = Counter(s)
    stack = []
    for char in s:
        if stack and stack[-1] == char:
            stack.pop()
            counts[char] -= 2
        else:
            stack.append(char)
            counts[char] += 1
    return "".join(stack)


# =============================================================================
# WAY 7: Using deque
# =============================================================================
from collections import deque


def remove_duplicates_7(s):
    stack = deque()
    for char in s:
        if stack and stack[-1] == char:
            stack.pop()
        else:
            stack.append(char)
    return "".join(stack)


# =============================================================================
# WAY 8: With helper function
# =============================================================================
def remove_duplicates_8(s):
    def process(stack, char):
        if stack and stack[-1] == char:
            stack.pop()
        else:
            stack.append(char)
        return stack

    stack = []
    for char in s:
        stack = process(stack, char)
    return "".join(stack)


# =============================================================================
# WAY 9: With explicit if-else
# =============================================================================
def remove_duplicates_9(s):
    stack = []
    for char in s:
        if not stack:
            stack.append(char)
        elif stack[-1] == char:
            stack.pop()
        else:
            stack.append(char)
    return "".join(stack)


# =============================================================================
# WAY 10: One-liner
# =============================================================================
def remove_duplicates_10(s):
    stack = []
    for c in s:
        if stack and stack[-1] == c:
            stack.pop()
        else:
            stack.append(c)
    return "".join(stack)


# =============================================================================
# WAY 11: Using a Stack class
# =============================================================================
class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        return self.items.pop() if self.items else None

    def peek(self):
        return self.items[-1] if self.items else None

    def is_empty(self):
        return not self.items


def remove_duplicates_11(s):
    stack = Stack()
    for char in s:
        if not stack.is_empty() and stack.peek() == char:
            stack.pop()
        else:
            stack.push(char)
    return "".join(stack.items)


# =============================================================================
# WAY 12: Try-except approach
# =============================================================================
def remove_duplicates_12(s):
    stack = []
    for char in s:
        try:
            if stack[-1] == char:
                stack.pop()
            else:
                stack.append(char)
        except IndexError:
            stack.append(char)
    return "".join(stack)


# =============================================================================
# WAY 13: Compact conditional
# =============================================================================
def remove_duplicates_13(s):
    stack = []
    for c in s:
        stack.pop() if stack and stack[-1] == c else stack.append(c)
    return "".join(stack)


# =============================================================================
# WAY 14: Using list as mutable
# =============================================================================
def remove_duplicates_14(s):
    result = []
    for char in s:
        if result and result[-1] == char:
            result.pop()
        else:
            result.append(char)
    return "".join(result)


# =============================================================================
# WAY 15: Index-based
# =============================================================================
def remove_duplicates_15(s):
    stack = []
    for i, char in enumerate(s):
        if stack and stack[-1] == char:
            stack.pop()
        else:
            stack.append(char)
    return "".join(stack)


# =============================================================================
# WAY 16: Most compact
# =============================================================================
def remove_duplicates_16(s):
    stack = []
    for c in s:
        if stack and stack[-1] == c:
            stack.pop()
        else:
            stack.append(c)
    return "".join(stack)


# =============================================================================
# WAY 17: Recursive with helper
# =============================================================================
def remove_duplicates_17(s):
    def helper(s, stack):
        if not s:
            return "".join(stack)
        if stack and stack[-1] == s[0]:
            return helper(s[1:], stack[:-1])
        else:
            return helper(s[1:], stack + [s[0]])

    return helper(s, [])


# =============================================================================
# WAY 18: With Counter tracking
# =============================================================================
from collections import defaultdict


def remove_duplicates_18(s):
    counts = defaultdict(int)
    stack = []
    for char in s:
        if stack and stack[-1] == char:
            stack.pop()
            counts[char] -= 2
        else:
            stack.append(char)
            counts[char] += 1
    return "".join(stack)


# =============================================================================
# WAY 19: Functional style
# =============================================================================
def remove_duplicates_19(s):
    stack = []
    for c in s:
        if stack and stack[-1] == c:
            stack.pop()
        else:
            stack.append(c)
    return "".join(stack)


# =============================================================================
# WAY 20: Most elegant
# =============================================================================
def remove_duplicates_20(s):
    stack = []
    for c in s:
        if stack and stack[-1] == c:
            stack.pop()
        else:
            stack.append(c)
    return "".join(stack)


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to repeatedly remove adjacent duplicate letters until no more
can be removed."

Key Insight:
"Similar to matching parentheses! When I see a character that matches
the top of my stack, they cancel out. Otherwise, I keep it."

Algorithm:
"1. Use a stack to track characters
2. For each character:
   - If stack is not empty AND top matches current, pop (they cancel)
   - Otherwise, push the character
3. The remaining stack is the answer"

Why stack works:
"LIFO behavior - the LAST character seen must be the one that cancels
with the current duplicate. Stack naturally handles this."

Edge cases:
- Empty string: return ""
- All duplicates: return ""
- No duplicates: return original

COMPLEXITY:
+-----------+--------+----------+
| Approach  | Time   | Space    |
+-----------+--------+----------+
| Stack     | O(n)   | O(n)     |
| Two ptr   | O(n)   | O(1)     |
| Recursive | O(n^2) | O(n)     |
+-----------+--------+----------+
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Basic Stack", remove_duplicates_1),
        ("Way 2: List comp", remove_duplicates_2),
        ("Way 3: Reduce", remove_duplicates_3),
        ("Way 4: Two pointer", remove_duplicates_4),
        ("Way 5: Recursive", remove_duplicates_5),
        ("Way 6: Counter", remove_duplicates_6),
        ("Way 7: deque", remove_duplicates_7),
        ("Way 8: Helper", remove_duplicates_8),
        ("Way 9: Explicit if-else", remove_duplicates_9),
        ("Way 10: One-liner", remove_duplicates_10),
        ("Way 11: Stack class", remove_duplicates_11),
        ("Way 12: Try-except", remove_duplicates_12),
        ("Way 13: Compact", remove_duplicates_13),
        ("Way 14: List mutable", remove_duplicates_14),
        ("Way 15: Index-based", remove_duplicates_15),
        ("Way 16: Most compact", remove_duplicates_16),
        ("Way 17: Recursive helper", remove_duplicates_17),
        ("Way 18: Counter track", remove_duplicates_18),
        ("Way 19: Functional", remove_duplicates_19),
        ("Way 20: Most elegant", remove_duplicates_20),
    ]

    test_cases = [
        ("abbaca", "ca"),
        ("azbbzyac", "ac"),
        ("aa", ""),
        ("abc", "abc"),
        ("g", "g"),
        ("ggaabcdeb", "gcbdeb"),  # ggaabcdeb: g,g(a)g pops, a,a(c)a pops, c, d, e, b
        ("abbabccblkklu", "abcu"),  # iterative removal
        ("aannkwwwkkkwna", "ankwna"),
    ]

    print("=" * 70)
    print("REMOVE ALL ADJACENT DUPLICATES IN STRING - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/solution-remove-all-adjacent-duplicates-in-string")
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
                    print(f"  ✗ {name}: '{s}' -> '{result}' (expected '{expected}')")
            except RecursionError:
                all_test_pass = False
                all_pass = False
                print(f"  ✗ {name}: RECURSION ERROR on '{s}'")
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
