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

from collections import Counter
from typing import Tuple


def most_mentioned(words_by_category: dict[str, list[str]]) -> Tuple[str, int]:
    """Return the (word, total_count) of the most-mentioned word across all categories."""
    counter: Counter[str] = Counter()
    for words in words_by_category.values():
        counter.update(words)
    if not counter:
        return ('', 0)
    # most_common returns a list of (word, count) sorted by count desc
    return counter.most_common(1)[0]


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
    # Single category
    assert most_mentioned({'a': ['x', 'x', 'y']}) == ('x', 2)
    # Same word in multiple categories — counts add up
    d = {'c1': ['foo', 'bar'], 'c2': ['foo']}
    assert most_mentioned(d) == ('foo', 2)
    # Empty
    assert most_mentioned({}) == ('', 0)
    print("All tests passed for most_mentioned.")
