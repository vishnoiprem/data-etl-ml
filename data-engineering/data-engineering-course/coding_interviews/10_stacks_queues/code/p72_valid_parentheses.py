"""Valid Parentheses — check all brackets in s are balanced.

Time:  O(n)
Space: O(n) — stack
"""


def solve_valid_parentheses(s):
    """Return True if every opener has a matching closer in the right order.

    >>> solve_valid_parentheses("()[]{}")
    True
    """
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for ch in s:
        if ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
        else:
            stack.append(ch)
    return not stack


if __name__ == "__main__":
    print(solve_valid_parentheses("()[]{}"))
