def minDistance(word1, word2):
    """
    Return the minimum number of insertions, deletions, or replacements
    needed to transform word1 into word2.

    Classic Levenshtein distance via 2D DP.
    dp[i][j] = min operations to transform word1[:i] -> word2[:j]
    """
    m, n = len(word1), len(word2)

    # dp[i][j] = min operations to convert word1[:i] to word2[:j]
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Base cases: empty source / target
    for i in range(m + 1):
        dp[i][0] = i          # delete i chars
    for j in range(n + 1):
        dp[0][j] = j          # insert j chars

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if word1[i - 1] == word2[j - 1]:
                # No operation needed for this matching character
                dp[i][j] = dp[i - 1][j - 1]
            else:
                # Try: replace (dp[i-1][j-1]), delete (dp[i-1][j]),
                #      insert (dp[i][j-1])
                dp[i][j] = 1 + min(
                    dp[i - 1][j - 1],   # replace
                    dp[i - 1][j],       # delete from word1
                    dp[i][j - 1],       # insert into word1
                )

    return dp[m][n]


if __name__ == "__main__":
    # Test cases
    print(minDistance("horse", "ros"))       # 3
    print(minDistance("intention", "execution"))  # 5
    print(minDistance("", ""))                # 0
    print(minDistance("abc", ""))             # 3
    print(minDistance("", "abc"))             # 3
    print(minDistance("abc", "abc"))          # 0
