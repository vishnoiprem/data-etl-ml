"""Generate Parentheses — all well-formed combos of n pairs.

Time:  Catalan(n) results, each built in O(n)
Space: O(n) — recursion stack
"""


def solve_generate_parens(n):
    """Return all combinations of well-formed parentheses.

    >>> sorted(solve_generate_parens(3))
    ['((()))', '(()())', '(())()', '()(())', '()()()']
    """
    out = []

    def backtrack(current, open_count, close_count):
        if len(current) == 2 * n:
            out.append("".join(current))
            return
        if open_count < n:
            current.append("(")
            backtrack(current, open_count + 1, close_count)
            current.pop()
        if close_count < open_count:
            current.append(")")
            backtrack(current, open_count, close_count + 1)
            current.pop()

    backtrack([], 0, 0)
    return out


if __name__ == "__main__":
    print(solve_generate_parens(3))
