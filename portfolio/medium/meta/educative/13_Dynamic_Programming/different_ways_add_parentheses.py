def diffWaysToCompute(expression):
    """
    Given a string expression of non-negative integers and operators +, -, *,
    return all possible results from computing the expression by inserting
    parentheses in every possible way.

    Uses recursion with memoization (top-down dynamic programming).
    """
    # Memoization cache to avoid recomputing subproblems
    memo = {}

    def compute(expr):
        # Return cached result if already computed
        if expr in memo:
            return memo[expr]

        results = []

        # Scan for operators; for each operator, split expression and
        # recursively compute left and right subexpression results
        for i, ch in enumerate(expr):
            if ch in "+-*":
                left_results = compute(expr[:i])
                right_results = compute(expr[i + 1:])

                # Combine left and right results using the current operator
                for left in left_results:
                    for right in right_results:
                        if ch == '+':
                            results.append(left + right)
                        elif ch == '-':
                            results.append(left - right)
                        elif ch == '*':
                            results.append(left * right)

        # Base case: if no operator found, expr is a single number
        if not results:
            results.append(int(expr))

        memo[expr] = results
        return results

    return compute(expression)


if __name__ == "__main__":
    # Test cases
    print(diffWaysToCompute("2-1-1"))       # [0, 2]
    print(diffWaysToCompute("2*3-4*5"))    # [-34, -10, -14, -10, 10]
