"""
Minimum String Length After Removing Substrings
Easy | 15 min

Given a string s containing only uppercase English letters.
You can repeatedly remove "AB" or "CD" substrings.
Return the length of the shortest possible resulting string.

After each removal, the string joins and may form new "AB" or "CD" that
can also be removed.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-string-length-after-removing-substrings

Examples:
    "ABFCACDB"      -> 4  (remove "AB", "CD" -> "FCAB" then "AB" -> "FC", length 2... wait let me recheck)
    Actually: "ABFCACDB"
      - Remove "AB" at start: "FCACDB"
      - Remove "CD" at end: "FCAB"
      - Remove "AB" at end: "FC"
    Result: 2

    "ACBBD"         -> 5  (no AB or CD)
    "ABAB"          -> 0  (AB -> "" -> AB -> "")
    "CDCD"          -> 0  (similar)

Constraints:
- 1 <= s.length <= 100
- s consists only of uppercase English letters
"""


# =============================================================================
# WAY 1: Stack approach (BEST - Memorize!)
# =============================================================================
# THINKING: "Push chars. When new char forms 'AB' or 'CD' with stack top,
#           pop. The remaining stack is the answer."
def min_length_1(s):
    stack = []
    for char in s:
        if stack and stack[-1] + char in ("AB", "CD"):
            stack.pop()
        else:
            stack.append(char)
    return len(stack)


# =============================================================================
# WAY 2: Replace approach (clever but slow)
# =============================================================================
def min_length_2(s):
    while "AB" in s or "CD" in s:
        s = s.replace("AB", "").replace("CD", "")
    return len(s)


# =============================================================================
# WAY 3: Two stacks - for tracking
# =============================================================================
def min_length_3(s):
    stack = []
    removed_patterns = []
    for char in s:
        if stack and stack[-1] + char in ("AB", "CD"):
            removed_patterns.append(stack.pop() + char)
        else:
            stack.append(char)
    return len(stack)


# =============================================================================
# WAY 4: With deque
# =============================================================================
from collections import deque

def min_length_4(s):
    stack = deque()
    for char in s:
        if stack and stack[-1] + char in ("AB", "CD"):
            stack.pop()
        else:
            stack.append(char)
    return len(stack)


# =============================================================================
# WAY 5: Explicit if-else
# =============================================================================
def min_length_5(s):
    stack = []
    for char in s:
        if stack:
            top = stack[-1]
            if top == 'A' and char == 'B':
                stack.pop()
            elif top == 'C' and char == 'D':
                stack.pop()
            else:
                stack.append(char)
        else:
            stack.append(char)
    return len(stack)


# =============================================================================
# WAY 6: With set check
# =============================================================================
def min_length_6(s):
    stack = []
    removable = {("A", "B"), ("C", "D")}
    for char in s:
        if stack and (stack[-1], char) in removable:
            stack.pop()
        else:
            stack.append(char)
    return len(stack)


# =============================================================================
# WAY 7: One-liner style
# =============================================================================
def min_length_7(s):
    stack = []
    for c in s:
        if stack and ((stack[-1] == 'A' and c == 'B') or (stack[-1] == 'C' and c == 'D')):
            stack.pop()
        else:
            stack.append(c)
    return len(stack)


# =============================================================================
# WAY 8: Using reduce
# =============================================================================
def min_length_8(s):
    from functools import reduce

    def step(stack, char):
        if stack and stack[-1] + char in ("AB", "CD"):
            return stack[:-1]
        return stack + [char]

    result = reduce(step, s, [])
    return len(result)


# =============================================================================
# WAY 9: With list comprehension
# =============================================================================
def min_length_9(s):
    # Simulate stack using list ops
    stack = []
    [stack.pop() if stack and stack[-1] + c in ("AB", "CD") else stack.append(c) for c in s]
    return len(stack)


# =============================================================================
# WAY 10: Iterative with mutation
# =============================================================================
def min_length_10(s):
    stack = list(s)
    i = 0
    # Don't try this - too complex. Use Way 1.
    # Actually let me do a different approach: iterate and modify
    result_stack = []
    for char in s:
        if result_stack and result_stack[-1] + char in ("AB", "CD"):
            result_stack.pop()
        else:
            result_stack.append(char)
    return len(result_stack)


# =============================================================================
# WAY 11: With explicit lookup table
# =============================================================================
def min_length_11(s):
    lookup = {"A": "B", "C": "D"}
    stack = []
    for char in s:
        if stack and lookup.get(stack[-1]) == char:
            stack.pop()
        else:
            stack.append(char)
    return len(stack)


# =============================================================================
# WAY 12: Functional with recursion
# =============================================================================
def min_length_12(s):
    def helper(idx, stack):
        if idx == len(s):
            return len(stack)
        char = s[idx]
        if stack and stack[-1] + char in ("AB", "CD"):
            return helper(idx + 1, stack[:-1])
        else:
            return helper(idx + 1, stack + [char])

    return helper(0, [])


# =============================================================================
# WAY 13: With try-except (suboptimal but works)
# =============================================================================
def min_length_13(s):
    stack = []
    for char in s:
        try:
            if stack[-1] + char in ("AB", "CD"):
                stack.pop()
            else:
                stack.append(char)
        except IndexError:
            stack.append(char)
    return len(stack)


# =============================================================================
# WAY 14: Using re module (regex)
# =============================================================================
def min_length_14(s):
    import re
    prev = None
    while prev != s:
        prev = s
        s = re.sub(r'AB|CD', '', s)
    return len(s)


# =============================================================================
# WAY 15: Most compact (Way 1 minimal)
# =============================================================================
def min_length_15(s):
    st = []
    for c in s:
        if st and st[-1] + c in 'AB CD':
            st.pop()
        else:
            st.append(c)
    return len(st)


# =============================================================================
# WAY 16: Counter approach (track removable patterns)
# =============================================================================
def min_length_16(s):
    # Count chars and figure out minimum removals
    from collections import Counter
    counts = Counter(s)
    # 'A's can cancel with 'B's (min of count(A), count(B))
    ab_removals = min(counts['A'], counts['B'])
    cd_removals = min(counts['C'], counts['D'])
    return len(s) - 2 * (ab_removals + cd_removals)


# Note: Way 16 is INCORRECT for cases where A and B aren't adjacent.
# E.g., "BA" -> can't remove, length 2 not 0
# "AB" -> can remove, length 0
# Both have min(A,B) = 1, but only one is removable.
# Skip this way - it's a wrong approach. Replace with another valid way.


# =============================================================================
# WAY 16 (corrected): Stack approach with explicit pattern check
# =============================================================================
def min_length_16_v2(s):
    stack = []
    for char in s:
        if stack and ((stack[-1] == 'A' and char == 'B') or
                      (stack[-1] == 'C' and char == 'D')):
            stack.pop()
        else:
            stack.append(char)
    return len(stack)


# =============================================================================
# WAY 17: Using enumerate (still stack-based)
# =============================================================================
def min_length_17(s):
    stack = []
    for i, c in enumerate(s):
        if stack and stack[-1] + c in ("AB", "CD"):
            stack.pop()
        else:
            stack.append(c)
    return len(stack)


# =============================================================================
# WAY 18: Most elegant
# =============================================================================
def min_length_18(s):
    stack = []
    for char in s:
        if stack and (stack[-1] + char) in {"AB", "CD"}:
            stack.pop()
        else:
            stack.append(char)
    return len(stack)


# =============================================================================
# WAY 19: String builder (avoid stack overhead)
# =============================================================================
def min_length_19(s):
    # Use string as accumulator; rebuild when removal happens
    # Actually string concatenation is slow, use list
    result = []
    for char in s:
        if result and result[-1] + char in ("AB", "CD"):
            result.pop()
        else:
            result.append(char)
    return len(result)


# =============================================================================
# WAY 20: With character class check
# =============================================================================
def min_length_20(s):
    stack = []
    for char in s:
        if not stack:
            stack.append(char)
            continue
        top = stack[-1]
        if (top == 'A' and char == 'B') or (top == 'C' and char == 'D'):
            stack.pop()
        else:
            stack.append(char)
    return len(stack)


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to repeatedly remove 'AB' and 'CD' substrings until no more can
be removed, then return the final length."

Key Insight:
"This is a STACK problem!
Push each char. When the new char forms 'AB' or 'CD' with the top of
the stack, POP instead of push - they cancel out.
After processing all chars, the remaining stack length is the answer."

Algorithm:
"1. Initialize empty stack
2. For each character in s:
   - If stack is not empty AND (stack[-1] + char) is 'AB' or 'CD':
     * Pop the stack (the pattern is removed)
   - Else:
     * Push char onto stack
3. Return len(stack)"

Why this works:
"When 'AB' is removed, the chars BEFORE 'A' and AFTER 'B' become adjacent.
The stack tracks unresolved chars in order. When new char cancels with top,
it's like the removal - new chars can now pair with the new top!
This naturally handles cascading removals."

Edge cases:
- No removable patterns: length unchanged
- All 'AB' pairs: length 0
- Nested cases: "CABD" -> "CD" -> ""

COMPLEXITY:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Stack     | O(n)   | O(n)   |
| Replace   | O(n^2) | O(n)   |
+-----------+--------+--------+

KEY TRICK:
The stack gives us access to the LAST character. When new char + last char
forms a removable pattern, they CANCEL. This is similar to valid parentheses!
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Stack (BEST)", min_length_1),
        ("Way 2: Replace approach", min_length_2),
        ("Way 3: Two stacks", min_length_3),
        ("Way 4: deque", min_length_4),
        ("Way 5: Explicit if-else", min_length_5),
        ("Way 6: Set check", min_length_6),
        ("Way 7: One-liner", min_length_7),
        ("Way 8: reduce", min_length_8),
        ("Way 9: List comp", min_length_9),
        ("Way 10: Iterative mutation", min_length_10),
        ("Way 11: Lookup table", min_length_11),
        ("Way 12: Recursive", min_length_12),
        ("Way 13: Try-except", min_length_13),
        ("Way 14: Regex", min_length_14),
        ("Way 15: Most compact", min_length_15),
        ("Way 16: Explicit pattern check", min_length_16_v2),
        ("Way 17: enumerate", min_length_17),
        ("Way 18: Most elegant", min_length_18),
        ("Way 19: String builder", min_length_19),
        ("Way 20: Char class check", min_length_20),
    ]

    # Note: test_cases is defined further down (after the trace comments)

    # Let me re-trace "CBACD" carefully:
    # i=0, 'C': stack=[], push. stack=[C]
    # i=1, 'B': stack[-1]+B = "CB", not in (AB,CD). push. stack=[C,B]
    # i=2, 'A': "BA", not in (AB,CD). push. stack=[C,B,A]
    # i=3, 'C': "AC", not. push. stack=[C,B,A,C]
    # i=4, 'D': "CD" matches! pop. stack=[C,B,A]
    # Result: length 3

    # Trace "ABBACD":
    # i=0, 'A': stack=[A]
    # i=1, 'B': "AB" matches! pop. stack=[]
    # i=2, 'B': stack=[B]
    # i=3, 'A': "BA" no match. stack=[B,A]
    # i=4, 'C': "AC" no match. stack=[B,A,C]
    # i=5, 'D': "CD" matches! pop. stack=[B,A]
    # Result: length 2

    # Trace "ABCDABCD":
    # i=0, 'A': [A]
    # i=1, 'B': AB pops. []
    # i=2, 'C': [C]
    # i=3, 'D': CD pops. []
    # i=4, 'A': [A]
    # i=5, 'B': AB pops. []
    # i=6, 'C': [C]
    # i=7, 'D': CD pops. []
    # Result: 0

    test_cases = [
        ("ABFCACDB", 2),
        ("ACBBD", 5),
        ("ABAB", 0),
        ("CDCD", 0),
        ("ABC", 1),
        ("CBACD", 3),
        ("CABD", 0),
        ("ABBACD", 2),
        ("AAAA", 4),
        ("", 0),
        ("AB", 0),
        ("ABCDABCD", 0),
        ("BACAB", 3),
    ]

    print("=" * 70)
    print("MINIMUM STRING LENGTH AFTER REMOVING SUBSTRINGS - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-string-length-after-removing-substrings")
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
                    print(f"  X {name}: '{s}' -> {result} (expected {expected})")
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
