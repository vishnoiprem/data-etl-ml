"""
3Sum - 20 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/3-sum

Given an integer array nums, return all the triplets [nums[i], nums[j], nums[k]]
such that i != j, i != k, and j != k, and nums[i] + nums[j] + nums[k] == 0.
The solution set must not contain duplicate triplets.

KEY INSIGHT:
Sort first so two-pointer can exploit ordering. For each fixed i, find pairs
that sum to -nums[i] using two pointers. Skip duplicates carefully to ensure
uniqueness.

Examples:
    [-1, 0, 1, 2, -1, -4] -> [[-1, -1, 2], [-1, 0, 1]]
    [0, 1, 1] -> []
    [0, 0, 0] -> [[0, 0, 0]]

Constraints:
- 3 <= nums.length <= 3000
- -10^5 <= nums[i] <= 10^5
"""

import copy
import sys

sys.setrecursionlimit(100000)


# ============================================================
# Way 1: Sort + Two-pointer (BEST - Memorize!)
# ============================================================
def three_sum_1(nums):
    """Sort the array. For each i, use two pointers to find pairs that sum
    to -nums[i]. Skip duplicates to ensure unique triplets."""
    nums = sorted(nums)
    n = len(nums)
    result = []
    for i in range(n - 2):
        # Skip duplicate first elements
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        # Early termination: if smallest triplet already > 0, no more answers
        if nums[i] > 0:
            break
        left, right = i + 1, n - 1
        target = -nums[i]
        while left < right:
            s = nums[left] + nums[right]
            if s == target:
                result.append([nums[i], nums[left], nums[right]])
                # Skip duplicates on both sides
                while left < right and nums[left] == nums[left + 1]:
                    left += 1
                while left < right and nums[right] == nums[right - 1]:
                    right -= 1
                left += 1
                right -= 1
            elif s < target:
                left += 1
            else:
                right -= 1
    return result


# ============================================================
# Way 2: Hash set per fixed i
# ============================================================
def three_sum_2(nums):
    """For each pair (i, j), check if -(nums[i]+nums[j]) is in a set of
    seen values from previous iterations. Track triplets to avoid duplicates."""
    nums = sorted(nums)
    n = len(nums)
    result = set()
    for i in range(n - 2):
        seen = set()
        for j in range(i + 1, n):
            complement = -(nums[i] + nums[j])
            if complement in seen:
                triplet = (nums[i], nums[j], complement)
                result.add(triplet)
            seen.add(nums[j])
    return [list(t) for t in result]


# ============================================================
# Way 3: Brute force triple loop
# ============================================================
def three_sum_3(nums):
    """Triple nested loop, deduplicate via set."""
    n = len(nums)
    result = set()
    for i in range(n - 2):
        for j in range(i + 1, n - 1):
            for k in range(j + 1, n):
                if nums[i] + nums[j] + nums[k] == 0:
                    triplet = tuple(sorted([nums[i], nums[j], nums[k]]))
                    result.add(triplet)
    return [list(t) for t in result]


# ============================================================
# Way 4: Hash map of value -> list of indices
# ============================================================
def three_sum_4(nums):
    """Use a hash map. For each (i, j), find k such that nums[k] = -(nums[i]+nums[j]).
    Track used indices to avoid duplicates."""
    n = len(nums)
    result = set()
    for i in range(n - 2):
        for j in range(i + 1, n - 1):
            s = nums[i] + nums[j]
            for k in range(j + 1, n):
                if nums[k] == -s:
                    triplet = tuple(sorted([nums[i], nums[j], nums[k]]))
                    result.add(triplet)
    return [list(t) for t in result]


# ============================================================
# Way 5: Two-pointer with bsearch for third
# ============================================================
def three_sum_5(nums):
    """For each pair (i, j), binary search for -sum in remaining."""
    import bisect
    nums = sorted(nums)
    n = len(nums)
    result = []
    for i in range(n - 2):
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        if nums[i] > 0:
            break
        for j in range(i + 1, n - 1):
            if j > i + 1 and nums[j] == nums[j - 1]:
                continue
            target = -(nums[i] + nums[j])
            k = bisect.bisect_left(nums, target, j + 1, n)
            if k < n and nums[k] == target:
                result.append([nums[i], nums[j], nums[k]])
    return result


# ============================================================
# Way 6: No-sort with deduplication via indices
# ============================================================
def three_sum_6(nums):
    """Brute force with index-based dedup. No sort."""
    n = len(nums)
    triplets = set()
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                if nums[i] + nums[j] + nums[k] == 0:
                    triplets.add(tuple(sorted([nums[i], nums[j], nums[k]])))
    return [list(t) for t in triplets]


# ============================================================
# Way 7: Two-pointer iterative with skip-block
# ============================================================
def three_sum_7(nums):
    """Same as Way 1 but consolidated skip logic for clarity."""
    nums = sorted(nums)
    n = len(nums)
    result = []
    for i in range(n - 2):
        if nums[i] > 0:
            break
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        left, right = i + 1, n - 1
        while left < right:
            s = nums[left] + nums[right]
            if s == -nums[i]:
                result.append([nums[i], nums[left], nums[right]])
                lv, rv = nums[left], nums[right]
                while left < right and nums[left] == lv:
                    left += 1
                while left < right and nums[right] == rv:
                    right -= 1
            elif s < -nums[i]:
                left += 1
            else:
                right -= 1
    return result


# ============================================================
# Way 8: numpy vectorized (conceptual)
# ============================================================
def three_sum_8(nums):
    """Use numpy to vectorize the inner two-pointer step where possible.
    Still requires loop over i in practice, but uses vectorized inner ops."""
    try:
        import numpy as np
        arr = np.array(sorted(nums))
    except ImportError:
        return three_sum_1(nums)
    n = len(arr)
    result = []
    for i in range(n - 2):
        if arr[i] > 0:
            break
        if i > 0 and arr[i] == arr[i - 1]:
            continue
        target = -arr[i]
        left, right = i + 1, n - 1
        while left < right:
            s = int(arr[left]) + int(arr[right])
            if s == target:
                result.append([int(arr[i]), int(arr[left]), int(arr[right])])
                lv, rv = int(arr[left]), int(arr[right])
                while left < right and arr[left] == lv:
                    left += 1
                while left < right and arr[right] == rv:
                    right -= 1
            elif s < target:
                left += 1
            else:
                right -= 1
    return result


# ============================================================
# Way 9: Class-based
# ============================================================
class ThreeSum_9:
    def __init__(self, nums):
        self.nums = nums

    def solve(self):
        nums = sorted(self.nums)
        n = len(nums)
        result = []
        for i in range(n - 2):
            if i > 0 and nums[i] == nums[i - 1]:
                continue
            if nums[i] > 0:
                break
            left, right = i + 1, n - 1
            while left < right:
                s = nums[left] + nums[right]
                if s == -nums[i]:
                    result.append([nums[i], nums[left], nums[right]])
                    while left < right and nums[left] == nums[left + 1]:
                        left += 1
                    while left < right and nums[right] == nums[right - 1]:
                        right -= 1
                    left += 1
                    right -= 1
                elif s < -nums[i]:
                    left += 1
                else:
                    right -= 1
        return result


def three_sum_9(nums):
    return ThreeSum_9(nums).solve()


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def three_sum_10(nums):
    """
    THE ONE TO MEMORIZE.

    1. Sort.
    2. Fix i; if nums[i] > 0, break.
    3. Skip duplicate i.
    4. Two-pointer search for -nums[i] in nums[i+1:].
    5. On match, skip duplicate left and right.

    Time:  O(n^2)
    Space: O(1) extra (excluding output and sort).
    """
    nums = sorted(nums)
    n = len(nums)
    result = []
    for i in range(n - 2):
        if nums[i] > 0:
            break
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        left, right = i + 1, n - 1
        target = -nums[i]
        while left < right:
            s = nums[left] + nums[right]
            if s == target:
                result.append([nums[i], nums[left], nums[right]])
                while left < right and nums[left] == nums[left + 1]:
                    left += 1
                while left < right and nums[right] == nums[right - 1]:
                    right -= 1
                left += 1
                right -= 1
            elif s < target:
                left += 1
            else:
                right -= 1
    return result


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find all unique triplets in an array that sum to zero."

Key Insight:
"After sorting, for each fixed nums[i], the problem reduces to 2-Sum:
find a pair that sums to -nums[i]. I can solve that with two pointers
because the array is sorted. Skip duplicates to avoid repeated triplets."

Algorithm:
1. Sort the array.
2. For i in [0, n-2]:
   a. If nums[i] > 0, break (smallest possible sum is positive).
   b. Skip if nums[i] == nums[i-1] (duplicate first element).
   c. left = i+1, right = n-1; target = -nums[i].
   d. While left < right:
      - sum = nums[left] + nums[right].
      - If sum == target: record triplet; skip dup left and right; advance both.
      - If sum < target: left += 1.
      - If sum > target: right -= 1.

Edge Cases:
- All zeros: [0, 0, 0] -> [[0, 0, 0]].
- No valid triplet: [].
- All same positive: [] (early break).
- Mix with negatives and positives.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Sort+2ptr | O(n^2) | O(1)   |
| Hash      | O(n^2) | O(n)   |
| Brute     | O(n^3) | O(n)   |
+-----------+--------+--------+

KEY TRICK:
Three dedup checks are needed:
1. Skip duplicate i (across outer loop).
2. Skip duplicate left (after match).
3. Skip duplicate right (after match).

RELATED PROBLEMS:
- 3Sum Closest (LC 16): find closest sum.
- 4Sum (LC 18): extend to quadruplets.
- Two Sum (LC 1): base problem.
- Two Sum II (LC 167): sorted input.
"""


# ============================================================
# Solutions 11-20 (additional approaches)
# ============================================================


# Solution 11: itertools combinations + set
def three_sum_11(nums):
    from itertools import combinations
    seen = set()
    result = []
    for combo in combinations(nums, 3):
        if sum(combo) == 0:
            key = tuple(sorted(combo))
            if key not in seen:
                seen.add(key)
                result.append(list(key))
    return result


# Solution 12: Sort + binary search for third
def three_sum_12(nums):
    nums = sorted(nums)
    n = len(nums)
    result = []
    for i in range(n - 2):
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        for j in range(i + 1, n - 1):
            if j > i + 1 and nums[j] == nums[j - 1]:
                continue
            target = -(nums[i] + nums[j])
            import bisect
            lo = bisect.bisect_left(nums, target, j + 1, n)
            if lo < n and nums[lo] == target:
                result.append([nums[i], nums[j], nums[lo]])
    return result


# Solution 13: Dictionary + two-pointer (one fixed)
def three_sum_13(nums):
    nums = sorted(nums)
    n = len(nums)
    result = []
    for i in range(n - 2):
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        seen = set()
        for j in range(i + 1, n):
            complement = -(nums[i] + nums[j])
            if complement in seen:
                result.append([nums[i], complement, nums[j]])
                # Skip dup for j
                while j + 1 < n and nums[j] == nums[j + 1]:
                    j += 1
            seen.add(nums[j])
    return result


# Solution 14: Recursive general k-sum specialized to k=3
def three_sum_14(nums):
    nums = sorted(nums)
    result = []
    n = len(nums)

    def ksum(start, target, k, path):
        if k == 2:
            lo, hi = start, n - 1
            while lo < hi:
                s = nums[lo] + nums[hi]
                if s == target:
                    result.append(path + [nums[lo], nums[hi]])
                    lo += 1
                    while lo < hi and nums[lo] == nums[lo - 1]:
                        lo += 1
                    hi -= 1
                    while lo < hi and nums[hi] == nums[hi + 1]:
                        hi -= 1
                elif s < target:
                    lo += 1
                else:
                    hi -= 1
            return
        for i in range(start, n - k + 1):
            if i > start and nums[i] == nums[i - 1]:
                continue
            ksum(i + 1, target - nums[i], k - 1, path + [nums[i]])
    ksum(0, 0, 3, [])
    return result


# Solution 15: Use Counter (multiplicities)
def three_sum_15(nums):
    from collections import Counter
    counter = Counter(nums)
    uniq = list(counter.keys())
    result = []
    uniq.sort()
    n = len(uniq)
    for i in range(n):
        x = uniq[i]
        # Two distinct values y != z with y + z = -x
        for j in range(i, n):
            y = uniq[j]
            z = -x - y
            if z < y:
                continue
            if z not in counter:
                continue
            # Check multiplicities
            triplet = [x, y, z]
            need = Counter(triplet)
            if all(counter[k] >= need[k] for k in need):
                if not (len(set(triplet)) < 3 and any(need[k] > counter[k] for k in need)):
                    # Avoid duplicate: enforce x <= y <= z (we already enforce y <= z, plus i <= j)
                    if i < j or (i == j and y != z) or (i == j and y == z and counter[y] >= 2):
                        # ensure distinct indices: at least we have enough multiplicities
                        result.append(triplet)
    # Deduplicate
    out = []
    seen = set()
    for t in result:
        key = tuple(sorted(t))
        if key not in seen:
            seen.add(key)
            out.append(t)
    return out


# Solution 16: Brute force O(n^3) with dup skip via sort
def three_sum_16(nums):
    nums = sorted(nums)
    n = len(nums)
    result = []
    for i in range(n - 2):
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        for j in range(i + 1, n - 1):
            if j > i + 1 and nums[j] == nums[j - 1]:
                continue
            for k in range(j + 1, n):
                if k > j + 1 and nums[k] == nums[k - 1]:
                    continue
                if nums[i] + nums[j] + nums[k] == 0:
                    result.append([nums[i], nums[j], nums[k]])
    return result


# Solution 17: Two-pointer with explicit pointer advancement logging
def three_sum_17(nums):
    nums = sorted(nums)
    n = len(nums)
    result = []
    for i in range(n - 2):
        if nums[i] > 0:
            break
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        lo, hi = i + 1, n - 1
        while lo < hi:
            s = nums[i] + nums[lo] + nums[hi]
            if s == 0:
                result.append([nums[i], nums[lo], nums[hi]])
                lo += 1
                hi -= 1
                while lo < hi and nums[lo] == nums[lo - 1]:
                    lo += 1
                while lo < hi and nums[hi] == nums[hi + 1]:
                    hi -= 1
            elif s < 0:
                lo += 1
            else:
                hi -= 1
    return result


# Solution 18: Using a dict mapping value to list of indices
def three_sum_18(nums):
    index_map = {}
    for i, v in enumerate(nums):
        index_map.setdefault(v, []).append(i)
    n = len(nums)
    result = []
    seen = set()
    for i in range(n):
        for j in range(i + 1, n):
            complement = -(nums[i] + nums[j])
            if complement not in index_map:
                continue
            for k in index_map[complement]:
                if k > j:
                    key = tuple(sorted((nums[i], nums[j], nums[k])))
                    if key not in seen:
                        seen.add(key)
                        result.append(list(key))
    return result


# Solution 19: Sort + recursion on remaining
def three_sum_19(nums):
    nums = sorted(nums)
    n = len(nums)
    result = []

    def rec(start, target, path):
        if len(path) == 3:
            if target == 0:
                result.append(path[:])
            return
        for i in range(start, n):
            if i > start and nums[i] == nums[i - 1]:
                continue
            path.append(nums[i])
            rec(i + 1, target - nums[i], path)
            path.pop()
    rec(0, 0, [])
    return result


# Solution 20: Group by value, iterate distinct combos
def three_sum_20(nums):
    from itertools import combinations_with_replacement
    nums = sorted(nums)
    uniq = sorted(set(nums))
    result = []
    for combo in combinations_with_replacement(uniq, 3):
        if sum(combo) == 0:
            # Verify multiplicities exist
            counts = {}
            for c in combo:
                counts[c] = counts.get(c, 0) + 1
            if all(nums.count(c) >= counts[c] for c in counts):
                result.append(list(combo))
    return result


# ============================================================
# TEST CASES
# ============================================================
def _normalize(triplets):
    """Sort each triplet and the list for comparison."""
    return sorted([sorted(t) for t in triplets])


def run_tests():
    test_cases = [
        ([-1, 0, 1, 2, -1, -4], [[-1, -1, 2], [-1, 0, 1]], "Standard"),
        ([0, 1, 1], [], "No valid triplet"),
        ([0, 0, 0], [[0, 0, 0]], "All zeros"),
        ([1, 2, -2, -1], [], "No triplet"),
        ([1, 1, -2, 2], [[-2, 1, 1]], "Mixed small"),
        ([-1, 0, 1, 2, -1, -4], [[-1, -1, 2], [-1, 0, 1]], "Mixed dup"),
        ([], [], "Empty input"),
        ([1], [], "Single element"),
        ([1, 2], [], "Two elements"),
        ([-2, 0, 1, 1, 2], [[-2, 0, 2], [-2, 1, 1]], "Multiple triplets"),
        ([-1, 0, 1, 0], [[-1, 0, 1]], "With zero duplicate"),
        ([3, 0, -2, -1, 1, 2], [[-2, -1, 3], [-2, 0, 2], [-1, 0, 1]], "Many triplets"),
    ]

    implementations = [
        ("Way 1: Sort+2ptr (BEST)", three_sum_1),
        ("Way 2: Hash set", three_sum_2),
        ("Way 3: Brute triple loop", three_sum_3),
        ("Way 4: Hash search", three_sum_4),
        ("Way 5: 2ptr+bsearch", three_sum_5),
        ("Way 6: Brute no-sort", three_sum_6),
        ("Way 7: 2ptr skip-block", three_sum_7),
        ("Way 8: numpy", three_sum_8),
        ("Way 9: Class-based", three_sum_9),
        ("Way 10: Final cleanest", three_sum_10),
        ("Way 11: combinations+set", three_sum_11),
        ("Way 12: 2ptr+bsearch", three_sum_12),
        ("Way 13: dict+2ptr", three_sum_13),
        ("Way 14: recursive k-sum", three_sum_14),
        ("Way 15: Counter multiplicities", three_sum_15),
        ("Way 16: brute O(n^3) sorted", three_sum_16),
        ("Way 17: explicit skip logging", three_sum_17),
        ("Way 18: value-to-indices map", three_sum_18),
        ("Way 19: recursive general", three_sum_19),
        ("Way 20: combinations_with_replacement", three_sum_20),
    ]

    for name, fn in implementations:
        passed = 0
        failed = 0
        for nums, expected, desc in test_cases:
            try:
                nums_copy = copy.deepcopy(nums)
                result = fn(nums_copy)
                if _normalize(result) == _normalize(expected):
                    passed += 1
                else:
                    failed += 1
                    print(f"  FAIL [{name}] {desc}: nums={nums} expected={expected} got={result}")
            except Exception as e:
                failed += 1
                print(f"  ERROR [{name}] {desc}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)
    print(HOW_TO_THINK)


if __name__ == "__main__":
    run_tests()
