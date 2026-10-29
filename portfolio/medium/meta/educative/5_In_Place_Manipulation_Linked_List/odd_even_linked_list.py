"""
Odd Even Linked List - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/odd-even-linked-list

Given the head of a singly linked list, group all nodes with odd indices
together followed by nodes with even indices, and return the reordered list.
First node is odd (index 1).

KEY INSIGHT:
Walk with two pointers: odd_head/odd_tail and even_head/even_tail. Detach
even nodes; connect odd's tail to next odd; connect even's tail to next even.
At the end, connect odd's tail to even_head.

Examples:
    1->2->3->4->5  =>  1->3->5->2->4

Constraints:
- 0 <= number of nodes <= 10^4
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
# Way 1: Two pointers odd/even (BEST - Memorize!)
# ============================================================
def odd_even_list_1(head):
    """Split odd/even indexed nodes; reconnect odd -> even_head."""
    if not head or not head.next:
        return head
    odd = head
    even = head.next
    even_head = even
    while even and even.next:
        odd.next = even.next
        odd = odd.next
        even.next = odd.next
        even = even.next
    odd.next = even_head
    return head


# ============================================================
# Way 2: Build into array; rebuild
# ============================================================
def odd_even_list_2(head):
    """Collect values; alternate odd/even into output."""
    vals = []
    cur = head
    while cur:
        vals.append(cur.val)
        cur = cur.next
    n = len(vals)
    # Odd-indexed (1, 3, 5, ...) come first, then even (2, 4, 6, ...)
    odd_vals = vals[0::2]  # indices 0, 2, 4 -> 1st, 3rd, 5th in 1-indexed
    even_vals = vals[1::2]
    return list_from_array(odd_vals + even_vals)


# ============================================================
# Way 3: Recursive
# ============================================================
def odd_even_list_3(head):
    """Recursive split."""
    if not head or not head.next:
        return head
    odd_head = head
    even_head = head.next
    odd_tail = odd_head
    even_tail = even_head
    cur = even_head.next
    is_odd = True
    while cur:
        if is_odd:
            odd_tail.next = cur
            odd_tail = cur
        else:
            even_tail.next = cur
            even_tail = cur
        cur = cur.next
        is_odd = not is_odd
    odd_tail.next = even_head
    even_tail.next = None
    return odd_head


# ============================================================
# Way 4: Hash map by index
# ============================================================
def odd_even_list_4(head):
    """Use dict to map index to node; relink."""
    if not head or not head.next:
        return head
    nodes = []
    cur = head
    while cur:
        nodes.append(cur)
        cur = cur.next
    n = len(nodes)
    # New order: 0, 2, 4, ..., 1, 3, 5, ...
    new_order = []
    for i in range(0, n, 2):
        new_order.append(nodes[i])
    for i in range(1, n, 2):
        new_order.append(nodes[i])
    # Relink
    for i in range(n - 1):
        new_order[i].next = new_order[i + 1]
    new_order[-1].next = None
    return new_order[0]


# ============================================================
# Way 5: Class-based wrapper
# ============================================================
class OddEvenSeparator_5:
    def __init__(self, head):
        self.head = head

    def reorder(self):
        return odd_even_list_1(self.head)


def odd_even_list_5(head):
    return OddEvenSeparator_5(head).reorder()


# ============================================================
# Way 6: Three pointers (prev, cur, nxt)
# ============================================================
def odd_even_list_6(head):
    """Use prev/cur/nxt walking; swap each odd-even pair conceptually."""
    if not head or not head.next:
        return head
    # Easier: build even list, append to end of odd list
    odd = head
    even_head = head.next
    even = even_head
    while odd.next and even.next:
        odd.next = even.next
        odd = odd.next
        even.next = odd.next
        even = even.next
    odd.next = even_head
    return head


# ============================================================
# Way 7: Stack-based
# ============================================================
def odd_even_list_7(head):
    """Build stacks of odd/even; pop to rebuild."""
    if not head or not head.next:
        return head
    odd_stack = []
    even_stack = []
    cur = head
    is_odd = True
    while cur:
        if is_odd:
            odd_stack.append(cur)
        else:
            even_stack.append(cur)
        cur = cur.next
        is_odd = not is_odd
    # Rebuild
    new_head = odd_stack[0]
    cur = new_head
    for i in range(1, len(odd_stack)):
        cur.next = odd_stack[i]
        cur = cur.next
    for n in even_stack:
        cur.next = n
        cur = cur.next
    cur.next = None
    return new_head


# ============================================================
# Way 8: Deque-based
# ============================================================
def odd_even_list_8(head):
    """Use deque for alternate pops."""
    if not head or not head.next:
        return head
    from collections import deque
    odd = deque()
    even = deque()
    cur = head
    is_odd = True
    while cur:
        if is_odd:
            odd.append(cur)
        else:
            even.append(cur)
        cur = cur.next
        is_odd = not is_odd
    new_head = odd[0]
    cur = new_head
    for i in range(1, len(odd)):
        cur.next = odd[i]
        cur = cur.next
    for n in even:
        cur.next = n
        cur = cur.next
    cur.next = None
    return new_head


# ============================================================
# Way 9: Recursive (alt)
# ============================================================
def odd_even_list_9(head):
    """Recursive helper to split and recurse."""
    def helper(node, is_odd):
        if not node:
            return None, None
        if is_odd:
            odd_head, odd_tail = helper(node.next, False)
            node.next = odd_head
            return node, odd_tail or node
        else:
            even_head, even_tail = helper(node.next, True)
            node.next = even_head
            return node, even_tail or node

    if not head or not head.next:
        return head
    # Walk and partition into two lists
    odd_dummy = ListNode(0)
    even_dummy = ListNode(0)
    odd_tail = odd_dummy
    even_tail = even_dummy
    cur = head
    is_odd = True
    while cur:
        if is_odd:
            odd_tail.next = cur
            odd_tail = cur
        else:
            even_tail.next = cur
            even_tail = cur
        cur = cur.next
        is_odd = not is_odd
    odd_tail.next = even_dummy.next
    even_tail.next = None
    return odd_dummy.next


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def odd_even_list_10(head):
    """
    THE ONE TO MEMORIZE.

    1. odd = head; even = head.next; even_head = even.
    2. While even and even.next:
       a. odd.next = even.next; odd = odd.next
       b. even.next = odd.next; even = even.next
    3. odd.next = even_head; return head.

    Time:  O(n)
    Space: O(1).
    """
    if not head or not head.next:
        return head
    odd = head
    even = head.next
    even_head = even
    while even and even.next:
        odd.next = even.next
        odd = odd.next
        even.next = odd.next
        even = even.next
    odd.next = even_head
    return head


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to reorder a linked list so all odd-indexed nodes come first,
followed by all even-indexed nodes."

Key Insight:
"Maintain two pointers: odd (head) and even (head.next). Detach even nodes
from the main chain; build a separate chain. At the end, connect odd's
tail to even_head."

Algorithm:
1. odd = head; even = head.next; even_head = even.
2. While even and even.next:
   a. odd.next = even.next; odd = odd.next (advance odd by 2).
   b. even.next = odd.next; even = even.next (advance even by 2).
3. odd.next = even_head; return head.

Edge Cases:
- Empty / single node: return as-is.
- Two nodes: swap.
- Odd count: middle node ends up at end of odd chain.

KEY TRICK:
The loop runs while BOTH even and even.next exist. After one iteration,
odd has advanced by 2 and even has advanced by 2. The even chain is
already detached.

RELATED PROBLEMS:
- Reverse Linked List II (LC 92).
- Swap Nodes in Pairs (LC 24).
- Reorder List (LC 143).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([1, 2, 3, 4, 5], [1, 3, 5, 2, 4], "Standard LC328"),
        ([2, 1, 3, 5, 6, 4, 7], [2, 3, 6, 7, 1, 5, 4], "LC328 example"),
        ([], [], "Empty"),
        ([1], [1], "Single"),
        ([1, 2], [1, 2], "Two nodes"),
        ([1, 2, 3], [1, 3, 2], "Three nodes"),
    ]

    implementations = [
        ("Way 1: Two ptr (BEST)", odd_even_list_1),
        ("Way 2: Array rebuild", odd_even_list_2),
        ("Way 3: Recursive", odd_even_list_3),
        ("Way 4: Hash map", odd_even_list_4),
        ("Way 5: Class-based", odd_even_list_5),
        ("Way 6: Three pointers", odd_even_list_6),
        ("Way 7: Stack", odd_even_list_7),
        ("Way 8: Deque", odd_even_list_8),
        ("Way 9: Recursive alt", odd_even_list_9),
        ("Way 10: Final cleanest", odd_even_list_10),
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