"""
Largest Number - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/largest-number

Given a list of non-negative integers nums, rearrange them to form the largest
possible number. Return as a string.

KEY INSIGHT:
Custom comparator: sort strings such that for two strings a, b, "a + b" > "b + a"
means a comes first. Python's `functools.cmp_to_key` converts this.
Also handle edge case: if max is "0", result is "0".

Examples:
    [10, 2] -> "210"
    [3, 30, 34, 5, 9] -> "9534330"
    [0, 0] -> "0"

Constraints:
- 1 <= nums.length <= 100
- 0 <= nums[i] <= 10^3
"""

import copy
import sys

sys.setrecursionlimit(100000)


# ============================================================
# Way 1: cmp_to_key with custom comparator (BEST - Memorize!)
# ============================================================
def largest_number_1(nums):
    from functools import cmp_to_key

    def compare(x, y):
        if x + y > y + x:
            return -1  # x first
        elif x + y < y + x:
            return 1   # y first
        return 0

    s = list(map(str, nums))
    s.sort(key=cmp_to_key(compare))
    result = ''.join(s)
    return '0' if result[0] == '0' else result


# ============================================================
# Way 2: Sort by x*4 trick (works when nums <= 10^3, length <= 4)
# ============================================================
def largest_number_2(nums):
    s = list(map(str, nums))
    s.sort(key=lambda x: x * 4, reverse=True)
    result = ''.join(s)
    return '0' if result[0] == '0' else result


# ============================================================
# Way 3: Bubble sort with custom comparator
# ============================================================
def largest_number_3(nums):
    s = list(map(str, nums))
    n = len(s)
    for i in range(n):
        for j in range(n - 1 - i):
            if s[j] + s[j + 1] < s[j + 1] + s[j]:
                s[j], s[j + 1] = s[j + 1], s[j]
    result = ''.join(s)
    return '0' if result and result[0] == '0' else result


# ============================================================
# Way 4: Selection sort with custom comparator
# ============================================================
def largest_number_4(nums):
    s = list(map(str, nums))
    n = len(s)
    for i in range(n):
        best_idx = i
        for j in range(i + 1, n):
            if s[j] + s[best_idx] > s[best_idx] + s[j]:
                best_idx = j
        if best_idx != i:
            s[i], s[best_idx] = s[best_idx], s[i]
    result = ''.join(s)
    return '0' if result and result[0] == '0' else result


# ============================================================
# Way 5: Insertion sort with comparator
# ============================================================
def largest_number_5(nums):
    s = list(map(str, nums))
    for i in range(1, len(s)):
        key = s[i]
        j = i - 1
        while j >= 0 and s[j] + key < key + s[j]:
            s[j + 1] = s[j]
            j -= 1
        s[j + 1] = key
    result = ''.join(s)
    return '0' if result[0] == '0' else result


# ============================================================
# Way 6: Heap-based with custom key
# ============================================================
def largest_number_6(nums):
    import heapq
    if not nums:
        return '0'
    s = list(map(str, nums))
    # Heap key: repeat string so longer sorts after shorter same-prefix
    max_len = max(len(x) for x in s)
    target_len = max_len * 12  # divisible by 1, 2, 3, 4
    heap = []
    for x in s:
        repeat = target_len // len(x)
        key_str = x * repeat
        heapq.heappush(heap, (-int(key_str), x))
    out = []
    while heap:
        _, x = heapq.heappop(heap)
        out.append(x)
    result = ''.join(out)
    return '0' if result[0] == '0' else result


# ============================================================
# Way 7: Quicksort with comparator
# ============================================================
def largest_number_7(nums):
    s = list(map(str, nums))

    def quicksort(arr, lo, hi):
        if lo < hi:
            p = partition(arr, lo, hi)
            quicksort(arr, lo, p - 1)
            quicksort(arr, p + 1, hi)

    def partition(arr, lo, hi):
        pivot = arr[hi]
        i = lo - 1
        for j in range(lo, hi):
            if arr[j] + pivot >= pivot + arr[j]:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
        arr[i + 1], arr[hi] = arr[hi], arr[i + 1]
        return i + 1

    if s:
        quicksort(s, 0, len(s) - 1)
    result = ''.join(s)
    if not result or result[0] == '0':
        return '0'
    return result


# ============================================================
# Way 8: Merge sort with comparator
# ============================================================
def largest_number_8(nums):
    s = list(map(str, nums))

    def merge_sort(arr):
        if len(arr) <= 1:
            return arr
        mid = len(arr) // 2
        left = merge_sort(arr[:mid])
        right = merge_sort(arr[mid:])
        return merge(left, right)

    def merge(left, right):
        result = []
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i] + right[j] >= right[j] + left[i]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        result.extend(left[i:])
        result.extend(right[j:])
        return result

    sorted_s = merge_sort(s)
    result = ''.join(sorted_s)
    if not result or result[0] == '0':
        return '0'
    return result


# ============================================================
# Way 9: Class-based
# ============================================================
class LargestNumber_9:
    def __init__(self, nums):
        self.nums = nums

    def compute(self):
        from functools import cmp_to_key

        def compare(x, y):
            if x + y > y + x:
                return -1
            elif x + y < y + x:
                return 1
            return 0

        s = list(map(str, self.nums))
        s.sort(key=cmp_to_key(compare))
        result = ''.join(s)
        if not result or result[0] == '0':
            return '0'
        return result


def largest_number_9(nums):
    return LargestNumber_9(nums).compute()


# ============================================================
# Way 10: Final cleanest
# ============================================================
def largest_number_10(nums):
    from functools import cmp_to_key

    def compare(a, b):
        if a + b > b + a:
            return -1
        if a + b < b + a:
            return 1
        return 0

    s = sorted(map(str, nums), key=cmp_to_key(compare))
    return '0' if not s or s[0] == '0' else ''.join(s)


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([10, 2], "210", "Standard"),
        ([3, 30, 34, 5, 9], "9534330", "LeetCode standard"),
        ([0, 0], "0", "All zeros"),
        ([0], "0", "Single zero"),
        ([1], "1", "Single digit"),
        ([121, 12], "12121", "Equal starts (121 vs 12)"),
        ([12, 121], "12121", "Same test, different order"),
        ([9, 99, 999], "999999", "Cascading lengths"),
        ([830, 8308], "8308830", "Mid-prefix"),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9], "987654321", "All different"),
        ([5, 4, 3, 2, 1], "54321", "Descending"),
        ([1, 2, 3, 4, 5], "54321", "Ascending"),
    ]

    implementations = [
        ("Way 1: cmp_to_key (BEST)", largest_number_1),
        ("Way 2: x*4 trick", largest_number_2),
        ("Way 3: Bubble sort", largest_number_3),
        ("Way 4: Selection sort", largest_number_4),
        ("Way 5: Insertion sort", largest_number_5),
        ("Way 6: Heap-based", largest_number_6),
        ("Way 7: Quicksort", largest_number_7),
        ("Way 8: Merge sort", largest_number_8),
        ("Way 9: Class-based", largest_number_9),
        ("Way 10: Final cleanest", largest_number_10),
    ]

    for name, fn in implementations:
        passed = 0
        failed = 0
        for nums, expected, desc in test_cases:
            try:
                nums_copy = copy.deepcopy(nums)
                result = fn(nums_copy)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    print(f"  FAIL [{name}] {desc}: nums={nums} expected='{expected}' got='{result}'")
            except Exception as e:
                failed += 1
                print(f"  ERROR [{name}] {desc}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    run_tests()
