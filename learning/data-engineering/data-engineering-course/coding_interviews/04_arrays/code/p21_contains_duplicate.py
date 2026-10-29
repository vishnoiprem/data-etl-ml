"""Contains Duplicate — does the array have any value appearing twice?

Time:  O(n) — set insert is O(1) avg
Space: O(n) — the set
"""


def solve_contains_duplicate(nums):
    """Return True if any value appears at least twice.

    >>> solve_contains_duplicate([1, 2, 3, 1])
    True
    """
    seen = set()
    for val in nums:
        if val in seen:
            return True
        seen.add(val)
    return False


if __name__ == "__main__":
    print(solve_contains_duplicate([1, 2, 3, 1]))
