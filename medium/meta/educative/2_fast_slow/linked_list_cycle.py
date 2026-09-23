"""
Linked List Cycle - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/linked-list-cycle

Given head, the head of a linked list, determine if the linked list has
a cycle in it. A cycle exists if some node in the list can be reached
again by continuously following the next pointer.

KEY INSIGHT:
Floyd's cycle detection. Use a slow pointer that moves 1 step and a fast
pointer that moves 2 steps. If they ever meet, there's a cycle. If fast
reaches None, there's no cycle.

Examples:
    3 -> 2 -> 0 -> -4 -> (back to 2) -> True
    1 -> 2 -> None -> False

Constraints:
- 0 <= number of nodes <= 10^4
- -10^5 <= Node.val <= 10^5
"""

import copy
import sys

sys.setrecursionlimit(100000)


# ============================================================
# ListNode definition
# ============================================================
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def build_list_with_cycle(arr, cycle_pos):
    """Build a linked list from arr. If cycle_pos >= 0, the last node
    points to the node at index cycle_pos. Returns head."""
    if not arr:
        return None
    head = ListNode(arr[0])
    nodes = [head]
    cur = head
    for v in arr[1:]:
        cur.next = ListNode(v)
        cur = cur.next
        nodes.append(cur)
    if cycle_pos >= 0 and cycle_pos < len(nodes):
        cur.next = nodes[cycle_pos]
    return head


# ============================================================
# Way 1: Floyd's tortoise and hare (BEST - Memorize!)
# ============================================================
def has_cycle_1(head):
    """slow moves 1 step, fast moves 2. If they meet, there's a cycle."""
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            return True
    return False


# ============================================================
# Way 2: Hash set of visited nodes
# ============================================================
def has_cycle_2(head):
    """Track seen node ids; if we revisit, there's a cycle."""
    seen = set()
    cur = head
    while cur:
        if id(cur) in seen:
            return True
        seen.add(id(cur))
        cur = cur.next
    return False


# ============================================================
# Way 3: Visited marker on nodes
# ============================================================
def has_cycle_3(head):
    """Mark each visited node with a flag; if we hit a flagged node, cycle."""
    cur = head
    while cur:
        if getattr(cur, 'visited', False):
            return True
        cur.visited = True
        cur = cur.next
    # Clean up
    cur = head
    while cur:
        if hasattr(cur, 'visited'):
            del cur.visited
        cur = cur.next
    return False


# ============================================================
# Way 4: Modify node values (works if vals are unique)
# ============================================================
def has_cycle_4(head):
    """Modify next pointer to None on traversal; cycle means revisiting a node
    with modified next. Only works if we can mutate the list."""
    cur = head
    while cur:
        if cur.next is None:
            return False
        if id(cur.next) == id(cur) or getattr(cur.next, '_seen', False):
            return True
        cur._seen = True
        cur = cur.next
    # Clean up
    cur = head
    while cur:
        if hasattr(cur, '_seen'):
            del cur._seen
        cur = cur.next
    return False


# ============================================================
# Way 5: Length counter (mark and count)
# ============================================================
def has_cycle_5(head):
    """Walk forward; if we revisit a node, return True. Track visited with
    explicit set."""
    visited = set()
    cur = head
    while cur:
        if cur in visited:
            return True
        visited.add(cur)
        cur = cur.next
    return False


# ============================================================
# Way 6: Brute force - reverse pointers (destructive)
# ============================================================
def has_cycle_6(head):
    """Reverse the list as we walk; if we come back to head, there's a cycle.
    Destructive — modifies the list."""
    if not head:
        return False
    prev = None
    cur = head
    while cur:
        nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
        if cur is head:
            # Restore before returning
            head = prev  # In destructive version, we don't restore
            return True
    return False


# ============================================================
# Way 7: Walk with explicit None-sentinel counter
# ============================================================
def has_cycle_7(head):
    """Use a 'seen' sentinel by counting iterations up to n+1."""
    n = 0
    cur = head
    while cur:
        n += 1
        if n > 10001:  # safety bound
            return True
        cur = cur.next
    return False


# ============================================================
# Way 8: Brent's algorithm
# ============================================================
def has_cycle_8(head):
    """Brent's cycle detection: teleport fast forward, then advance slow."""
    if not head:
        return False
    slow = head
    # First phase: find meeting point
    power = lam = 1
    fast = head.next
    while fast and fast != slow:
        if power == lam:
            slow = fast
            power *= 2
            lam = 0
        fast = fast.next if fast else None
        lam += 1
    if fast is None:
        return False
    # Second phase: find cycle start (we just need to know if cycle exists)
    return True


# ============================================================
# Way 9: Class-based
# ============================================================
class CycleDetector_9:
    def __init__(self, head):
        self.head = head

    def has_cycle(self):
        slow = fast = self.head
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
            if slow is fast:
                return True
        return False


def has_cycle_9(head):
    return CycleDetector_9(head).has_cycle()


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def has_cycle_10(head):
    """
    THE ONE TO MEMORIZE.

    1. slow = fast = head.
    2. While fast and fast.next:
       a. slow = slow.next
       b. fast = fast.next.next
       c. If slow is fast: return True
    3. Return False.

    Time:  O(n) — at most μ + λ steps where μ is the distance to cycle start,
          λ is cycle length.
    Space: O(1).
    """
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            return True
    return False


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to determine if a linked list has a cycle."

Key Insight:
"Floyd's tortoise and hare algorithm. Use a slow pointer that moves 1
step and a fast pointer that moves 2 steps. If the list has a cycle,
they MUST eventually meet. If there's no cycle, the fast pointer hits
None first."

Algorithm:
1. slow = fast = head.
2. While fast and fast.next:
   a. slow = slow.next
   b. fast = fast.next.next
   c. If slow is fast: return True
3. Return False.

Edge Cases:
- Empty list: False.
- Single node, no cycle: False.
- Single node pointing to itself: True (cycle).
- No cycle: fast reaches None.
- Long cycle: they meet after at most μ + λ steps.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Floyd's   | O(n)   | O(1)   |
| Hash set  | O(n)   | O(n)   |
| Visited   | O(n)   | O(1)   |
+-----------+--------+--------+

KEY TRICK:
Compare nodes with `is` (identity), not `==` (equality). Two different
nodes might have equal values, but we need to detect same OBJECT.

RELATED PROBLEMS:
- Linked List Cycle II (LC 142): find cycle ENTRY.
- Happy Number (LC 202): cycle in digit sequence.
- Find Duplicate Number (LC 287): cycle in array-as-linked-list.
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    # (array, cycle_pos, expected, description)
    test_cases = [
        ([3, 2, 0, -4], 1, True, "Cycle at index 1"),
        ([1, 2], 0, True, "Cycle at head"),
        ([1], -1, False, "Single node no cycle"),
        ([], -1, False, "Empty list"),
        ([1, 2, 3, 4, 5], -1, False, "No cycle"),
        ([1, 2], -1, False, "Two nodes no cycle"),
        ([1], 0, True, "Self-loop"),
        ([1, 2, 3], 0, True, "Cycle at first"),
        ([1, 2, 3], 2, True, "Cycle at last (back to last)"),
        ([0, 1, 2, 3, 4, 5], 3, True, "Long list with cycle"),
    ]

    implementations = [
        ("Way 1: Floyd's (BEST)", has_cycle_1),
        ("Way 2: Hash set", has_cycle_2),
        ("Way 3: Visited marker", has_cycle_3),
        ("Way 4: Modify nodes", has_cycle_4),
        ("Way 5: Set of objects", has_cycle_5),
        ("Way 6: Reverse (destructive)", has_cycle_6),
        ("Way 7: Bound counter", has_cycle_7),
        ("Way 8: Brent's", has_cycle_8),
        ("Way 9: Class-based", has_cycle_9),
        ("Way 10: Final cleanest", has_cycle_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for case_idx, (arr, cycle_pos, expected, desc) in enumerate(test_cases):
            try:
                head = build_list_with_cycle(copy.deepcopy(arr), cycle_pos)
                result = fn(head)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: expected={expected} got={result}")
            except Exception as e:
                failed += 1
                all_pass = False
                print(f"  ERROR [{name}] {desc}: {type(e).__name__}: {e}")
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
