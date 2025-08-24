import heapq
from collections import Counter


def top_k_frequent(nums, k):
    # Step 1: Count frequency of each number
    # Example: [1,1,1,2,2,3] → {1: 3, 2: 2, 3: 1}
    cnt = Counter(nums)

    print('cnt',cnt)

    # Step 2: Create a list of (frequency, number) pairs
    # We use (c, n) so we can sort by frequency (c)
    # Example: [(3, 1), (2, 2), (1, 3)]
    freq_pairs = [(c, n) for n, c in cnt.items()]
    print('freq_pairs',freq_pairs)

    # Step 3: Use heapq.nlargest to get the k largest items by frequency
    # It returns k tuples like [(3,1), (2,2)]
    largest_k = heapq.nlargest(k, freq_pairs)

    # Step 4: Extract just the numbers (the second item in each tuple)
    # Example: [1, 2]
    return [num for (_, num) in largest_k]


print(top_k_frequent([1, 2, 3, 4, 5], 2))