"""Longest Substring Without Repeating Characters.

Time:  O(n) — sliding window with last-seen map
Space: O(k) — k distinct chars in the window
"""


def solve_longest_substring(s):
    """Return the length of the longest substring with all unique characters.

    >>> solve_longest_substring("abcabcbb")
    3
    """
    last_seen = {}
    left = 0
    best = 0
    for right, ch in enumerate(s):
        # If we've seen this char in the current window, shrink from the left.
        if ch in last_seen and last_seen[ch] >= left:
            left = last_seen[ch] + 1
        last_seen[ch] = right
        best = max(best, right - left + 1)
    return best


if __name__ == "__main__":
    print(solve_longest_substring("abcabcbb"))
