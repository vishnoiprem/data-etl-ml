"""
Parsing A Boolean Expression
Hard | 40 min

A boolean expression is either:
- 't' (true)
- 'f' (false)
- '!(expr)'  (NOT)
- '&(expr1,expr2,...)'  (AND)
- '|(expr1,expr2,...)'  (OR)

Return the result of evaluating the expression.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/parsing-a-boolean-expression

Examples:
    "!(f)"           -> True
    "|(f,t)"         -> True
    "&(t,f)"         -> False
    "|(&(t,f,t),!(t))" -> False
    "!(&(t,t))"      -> False
    "&(|(t,!(t)),t)" -> True

Constraints:
- 1 <= expression.length <= 20000
- expression consists of characters: '(', ')', ',', 't', 'f', '!', '&', '|'
- Expression is always valid
"""


# =============================================================================
# WAY 1: Stack-based parsing (BEST - Memorize!)
# =============================================================================
# THINKING: "Process char by char. When we see ')', pop operands until '('
#           and apply the operator. Otherwise push to stack."
def parse_bool_expr_1(expression):
    stack = []
    for char in expression:
        if char == ')':
            # Pop operands until we find '('
            operands = []
            while stack and stack[-1] != '(':
                operands.append(stack.pop())
            stack.pop()  # Remove '('
            # Get the operator (it's now on top)
            op = stack.pop()
            # Apply operator
            if op == '!':
                result = not operands[0]
            elif op == '&':
                result = all(operands)
            elif op == '|':
                result = any(operands)
            stack.append('t' if result else 'f')
        elif char != ',':
            stack.append(char)
    return stack[-1] == 't'


# =============================================================================
# WAY 2: With explicit operator functions
# =============================================================================
def parse_bool_expr_2(expression):
    stack = []
    for char in expression:
        if char == ')':
            operands = []
            while stack and stack[-1] != '(':
                operands.append(stack.pop() == 't')
            stack.pop()  # Remove '('
            op = stack.pop()
            if op == '!':
                result = not operands[0]
            elif op == '&':
                result = all(operands)
            else:  # '|'
                result = any(operands)
            stack.append(result)
        elif char not in (',', '('):
            stack.append(char)
    return stack[-1] == 't'


# =============================================================================
# WAY 3: Track operands as we go (push results immediately)
# =============================================================================
def parse_bool_expr_3(expression):
    stack = []
    i = 0
    while i < len(expression):
        char = expression[i]
        if char == ',':
            i += 1
            continue
        if char in ('t', 'f'):
            stack.append(char)
        elif char in '!&|':
            stack.append(char)
        elif char == '(':
            stack.append(char)
        elif char == ')':
            # Evaluate
            operands = []
            while stack and stack[-1] != '(':
                operands.append(stack.pop() == 't')
            stack.pop()  # Remove '('
            op = stack.pop()
            if op == '!':
                result = not operands[0]
            elif op == '&':
                result = all(operands)
            else:
                result = any(operands)
            stack.append('t' if result else 'f')
        i += 1
    return stack[-1] == 't'


# =============================================================================
# WAY 4: With deque
# =============================================================================
from collections import deque

def parse_bool_expr_4(expression):
    stack = deque()
    for char in expression:
        if char == ')':
            operands = []
            while stack and stack[-1] != '(':
                operands.append(stack.pop())
            stack.pop()  # '('
            op = stack.pop()
            if op == '!':
                result = not (operands[0] == 't')
            elif op == '&':
                result = all(o == 't' for o in operands)
            elif op == '|':
                result = any(o == 't' for o in operands)
            stack.append('t' if result else 'f')
        elif char != ',':
            stack.append(char)
    return stack[-1] == 't'


# =============================================================================
# WAY 5: Recursive descent parser
# =============================================================================
def parse_bool_expr_5(expression):
    pos = [0]

    def parse_expr():
        # parseBoolExpr at current pos, return bool
        char = expression[pos[0]]
        pos[0] += 1
        if char == 't':
            return True
        if char == 'f':
            return False
        # Must be operator
        op = char
        pos[0] += 1  # skip '('
        operands = []
        # Parse comma-separated expressions until ')'
        while expression[pos[0]] != ')':
            operands.append(parse_expr())
            if expression[pos[0]] == ',':
                pos[0] += 1
        pos[0] += 1  # skip ')'
        if op == '!':
            return not operands[0]
        elif op == '&':
            return all(operands)
        else:
            return any(operands)

    return parse_expr()


# =============================================================================
# WAY 6: Recursive with helper
# =============================================================================
def parse_bool_expr_6(expression):
    def helper(expr, i):
        if expr[i] == 't':
            return True, i + 1
        if expr[i] == 'f':
            return False, i + 1
        # Operator
        op = expr[i]
        i += 1  # skip '('
        operands = []
        while expr[i] != ')':
            val, i = helper(expr, i)
            operands.append(val)
            if expr[i] == ',':
                i += 1
        i += 1  # skip ')'
        if op == '!':
            return not operands[0], i
        elif op == '&':
            return all(operands), i
        else:
            return any(operands), i

    result, _ = helper(expression, 0)
    return result


# =============================================================================
# WAY 7: Stack with operator lookup
# =============================================================================
def parse_bool_expr_7(expression):
    stack = []
    operator_map = {
        '&': all,
        '|': any,
        '!': lambda x: not x[0]
    }
    for char in expression:
        if char == ')':
            operands = []
            while stack and stack[-1] != '(':
                val = stack.pop()
                operands.append(val == 't')
            stack.pop()  # '('
            op = stack.pop()
            result = operator_map[op](operands)
            stack.append('t' if result else 'f')
        elif char != ',':
            stack.append(char)
    return stack[-1] == 't'


# =============================================================================
# WAY 8: With string replacement (clean first)
# =============================================================================
def parse_bool_expr_8(expression):
    # Repeatedly simplify
    while len(expression) > 1:
        # Find innermost (op,...,)
        # Replace innermost first
        for i in range(len(expression) - 1, -1, -1):
            if expression[i] == ')':
                # Find matching '('
                depth = 1
                j = i - 1
                while depth > 0:
                    j -= 1
                    if expression[j] == ')':
                        depth += 1
                    elif expression[j] == '(':
                        depth -= 1
                # j is index of '('
                # expression[j-1] should be operator
                op = expression[j - 1]
                inner = expression[j + 1:i]
                # Parse inner comma-separated values
                operands = [v == 't' for v in inner.split(',')]
                if op == '!':
                    val = not operands[0]
                elif op == '&':
                    val = all(operands)
                else:
                    val = any(operands)
                expression = expression[:j - 1] + ('t' if val else 'f') + expression[i + 1:]
                break
        else:
            break  # No ')' found
    return expression == 't'


# =============================================================================
# WAY 9: Replace innermost with regex
# =============================================================================
import re

def parse_bool_expr_9(expression):
    # Replace !x, x|y, x&y iteratively
    pattern = re.compile(r'([!&|])\(([^()]+)\)')
    while True:
        new = pattern.sub(lambda m: _eval_simple(m.group(1), m.group(2)), expression)
        if new == expression:
            break
        expression = new
    return expression == 't'


def _eval_simple(op, inner):
    operands = [v == 't' for v in inner.split(',')]
    if op == '!':
        result = not operands[0]
    elif op == '&':
        result = all(operands)
    else:
        result = any(operands)
    return 't' if result else 'f'


# =============================================================================
# WAY 10: Using dictionary for operators
# =============================================================================
def parse_bool_expr_10(expression):
    ops = {'!': lambda x: not x, '&': all, '|': any}
    stack = []
    for char in expression:
        if char == ')':
            args = []
            while stack[-1] != '(':
                args.append(stack.pop() == 't')
            stack.pop()
            op = stack.pop()
            stack.append('t' if ops[op](args) else 'f')
        elif char not in ',( ':
            stack.append(char)
    return stack[-1] == 't'


# =============================================================================
# WAY 11: Direct boolean evaluation on stack
# =============================================================================
def parse_bool_expr_11(expression):
    stack = []
    for char in expression:
        if char in 'tf':
            stack.append(char == 't')
        elif char in '!&|':
            stack.append(char)
        elif char == '(':
            stack.append(char)
        elif char == ')':
            args = []
            while stack[-1] != '(':
                args.append(stack.pop())
            stack.pop()
            op = stack.pop()
            if op == '!':
                result = not args[0]
            elif op == '&':
                result = all(args)
            elif op == '|':
                result = any(args)
            stack.append(result)
    return stack[-1]


# =============================================================================
# WAY 12: Two-pass evaluation
# =============================================================================
def parse_bool_expr_12(expression):
    # First pass: collect tokens
    # Second pass: evaluate
    stack = []
    i = 0
    while i < len(expression):
        char = expression[i]
        if char == ' ' or char == ',':
            i += 1
            continue
        if char == ')':
            operands = []
            while stack and stack[-1] != '(':
                operands.append(stack.pop())
            stack.pop()  # '('
            op = stack.pop()
            if op == '!':
                result = not operands[0]
            elif op == '&':
                result = all(operands)
            else:
                result = any(operands)
            stack.append('t' if result else 'f')
            i += 1
            continue
        stack.append(char)
        i += 1
    return stack[-1] == 't'


# =============================================================================
# WAY 13: Most concise
# =============================================================================
def parse_bool_expr_13(expression):
    s = []
    for c in expression:
        if c == ')':
            args = []
            while s[-1] != '(':
                args.append(s.pop() == 't')
            s.pop()
            op = s.pop()
            if op == '!':
                v = not args[0]
            elif op == '&':
                v = all(args)
            else:
                v = any(args)
            s.append('t' if v else 'f')
        elif c != ',':
            s.append(c)
    return s[-1] == 't'


# =============================================================================
# WAY 14: Class-based
# =============================================================================
class BoolExprParser:
    def __init__(self, expression):
        self.expr = expression
        self.stack = []
        self.pos = 0

    def eval(self):
        for char in self.expr:
            if char == ')':
                operands = []
                while self.stack and self.stack[-1] != '(':
                    operands.append(self.stack.pop())
                self.stack.pop()
                op = self.stack.pop()
                if op == '!':
                    result = not operands[0]
                elif op == '&':
                    result = all(operands)
                else:
                    result = any(operands)
                self.stack.append('t' if result else 'f')
            elif char != ',':
                self.stack.append(char)
        return self.stack[-1] == 't'


def parse_bool_expr_14(expression):
    return BoolExprParser(expression).eval()


# =============================================================================
# WAY 15: With explicit operator dispatch
# =============================================================================
def parse_bool_expr_15(expression):
    stack = []
    for char in expression:
        if char == ')':
            operands = []
            while stack and stack[-1] != '(':
                val = stack.pop()
                operands.append(val == 't')
            stack.pop()  # '('
            op = stack.pop()
            if op == '!':
                val = not operands[0]
            elif op == '&':
                val = True
                for o in operands:
                    val = val and o
            else:  # '|'
                val = False
                for o in operands:
                    val = val or o
            stack.append('t' if val else 'f')
        elif char not in (',', ' '):
            stack.append(char)
    return stack[-1] == 't'


# =============================================================================
# WAY 16: Compact stack (use index 0 = true)
# =============================================================================
def parse_bool_expr_16(expression):
    stack = []
    for char in expression:
        if char == ')':
            values = []
            while stack and stack[-1] != '(':
                values.append(stack.pop())
            stack.pop()
            op = stack.pop()
            if op == '!':
                r = not values[0]
            elif op == '&':
                r = all(values)
            else:
                r = any(values)
            stack.append('t' if r else 'f')
        elif char not in (',', ' ', '('):
            stack.append(char)
    return stack.pop() == 't'


# =============================================================================
# WAY 17: Recursive with operator functions
# =============================================================================
def parse_bool_expr_17(expression):
    def parse(i):
        if expression[i] == 't':
            return True, i + 1
        if expression[i] == 'f':
            return False, i + 1
        # Operator
        op = expression[i]
        i += 2  # skip operator and '('
        args = []
        while expression[i] != ')':
            val, i = parse(i)
            args.append(val)
            if expression[i] == ',':
                i += 1
        i += 1  # skip ')'
        if op == '!':
            return not args[0], i
        elif op == '&':
            return all(args), i
        else:
            return any(args), i

    result, _ = parse(0)
    return result


# =============================================================================
# WAY 18: With short-circuit evaluation
# =============================================================================
def parse_bool_expr_18(expression):
    stack = []
    for char in expression:
        if char in ('t', 'f'):
            stack.append(char)
        elif char in ('!', '&', '|'):
            stack.append(char)
        elif char == '(':
            stack.append(char)
        elif char == ')':
            # Evaluate
            args = []
            while stack and stack[-1] != '(':
                v = stack.pop()
                args.append(v == 't')
            stack.pop()  # '('
            op = stack.pop()
            if op == '!':
                # Special: ! has exactly 1 arg
                result = not args[0]
            elif op == '&':
                # Short-circuit: if any False, return False
                result = all(args)
            else:  # '|'
                # Short-circuit: if any True, return True
                result = any(args)
            stack.append('t' if result else 'f')
    return stack[-1] == 't'


# =============================================================================
# WAY 19: Iterate with pop helper
# =============================================================================
def parse_bool_expr_19(expression):
    stack = []

    def pop_until_paren():
        vals = []
        while stack and stack[-1] != '(':
            vals.append(stack.pop() == 't')
        if stack:
            stack.pop()  # remove '('
        op = stack.pop() if stack else None
        return vals, op

    for char in expression:
        if char == ')':
            vals, op = pop_until_paren()
            if op == '!':
                r = not vals[0]
            elif op == '&':
                r = all(vals)
            else:
                r = any(vals)
            stack.append('t' if r else 'f')
        elif char != ',':
            stack.append(char)
    return stack[-1] == 't'


# =============================================================================
# WAY 20: Final cleanest (Way 1 minimal)
# =============================================================================
def parse_bool_expr_20(expression):
    s = []
    for c in expression:
        if c == ')':
            a = []
            while s[-1] != '(':
                a.append(s.pop())
            s.pop()
            o = s.pop()
            if o == '!':
                r = not (a[0] == 't')
            elif o == '&':
                r = all(x == 't' for x in a)
            else:
                r = any(x == 't' for x in a)
            s.append('t' if r else 'f')
        elif c != ',':
            s.append(c)
    return s[-1] == 't'


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to parse and evaluate a boolean expression that uses '!', '&', '|'
operators with multiple operands. The expression has fully parenthesized
sub-expressions."

Key Insight:
"This is a SHUNTING problem. Use a STACK:
- When we encounter ')', the top of stack has operands and operator
  (since we pushed '(' before each subgroup).
- Pop operands until '(', then pop operator, evaluate, push result back.
- Continue until done; final stack top is the answer."

Algorithm:
"1. Initialize empty stack
2. For each char in expression:
   - If char == ')', evaluate:
     * Pop operands (t/f) until we hit '('
     * Pop '('
     * Pop the operator (!, &, |)
     * Evaluate: ! = not operand, & = and all, | = or all
     * Push result ('t' or 'f')
   - Else if char != ',': push to stack
3. Return top of stack == 't'"

Why this works:
"Each ')' closes a complete subexpression with its operands and operator
in the stack just below '('. We pop them all, evaluate using the operator,
and push the result. The stack grows/shrinks as we evaluate nested groups."

Edge cases:
- Single value: 't' or 'f' returns it
- NOT: exactly 1 operand
- AND/OR: 1 or more operands
- Deep nesting: stack handles naturally

COMPLEXITY:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Stack     | O(n)   | O(n)   |
| Recursive | O(n)   | O(d)   |
| Regex     | O(n^2) | O(n)   |
+-----------+--------+--------+

KEY TRICK:
When ')' is seen, the stack top has operands and operator ready to evaluate.
The '(' we pushed earlier marks the boundary.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Stack (BEST)", parse_bool_expr_1),
        ("Way 2: Explicit functions", parse_bool_expr_2),
        ("Way 3: Push results immediately", parse_bool_expr_3),
        ("Way 4: deque", parse_bool_expr_4),
        ("Way 5: Recursive", parse_bool_expr_5),
        ("Way 6: Recursive helper", parse_bool_expr_6),
        ("Way 7: Operator map", parse_bool_expr_7),
        ("Way 8: String replacement", parse_bool_expr_8),
        ("Way 9: Regex", parse_bool_expr_9),
        ("Way 10: dict operators", parse_bool_expr_10),
        ("Way 11: Direct bool on stack", parse_bool_expr_11),
        ("Way 12: Two-pass", parse_bool_expr_12),
        ("Way 13: Most concise", parse_bool_expr_13),
        ("Way 14: Class-based", parse_bool_expr_14),
        ("Way 15: Explicit dispatch", parse_bool_expr_15),
        ("Way 16: Compact stack", parse_bool_expr_16),
        ("Way 17: Recursive op functions", parse_bool_expr_17),
        ("Way 18: Short-circuit", parse_bool_expr_18),
        ("Way 19: Pop helper", parse_bool_expr_19),
        ("Way 20: Final cleanest", parse_bool_expr_20),
    ]

    test_cases = [
        ("!(f)", True),
        ("|(f,t)", True),
        ("&(t,f)", False),
        ("|(&(t,f,t),!(t))", False),
        ("!(&(t,t))", False),
        ("&(|(t,!(t)),t)", True),
        ("t", True),
        ("f", False),
        ("!(t)", False),
        ("!(t,f)|...", None),  # Skip - invalid expression
        ("&(t,t,t)", True),
        ("|(f,f,f)", False),
        ("&(t,f,t)", False),
        ("!(|(t,f))", False),
        ("|(&(t,t),!(t,f))", True),  # &(t,t)=t, !(t,f)... wait !(t,f) is invalid
    ]

    # Let me fix the test cases - skipping invalid ones
    test_cases = [
        ("!(f)", True),
        ("|(f,t)", True),
        ("&(t,f)", False),
        ("|(&(t,f,t),!(t))", False),
        ("!(&(t,t))", False),
        ("&(|(t,!(t)),t)", True),
        ("t", True),
        ("f", False),
        ("!(t)", False),
        ("!(f)", True),
        ("&(t,t,t)", True),
        ("|(f,f,f)", False),
        ("&(t,f,t)", False),
        ("!(|(t,f))", False),
        ("!(&(t,t,f))", False),  # &(t,t,f)=f, !f=t
        ("|(&(t,f),|)", None),  # Skip - invalid
        ("!(|(t,f))", False),
        ("&(!(t),f)", False),  # !(t)=f, f&f=f
    ]

    print("=" * 70)
    print("PARSING A BOOLEAN EXPRESSION - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/parsing-a-boolean-expression")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for expr, expected in test_cases:
            if expected is None:
                continue
            try:
                result = func(expr)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: '{expr}' -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on '{expr}' - {e}")
        print(f"  {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
