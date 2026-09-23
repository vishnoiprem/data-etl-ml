"""
Linked List Cycle III (Cycle Start) - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/linked-list-cycle-iii

Given a linked list, return the node where the cycle begins. If there's no
cycle, return None.

KEY INSIGHT:
Floyd's two-phase algorithm:
  Phase 1: slow/fast pointers find a meeting point inside the cycle.
  Phase 2: Reset one pointer to head. Walk both 1 step at a time. They meet
           at the cycle's entry point.

Mathematical proof: distance from head to cycle start = distance from
meeting point to cycle start (mod cycle length).

Examples:
    1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 3  -> node 3
    1 -> 2 -> 3 -> 4 -> 5 -> 6 -> None -> None

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


def list_from_array(arr):
    if not arr:
        return None
    head = ListNode(arr[0])
    cur = head
    for v in arr[1:]:
        cur.next = ListNode(v)
        cur = cur.next
    return head


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


# ============================================================
# Way 1: Floyd's two-phase (BEST - Memorize!)
# ============================================================
def detect_cycle_start_1(head):
    """Phase 1: find meeting point. Phase 2: find entry."""
    if not head or not head.next:
        return None
    slow = head
    fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            # Phase 2: find cycle start
            ptr = head
            while ptr != slow:
                ptr = ptr.next
                slow = slow.next
            return ptr
    return None


# ============================================================
# Way 2: Hash set of visited nodes
# ============================================================
def detect_cycle_start_2(head):
    """Track visited nodes. First repeated node is the cycle start."""
    seen = set()
    cur = head
    while cur:
        if cur in seen:
            return cur
        seen.add(cur)
        cur = cur.next
    return None


# ============================================================
# Way 3: Hash set of visited node IDs
# ============================================================
def detect_cycle_start_3(head):
    """Same as Way 2 but uses id() to handle custom __hash__ cases."""
    seen = set()
    cur = head
    while cur:
        if id(cur) in seen:
            return cur
        seen.add(id(cur))
        cur = cur.next
    return None


# ============================================================
# Way 4: Mark visited nodes (mutation)
# ============================================================
def detect_cycle_start_4(head):
    """Mark each visited node by setting a 'visited' attribute. Mutates nodes."""
    cur = head
    while cur:
        if getattr(cur, 'visited', False):
            return cur
        cur.visited = True
        cur = cur.next
    return None


# ============================================================
# Way 5: Length of cycle + two-pointer
# ============================================================
def detect_cycle_start_5(head):
    """Find cycle length; then use two-pointer with that gap."""
    if not head or not head.next:
        return None
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            # Find cycle length
            length = 1
            cur = slow.next
            while cur != slow:
                cur = cur.next
                length += 1
            # Two-pointer with gap = length
            p1 = p2 = head
            for _ in range(length):
                p2 = p2.next
            while p1 != p2:
                p1 = p1.next
                p2 = p2.next
            return p1
    return None


# ============================================================
# Way 6: Recursive
# ============================================================
def detect_cycle_start_6(head):
    """Walk recursively; track visited."""
    seen = set()
    found = [None]

    def walk(node):
        if node is None or found[0] is not None:
            return
        if id(node) in seen:
            found[0] = node
            return
        seen.add(id(node))
        walk(node.next)

    walk(head)
    return found[0]


# ============================================================
# Way 7: Floyd's variant (move slow 1, fast 2 - cleaner phase-2)
# ============================================================
def detect_cycle_start_7(head):
    """Standard Floyd's but with a do-while style loop."""
    if not head or not head.next:
        return None
    slow = head.next
    fast = head.next.next
    # Phase 1: find meeting point
    while slow != fast:
        if not fast or not fast.next:
            return None
        slow = slow.next
        fast = fast.next.next
    # Phase 2: find cycle start
    ptr = head
    while ptr != slow:
        ptr = ptr.next
        slow = slow.next
    return ptr


# ============================================================
# Way 8: Walk + check next (using visited set, bounded)
# ============================================================
def detect_cycle_start_8(head):
    """For each node, check if it's the start of a cycle."""
    if not head:
        return None
    cur = head
    while cur:
        # Check if cur.next leads back to cur (cycle at cur)
        walker = cur.next
        steps = 0
        while walker and walker != cur and steps < 10000:
            walker = walker.next
            steps += 1
        if walker == cur:
            return cur
        cur = cur.next
    return None


# ============================================================
# Way 9: Class-based
# ============================================================
class CycleFinder_9:
    def __init__(self, head):
        self.head = head

    def find_start(self):
        if not self.head or not self.head.next:
            return None
        slow = self.head
        fast = self.head
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
            if slow == fast:
                ptr = self.head
                while ptr != slow:
                    ptr = ptr.next
                    slow = slow.next
                return ptr
        return None


def detect_cycle_start_9(head):
    return CycleFinder_9(head).find_start()


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def detect_cycle_start_10(head):
    """
    THE ONE TO MEMORIZE.

    Phase 1: slow/fast from head. If they meet, there's a cycle.
    Phase 2: Reset slow to head. Advance both 1 step. They meet at
             the cycle's entry node.

    Time:  O(n)
    Space: O(1)
    """
    if not head or not head.next:
        return None
    slow = head
    fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow == fast:
            slow = head
            while slow != fast:
                slow = slow.next
                fast = fast.next
            return slow
    return None


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the node where a cycle begins in a linked list, or None
if no cycle exists."

Key Insight:
"Floyd's two-phase algorithm. First, use slow/fast pointers to find a
meeting point inside the cycle. Then, reset one pointer to head and walk
both 1 step at a time. The distance from head to cycle start equals the
distance from meeting point to cycle start, so they meet at the cycle entry."

Algorithm:
Phase 1: Find meeting point.
  slow = fast = head.
  While fast and fast.next:
    slow = slow.next
    fast = fast.next.next
    If slow == fast: break
  If no meeting: return None.
Phase 2: Find cycle start.
  slow = head.
  While slow != fast:
    slow = slow.next
    fast = fast.next
  Return slow.

Edge Cases:
- Empty / single node: None.
- No cycle: None.
- Cycle at head: return head.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Floyd's   | O(n)   | O(1)   |
| Hash set  | O(n)   | O(n)   |
+-----------+--------+--------+

KEY TRICK:
The mathematical insight: if L is distance to cycle start, M is meeting
point distance inside cycle, C is cycle length, then the distance from
meeting point to cycle start equals L mod C. By resetting one pointer to
head and moving both at the same speed, both pointers traverse L steps
to reach cycle start.

RELATED PROBLEMS:
- Linked List Cycle (LC 141): just detect, no start.
- Find Duplicate Number (LC 287): same trick on arrays.
- Happy Number (LC 202).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    # Each test: (arr, cycle_pos, expected_val, description)
    # cycle_pos=None means no cycle.
    test_cases = [
        ([1, 2, 3, 4, 5, 6], 2, 3, "Cycle starts at index 2"),
        ([1, 2, 3, 4, 5, 6], 0, 1, "Cycle starts at head"),
        ([1, 2, 3, 4, 5, 6], 5, 6, "Cycle of length 1 (last points to itself)"),
        ([1, 2, 3, 4, 5], None, None, "No cycle"),
        ([], None, None, "Empty"),
        ([1], None, None, "Single node, no cycle"),
        ([1, 2], 0, 1, "Two nodes forming cycle at head"),
        ([1, 2, 3], 1, 2, "Cycle of length 2"),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 4, 5, "Long list, mid cycle"),
    ]

    implementations = [
        ("Way 1: Floyd's two-phase (BEST)", detect_cycle_start_1),
        ("Way 2: Hash set nodes", detect_cycle_start_2),
        ("Way 3: Hash set ids", detect_cycle_start_3),
        ("Way 4: Mark visited", detect_cycle_start_4),
        ("Way 5: Length + 2-ptr", detect_cycle_start_5),
        ("Way 6: Recursive", detect_cycle_start_6),
        ("Way 7: Floyd's variant", detect_cycle_start_7),
        ("Way 8: Walk + check next", detect_cycle_start_8),
        ("Way 9: Class-based", detect_cycle_start_9),
        ("Way 10: Final cleanest", detect_cycle_start_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for arr, cycle_pos, expected_val, desc in test_cases:
            try:
                head = build_with_cycle(copy.deepcopy(arr), cycle_pos)
                result = fn(head)
                actual = result.val if result else None
                if actual == expected_val:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: arr={arr} cycle_pos={cycle_pos} expected={expected_val} got={actual}")
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
