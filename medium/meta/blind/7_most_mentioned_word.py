"""
Problem 7 (Medium) — Most-mentioned word across a dict of word lists

Given a dictionary mapping a category -> list of words, find the single
word that appears the most across ALL lists. Return the word AND its
total count. If there's a tie, return any of them.

Examples
--------
>>> d = {'titles': ['hello', 'world'], 'body': ['hello', 'there']}
>>> most_mentioned(d)
('hello', 2)
>>> d = {'a': ['x'], 'b': ['y']}
>>> most_mentioned(d)
('x', 1)
>>> most_mentioned({})
('', 0)

How to think (interview script)
------------------------------
"Flatten the dict's values into a stream of words, then count with a
defaultdict or dict.get. Loop twice: once to count, once to find the
max — OR use a single pass with a running max.

The Blind post mentions 'swapping key value of dict'. If the question
were 'sort by count descending', I'd build a new dict with
{count: [words]}, swap, and sort."

Complexity: O(n) time, O(k) extra space where k = unique words.

Follow-ups
----------
- "Top N words?"
  Use heapq.nlargest(n, counts.items(), key=lambda x: x[1]).
- "Case-insensitive?"
  Lower-case before counting.
- "Skip stop words?"
  Filter against a set.
"""

import heapq
from collections import Counter
from typing import Iterable, Tuple


# ----------------------------------------------------------------------
# L0 — Easy / brute force: two-pass dict accumulator.
# How to think: "Two nested loops, dict accumulator, then `max` with
# key=. This is the version that works without any imports."
# ----------------------------------------------------------------------
def most_mentioned_l0(words_by_category: dict[str, list[str]]) -> Tuple[str, int]:
    counts: dict[str, int] = {}
    for words in words_by_category.values():
        for w in words:
            counts[w] = counts.get(w, 0) + 1
    if not counts:
        return ('', 0)
    best = max(counts, key=counts.get)
    return best, counts[best]


# ----------------------------------------------------------------------
# L1 — Medium / interview-canonical: `Counter`.
# How to think: "`Counter` is the standard tool. `update` merges
# another iterable's counts. `most_common(1)[0]` is the idiomatic
# winner-pick."
# ----------------------------------------------------------------------
def most_mentioned(words_by_category: dict[str, list[str]]) -> Tuple[str, int]:
    """Return the (word, total_count) of the most-mentioned word across all categories."""
    counter: Counter[str] = Counter()
    for words in words_by_category.values():
        counter.update(words)
    if not counter:
        return ('', 0)
    # most_common returns a list of (word, count) sorted by count desc
    return counter.most_common(1)[0]


# ----------------------------------------------------------------------
# L2 — Hard / production-grade: streaming Top-K with `nlargest`.
# How to think: "If you need Top-K instead of just the max, switch to
# `heapq.nlargest`. Same Counter, different winner-pick. If the input
# is a stream and memory matters, keep a bounded heap as you process."
# ----------------------------------------------------------------------
def most_mentioned_l2(words_by_category: dict[str, list[str]], top_k: int = 1) -> list[Tuple[str, int]]:
    counter: Counter[str] = Counter()
    for words in words_by_category.values():
        counter.update(words)
    if not counter:
        return [('', 0)]
    # nlargest returns top-k sorted desc by count
    return heapq.nlargest(top_k, counter.items(), key=lambda kv: kv[1])


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
    samples = [
        ({'titles': ['hello', 'world'], 'body': ['hello', 'there']}, ('hello', 2)),
        ({'a': ['x'], 'b': ['y']}, ('x', 1)),
        ({}, ('', 0)),
        ({'a': ['x', 'x', 'y']}, ('x', 2)),
        ({'c1': ['foo', 'bar'], 'c2': ['foo']}, ('foo', 2)),
    ]
    for d, expected in samples:
        assert most_mentioned_l0(d) == expected, d
        assert most_mentioned(d) == expected, d
        # L2 with k=1 returns a list; compare first element
        assert most_mentioned_l2(d, top_k=1)[0] == expected, d
    # L2 top-2
    top2 = most_mentioned_l2({'a': ['x', 'y'], 'b': ['x', 'z']}, top_k=2)
    assert [w for w, _ in top2] == ['x', 'y'] or [w for w, _ in top2] == ['x', 'z']
    print("All tests passed for most_mentioned (L0 + L1 + L2).")
