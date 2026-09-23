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


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
    # Tie-break determinism: with the same count, max returns the first inserted.
    assert most_common_comment([['a'], ['b']]) == 'a'
    # Single location, single comment.
    assert most_common_comment([['foo', 'foo', 'foo']]) == 'foo'
    print("All tests passed for most_common_comment.")
