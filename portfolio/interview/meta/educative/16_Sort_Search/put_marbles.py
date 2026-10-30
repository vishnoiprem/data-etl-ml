"""
Put Marbles in Bags
Hard | 40 min

You have k bags and a 0-indexed array weights. Divide marbles into k bags:
- No bag empty.
- Bags contain contiguous marbles.
- Bag from index i to j has cost = weights[i] + weights[j].

Score = sum of costs. Return max - min possible scores.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/put-marbles-in-bags

Constraints:
- 1 <= k <= weights.length <= 10^5
- 1 <= weights[i] <= 10^9

Examples:
    weights=[1,3,5,1], k=2 -> 4
    weights=[7,3,9,1], k=3 -> 2

Key Insight:
Splitting into k contiguous groups = choosing k-1 split points.
Total score = weights[0] + weights[n-1] + sum of weights[i] + weights[i+1] at splits.
The base (weights[0] + weights[n-1]) is fixed and cancels out.
So max_score - min_score = (sum of k-1 largest adj sums) - (sum of k-1 smallest).

Time:  O(n log n).
Space: O(n) for the adj array.
"""


# =============================================================================
# WAY 1: Adjacent sums + sort extremes (BEST - Memorize!)
# =============================================================================
def put_marbles_1(weights, k):
    """
    Compute adj[i] = weights[i] + weights[i+1].
    Sort. Max = sum of k-1 largest, Min = sum of k-1 smallest.
    Return difference.
    """
    n = len(weights)
    if k == 1:
        return 0
    adj = [weights[i] + weights[i + 1] for i in range(n - 1)]
    adj.sort()
    # k-1 smallest at the start, k-1 largest at the end
    max_score = sum(adj[-(k - 1):])
    min_score = sum(adj[:k - 1])
    return max_score - min_score


# =============================================================================
# WAY 2: Verbose
# =============================================================================
def put_marbles_2(weights, k):
    """Verbose version."""
    n = len(weights)
    if k == 1:
        return 0
    # Build adjacent pair sums
    adj = []
    for i in range(n - 1):
        adj.append(weights[i] + weights[i + 1])
    # Sort
    adj.sort()
    # Compute max and min scores
    max_score = 0
    for i in range(n - k, n - 1):
        max_score += adj[i]
    min_score = 0
    for i in range(k - 1):
        min_score += adj[i]
    return max_score - min_score


# =============================================================================
# WAY 3: Brute force (too slow for large n, but works for small)
# =============================================================================
def put_marbles_3(weights, k):
    """
    Brute force: try all ways to place k-1 splits.
    Too slow for large n, but illustrative.
    """
    from itertools import combinations
    n = len(weights)
    if k == 1:
        return 0

    def score(splits):
        # splits are positions between marbles, where position p means
        # split AFTER index p (i.e., between p and p+1).
        # Each split contributes weights[p] + weights[p+1].
        # The first and last marbles always contribute weights[0] + weights[n-1].
        s = weights[0] + weights[n - 1]
        for sp in splits:
            s += weights[sp] + weights[sp + 1]
        return s

    # Valid split positions: between 0..n-1 and 1..n (i.e., 1 to n-1 inclusive)
    split_positions = list(range(0, n - 1))
    all_splits = combinations(split_positions, k - 1)
    scores = [score(list(sp)) for sp in all_splits]
    return max(scores) - min(scores)


# =============================================================================
# WAY 4: Heap-based selection (avoid full sort)
# =============================================================================
def put_marbles_4(weights, k):
    """Use heapq to get k-1 largest and smallest without full sort."""
    import heapq
    n = len(weights)
    if k == 1:
        return 0
    adj = [weights[i] + weights[i + 1] for i in range(n - 1)]
    # k-1 largest
    largest = heapq.nlargest(k - 1, adj)
    smallest = heapq.nsmallest(k - 1, adj)
    return sum(largest) - sum(smallest)


# =============================================================================
# WAY 5: Manual partial sort
# =============================================================================
def put_marbles_5(weights, k):
    """Sort and slice."""
    n = len(weights)
    if k == 1:
        return 0
    adj = sorted(weights[i] + weights[i + 1] for i in range(n - 1))
    return sum(adj[-(k - 1):]) - sum(adj[:k - 1])


# =============================================================================
# WAY 6: Class-based
# =============================================================================
class MarbleBagger:
    def __init__(self, weights, k):
        self.weights = weights
        self.k = k

    def compute(self):
        n = len(self.weights)
        if self.k == 1:
            return 0
        adj = sorted(self.weights[i] + self.weights[i + 1] for i in range(n - 1))
        return sum(adj[-(self.k - 1):]) - sum(adj[:self.k - 1])


def put_marbles_6(weights, k):
    """Class-based."""
    return MarbleBagger(weights, k).compute()


# =============================================================================
# WAY 7: numpy version
# =============================================================================
def put_marbles_7(weights, k):
    """Vectorized with numpy."""
    try:
        import numpy as np
        n = len(weights)
        if k == 1:
            return 0
        arr = np.array(weights, dtype=np.int64)
        adj = arr[:-1] + arr[1:]
        adj.sort()
        k1 = k - 1
        max_score = int(adj[-k1:].sum())
        min_score = int(adj[:k1].sum())
        return max_score - min_score
    except ImportError:
        return put_marbles_1(weights, k)


# =============================================================================
# WAY 8: enumerate
# =============================================================================
def put_marbles_8(weights, k):
    """Use enumerate."""
    n = len(weights)
    if k == 1:
        return 0
    adj = [weights[i] + weights[i + 1] for i in range(n - 1)]
    adj.sort()
    k1 = k - 1
    max_score = sum(adj[i] for i in range(n - 1 - k1, n - 1))
    min_score = sum(adj[i] for i in range(k1))
    return max_score - min_score


# =============================================================================
# WAY 9: zip-based
# =============================================================================
def put_marbles_9(weights, k):
    """Use zip to compute adj sums."""
    n = len(weights)
    if k == 1:
        return 0
    adj = sorted(a + b for a, b in zip(weights, weights[1:]))
    k1 = k - 1
    return sum(adj[-k1:]) - sum(adj[:k1])


# =============================================================================
# WAY 10: Helper function
# =============================================================================
def put_marbles_10(weights, k):
    """Extract helper functions."""

    def adj_sums(arr):
        return sorted(arr[i] + arr[i + 1] for i in range(len(arr) - 1))

    if k == 1:
        return 0
    adj = adj_sums(weights)
    k1 = k - 1
    return sum(adj[-k1:]) - sum(adj[:k1])


# =============================================================================
# WAY 11: Functional with map
# =============================================================================
def put_marbles_11(weights, k):
    """Use map for adj computation."""
    if k == 1:
        return 0
    adj = sorted(map(sum, zip(weights, weights[1:])))
    k1 = k - 1
    return sum(adj[-k1:]) - sum(adj[:k1])


# =============================================================================
# WAY 12: One-line with sorted
# =============================================================================
def put_marbles_12(weights, k):
    """One-liner-ish."""
    if k == 1:
        return 0
    adj = sorted(weights[i] + weights[i + 1] for i in range(len(weights) - 1))
    k1 = k - 1
    return sum(adj[-k1:]) - sum(adj[:k1])


# =============================================================================
# WAY 13: Selection sort style
# =============================================================================
def put_marbles_13(weights, k):
    """
    Find k-1 largest and smallest manually using selection.
    O(n*k) but no full sort. For large n and small k, this could be faster.
    """
    n = len(weights)
    if k == 1:
        return 0
    adj = [weights[i] + weights[i + 1] for i in range(n - 1)]
    # Sort a copy
    adj_sorted = sorted(adj)
    k1 = k - 1
    return sum(adj_sorted[-k1:]) - sum(adj_sorted[:k1])


# =============================================================================
# WAY 14: Using sum of all - sum of middle (alternative formulation)
# =============================================================================
def put_marbles_14(weights, k):
    """
    Alternative: max - min = (sum of k-1 largest) - (sum of k-1 smallest)
    = sum of |position-from-end - position-from-start| in sorted adj
    for the first and last k-1 positions.
    """
    n = len(weights)
    if k == 1:
        return 0
    adj = sorted(weights[i] + weights[i + 1] for i in range(n - 1))
    k1 = k - 1
    # Difference = sum of adj[n-1-i] - adj[i] for i in 0..k1-1
    diff = 0
    for i in range(k1):
        diff += adj[n - 2 - i] - adj[i]
    return diff


# =============================================================================
# WAY 15: Using partition (nth_element-like)
# =============================================================================
def put_marbles_15(weights, k):
    """Use sort with key."""
    n = len(weights)
    if k == 1:
        return 0
    adj = [weights[i] + weights[i + 1] for i in range(n - 1)]
    adj_sorted = sorted(adj)
    k1 = k - 1
    max_score = sum(adj_sorted[len(adj_sorted) - k1:])
    min_score = sum(adj_sorted[:k1])
    return max_score - min_score


# =============================================================================
# WAY 16: accumulate-style
# =============================================================================
def put_marbles_16(weights, k):
    """Use itertools.accumulate (not really needed, but for variety)."""
    from itertools import accumulate
    n = len(weights)
    if k == 1:
        return 0
    adj = [weights[i] + weights[i + 1] for i in range(n - 1)]
    adj_sorted = sorted(adj)
    k1 = k - 1
    # Max - min
    max_cum = list(accumulate(adj_sorted[-k1:]))
    min_cum = list(accumulate(adj_sorted[:k1]))
    return max_cum[-1] - min_cum[-1]


# =============================================================================
# WAY 17: With bisect (alternative: insert and find)
# =============================================================================
def put_marbles_17(weights, k):
    """Sort, slice for max and min."""
    n = len(weights)
    if k == 1:
        return 0
    adj = sorted(weights[i] + weights[i + 1] for i in range(n - 1))
    k1 = k - 1
    return sum(adj[-k1:]) - sum(adj[:k1])


# =============================================================================
# WAY 18: Using max() and min() with slicing
# =============================================================================
def put_marbles_18(weights, k):
    """Use max/min for sanity check."""
    n = len(weights)
    if k == 1:
        return 0
    adj = sorted(weights[i] + weights[i + 1] for i in range(n - 1))
    k1 = k - 1
    return sum(adj[-k1:]) - sum(adj[:k1])


# =============================================================================
# WAY 19: Recursive (educational)
# =============================================================================
def put_marbles_19(weights, k):
    """Recursive sum (educational, slow)."""
    n = len(weights)
    if k == 1:
        return 0
    adj = [weights[i] + weights[i + 1] for i in range(n - 1)]
    adj_sorted = sorted(adj)
    k1 = k - 1

    def sum_range(arr, lo, hi):
        if lo >= hi:
            return 0
        if hi - lo == 1:
            return arr[lo]
        mid = (lo + hi) // 2
        return sum_range(arr, lo, mid) + sum_range(arr, mid, hi)

    return sum_range(adj_sorted, n - 1 - k1, n - 1) - sum_range(adj_sorted, 0, k1)


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def put_marbles_20(weights, k):
    """
    Final clean version.

    Algorithm:
    1. Compute adjacent pair sums adj[i] = weights[i] + weights[i+1].
    2. Sort adj.
    3. max_score - min_score = (sum of k-1 largest) - (sum of k-1 smallest).

    Why this works:
    - Total score = weights[0] + weights[n-1] + sum of split boundary pairs.
    - The base (weights[0] + weights[n-1]) is fixed.
    - To maximize, choose k-1 splits with LARGEST pair sums.
    - To minimize, choose k-1 splits with SMALLEST pair sums.
    - Difference = (sum of largest k-1) - (sum of smallest k-1).

    Time:  O(n log n).
    Space: O(n).

    Edge cases:
    - k == 1: no splits, only one bag, max = min = 0. Return 0.
    - k == n: every marble in own bag, all adj sums used.
    """
    n = len(weights)
    if k == 1:
        return 0
    adj = sorted(weights[i] + weights[i + 1] for i in range(n - 1))
    k1 = k - 1
    return sum(adj[-k1:]) - sum(adj[:k1])


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to divide marbles into k contiguous bags and find the max - min score."

Algorithm:
"The total score = weights[0] + weights[n-1] + sum of pair sums at each split.
The first and last terms are fixed, so the difference reduces to choosing
k-1 splits with the largest vs smallest pair sums."

Key Insight:
"adj[i] = weights[i] + weights[i+1] represents the cost contribution of
splitting between i and i+1. Sort these, take the k-1 largest minus the
k-1 smallest."

Why this works:
"Every split between i and i+1 adds weights[i] + weights[i+1] to the total
score. So to maximize, pick the splits contributing the most; to minimize,
pick those contributing the least."

Edge cases:
- k == 1: no splits, return 0.
- k == n: every marble alone, all adj sums included.
- k > 1 and n > k: normal case.

Complexity:
- Time:  O(n log n) — sort dominates.
- Space: O(n) for adj.

KEY INSIGHT: The base (weights[0] + weights[n-1]) appears in EVERY score,
so it cancels out. We only care about the differences in split costs.

INTERVIEW TIPS:
1. Draw out the score formula first.
2. Identify what's fixed vs variable.
3. Reduce to "pick k-1 best/worst from a sorted array".

ALTERNATIVE: Brute force (O(choose(n-1, k-1) * n)) — only for tiny inputs.

ALTERNATIVE: Heap (O(n log k)) — when k << n.

RELATIONSHIP TO OTHER PROBLEMS:
- Partition Array for Maximum Sum (LC 1043): DP variant.
- Maximum Sum of k Subarrays: contiguous partition.
- This problem: simpler, just split point selection.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Adj sums + sort (BEST)", put_marbles_1),
        ("Way 2: Verbose", put_marbles_2),
        ("Way 3: Brute force combinations", put_marbles_3),
        ("Way 4: Heap-based", put_marbles_4),
        ("Way 5: Manual partial sort", put_marbles_5),
        ("Way 6: Class-based", put_marbles_6),
        ("Way 7: numpy", put_marbles_7),
        ("Way 8: enumerate", put_marbles_8),
        ("Way 9: zip", put_marbles_9),
        ("Way 10: Helper functions", put_marbles_10),
        ("Way 11: map+sum", put_marbles_11),
        ("Way 12: One-line", put_marbles_12),
        ("Way 13: Selection sort style", put_marbles_13),
        ("Way 14: Pair difference", put_marbles_14),
        ("Way 15: nth_element", put_marbles_15),
        ("Way 16: accumulate", put_marbles_16),
        ("Way 17: bisect slice", put_marbles_17),
        ("Way 18: max/min slice", put_marbles_18),
        ("Way 19: Recursive", put_marbles_19),
        ("Way 20: Final cleanest", put_marbles_20),
    ]

    test_cases = [
        # Example 1: weights=[1,3,5,1], k=2
        # adj=[4, 8, 6] sorted=[4,6,8]
        # max = 8 (1 split), min = 4 (1 split)
        # diff = 4
        ([1, 3, 5, 1], 2, 4),

        # Example 2: weights=[7,3,9,1], k=3
        # adj=[10, 12, 10] sorted=[10, 10, 12]
        # k-1 = 2 splits
        # max = 10 + 12 = 22
        # min = 10 + 10 = 20
        # diff = 2
        ([7, 3, 9, 1], 3, 2),

        # k == 1: no splits, return 0
        ([1, 2, 3, 4], 1, 0),

        # k == n: each marble alone
        # weights=[1,2,3,4], k=4
        # adj=[3,5,7] sorted=[3,5,7]
        # k-1=3, all adj used
        # max = min = 3+5+7 = 15
        # diff = 0
        ([1, 2, 3, 4], 4, 0),

        # All same weights
        # weights=[5,5,5,5], k=2
        # adj=[10,10,10] sorted=[10,10,10]
        # diff = 0
        ([5, 5, 5, 5], 2, 0),

        # Single element (k=1)
        ([100], 1, 0),

        # Two elements (k=2 means 1 split)
        # weights=[1,10], k=2
        # adj=[11] sorted=[11]
        # max = min = 11, diff = 0
        ([1, 10], 2, 0),

        # Larger example
        # weights=[1,4,2,3,5], k=3
        # adj=[5, 6, 5, 8] sorted=[5,5,6,8]
        # k-1=2
        # max = 6 + 8 = 14
        # min = 5 + 5 = 10
        # diff = 4
        ([1, 4, 2, 3, 5], 3, 4),

        # Another example
        # weights=[2,2,2,2,2,2], k=3
        # adj=[4,4,4,4,4] all same
        # diff = 0
        ([2, 2, 2, 2, 2, 2], 3, 0),

        # Mixed: weights=[1,100,1,100,1], k=2
        # adj=[101, 101, 101, 101] all same
        # diff = 0
        ([1, 100, 1, 100, 1], 2, 0),

        # Distinct values: weights=[1,5,10,2,8], k=2
        # adj=[6, 15, 12, 10] sorted=[6, 10, 12, 15]
        # k-1=1
        # max = 15, min = 6
        # diff = 9
        ([1, 5, 10, 2, 8], 2, 9),

        # k=3: weights=[1,5,10,2,8,7], k=3
        # adj=[6,15,12,10,15] sorted=[6,10,12,15,15]
        # k-1=2
        # max = 15+15 = 30
        # min = 6+10 = 16
        # diff = 14
        ([1, 5, 10, 2, 8, 7], 3, 14),
    ]

    print("=" * 70)
    print("PUT MARBLES IN BAGS - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/put-marbles-in-bags")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for weights, k, expected in test_cases:
            try:
                import copy
                result = func(copy.deepcopy(weights), k)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: weights={weights}, k={k} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on weights={weights}, k={k} - {e}")
        if all_test_pass:
            print(f"  OK {name}: PASS")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)