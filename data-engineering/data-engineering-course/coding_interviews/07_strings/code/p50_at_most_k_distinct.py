"""Longest Substring with At Most K Distinct Characters.

Time:  O(n) — sliding window
Space: O(k) — the counter
"""

from collections import defaultdict


def solve_at_most_k_distinct(s, k):
    """Length of the longest substring with at most ``k`` distinct chars.

    >>> solve_at_most_k_distinct("eceba", 2)
    3
    """
    if k == 0:
        return 0
    counts = defaultdict(int)
    left = 0
    best = 0
    distinct = 0
    for right, ch in enumerate(s):
        if counts[ch] == 0:
            distinct += 1
        counts[ch] += 1
        while distinct > k:
            counts[s[left]] -= 1
            if counts[s[left]] == 0:
                distinct -= 1
            left += 1
        best = max(best, right - left + 1)
    return best


if __name__ == "__main__":
    print(solve_at_most_k_distinct("eceba", 2))
