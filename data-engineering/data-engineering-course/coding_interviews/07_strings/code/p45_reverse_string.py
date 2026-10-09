"""Reverse String — reverse a list of characters in-place.

Time:  O(n)
Space: O(1)
"""


def solve_reverse_string(s):
    """Reverse a list of characters in-place and return it.

    >>> solve_reverse_string(list("hello"))
    ['o', 'l', 'l', 'e', 'h']
    """
    left, right = 0, len(s) - 1
    while left < right:
        s[left], s[right] = s[right], s[left]
        left += 1
        right -= 1
    return s


if __name__ == "__main__":
    print(solve_reverse_string(list("hello")))
