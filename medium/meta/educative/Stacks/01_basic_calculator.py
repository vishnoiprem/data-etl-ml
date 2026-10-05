"""
Basic Calculator
Hard | 40 min

Evaluate an arithmetic expression with +, -, and ().

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/basic-calculator

Examples:
    "1+1" -> 2
    " 2-1 + 2 " -> 3
    "(1+(4+5+2)-3)+(6+8)" -> 23
    "-2+1" -> -1 (unary minus)
    "-(1+2)" -> -3

Constraints:
- 1 <= s.length <= 3 * 10^3
- Digits, +, -, (, )
- Valid expression
- '+' not unary; '-' can be unary
- Fits in 32-bit integer
"""

import operator
from collections import deque


# =============================================================================
# WAY 1: Stack for Sign (BEST - Memorize!)
# =============================================================================
# THINKING: "Track sign multiplier. Stack holds signs for nested parens."
def calculator_1(s):
    stack = [1]  # current sign multiplier
    sign = 1
    result = 0
    num = 0

    for char in s:
        if char.isdigit():
            num = num * 10 + int(char)
        elif char == '+':
            result += sign * num
            num = 0
            sign = stack[-1]
        elif char == '-':
            result += sign * num
            num = 0
            sign = -stack[-1]
        elif char == '(':
            stack.append(sign)
        elif char == ')':
            stack.pop()

    return result + sign * num


# =============================================================================
# WAY 2: Stack with state
# =============================================================================
def calculator_2(s):
    stack = []
    num = 0
    sign = 1
    result = 0

    for char in s:
        if char.isdigit():
            num = num * 10 + int(char)
        elif char in '+-':
            result += sign * num
            num = 0
            sign = 1 if char == '+' else -1
        elif char == '(':
            stack.append((result, sign))
            result = 0
            sign = 1
        elif char == ')':
            result += sign * num
            num = 0
            prev_result, prev_sign = stack.pop()
            result = prev_result + prev_sign * result
        elif char == ' ':
            continue

    return result + sign * num


# =============================================================================
# WAY 3: Single stack
# =============================================================================
def calculator_3(s):
    stack = []
    num = 0
    sign = 1
    result = 0

    for char in s:
        if char.isdigit():
            num = num * 10 + int(char)
        elif char == '+':
            result += sign * num
            num = 0
            sign = 1
        elif char == '-':
            result += sign * num
            num = 0
            sign = -1
        elif char == '(':
            stack.append(result)
            stack.append(sign)
            result = 0
            sign = 1
        elif char == ')':
            result += sign * num
            num = 0
            result *= stack.pop()  # sign
            result += stack.pop()  # previous result
        elif char == ' ':
            continue

    return result + sign * num


# =============================================================================
# WAY 4: Recursive approach
# =============================================================================
def calculator_4(s):
    def parse(s, i):
        num = 0
        sign = 1
        result = 0

        while i < len(s):
            if s[i].isdigit():
                num = num * 10 + int(s[i])
            elif s[i] == '+':
                result += sign * num
                num = 0
                sign = 1
            elif s[i] == '-':
                result += sign * num
                num = 0
                sign = -1
            elif s[i] == '(':
                sub_result, i = parse(s, i + 1)
                result += sign * sub_result
                num = 0
                sign = 1
            elif s[i] == ')':
                result += sign * num
                return result, i + 1
            i += 1

        return result + sign * num, i

    return parse(s, 0)[0]


# =============================================================================
# WAY 5: With index tracking
# =============================================================================
def calculator_5(s):
    stack = []
    num = 0
    sign = 1
    result = 0

    i = 0
    while i < len(s):
        char = s[i]
        if char.isdigit():
            num = num * 10 + int(char)
        elif char == '+':
            result += sign * num
            num = 0
            sign = 1
        elif char == '-':
            result += sign * num
            num = 0
            sign = -1
        elif char == '(':
            stack.append((result, sign))
            result = 0
            sign = 1
        elif char == ')':
            result += sign * num
            num = 0
            prev_result, prev_sign = stack.pop()
            result = prev_result + prev_sign * result
        i += 1

    return result + sign * num


# =============================================================================
# WAY 6: Using deque
# =============================================================================
def calculator_6(s):
    stack = deque()
    num = 0
    sign = 1
    result = 0

    for char in s:
        if char.isdigit():
            num = num * 10 + int(char)
        elif char == '+':
            result += sign * num
            num = 0
            sign = 1
        elif char == '-':
            result += sign * num
            num = 0
            sign = -1
        elif char == '(':
            stack.append((result, sign))
            result = 0
            sign = 1
        elif char == ')':
            result += sign * num
            num = 0
            prev_result, prev_sign = stack.pop()
            result = prev_result + prev_sign * result
        elif char == ' ':
            continue

    return result + sign * num


# =============================================================================
# WAY 7: Most compact stack
# =============================================================================
def calculator_7(s):
    stack = [1]
    num = 0
    sign = 1
    result = 0

    for char in s:
        if char.isdigit():
            num = num * 10 + int(char)
        elif char == '+':
            result += sign * num
            num = 0
            sign = stack[-1]
        elif char == '-':
            result += sign * num
            num = 0
            sign = -stack[-1]
        elif char == '(':
            stack.append(sign)
        elif char == ')':
            stack.pop()
        elif char == ' ':
            continue

    return result + sign * num


# =============================================================================
# WAY 8: Two-stack approach
# =============================================================================
def calculator_8(s):
    nums = []
    ops = []
    num = 0
    sign = 1
    result = 0

    for char in s:
        if char.isdigit():
            num = num * 10 + int(char)
        elif char == '+':
            result += sign * num
            num = 0
            sign = 1
        elif char == '-':
            result += sign * num
            num = 0
            sign = -1
        elif char == '(':
            nums.append(result)
            ops.append(sign)
            result = 0
            sign = 1
        elif char == ')':
            result += sign * num
            num = 0
            prev_sign = ops.pop()
            prev_result = nums.pop()
            result = prev_result + prev_sign * result

    return result + sign * num


# =============================================================================
# WAY 9: Using operator module
# =============================================================================
def calculator_9(s):
    ops_func = {1: operator.add, -1: operator.sub}
    stack = []
    num = 0
    sign = 1
    result = 0

    for char in s:
        if char.isdigit():
            num = num * 10 + int(char)
        elif char == '+':
            result = ops_func[sign](result, num)
            num = 0
            sign = 1
        elif char == '-':
            result = ops_func[sign](result, num)
            num = 0
            sign = -1
        elif char == '(':
            stack.append((result, sign))
            result = 0
            sign = 1
        elif char == ')':
            result = ops_func[sign](result, num)
            num = 0
            prev_result, prev_sign = stack.pop()
            result = prev_result + prev_sign * result

    return ops_func[sign](result, num)


# =============================================================================
# WAY 10: Most elegant sign stack
# =============================================================================
def calculator_10(s):
    stack = [1]
    sign = 1
    result = 0
    num = 0

    for char in s:
        if char.isdigit():
            num = num * 10 + int(char)
        elif char == '+':
            result += stack[-1] * num
            num = 0
            sign = stack[-1]
        elif char == '-':
            result += stack[-1] * num
            num = 0
            sign = -stack[-1]
        elif char == '(':
            stack.append(sign)
        elif char == ')':
            stack.pop()

    return result + sign * num


# =============================================================================
# WAY 11: With explicit operator handling
# =============================================================================
def calculator_11(s):
    stack = []
    num = 0
    sign = 1
    result = 0

    op_map = {'+': 1, '-': -1}

    for char in s:
        if char.isdigit():
            num = num * 10 + int(char)
        elif char in '+-':
            result += sign * num
            num = 0
            sign = op_map[char]
        elif char == '(':
            stack.append((result, sign))
            result = 0
            sign = 1
        elif char == ')':
            result += sign * num
            num = 0
            prev_result, prev_sign = stack.pop()
            result = prev_result + prev_sign * result
        elif char == ' ':
            continue

    return result + sign * num


# =============================================================================
# WAY 12: Functional style
# =============================================================================
def calculator_12(s):
    stack = [1]
    sign = 1
    result = 0
    num = 0

    for char in s:
        if char.isdigit():
            num = num * 10 + int(char)
        elif char in '+-':
            result += sign * num
            num = 0
            sign = stack[-1] if char == '+' else -stack[-1]
        elif char == '(':
            stack.append(sign)
        elif char == ')':
            stack.pop()
        elif char == ' ':
            continue

    return result + sign * num


# =============================================================================
# WAY 13: Most compact
# =============================================================================
def calculator_13(s):
    stack, num, sign, res = [], 0, 1, 0
    for c in s:
        if c.isdigit():
            num = num * 10 + int(c)
        elif c in '+-':
            res += sign * num
            num = 0
            sign = 1 if c == '+' else -1
        elif c == '(':
            stack.append((res, sign))
            res, sign = 0, 1
        elif c == ')':
            res += sign * num
            num = 0
            pr, ps = stack.pop()
            res = pr + ps * res
    return res + sign * num


# =============================================================================
# WAY 14: Class-based
# =============================================================================
class Calculator:
    def __init__(self):
        self.stack = []
        self.num = 0
        self.sign = 1
        self.result = 0

    def calculate(self, s):
        for char in s:
            if char.isdigit():
                self.num = self.num * 10 + int(char)
            elif char == '+':
                self.result += self.sign * self.num
                self.num = 0
                self.sign = 1
            elif char == '-':
                self.result += self.sign * self.num
                self.num = 0
                self.sign = -1
            elif char == '(':
                self.stack.append((self.result, self.sign))
                self.result = 0
                self.sign = 1
            elif char == ')':
                self.result += self.sign * self.num
                self.num = 0
                prev_result, prev_sign = self.stack.pop()
                self.result = prev_result + prev_sign * self.result
            elif char == ' ':
                continue

        return self.result + self.sign * self.num


def calculator_14(s):
    return Calculator().calculate(s)


# =============================================================================
# WAY 15: Clean stack approach
# =============================================================================
def calculator_15(s):
    stack = []
    num = 0
    sign = 1
    result = 0

    for char in s:
        if char.isdigit():
            num = num * 10 + int(char)
        elif char in '+-':
            result += sign * num
            num = 0
            sign = 1 if char == '+' else -1
        elif char == '(':
            stack.append((result, sign))
            result = 0
            sign = 1
        elif char == ')':
            result += sign * num
            num = 0
            prev_result, prev_sign = stack.pop()
            result = prev_result + prev_sign * result

    return result + sign * num


# =============================================================================
# WAY 16: With sign tuple
# =============================================================================
def calculator_16(s):
    stack = []
    num = 0
    sign = 1
    result = 0

    for char in s:
        if char.isdigit():
            num = num * 10 + int(char)
        elif char in '+-':
            result += sign * num
            num = 0
            sign = 1 if char == '+' else -1
        elif char == '(':
            stack.append((result, sign))
            result = 0
            sign = 1
        elif char == ')':
            result += sign * num
            num = 0
            r, s = stack.pop()
            result = r + s * result

    return result + sign * num


# =============================================================================
# WAY 17: Pre-process spaces
# =============================================================================
def calculator_17(s):
    s = s.replace(' ', '')
    stack = []
    num = 0
    sign = 1
    result = 0

    for char in s:
        if char.isdigit():
            num = num * 10 + int(char)
        elif char in '+-':
            result += sign * num
            num = 0
            sign = 1 if char == '+' else -1
        elif char == '(':
            stack.append((result, sign))
            result = 0
            sign = 1
        elif char == ')':
            result += sign * num
            num = 0
            prev_result, prev_sign = stack.pop()
            result = prev_result + prev_sign * result

    return result + sign * num


# =============================================================================
# WAY 18: Using reversed processing
# =============================================================================
def calculator_18(s):
    # Simpler: use state machine
    stack = []
    num = 0
    sign = 1
    result = 0

    for char in s:
        if char.isdigit():
            num = num * 10 + int(char)
        elif char in '+-':
            result += sign * num
            num = 0
            sign = 1 if char == '+' else -1
        elif char == '(':
            stack.append((result, sign))
            result = 0
            sign = 1
        elif char == ')':
            result += sign * num
            num = 0
            prev_r, prev_s = stack.pop()
            result = prev_r + prev_s * result
        elif char == ' ':
            continue

    return result + sign * num


# =============================================================================
# WAY 19: Dict-based state
# =============================================================================
def calculator_19(s):
    state = {'result': 0, 'sign': 1, 'num': 0, 'stack': []}

    for char in s:
        if char.isdigit():
            state['num'] = state['num'] * 10 + int(char)
        elif char == '+':
            state['result'] += state['sign'] * state['num']
            state['num'] = 0
            state['sign'] = 1
        elif char == '-':
            state['result'] += state['sign'] * state['num']
            state['num'] = 0
            state['sign'] = -1
        elif char == '(':
            state['stack'].append((state['result'], state['sign']))
            state['result'] = 0
            state['sign'] = 1
        elif char == ')':
            state['result'] += state['sign'] * state['num']
            state['num'] = 0
            prev_result, prev_sign = state['stack'].pop()
            state['result'] = prev_result + prev_sign * state['result']

    return state['result'] + state['sign'] * state['num']


# =============================================================================
# WAY 20: Final clean version
# =============================================================================
def calculator_20(s):
    stack = []
    num = 0
    sign = 1
    result = 0

    for char in s:
        if char.isdigit():
            num = num * 10 + int(char)
        elif char in '+-':
            result += sign * num
            num = 0
            sign = 1 if char == '+' else -1
        elif char == '(':
            stack.append((result, sign))
            result = 0
            sign = 1
        elif char == ')':
            result += sign * num
            num = 0
            prev_result, prev_sign = stack.pop()
            result = prev_result + prev_sign * result
        elif char == ' ':
            continue

    return result + sign * num


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to evaluate an arithmetic expression with +, -, and parentheses."

Key Insight:
"Use a stack to track state across parentheses:
- When I see '(', save the current accumulated result and sign
- When I see ')', restore and combine
- This handles nested expressions"

Algorithm:
"1. Track: num (current number), sign (current +1/-1), result (accumulated)
2. For each char:
   - Digit: build number (handle multi-digit)
   - '+': add num*sign to result, reset num, sign=+1
   - '-': add num*sign to result, reset num, sign=-1
   - '(': save (result, sign) on stack, reset
   - ')': combine with saved state
3. Don't forget the last number!"

Why this works:
"Each '(' creates a new evaluation context. The stack remembers what
came before. When ')' closes, we combine the inner result with the outer context."

Edge cases:
- Unary minus: handled by sign stack (like in "(1+(-2))" or "-1")
- Multi-digit numbers: build using num = num*10 + digit
- Spaces: just skip them

COMPLEXITY:
+-----------+--------+----------+
| Approach  | Time   | Space    |
+-----------+--------+----------+
| Stack     | O(n)   | O(n)     |
| Recursive | O(n)   | O(n)     |
+-----------+--------+----------+
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Sign stack", calculator_1),
        ("Way 2: State stack", calculator_2),
        ("Way 3: Single stack", calculator_3),
        ("Way 4: Recursive", calculator_4),
        ("Way 5: Index tracking", calculator_5),
        ("Way 6: deque", calculator_6),
        ("Way 7: Compact stack", calculator_7),
        ("Way 8: Two-stack", calculator_8),
        ("Way 9: operator", calculator_9),
        ("Way 10: Sign stack elegant", calculator_10),
        ("Way 11: Op map", calculator_11),
        ("Way 12: Functional", calculator_12),
        ("Way 13: Most compact", calculator_13),
        ("Way 14: Class", calculator_14),
        ("Way 15: Clean stack", calculator_15),
        ("Way 16: Sign tuple", calculator_16),
        ("Way 17: Pre-process", calculator_17),
        ("Way 18: Reversed", calculator_18),
        ("Way 19: Dict state", calculator_19),
        ("Way 20: Final clean", calculator_20),
    ]

    test_cases = [
        ("1+1", 2),
        (" 2-1 + 2 ", 3),
        ("(1+(4+5+2)-3)+(6+8)", 23),
        ("-2+1", -1),
        ("-(1+2)", -3),
        ("(5)", 5),
        ("1-(-2)", 3),
        ("-1+2", 1),
        ("10-20", -10),
        ("0", 0),
    ]

    print("=" * 70)
    print("BASIC CALCULATOR - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/basic-calculator")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for expr, expected in test_cases:
            try:
                result = func(expr)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  ✗ {name}: '{expr}' -> {result} (expected {expected})")
            except RecursionError:
                all_test_pass = False
                all_pass = False
                print(f"  ✗ {name}: RECURSION ERROR on '{expr}'")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  ✗ {name}: ERROR on '{expr}' - {e}")
        print(f"  {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS! 🎉")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
