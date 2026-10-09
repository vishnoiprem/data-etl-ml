"""Expression Add Operators — insert +, -, * between digits to hit target.

Time:  O(4^n) — three operators (or none) per gap, pruned heavily
Space: O(n) — recursion stack
"""


def solve_expression_add_operators(num, target):
    """Return every expression that evaluates to ``target``.

    >>> sorted(solve_expression_add_operators("123", 6))
    ['1+2+3', '1*2*3']
    """
    out = []
    n = len(num)

    def backtrack(idx, path, value, prev_operand):
        if idx == n:
            if value == target:
                out.append(path)
            return
        for end in range(idx, n):
            segment = num[idx:end + 1]
            # Leading zero not allowed for multi-digit segments.
            if len(segment) > 1 and segment[0] == "0":
                break
            cur = int(segment)
            if idx == 0:
                backtrack(end + 1, segment, cur, cur)
            else:
                # Addition: reset the previous-multiplication carry.
                backtrack(end + 1, path + "+" + segment, value + cur, cur)
                backtrack(end + 1, path + "-" + segment, value - cur, -cur)
                # Multiplication: merge the previous operand into the running product.
                backtrack(
                    end + 1, path + "*" + segment,
                    value - prev_operand + prev_operand * cur,
                    prev_operand * cur,
                )

    backtrack(0, "", 0, 0)
    return out


if __name__ == "__main__":
    print(solve_expression_add_operators("123", 6))
