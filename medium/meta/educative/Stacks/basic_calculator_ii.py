"""
Basic Calculator II
Medium | 30 min

Evaluate a mathematical expression string s containing:
- Non-negative integers
- Operators: '+', '-', '*', '/'
- Spaces (ignored)

Operations follow standard precedence: * and / before + and -.
Integer division truncates toward zero.

Return the result.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/basic-calculator-ii

Examples:
    "3+2*2"        -> 7
    " 3/2 "        -> 1
    " 3+5 / 2 "    -> 5
    "0-2147483647" -> -2147483647
    "1+1+1+1+1"    -> 5

Constraints:
- 1 <= s.length <= 3*10^5
- s has digits, operators, and spaces
- Expression is always valid
"""


# =============================================================================
# WAY 1: Stack with deferred addition (BEST - Memorize!)
# =============================================================================
# THINKING: "+/- pushes value (positive or negative). * /: pop, compute, push.
# Sum the stack at the end."
def calculate_1(s):
    stack = []
    num = 0
    sign = '+'

    for char in s:
        if char.isdigit():
            num = num * 10 + int(char)
        elif char in '+-*/' or char == ' ' and False:  # process on next operator
            # Process previous operator with current num
            if sign == '+':
                stack.append(num)
            elif sign == '-':
                stack.append(-num)
            elif sign == '*':
                stack.append(stack.pop() * num)
            elif sign == '/':
                # Truncate toward zero
                top = stack.pop()
                if top < 0:
                    stack.append(-((-top) // num))
                else:
                    stack.append(top // num)
            sign = char
            num = 0

    # Don't forget the last number!
    if sign == '+':
        stack.append(num)
    elif sign == '-':
        stack.append(-num)
    elif sign == '*':
        stack.append(stack.pop() * num)
    elif sign == '/':
        top = stack.pop()
        if top < 0:
            stack.append(-((-top) // num))
        else:
            stack.append(top // num)

    return sum(stack)


# Cleaner way 1: handle space via not entering any branch
def calculate_1_v2(s):
    stack = []
    num = 0
    sign = '+'

    for char in s:
        if char.isdigit():
            num = num * 10 + int(char)
        elif char in '+-*/':
            # Process previous operator with current num
            if sign == '+':
                stack.append(num)
            elif sign == '-':
                stack.append(-num)
            elif sign == '*':
                stack.append(stack.pop() * num)
            elif sign == '/':
                top = stack.pop()
                if top < 0:
                    stack.append(-((-top) // num))
                else:
                    stack.append(top // num)
            sign = char
            num = 0
        # Space: ignore

    # Process last number
    if sign == '+':
        stack.append(num)
    elif sign == '-':
        stack.append(-num)
    elif sign == '*':
        stack.append(stack.pop() * num)
    elif sign == '/':
        top = stack.pop()
        if top < 0:
            stack.append(-((-top) // num))
        else:
            stack.append(top // num)

    return sum(stack)


# Use this as the main Way 1
def calculate_1_main(s):
    return calculate_1_v2(s)


# =============================================================================
# WAY 2: Stack with current op state
# =============================================================================
def calculate_2(s):
    stack = []
    num = 0
    op = '+'
    s = s.replace(' ', '')

    for i, c in enumerate(s):
        if c.isdigit():
            num = num * 10 + int(c)
        if c in '+-*/' or i == len(s) - 1:  # last char (operator or digit)
            if op == '+':
                stack.append(num)
            elif op == '-':
                stack.append(-num)
            elif op == '*':
                stack.append(stack.pop() * num)
            elif op == '/':
                top = stack.pop()
                if top < 0:
                    stack.append(-((-top) // num))
                else:
                    stack.append(top // num)
            op = c
            num = 0

    return sum(stack)


# =============================================================================
# WAY 3: Pre-compute with helper to handle spaces
# =============================================================================
def calculate_3(s):
    # Replace consecutive spaces with single space for safety
    s = s.replace(' ', '')
    stack = []
    num = 0
    sign = '+'

    for i, c in enumerate(s):
        if c.isdigit():
            num = num * 10 + int(c)
        if (not c.isdigit() and c != ' ') or i == len(s) - 1:
            # Process
            if sign == '+':
                stack.append(num)
            elif sign == '-':
                stack.append(-num)
            elif sign == '*':
                stack.append(stack.pop() * num)
            elif sign == '/':
                top = stack.pop()
                if top < 0:
                    stack.append(-((-top) // num))
                else:
                    stack.append(top // num)
            sign = c
            num = 0

    return sum(stack)


# =============================================================================
# WAY 4: With two passes
# =============================================================================
def calculate_4(s):
    # First pass: extract numbers and operators (skipping spaces)
    tokens = []
    num = ''
    for c in s:
        if c.isdigit():
            num += c
        else:
            if num:
                tokens.append(int(num))
                num = ''
            if c in '+-*/':
                tokens.append(c)
    if num:
        tokens.append(int(num))

    # Process * and / first
    stack = []
    i = 0
    while i < len(tokens):
        if tokens[i] == '*':
            a = stack.pop()
            i += 1
            stack.append(a * tokens[i])
        elif tokens[i] == '/':
            a = stack.pop()
            i += 1
            top = a
            if top < 0:
                stack.append(-((-top) // tokens[i]))
            else:
                stack.append(top // tokens[i])
        else:
            stack.append(tokens[i])
        i += 1

    # Now stack is like: [3, +, 4, +, 5]
    # Evaluate left-to-right
    result = stack[0]
    i = 1
    while i < len(stack):
        op = stack[i]
        if op == '+':
            result += stack[i+1]
        elif op == '-':
            result -= stack[i+1]
        i += 2

    return result


# =============================================================================
# WAY 5: Without stack - process on the fly with precedence
# =============================================================================
def calculate_5(s):
    # Remove spaces
    s = s.replace(' ', '')
    # Use two variables: current number being built, last number (for * and /)
    last = 0
    num = 0
    result = 0
    op = '+'
    n = len(s)

    for i, c in enumerate(s):
        if c.isdigit():
            num = num * 10 + int(c)
        if c in '+-*/' or i == n - 1:
            if op == '+':
                result += last
                last = num
            elif op == '-':
                result += last
                last = -num
            elif op == '*':
                last = last * num
            elif op == '/':
                if last < 0:
                    last = -((-last) // num)
                else:
                    last = last // num
            op = c
            num = 0

    return result + last


# =============================================================================
# WAY 6: Use regex to split
# =============================================================================
import re

def calculate_6(s):
    # Tokenize using regex
    tokens = re.findall(r'\d+|[+\-*/]', s)
    # Use stack approach
    stack = []
    num = 0
    op = '+'

    for token in tokens:
        if token.isdigit():
            num = int(token)
            if op == '+':
                stack.append(num)
            elif op == '-':
                stack.append(-num)
            elif op == '*':
                stack.append(stack.pop() * num)
            elif op == '/':
                top = stack.pop()
                if top < 0:
                    stack.append(-((-top) // num))
                else:
                    stack.append(top // num)
        else:
            op = token

    return sum(stack)


# =============================================================================
# WAY 7: Recursive parsing (handle precedence)
# =============================================================================
def calculate_7(s):
    s = s.replace(' ', '')
    pos = [0]

    def parse_number():
        n = 0
        while pos[0] < len(s) and s[pos[0]].isdigit():
            n = n * 10 + int(s[pos[0]])
            pos[0] += 1
        return n

    def parse_term():
        # Parse multiplication/division chain
        result = parse_number()
        while pos[0] < len(s) and s[pos[0]] in '*/':
            op = s[pos[0]]
            pos[0] += 1
            right = parse_number()
            if op == '*':
                result *= right
            else:
                # Truncate toward zero
                if result < 0:
                    result = -((-result) // right)
                else:
                    result = result // right
        return result

    def parse_expr():
        # Parse addition/subtraction chain
        result = parse_term()
        while pos[0] < len(s) and s[pos[0]] in '+-':
            op = s[pos[0]]
            pos[0] += 1
            right = parse_term()
            if op == '+':
                result += right
            else:
                result -= right
        return result

    return parse_expr()


# =============================================================================
# WAY 8: Use while loop with explicit character index
# =============================================================================
def calculate_8(s):
    s = s.replace(' ', '')
    stack = []
    num = 0
    sign = '+'
    i = 0
    while i < len(s):
        if s[i].isdigit():
            num = num * 10 + int(s[i])
        if (not s[i].isdigit() and s[i] != ' ') or i == len(s) - 1:
            if sign == '+':
                stack.append(num)
            elif sign == '-':
                stack.append(-num)
            elif sign == '*':
                stack.append(stack.pop() * num)
            elif sign == '/':
                top = stack.pop()
                if top < 0:
                    stack.append(-((-top) // num))
                else:
                    stack.append(top // num)
            sign = s[i]
            num = 0
        i += 1
    return sum(stack)


# =============================================================================
# WAY 9: One-liner with helper
# =============================================================================
def calculate_9(s):
    def apply_op(stack, op, num):
        if op == '+':
            stack.append(num)
        elif op == '-':
            stack.append(-num)
        elif op == '*':
            stack.append(stack.pop() * num)
        elif op == '/':
            top = stack.pop()
            if top < 0:
                stack.append(-((-top) // num))
            else:
                stack.append(top // num)

    stack = []
    num = 0
    op = '+'
    for c in s:
        if c.isdigit():
            num = num * 10 + int(c)
        elif c in '+-*/':
            apply_op(stack, op, num)
            op = c
            num = 0
    apply_op(stack, op, num)
    return sum(stack)


# =============================================================================
# WAY 10: Using deque
# =============================================================================
from collections import deque

def calculate_10(s):
    stack = deque()
    num = 0
    sign = '+'
    for c in s:
        if c.isdigit():
            num = num * 10 + int(c)
        elif c in '+-*/':
            if sign == '+':
                stack.append(num)
            elif sign == '-':
                stack.append(-num)
            elif sign == '*':
                stack.append(stack.pop() * num)
            elif sign == '/':
                top = stack.pop()
                if top < 0:
                    stack.append(-((-top) // num))
                else:
                    stack.append(top // num)
            sign = c
            num = 0
    # Process last num
    if sign == '+':
        stack.append(num)
    elif sign == '-':
        stack.append(-num)
    elif sign == '*':
        stack.append(stack.pop() * num)
    elif sign == '/':
        top = stack.pop()
        if top < 0:
            stack.append(-((-top) // num))
        else:
            stack.append(top // num)
    return sum(stack)


# =============================================================================
# WAY 11: Most elegant no-stack (track last and result)
# =============================================================================
def calculate_11(s):
    s = s.replace(' ', '')
    last = 0
    cur = 0
    result = 0
    op = '+'

    for i, c in enumerate(s):
        if c.isdigit():
            cur = cur * 10 + int(c)
        if (not c.isdigit() and c != ' ') or i == len(s) - 1:
            if op == '+':
                result += last
                last = cur
            elif op == '-':
                result += last
                last = -cur
            elif op == '*':
                last = last * cur
            elif op == '/':
                if last < 0:
                    last = -((-last) // cur)
                else:
                    last = last // cur
            op = c
            cur = 0

    return result + last


# =============================================================================
# WAY 12: Class-based
# =============================================================================
class Calculator:
    def __init__(self, s):
        self.s = s
        self.stack = []
        self.num = 0
        self.sign = '+'

    def calculate(self):
        for c in self.s:
            if c.isdigit():
                self.num = self.num * 10 + int(c)
            elif c in '+-*/':
                self._apply()
                self.sign = c
                self.num = 0
        self._apply()
        return sum(self.stack)

    def _apply(self):
        if self.sign == '+':
            self.stack.append(self.num)
        elif self.sign == '-':
            self.stack.append(-self.num)
        elif self.sign == '*':
            self.stack.append(self.stack.pop() * self.num)
        elif self.sign == '/':
            top = self.stack.pop()
            if top < 0:
                self.stack.append(-((-top) // self.num))
            else:
                self.stack.append(top // self.num)


def calculate_12(s):
    return Calculator(s).calculate()


# =============================================================================
# WAY 13: Using math.trunc for division
# =============================================================================
import math

def calculate_13(s):
    s = s.replace(' ', '')
    stack = []
    num = 0
    sign = '+'

    for c in s:
        if c.isdigit():
            num = num * 10 + int(c)
        elif c in '+-*/':
            if sign == '+':
                stack.append(num)
            elif sign == '-':
                stack.append(-num)
            elif sign == '*':
                stack.append(stack.pop() * num)
            elif sign == '/':
                top = stack.pop()
                stack.append(math.trunc(top / num))
            sign = c
            num = 0
    # Last num
    if sign == '+':
        stack.append(num)
    elif sign == '-':
        stack.append(-num)
    elif sign == '*':
        stack.append(stack.pop() * num)
    elif sign == '/':
        top = stack.pop()
        stack.append(math.trunc(top / num))
    return sum(stack)


# =============================================================================
# WAY 14: Compact with one pass
# =============================================================================
def calculate_14(s):
    stack = []
    num = 0
    sign = '+'
    for i, c in enumerate(s):
        if c.isdigit():
            num = num * 10 + int(c)
        if c in '+-*/' or i == len(s) - 1:
            if sign == '+':
                stack.append(num)
            elif sign == '-':
                stack.append(-num)
            elif sign == '*':
                stack.append(stack.pop() * num)
            else:  # /
                a = stack.pop()
                stack.append(int(a / num) if a >= 0 else -int((-a) / num))
            sign = c
            num = 0
    return sum(stack)


# =============================================================================
# WAY 15: With helper for truncating division
# =============================================================================
def truncate_div(a, b):
    """Truncate toward zero."""
    if a < 0:
        return -((-a) // b)
    return a // b


def calculate_15(s):
    stack = []
    num = 0
    sign = '+'
    for i, c in enumerate(s):
        if c.isdigit():
            num = num * 10 + int(c)
        if c in '+-*/' or i == len(s) - 1:
            if sign == '+':
                stack.append(num)
            elif sign == '-':
                stack.append(-num)
            elif sign == '*':
                stack.append(stack.pop() * num)
            elif sign == '/':
                stack.append(truncate_div(stack.pop(), num))
            sign = c
            num = 0
    return sum(stack)


# =============================================================================
# WAY 16: With conditional processing
# =============================================================================
def calculate_16(s):
    stack = []
    num = 0
    op = '+'
    for c in s:
        if c.isdigit():
            num = num * 10 + int(c)
        elif c == ' ':
            continue
        else:  # operator
            if op == '+':
                stack.append(num)
            elif op == '-':
                stack.append(-num)
            elif op == '*':
                stack.append(stack.pop() * num)
            elif op == '/':
                # truncate
                a = stack.pop()
                stack.append(int(a / num))
            op = c
            num = 0
    # Process last num
    if op == '+':
        stack.append(num)
    elif op == '-':
        stack.append(-num)
    elif op == '*':
        stack.append(stack.pop() * num)
    elif op == '/':
        stack.append(int(stack.pop() / num))
    return sum(stack)


# =============================================================================
# WAY 17: With helper function for op
# =============================================================================
def calculate_17(s):
    # Op functions: a (left operand) and b (right operand)
    def add(a, b): return b
    def sub(a, b): return -b
    def mul(a, b): return a * b
    def div(a, b):
        if (a < 0) != (b < 0):
            return -(abs(a) // abs(b))
        return a // b if a >= 0 else -((-a) // b)

    op_funcs = {'+': add, '-': sub, '*': mul, '/': div}
    stack = []
    num = 0
    op = '+'
    s = s.replace(' ', '')
    n = len(s)

    for i, c in enumerate(s):
        if c.isdigit():
            num = num * 10 + int(c)
        if c in '+-*/' or i == n - 1:
            if op == '+' or op == '-':
                stack.append(op_funcs[op](0, num))
            else:
                stack.append(op_funcs[op](stack.pop(), num))
            op = c
            num = 0
    return sum(stack)


# =============================================================================
# WAY 18: Most compact
# =============================================================================
def calculate_18(s):
    stack = []
    num = 0
    op = '+'
    for c in s:
        if c.isdigit():
            num = num * 10 + int(c)
        if c in '+-*/':
            if op == '+': stack.append(num)
            elif op == '-': stack.append(-num)
            elif op == '*': stack.append(stack.pop() * num)
            else: stack.append(int(stack.pop() / num))
            op = c
            num = 0
    # Process last
    if op == '+': stack.append(num)
    elif op == '-': stack.append(-num)
    elif op == '*': stack.append(stack.pop() * num)
    else: stack.append(int(stack.pop() / num))
    return sum(stack)


# =============================================================================
# WAY 19: With explicit num tracking
# =============================================================================
def calculate_19(s):
    """Two-pass style: read number, if followed by * or /, read next and combine."""
    stack = []
    s = s.replace(' ', '')
    n = len(s)
    i = 0
    while i < n:
        # Skip spaces (already removed)
        # Read number
        num = 0
        while i < n and s[i].isdigit():
            num = num * 10 + int(s[i])
            i += 1
        # Check if followed by * or /
        if i < n and s[i] in '*/':
            op = s[i]
            i += 1
            # Read next number
            num2 = 0
            while i < n and s[i].isdigit():
                num2 = num2 * 10 + int(s[i])
                i += 1
            if op == '*':
                stack.append(num * num2)
            else:
                if (num < 0) != (num2 < 0):
                    stack.append(-(abs(num) // abs(num2)))
                else:
                    stack.append(num // num2)
            # After * /, continue combining if more * /
            while i < n and s[i] in '*/':
                op = s[i]
                i += 1
                num2 = 0
                while i < n and s[i].isdigit():
                    num2 = num2 * 10 + int(s[i])
                    i += 1
                top = stack.pop()
                if op == '*':
                    stack.append(top * num2)
                else:
                    if (top < 0) != (num2 < 0):
                        stack.append(-(abs(top) // abs(num2)))
                    else:
                        stack.append(top // num2)
        else:
            # Push as-is. The op before us (set externally) determines sign
            stack.append(num)
        # Skip operator (+/-) for next iteration
        if i < n and s[i] in '+-':
            if s[i] == '-':
                # Mark next number as negative
                i += 1
                num_next = 0
                while i < n and s[i].isdigit():
                    num_next = num_next * 10 + int(s[i])
                    i += 1
                # Check for */ chain after
                if i < n and s[i] in '*/':
                    op = s[i]
                    i += 1
                    num2 = 0
                    while i < n and s[i].isdigit():
                        num2 = num2 * 10 + int(s[i])
                        i += 1
                    val = -num_next
                    if op == '*':
                        stack.append(val * num2)
                    else:
                        if (val < 0) != (num2 < 0):
                            stack.append(-(abs(val) // abs(num2)))
                        else:
                            stack.append(val // num2)
                else:
                    stack.append(-num_next)
            else:
                i += 1
    return sum(stack)


# =============================================================================
# WAY 20: Final cleanest
# =============================================================================
def calculate_20(s):
    stack = []
    num = 0
    sign = '+'
    for c in s:
        if c.isdigit():
            num = num * 10 + int(c)
        elif c in '+-*/':
            if sign == '+': stack.append(num)
            elif sign == '-': stack.append(-num)
            elif sign == '*': stack.append(stack.pop() * num)
            elif sign == '/':
                top = stack.pop()
                stack.append(top // num if top >= 0 else -((-top) // num))
            sign = c
            num = 0
    if sign == '+': stack.append(num)
    elif sign == '-': stack.append(-num)
    elif sign == '*': stack.append(stack.pop() * num)
    elif sign == '/':
        top = stack.pop()
        stack.append(top // num if top >= 0 else -((-top) // num))
    return sum(stack)


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to evaluate a math expression with +,-,*,/. * and / have higher
precedence than + and -. Integer division truncates toward zero."

Key Insight:
"Use a STACK with DEFERRED addition!
- When we see +: push NUM (positive)
- When we see -: push -NUM (negative)
- When we see *: pop and push POP * NUM
- When we see /: pop and push POP // NUM (with truncation)
At the end, sum the stack!"

Algorithm:
"1. Initialize empty stack, num = 0, sign = '+'
2. For each char in s:
   - If digit: build num (num = num * 10 + int(c))
   - If operator or end of string:
     * If sign == '+': push num to stack
     * If sign == '-': push -num to stack
     * If sign == '*': pop, push (top * num)
     * If sign == '/': pop, push (top // num) (truncate toward zero)
     * sign = current char, num = 0
3. Return sum(stack)"

Why this works:
"* and / bind tighter than + and - so we resolve them immediately.
When we encounter a * or /, the LEFT operand is whatever is on the
stack. We pop, compute, push result back.
For + and -, we just push the signed value to defer the addition
until the end (since they have lower precedence, other ops come first)."

Edge cases:
- Single number: just push and sum
- All multiplications: stack stays at 1-2 items
- Division by negative: careful with truncation
- Spaces: ignore them (not part of tokenization)

COMPLEXITY:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Stack     | O(n)   | O(n)   |
| Regex+two | O(n)   | O(n)   |
| Recursive | O(n)   | O(d)   |
+-----------+--------+--------+

KEY TRICK:
Push with SIGN (+ or -) for low-priority ops. COMPUTE IMMEDIATELY
for high-priority ops (* or /). This naturally handles precedence
without a parser.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Stack (BEST)", calculate_1_main),
        ("Way 2: Stack + op state", calculate_2),
        ("Way 3: Skip space", calculate_3),
        ("Way 4: Two passes", calculate_4),
        ("Way 5: No stack (track last)", calculate_5),
        ("Way 6: Regex split", calculate_6),
        ("Way 7: Recursive parser", calculate_7),
        ("Way 8: While loop", calculate_8),
        ("Way 9: With helper", calculate_9),
        ("Way 10: deque", calculate_10),
        ("Way 11: Most elegant no-stack", calculate_11),
        ("Way 12: Class-based", calculate_12),
        ("Way 13: math.trunc", calculate_13),
        ("Way 14: Compact one pass", calculate_14),
        ("Way 15: With helper trunc div", calculate_15),
        ("Way 16: Conditional processing", calculate_16),
        ("Way 17: Op map", calculate_17),
        ("Way 18: Most compact", calculate_18),
        ("Way 19: Explicit num tracking", calculate_19),
        ("Way 20: Final cleanest", calculate_20),
    ]

    test_cases = [
        ("3+2*2", 7),
        (" 3/2 ", 1),
        (" 3+5 / 2 ", 5),
        ("0-2147483647", -2147483647),
        ("1+1+1+1+1", 5),
        ("14/3*2", 8),  # 14/3=4 (truncated), 4*2=8
        ("14-3/2", 13),  # 3/2 = 1 (truncated toward zero: 1.5 -> 1), 14-1=13
        ("0+0", 0),
        ("1-1-1-1-1", -3),  # 1-1-1-1-1 = -3
        ("1*2*3*4*5", 120),
        ("100/3/2", 16),  # 100/3 = 33 (truncated), 33/2 = 16 (truncated)
        ("1+2*3-4", 3),  # 2*3=6, 1+6-4=3
        ("2*3+4/2", 8),  # 2*3=6, 4/2=2, 6+2=8
        ("100000000/1/2", 50000000),  # 100000000//1=100000000, //2=50000000
    ]

    print("=" * 70)
    print("BASIC CALCULATOR II - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/basic-calculator-ii")
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
