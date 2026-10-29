"""Palindrome Partitioning — every way to split s into palindromic pieces.

Time:  O(n · 2^n) — there are 2^(n-1) splits to consider
Space: O(n)
"""


def solve_palindrome_partitioning(s):
    """Return every palindromic partition of s.

    >>> sorted([tuple(p) for p in solve_palindrome_partitioning("aab")])
    [('a', 'a', 'b'), ('aa', 'b')]
    """
    out = []

    def is_pal(left, right):
        while left < right:
            if s[left] != s[right]:
                return False
            left += 1
            right -= 1
        return True

    def backtrack(start, current):
        if start == len(s):
            out.append(current[:])
            return
        for end in range(start, len(s)):
            if is_pal(start, end):
                current.append(s[start:end + 1])
                backtrack(end + 1, current)
                current.pop()

    backtrack(0, [])
    return out


if __name__ == "__main__":
    print(solve_palindrome_partitioning("aab"))
