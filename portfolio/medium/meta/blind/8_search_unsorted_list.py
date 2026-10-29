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


# ----------------------------------------------------------------------
# L0 — Easy / brute force: built-in `.index()`.
# How to think: "`list.index` is built-in; O(n), returns -1 on miss via
# try/except. Looks too easy to write in an interview — that's the
# point: say it out loud, then show you can do the explicit version."
# ----------------------------------------------------------------------
def search_l0(lst: list, target) -> int:
    try:
        return lst.index(target)
    except ValueError:
        return -1


# ----------------------------------------------------------------------
# L1 — Medium / interview-canonical: explicit enumerate loop.
# How to think: "Same complexity, but readable. Use this in interviews
# — `.index` looks too easy."
# ----------------------------------------------------------------------
def search(lst: list, target) -> int:
    """Return the index of `target` in `lst`, or -1 if not found."""
    for i, x in enumerate(lst):
        if x == target:
            return i
    return -1


# ----------------------------------------------------------------------
# L2 — Hard / production-grade: build a {value: index} dict once for
# O(1) repeated lookups (the list is static).
# How to think: "If the same list gets searched many times, build an
# index dict in O(n) preprocessing; subsequent lookups are O(1).
# Memory trade — say so in the interview."
# ----------------------------------------------------------------------
class SearchIndex:
    """O(1) lookups against a static unsorted list, at the cost of O(n) extra memory."""

    def __init__(self, lst: list) -> None:
        self._index: dict = {}
        for i, x in enumerate(lst):
            # First occurrence wins; if you want ALL indices, store a list.
            self._index.setdefault(x, i)

    def find(self, target) -> int:
        return self._index.get(target, -1)


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
    samples = [
        ([4, 2, 9, 7], 9, 2),
        ([4, 2, 9, 7], 5, -1),
        ([], 1, -1),
        ([1, 2, 1, 2], 2, 1),
        ([42], 42, 0),
        ([42], 0, -1),
    ]
    for lst, target, expected in samples:
        assert search_l0(lst, target) == expected, (lst, target)
        assert search(lst, target) == expected, (lst, target)
        # L2: SearchIndex
        idx = SearchIndex(lst)
        assert idx.find(target) == expected, (lst, target)
    print("All tests passed for search (L0 + L1 + L2).")
