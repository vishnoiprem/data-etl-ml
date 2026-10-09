"""Longest Common Subsequence.

Time:  O(m · n)
Space: O(min(m, n)) — rolling row
"""


def solve_lcs(text1, text2):
    """Return the length of the LCS.

    >>> solve_lcs("abcde", "ace")
    3
    """
    if len(text1) < len(text2):
        text1, text2 = text2, text1
    m, n = len(text1), len(text2)
    prev = [0] * (n + 1)
    for i in range(1, m + 1):
        curr = [0] * (n + 1)
        for j in range(1, n + 1):
            if text1[i - 1] == text2[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev = curr
    return prev[n]


if __name__ == "__main__":
    print(solve_lcs("abcde", "ace"))
