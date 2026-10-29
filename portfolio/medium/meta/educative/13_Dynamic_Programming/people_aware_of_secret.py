MOD = 10**9 + 7


def peopleAwareOfSecret(n, delay, forget):
    """
    On day 1, one person discovers a secret. Each person shares with one new
    person every day after `delay` days, and forgets after `forget` days.
    Return the number of people aware of the secret at the end of day n,
    modulo 10^9 + 7.

    dp[d] = number of NEW people who discover the secret on day d.
    The number of people who know the secret at end of day n equals the sum
    of dp[d] for days d in [n - forget + 1, n] (people who haven't yet
    forgotten by day n).
    """
    # dp[d] = number of people who first learn the secret on day d
    dp = [0] * (n + 2)
    dp[1] = 1

    for day in range(2, n + 1):
        # New learners on `day` come from people who learned the secret on
        # days in [day - forget + 1, day - delay], because:
        # - They must have started sharing by `day` (learned on day <= day - delay)
        # - They must still remember the secret on `day` (learned on day >= day - forget + 1)
        start = max(1, day - forget + 1)
        end = day - delay
        if end >= start:
            dp[day] = sum(dp[start:end + 1]) % MOD
        else:
            dp[day] = 0

    # People aware at end of day n: those who learned on a day in
    # [n - forget + 1, n] and have not yet forgotten by day n.
    start = max(1, n - forget + 1)
    return sum(dp[start:n + 1]) % MOD


if __name__ == "__main__":
    # Test cases
    print(peopleAwareOfSecret(6, 2, 4))   # 5
    print(peopleAwareOfSecret(4, 1, 3))   # 6
    print(peopleAwareOfSecret(5, 1, 2))   # 2
