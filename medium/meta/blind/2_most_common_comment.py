"""
Problem 2 (Medium) — Most common comment across locations (dedup per location)

The bookstore gathered a list of customer comments from each shop location
and wants to find the most common comment across all locations, IGNORING
duplicates from the same location. If multiple comments tie, return any one.

Input: list[list[str]] — outer is locations, inner is comments at that location.
Output: the comment string that appears most often across distinct locations.

Examples
--------
>>> most_common_comment([['love', 'great'], ['love', 'amazing'], ['love']])
'love'
>>> most_common_comment([['a', 'b'], ['b', 'c'], ['a', 'b']])
'b'
>>> most_common_comment([])
''
>>> most_common_comment([['solo']])
'solo'

How to think (interview script)
------------------------------
"Per location I treat the comment as a set — duplicates inside one
location collapse to 1. Then across locations, count each unique
comment's locations. The comment with the highest count wins.

Data structure: dict[comment -> location_count]. One pass to populate
(using set per location), one pass to find the max.

This is the canonical 'use a dict' question — the toolkit called out in
the Blind post (dict, list, set, sort)."

Complexity: O(n * k) where n = locations, k = avg comments per location.

Follow-ups
----------
- "What if we want ties broken alphabetically?"
  Return min(comment for comment, count == max_count)
- "What if comments are case-sensitive?"
  Lower-case them first: comment.lower()
- "What if the input is a flat list, not nested?"
  Each comment becomes its own 'location' — but then dedup-per-location
  is trivially 1, and we just want the global mode.
"""

from collections import Counter
from typing import Iterable


# ----------------------------------------------------------------------
# L0 — Easy / brute force: for every comment, count distinct locations.
# How to think: "For every comment, count how many distinct locations
# contain it. Nested loops → O(L²·K). Ugly but correct. Start here to
# show you understand the problem, then improve."
# ----------------------------------------------------------------------
def most_common_comment_l0(comments_by_location: list[list[str]]) -> str:
    best, best_count = '', 0
    for loc in comments_by_location:
        for c in set(loc):                               # dedup within this location
            n = sum(1 for other in comments_by_location if c in other)
            if n > best_count:
                best, best_count = c, n
    return best


# ----------------------------------------------------------------------
# L1 — Medium / interview-canonical: dict + set per location.
# How to think: "One pass: dedup inside each location with `set(loc)`,
# increment a dict. `max(..., key=...)` picks the winner. O(L·K)."
# ----------------------------------------------------------------------
def most_common_comment(comments_by_location: list[list[str]]) -> str:
    """Return the comment that appears in the most distinct locations. '' if none."""
    counts: dict[str, int] = {}
    for comments in comments_by_location:
        for c in set(comments):           # dedup per location
            counts[c] = counts.get(c, 0) + 1
    if not counts:
        return ''
    # max picks the first key it sees with the max value — stable.
    return max(counts, key=counts.get)


# ----------------------------------------------------------------------
# L2 — Hard / production-grade: Counter + explicit alphabetical tie-break.
# How to think: "`Counter.most_common()` already sorts by count desc.
# To break ties alphabetically, sort on `(-count, name)`. If ties
# don't matter, just take `most_common(1)` and you're done."
# ----------------------------------------------------------------------
def most_common_comment_l2(comments_by_location: Iterable[Iterable[str]]) -> str:
    flat: Counter[str] = Counter()
    for loc in comments_by_location:
        flat.update(set(loc))             # set() per location dedups
    if not flat:
        return ''
    # min on (-count, name) → highest count, alphabetical on tie
    return min(flat.items(), key=lambda kv: (-kv[1], kv[0]))[0]


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
    samples = [
        [['love', 'great'], ['love', 'amazing'], ['love']],
        [['a', 'b'], ['b', 'c'], ['a', 'b']],
        [],
        [['solo']],
        [['a'], ['b']],
        [['foo', 'foo', 'foo']],
    ]
    for s in samples:
        a = most_common_comment_l0(s)
        b = most_common_comment(s)
        c = most_common_comment_l2(s)
        # L0 / L1 / L2 may differ on tie-breaks, but each must pick a comment
        # with the maximum location count.
        loc_counts = Counter(c for loc in s for c in set(loc))
        best = max(loc_counts.values(), default=0)
        for pick in (a, b, c):
            assert loc_counts.get(pick, 0) == best, (s, a, b, c)
    # Tie-break determinism: with the same count, max returns the first inserted.
    assert most_common_comment([['a'], ['b']]) == 'a'
    # L2 picks alphabetically first on tie
    assert most_common_comment_l2([['b'], ['a']]) == 'a'
    # Single location, single comment.
    assert most_common_comment([['foo', 'foo', 'foo']]) == 'foo'
    print("All tests passed for most_common_comment (L0 + L1 + L2).")
