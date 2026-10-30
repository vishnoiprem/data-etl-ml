"""
Longest Subsequence With Limited Sum
Easy | 15 min

Given nums[] and queries[], for each query, find max number of elements
from nums forming a subsequence with sum <= query.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/longest-subsequence-with-limited-sum

Examples:
    nums=[4,5,2,1], queries=[3,10,21] -> [2,3,4]
    nums=[2,3,4,5], queries=[1] -> [0]

Constraints:
- 1 <= n, m <= 10^3
- 1 <= nums[i], queries[i] <= 10^5

KEY INSIGHT: Sort nums ascending. Greedy pick smallest first.
Prefix sums + binary search each query: bisect_right(prefix, q) - 1.
"""


import bisect


# =============================================================================
# WAY 1: Sort + prefix + BS (BEST - Memorize!)
# =============================================================================
def answer_queries_1(nums, queries):
    """Sort. Prefix sums. For each query, BS."""
    a = sorted(nums)
    n = len(a)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + a[i]
    return [bisect.bisect_right(prefix, q) - 1 for q in queries]


# =============================================================================
# WAY 2: Sort + manual BS
# =============================================================================
def answer_queries_2(nums, queries):
    a = sorted(nums)
    n = len(a)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + a[i]
    result = []
    for q in queries:
        lo, hi = 0, n
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if prefix[mid] <= q:
                lo = mid
            else:
                hi = mid - 1
        result.append(lo)
    return result


# =============================================================================
# WAY 3: Sort + iterate per query
# =============================================================================
def answer_queries_3(nums, queries):
    a = sorted(nums)
    result = []
    for q in queries:
        s = 0
        count = 0
        for x in a:
            if s + x > q:
                break
            s += x
            count += 1
        result.append(count)
    return result


# =============================================================================
# WAY 4: Brute force precompute
# =============================================================================
def answer_queries_4(nums, queries):
    a = sorted(nums)
    n = len(a)
    min_sums = [0] * (n + 1)
    for k in range(1, n + 1):
        min_sums[k] = sum(a[:k])
    result = []
    for q in queries:
        max_k = 0
        for k in range(1, n + 1):
            if min_sums[k] <= q:
                max_k = k
        result.append(max_k)
    return result


# =============================================================================
# WAY 5: With prefix sums on the fly
# =============================================================================
def answer_queries_5(nums, queries):
    a = sorted(nums)
    result = []
    for q in queries:
        s = 0
        count = 0
        for x in a:
            if s + x > q:
                break
            s += x
            count += 1
        result.append(count)
    return result


# =============================================================================
# WAY 6: Class OOP
# =============================================================================
class QueryAnswerer:
    def __init__(self, nums):
        self.a = sorted(nums)
        self.n = len(self.a)
        self.prefix = [0] * (self.n + 1)
        for i in range(self.n):
            self.prefix[i + 1] = self.prefix[i] + self.a[i]

    def answer(self, q):
        idx = bisect.bisect_right(self.prefix, q)
        return idx - 1

    def answer_queries(self, queries):
        return [self.answer(q) for q in queries]


def answer_queries_6(nums, queries):
    return QueryAnswerer(nums).answer_queries(queries)


# =============================================================================
# WAY 7: Numpy
# =============================================================================
def answer_queries_7(nums, queries):
    import numpy as np
    a = np.sort(np.array(nums))
    prefix = np.concatenate([[0], np.cumsum(a)])
    q_arr = np.array(queries)
    idxs = np.searchsorted(prefix, q_arr, side='right')
    return (idxs - 1).tolist()


# =============================================================================
# WAY 8: Sort + bisect_left
# =============================================================================
def answer_queries_8(nums, queries):
    a = sorted(nums)
    n = len(a)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + a[i]
    result = []
    for q in queries:
        idx = bisect.bisect_left(prefix, q + 1)
        result.append(idx - 1 if idx > 0 else 0)
    return result


# =============================================================================
# WAY 9: Recursive BS
# =============================================================================
def answer_queries_9(nums, queries):
    a = sorted(nums)
    n = len(a)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + a[i]

    def find_count(q):
        def search(lo, hi):
            if lo >= hi:
                return lo
            mid = (lo + hi + 1) // 2
            if prefix[mid] <= q:
                return search(mid, hi)
            return search(lo, mid - 1)
        return search(0, n)

    return [find_count(q) for q in queries]


# =============================================================================
# WAY 10: Sort + iterate all sums
# =============================================================================
def answer_queries_10(nums, queries):
    a = sorted(nums)
    n = len(a)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + a[i]
    result = []
    for q in queries:
        k = 0
        for i in range(n + 1):
            if prefix[i] <= q:
                k = i
            else:
                break
        result.append(k)
    return result


# =============================================================================
# WAY 11: Sort + bisect with index
# =============================================================================
def answer_queries_11(nums, queries):
    a = sorted(nums)
    n = len(a)
    prefix = []
    s = 0
    for x in a:
        s += x
        prefix.append(s)
    result = []
    for q in queries:
        idx = bisect.bisect_right(prefix, q)
        result.append(idx)
    return result


# =============================================================================
# WAY 12: Generator
# =============================================================================
def answer_queries_12(nums, queries):
    a = sorted(nums)

    def gen_prefix():
        s = 0
        for x in a:
            s += x
            yield s

    prefix = [0] + list(gen_prefix())
    return [bisect.bisect_right(prefix, q) - 1 for q in queries]


# =============================================================================
# WAY 13: One-liner
# =============================================================================
def answer_queries_13(nums, queries):
    a = sorted(nums)
    p = [0]
    for x in a:
        p.append(p[-1] + x)
    return [bisect.bisect_right(p, q) - 1 for q in queries]


# =============================================================================
# WAY 14: Helper function
# =============================================================================
def answer_queries_14(nums, queries):
    a = sorted(nums)
    prefix = [0]
    for x in a:
        prefix.append(prefix[-1] + x)

    def count_for(q):
        return bisect.bisect_right(prefix, q) - 1

    return [count_for(q) for q in queries]


# =============================================================================
# WAY 15: itertools.accumulate
# =============================================================================
def answer_queries_15(nums, queries):
    import itertools
    a = sorted(nums)
    prefix = [0] + list(itertools.accumulate(a))
    return [bisect.bisect_right(prefix, q) - 1 for q in queries]


# =============================================================================
# WAY 16: Sort + explicit loop
# =============================================================================
def answer_queries_16(nums, queries):
    a = sorted(nums)
    n = len(a)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + a[i]
    result = []
    for q in queries:
        lo, hi = 0, n
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if prefix[mid] <= q:
                lo = mid
            else:
                hi = mid - 1
        result.append(lo)
    return result


# =============================================================================
# WAY 17: bisect + accumulate
# =============================================================================
def answer_queries_17(nums, queries):
    a = sorted(nums)
    prefix = list(__import__('itertools').accumulate(a, initial=0))
    return [bisect.bisect_right(prefix, q) - 1 for q in queries]


# =============================================================================
# WAY 18: cumsum + bisect
# =============================================================================
def answer_queries_18(nums, queries):
    a = sorted(nums)
    cumsum = []
    s = 0
    for x in a:
        s += x
        cumsum.append(s)
    result = []
    for q in queries:
        idx = bisect.bisect_right(cumsum, q)
        result.append(idx)
    return result


# =============================================================================
# WAY 19: Lambda map
# =============================================================================
def answer_queries_19(nums, queries):
    a = sorted(nums)
    prefix = [0]
    for x in a:
        prefix.append(prefix[-1] + x)
    return list(map(lambda q: bisect.bisect_right(prefix, q) - 1, queries))


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def answer_queries_20(nums, queries):
    """Sort, prefix sums, bisect_right for each query."""
    a = sorted(nums)
    n = len(a)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + a[i]
    return [bisect.bisect_right(prefix, q) - 1 for q in queries]


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"For each query q, I need to find the maximum number of elements from
nums that can be summed to <= q."

Key Insight:
"To maximize the count for any sum budget, take the SMALLEST elements
first. Sort nums ascending. Compute prefix sums. For query q, find
the largest k where prefix[k] <= q."

Algorithm:
1. Sort nums.
2. Build prefix sum array (with leading 0).
3. For each query q:
   - bisect_right(prefix, q) returns first idx where prefix[idx] > q.
   - Answer = idx - 1.
4. Return list of answers.

Edge Cases:
- Empty nums: 0.
- q < min(nums): 0.
- q >= sum(nums): n.

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| Sort+BS  | O(nlogn| O(n)   |
|          | +mlogn)|        |
| Brute    | O(n*m) | O(1)   |
+----------+--------+--------+

KEY TRICK:
Same as max_count problem. Sort, smallest first, prefix sums + binary
search.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Sort+prefix+bisect (BEST)", answer_queries_1),
        ("Way 2: Manual BS", answer_queries_2),
        ("Way 3: Iterate per query", answer_queries_3),
        ("Way 4: Brute min sums", answer_queries_4),
        ("Way 5: Prefix on fly", answer_queries_5),
        ("Way 6: Class OOP", answer_queries_6),
        ("Way 7: Numpy", answer_queries_7),
        ("Way 8: bisect_left", answer_queries_8),
        ("Way 9: Recursive BS", answer_queries_9),
        ("Way 10: Iterate all sums", answer_queries_10),
        ("Way 11: Bisect index", answer_queries_11),
        ("Way 12: Generator", answer_queries_12),
        ("Way 13: One-liner", answer_queries_13),
        ("Way 14: Helper fn", answer_queries_14),
        ("Way 15: itertools.accumulate", answer_queries_15),
        ("Way 16: Explicit loop", answer_queries_16),
        ("Way 17: itertools accumulate v2", answer_queries_17),
        ("Way 18: Bisect direct", answer_queries_18),
        ("Way 19: Lambda map", answer_queries_19),
        ("Way 20: Final cleanest", answer_queries_20),
    ]

    test_cases = [
        ([4, 5, 2, 1], [3, 10, 21], [2, 3, 4]),
        ([2, 3, 4, 5], [1], [0]),
        ([1], [1, 2, 3], [1, 1, 1]),
        ([1, 2, 3], [6], [3]),
        ([1, 2, 3], [5], [2]),
        ([5, 5, 5], [10], [2]),
        ([5, 5, 5], [15], [3]),
        ([5, 5, 5], [4], [0]),
        ([1, 2, 3, 4, 5], [15], [5]),
        ([1, 2, 3, 4, 5], [1], [1]),
        ([1, 2, 3, 4, 5], [7], [3]),
    ]

    print("=" * 70)
    print("LONGEST SUBSEQUENCE WITH LIMITED SUM - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/longest-subsequence-with-limited-sum")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for nums, queries, expected in test_cases:
            try:
                result = func(nums[:], queries[:])
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: nums={nums}, queries={queries}, expected={expected}, got={result}")
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
