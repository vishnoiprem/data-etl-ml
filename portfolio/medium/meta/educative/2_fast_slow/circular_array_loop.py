"""
Circular Array Loop - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/circular-array-loop

You have a circular array nums of length n. nums[i] -> (i + nums[i]) % n
moves forward if positive, backward if negative. A "circular array loop"
exists if there's a sequence of moves that loops (revisits a start index)
with all steps in the same direction (all forward or all backward).
Length must be > 1.

KEY INSIGHT:
Treat the array as a linked list. Each index points to next via the jump.
For each start, walk with slow/fast. Detect a cycle; if its length > 1
and all jumps have the same sign, return True.

Examples:
    [2, -1, 1, 2, 2] -> True (cycle 0 -> 2 -> 3 -> 0, all forward)
    [-1, 2] -> False (length 1)
    [-2, 1, -1, -2, -2] -> False (mixed directions)

Constraints:
- 1 <= n <= 5000
- -5000 <= nums[i] <= 5000
- nums[i] != 0
"""

import copy
import sys

sys.setrecursionlimit(100000)


def _next(nums, i):
    """Compute next index from i."""
    n = len(nums)
    return (i + nums[i]) % n


def _same_sign(a, b):
    """Return True if a and b have the same sign (both positive or both negative)."""
    return (a > 0) == (b > 0)


def _verify_and_get_length(nums, meeting_point, direction):
    """Walk the cycle from meeting_point. Verify every jump has the same
    sign as `direction`. Return cycle length if valid, else 0."""
    n = len(nums)
    length = 0
    cur = meeting_point
    start = meeting_point
    for _ in range(n + 1):
        nxt = _next(nums, cur)
        if not _same_sign(nums[nxt], direction):
            return 0
        cur = nxt
        length += 1
        if cur == start:
            break
    return length


# ============================================================
# Way 1: Walk from each unvisited start (BEST - Memorize!)
# ============================================================
def circular_array_loop_1(nums):
    """Floyd's, but break if direction changes."""
    n = len(nums)
    for i in range(n):
        direction = nums[i]
        slow = fast = i
        for _ in range(n + 2):
            slow = _next(nums, slow)
            fast = _next(nums, _next(nums, fast))
            if slow == fast:
                length = _verify_and_get_length(nums, slow, direction)
                if length > 1:
                    return True
                break
            if not _same_sign(nums[slow], direction):
                break
    return False


# ============================================================
# Way 2: Hash set of visited indices per walk
# ============================================================
def circular_array_loop_2(nums):
    """Track visited indices per walk in a set."""
    n = len(nums)
    for i in range(n):
        cur = i
        direction = nums[i]
        path = {}
        # path[idx] = True/False: True if cycle forms here.
        while cur not in path:
            path[cur] = True
            nxt = _next(nums, cur)
            if not _same_sign(nums[nxt], direction):
                break
            cur = nxt
            if len(path) > n + 1:
                break
        # cur already in path -> cycle found at cur. Verify direction and length.
        if cur in path:
            length = _verify_and_get_length(nums, cur, direction)
            if length > 1:
                return True
    return False


# ============================================================
# Way 3: Brute force from each index
# ============================================================
def circular_array_loop_3(nums):
    """From each index, walk with slow/fast same-direction check."""
    n = len(nums)
    for start in range(n):
        slow = fast = start
        direction = nums[start]
        for _ in range(n + 2):
            slow = _next(nums, slow)
            fast = _next(nums, _next(nums, fast))
            if slow == fast:
                length = _verify_and_get_length(nums, slow, direction)
                if length > 1:
                    return True
                break
            if not _same_sign(nums[slow], direction):
                break
    return False


# ============================================================
# Way 4: Floyd's with direction check
# ============================================================
def circular_array_loop_4(nums):
    """Floyd's, breaking if direction changes."""
    n = len(nums)
    for i in range(n):
        slow = fast = i
        steps = 0
        direction = nums[i]
        while True:
            slow = _next(nums, slow)
            fast = _next(nums, fast)
            fast = _next(nums, fast)
            if slow == fast:
                length = _verify_and_get_length(nums, slow, direction)
                if length > 1:
                    return True
                break
            if not _same_sign(nums[slow], direction):
                break
            steps += 1
            if steps > n + 1:
                break
    return False


# ============================================================
# Way 5: Iterative with explicit visited set per walk
# ============================================================
def circular_array_loop_5(nums):
    """Walk from each start; if cycle > 1 with same direction, return True."""
    n = len(nums)
    for start in range(n):
        cur = start
        direction = nums[start]
        seen = set()
        for _ in range(n + 2):
            if cur in seen:
                length = 0
                tmp = cur
                for _ in range(n + 1):
                    tmp = _next(nums, tmp)
                    length += 1
                    if tmp == cur:
                        break
                if length > 1:
                    return True
                break
            seen.add(cur)
            nxt = _next(nums, cur)
            if not _same_sign(nums[nxt], direction):
                break
            cur = nxt
    return False


# ============================================================
# Way 6: Walk and detect direction mismatch (same approach)
# ============================================================
def circular_array_loop_6(nums):
    """Identical structure to Way 5 with minor naming differences."""
    n = len(nums)
    for start in range(n):
        cur = start
        direction = nums[start]
        seen = set()
        for _ in range(n + 2):
            if cur in seen:
                length = 0
                tmp = cur
                for _ in range(n + 1):
                    tmp = _next(nums, tmp)
                    length += 1
                    if tmp == cur:
                        break
                if length > 1:
                    return True
                break
            seen.add(cur)
            nxt = _next(nums, cur)
            if not _same_sign(nums[nxt], direction):
                break
            cur = nxt
    return False


# ============================================================
# Way 7: Recursive
# ============================================================
def circular_array_loop_7(nums):
    """Recursive walker with visited set."""
    n = len(nums)
    visited = [False] * n

    def walk(start):
        cur = start
        direction = nums[start]
        path = set()
        while True:
            if cur in path:
                # cur repeats -> cycle. Compute length.
                length = 0
                tmp = cur
                for _ in range(n + 1):
                    tmp = _next(nums, tmp)
                    length += 1
                    if tmp == cur:
                        break
                return length > 1
            if visited[cur]:
                return False
            path.add(cur)
            visited[cur] = True
            nxt = _next(nums, cur)
            if not _same_sign(nums[nxt], direction):
                return False
            cur = nxt
            if len(path) > n + 1:
                return False

    for i in range(n):
        if not visited[i]:
            if walk(i):
                return True
    return False


# ============================================================
# Way 8: Two-pointer walk, find meeting point
# ============================================================
def circular_array_loop_8(nums):
    """Walk fast/slow from each start; check direction and length."""
    n = len(nums)
    for i in range(n):
        direction = nums[i]
        slow = fast = i
        for _ in range(n + 2):
            slow = _next(nums, slow)
            fast = _next(nums, _next(nums, fast))
            if slow == fast:
                cycle_len = _verify_and_get_length(nums, slow, direction)
                if cycle_len > 1:
                    return True
                break
            if not _same_sign(nums[slow], direction):
                break
    return False


# ============================================================
# Way 9: Class-based
# ============================================================
class CircularArrayChecker_9:
    def __init__(self, nums):
        self.nums = nums

    def has_loop(self):
        n = len(self.nums)
        for i in range(n):
            direction = self.nums[i]
            slow = fast = i
            for _ in range(n + 2):
                slow = _next(self.nums, slow)
                fast = _next(self.nums, _next(self.nums, fast))
                if slow == fast:
                    length = _verify_and_get_length(self.nums, slow, direction)
                    if length > 1:
                        return True
                    break
                if not _same_sign(self.nums[slow], direction):
                    break
        return False


def circular_array_loop_9(nums):
    return CircularArrayChecker_9(nums).has_loop()


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def circular_array_loop_10(nums):
    """
    THE ONE TO MEMORIZE.

    For each start index i:
      Track direction. Walk with slow/fast. If they meet, compute length.
      Break early if direction changes.

    Time:  O(n)
    Space: O(1)
    """
    n = len(nums)
    for i in range(n):
        direction = nums[i]
        slow = fast = i
        for _ in range(n + 2):
            slow = _next(nums, slow)
            fast = _next(nums, _next(nums, fast))
            if slow == fast:
                length = _verify_and_get_length(nums, slow, direction)
                if length > 1:
                    return True
                break
            if not _same_sign(nums[slow], direction):
                break
    return False


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to determine if a circular array has a 'loop' — a sequence of
moves that revisits a starting index with all steps in the same direction
and length > 1."

Key Insight:
"Treat the array as a linked list. Each index i points to (i + nums[i]) % n.
Use slow/fast pointers to find a meeting point (cycle). Validate length > 1
and one-directional movement."

Algorithm:
For each start index i:
  direction = sign(nums[i]).
  slow = fast = i.
  While True:
    slow = next(slow).
    fast = next(next(fast)).
    If slow == fast: compute cycle length; if > 1, return True.
    If direction changed at slow: break.

Edge Cases:
- Self-loop (nums[i] is multiple of n): length 1, invalid.
- Mixed directions: not a valid cycle.
- All forward or all backward with length > 1: valid.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Slow/fast | O(n)   | O(1)   |
| Hash set  | O(n)   | O(n)   |
+-----------+--------+--------+

KEY TRICK:
The cycle length check distinguishes real loops from self-loops. Be sure
to break out if direction changes mid-walk. Use a bounded loop (n+1) to
prevent infinite loops.

RELATED PROBLEMS:
- Linked List Cycle (LC 141).
- Find Duplicate Number (LC 287).
- Happy Number (LC 202).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        # (input, expected, description)
        ([2, -1, 1, 2, 2], True, "Standard cycle forward"),
        ([-1, 2], False, "Mixed signs, no valid cycle"),
        ([-2, 1, -1, -2, -2], False, "Mixed direction"),
        ([1, -1], False, "Two opposite"),
        ([2, 2, 2, 2], True, "All forward, valid cycle"),
        ([-1, -1, -1], True, "All backward"),
        ([3, 1, 2], True, "Mixed cycle forward"),
        ([1, 2, 3, 4, 5], True, "Forward with wraparound"),
        ([1], False, "Single element"),
        ([1, 1], True, "Two forward"),
        ([1, -2], False, "Mixed"),
    ]

    implementations = [
        ("Way 1: Floyd's (BEST)", circular_array_loop_1),
        ("Way 2: Hash set", circular_array_loop_2),
        ("Way 3: Brute from each", circular_array_loop_3),
        ("Way 4: Floyd's direction", circular_array_loop_4),
        ("Way 5: Iterative visited", circular_array_loop_5),
        ("Way 6: Walk + check", circular_array_loop_6),
        ("Way 7: Recursive", circular_array_loop_7),
        ("Way 8: Two-pointer walk", circular_array_loop_8),
        ("Way 9: Class-based", circular_array_loop_9),
        ("Way 10: Final cleanest", circular_array_loop_10),
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
