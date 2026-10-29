"""Decode Ways — count ways to decode a digit string.

Time:  O(n)
Space: O(1) — rolling two values
"""


def solve_decode_ways(s):
    """Return the number of ways to decode ``s`` (1='A', 26='Z').

    >>> solve_decode_ways("226")
    3
    """
    if not s or s[0] == "0":
        return 0
    # dp[i] = number of ways to decode s[:i].
    prev2, prev1 = 1, 1
    for i in range(1, len(s)):
        curr = 0
        # Single digit: must be 1-9.
        if s[i] != "0":
            curr += prev1
        # Two digits: 10-26.
        two = int(s[i - 1:i + 1])
        if 10 <= two <= 26:
            curr += prev2
        prev2, prev1 = prev1, curr
    return prev1


if __name__ == "__main__":
    print(solve_decode_ways("226"))
