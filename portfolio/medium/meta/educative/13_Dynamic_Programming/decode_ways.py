def num_of_decodings(decode_str):
    """
    Count the number of ways to decode a digit string.
    Mapping: '1'-'26' -> 'A'-'Z'. '0' and leading zeros are invalid.
    """
    if not decode_str or decode_str[0] == '0':
        return 0

    n = len(decode_str)
    # dp[i] = number of ways to decode s[:i]
    dp = [0] * (n + 1)
    dp[0] = 1
    dp[1] = 1

    for i in range(2, n + 1):
        # Single digit at position i-1
        if decode_str[i - 1] != '0':
            dp[i] += dp[i - 1]
        # Two-digit number ending at position i-1
        two = int(decode_str[i - 2:i])
        if 10 <= two <= 26:
            dp[i] += dp[i - 2]

    return dp[n]


if __name__ == "__main__":
    # Test cases
    print(num_of_decodings("231012"))     # 4
    print(num_of_decodings("12"))          # 2 (1,2 -> "AB"; 12 -> "L")
    print(num_of_decodings("226"))         # 3
    print(num_of_decodings("06"))          # 0 (leading zero)
    print(num_of_decodings("0"))           # 0
    print(num_of_decodings("1"))           # 1
    print(num_of_decodings("27"))          # 1 (only 2,7)
    print(num_of_decodings("100"))         # 0
    print(num_of_decodings("101"))         # 1 (10,1)
    print(num_of_decodings("110"))         # 1 (11,0 invalid; only 1,10)
