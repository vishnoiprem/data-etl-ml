def findCheapestPrice(n, flights, src, dst, k):
    """
    Find the minimum cost from src to dst using at most k stops
    (i.e., at most k+1 flights). Return -1 if no valid route.

    Approach: Bellman-Ford-style DP.
    dp[t][u] = min cost to reach u using at most t flights.
    For each t from 1..k+1, relax edges using the previous layer.
    """
    # dp[cost-so-far to each city] using at most `steps` flights
    INF = float("inf")
    dp = [INF] * n
    dp[src] = 0

    # Allow up to k stops => at most k+1 flights
    for _ in range(k + 1):
        # Snapshot previous layer so each step uses at most ONE new flight
        prev = dp[:]
        for u, v, w in flights:
            if prev[u] == INF:
                continue
            # Use only the snapshot values to avoid using a freshly-updated
            # city in the same iteration (would imply 2 flights in 1 step).
            if prev[u] + w < dp[v]:
                dp[v] = prev[u] + w

    return dp[dst] if dp[dst] != INF else -1


if __name__ == "__main__":
    # Test cases (LeetCode 787 style)
    flights1 = [
        [0, 1, 100],
        [1, 2, 100],
        [0, 2, 500],
    ]
    print(findCheapestPrice(3, flights1, 0, 2, 1))   # 200

    flights2 = [
        [0, 1, 100],
        [1, 2, 100],
        [0, 2, 500],
    ]
    print(findCheapestPrice(3, flights2, 0, 2, 0))   # 500

    flights3 = [
        [0, 1, 1],
        [1, 2, 1],
        [2, 3, 1],
        [3, 4, 1],
        [4, 5, 1],
        [0, 5, 20],
    ]
    print(findCheapestPrice(6, flights3, 0, 5, 2))   # 20

    flights4 = [[0, 1, 100]]
    print(findCheapestPrice(2, flights4, 0, 1, 0))    # 100

    print(findCheapestPrice(2, [], 0, 1, 0))          # -1
