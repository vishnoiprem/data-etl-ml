"""Evaluate Reverse Polish Notation.

Time:  O(n)
Space: O(n) — stack
"""


def solve_eval_rpn(tokens):
    """Evaluate an RPN expression and return the integer result.

    >>> solve_eval_rpn(["2","1","+","3","*"])
    9
    """
    ops = {
        "+": lambda a, b: a + b,
        "-": lambda a, b: a - b,
        "*": lambda a, b: a * b,
        "/": lambda a, b: int(a / b),  # truncate toward zero
    }
    stack = []
    for tok in tokens:
        if tok in ops:
            b = stack.pop()
            a = stack.pop()
            stack.append(ops[tok](a, b))
        else:
            stack.append(int(tok))
    return stack[0]


if __name__ == "__main__":
    print(solve_eval_rpn(["2", "1", "+", "3", "*"]))
