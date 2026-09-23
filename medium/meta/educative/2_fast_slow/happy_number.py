"""
Happy Number - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/happy-number

Determine if a number n is "happy". A happy number is one where repeatedly
replacing it with the sum of the squares of its digits eventually reaches 1.
If it loops in a cycle that doesn't include 1, it's not happy.

KEY INSIGHT:
Treat the digit-square-sum transformation as a linked list (each value is a
"node" pointing to the next). Use Floyd's cycle detection. If the cycle
contains 1, it's happy; otherwise, the slow and fast pointers meet at some
non-1 value.

Examples:
    19 -> True (19 -> 82 -> 68 -> 100 -> 1)
    2 -> False (2 -> 4 -> 16 -> 37 -> 58 -> 89 -> 145 -> 42 -> 20 -> 4...)

Constraints:
- 1 <= n <= 2^31 - 1
"""

import copy
import sys

sys.setrecursionlimit(100000)


# ============================================================
# Helper: sum of squares of digits
# ============================================================
def sum_sq_digits(n):
    total = 0
    while n > 0:
        d = n % 10
        total += d * d
        n //= 10
    return total


# ============================================================
# Way 1: Floyd's cycle detection (BEST - Memorize!)
# ============================================================
def is_happy_1(n):
    """Slow = next(n). Fast = next(next(n)). If they meet, n isn't happy.
    If they meet at 1, n is happy."""
    def next_val(x):
        return sum_sq_digits(x)
    slow = next_val(n)
    fast = next_val(next_val(n))
    while slow != fast:
        slow = next_val(slow)
        fast = next_val(next_val(fast))
    return slow == 1


# ============================================================
# Way 2: Hash set
# ============================================================
def is_happy_2(n):
    """Track visited values; if we revisit without reaching 1, not happy."""
    seen = set()
    while n != 1:
        if n in seen:
            return False
        seen.add(n)
        n = sum_sq_digits(n)
    return True


# ============================================================
# Way 3: Recursive
# ============================================================
def is_happy_3(n, seen=None):
    """Recursive check with memoization."""
    if seen is None:
        seen = set()
    if n == 1:
        return True
    if n == 0:
        return False  # 0 -> 0 forever
    if n in seen:
        return False
    seen.add(n)
    return is_happy_3(sum_sq_digits(n), seen)


# ============================================================
# Way 4: Cache-friendly version
# ============================================================
def is_happy_4(n):
    """Same as Way 1 but with explicit caching of next_val."""
    cache = {}

    def next_val(x):
        if x in cache:
            return cache[x]
        s = sum_sq_digits(x)
        cache[x] = s
        return s

    slow = next_val(n)
    fast = next_val(next_val(n))
    while slow != fast:
        slow = next_val(slow)
        fast = next_val(next_val(fast))
    return slow == 1


# ============================================================
# Way 5: Walk until 1 or repeat
# ============================================================
def is_happy_5(n):
    """Walk forward until 1 or repeat."""
    seen = {n}
    while n != 1:
        n = sum_sq_digits(n)
        if n in seen:
            return False
        seen.add(n)
    return True


# ============================================================
# Way 6: Detect cycle start, check if it's 1
# ============================================================
def is_happy_6(n):
    """Floyd's with explicit cycle-entry detection."""
    def nxt(x):
        return sum_sq_digits(x)
    slow = fast = n
    while True:
        slow = nxt(slow)
        fast = nxt(nxt(fast))
        if slow == fast:
            break
    return slow == 1


# ============================================================
# Way 7: Counter-based with bound
# ============================================================
def is_happy_7(n):
    """Bound the iterations (max 1000)."""
    for _ in range(1000):
        if n == 1:
            return True
        n = sum_sq_digits(n)
    return n == 1


# ============================================================
# Way 8: Mathematical cycle detection
# ============================================================
def is_happy_8(n):
    """All non-happy numbers eventually reach the cycle [4, 16, 37, 58, 89, 145, 42, 20]."""
    known_cycle = {4, 16, 37, 58, 89, 145, 42, 20}
    while n != 1:
        if n in known_cycle:
            return False
        n = sum_sq_digits(n)
    return True


# ============================================================
# Way 9: Class-based
# ============================================================
class HappyChecker_9:
    def __init__(self, n):
        self.n = n

    def is_happy(self):
        def nxt(x):
            return sum_sq_digits(x)
        slow = fast = self.n
        while True:
            slow = nxt(slow)
            fast = nxt(nxt(fast))
            if slow == fast:
                break
        return slow == 1


def is_happy_9(n):
    return HappyChecker_9(n).is_happy()


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def is_happy_10(n):
    """
    THE ONE TO MEMORIZE.

    1. slow = sum_sq_digits(n), fast = sum_sq_digits(sum_sq_digits(n)).
    2. While slow != fast: advance slow 1 step, fast 2 steps.
    3. Return slow == 1.

    Time:  O(log n) per step; bounded by the cycle length (~ 1000 in practice).
    Space: O(1).
    """
    def nxt(x):
        s = 0
        while x:
            d = x % 10
            s += d * d
            x //= 10
        return s

    slow = nxt(n)
    fast = nxt(nxt(n))
    while slow != fast:
        slow = nxt(slow)
        fast = nxt(nxt(fast))
    return slow == 1


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to determine if a number is 'happy' — repeatedly summing squares
of its digits eventually reaches 1."

Key Insight:
"Each digit-square-sum is a deterministic next state. Treat it like a
linked list. If the sequence eventually reaches 1, it's happy. If it
gets stuck in a cycle that doesn't include 1, it's not. Use Floyd's
cycle detection: slow and fast pointers; if they meet, there's a cycle;
check if the meeting point is 1."

Algorithm:
1. slow = next(n), fast = next(next(n)).
2. While slow != fast: slow = next(slow), fast = next(next(fast)).
3. Return slow == 1.

Edge Cases:
- n == 1: True.
- Single digit non-1: loop to a known cycle.
- Repeated cycle: detected by Floyd's.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Floyd's   | O(log n)| O(1)  |
| Hash set  | O(log n)| O(log n)|
+-----------+--------+--------+

KEY TRICK:
Don't try to track all visited values — Floyd's gives O(1) space.

RELATED PROBLEMS:
- Linked List Cycle (LC 141).
- Find Duplicate Number (LC 287).
- Ugly Number (LC 263).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        # (input, expected, description)
        (19, True, "Standard happy"),
        (2, False, "Standard not happy"),
        (1, True, "Single 1"),
        (7, True, "Another happy"),
        (10, True, "10 -> 1"),
        (11, False, "11 -> 2 -> 4 -> ..."),
        (23, True, "23 is happy"),
        (4, False, "4 starts the cycle"),
        (100, True, "100 -> 1"),
        (999, False, "Big non-happy"),
    ]

    implementations = [
        ("Way 1: Floyd's (BEST)", is_happy_1),
        ("Way 2: Hash set", is_happy_2),
        ("Way 3: Recursive", is_happy_3),
        ("Way 4: Cached next", is_happy_4),
        ("Way 5: Set walk", is_happy_5),
        ("Way 6: Detect cycle start", is_happy_6),
        ("Way 7: Bounded loop", is_happy_7),
        ("Way 8: Known cycle", is_happy_8),
        ("Way 9: Class-based", is_happy_9),
        ("Way 10: Final cleanest", is_happy_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for n, expected, desc in test_cases:
            try:
                result = fn(n)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: n={n} expected={expected} got={result}")
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
