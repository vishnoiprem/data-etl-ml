def find_max_knapsack_profit(capacity, weights, values):
    """
    Classic 0/1 Knapsack: each item either included (1) or not (0).
    dp[i][c] = max profit using first i items with capacity c.
    """
    n = len(values)
    # dp[i][c] = max profit using first i items with capacity c
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        w, v = weights[i - 1], values[i - 1]
        for c in range(capacity + 1):
            # Option 1: skip item i
            dp[i][c] = dp[i - 1][c]
            # Option 2: take item i (if it fits)
            if w <= c:
                take = v + dp[i - 1][c - w]
                if take > dp[i][c]:
                    dp[i][c] = take

    return dp[n][capacity]


if __name__ == "__main__":
    # Test cases
    print(find_max_knapsack_profit(5, [2, 3, 4, 5], [3, 4, 5, 6]))   # 7 (items 1+2: 3+4)
    print(find_max_knapsack_profit(7, [2, 3, 5], [3, 4, 5]))        # 8 (items 1+3: 3+5, weight 7)
    print(find_max_knapsack_profit(10, [1, 3, 5, 7], [2, 5, 9, 8])) # 16 (items 1+3+5: 2+5+9)
    print(find_max_knapsack_profit(3, [1, 2, 3], [10, 15, 20]))     # 25 (items 1+2: 10+15, weight 3)

    # Classic example (weights=values) with cap 50
    weights_classic = [10, 20, 30]
    values_classic  = [60, 100, 120]
    print(find_max_knapsack_profit(50, weights_classic, values_classic))  # 220
