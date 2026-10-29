"""
Decode String
Medium | 30 min

Given an encoded string, return its decoded version.
The encoding rule: k[encoded_string] means repeat encoded_string k times.

Examples:
    "3[a]2[bc]"     -> "aaabcbc"
    "3[a2[c]]"      -> "accaccacc"
    "2[abc]3[cd]ef" -> "abcabccdcdcdef"
    "abc"           -> "abc"

Constraints:
- 1 <= s.length <= 30
- 1 <= k <= 100
- s consists of lowercase English letters, digits, and square brackets
- k is guaranteed to be a positive integer
- Input is always valid

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/decode-string
"""


# =============================================================================
# WAY 1: Two stacks - counts and strings (BEST - Memorize!)
# =============================================================================
# THINKING: "Stack of counts (for repetition) and stack of current strings.
#           When we see '[', push current state. When ']', pop and repeat."
def decode_1(s):
    count_stack = []
    string_stack = []
    current_string = ""
    current_num = 0

    for char in s:
        if char.isdigit():
            current_num = current_num * 10 + int(char)
        elif char == '[':
            count_stack.append(current_num)
            string_stack.append(current_string)
            current_num = 0
            current_string = ""
        elif char == ']':
            repeat_count = count_stack.pop()
            prev_string = string_stack.pop()
            current_string = prev_string + current_string * repeat_count
        else:
            current_string += char

    return current_string


# =============================================================================
# WAY 2: Single stack of tuples (count, string)
# =============================================================================
def decode_2(s):
    stack = []
    current_string = ""
    current_num = 0

    for char in s:
        if char.isdigit():
            current_num = current_num * 10 + int(char)
        elif char == '[':
            stack.append((current_num, current_string))
            current_num = 0
            current_string = ""
        elif char == ']':
            count, prev = stack.pop()
            current_string = prev + current_string * count
        else:
            current_string += char

    return current_string


# =============================================================================
# WAY 3: Recursive with index
# =============================================================================
def decode_3(s):
    """Recursive decode using an index list for mutability."""
    idx = [0]

    def parse():
        result = ""
        num = 0
        while idx[0] < len(s):
            ch = s[idx[0]]
            if ch.isdigit():
                num = num * 10 + int(ch)
                idx[0] += 1
            elif ch == '[':
                idx[0] += 1  # skip '['
                inner = parse()
                result += inner * num
                num = 0
            elif ch == ']':
                idx[0] += 1  # skip ']'
                return result
            else:
                result += ch
                idx[0] += 1
        return result

    return parse()


# =============================================================================
# WAY 4: Using deque
# =============================================================================
from collections import deque

def decode_4(s):
    count_stack = deque()
    string_stack = deque()
    current_string = ""
    current_num = 0

    for char in s:
        if char.isdigit():
            current_num = current_num * 10 + int(char)
        elif char == '[':
            count_stack.append(current_num)
            string_stack.append(current_string)
            current_num = 0
            current_string = ""
        elif char == ']':
            repeat_count = count_stack.pop()
            prev_string = string_stack.pop()
            current_string = prev_string + current_string * repeat_count
        else:
            current_string += char

    return current_string


# =============================================================================
# WAY 5: Stack of lists - cleaner state
# =============================================================================
def decode_5(s):
    stack = []  # each entry: (multiplier_so_far, accumulated_string)
    multiplier = 0
    result = ""

    for char in s:
        if char.isdigit():
            multiplier = multiplier * 10 + int(char)
        elif char == '[':
            stack.append((multiplier, result))
            multiplier = 0
            result = ""
        elif char == ']':
            prev_mult, prev_result = stack.pop()
            result = prev_result + result * prev_mult
        else:
            result += char

    return result


# =============================================================================
# WAY 6: Recursive approach with stack
# =============================================================================
def decode_6(s):
    idx = [0]

    def parse():
        result = ""
        num = 0
        while idx[0] < len(s):
            ch = s[idx[0]]
            if ch.isdigit():
                num = num * 10 + int(ch)
                idx[0] += 1
            elif ch == '[':
                idx[0] += 1
                inner = parse()
                result += inner * num
                num = 0
            elif ch == ']':
                idx[0] += 1
                return result
            else:
                result += ch
                idx[0] += 1
        return result

    return parse()


# =============================================================================
# WAY 7: Using class for cleaner state
# =============================================================================
class Decoder:
    def __init__(self, s):
        self.s = s
        self.stack = []
        self.current_string = ""
        self.current_num = 0

    def decode(self):
        for char in self.s:
            if char.isdigit():
                self.current_num = self.current_num * 10 + int(char)
            elif char == '[':
                self.stack.append((self.current_num, self.current_string))
                self.current_num = 0
                self.current_string = ""
            elif char == ']':
                count, prev = self.stack.pop()
                self.current_string = prev + self.current_string * count
            else:
                self.current_string += char
        return self.current_string


def decode_7(s):
    return Decoder(s).decode()


# =============================================================================
# WAY 8: With reduce
# =============================================================================
def decode_8(s):
    from functools import reduce

    def step(state, char):
        current_string, current_num, stack = state
        if char.isdigit():
            return (current_string, current_num * 10 + int(char), stack)
        elif char == '[':
            return ("", 0, stack + [(current_num, current_string)])
        elif char == ']':
            count, prev = stack[-1]
            return (prev + current_string * count, 0, stack[:-1])
        else:
            return (current_string + char, current_num, stack)

    result, _, _ = reduce(step, s, ("", 0, []))
    return result


# =============================================================================
# WAY 9: Compact tuple stack
# =============================================================================
def decode_9(s):
    stack = []
    num = 0
    res = ""

    for c in s:
        if c.isdigit():
            num = num * 10 + int(c)
        elif c == '[':
            stack.append((num, res))
            num = 0
            res = ""
        elif c == ']':
            n, prev = stack.pop()
            res = prev + res * n
        else:
            res += c

    return res


# =============================================================================
# WAY 10: Using index pointer and recursion
# =============================================================================
def decode_10(s):
    idx = [0]

    def helper():
        result = ""
        num = 0

        while idx[0] < len(s):
            ch = s[idx[0]]
            if ch.isdigit():
                num = num * 10 + int(ch)
                idx[0] += 1
            elif ch == '[':
                idx[0] += 1
                inner = helper()
                result += inner * num
                num = 0
            elif ch == ']':
                idx[0] += 1
                return result
            else:
                result += ch
                idx[0] += 1

        return result

    return helper()


# =============================================================================
# WAY 11: Stack with explicit brackets tracking (using string representations)
# =============================================================================
def decode_11(s):
    # Each entry: [count, accumulated_string] - similar to Way 19 but cleaner
    stack = [[1, ""]]
    num = 0

    for c in s:
        if c.isdigit():
            num = num * 10 + int(c)
        elif c == '[':
            stack.append([num, ""])
            num = 0
        elif c == ']':
            count, inner = stack.pop()
            stack[-1][1] += inner * count
        else:
            stack[-1][1] += c

    return stack[0][1]


# =============================================================================
# WAY 12: Two-pass with bracket matching
# =============================================================================
def decode_12(s):
    # First pass: identify all matching bracket pairs
    pairs = {}
    stack = []

    for i, char in enumerate(s):
        if char == '[':
            stack.append(i)
        elif char == ']':
            j = stack.pop()
            pairs[j] = i

    # Second pass: decode
    def decode_range(start, end):
        result = ""
        i = start + 1  # skip '['
        while i < end:
            if s[i].isdigit():
                num = 0
                while i < end and s[i].isdigit():
                    num = num * 10 + int(s[i])
                    i += 1
                # Now s[i] should be '['
                inner = decode_range(i, pairs[i])
                result += inner * num
                i = pairs[i] + 1
            elif s[i].isalpha():
                result += s[i]
                i += 1
            else:
                i += 1  # should be '['
        return result

    return decode_range(-1, len(s))


# =============================================================================
# WAY 13: Most compact - same as Way 1 but minimized
# =============================================================================
def decode_13(s):
    s1, s2 = [], []
    n, r = 0, ""
    for c in s:
        if c.isdigit():
            n = n * 10 + int(c)
        elif c == '[':
            s1.append(n)
            s2.append(r)
            n, r = 0, ""
        elif c == ']':
            r = s2.pop() + r * s1.pop()
        else:
            r += c
    return r


# =============================================================================
# WAY 14: Using iteration with explicit state
# =============================================================================
def decode_14(s):
    stack = []  # stores (count, current_string)
    count = 0
    result = ""

    for c in s:
        if c.isdigit():
            count = count * 10 + int(c)
        elif c == '[':
            stack.append((count, result))
            count = 0
            result = ""
        elif c == ']':
            cnt, prev = stack.pop()
            result = prev + result * cnt
        else:
            result += c

    return result


# =============================================================================
# WAY 15: With reduce (functional approach)
# =============================================================================
def decode_15(s):
    from functools import reduce

    # State: (current_string, current_num, count_stack, string_stack)
    # 4 elements - too complex for clean one-liner, but functional
    def step(state, char):
        cur_str, cur_num, count_stk, str_stk = state
        if char.isdigit():
            return (cur_str, cur_num * 10 + int(char), count_stk, str_stk)
        elif char == '[':
            return ("", 0, count_stk + [cur_num], str_stk + [cur_str])
        elif char == ']':
            cnt = count_stk[-1]
            prev = str_stk[-1]
            return (prev + cur_str * cnt, 0, count_stk[:-1], str_stk[:-1])
        else:
            return (cur_str + char, cur_num, count_stk, str_stk)

    result, _, _, _ = reduce(step, s, ("", 0, [], []))
    return result


# =============================================================================
# WAY 16: Using collections.deque and explicit tracking
# =============================================================================
def decode_16(s):
    from collections import deque

    count_deque = deque()
    string_deque = deque()
    num = 0
    res = ""

    for c in s:
        if c.isdigit():
            num = num * 10 + int(c)
        elif c == '[':
            count_deque.append(num)
            string_deque.append(res)
            num = 0
            res = ""
        elif c == ']':
            cnt = count_deque.pop()
            prev = string_deque.pop()
            res = prev + res * cnt
        else:
            res += c

    return res


# =============================================================================
# WAY 17: Recursive with global index
# =============================================================================
def decode_17(s):
    i = [0]

    def rec():
        result = ""
        num = 0
        while i[0] < len(s):
            ch = s[i[0]]
            if ch.isdigit():
                num = num * 10 + int(ch)
            elif ch == '[':
                i[0] += 1
                inner = rec()
                result += inner * num
                num = 0
                continue
            elif ch == ']':
                i[0] += 1
                return result
            else:
                result += ch
            i[0] += 1
        return result

    return rec()


# =============================================================================
# WAY 18: Most elegant - clean Way 1
# =============================================================================
def decode_18(s):
    count_stack = []
    string_stack = []
    current_string = ""
    k = 0

    for ch in s:
        if ch.isdigit():
            k = k * 10 + int(ch)
        elif ch == '[':
            count_stack.append(k)
            string_stack.append(current_string)
            current_string = ""
            k = 0
        elif ch == ']':
            current_string = string_stack.pop() + current_string * count_stack.pop()
        else:
            current_string += ch

    return current_string


# =============================================================================
# WAY 19: Nested stack with multiplier on the inner side
# =============================================================================
def decode_19(s):
    # Each entry stores the count FOR its content
    # Top of stack: [count, accumulated_string]
    stack = [[1, ""]]  # outer: count=1 (multiply by 1)
    num = 0

    for c in s:
        if c.isdigit():
            num = num * 10 + int(c)
        elif c == '[':
            # Push current num as the multiplier for inner content
            stack.append([num, ""])
            num = 0
        elif c == ']':
            count, inner = stack.pop()
            stack[-1][1] += inner * count
        else:
            stack[-1][1] += c

    return stack[0][1]


# =============================================================================
# WAY 20: Most elegant - Way 1 with helper variables
# =============================================================================
def decode_20(s):
    counts = []
    strings = []
    cur_str = ""
    cur_num = 0

    for ch in s:
        if ch.isdigit():
            cur_num = cur_num * 10 + int(ch)
        elif ch == '[':
            counts.append(cur_num)
            strings.append(cur_str)
            cur_num = 0
            cur_str = ""
        elif ch == ']':
            cnt = counts.pop()
            prev = strings.pop()
            cur_str = prev + cur_str * cnt
        else:
            cur_str += ch

    return cur_str


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to decode a string where k[encoded] means repeat encoded k times.
The pattern includes nested brackets like 3[a2[c]] = 'accaccacc'."

Key Insight:
"Use TWO STACKS - one for the repeat counts, one for the strings we've built.
When I see '[', I push my current state and reset.
When I see ']', I pop and repeat the current string k times, then append
to the previous context."

Algorithm:
"1. count_stack = [], string_stack = [], current_string = '', num = 0
2. For each char:
   - If digit: build the number (multi-digit support)
   - If '[': push num and current_string, reset both
   - If ']': pop count and prev, current_string = prev + current_string * count
   - If letter: append to current_string
3. Return current_string"

Why this works:
"When we see '[', we enter a new context. We save the current count and string
so we can come back to them. When we see ']', we're done with the current
context - we repeat our inner string and combine with the outer context.
Two stacks perfectly model the nested contexts!"

Edge cases:
- Single chars: "a" -> "a"
- Multi-digit counts: "10[a]" -> "aaaaaaaaaa"
- Nested brackets: "3[a2[c]]" -> "accaccacc"
- Multiple groups: "2[ab]3[c]" -> "ababcabc"

COMPLEXITY:
+-----------+--------+----------+
| Approach  | Time   | Space    |
+-----------+--------+----------+
| 2 stacks  | O(n*K) | O(n)     |
| Recursive | O(n*K) | O(n)     |
+-----------+--------+----------+

where K = max repetition count, n = length of input

KEY TRICK:
Two parallel stacks - one for numbers, one for strings - perfectly model
nested contexts. Each '[' opens a new context; each ']' closes one.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Two stacks (BEST)", decode_1),
        ("Way 2: Single tuple stack", decode_2),
        ("Way 3: Recursive with index", decode_3),
        ("Way 4: deque", decode_4),
        ("Way 5: Stack of tuples", decode_5),
        ("Way 6: Recursive with closure", decode_6),
        ("Way 7: With Decoder class", decode_7),
        ("Way 8: reduce", decode_8),
        ("Way 9: Compact tuple stack", decode_9),
        ("Way 10: Index pointer + recursion", decode_10),
        ("Way 11: Explicit brackets", decode_11),
        ("Way 12: Two-pass bracket matching", decode_12),
        ("Way 13: Most compact", decode_13),
        ("Way 14: Explicit state", decode_14),
        ("Way 15: One-liner reduce", decode_15),
        ("Way 16: deque + tracking", decode_16),
        ("Way 17: Recursive global idx", decode_17),
        ("Way 18: Most elegant", decode_18),
        ("Way 19: List as nested stack", decode_19),
        ("Way 20: Helper variables", decode_20),
    ]

    test_cases = [
        ("3[a]2[bc]", "aaabcbc"),
        ("3[a2[c]]", "accaccacc"),
        ("2[abc]3[cd]ef", "abcabccdcdcdef"),
        ("abc", "abc"),
        ("", ""),
        ("3[]", ""),  # edge case - empty inside brackets (problem says no)
        ("10[a]", "aaaaaaaaaa"),  # multi-digit count
        ("2[2[b]]", "bbbb"),  # nested multi-digit
        ("a", "a"),
        ("100[leetcode]", "leetcode" * 100),
    ]

    print("=" * 70)
    print("DECODE STRING - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/decode-string")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for s, expected in test_cases:
            # Skip the "3[]" case for implementations that may not handle it
            if s == "3[]":
                continue
            try:
                result = func(s)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: '{s}' -> '{result[:50]}{'...' if len(result) > 50 else ''}' (expected '{expected[:50]}')")
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
