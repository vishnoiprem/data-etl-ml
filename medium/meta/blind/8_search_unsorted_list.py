"""
Problem 8 (Easy) — Search an element in an unsorted list

Return the index of `target` in `lst`, or -1 if not found. Linear scan
because the list is unsorted.

Examples
--------
>>> search([4, 2, 9, 7], 9)
2
>>> search([4, 2, 9, 7], 5)
-1
>>> search([], 1)
-1

How to think (interview script)
------------------------------
"Linear scan is O(n); the list is unsorted so we can't do better. The
interviewer might be probing whether I default to binary search
incorrectly — I should explicitly call out that the input is unsorted.

If I wanted O(1) lookup, I'd build a {value: index} dict in O(n)
preprocessing. That trades memory for repeated lookups. Mention this
only if the use case calls for many searches."

Complexity: O(n) time, O(1) extra space.

Follow-ups
----------
- "What if the list is sorted?"
  Binary search, O(log n).
- "What if I have many searches on the same list?"
  Build a dict: {value: index} in O(n) preprocessing, then O(1) lookups.
- "What if there are duplicates and I want ALL indices?"
  Continue the scan and collect indices into a list.
"""


def search(lst: list, target) -> int:
    """Return the index of `target` in `lst`, or -1 if not found."""
    for i, x in enumerate(lst):
        if x == target:
            return i
    return -1


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
    # Duplicates: returns first occurrence
    assert search([1, 2, 1, 2], 2) == 1
    # Single element
    assert search([42], 42) == 0
    assert search([42], 0) == -1
    print("All tests passed for search.")
