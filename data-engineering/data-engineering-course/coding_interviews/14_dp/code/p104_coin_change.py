"""Coin Change — minimum number of coins to make up amount.

Time:  O(amount · len(coins))
Space: O(amount)
"""


def solve_coin_change(coins, amount):
    """Return the minimum number of coins; -1 if impossible.

    >>> solve_coin_change([1, 5, 11, 25], 30)
    2
    """
    INF = amount + 1
    dp = [INF] * (amount + 1)
    dp[0] = 0
    for value in range(1, amount + 1):
        for coin in coins:
            if coin <= value and dp[value - coin] + 1 < dp[value]:
                dp[value] = dp[value - coin] + 1
    return dp[amount] if dp[amount] != INF else -1


if __name__ == "__main__":
    print(solve_coin_change([1, 5, 11, 25], 30))
