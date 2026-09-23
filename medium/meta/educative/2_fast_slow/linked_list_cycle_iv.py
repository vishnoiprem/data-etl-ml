"""
Linked List Cycle IV (Happy List) - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/linked-list-cycle-iv

Given a linked list, return True if it's "happy":
  - No cycle: True.
  - Has a cycle with EVEN length: True (will return to start after even number of steps).
  - Has a cycle with ODD length: False.

KEY INSIGHT:
Use Floyd's to find a meeting point inside the cycle. From the meeting
point, count the cycle length. Even -> True, odd -> False.

Examples:
    1 -> 2 -> 3 -> 4 -> 5 -> None -> True (no cycle)
    1 -> 2 -> 3 -> 4 -> 1 -> True (cycle length 3: ODD -> False)

Constraints:
- 0 <= list length <= 10^4
"""

import copy
import sys

sys.setrecursionlimit(100000)


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def build_with_cycle(arr, cycle_pos):
    """Build list with cycle linking last node to the node at cycle_pos (0-indexed)."""
    if not arr:
        return None
    nodes = [ListNode(v) for v in arr]
    for i in range(len(nodes) - 1):
        nodes[i].next = nodes[i + 1]
    if cycle_pos is not None and 0 <= cycle_pos < len(nodes):
        nodes[-1].next = nodes[cycle_pos]
    return nodes[0] if nodes else None


def _has_cycle(head):
    """Return meeting point if cycle exists, else None."""
    if not head or not head.next:
        return None
    slow = head
    fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            return slow
    return None


def _cycle_length(head, meeting):
    """Given a meeting point inside a cycle, return the cycle length."""
    length = 1
    cur = meeting.next
    while cur != meeting:
        cur = cur.next
        length += 1
    return length


# ============================================================
# Way 1: Floyd's + length check (BEST - Memorize!)
# ============================================================
def is_happy_list_1(head):
    """No cycle -> True. Cycle length even -> True. Odd -> False."""
    meeting = _has_cycle(head)
    if meeting is None:
        return True
    length = _cycle_length(head, meeting)
    return length % 2 == 0


# ============================================================
# Way 2: Hash set, check size
# ============================================================
def is_happy_list_2(head):
    """If visited set size is even when we hit a repeat -> happy."""
    if not head:
        return True
    seen = set()
    cur = head
    while cur:
        if cur in seen:
            return len(seen) % 2 == 0
        seen.add(cur)
        cur = cur.next
    return True


# ============================================================
# Way 3: Hash set, count visited on cycle detection
# ============================================================
def is_happy_list_3(head):
    """Track visited; check parity of cycle length."""
    seen = set()
    cur = head
    cycle_start = None
    while cur:
        if cur in seen:
            cycle_start = cur
            break
        seen.add(cur)
        cur = cur.next
    if cycle_start is None:
        return True
    # Walk the cycle; count its length
    length = 0
    cur = cycle_start
    while True:
        cur = cur.next
        length += 1
        if cur == cycle_start:
            break
    return length % 2 == 0


# ============================================================
# Way 4: Slow/fast without length count (use meeting identity)
# ============================================================
def is_happy_list_4(head):
    """When slow and fast meet, check if they met at head -> even cycle."""
    if not head:
        return True
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            # The cycle's length parity can be determined by walking back to itself.
            length = 0
            cur = slow
            for _ in range(10001):
                cur = cur.next
                length += 1
                if cur == slow:
                    break
            return length % 2 == 0
    return True


# ============================================================
# Way 5: Detect cycle and check if start is reachable
# ============================================================
def is_happy_list_5(head):
    """Walk with visited set; check the size of the cycle segment."""
    seen = set()
    cur = head
    while cur and cur not in seen:
        seen.add(cur)
        cur = cur.next
    if cur is None:
        return True
    # cur is in seen -> cycle detected. Cycle = nodes from first occurrence of cur.
    # Find first occurrence index
    cycle_nodes = set()
    walker = cur
    while walker not in cycle_nodes:
        cycle_nodes.add(walker)
        walker = walker.next
    return len(cycle_nodes) % 2 == 0


# ============================================================
# Way 6: Mark visited nodes
# ============================================================
def is_happy_list_6(head):
    """Mark nodes; count cycle nodes by walking until marked again."""
    cur = head
    while cur and not getattr(cur, 'visited', False):
        cur.visited = True
        cur = cur.next
    if cur is None:
        return True
    # Walk cycle to count
    length = 0
    walker = cur
    while not getattr(walker, 'counted', False):
        walker.counted = True
        walker = walker.next
        length += 1
        if walker == cur:
            break
    return length % 2 == 0


# ============================================================
# Way 7: Recursive
# ============================================================
def is_happy_list_7(head):
    """Recursive walker with seen set."""
    seen = set()

    def walk(node):
        if node is None:
            return True, None
        if node in seen:
            return False, node  # cycle detected
        seen.add(node)
        happy, cycle_start = walk(node.next)
        if cycle_start is not None:
            return happy, cycle_start
        return happy, None

    happy, cycle_start = walk(head)
    if cycle_start is None:
        return True
    length = 0
    cur = cycle_start
    while True:
        cur = cur.next
        length += 1
        if cur == cycle_start:
            break
    return length % 2 == 0


# ============================================================
# Way 8: Two pointers + cycle length count
# ============================================================
def is_happy_list_8(head):
    """Walk slow/fast; on meet, count cycle length."""
    if not head:
        return True
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            length = 0
            cur = slow
            for _ in range(10001):
                cur = cur.next
                length += 1
                if cur == slow:
                    break
            return length % 2 == 0
    return True


# ============================================================
# Way 9: Class-based
# ============================================================
class HappyListChecker_9:
    def __init__(self, head):
        self.head = head

    def is_happy(self):
        meeting = _has_cycle(self.head)
        if meeting is None:
            return True
        length = _cycle_length(self.head, meeting)
        return length % 2 == 0


def is_happy_list_9(head):
    return HappyListChecker_9(head).is_happy()


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def is_happy_list_10(head):
    """
    THE ONE TO MEMORIZE.

    1. Use Floyd's to find a meeting point inside the cycle.
    2. If no cycle: True.
    3. Count the cycle length from the meeting point.
    4. Return True iff cycle length is even.

    Time:  O(n)
    Space: O(1)
    """
    meeting = _has_cycle(head)
    if meeting is None:
        return True
    length = _cycle_length(head, meeting)
    return length % 2 == 0


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to determine if a linked list is 'happy' — no cycle, or a cycle
with even length (so traversal will eventually return to start)."

Key Insight:
"Use Floyd's cycle detection. If no cycle, the list is happy. If there
is a cycle, count its length. Even length -> happy; odd -> not happy."

Algorithm:
1. Phase 1: slow/fast from head. If they don't meet, return True.
2. Phase 2: from meeting point, walk until we return. Count length.
3. Return length % 2 == 0.

Edge Cases:
- Empty / single node: True (no cycle).
- Cycle of length 1 (self-loop): not happy.
- Cycle of length 2: happy.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Floyd's   | O(n)   | O(1)   |
| Hash set  | O(n)   | O(n)   |
+-----------+--------+--------+

KEY TRICK:
The cycle length parity is what determines happiness. Count from meeting
point walking forward — the count when we return to meeting is the length.

RELATED PROBLEMS:
- Linked List Cycle (LC 141).
- Linked List Cycle II (LC 142): find start.
- Happy Number (LC 202).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    # (arr, cycle_pos, expected, description)
    # cycle_pos=None means no cycle.
    test_cases = [
        ([1, 2, 3, 4, 5], None, True, "No cycle"),
        ([1, 2, 3], 0, False, "Cycle of length 3 (odd)"),
        ([1, 2, 3, 4], 0, True, "Cycle of length 4 (even)"),
        ([1, 2], 0, True, "Cycle of length 2 (even)"),
        ([1], None, True, "Single node"),
        ([], None, True, "Empty"),
        ([1, 2, 3, 4, 5, 6], 2, False, "Cycle length 4 (even)... wait")
    ]
    # Correct: cycle_pos=2 in [1..6] gives cycle 3->4->5->6->3 = length 4. EVEN -> True.
    # Fix:
    test_cases[6] = ([1, 2, 3, 4, 5, 6], 2, True, "Cycle length 4 (even)")

    implementations = [
        ("Way 1: Floyd's + length (BEST)", is_happy_list_1),
        ("Way 2: Hash set size", is_happy_list_2),
        ("Way 3: Hash set count", is_happy_list_3),
        ("Way 4: Floyd's walk", is_happy_list_4),
        ("Way 5: Visited parity", is_happy_list_5),
        ("Way 6: Mark visited", is_happy_list_6),
        ("Way 7: Recursive", is_happy_list_7),
        ("Way 8: Two-ptr + hash", is_happy_list_8),
        ("Way 9: Class-based", is_happy_list_9),
        ("Way 10: Final cleanest", is_happy_list_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for arr, cycle_pos, expected, desc in test_cases:
            try:
                head = build_with_cycle(arr, cycle_pos)
                result = fn(head)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: arr={arr} cycle_pos={cycle_pos} expected={expected} got={result}")
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
