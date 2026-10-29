"""
Number of Valid Subarrays
Hard | 40 min

Given an integer array nums, count how many non-empty contiguous subarrays
exist where the first element of each subarray is <= every other element
in that subarray.

A subarray is "valid" if the leftmost element is the MINIMUM of the subarray.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/number-of-valid-subarrays

Examples:
    [1, 4, 2, 5, 3]      -> ?
        - All subarrays starting with 1 are valid (1 is min of all)
          Count: 5 (start at 0, length 1 to 5)
        - Subarrays starting with 4: only [4] valid (4 < anything else in any subarray)
          Actually: [4,2]? No, 2 < 4. [4] alone yes.
          Count: 1
        - Subarrays starting with 2: [2,5,3]? No, 3<... wait 2<=5 and 2<=3? Yes! [2,5]? 2<=5 yes. [2,5,3]? 2<=5, 2<=3 yes. [2]? Yes.
          Count: 3
        - Subarrays starting with 5: [5,3]? No, 3<5. [5]? Yes.
          Count: 1
        - Subarrays starting with 3: [3]? Yes.
          Count: 1
        Total: 5 + 1 + 3 + 1 + 1 = 11

    [3, 1, 4]            -> ?
        - [3]: yes (1). [3,1]? No, 1<3 (0). [3,1,4]? No (0).
        - [1]: yes (1). [1,4]? 1<=4 yes (1). Total 2.
        - [4]: yes (1).
        Total: 1 + 0 + 0 + 1 + 1 + 1 + 1 = 5

    [1, 2, 3]            -> 6 (all subarrays valid since increasing)

Constraints:
- 1 <= nums.length <= 1000
- 0 <= nums[i] <= 10^5
"""


# =============================================================================
# WAY 1: Monotonic stack with index counting (BEST - Memorize!)
# =============================================================================
# THINKING: "For each index i, count subarrays starting at i where nums[i]
#           is the minimum. The number of such subarrays = distance to the
#           next smaller element (exclusive) = i - prev_smaller_index - 1
#           PLUS 1 for the subarray [i:i+1].
#           Actually: count = next_smaller_index - i
#           Use a monotonic increasing stack to find next smaller."
def valid_subarrays_1(nums):
    n = len(nums)
    # next_smaller[i] = index of next element smaller than nums[i], or n if none
    next_smaller = [n] * n
    stack = []  # monotonic increasing stack of indices

    for i in range(n):
        # Pop elements greater than nums[i] (they have found a smaller)
        while stack and nums[stack[-1]] > nums[i]:
            idx = stack.pop()
            next_smaller[idx] = i
        stack.append(i)

    # For each i, valid subarrays starting at i = next_smaller[i] - i
    count = 0
    for i in range(n):
        count += next_smaller[i] - i

    return count


# =============================================================================
# WAY 2: Using prev_smaller (left boundary)
# =============================================================================
def valid_subarrays_2(nums):
    """For each i, count = next_smaller[i] - i. Same as Way 1."""
    n = len(nums)
    next_smaller = [n] * n
    stack = []

    for i in range(n):
        while stack and nums[stack[-1]] > nums[i]:
            next_smaller[stack.pop()] = i
        stack.append(i)

    return sum(next_smaller[i] - i for i in range(n))


# =============================================================================
# WAY 3: Brute force O(n^2)
# =============================================================================
def valid_subarrays_3(nums):
    n = len(nums)
    count = 0

    for i in range(n):
        min_val = nums[i]
        for j in range(i, n):
            min_val = min(min_val, nums[j])
            if min_val == nums[i]:
                count += 1
            else:
                break

    return count


# =============================================================================
# WAY 4: Using deque
# =============================================================================
from collections import deque

def valid_subarrays_4(nums):
    n = len(nums)
    next_smaller = [n] * n
    stack = deque()

    for i in range(n):
        while stack and nums[stack[-1]] > nums[i]:
            next_smaller[stack.pop()] = i
        stack.append(i)

    return sum(next_smaller[i] - i for i in range(n))


# =============================================================================
# WAY 5: Using enumerate with stack
# =============================================================================
def valid_subarrays_5(nums):
    n = len(nums)
    next_smaller = [n] * n
    stack = []

    for i, num in enumerate(nums):
        while stack and nums[stack[-1]] > num:
            next_smaller[stack.pop()] = i
        stack.append(i)

    total = 0
    for i in range(n):
        total += next_smaller[i] - i

    return total


# =============================================================================
# WAY 6: With helper function for next_smaller
# =============================================================================
def valid_subarrays_6(nums):
    def next_smaller_indices(arr):
        n = len(arr)
        result = [n] * n
        stack = []
        for i in range(n):
            while stack and arr[stack[-1]] > arr[i]:
                result[stack.pop()] = i
            stack.append(i)
        return result

    ns = next_smaller_indices(nums)
    return sum(ns[i] - i for i in range(len(nums)))


# =============================================================================
# WAY 7: Using reduce for next_smaller
# =============================================================================
def valid_subarrays_7(nums):
    from functools import reduce

    def step(state, item):
        i, num = item
        ns, stack = state
        new_ns = ns[:]
        new_stack = []
        while stack and nums[stack[-1]] > num:
            new_ns[stack.pop()] = i
        new_stack = stack[:] + [i]
        return new_ns, new_stack

    n = len(nums)
    ns, _ = reduce(step, enumerate(nums), ([n] * n, []))
    return sum(ns[i] - i for i in range(n))


# =============================================================================
# WAY 8: Iterative with explicit count
# =============================================================================
def valid_subarrays_8(nums):
    n = len(nums)
    next_smaller = [n] * n
    stack = []
    count = 0

    for i in range(n):
        while stack and nums[stack[-1]] > nums[i]:
            idx = stack.pop()
            next_smaller[idx] = i
        stack.append(i)

    for i in range(n):
        count += next_smaller[i] - i

    return count


# =============================================================================
# WAY 9: Most compact
# =============================================================================
def valid_subarrays_9(nums):
    n = len(nums)
    ns = [n] * n
    s = []
    for i, x in enumerate(nums):
        while s and nums[s[-1]] > x:
            ns[s.pop()] = i
        s.append(i)
    return sum(ns[i] - i for i in range(n))


# =============================================================================
# WAY 10: With try-except
# =============================================================================
def valid_subarrays_10(nums):
    n = len(nums)
    ns = [n] * n
    s = []

    for i in range(n):
        try:
            while nums[s[-1]] > nums[i]:
                ns[s.pop()] = i
        except IndexError:
            pass
        s.append(i)

    return sum(ns[i] - i for i in range(n))


# =============================================================================
# WAY 11: Using list comprehension
# =============================================================================
def valid_subarrays_11(nums):
    n = len(nums)
    ns = [n] * n
    s = []
    for i in range(n):
        while s and nums[s[-1]] > nums[i]:
            ns[s.pop()] = i
        s.append(i)
    return sum(ns[i] - i for i in range(n))


# =============================================================================
# WAY 12: With numpy for clarity (using min calculations)
# =============================================================================
def valid_subarrays_12(nums):
    """Brute force using prefix minimum approach."""
    n = len(nums)
    count = 0
    for i in range(n):
        for j in range(i, n):
            # Check if nums[i] is min in nums[i:j+1]
            if min(nums[i:j+1]) == nums[i]:
                count += 1
    return count


# =============================================================================
# WAY 13: Reverse iteration with stack
# =============================================================================
def valid_subarrays_13(nums):
    """Process from right; find prev_smaller for each."""
    n = len(nums)
    prev_smaller = [-1] * n
    stack = []

    for i in range(n - 1, -1, -1):
        while stack and nums[stack[-1]] >= nums[i]:
            stack.pop()
        if stack:
            prev_smaller[i] = stack[-1]
        else:
            prev_smaller[i] = n  # no smaller after i
        stack.append(i)

    # For each i, valid subarrays starting at i = prev_smaller[i] - i
    # But wait, prev_smaller should be NEXT smaller
    # This is reversed - let me re-do
    # Actually: count = next_smaller_index - i where next_smaller > i
    # If we want subarrays starting at i to be valid, we need to extend
    # until we hit a smaller element.
    # If we compute prev_smaller going right-to-left, prev_smaller[i] is
    # the next smaller element to the right of i.
    # So count for i = prev_smaller[i] - i

    return sum(prev_smaller[i] - i for i in range(n))


# =============================================================================
# WAY 14: Using class for clarity
# =============================================================================
class SubarrayCounter:
    def __init__(self, nums):
        self.nums = nums
        self.n = len(nums)

    def count(self):
        ns = self._next_smaller()
        return sum(ns[i] - i for i in range(self.n))

    def _next_smaller(self):
        ns = [self.n] * self.n
        stack = []
        for i in range(self.n):
            while stack and self.nums[stack[-1]] > self.nums[i]:
                ns[stack.pop()] = i
            stack.append(i)
        return ns


def valid_subarrays_14(nums):
    return SubarrayCounter(nums).count()


# =============================================================================
# WAY 15: Most elegant (clean Way 1)
# =============================================================================
def valid_subarrays_15(nums):
    n = len(nums)
    next_smaller = [n] * n
    stack = []

    for i, num in enumerate(nums):
        while stack and nums[stack[-1]] > num:
            next_smaller[stack.pop()] = i
        stack.append(i)

    return sum(next_smaller[i] - i for i in range(n))


# =============================================================================
# WAY 16: One-liner style with explicit sum
# =============================================================================
def valid_subarrays_16(nums):
    n = len(nums)
    next_smaller = [n] * n
    stack = []

    for i in range(n):
        while stack and nums[stack[-1]] > nums[i]:
            next_smaller[stack.pop()] = i
        stack.append(i)

    total = 0
    for i in range(n):
        total = total + (next_smaller[i] - i)

    return total


# =============================================================================
# WAY 17: Recursive brute force (matches the algorithm)
# =============================================================================
def valid_subarrays_17(nums):
    """For each starting index i, recursively extend right."""
    n = len(nums)
    count = [0]

    def extend(start, idx, current_min):
        # We've started a subarray at 'start' and extended to 'idx'
        # current_min is the minimum seen so far
        if idx == n:
            return
        # The subarray nums[start:idx+1] is valid if current_min == nums[start]
        # Extend further
        if nums[idx] >= current_min:
            count[0] += 1
            extend(start, idx + 1, current_min)

    # For each starting position, try extending
    for i in range(n):
        count[0] += 1  # subarray [i:i+1] is always valid
        extend(i, i + 1, nums[i])

    return count[0]


# =============================================================================
# WAY 18: Most compact stack approach
# =============================================================================
def valid_subarrays_18(nums):
    n = len(nums)
    result = [n] * n
    s = []
    for i, v in enumerate(nums):
        while s and nums[s[-1]] > v:
            result[s.pop()] = i
        s.append(i)
    return sum(result[i] - i for i in range(n))


# =============================================================================
# WAY 19: Using helper for counting
# =============================================================================
def valid_subarrays_19(nums):
    def count_for_each(nums):
        n = len(nums)
        ns = [n] * n
        s = []
        for i in range(n):
            while s and nums[s[-1]] > nums[i]:
                ns[s.pop()] = i
            s.append(i)
        return ns

    def sum_distances(ns):
        return sum(ns[i] - i for i in range(len(ns)))

    return sum_distances(count_for_each(nums))


# =============================================================================
# WAY 20: Final cleanest (Way 1 repeated with comments)
# =============================================================================
def valid_subarrays_20(nums):
    n = len(nums)
    # For each index i, find the next index j > i where nums[j] < nums[i]
    # Then valid subarrays starting at i are: nums[i:i+1], nums[i:i+2], ..., nums[i:j]
    # Count = j - i. If no smaller exists, j = n, count = n - i.

    next_smaller = [n] * n
    stack = []

    for i in range(n):
        while stack and nums[stack[-1]] > nums[i]:
            next_smaller[stack.pop()] = i
        stack.append(i)

    return sum(next_smaller[i] - i for i in range(n))


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to count contiguous subarrays where the first element is <= all
other elements. This means the first element is the MINIMUM of the subarray."

Key Insight:
"For each index i, count subarrays starting at i.
If I extend the subarray rightward, I can include elements until I hit
something SMALLER than nums[i]. The moment I hit a smaller element, nums[i]
is no longer the minimum.
So count for i = (next_smaller_index) - i."

Algorithm:
"1. Find next_smaller[i] = first index j > i where nums[j] < nums[i].
   If no such j exists, next_smaller[i] = n.
2. Answer = sum of (next_smaller[i] - i) for all i.

For step 1, use a MONOTONIC INCREASING STACK:
- Push indices of increasing values
- When we see a smaller value, pop larger indices and set their next_smaller.
- After processing all, indices left in stack have no smaller to the right,
  so next_smaller = n."

Why this works:
"Each index is pushed once and popped at most once.
When popped, we KNOW the next smaller exists (it's the current index).
The monotonic stack property (increasing values) ensures we find the
CLOSEST smaller element to the right."

Edge cases:
- Empty array: 0
- All increasing: every subarray valid -> n*(n+1)/2
- All decreasing: only subarrays of length 1 valid -> n
- Equal adjacent: depends on tie-breaking

COMPLEXITY:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Monotonic | O(n)   | O(n)   |
| Brute     | O(n^2) | O(1)   |
+-----------+--------+--------+

KEY TRICK:
The trick is recognizing this as a 'next smaller element' problem.
For each index i, find how far we can extend right with nums[i] as min.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Monotonic stack (BEST)", valid_subarrays_1),
        ("Way 2: With sum", valid_subarrays_2),
        ("Way 3: Brute force", valid_subarrays_3),
        ("Way 4: deque", valid_subarrays_4),
        ("Way 5: enumerate", valid_subarrays_5),
        ("Way 6: Helper function", valid_subarrays_6),
        ("Way 7: reduce", valid_subarrays_7),
        ("Way 8: Explicit count", valid_subarrays_8),
        ("Way 9: Most compact", valid_subarrays_9),
        ("Way 10: Try-except", valid_subarrays_10),
        ("Way 11: List comprehension", valid_subarrays_11),
        ("Way 12: Brute with min", valid_subarrays_12),
        ("Way 13: Reverse iteration", valid_subarrays_13),
        ("Way 14: With class", valid_subarrays_14),
        ("Way 15: Most elegant", valid_subarrays_15),
        ("Way 16: Explicit sum", valid_subarrays_16),
        ("Way 17: Recursive", valid_subarrays_17),
        ("Way 18: Most compact stack", valid_subarrays_18),
        ("Way 19: Helper counting", valid_subarrays_19),
        ("Way 20: Final cleanest", valid_subarrays_20),
    ]

    # Let me verify expected values:
    # [1, 4, 2, 5, 3]
    # next_smaller = ?
    # i=0, num=1: stack empty, push 0. stack=[0]
    # i=1, num=4: 1<4, push 1. stack=[0,1]
    # i=2, num=2: 4>2, pop 1, next_smaller[1]=2. 1<2, push 2. stack=[0,2]
    # i=3, num=5: 2<5, push 3. stack=[0,2,3]
    # i=4, num=3: 5>3, pop 3, next_smaller[3]=4. 2<3, push 4. stack=[0,2,4]
    # End: stack=[0,2,4], no pops. next_smaller for them = 5.
    # next_smaller = [5, 2, 5, 4, 5]
    # count = (5-0) + (2-1) + (5-2) + (4-3) + (5-4) = 5 + 1 + 3 + 1 + 1 = 11

    # [3, 1, 4]
    # i=0, num=3: push 0. stack=[0]
    # i=1, num=1: 3>1, pop 0, next_smaller[0]=1. push 1. stack=[1]
    # i=2, num=4: 1<4, push 2. stack=[1,2]
    # End: stack=[1,2], next_smaller for them = 3.
    # next_smaller = [1, 3, 3]
    # count = (1-0) + (3-1) + (3-2) = 1 + 2 + 1 = 4
    # Wait, I had 5 earlier. Let me re-count.
    # [3, 1, 4]: subarrays: [3], [3,1], [3,1,4], [1], [1,4], [4]
    # [3]: valid (3 is min=3)
    # [3,1]: 3 vs 1, 1<3 so 3 is NOT min. Invalid.
    # [3,1,4]: 3 vs (1,4), 1<3. Invalid.
    # [1]: valid
    # [1,4]: valid (1<=4)
    # [4]: valid
    # Total: 1 + 0 + 0 + 1 + 1 + 1 = 4 ✓ (I had 5 earlier which was wrong)

    # [1, 2, 3]: all increasing, all subarrays valid
    # n=3, total subarrays = 6
    # next_smaller = [3, 3, 3]
    # count = 3 + 2 + 1 = 6 ✓

    test_cases = [
        ([1, 4, 2, 5, 3], 11),
        ([3, 1, 4], 4),
        ([1, 2, 3], 6),
        ([3, 2, 1], 3),  # only length-1 subarrays
        ([1], 1),
        ([2, 2, 2], 6),  # all equal, all subarrays valid
        ([1, 3, 2, 4, 5], 12),  # let me verify: i=0,1: 1<=anything, count from 0:5 + 1:4? Let me compute
        ([5, 4, 3, 2, 1], 5),  # decreasing, only length-1
        ([1, 1, 1, 1], 10),  # n*(n+1)/2
    ]

    # Verify [1, 3, 2, 4, 5]:
    # i=0, num=1: push 0. [0]
    # i=1, num=3: 1<3, push 1. [0,1]
    # i=2, num=2: 3>2, pop 1, next_smaller[1]=2. 1<2, push 2. [0,2]
    # i=3, num=4: 2<4, push 3. [0,2,3]
    # i=4, num=5: 4<5, push 4. [0,2,3,4]
    # End: stack=[0,2,3,4], next_smaller = [5,2,5,5,5]
    # count = 5 + 1 + 3 + 2 + 1 = 12 ✓

    # Verify [2, 2, 2]:
    # i=0, num=2: push 0. [0]
    # i=1, num=2: nums[0]=2, NOT >2 (we use strict >). push 1. [0,1]
    # i=2, num=2: NOT >2. push 2. [0,1,2]
    # End: stack=[0,1,2], next_smaller = [3,3,3]
    # count = 3 + 2 + 1 = 6 ✓ (all subarrays valid since all equal)

    print("=" * 70)
    print("NUMBER OF VALID SUBARRAYS - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/number-of-valid-subarrays")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for nums, expected in test_cases:
            try:
                result = func(nums)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: {nums} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on {nums} - {e}")
        print(f"  {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
