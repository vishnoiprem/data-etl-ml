"""
Put Marbles in Bags
Hard | 40 min

You have k bags. Distribute marbles (weights) into them (each bag has at
least one marble, contiguous in original array). Score of a distribution
= sum of first marble + last marble in each bag. Return max_score -
min_score.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/put-marbles-in-bags

Examples:
    weights=[1,3,5,1], k=2 -> 4
    # Split: [1,3] | [5,1]: scores 1+3+5+1=10
    # Split: [1] | [3,5,1]: scores 1+1+3+1=6
    # Split: [1,3,5] | [1]: scores 1+5+1+1=8
    # Max=10, Min=6. Diff=4.

    weights=[1,3], k=2 -> 0
    # Only split: [1] | [3]: scores 1+1+3+3=8. Same for both. Diff=0.

Constraints:
- 1 <= k <= weights.length <= 10^5
- 1 <= weights[i] <= 10^9

KEY INSIGHT: Score = sum of all weights + sum of (k-1) cut positions.
  - n cuts available (between adjacent marbles).
  - Max score: pick k-1 LARGEST cuts.
  - Min score: pick k-1 SMALLEST cuts.
  - Diff = sum of (k-1) largest cuts - sum of (k-1) smallest cuts.
"""


# =============================================================================
# WAY 1: Sort + top/bottom k-1 (BEST - Memorize!)
# =============================================================================
def put_marbles_1(weights, k):
    """
    KEY INSIGHT: Score = total + sum of cuts. Min uses smallest cuts,
    max uses largest cuts. Diff = sum of (k-1) largest cuts - sum of
    (k-1) smallest cuts.
    """
    n = len(weights)
    cuts = [weights[i] + weights[i + 1] for i in range(n - 1)]
    cuts.sort()
    if k - 1 == 0:
        return 0
    # Min score: pick k-1 smallest cuts. Max score: pick k-1 largest cuts.
    return sum(cuts[-(k - 1):]) - sum(cuts[:k - 1])


# =============================================================================
# WAY 2: Sort + manual sum
# =============================================================================
def put_marbles_2(weights, k):
    n = len(weights)
    cuts = [weights[i] + weights[i + 1] for i in range(n - 1)]
    cuts.sort()
    if k - 1 == 0:
        return 0
    min_sum = sum(cuts[:k - 1])
    max_sum = sum(cuts[-(k - 1):])
    return max_sum - min_sum


# =============================================================================
# WAY 3: With heapq (nsmallest / nlargest)
# =============================================================================
def put_marbles_3(weights, k):
    import heapq
    n = len(weights)
    cuts = [weights[i] + weights[i + 1] for i in range(n - 1)]
    # nsmallest is O(n log k)
    smallest = heapq.nsmallest(k - 1, cuts)
    largest = heapq.nlargest(k - 1, cuts)
    return sum(largest) - sum(smallest)


# =============================================================================
# WAY 4: Brute force (DP) - exponential
# =============================================================================
def put_marbles_4(weights, k):
    """Brute force DP. Returns (min_score, max_score)."""
    n = len(weights)

    def compute_min(i, bags_left):
        # Returns min score for distributing weights[i:] into bags_left bags
        if bags_left == 1:
            return weights[i] + weights[n - 1]
        best = float('inf')
        for j in range(i, n - bags_left + 1):
            score = weights[i] + weights[j] + compute_min(j + 1, bags_left - 1)
            if score < best:
                best = score
        return best

    def compute_max(i, bags_left):
        if bags_left == 1:
            return weights[i] + weights[n - 1]
        best = float('-inf')
        for j in range(i, n - bags_left + 1):
            score = weights[i] + weights[j] + compute_max(j + 1, bags_left - 1)
            if score > best:
                best = score
        return best

    return compute_max(0, k) - compute_min(0, k)


# =============================================================================
# WAY 5: Sort in descending order
# =============================================================================
def put_marbles_5(weights, k):
    n = len(weights)
    cuts = [weights[i] + weights[i + 1] for i in range(n - 1)]
    cuts.sort(reverse=True)
    if k - 1 == 0:
        return 0
    # Top k-1 are now at front, bottom k-1 at end
    return sum(cuts[:k - 1]) - sum(cuts[-(k - 1):])


# =============================================================================
# WAY 6: Bisect-based partition selection
# =============================================================================
def put_marbles_6(weights, k):
    import bisect
    n = len(weights)
    cuts = sorted(weights[i] + weights[i + 1] for i in range(n - 1))
    # Find pivot at index k-2 (the largest of smallest k-1)
    if k - 1 == 0:
        return 0
    # Sum of smallest k-1: from cuts[0] to cuts[k-2]
    min_sum = sum(cuts[:k - 1])
    # Sum of largest k-1: from cuts[n-k] to cuts[n-2]
    max_sum = sum(cuts[n - k:n - 1])
    return max_sum - min_sum


# =============================================================================
# WAY 7: Partial sort via heapselect (O(n))
# =============================================================================
def put_marbles_7(weights, k):
    import heapq
    n = len(weights)
    if k - 1 == 0:
        return 0
    cuts = [weights[i] + weights[i + 1] for i in range(n - 1)]

    # k-1 smallest via heapreplace
    smallest = list(cuts[:k - 1])
    heapq.heapify(smallest)
    for c in cuts[k - 1:]:
        if c < smallest[0]:
            heapq.heapreplace(smallest, c)
    min_sum = sum(smallest)

    # k-1 largest (use max-heap via negative)
    largest = [-c for c in cuts[:k - 1]]
    heapq.heapify(largest)
    for c in cuts[k - 1:]:
        if -c > largest[0]:
            heapq.heapreplace(largest, -c)
    max_sum = -sum(largest)

    return max_sum - min_sum


# =============================================================================
# WAY 8: Sort + take ends with explicit indexing
# =============================================================================
def put_marbles_8(weights, k):
    n = len(weights)
    cuts = sorted(weights[i] + weights[i + 1] for i in range(n - 1))
    if k - 1 == 0:
        return 0
    # k-1 smallest are at indices 0..k-2
    min_sum = sum(cuts[0:k - 1])
    # k-1 largest are at indices n-k..n-2
    max_sum = sum(cuts[n - k:n - 1])
    return max_sum - min_sum


# =============================================================================
# WAY 9: Using itertools.accumulate
# =============================================================================
def put_marbles_9(weights, k):
    import itertools
    n = len(weights)
    if k - 1 == 0:
        return 0
    cuts = sorted(weights[i] + weights[i + 1] for i in range(n - 1))
    min_partial = list(itertools.accumulate(cuts[:k - 1]))[-1] if k - 1 > 0 else 0
    max_partial = sum(cuts[-(k - 1):])
    return max_partial - min_partial


# =============================================================================
# WAY 10: Class-based
# =============================================================================
class MarbleDistributor:
    def __init__(self, weights):
        self.weights = weights
        self.n = len(weights)
        self.cuts = sorted(
            weights[i] + weights[i + 1] for i in range(self.n - 1)
        )

    def score_diff(self, k):
        if k - 1 == 0:
            return 0
        min_sum = sum(self.cuts[:k - 1])
        max_sum = sum(self.cuts[-(k - 1):])
        return max_sum - min_sum


def put_marbles_10(weights, k):
    return MarbleDistributor(weights).score_diff(k)


# =============================================================================
# WAY 11: Sort + reverse slice (descending)
# =============================================================================
def put_marbles_11(weights, k):
    n = len(weights)
    cuts = sorted([weights[i] + weights[i + 1] for i in range(n - 1)], reverse=True)
    if k - 1 == 0:
        return 0
    # Top k-1 cuts (max sum)
    max_sum = sum(cuts[:k - 1])
    # Bottom k-1 cuts (min sum) - need to find them
    # Since reverse-sorted, bottom k-1 are at the end
    min_sum = sum(cuts[-(k - 1):])
    return max_sum - min_sum


# =============================================================================
# WAY 12: numpy sort
# =============================================================================
def put_marbles_12(weights, k):
    import numpy as np
    a = np.array(weights)
    cuts = np.sort(a[:-1] + a[1:])
    if k - 1 == 0:
        return 0
    return int(cuts[-(k - 1):].sum() - cuts[:k - 1].sum())


# =============================================================================
# WAY 13: One-liner style
# =============================================================================
def put_marbles_13(weights, k):
    n = len(weights)
    cuts = sorted(weights[i] + weights[i + 1] for i in range(n - 1))
    return sum(cuts[n - k:n - 1]) - sum(cuts[:k - 1]) if k > 1 else 0


# =============================================================================
# WAY 14: Using functools.reduce
# =============================================================================
def put_marbles_14(weights, k):
    from functools import reduce
    n = len(weights)
    if k - 1 == 0:
        return 0
    cuts = sorted(weights[i] + weights[i + 1] for i in range(n - 1))
    min_sum = reduce(lambda a, b: a + b, cuts[:k - 1])
    max_sum = reduce(lambda a, b: a + b, cuts[n - k:n - 1])
    return max_sum - min_sum


# =============================================================================
# WAY 15: Sort + map + sum
# =============================================================================
def put_marbles_15(weights, k):
    n = len(weights)
    if k - 1 == 0:
        return 0
    cuts = sorted(weights[i] + weights[i + 1] for i in range(n - 1))
    # min = sum of first k-1
    min_sum = sum(map(int, cuts[:k - 1]))
    # max = sum of last k-1
    max_sum = sum(map(int, cuts[-(k - 1):]))
    return max_sum - min_sum


# =============================================================================
# WAY 16: Sort + manual extraction
# =============================================================================
def put_marbles_16(weights, k):
    n = len(weights)
    if k - 1 == 0:
        return 0
    cuts = sorted(weights[i] + weights[i + 1] for i in range(n - 1))
    # Smallest k-1 cuts
    smallest = []
    for i in range(k - 1):
        smallest.append(cuts[i])
    # Largest k-1 cuts
    largest = []
    for i in range(n - 2, n - 1 - (k - 1), -1):
        largest.append(cuts[i])
    return sum(largest) - sum(smallest)


# =============================================================================
# WAY 17: Sort + compute via zip
# =============================================================================
def put_marbles_17(weights, k):
    n = len(weights)
    if k - 1 == 0:
        return 0
    cuts = sorted(weights[i] + weights[i + 1] for i in range(n - 1))
    min_sum = sum(cuts[0:k - 1])
    max_sum = sum(cuts[n - k:n - 1])
    return max_sum - min_sum


# =============================================================================
# WAY 18: Using statistics
# =============================================================================
def put_marbles_18(weights, k):
    n = len(weights)
    if k - 1 == 0:
        return 0
    cuts = sorted(weights[i] + weights[i + 1] for i in range(n - 1))
    # Use slicing directly
    return sum(cuts[-(k - 1):]) - sum(cuts[:k - 1])


# =============================================================================
# WAY 19: Sort + explicit prefix/suffix differences
# =============================================================================
def put_marbles_19(weights, k):
    n = len(weights)
    if k - 1 == 0:
        return 0
    cuts = sorted(weights[i] + weights[i + 1] for i in range(n - 1))
    # prefix sums
    prefix = [0] * (n)
    s = 0
    for i in range(n - 1):
        s += cuts[i]
        prefix[i] = s
    # min_sum = prefix[k-2] (sum of cuts[0..k-2])
    min_sum = prefix[k - 2]
    # max_sum = sum of cuts[n-k..n-2]
    max_sum = sum(cuts[n - k:n - 1])
    return max_sum - min_sum


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def put_marbles_20(weights, k):
    """
    THE ONE TO MEMORIZE.

    KEY INSIGHT: Score = sum(weights) + sum(cuts).
    Max score uses k-1 LARGEST cuts. Min score uses k-1 SMALLEST cuts.
    Diff = sum of top (k-1) cuts - sum of bottom (k-1) cuts.

    1. Compute cuts = [w[i] + w[i+1] for i in 0..n-2].
    2. Sort cuts.
    3. diff = sum(cuts[-(k-1):]) - sum(cuts[:k-1]).

    Time:  O(n log n)
    Space: O(n)
    """
    n = len(weights)
    cuts = sorted(weights[i] + weights[i + 1] for i in range(n - 1))
    return sum(cuts[-(k - 1):]) - sum(cuts[:k - 1])


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the difference between max and min scores of distributing
n marbles into k bags."

Key Insight:
"CRUCIAL: Score = sum(weights) + sum of (k-1) cut positions.
- When I split at positions p_1 < p_2 < ... < p_{k-1}, the score is:
  weights[0] + weights[p_1+1] + weights[p_2+1] + ... + weights[n-1]
            + weights[p_1] + weights[p_2] + ... + weights[p_{k-1}]
  Wait, simpler: each split contributes (left_end + right_start) = w[i] + w[i+1].
- So Score = total_weights + sum of k-1 cuts.
- total_weights is CONSTANT regardless of split.
- To MAXIMIZE: pick k-1 LARGEST cuts.
- To MINIMIZE: pick k-1 SMALLEST cuts.
- diff = sum(top k-1 cuts) - sum(bottom k-1 cuts).

Algorithm:
1. Compute cuts = [w[i] + w[i+1] for i in 0..n-2]. (n-1 cuts.)
2. Sort cuts.
3. diff = sum(cuts[-(k-1):]) - sum(cuts[:k-1]).

Edge Cases:
- k = 1: only one bag, no cuts. Score = w[0] + w[n-1]. diff = 0.
- k = n: each marble is its own bag. Score = 2 * sum(weights). diff = 0.
- n = 1: impossible to split. Return 0.

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| Sort     | O(nlogn| O(n)   |
|          | )      |        |
| Heap     | O(nlogk| O(k)   |
|          | )      |        |
| DP brute | O(C(n-1| O(n*k) |
|          | ,k-1)) |        |
+----------+--------+--------+

KEY TRICK:
Score = sum(weights) + sum of cut values. Cut at position i contributes
w[i] + w[i+1]. Max score = largest k-1 cuts. Min score = smallest k-1 cuts.

RELATED PROBLEMS:
- Partition Array for Maximum Sum (LC 1043): similar partition DP.
- Largest Sum of Averages (LC 813): partition into k groups.
- Split Array Largest Sum (LC 410): minimize max subarray sum.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Sort+top/bottom (BEST)", put_marbles_1),
        ("Way 2: Sort+manual sum", put_marbles_2),
        ("Way 3: Heapq", put_marbles_3),
        ("Way 4: DP brute", put_marbles_4),
        ("Way 5: Sort desc", put_marbles_5),
        ("Way 6: Bisect", put_marbles_6),
        ("Way 7: Partial heap", put_marbles_7),
        ("Way 8: Sort+ends", put_marbles_8),
        ("Way 9: Accumulate", put_marbles_9),
        ("Way 10: Class OOP", put_marbles_10),
        ("Way 11: Sort desc slice", put_marbles_11),
        ("Way 12: Numpy", put_marbles_12),
        ("Way 13: One-liner", put_marbles_13),
        ("Way 14: Reduce", put_marbles_14),
        ("Way 15: Map+sum", put_marbles_15),
        ("Way 16: Manual extract", put_marbles_16),
        ("Way 17: Zip", put_marbles_17),
        ("Way 18: Statistics", put_marbles_18),
        ("Way 19: Prefix sums", put_marbles_19),
        ("Way 20: Final cleanest", put_marbles_20),
    ]

    test_cases = [
        # (weights, k, expected)
        ([1, 3, 5, 1], 2, 4),
        ([1, 3], 2, 0),
        ([1], 1, 0),
        ([1, 2, 3, 4, 5], 5, 0),  # each marble its own bag
        ([1, 2, 3, 4, 5], 1, 0),  # one bag, no cuts
        ([10, 14, 12, 1, 5, 4], 3, 35),
        # Cuts: 24, 26, 13, 6, 9. Sorted: 6, 9, 13, 24, 26.
        # k-1 = 2. min = 6+9 = 15. max = 26+24 = 50. diff = 35. Wait...
        # Let me recompute. weights=[10,14,12,1,5,4]. cuts = [10+14, 14+12, 12+1, 1+5, 5+4] = [24, 26, 13, 6, 9].
        # Sorted: [6, 9, 13, 24, 26].
        # k=3, k-1=2. min sum = 6+9=15. max sum = 24+26=50. diff=35.
        # Hmm, expected is 18. Let me re-verify.
        # Actually let me check: k=3 means 3 bags, 2 splits.
        # Splits (cuts at positions p1<p2, 0-indexed in cuts array):
        # (0,1): cuts = 24+26 = 50. Score = total + 50 = 46 + 50 = 96.
        # (0,2): 24+13 = 37. Score = 46+37 = 83.
        # (0,3): 24+6 = 30. Score = 46+30 = 76.
        # (0,4): 24+9 = 33. Score = 79.
        # (1,2): 26+13 = 39. Score = 85.
        # (1,3): 26+6 = 32. Score = 78.
        # (1,4): 26+9 = 35. Score = 81.
        # (2,3): 13+6 = 19. Score = 65.
        # (2,4): 13+9 = 22. Score = 68.
        # (3,4): 6+9 = 15. Score = 61.
        # Max = 96 (cuts 0,1 = 24, 26). Min = 61 (cuts 3,4 = 6, 9). Diff = 35.
        # Hmm expected was 18 but my calculation says 35.
        # Let me check the formula. Score = w[0] + w[n-1] + sum of bag boundaries.
        # Bag boundaries: for each bag, w[start] + w[end] (start and end inclusive).
        # If we split at i, bag i+1 starts at i+1. So bag's last is i, next bag's first is i+1.
        # Sum of (start + end) for each bag = sum of all starts + sum of all ends = w[0] + w[n-1] + (sum of interior starts and ends)
        # Actually simpler: each cut contributes w[i] + w[i+1] = both endpoints.
        # Total score = sum of all w[i] (each marble counted in 2 bags = its own bag's start AND previous bag's end) = 2 * sum(weights).
        # Wait no, w[i] is in exactly 2 bags (unless i=0 or i=n-1).
        # w[0] is start of first bag. w[n-1] is end of last bag. w[i] for 0<i<n-1 is end of one bag and start of next.
        # So each w[i] for 0<i<n-1 contributes 2 to score. w[0] and w[n-1] contribute 1 each.
        # Total = w[0] + w[n-1] + 2 * sum(w[1..n-2]) = 2*sum(weights) - w[0] - w[n-1].
        # Hmm that's interesting. Let me re-derive.
        # For cuts at positions i_1 < i_2 < ... < i_{k-1}:
        # Bags: [0..i_1], [i_1+1..i_2], ..., [i_{k-1}+1..n-1]
        # Score = (w[0]+w[i_1]) + (w[i_1+1]+w[i_2]) + ... + (w[i_{k-1}+1]+w[n-1])
        #      = w[0] + w[n-1] + (w[i_1]+w[i_1+1]) + (w[i_2]+w[i_2+1]) + ...
        #      = w[0] + w[n-1] + sum of (w[i_j]+w[i_j+1])
        # Note: w[0] and w[n-1] are FIXED (not affected by cuts).
        # cuts_j = w[i_j] + w[i_j+1] for each split.
        # So Score = w[0] + w[n-1] + sum(cuts).
        # DIFFERENCE max_score - min_score = max(sum of cuts) - min(sum of cuts)
        #                          = sum of top (k-1) cuts - sum of bottom (k-1) cuts.
        # Note: cuts is computed from w[i]+w[i+1] for ALL adjacent pairs.
        # So cuts = [10+14, 14+12, 12+1, 1+5, 5+4] = [24, 26, 13, 6, 9]. Sorted: [6, 9, 13, 24, 26].
        # k-1 = 2. Top 2 = 24+26 = 50. Bottom 2 = 6+9 = 15. Diff = 35.
        # So expected should be 35, not 18. Let me change expected.
        ([10, 14, 12, 1, 5, 4], 3, 35),
        # Verify: cuts sum = 24+26+13+6+9 = 78. Total weights = 46. w[0]+w[n-1] = 14. So cuts sum should match.
        # Hmm 78 != 46 + something. Let me recompute.
        # Actually w[0] + w[n-1] = 10+4 = 14. sum(cuts) = 78. Score = 14 + 78 = 92. But sum(weights) = 46.
        # So formula gives: Score = w[0] + w[n-1] + sum(selected cuts).
        # For all 5 cuts selected: 14 + 78 = 92. Verify: 2*sum(weights) - w[0] - w[n-1] = 92 - 14 = 78. Yes!
        # So when all cuts selected (k=n=6), Score = 2*46 - 14 = 78. But we have only 5 cuts (n-1).
        # When k=n, splits = n-1 cuts, all cuts selected. Score = w[0]+w[n-1] + sum(all cuts) = 14 + 78 = 92.
        # Each marble (except endpoints) is in 2 bags, contributes 2 to score. Endpoints contribute 1 each.
        # So total = 2*(sum-w[0]-w[n-1]) + w[0] + w[n-1] = 2*sum - w[0] - w[n-1] = 92-14 = 78.
        # Hmm but score should be 92 according to formula.
        # Wait let me re-verify. With k=6 bags, each marble is its own bag.
        # Each bag contributes w[i]+w[i] = 2*w[i]. Total = 2*sum = 92. OK so my formula gives 92.
        # But the alternate computation 2*sum - w[0] - w[n-1] = 78. Conflict.
        # Let me recompute. With n=6 marbles, k=6 bags:
        # Bags: [0], [1], [2], [3], [4], [5]. Each contributes w[i]+w[i] = 2*w[i].
        # Score = 2*sum(w) = 92.
        # Now apply formula: Score = w[0] + w[n-1] + sum(selected cuts).
        # All 5 cuts selected: cuts = [24, 26, 13, 6, 9]. Sum = 78.
        # Score = 14 + 78 = 92. ✓
        # Alternative formula: Score = w[0] + w[n-1] + sum(cuts) = sum of all bag start-ends.
        # Let's check: bag [0]: start=end=w[0]=10. Bag [1]: start=end=w[1]=14. ... Bag [5]: start=end=w[5]=4.
        # Total = 2*(10+14+12+1+5+4) = 2*46 = 92. ✓
        # Great. So formula Score = w[0] + w[n-1] + sum(selected cuts) is correct.
        # Difference = sum(top k-1 cuts) - sum(bottom k-1 cuts).
        # For [10,14,12,1,5,4], k=3, diff = (24+26) - (6+9) = 50-15 = 35.
        ([1, 4, 2, 5, 3], 2, 3),
        # Cuts: 5, 6, 7, 8. Sorted same. k-1=1. Top - bottom = 8-5 = 3.
        # Hmm I computed 4. Let me recompute.
        # weights = [1, 4, 2, 5, 3]. Adjacent sums: 1+4=5, 4+2=6, 2+5=7, 5+3=8. Cuts = [5,6,7,8].
        # Sorted: [5,6,7,8]. k-1=1. top = 8, bottom = 5. diff = 3.
        # So expected is 3 not 4.
        ([2, 2, 2, 2, 2], 2, 0),  # all cuts same
        ([1, 2], 2, 0),  # only cut: 3
        ([1, 2, 3], 2, 2),  # cuts = [3, 5]. k-1=1. top-bottom = 5-3 = 2.
        # Hmm. Let me check.
        # weights = [1,2,3]. cuts = [1+2, 2+3] = [3, 5]. Sorted: [3, 5].
        # k=2, k-1=1. top = 5, bottom = 3. diff = 2.
        # So expected is 2.
        ([1, 2, 3], 2, 2),
        ([1, 2, 3, 4], 2, 4),  # cuts=[3,5,7], sorted. top-bottom = 7-3 = 4.
        # Wait, cuts = [1+2, 2+3, 3+4] = [3, 5, 7]. k-1=1. top-bottom = 7-3 = 4.
        # So expected is 4.
        ([1, 2, 3, 4], 2, 4),
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
                result = func(weights[:], k)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: weights={weights}, k={k}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
