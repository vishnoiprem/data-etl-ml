"""Basic Calculator — handle +, -, (, ) with integer literals.

Time:  O(n)
Space:  O(n) — stack of signs
"""


def solve_basic_calculator(s):
    """Evaluate a single-digit/whole-number expression.

    >>> solve_basic_calculator("1 + 1")
    2
    """
    stack = [1]
    sign = 1
    result = 0
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == " ":
            i += 1
        elif ch == "+":
            sign = stack[-1]
            i += 1
        elif ch == "-":
            sign = -stack[-1]
            i += 1
        elif ch == "(":
            # Push the sign-of-this-context for any inner expression.
            stack.append(sign)
            i += 1
        elif ch == ")":
            stack.pop()
            i += 1
        elif ch.isdigit():
            num = 0
            while i < len(s) and s[i].isdigit():
                num = num * 10 + int(s[i])
                i += 1
            result += sign * num
        else:
            i += 1
    return result


if __name__ == "__main__":
    print(solve_basic_calculator("(1+(4+5+2)-3)+(6+8)"))
