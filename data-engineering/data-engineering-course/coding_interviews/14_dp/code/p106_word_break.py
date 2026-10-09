"""Word Break — can ``s`` be segmented into words?

Time:  O(n² · L) where L is the average word length (set lookups)
Space: O(n)
"""


def solve_word_break(s, word_dict):
    """Return True if s can be segmented into words from word_dict.

    >>> solve_word_break("leetcode", ["leet", "code"])
    True
    """
    word_set = set(word_dict)
    n = len(s)
    dp = [False] * (n + 1)
    dp[0] = True
    for i in range(1, n + 1):
        for j in range(i):
            if dp[j] and s[j:i] in word_set:
                dp[i] = True
                break
    return dp[n]


if __name__ == "__main__":
    print(solve_word_break("leetcode", ["leet", "code"]))
