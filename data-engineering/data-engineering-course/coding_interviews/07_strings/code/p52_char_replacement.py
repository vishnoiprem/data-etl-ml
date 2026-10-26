"""Longest Repeating Character Replacement.

Time:  O(n) — sliding window with running max frequency
Space: O(k) — k distinct chars
"""

from collections import defaultdict


def solve_char_replacement(s, k):
    """Length of longest substring with at most ``k`` replacements.

    >>> solve_char_replacement("ABAB", 2)
    4
    """
    counts = defaultdict(int)
    left = 0
    max_count = 0  # max frequency of any single char in the window
    best = 0
    for right, ch in enumerate(s):
        counts[ch] += 1
        max_count = max(max_count, counts[ch])
        # Window is valid if (size - max_count) <= k.
        if (right - left + 1) - max_count > k:
            counts[s[left]] -= 1
            left += 1
        best = max(best, right - left + 1)
    return best


if __name__ == "__main__":
    print(solve_char_replacement("ABAB", 2))
