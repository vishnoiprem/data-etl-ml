"""
Reverse Linked List - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/reverse-linked-list

Reverse a singly linked list in place. Return the new head.

KEY INSIGHT:
Iterative: walk through, redirect each node's next pointer to its previous.
Use three pointers: prev, cur, nxt.

Examples:
    1 -> 2 -> 3 -> None  =>  3 -> 2 -> 1 -> None

Constraints:
- 0 <= number of nodes <= 5000
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


def list_to_array(head):
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


# ============================================================
# Way 1: Iterative with three pointers (BEST - Memorize!)
# ============================================================
def reverse_list_1(head):
    """prev, cur, nxt walk; reverse pointers."""
    prev = None
    cur = head
    while cur:
        nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
    return prev


# ============================================================
# Way 2: Iterative with two pointers
# ============================================================
def reverse_list_2(head):
    """Use only prev and cur (save nxt inline)."""
    prev = None
    cur = head
    while cur:
        cur.next, prev, cur = prev, cur, cur.next
    return prev


# ============================================================
# Way 3: Recursive
# ============================================================
def reverse_list_3(head):
    """Reverse via recursion."""
    if not head or not head.next:
        return head
    new_head = reverse_list_3(head.next)
    head.next.next = head
    head.next = None
    return new_head


# ============================================================
# Way 4: Head-insertion into new list
# ============================================================
def reverse_list_4(head):
    """Insert each node at the head of a new list."""
    new_head = None
    cur = head
    while cur:
        nxt = cur.next
        cur.next = new_head
        new_head = cur
        cur = nxt
    return new_head


# ============================================================
# Way 5: Stack-based
# ============================================================
def reverse_list_5(head):
    """Push all onto stack, pop and reconnect."""
    stack = []
    cur = head
    while cur:
        stack.append(cur)
        cur = cur.next
    new_head = stack.pop() if stack else None
    cur = new_head
    while stack:
        nxt = stack.pop()
        cur.next = nxt
        cur = nxt
    if cur:
        cur.next = None
    return new_head


# ============================================================
# Way 6: Recursive with helper to reverse tail
# ============================================================
def reverse_list_6(head):
    """Reverse via recursion that returns new head."""
    def helper(node):
        if not node or not node.next:
            return node
        new_head = helper(node.next)
        node.next.next = node
        node.next = None
        return new_head
    return helper(head)


# ============================================================
# Way 7: Build into list, rebuild reversed
# ============================================================
def reverse_list_7(head):
    """Collect values, rebuild reversed list."""
    vals = []
    cur = head
    while cur:
        vals.append(cur.val)
        cur = cur.next
    vals.reverse()
    return list_from_array(vals)


# ============================================================
# Way 8: Class-based wrapper
# ============================================================
class ListReverser_8:
    def __init__(self, head):
        self.head = head

    def reverse(self):
        return reverse_list_1(self.head)


def reverse_list_8(head):
    return ListReverser_8(head).reverse()


# ============================================================
# Way 9: Generator-based approach
# ============================================================
def reverse_list_9(head):
    """Walk twice - once to collect nodes, once to reverse."""
    nodes = []
    cur = head
    while cur:
        nodes.append(cur)
        cur = cur.next
    # Reverse pointers in place
    for i in range(len(nodes) - 1, 0, -1):
        nodes[i].next = nodes[i - 1]
    if nodes:
        nodes[0].next = None
        return nodes[-1]
    return None


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def reverse_list_10(head):
    """
    THE ONE TO MEMORIZE.

    1. prev = None, cur = head.
    2. While cur:
       nxt = cur.next
       cur.next = prev
       prev = cur
       cur = nxt
    3. Return prev.

    Time:  O(n)
    Space: O(1).
    """
    prev = None
    cur = head
    while cur:
        nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
    return prev


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to reverse a singly linked list in place, returning the new head."

Key Insight:
"Use three pointers (or two if you're clever): prev (already reversed),
cur (current node), nxt (next node to visit). For each node, save nxt,
redirect cur.next to prev, advance both prev and cur."

Algorithm:
1. prev = None, cur = head.
2. While cur:
   nxt = cur.next
   cur.next = prev
   prev = cur
   cur = nxt
3. Return prev (which is the new head).

Edge Cases:
- Empty list: return None.
- Single node: return that node.
- Two nodes: swap them.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Iterative | O(n)   | O(1)   |
| Recursive | O(n)   | O(n)   |
| Stack     | O(n)   | O(n)   |
+-----------+--------+--------+

KEY TRICK:
The "cur.next = prev" is what actually does the reversal. The nxt save is
just so we don't lose the rest of the list.

RELATED PROBLEMS:
- Reverse Linked List II (LC 92).
- Reverse Nodes in k-Group (LC 25).
- Palindrome Linked List (LC 234).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([1, 2, 3, 4, 5], [5, 4, 3, 2, 1], "Standard"),
        ([1, 2], [2, 1], "Two nodes"),
        ([], [], "Empty"),
        ([1], [1], "Single"),
        ([1, 2, 3], [3, 2, 1], "Three nodes"),
    ]

    implementations = [
        ("Way 1: Iterative 3-ptr (BEST)", reverse_list_1),
        ("Way 2: Iterative 2-ptr", reverse_list_2),
        ("Way 3: Recursive", reverse_list_3),
        ("Way 4: Head-insertion", reverse_list_4),
        ("Way 5: Stack-based", reverse_list_5),
        ("Way 6: Recursive helper", reverse_list_6),
        ("Way 7: Build + rebuild", reverse_list_7),
        ("Way 8: Class-based", reverse_list_8),
        ("Way 9: Collect + reverse", reverse_list_9),
        ("Way 10: Final cleanest", reverse_list_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for inp, expected, desc in test_cases:
            try:
                head = list_from_array(copy.deepcopy(inp))
                result = fn(head)
                got = list_to_array(result)
                if got == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: input={inp} expected={expected} got={got}")
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
