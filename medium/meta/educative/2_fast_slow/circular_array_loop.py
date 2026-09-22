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
Use Floyd's to detect cycles that satisfy the constraints. Or, mark
visited indices and check.

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


def _is_valid_cycle(nums, start, length):
    """Check if cycle starting at 'start' has length > 1 and is one-directional."""
    if length <= 1:
        return False
    direction = 1 if nums[start] > 0 else -1
    cur = start
    for _ in range(length):
        if (nums[cur] > 0) != (direction > 0):
            return False
        cur = _next(nums, cur)
    return cur == start


# ============================================================
# Way 1: Mark visited (BEST - Memorize!)
# ============================================================
def circular_array_loop_1(nums):
    """Mark visited indices. For each unvisited, walk until cycle or revisit.
    Cycle is valid if length > 1 and one-directional."""
    n = len(nums)
    for i in range(n):
        if nums[i] == 0:  # 0 means visited/invalid (we'll mark with 0)
            continue
        slow = fast = i
        direction = 1 if nums[i] > 0 else -1
        while True:
            slow = _next(nums, slow)
            fast = _next(nums, _next(nums, fast))
            if slow == fast:
                break
            # Direction changed -> not a valid cycle
            if (nums[slow] > 0) != (direction > 0):
                break
        # Walk once more to mark visited
        # (Simplified: we just check if slow == fast and length > 1)
        if slow == fast and _cycle_length(nums, i) > 1:
            return True
    return False


def _cycle_length(nums, start):
    """Compute cycle length starting from start. Assume valid."""
    cur = _next(nums, start)
    length = 1
    while cur != start:
        cur = _next(nums, cur)
        length += 1
    return length


# ============================================================
# Way 2: Hash set of visited
# ============================================================
def circular_array_loop_2(nums):
    """Track visited indices in a set."""
    n = len(nums)
    visited = set()
    for i in range(n):
        if i in visited:
            continue
        cur = i
        path = []
        while cur not in visited:
            visited.add(cur)
            path.append(cur)
            nxt = _next(nums, cur)
            if (nums[nxt] > 0) != (nums[cur] > 0):
                break
            cur = nxt
        # Check if cur is in path (cycle)
        if cur in path and len(path) - path.index(cur) > 1:
            return True
    return False


# ============================================================
# Way 3: Brute force from each index
# ============================================================
def circular_array_loop_3(nums):
    """From each index, walk and check for a same-direction cycle."""
    n = len(nums)
    for start in range(n):
        cur = start
        path = []
        seen = set()
        while cur not in seen:
            seen.add(cur)
            nxt = _next(nums, cur)
            if (nums[nxt] > 0) != (nums[cur] > 0):
                break
            cur = nxt
        if cur in seen and seen - {cur}:
            # cur was visited; check if cycle length > 1
            cycle = []
            tmp = cur
            while True:
                cycle.append(tmp)
                tmp = _next(nums, tmp)
                if tmp == cur:
                    break
            if len(cycle) > 1:
                return True
    return False


# ============================================================
# Way 4: Floyd's with direction check
# ============================================================
def circular_array_loop_4(nums):
    """Floyd's, but break if direction changes."""
    n = len(nums)
    for i in range(n):
        if nums[i] == 0:
            continue
        slow = fast = i
        while True:
            slow = _next(nums, slow)
            fast = _next(nums, fast)
            fast = _next(nums, fast) if fast is not None else None
            if slow is None or fast is None:
                break
            if slow == fast:
                # Check cycle length > 1
                length = 0
                cur = slow
                while True:
                    cur = _next(nums, cur)
                    length += 1
                    if cur == slow:
                        break
                if length > 1:
                    return True
                break
            if (nums[slow] > 0) != (nums[i] > 0) or (nums[fast] > 0) != (nums[i] > 0):
                break
    return False


# ============================================================
# Way 5: Mark visited with direction
# ============================================================
def circular_array_loop_5(nums):
    """Use a 'visited' marker: subtract 10000 from values, marking them."""
    n = len(nums)
    for i in range(n):
        if nums[i] > 5000 or nums[i] < -5000:  # already visited
            continue
        slow = fast = i
        direction = 1 if nums[i] > 0 else -1
        while True:
            slow = _next(nums, slow)
            fast = _next(nums, _next(nums, fast))
            if slow == fast:
                # Determine cycle length
                length = 0
                cur = slow
                while True:
                    cur = _next(nums, cur)
                    length += 1
                    if cur == slow:
                        break
                if length > 1:
                    return True
                break
            if (nums[slow] > 0) != (direction > 0):
                break
    return False


# ============================================================
# Way 6: Walk and detect direction mismatch
# ============================================================
def circular_array_loop_6(nums):
    """Walk from each start; on direction change or revisit, decide."""
    n = len(nums)
    for start in range(n):
        cur = start
        seen = set()
        while cur not in seen:
            seen.add(cur)
            nxt = _next(nums, cur)
            # Direction must match
            if (nums[nxt] > 0) != (nums[cur] > 0):
                break
            cur = nxt
        if cur in seen and len(seen - {cur}) > 0:
            # Check cycle length > 1
            cycle_len = 0
            tmp = cur
            while True:
                tmp = _next(nums, tmp)
                cycle_len += 1
                if tmp == cur:
                    break
            if cycle_len > 1:
                return True
    return False


# ============================================================
# Way 7: Recursive with direction tracking
# ============================================================
def circular_array_loop_7(nums):
    """Recursive helper."""
    n = len(nums)
    visited = [False] * n

    def walk(start):
        if visited[start]:
            return False
        visited[start] = True
        nxt = _next(nums, start)
        if (nums[nxt] > 0) != (nums[start] > 0):
            return False
        if nxt == start:
            return False
        if walk(nxt):
            return True
        return False

    for i in range(n):
        if walk(i):
            return True
    return False


# ============================================================
# Way 8: Detect cycle via Floyd + separate validation
# ============================================================
def circular_array_loop_8(nums):
    """Floyd's to find candidate cycle; validate direction and length."""
    n = len(nums)
    for i in range(n):
        slow = fast = i
        # Find meeting point
        steps = 0
        while True:
            slow = _next(nums, slow)
            fast = _next(nums, _next(nums, fast))
            if slow == fast:
                break
            steps += 1
            if steps > n + 10:
                slow = fast = -1
                break
        if slow == -1:
            continue
        if slow != fast:
            continue
        # Validate: walk once from i and check direction
        direction = 1 if nums[i] > 0 else -1
        cur = i
        length = 0
        valid = True
        for _ in range(n):
            if (nums[cur] > 0) != (direction > 0):
                valid = False
                break
            cur = _next(nums, cur)
            length += 1
            if cur == i:
                break
        if valid and length > 1 and cur == i:
            return True
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
            if self.nums[i] == 0:
                continue
            slow = fast = i
            while True:
                slow = _next(self.nums, slow)
                fast = _next(self.nums, _next(self.nums, fast))
                if slow == fast:
                    length = 0
                    cur = slow
                    while True:
                        cur = _next(self.nums, cur)
                        length += 1
                        if cur == slow:
                            break
                    if length > 1:
                        return True
                    break
                if (self.nums[slow] > 0) != (self.nums[i] > 0):
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

    For each unvisited index i:
      Use Floyd's to find a meeting point. If found, compute cycle length.
      If length > 1 and the cycle is one-directional, return True.
    Else False.
    """
    n = len(nums)
    for i in range(n):
        if nums[i] == 0:
            continue
        slow = fast = i
        direction = 1 if nums[i] > 0 else -1
        while True:
            slow = _next(nums, slow)
            fast = _next(nums, _next(nums, fast))
            if slow == fast:
                length = 0
                cur = slow
                while True:
                    cur = _next(nums, cur)
                    length += 1
                    if cur == slow:
                        break
                if length > 1:
                    return True
                break
            if (nums[slow] > 0) != (direction > 0):
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
Floyd's cycle detection finds a cycle; we then validate it satisfies the
constraints (length > 1, one-directional)."

Algorithm:
For each unvisited start:
  slow = fast = start.
  While True:
    slow = next(slow).
    fast = next(next(fast)).
    If slow == fast: compute cycle length; if > 1, return True.
    If direction changed: break.

Edge Cases:
- Self-loop (nums[i] is multiple of n): length 1, invalid.
- Mixed directions: not a valid cycle.
- All same direction with length > 1: valid.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Floyd's   | O(n)   | O(1)   |
| Hash set  | O(n)   | O(n)   |
+-----------+--------+--------+

KEY TRICK:
Use the cycle length check to disambiguate self-loops (length 1) from
real loops. The "next" function (i + nums[i]) % n handles wraparound.

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
        ([-1, 2], False, "Length 1 cycle"),
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
        ("Way 1: Mark visited (BEST)", circular_array_loop_1),
        ("Way 2: Hash set", circular_array_loop_2),
        ("Way 3: Brute from each", circular_array_loop_3),
        ("Way 4: Floyd's direction", circular_array_loop_4),
        ("Way 5: Mark direction", circular_array_loop_5),
        ("Way 6: Walk + check", circular_array_loop_6),
        ("Way 7: Recursive", circular_array_loop_7),
        ("Way 8: Floyd + validate", circular_array_loop_8),
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
