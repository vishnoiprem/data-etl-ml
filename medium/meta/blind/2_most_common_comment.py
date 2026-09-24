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
"Per location I treat the comments as a set — duplicates inside one
location collapse to 1. Then across locations, count each unique
comment's locations. The comment with the highest count wins.

Data structure: dict[comment -> location_count]. One pass to populate
(dedup per location), one pass to find the max.

This is the canonical 'use a dict' question — the toolkit called out in
the Blind post (dict, list, set, sort)."

Complexity: O(n * k) where n = locations, k = avg comments per location.

Gotcha worth saying out loud
----------------------------
Iterating a `set` of strings has a RANDOM order per Python process (hash
randomization). If you dedup with `set(loc)`, ties can come out
differently on every run. `dict.fromkeys(loc)` dedups AND keeps the
original order, so ties go deterministically to the first comment seen.

Follow-ups
----------
- "What if we want ties broken alphabetically?"
  min(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0]   (see L2)
- "What if comments differ only by case / whitespace?"
  Normalize first: comment.strip().lower()
- "What if the input is a flat list, not nested?"
  Each comment becomes its own 'location' — but then dedup-per-location
  is trivially 1, and we just want the global mode.
- "Which locations mentioned it?"  Keep a set of location ids (see L4).
- "Top-k instead of top-1?"  heapq.nlargest(k, ...) (see L9).
"""

import heapq
from collections import Counter, defaultdict
from itertools import chain, groupby
from typing import Iterable


# ----------------------------------------------------------------------
# L0 — Easy / brute force: for every comment, count distinct locations.
# How to think: "For every comment, count how many locations contain it.
# `c in other` scans a list, so this is O(L²·K²). Ugly but correct.
# Start here to show you understand the problem, then improve."
# ----------------------------------------------------------------------
def most_common_comment_l0(comments_by_location: list[list[str]]) -> str:
    best, best_count = '', 0
    for loc in comments_by_location:
        for c in dict.fromkeys(loc):                     # dedup within this location
            n = sum(1 for other in comments_by_location if c in other)
            if n > best_count:
                best, best_count = c, n
    return best


# ----------------------------------------------------------------------
# L1 — Medium / interview-canonical: dict + dedup per location.
# How to think: "One pass: dedup inside each location, increment a dict.
# `max(..., key=...)` picks the winner. O(L·K). This is the answer."
# ----------------------------------------------------------------------
def most_common_comment(comments_by_location: list[list[str]]) -> str:
    """Return the comment that appears in the most distinct locations. '' if none."""
    counts: dict[str, int] = {}
    for comments in comments_by_location:
        for c in dict.fromkeys(comments):   # dedup per location, order kept
            counts[c] = counts.get(c, 0) + 1
    if not counts:
        return ''
    # max returns the first key with the max value; dicts keep insertion
    # order, so on a tie the comment seen first wins — every run.
    return max(counts, key=counts.get)


# ----------------------------------------------------------------------
# L2 — Counter + explicit alphabetical tie-break.
# How to think: "`Counter.update` counts an iterable. To break ties
# alphabetically, take the min of (-count, name). If ties don't matter,
# `most_common(1)` is enough."
# ----------------------------------------------------------------------
def most_common_comment_l2(comments_by_location: Iterable[Iterable[str]]) -> str:
    counts: Counter[str] = Counter()
    for loc in comments_by_location:
        counts.update(set(loc))           # set() per location dedups
    if not counts:
        return ''
    # min on (-count, name) → highest count, alphabetical on tie
    return min(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0]


# ----------------------------------------------------------------------
# L3 — defaultdict(int).
# How to think: "Same as L1, but defaultdict removes the .get(c, 0)
# boilerplate. Say 'defaultdict' out loud — interviewers like hearing
# that you know it."
# ----------------------------------------------------------------------
def most_common_comment_l3(comments_by_location: list[list[str]]) -> str:
    counts: defaultdict[str, int] = defaultdict(int)
    for loc in comments_by_location:
        for c in dict.fromkeys(loc):
            counts[c] += 1
    return max(counts, key=counts.get) if counts else ''


# ----------------------------------------------------------------------
# L4 — dict of sets: comment -> {location ids}.
# How to think: "Instead of a count, store WHICH locations mentioned the
# comment. A set ignores repeats automatically, so no dedup step. The
# answer is the comment with the biggest set — and it answers the
# follow-up 'which locations?' for free. Costs O(L·K) memory."
# ----------------------------------------------------------------------
def most_common_comment_l4(comments_by_location: list[list[str]]) -> str:
    locations: dict[str, set[int]] = {}
    for loc_id, loc in enumerate(comments_by_location):
        for c in loc:
            locations.setdefault(c, set()).add(loc_id)
    if not locations:
        return ''
    return max(locations, key=lambda c: len(locations[c]))


# ----------------------------------------------------------------------
# L5 — one-liner: Counter over chained, deduped locations.
# How to think: "map(set, ...) dedups each location, chain flattens,
# Counter counts, most_common(1) picks the winner. Show it AFTER L1 as
# 'the Pythonic version' — don't lead with it."
# ----------------------------------------------------------------------
def most_common_comment_l5(comments_by_location: list[list[str]]) -> str:
    top = Counter(chain.from_iterable(map(dict.fromkeys, comments_by_location))).most_common(1)
    return top[0][0] if top else ''


# ----------------------------------------------------------------------
# L6 — sort + groupby (no dict at all).
# How to think: "Flatten the deduped comments, sort so equal comments
# sit next to each other, then groupby gives each comment's run length.
# O(N log N). This is literally what SQL does for
# SELECT comment, COUNT(DISTINCT location) ... GROUP BY comment."
# ----------------------------------------------------------------------
def most_common_comment_l6(comments_by_location: list[list[str]]) -> str:
    flat = sorted(c for loc in comments_by_location for c in set(loc))
    best, best_count = '', 0
    for comment, group in groupby(flat):
        n = sum(1 for _ in group)
        if n > best_count:
            best, best_count = comment, n
    return best


# ----------------------------------------------------------------------
# L7 — single pass with a running max.
# How to think: "Update the leader while counting instead of a second
# pass over the dict. Useful when the data is a stream and you want the
# current leader at any moment. Ties: the first comment to REACH the
# top count keeps the lead."
# ----------------------------------------------------------------------
def most_common_comment_l7(comments_by_location: Iterable[Iterable[str]]) -> str:
    counts: dict[str, int] = {}
    best, best_count = '', 0
    for loc in comments_by_location:
        for c in dict.fromkeys(loc):
            counts[c] = counts.get(c, 0) + 1
            if counts[c] > best_count:
                best, best_count = c, counts[c]
    return best


# ----------------------------------------------------------------------
# L8 — swap key/value: bucket comments by their count.
# How to think: "The Blind post mentions 'swapping key value of dict'.
# Invert {comment: count} into {count: [comments]}. The answer is any
# comment in the bucket with the highest count — and that bucket IS
# the full list of tied winners, which is a nice follow-up answer."
# ----------------------------------------------------------------------
def most_common_comment_l8(comments_by_location: list[list[str]]) -> str:
    counts: dict[str, int] = {}
    for loc in comments_by_location:
        for c in dict.fromkeys(loc):
            counts[c] = counts.get(c, 0) + 1
    by_count: dict[int, list[str]] = {}
    for comment, n in counts.items():
        by_count.setdefault(n, []).append(comment)
    if not by_count:
        return ''
    return by_count[max(by_count)][0]


# ----------------------------------------------------------------------
# L9 — heapq.nlargest for top-k.
# How to think: "If the follow-up is 'give me the top 3 comments',
# nlargest(k, ...) is O(U log k) instead of sorting all U unique
# comments. For k=1 it's the same as max. Returns the top-1 string to
# match the other versions; top_k() below is the real follow-up."
# ----------------------------------------------------------------------
def top_k_comments(comments_by_location: list[list[str]], k: int) -> list[tuple[str, int]]:
    counts = Counter(chain.from_iterable(map(dict.fromkeys, comments_by_location)))
    return heapq.nlargest(k, counts.items(), key=lambda kv: kv[1])


def most_common_comment_l9(comments_by_location: list[list[str]]) -> str:
    top = top_k_comments(comments_by_location, 1)
    return top[0][0] if top else ''


IMPLEMENTATIONS = [
    most_common_comment_l0,
    most_common_comment,
    most_common_comment_l2,
    most_common_comment_l3,
    most_common_comment_l4,
    most_common_comment_l5,
    most_common_comment_l6,
    most_common_comment_l7,
    most_common_comment_l8,
    most_common_comment_l9,
]


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
    samples = [
        [['love', 'great'], ['love', 'amazing'], ['love']],
        [['a', 'b'], ['b', 'c'], ['a', 'b']],
        [],
        [[]],
        [['solo']],
        [['a'], ['b']],
        [['foo', 'foo', 'foo']],
        # 'spam' is repeated at ONE location, 'ok' appears at two —
        # without per-location dedup 'spam' would wrongly win.
        [['spam', 'spam', 'spam', 'ok'], ['ok']],
    ]
    for sample in samples:
        loc_counts = Counter(c for loc in sample for c in set(loc))
        best = max(loc_counts.values(), default=0)
        for impl in IMPLEMENTATIONS:
            pick = impl(sample)
            # Ties may be broken differently, but every version must pick
            # a comment with the maximum location count.
            assert loc_counts.get(pick, 0) == best, (impl.__name__, sample, pick)
    assert all(impl([['spam', 'spam', 'spam', 'ok'], ['ok']]) == 'ok' for impl in IMPLEMENTATIONS)
    # Tie-breaks: first seen wins for dict-based versions (every run),
    # alphabetical for L2.
    assert most_common_comment([['y', 'x']]) == 'y'
    assert most_common_comment_l2([['b'], ['a']]) == 'a'
    assert top_k_comments([['a', 'b'], ['a', 'c'], ['a', 'b']], 2) == [('a', 3), ('b', 2)]
    print(f"All tests passed for most_common_comment ({len(IMPLEMENTATIONS)} implementations, L0..L9).")
