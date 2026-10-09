"""Edit Distance (Levenshtein) — minimum insertions, deletions, substitutions.

Time:  O(m · n) — full DP table
Space: O(min(m, n)) — rolling row optimization
"""


def solve_edit_distance(word1, word2):
    """Return the minimum number of single-char edits to convert word1 to word2.

    >>> solve_edit_distance("horse", "ros")
    3
    """
    # Make word1 the longer string to keep the rolling row small.
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
    print(solve_edit_distance("horse", "ros"))
