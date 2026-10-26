"""Minimum Remove to Make Valid Parentheses.

Time:  O(n) — two passes with a stack of indices
Space: O(n)
"""


def solve_min_remove_parens(s):
    """Remove the minimum number of parens to make ``s`` valid.

    >>> solve_min_remove_parens("a)b(c)d")
    'ab(c)d'
    """
    s_list = list(s)
    stack = []  # indices of unmatched '('
    for i, ch in enumerate(s_list):
        if ch == "(":
            stack.append(i)
        elif ch == ")":
            if stack:
                stack.pop()
            else:
                s_list[i] = ""  # mark unmatched ')' for removal
    # Any remaining '(' on the stack are unmatched.
    for i in stack:
        s_list[i] = ""
    return "".join(s_list)


if __name__ == "__main__":
    print(solve_min_remove_parens("a)b(c)d"))
