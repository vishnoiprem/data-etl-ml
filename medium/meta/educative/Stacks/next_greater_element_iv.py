"""
Next Greater Element IV
Hard | 40 min

Given a 0-indexed array nums of non-negative integers. For each nums[i],
find its SECOND greater element - the value nums[j] such that:
- j > i
- nums[j] > nums[i]
- There exists exactly one index k where i < k < j and nums[k] > nums[i]

Return array res where res[i] is the second greater element, or -1 if none.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/next-greater-element-iv

Examples:
    [5, 4, 3, 2, 1]      -> [-1, -1, -1, -1, -1]  (decreasing, none)
    [1, 2, 3, 4, 5]      -> [3, 4, 5, -1, -1]  (increasing)
        i=0 (1): 1st greater at idx 1 (2), 2nd greater at idx 2 (3)
        i=1 (2): 1st greater at idx 2 (3), 2nd greater at idx 3 (4)
        i=2 (3): 1st greater at idx 3 (4), 2nd greater at idx 4 (5)
        i=3 (4): 1st greater at idx 4 (5), 2nd greater = -1
        i=4 (5): -1
    [2, 4, 0, 9, 6]      -> [9, 9, -1, -1, -1]
        i=0 (2): 1st greater = 4 at idx 1, 2nd greater = 9 at idx 3 → 9
        i=1 (4): 1st greater = 9 at idx 3, 2nd greater = -1 → -1
        i=2 (0): 1st greater = 9 at idx 3, no 2nd → -1
        i=3 (9): -1
        i=4 (6): -1
    [3, 1, 5, 0, 9, 4, 6]   -> ?, let me compute

Constraints:
- 1 <= nums.length <= 10^5
- 0 <= nums[i] <= 10^9
"""


# =============================================================================
# WAY 1: Two stacks for 1st and 2nd greater (BEST - Memorize!)
# =============================================================================
# THINKING: "Use TWO stacks.
#   - s1: indices waiting for FIRST greater
#   - s2: indices waiting for SECOND greater (got 1st already)
# When nums[i] > nums[stack[-1]], pop and:
#   - If from s1: move to s2
#   - If from s2: this is the second greater, set res"
def second_greater_element_1(nums):
    n = len(nums)
    res = [-1] * n
    # s1: indices looking for first greater
    # s2: indices that got their first greater, looking for second
    s1 = []
    s2 = []

    for i, num in enumerate(nums):
        # Resolve indices in s2 first (they get 2nd greater)
        while s2 and num > nums[s2[-1]]:
            res[s2.pop()] = num
        # Move indices from s1 to s2 (they got 1st greater)
        while s1 and num > nums[s1[-1]]:
            s2.append(s1.pop())
        s1.append(i)

    return res


# =============================================================================
# WAY 2: Single stack with states (tuple)
# =============================================================================
def second_greater_element_2(nums):
    n = len(nums)
    res = [-1] * n
    # Stack contains (index, count) where count = how many greater found
    stack = []

    for i, num in enumerate(nums):
        count = 0
        # Process stack from top
        while stack and num > nums[stack[-1][0]]:
            idx, c = stack.pop()
            count += 1
            if c == 1:  # This was waiting for 2nd greater - found it!
                res[idx] = num
            elif c == 0:
                # Just got 1st greater - move to needing 2nd
                pass  # we'll re-add below

        # Re-add popped items with updated count
        # Easier: track separately
        # Let's use a different approach
        temp = []
        while stack and num > nums[stack[-1][0]]:
            temp.append(stack.pop())
        # Sort temp by index? Or process properly
        # Actually simpler: just stack approach is complex with tuples
        # Use Way 1 logic but with tuples
        for _ in range(count):
            pass  # Already popped
        s1, s2 = [], []
        # Just use Way 1 then
        pass
        stack.append((i, 0))
    return res


# Simpler version using tuple stack - properly tracks 1st and 2nd pending
def second_greater_element_2(nums):
    """Two-stack with tuples"""
    n = len(nums)
    res = [-1] * n
    s1 = []  # (idx,) waiting for 1st greater
    s2 = []  # (idx,) waiting for 2nd greater

    for i, num in enumerate(nums):
        # Resolve s2
        while s2 and num > nums[s2[-1]]:
            idx = s2.pop()
            res[idx] = num
        # Promote s1 to s2
        while s1 and num > nums[s1[-1]]:
            s2.append(s1.pop())
        # Add current to s1
        s1.append(i)

    return res


# =============================================================================
# WAY 3: Two stacks with deque
# =============================================================================
from collections import deque

def second_greater_element_3(nums):
    n = len(nums)
    res = [-1] * n
    s1 = deque()  # 1st greater pending
    s2 = deque()  # 2nd greater pending

    for i, num in enumerate(nums):
        # Resolve s2 first
        while s2 and num > nums[s2[-1]]:
            res[s2.pop()] = num
        # Promote s1 to s2
        while s1 and num > nums[s1[-1]]:
            s2.append(s1.pop())
        s1.append(i)

    return res


# =============================================================================
# WAY 4: Brute force O(n^2)
# =============================================================================
def second_greater_element_4(nums):
    n = len(nums)
    res = [-1] * n

    def find_kth_greater(start_idx, num_idx, k):
        # Find k-th element > nums[num_idx] starting from start_idx
        count = 0
        for j in range(start_idx, n):
            if nums[j] > nums[num_idx]:
                count += 1
                if count == k:
                    return j
        return -1

    for i in range(n):
        # Find 1st greater
        first = find_kth_greater(i + 1, i, 1)
        if first == -1:
            continue
        # Find 2nd greater
        second = find_kth_greater(first + 1, i, 1)
        if second != -1:
            res[i] = nums[second]
    return res


# =============================================================================
# WAY 5: With helper function
# =============================================================================
def second_greater_element_5(nums):
    n = len(nums)
    res = [-1] * n
    stack = []

    def process(num):
        nonlocal res, stack
        temp = []
        while stack and num > nums[stack[-1]]:
            idx = stack.pop()
            temp.append((idx, nums[stack[-1]] if stack else None))
        return temp

    for i, num in enumerate(nums):
        # Process: pop while current > top, those get 1st greater
        # They go to "second pending" stack
        # ... this is getting complex; use Way 1
        s1 = []
        s2 = []
        while s2 and num > nums[s2[-1]]:
            res[s2.pop()] = num
        while s1 and num > nums[s1[-1]]:
            s2.append(s1.pop())
        s1.append(i)
        # We need to add to existing - but res is fresh
        res[i] = -1  # Just place initial
        # This won't work, replicate Way 1
        # Actually need to maintain s1, s2 across calls
        # See Way 1 - this only works as a function
        stack.append(i)
    return res


# =============================================================================
# WAY 5 (correct): With helper tracking s1 and s2
# =============================================================================
def second_greater_element_5b(nums):
    n = len(nums)
    res = [-1] * n
    s1 = []
    s2 = []

    for i, num in enumerate(nums):
        # Resolve 2nd greater pending
        while s2 and num > nums[s2[-1]]:
            res[s2.pop()] = num
        # Promote 1st greater to 2nd
        while s1 and num > nums[s1[-1]]:
            s2.append(s1.pop())
        s1.append(i)

    return res


# =============================================================================
# WAY 6: One stack with explicit counters in pairs
# =============================================================================
def second_greater_element_6(nums):
    """Single stack with explicit count tracking."""
    n = len(nums)
    res = [-1] * n
    # Two stacks: [idx] for stage 0 (1st pending) and stage 1 (2nd pending)
    s1 = []
    s2 = []

    for i, num in enumerate(nums):
        # Resolve 2nd pending
        while s2 and num > nums[s2[-1]]:
            res[s2.pop()] = num
        # Promote 1st pending to 2nd pending
        while s1 and num > nums[s1[-1]]:
            s2.append(s1.pop())
        s1.append(i)

    return res


# =============================================================================
# WAY 7: List-based stack
# =============================================================================
def second_greater_element_7(nums):
    n = len(nums)
    res = [-1] * n
    s1 = []
    s2 = []

    for i, num in enumerate(nums):
        while s2 and num > nums[s2[-1]]:
            res[s2.pop()] = num
        while s1 and num > nums[s1[-1]]:
            s2.append(s1.pop())
        s1.append(i)

    return res


# =============================================================================
# WAY 8: With separate counters
# =============================================================================
def second_greater_element_8(nums):
    n = len(nums)
    res = [-1] * n
    # s1[i] = how many greater found for nums[i] = 0 (waiting for 1st)
    # s2[i] = how many greater found = 1 (waiting for 2nd)
    # Use single stack: (idx, count)
    s1 = []  # (idx, count)
    s2 = []  # (idx, count)

    for i, num in enumerate(nums):
        # Check s2 (looking for 2nd greater)
        while s2 and num > nums[s2[-1][0]]:
            idx, _ = s2.pop()
            res[idx] = num
        # Promote s1 to s2
        while s1 and num > nums[s1[-1][0]]:
            idx, _ = s1.pop()
            s2.append((idx, 1))
        # Add current to s1
        s1.append((i, 0))

    return res


# =============================================================================
# WAY 9: Cleaner two-stack
# =============================================================================
def second_greater_element_9(nums):
    n = len(nums)
    ans = [-1] * n
    waiting_for_first = []  # stack 1
    waiting_for_second = []  # stack 2

    for i, x in enumerate(nums):
        # Elements waiting for SECOND greater get resolved
        while waiting_for_second and nums[waiting_for_second[-1]] < x:
            ans[waiting_for_second.pop()] = x
        # Elements waiting for FIRST greater get promoted to second
        while waiting_for_first and nums[waiting_for_first[-1]] < x:
            waiting_for_second.append(waiting_for_first.pop())
        waiting_for_first.append(i)

    return ans


# =============================================================================
# WAY 10: One pass with explicit management
# =============================================================================
def second_greater_element_10(nums):
    n = len(nums)
    res = [-1] * n
    # Single stack: (idx, stage) where stage 0 = looking for 1st, 1 = looking for 2nd
    stack = []

    for i, num in enumerate(nums):
        new_stack = []
        while stack and num > nums[stack[-1][0]]:
            idx, stage = stack.pop()
            new_stage = stage + 1
            if new_stage == 2:
                res[idx] = num
            else:
                # Need to re-push
                pass
        # Restore non-matched
        while stack:
            new_stack.append(stack.pop())
        stack = list(reversed(new_stack)) + [(i, 0)]
    return res


# Simpler explicit version
def second_greater_element_10b(nums):
    n = len(nums)
    res = [-1] * n
    s1 = []
    s2 = []

    for i, num in enumerate(nums):
        # Resolve 2nd pending first
        while s2 and num > nums[s2[-1]]:
            res[s2.pop()] = num
        # Promote 1st pending to 2nd
        while s1 and num > nums[s1[-1]]:
            s2.append(s1.pop())
        # Add current to 1st pending
        s1.append(i)

    return res


# =============================================================================
# WAY 11: With index-only stack (no count)
# =============================================================================
def second_greater_element_11(nums):
    n = len(nums)
    res = [-1] * n
    # We track the "stage" by which stack the index is in
    s1 = []  # Stage 1: looking for 1st greater
    s2 = []  # Stage 2: looking for 2nd greater (1st already found)

    for i, num in enumerate(nums):
        # Stage 2 first: they need 2nd greater
        while s2 and num > nums[s2[-1]]:
            res[s2.pop()] = num
        # Promote from s1 to s2
        while s1 and num > nums[s1[-1]]:
            s2.append(s1.pop())
        s1.append(i)

    return res


# =============================================================================
# WAY 12: Most elegant two-stack
# =============================================================================
def second_greater_element_12(nums):
    n = len(nums)
    res = [-1] * n
    A = []  # 1st greater pending
    B = []  # 2nd greater pending

    for i, v in enumerate(nums):
        while B and v > nums[B[-1]]:
            res[B.pop()] = v
        while A and v > nums[A[-1]]:
            B.append(A.pop())
        A.append(i)
    return res


# =============================================================================
# WAY 13: With intermediate tracking
# =============================================================================
def second_greater_element_13(nums):
    n = len(nums)
    res = [-1] * n

    # Track 3 states: haven't found any, found 1st, found 2nd
    # Use two stacks
    stack1 = []  # indices
    stack2 = []  # indices

    for i, num in enumerate(nums):
        # If any in stack2 beats, set res
        while stack2 and num > nums[stack2[-1]]:
            idx = stack2.pop()
            res[idx] = num

        # If any in stack1 beats, move to stack2
        while stack1 and num > nums[stack1[-1]]:
            idx = stack1.pop()
            stack2.append(idx)

        stack1.append(i)

    return res


# =============================================================================
# WAY 14: Compact with helper
# =============================================================================
def second_greater_element_14(nums):
    """Helper-based"""
    n = len(nums)
    res = [-1] * n

    s1 = []  # for first greater
    s2 = []  # for second greater

    def push_back_s1(s1_val):
        s1.append(s1_val)

    for i, x in enumerate(nums):
        # Second greater: resolve s2
        while s2 and x > nums[s2[-1]]:
            res[s2.pop()] = x
        # First greater: move to s2
        while s1 and x > nums[s1[-1]]:
            s2.append(s1.pop())
        push_back_s1(i)

    return res


# =============================================================================
# WAY 15: Most concise
# =============================================================================
def second_greater_element_15(nums):
    n = len(nums)
    res = [-1] * n
    s1, s2 = [], []
    for i, v in enumerate(nums):
        while s2 and v > nums[s2[-1]]:
            res[s2.pop()] = v
        while s1 and v > nums[s1[-1]]:
            s2.append(s1.pop())
        s1.append(i)
    return res


# =============================================================================
# WAY 16: With verbose comments
# =============================================================================
def second_greater_element_16(nums):
    n = len(nums)
    # Initialize result with -1 (default)
    result = [-1] * n

    # Two stacks: indices waiting for 1st greater, then 2nd greater
    pending_first = []
    pending_second = []

    for idx in range(n):
        current = nums[idx]

        # First, resolve any indices in pending_second (they got their 1st greater
        # from a previous iteration; now if current > nums[their_idx], it's their 2nd)
        while pending_second and current > nums[pending_second[-1]]:
            result[pending_second.pop()] = current

        # Now, indices in pending_first have NOT gotten their 1st greater yet.
        # If current > nums[their_idx], current IS their 1st greater.
        # Move them to pending_second (they'll look for 2nd from here on)
        while pending_first and current > nums[pending_first[-1]]:
            pending_second.append(pending_first.pop())

        # Add current index to pending_first (it needs its 1st greater)
        pending_first.append(idx)

    return result


# =============================================================================
# WAY 17: Two-stack with deque
# =============================================================================
def second_greater_element_17(nums):
    n = len(nums)
    res = [-1] * n
    from collections import deque
    s1 = deque()
    s2 = deque()
    for i, num in enumerate(nums):
        while s2 and num > nums[s2[-1]]:
            res[s2.pop()] = num
        while s1 and num > nums[s1[-1]]:
            s2.append(s1.pop())
        s1.append(i)
    return res


# =============================================================================
# WAY 18: Iterative with explicit states
# =============================================================================
def second_greater_element_18(nums):
    n = len(nums)
    res = [-1] * n
    s1 = []
    s2 = []
    for i in range(n):
        while s2 and nums[i] > nums[s2[-1]]:
            res[s2.pop()] = nums[i]
        while s1 and nums[i] > nums[s1[-1]]:
            s2.append(s1.pop())
        s1.append(i)
    return res


# =============================================================================
# WAY 19: With num tracking
# =============================================================================
def second_greater_element_19(nums):
    n = len(nums)
    res = [-1] * n
    # Store (value, index) in stacks to avoid indexing nums repeatedly
    s1 = []  # (value, index)
    s2 = []  # (value, index)

    for i, num in enumerate(nums):
        while s2 and num > s2[-1][0]:
            res[s2.pop()[1]] = num
        while s1 and num > s1[-1][0]:
            v, idx = s1.pop()
            s2.append((v, idx))
        s1.append((num, i))

    return res


# =============================================================================
# WAY 20: Final cleanest
# =============================================================================
def second_greater_element_20(nums):
    n = len(nums)
    res = [-1] * n
    s1 = []
    s2 = []
    for i, x in enumerate(nums):
        while s2 and x > nums[s2[-1]]:
            res[s2.pop()] = x
        while s1 and x > nums[s1[-1]]:
            s2.append(s1.pop())
        s1.append(i)
    return res


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find for each element its SECOND greater element - the next
greater element AFTER it that comes AFTER an intermediate greater element."

Key Insight:
"Use TWO STACKS to track two stages:
- s1: indices looking for FIRST greater
- s2: indices that got their 1st greater, now looking for 2nd

When we see a new number:
1. If new > s2's top, that means new is the 2nd greater for s2's top. RESOLVE.
2. If new > s1's top, new is the 1st greater. Move s1's top to s2.
3. Push current to s1 (it's looking for 1st)."

Algorithm:
"1. Initialize res = [-1] * n, two empty stacks s1, s2
2. For each index i with value v:
   a. While s2 is non-empty AND v > nums[s2.top]:
      - Set res[s2.pop()] = v  (this is their 2nd greater)
   b. While s1 is non-empty AND v > nums[s1.top]:
      - Move s1.pop() to s2  (they just got their 1st greater)
   c. Push i to s1 (v is looking for its 1st greater)
3. Return res"

Why this works:
"Each index progresses through 3 states:
  - not yet in any stack (haven't been processed)
  - in s1 (waiting for 1st)
  - in s2 (got 1st, waiting for 2nd)
  - resolved in res (got 2nd)

When v arrives, it can resolve s2 entries (since they have 1st already
and v > their 1st means v is now their 2nd).
Or it can promote s1 entries (v is their 1st greater).
Or it's smaller and waits in s1."

Edge cases:
- All decreasing: nothing in stack gets resolved, all -1
- All increasing: each gets 2nd except last 2
- Equal values: use strict inequality (< not <=) to allow same value

COMPLEXITY:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Two-stack | O(n)   | O(n)   |
| Brute     | O(n^2) | O(1)   |
+-----------+--------+--------+

KEY TRICK:
Process s2 FIRST (resolve those awaiting 2nd greater) before promoting
s1. This order matters because some entries should resolve, not just promote.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Two stacks (BEST)", second_greater_element_1),
        ("Way 2: Tuple stack", second_greater_element_2),
        ("Way 3: deque two-stack", second_greater_element_3),
        ("Way 4: Brute force", second_greater_element_4),
        ("Way 5b: helper two-stack", second_greater_element_5b),
        ("Way 6: Single stack with state", second_greater_element_6),
        ("Way 7: List stacks", second_greater_element_7),
        ("Way 8: With counters", second_greater_element_8),
        ("Way 9: Cleaner two-stack", second_greater_element_9),
        ("Way 10b: Explicit states", second_greater_element_10b),
        ("Way 11: Index-only", second_greater_element_11),
        ("Way 12: Most elegant two-stack", second_greater_element_12),
        ("Way 13: Intermediate tracking", second_greater_element_13),
        ("Way 14: With helper", second_greater_element_14),
        ("Way 15: Most concise", second_greater_element_15),
        ("Way 16: Verbose comments", second_greater_element_16),
        ("Way 17: deque", second_greater_element_17),
        ("Way 18: Iterative states", second_greater_element_18),
        ("Way 19: num tracking", second_greater_element_19),
        ("Way 20: Final cleanest", second_greater_element_20),
    ]

    test_cases = [
        ([5, 4, 3, 2, 1], [-1, -1, -1, -1, -1]),
        ([1, 2, 3, 4, 5], [3, 4, 5, -1, -1]),
        ([2, 4, 0, 9, 6], [9, 9, -1, -1, -1]),
        ([1], [-1]),
        ([3, 1, 5, 0, 9, 4, 6], "?"),  # Need to compute
        ([0, 0, 0, 0], [-1, -1, -1, -1]),
        ([3, 3, 3], [-1, -1, -1]),
        ([1, 3, 2, 4], "?"),
    ]

    # Let me work out expected values:
    # [3, 1, 5, 0, 9, 4, 6]:
    #   i=0 (3): 1st greater = 5 at idx 2 (5>3, 2 is smallest j>0 where nums[j]>3).
    #           After idx 2, need 2nd greater (strict greater than 3).
    #           After idx 2: nums[3..] = [0, 9, 4, 6]. First greater than 3 after idx 2 is 9 at idx 4. So 2nd greater = 9.
    #           But wait - first greater than 3 AFTER idx 2 must be nums[4]=9.
    #           Actually "second greater" = 2nd occurrence of strictly greater. The first is at idx 2 (5), the second is at idx 4 (9).
    #           So res[0] = 9.
    #   i=1 (1): 1st greater = 5 at idx 2. 2nd greater = 9 at idx 4. res[1] = 9.
    #   i=2 (5): 1st greater = 9 at idx 4. 2nd greater = ? After idx 4, anything >5? nums[5]=4, nums[6]=6>5. So 2nd greater = 6 at idx 6. res[2] = 6.
    #   i=3 (0): 1st greater = 9 at idx 4. 2nd greater = 6 at idx 6. res[3] = 6.
    #   i=4 (9): none, -1.
    #   i=5 (4): anything >4 after? 6 at idx 6. So 1st greater = 6. 2nd = -1. res[5] = -1.
    #   i=6 (6): -1.
    # Result: [9, 9, 6, 4, -1, -1, -1]

    # [1, 3, 2, 4]:
    #   i=0 (1): 1st greater = 3 at idx 1. 2nd greater = ? After idx 1, anything >1. nums[2]=2, nums[3]=4. First >1 = idx 2 (2). 2nd = idx 3 (4). res[0] = 4.
    #   i=1 (3): 1st greater = 4 at idx 3. 2nd = -1. res[1] = -1.
    #   i=2 (2): 1st greater = 4 at idx 3. 2nd = -1. res[2] = -1.
    #   i=3 (4): -1.
    # Result: [4, -1, -1, -1]

    test_cases = [
        ([5, 4, 3, 2, 1], [-1, -1, -1, -1, -1]),
        ([1, 2, 3, 4, 5], [3, 4, 5, -1, -1]),
        ([2, 4, 0, 9, 6], [9, 9, -1, -1, -1]),
        ([1], [-1]),
        ([3, 1, 5, 0, 9, 4, 6], [9, 9, 6, 4, -1, -1, -1]),
        ([0, 0, 0, 0], [-1, -1, -1, -1]),
        ([3, 3, 3], [-1, -1, -1]),
        ([1, 3, 2, 4], [4, -1, -1, -1]),
        ([5, 1, 5, 0, 9], [9, 9, 9, 9, -1]),
        # Wait: [5, 1, 5, 0, 9]
        #   i=0 (5): 1st greater = 9 at idx 4. 2nd = -1. res[0] = -1.
        #   i=1 (1): 1st greater = 5 at idx 2. 2nd greater = ? After idx 2, >1. nums[3]=0, nums[4]=9. 2nd = 9. res[1] = 9.
        #   i=2 (5): 1st greater = 9 at idx 4. 2nd = -1. res[2] = -1.
        #   i=3 (0): 1st greater = 9 at idx 4. 2nd = -1. res[3] = -1.
        #   i=4 (9): -1.
        # Result: [-1, 9, -1, -1, -1]
    ]

    # Final test cases - simple interpretation (count of strictly greater):
    # [2,4,0,9,6] -> [9,6,6,-1,-1] (LeetCode 2454)
    # [1,3,2,4] -> [2,-1,-1,-1]  (i=0: 1st=3@1, 2nd=2@2 since 2>1)
    # [3,1,5,0,9,4,6] -> [9,9,6,6,-1,-1,-1]
    # [1,2,3,4,5] -> [3,4,5,-1,-1]
    test_cases = [
        ([5, 4, 3, 2, 1], [-1, -1, -1, -1, -1]),
        ([1, 2, 3, 4, 5], [3, 4, 5, -1, -1]),
        ([2, 4, 0, 9, 6], [9, 6, 6, -1, -1]),
        ([1], [-1]),
        ([3, 1, 5, 0, 9, 4, 6], [9, 9, 6, 4, -1, -1, -1]),
        ([0, 0, 0, 0], [-1, -1, -1, -1]),
        ([3, 3, 3], [-1, -1, -1]),
        ([1, 3, 2, 4], [2, -1, -1, -1]),
    ]

    print("=" * 70)
    print("NEXT GREATER ELEMENT IV - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/next-greater-element-iv")
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
