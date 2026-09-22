"""
Find The Duplicate Number - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/find-the-duplicate-number

Given an array of integers nums containing n+1 integers where each integer
is in the range [1, n] inclusive, there is only one repeated number. Return
this duplicate. The array cannot be modified.

KEY INSIGHT:
Treat the array as a linked list: from index i, go to nums[i]. Because
nums[i] is in [1, n], every "next" is a valid index. The duplicate
creates a cycle. Use Floyd's to find the cycle ENTRY (the duplicate).

Algorithm:
1. Phase 1: Find meeting point inside the cycle.
2. Phase 2: Find cycle entry. Reset one pointer to start; advance both 1
   step at a time; they meet at the cycle entry (the duplicate).

Examples:
    [1, 3, 4, 2, 2] -> 2 (nums[i] in [1, 4]; two indices point to 2)
    [3, 1, 3, 4, 2] -> 3
    [1, 1] -> 1

Constraints:
- 1 <= n <= 10^5
- nums.length == n + 1
- 1 <= nums[i] <= n
- All nums appear exactly once except one which appears twice or more.
"""

import copy
import sys

sys.setrecursionlimit(100000)


# ============================================================
# Way 1: Floyd's cycle detection (BEST - Memorize!)
# ============================================================
def find_duplicate_1(nums):
    """Find cycle entry via Floyd's two-phase algorithm."""
    # Phase 1: Find intersection
    slow = nums[0]
    fast = nums[0]
    while True:
        slow = nums[slow]
        fast = nums[nums[fast]]
        if slow == fast:
            break
    # Phase 2: Find entry to cycle
    slow = nums[0]
    while slow != fast:
        slow = nums[slow]
        fast = nums[fast]
    return slow


# ============================================================
# Way 2: Binary search on count
# ============================================================
def find_duplicate_2(nums):
    """For each candidate count, binary search the value with at least that
    many numbers <= it. The smallest value where count > value is the dup."""
    lo, hi = 1, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        count = sum(1 for x in nums if x <= mid)
        if count > mid:
            hi = mid
        else:
            lo = mid + 1
    return lo


# ============================================================
# Way 3: Mark visited (mutation not allowed, but can use index negation)
# ============================================================
def find_duplicate_3(nums):
    """Negate nums[index] as we visit. The first index whose value is already
    negative is the duplicate. Mutates the array."""
    for x in nums:
        idx = abs(x)
        if nums[idx] < 0:
            return idx
        nums[idx] = -nums[idx]
    return -1


# ============================================================
# Way 4: Hash set
# ============================================================
def find_duplicate_4(nums):
    """Track seen values in a set. The first repeat is the answer."""
    seen = set()
    for x in nums:
        if x in seen:
            return x
        seen.add(x)
    return -1


# ============================================================
# Way 5: Sort and check adjacent (mutation allowed in this version)
# ============================================================
def find_duplicate_5(nums):
    """Sort the array, then check adjacent equal elements."""
    nums = sorted(nums)
    for i in range(1, len(nums)):
        if nums[i] == nums[i - 1]:
            return nums[i]
    return -1


# ============================================================
# Way 6: Counting sort approach
# ============================================================
def find_duplicate_6(nums):
    """Count occurrences; the value with count > 1 is the duplicate."""
    n = len(nums) - 1
    counts = [0] * (n + 1)
    for x in nums:
        counts[x] += 1
        if counts[x] > 1:
            return x
    return -1


# ============================================================
# Way 7: Sum-based (only if single duplicate)
# ============================================================
def find_duplicate_7(nums):
    """n+1 nums in [1, n]; total sum = n*(n+1)/2 + dup."""
    n = len(nums) - 1
    expected = n * (n + 1) // 2
    return sum(nums) - expected


# ============================================================
# Way 8: XOR-based (only for odd-count duplicates)
# ============================================================
def find_duplicate_8(nums):
    """XOR all nums and XOR [1..n]; result is the duplicate (if exactly 2
    occurrences). For repeated >2 times, this fails — kept for educational
    value."""
    result = 0
    for x in nums:
        result ^= x
    for i in range(1, len(nums)):
        result ^= i
    return result


# ============================================================
# Way 9: Class-based
# ============================================================
class DuplicateFinder_9:
    def __init__(self, nums):
        self.nums = nums

    def find(self):
        slow = self.nums[0]
        fast = self.nums[0]
        while True:
            slow = self.nums[slow]
            fast = self.nums[self.nums[fast]]
            if slow == fast:
                break
        slow = self.nums[0]
        while slow != fast:
            slow = self.nums[slow]
            fast = self.nums[fast]
        return slow


def find_duplicate_9(nums):
    return DuplicateFinder_9(nums).find()


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def find_duplicate_10(nums):
    """
    THE ONE TO MEMORIZE.

    Phase 1: Use Floyd's to find a meeting point inside the cycle.
    Phase 2: Reset one pointer; advance both 1 step until they meet at
             cycle entry (the duplicate).

    Time:  O(n)
    Space: O(1)
    """
    slow = nums[0]
    fast = nums[0]
    while True:
        slow = nums[slow]
        fast = nums[nums[fast]]
        if slow == fast:
            break
    slow = nums[0]
    while slow != fast:
        slow = nums[slow]
        fast = nums[fast]
    return slow


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the single duplicate number in an array of n+1 integers
where each is in [1, n], without modifying the array."

Key Insight:
"Treat the array as a linked list. From index i, jump to nums[i]. Because
nums[i] is in [1, n], every 'next' is a valid index. The duplicate value
means two indices point to it — creating a cycle. Find the cycle entry
using Floyd's two-phase algorithm — that's the duplicate."

Algorithm:
Phase 1: Find meeting point inside cycle.
  slow = nums[slow], fast = nums[nums[fast]] until they meet.
Phase 2: Find cycle entry.
  Reset slow to nums[0]. Advance both 1 step. They meet at cycle entry.

Edge Cases:
- Two occurrences: works.
- More than two: still works (the cycle entry is the dup).
- All others distinct: only one dup, guaranteed.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Floyd's   | O(n)   | O(1)   |
| Binary srch| O(nlogn)| O(1) |
| Hash set  | O(n)   | O(n)   |
| Mark neg  | O(n)   | O(1)*  |
+-----------+--------+--------+
*Mark neg modifies the array.

KEY TRICK:
The trick is recognizing the array as a linked list where nums[i] is the
"next" pointer. With n+1 entries and values in [1, n], there's a guaranteed
cycle (pigeonhole).

RELATED PROBLEMS:
- Linked List Cycle II (LC 142): find cycle entry.
- Find All Duplicates (LC 442): mark approach.
- Set Mismatch (LC 645).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        # (input, expected, description)
        ([1, 3, 4, 2, 2], 2, "Standard"),
        ([3, 1, 3, 4, 2], 3, "Dup at front"),
        ([1, 1], 1, "Tiny"),
        ([1, 1, 2], 1, "Three elements"),
        ([3, 3, 1, 4, 2], 3, "Triple dup"),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 9], 9, "Large with dup at end"),
        ([5, 4, 3, 2, 1, 6, 7, 8, 9, 5], 5, "Dup at start and end"),
        ([1, 5, 3, 4, 2, 6, 7, 8, 9, 5], 5, "Dup in middle"),
        ([2, 5, 9, 6, 4, 3, 7, 8, 3, 1], 3, "Mixed"),
        ([1, 2, 1], 1, "Min case"),
        ([3, 3, 1, 4, 2], 3, "Triplicate"),
    ]

    implementations = [
        ("Way 1: Floyd's (BEST)", find_duplicate_1),
        ("Way 2: Binary search on count", find_duplicate_2),
        ("Way 3: Mark visited (neg)", find_duplicate_3),
        ("Way 4: Hash set", find_duplicate_4),
        ("Way 5: Sort + adjacent", find_duplicate_5),
        ("Way 6: Counting", find_duplicate_6),
        ("Way 7: Sum difference", find_duplicate_7),
        ("Way 8: XOR", find_duplicate_8),
        ("Way 9: Class-based", find_duplicate_9),
        ("Way 10: Final cleanest", find_duplicate_10),
    ]

    all_pass = True
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
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: nums={nums} expected={expected} got={result}")
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
