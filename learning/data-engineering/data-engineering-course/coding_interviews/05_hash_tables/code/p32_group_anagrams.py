"""Group Anagrams — group strings that are anagrams of each other.

Time:  O(n · k) — n strings, each of length k, sort each for the key
Space: O(n · k) — output
"""

from collections import defaultdict


def solve_group_anagrams(strs):
    """Group anagrams; the order within a group is the input order.

    >>> sorted([sorted(g) for g in solve_group_anagrams(['eat','tea','tan','ate','nat','bat'])])
    [['ate', 'eat', 'tea'], ['bat'], ['nat', 'tan']]
    """
    buckets = defaultdict(list)
    for s in strs:
        # Sorted character tuple is a canonical anagram key.
        key = tuple(sorted(s))
        buckets[key].append(s)
    return list(buckets.values())


if __name__ == "__main__":
    print(solve_group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"]))
