def counting_bits(n):
    """
    Return an array ans of length n+1 where ans[x] = number of 1 bits in x,
    for 0 <= x <= n.
    """
    # dp[i] = number of 1 bits in i
    dp = [0] * (n + 1)
    for i in range(1, n + 1):
        # Clever recurrence: i = (i >> 1) with possibly one extra bit set.
        # i & 1 is the new LSB; dp[i >> 1] is the count for i shifted right.
        dp[i] = dp[i >> 1] + (i & 1)
    return dp


if __name__ == "__main__":
    # Test cases
    print(counting_bits(2))     # [0, 1, 1]
    print(counting_bits(5))     # [0, 1, 1, 2, 1, 2]
    print(counting_bits(0))     # [0]
    print(counting_bits(15))    # [0,1,1,2,1,2,2,3,1,2,2,3,2,3,3,4]
