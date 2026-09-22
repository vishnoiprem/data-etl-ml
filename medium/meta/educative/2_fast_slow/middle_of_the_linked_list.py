"""
Middle of the Linked List - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/middle-of-the-linked-list

Return the middle node of a singly linked list. If two middles, return the
SECOND one (e.g., for 1->2->3->4->5, return 3; for 1->2->3->4, return 3).

KEY INSIGHT:
Fast/slow pointers. Fast moves 2, slow moves 1. When fast reaches the end,
slow is at the middle. With "fast.next" check, slow lands on the second
middle for even-length lists.

Examples:
    [1, 2, 3, 4, 5] -> node 3
    [1, 2, 3, 4] -> node 3

Constraints:
- 1 <= number of nodes <= 100
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


# ============================================================
# Way 1: Fast/slow canonical (BEST - Memorize!)
# ============================================================
def middle_node_1(head):
    """slow moves 1, fast moves 2. When fast ends, slow is at middle."""
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    return slow


# ============================================================
# Way 2: Count length, walk half
# ============================================================
def middle_node_2(head):
    length = 0
    cur = head
    while cur:
        length += 1
        cur = cur.next
    cur = head
    for _ in range(length // 2):
        cur = cur.next
    return cur


# ============================================================
# Way 3: Array of nodes
# ============================================================
def middle_node_3(head):
    nodes = []
    cur = head
    while cur:
        nodes.append(cur)
        cur = cur.next
    return nodes[len(nodes) // 2]


# ============================================================
# Way 4: Convert to array of values
# ============================================================
def middle_node_4(head):
    arr = []
    cur = head
    while cur:
        arr.append(cur)
        cur = cur.next
    return arr[len(arr) // 2]


# ============================================================
# Way 5: Fast/slow, single-condition loop
# ============================================================
def middle_node_5(head):
    slow = fast = head
    while fast.next and fast.next.next:
        slow = slow.next
        fast = fast.next.next
    # If fast.next exists (even length), advance slow once more
    if fast.next:
        slow = slow.next
    return slow


# ============================================================
# Way 6: Walk with explicit index counter
# ============================================================
def middle_node_6(head):
    """Use a counter; every other node, advance a tracker."""
    counter = 0
    middle = head
    cur = head
    while cur:
        if counter % 2 == 1:
            middle = middle.next
        counter += 1
        cur = cur.next
    return middle


# ============================================================
# Way 7: Recursive (educational)
# ============================================================
def middle_node_7(head):
    """Recursion: traverse to end, returning index; use index to find middle."""

    def get_length(node):
        if node is None:
            return 0
        return 1 + get_length(node.next)

    n = get_length(head)
    cur = head
    for _ in range(n // 2):
        cur = cur.next
    return cur


# ============================================================
# Way 8: Stack-based
# ============================================================
def middle_node_8(head):
    """Push all nodes; pop until middle reached."""
    stack = []
    cur = head
    while cur:
        stack.append(cur)
        cur = cur.next
    return stack[len(stack) // 2]


# ============================================================
# Way 9: Class-based
# ============================================================
class MiddleFinder_9:
    def __init__(self, head):
        self.head = head

    def find(self):
        slow = fast = self.head
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
        return slow


def middle_node_9(head):
    return MiddleFinder_9(head).find()


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def middle_node_10(head):
    """
    THE ONE TO MEMORIZE.

    1. slow = fast = head.
    2. While fast and fast.next:
       a. slow = slow.next
       b. fast = fast.next.next
    3. Return slow.

    Time:  O(n)
    Space: O(1).
    """
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    return slow


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the middle node of a linked list."

Key Insight:
"Fast and slow pointers. Slow moves 1 step at a time; fast moves 2. When
fast reaches the end, slow is at the middle. For even-length lists, this
gives the SECOND middle (e.g., 1->2->3->4 -> 3)."

Algorithm:
1. slow = fast = head.
2. While fast and fast.next:
   a. slow = slow.next
   b. fast = fast.next.next
3. Return slow.

Edge Cases:
- Empty list: return None.
- Single node: return that node.
- Two nodes: return second.
- Even length: returns second middle.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Fast/slow | O(n)   | O(1)   |
| Count+walk| O(n)   | O(1)   |
| Array     | O(n)   | O(n)   |
+-----------+--------+--------+

KEY TRICK:
Using `fast and fast.next` (not just `fast`) is what makes slow land on
the SECOND middle for even-length lists. This matches LeetCode's expected
behavior.

RELATED PROBLEMS:
- Palindrome Linked List (LC 234): uses fast/slow to find middle.
- Linked List Cycle II (LC 142).
- Remove Nth From End (LC 19): use fast/slow with n-gap.
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        # (array, expected_val, description)
        ([1, 2, 3, 4, 5], 3, "Odd length"),
        ([1, 2, 3, 4], 3, "Even length (second middle)"),
        ([1], 1, "Single"),
        ([1, 2], 2, "Two nodes"),
        ([], None, "Empty"),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 6, "10 nodes"),
        ([1, 2, 3, 4, 5, 6, 7], 4, "7 nodes"),
        ([10, 20, 30], 20, "Multi-digit"),
    ]

    implementations = [
        ("Way 1: Fast/slow (BEST)", middle_node_1),
        ("Way 2: Count + walk", middle_node_2),
        ("Way 3: Array of nodes", middle_node_3),
        ("Way 4: Values to array", middle_node_4),
        ("Way 5: Single-cond loop", middle_node_5),
        ("Way 6: Counter", middle_node_6),
        ("Way 7: Recursive length", middle_node_7),
        ("Way 8: Stack", middle_node_8),
        ("Way 9: Class-based", middle_node_9),
        ("Way 10: Final cleanest", middle_node_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for arr, expected_val, desc in test_cases:
            try:
                head = list_from_array(copy.deepcopy(arr))
                result = fn(head)
                actual_val = result.val if result else None
                if actual_val == expected_val:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: input={arr} expected={expected_val} got={actual_val}")
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
