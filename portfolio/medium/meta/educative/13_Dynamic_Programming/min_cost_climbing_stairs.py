def minCostClimbingStairs(cost):
    """
    Return the minimum total cost to climb past the last stair.
    You can start at step 0 or step 1 (free), and at each step pay the
    cost of the stair you land on. You may then jump 1 or 2 steps.
    """
    n = len(cost)
    # dp[i] = min cost to reach step i (we pay cost[i] when stepping onto it)
    # We can start from step 0 or step 1 with no initial cost.
    dp = [0] * n
    dp[0] = cost[0]
    dp[1] = cost[1]

    for i in range(2, n):
        dp[i] = cost[i] + min(dp[i - 1], dp[i - 2])

    # We want the cost to reach "the top", i.e., one step past the last stair.
    # From step n-1 or n-2 we can jump to the top without paying anything
    # more (the top itself isn't a stair).
    return min(dp[n - 1], dp[n - 2])


if __name__ == "__main__":
    # Test cases
    print(minCostClimbingStairs([10, 15, 20]))             # 15
    print(minCostClimbingStairs([1, 100, 1, 1, 1, 100, 1, 1, 100, 1]))  # 6
    print(minCostClimbingStairs([0, 0, 0, 0]))             # 0
    print(minCostClimbingStairs([1, 2]))                   # 1
