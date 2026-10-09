"""Top K Frequent Elements — k most common elements.

Time:  O(n) average using bucket sort by count
Space: O(n)
"""

from collections import Counter


def solve_top_k_frequent(nums, k):
    """Return the k most frequent elements (any order).

    >>> sorted(solve_top_k_frequent([1,1,1,2,2,3], 2))
    [1, 2]
    """
    counts = Counter(nums)
    n = len(nums)
    buckets = [[] for _ in range(n + 1)]
    for val, c in counts.items():
        buckets[c].append(val)
    out = []
    for c in range(n, 0, -1):
        for val in buckets[c]:
            out.append(val)
            if len(out) == k:
                return out
    return out


if __name__ == "__main__":
    print(sorted(solve_top_k_frequent([1, 1, 1, 2, 2, 3], 2)))
