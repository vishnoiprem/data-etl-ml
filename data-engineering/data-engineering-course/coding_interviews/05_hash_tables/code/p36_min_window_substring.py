"""Minimum Window Substring — smallest substring of ``s`` containing all of ``t``.

Time:  O(n) — sliding window with a counter
Space: O(k) — k distinct chars in t
"""

from collections import Counter


def solve_min_window_substring(s, t):
    """Return the smallest substring of s containing every char of t, or "".

    >>> solve_min_window_substring("ADOBECODEBANC", "ABC")
    'BANC'
    """
    if not t or not s:
        return ""
    need = Counter(t)
    missing = len(t)
    left = start = end = 0
    for right, ch in enumerate(s, 1):
        if need[ch] > 0:
            missing -= 1
        need[ch] -= 1
        if missing == 0:
            # Shrink from the left while we still have all chars.
            while left < right and need[s[left]] < 0:
                need[s[left]] += 1
                left += 1
            if end == 0 or right - left <= end - start:
                start, end = left, right
            # Drop the leftmost char and look for a new window.
            need[s[left]] += 1
            missing += 1
            left += 1
    return s[start:end]


if __name__ == "__main__":
    print(solve_min_window_substring("ADOBECODEBANC", "ABC"))
