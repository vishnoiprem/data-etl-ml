"""Top K Frequent Words.

Time:  O(n log k)
Space: O(n)
"""

import heapq
from collections import Counter


def solve_top_k_frequent_words(words, k):
    """Return the k most frequent words, ties broken by lexicographic order.

    >>> solve_top_k_frequent_words(["i","love","leetcode","i","love","coding"], 2)
    ['i', 'love']
    """
    counts = Counter(words)
    # Heap key is (count, -word) so smaller word wins ties at the same count,
    # and we then pop least-frequent (and lexicographically smallest on tie).
    heap = [(-count, word) for word, count in counts.items()]
    heapq.heapify(heap)
    return [heapq.heappop(heap)[1] for _ in range(min(k, len(heap)))]


if __name__ == "__main__":
    print(solve_top_k_frequent_words(["i", "love", "leetcode", "i", "love", "coding"], 2))
