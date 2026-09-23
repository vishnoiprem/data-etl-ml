"""
Rotate Array - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/rotate-array

Given an integer array nums, rotate the array to the right by k steps,
where k is non-negative. The rotation should be done in-place.

KEY INSIGHT:
Triple reverse trick. Reverse the whole array, then reverse the first k
elements, then reverse the remaining n-k elements. Each element ends up
in its rotated position. O(1) extra space.

Examples:
    [1, 2, 3, 4, 5, 6, 7], k=3 -> [5, 6, 7, 1, 2, 3, 4]
    [-1, -100, 3, 99], k=2 -> [3, 99, -1, -100]

Constraints:
- 1 <= nums.length <= 10^5
- -2^31 <= nums[i] <= 2^31 - 1
- 0 <= k <= 10^5
"""

import copy
import sys

sys.setrecursionlimit(100000)


def _reverse(nums, start, end):
    """Reverse nums[start:end+1] in-place."""
    while start < end:
        nums[start], nums[end] = nums[end], nums[start]
        start += 1
        end -= 1


# ============================================================
# Way 1: Triple reverse (BEST - Memorize!)
# ============================================================
def rotate_1(nums, k):
    """Reverse all, reverse first k, reverse rest."""
    n = len(nums)
    if n == 0:
        return
    k = k % n
    if k == 0:
        return
    _reverse(nums, 0, n - 1)
    _reverse(nums, 0, k - 1)
    _reverse(nums, k, n - 1)


# ============================================================
# Way 2: Cyclic replacements
# ============================================================
def rotate_2(nums, k):
    """Place each element at its rotated position via cycle-following."""
    n = len(nums)
    if n == 0:
        return
    k = k % n
    if k == 0:
        return
    start = 0
    count = 0
    while count < n:
        current = start
        prev = nums[start]
        while True:
            nxt = (current + k) % n
            tmp = nums[nxt]
            nums[nxt] = prev
            prev = tmp
            current = nxt
            count += 1
            if start == current:
                break
        start += 1


# ============================================================
# Way 3: Using extra array
# ============================================================
def rotate_3(nums, k):
    """Build a new array, copy back. O(n) space."""
    n = len(nums)
    if n == 0:
        return
    k = k % n
    result = [0] * n
    for i in range(n):
        result[(i + k) % n] = nums[i]
    for i in range(n):
        nums[i] = result[i]


# ============================================================
# Way 4: Slice + concat (in-place mutation of list)
# ============================================================
def rotate_4(nums, k):
    """Use slicing to rotate, then extend back."""
    n = len(nums)
    if n == 0:
        return
    k = k % n
    if k == 0:
        return
    nums[:] = nums[-k:] + nums[:-k]


# ============================================================
# Way 5: Pop from end and prepend (one-by-one)
# ============================================================
def rotate_5(nums, k):
    """Pop k elements from the end and prepend them. O(k*n) time."""
    n = len(nums)
    if n == 0:
        return
    k = k % n
    for _ in range(k):
        nums.insert(0, nums.pop())


# ============================================================
# Way 6: deque rotate
# ============================================================
def rotate_6(nums, k):
    """Use collections.deque.rotate and copy back."""
    from collections import deque
    n = len(nums)
    if n == 0:
        return
    k = k % n
    dq = deque(nums)
    dq.rotate(k)
    for i in range(n):
        nums[i] = dq[i]


# ============================================================
# Way 7: One-by-one right shift
# ============================================================
def rotate_7(nums, k):
    """Shift each element right by one, repeated k times."""
    n = len(nums)
    if n == 0:
        return
    k = k % n
    for _ in range(k):
        prev = nums[-1]
        for i in range(n):
            nums[i], prev = prev, nums[i]


# ============================================================
# Way 8: numpy-style
# ============================================================
def rotate_8(nums, k):
    """Use numpy roll, then copy back to list."""
    n = len(nums)
    if n == 0:
        return
    try:
        import numpy as np
        arr = np.array(nums)
        k = k % len(arr)
        rotated = np.roll(arr, k)
        for i in range(len(nums)):
            nums[i] = int(rotated[i])
    except ImportError:
        rotate_1(nums, k)


# ============================================================
# Way 9: Class-based
# ============================================================
class ArrayRotator_9:
    def __init__(self, nums):
        self.nums = nums

    def rotate(self, k):
        n = len(self.nums)
        if n == 0:
            return
        k = k % n
        if k == 0:
            return
        _reverse(self.nums, 0, n - 1)
        _reverse(self.nums, 0, k - 1)
        _reverse(self.nums, k, n - 1)


def rotate_9(nums, k):
    ArrayRotator_9(nums).rotate(k)


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def rotate_10(nums, k):
    """
    THE ONE TO MEMORIZE.

    1. k = k % n.
    2. Reverse the whole array.
    3. Reverse the first k elements.
    4. Reverse the last n - k elements.

    Time:  O(n)
    Space: O(1) extra.
    """
    n = len(nums)
    if n == 0:
        return
    k %= n
    if k == 0:
        return
    _reverse(nums, 0, n - 1)
    _reverse(nums, 0, k - 1)
    _reverse(nums, k, n - 1)


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to rotate an array to the right by k positions, in-place."

Key Insight:
"Triple reverse trick. Reversing the entire array, then reversing the
first k elements, then reversing the rest, gives the rotated result.
Each element ends up at its new position."

Algorithm:
1. k = k % n  (handle k > n).
2. Reverse nums[0..n-1].
3. Reverse nums[0..k-1].
4. Reverse nums[k..n-1].

Why does it work?
- After step 2: array is reversed.
- After step 3: first k are correctly placed (these should be the
  LAST k of the original, but reversed).
- After step 4: remaining n-k are correctly placed.

Edge Cases:
- k == 0: no rotation needed (early return).
- k == n: equivalent to k == 0.
- k > n: use k % n.
- Empty array: trivial.
- Single element: trivial.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Triple rev| O(n)   | O(1)   |
| Cyclic    | O(n)   | O(1)   |
| Extra arr | O(n)   | O(n)   |
| Pop+ins   | O(k*n) | O(1)   |
+-----------+--------+--------+

KEY TRICK:
The triple reverse works because reversing twice cancels out —
[1,2,3] -> [3,2,1] -> [1,2,3]. By reversing subsegments after a full
reverse, we shift the boundary.

RELATED PROBLEMS:
- Reverse String (LC 344): single reverse.
- Rotate List (LC 61): same idea on linked list.
- Reverse Words in a String (LC 151).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        # (input, k, expected, description)
        ([1, 2, 3, 4, 5, 6, 7], 3, [5, 6, 7, 1, 2, 3, 4], "Standard"),
        ([-1, -100, 3, 99], 2, [3, 99, -1, -100], "With negatives"),
        ([1, 2], 3, [2, 1], "k > n"),
        ([1, 2, 3], 0, [1, 2, 3], "k = 0"),
        ([1], 5, [1], "Single element"),
        ([], 3, [], "Empty"),
        ([1, 2, 3, 4, 5], 5, [1, 2, 3, 4, 5], "k = n"),
        ([1, 2, 3, 4, 5], 1, [5, 1, 2, 3, 4], "k = 1"),
        ([1, 2, 3, 4, 5], 4, [2, 3, 4, 5, 1], "k = n-1"),
        ([1, 2, 3, 4, 5, 6], 2, [5, 6, 1, 2, 3, 4], "Even length"),
        ([1, 2, 3, 4, 5, 6, 7], 7, [1, 2, 3, 4, 5, 6, 7], "Full rotation"),
    ]

    implementations = [
        ("Way 1: Triple reverse (BEST)", rotate_1),
        ("Way 2: Cyclic replacements", rotate_2),
        ("Way 3: Extra array", rotate_3),
        ("Way 4: Slice + concat", rotate_4),
        ("Way 5: Pop + prepend", rotate_5),
        ("Way 6: deque.rotate", rotate_6),
        ("Way 7: One-by-one shift", rotate_7),
        ("Way 8: numpy.roll", rotate_8),
        ("Way 9: Class-based", rotate_9),
        ("Way 10: Final cleanest", rotate_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for nums, k, expected, desc in test_cases:
            try:
                nums_copy = copy.deepcopy(nums)
                fn(nums_copy, k)
                if nums_copy == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: input={nums} k={k} expected={expected} got={nums_copy}")
            except Exception as e:
                failed += 1
                all_pass = False
                print(f"  ERROR [{name}] {desc}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 60)
    print(HOW_TO_THINK)


if __name__ == "__main__":
    run_tests()
