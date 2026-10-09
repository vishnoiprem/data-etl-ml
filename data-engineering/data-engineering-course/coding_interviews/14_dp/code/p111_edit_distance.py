"""Edit Distance (Levenshtein) — DP variant for the M14 lesson.

Time:  O(m · n)
Space: O(min(m, n)) — rolling row

This is the same algorithm as M07 p53; included here as a stand-alone
DP problem for the DP module.
"""


def solve_edit_distance_dp(word1, word2):
    """Return the minimum edit distance between word1 and word2.

    >>> solve_edit_distance_dp("horse", "ros")
    3
    """
    if len(word1) < len(word2):
        word1, word2 = word2, word1
    m, n = len(word1), len(word2)
    prev = list(range(n + 1))
    for i in range(1, m + 1):
        curr = [i] + [0] * n
        for j in range(1, n + 1):
            if word1[i - 1] == word2[j - 1]:
                curr[j] = prev[j - 1]
            else:
                curr[j] = 1 + min(prev[j], curr[j - 1], prev[j - 1])
        prev = curr
    return prev[n]


if __name__ == "__main__":
    print(solve_edit_distance_dp("horse", "ros"))
