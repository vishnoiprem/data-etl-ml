"""Longest Palindromic Substring — expand-around-center.

Time:  O(n²) — 2n-1 centers, each expanding O(n)
Space: O(1) extra
"""


def solve_longest_palindromic(s):
    """Return the longest palindromic substring.

    >>> solve_longest_palindromic("babad")
    'bab'
    """
    if len(s) < 2:
        return s

    def expand(left, right):
        while left >= 0 and right < len(s) and s[left] == s[right]:
            left -= 1
            right += 1
        return s[left + 1:right]

    best = s[0]
    for center in range(len(s) - 1):
        # Odd-length: single center; even-length: pair of centers.
        odd = expand(center, center)
        even = expand(center, center + 1)
        if len(odd) > len(best):
            best = odd
        if len(even) > len(best):
            best = even
    return best


if __name__ == "__main__":
    print(solve_longest_palindromic("babad"))
