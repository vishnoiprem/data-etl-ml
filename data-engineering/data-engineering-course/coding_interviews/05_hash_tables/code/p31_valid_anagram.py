"""Valid Anagram — are two strings anagrams of each other?

Time:  O(n) — single pass with a counter
Space: O(k) — k distinct characters
"""

from collections import Counter


def solve_valid_anagram(s, t):
    """Return True if ``s`` and ``t`` are anagrams (case-sensitive, a-z).

    >>> solve_valid_anagram("anagram", "nagaram")
    True
    """
    return Counter(s) == Counter(t)


if __name__ == "__main__":
    print(solve_valid_anagram("anagram", "nagaram"))
