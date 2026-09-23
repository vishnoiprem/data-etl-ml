"""
Reverse Linked List II - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/reverse-linked-list-ii

Reverse a linked list from position left to right (1-indexed). Do it in-place.

KEY INSIGHT:
Walk to the node just before `left`. Then iteratively reverse the next
(right - left + 1) nodes. Reconnect the boundaries.

Examples:
    1->2->3->4->5, left=2, right=4  =>  1->4->3->2->5

Constraints:
- 1 <= left <= right <= n
- Number of nodes up to 500
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
# Way 1: Walk to pre, reverse a window (BEST - Memorize!)
# ============================================================
def reverse_between_1(head, left, right):
    """Walk to node just before left; iteratively reverse the window."""
    if not head or left == right:
        return head
    dummy = ListNode(0)
    dummy.next = head
    pre = dummy
    for _ in range(left - 1):
        pre = pre.next
    cur = pre.next
    # Reverse (right - left + 1) nodes using head-insertion.
    for _ in range(right - left):
        nxt = cur.next
        cur.next = nxt.next
        nxt.next = pre.next
        pre.next = nxt
    return dummy.next


# ============================================================
# Way 2: Walk to pre, then standard prev/cur/nxt reverse
# ============================================================
def reverse_between_2(head, left, right):
    """Walk to pre; reverse window; reconnect."""
    if not head or left == right:
        return head
    dummy = ListNode(0)
    dummy.next = head
    pre = dummy
    for _ in range(left - 1):
        pre = pre.next
    cur = pre.next
    prev = None
    for _ in range(right - left + 1):
        nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
    # Now: pre.next is original first of window (now last), prev is new first.
    pre.next.next = cur  # original first's next -> first node after window
    pre.next = prev       # pre.next -> new first (original last)
    return dummy.next


# ============================================================
# Way 3: Build into array; reverse subarray; rebuild
# ============================================================
def reverse_between_3(head, left, right):
    """Collect values, reverse subarray, rebuild."""
    vals = []
    cur = head
    while cur:
        vals.append(cur.val)
        cur = cur.next
    # left, right are 1-indexed
    sub = vals[left - 1:right][::-1]
    vals = vals[:left - 1] + sub + vals[right:]
    return list_from_array(vals)


# ============================================================
# Way 4: Recursive
# ============================================================
def reverse_between_4(head, left, right):
    """Recursive reverse."""
    if left == 1:
        # Reverse first `right` nodes; the original head's next should connect
        # to whatever comes after the reversed portion.
        return reverse_n(head, right)
    head.next = reverse_between_4(head.next, left - 1, right - 1)
    return head


def reverse_n(head, n):
    """Reverse first n nodes. Return new head."""
    if n == 1:
        return head
    new_head = reverse_n(head.next, n - 1)
    rest = head.next.next
    head.next.next = head
    head.next = rest
    return new_head


# ============================================================
# Way 5: Stack-based
# ============================================================
def reverse_between_5(head, left, right):
    """Walk to pre; use a stack of nodes; pop to rebuild."""
    if not head or left == right:
        return head
    dummy = ListNode(0)
    dummy.next = head
    pre = dummy
    for _ in range(left - 1):
        pre = pre.next
    # Stack of (right - left + 1) nodes
    stack = []
    cur = pre.next
    for _ in range(right - left + 1):
        stack.append(cur)
        cur = cur.next
    # After window ends, cur is the first node after the window
    # Pop from stack and reconnect
    new_pre = pre
    for i in range(len(stack) - 1, -1, -1):
        new_pre.next = stack[i]
        new_pre = stack[i]
    new_pre.next = cur
    return dummy.next


# ============================================================
# Way 6: Index-based swap
# ============================================================
def reverse_between_6(head, left, right):
    """Use index map to access nodes."""
    if not head or left == right:
        return head
    nodes = []
    cur = head
    while cur:
        nodes.append(cur)
        cur = cur.next
    # Reverse nodes[left-1:right] (inclusive on both ends, 1-indexed -> 0-indexed)
    sub = nodes[left - 1:right][::-1]
    nodes[left - 1:right] = sub
    # Reconnect
    for i in range(len(nodes) - 1):
        nodes[i].next = nodes[i + 1]
    nodes[-1].next = None
    return nodes[0]


# ============================================================
# Way 7: Class-based wrapper
# ============================================================
class SublistReverser_7:
    def __init__(self, head):
        self.head = head

    def reverse(self, left, right):
        return reverse_between_1(self.head, left, right)


def reverse_between_7(head, left, right):
    return SublistReverser_7(head).reverse(left, right)


# ============================================================
# Way 8: Two-pass: collect, partial-reverse, rebuild
# ============================================================
def reverse_between_8(head, left, right):
    """Collect values; rebuild with subarray reversed (alt impl)."""
    if not head or left == right:
        return head
    vals = []
    cur = head
    while cur:
        vals.append(cur.val)
        cur = cur.next
    # Walk to left-1, then push (right-left+1) onto stack; pop to reverse.
    stack = []
    out = []
    for i, v in enumerate(vals):
        if i < left - 1:
            out.append(v)
        elif i < right:
            stack.append(v)
            if i == right - 1:
                while stack:
                    out.append(stack.pop())
        else:
            out.append(v)
    return list_from_array(out)


# ============================================================
# Way 9: Hash + relink
# ============================================================
def reverse_between_9(head, left, right):
    """Walk to find window; rebuild within window."""
    if not head or left == right:
        return head
    # Walk to node at position left
    cur = head
    for _ in range(left - 1):
        cur = cur.next
    # cur is first node of window
    # Reverse window of size (right - left + 1)
    new_head = None
    tail = cur
    for _ in range(right - left + 1):
        nxt = cur.next
        cur.next = new_head
        new_head = cur
        cur = nxt
    # new_head is new first, tail (still original first) is new last
    # tail.next should point to nxt (first after window)
    # But we need to connect: pre.next -> new_head
    tail.next = cur
    # Walk to pre
    pre = head
    for _ in range(left - 2):
        pre = pre.next
    if left == 1:
        return new_head
    pre.next = new_head
    return head


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def reverse_between_10(head, left, right):
    """
    THE ONE TO MEMORIZE.

    1. Use a dummy node pointing to head.
    2. Walk to the node just before position `left` (call it `pre`).
    3. cur = pre.next.
    4. Repeat (right - left) times: move the next node to the front of the window.
       nxt = cur.next
       cur.next = nxt.next
       nxt.next = pre.next
       pre.next = nxt
    5. Return dummy.next.

    Time:  O(n)
    Space: O(1).
    """
    if not head or left == right:
        return head
    dummy = ListNode(0)
    dummy.next = head
    pre = dummy
    for _ in range(left - 1):
        pre = pre.next
    cur = pre.next
    for _ in range(right - left):
        nxt = cur.next
        cur.next = nxt.next
        nxt.next = pre.next
        pre.next = nxt
    return dummy.next


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to reverse the linked list from position `left` to `right` (1-indexed),
in place, and return the head."

Key Insight:
"Use a dummy node to handle the boundary cleanly. Walk to the node just before
`left` (call it `pre`). Then iteratively move the next node to the front of
the window (right - left) times. This is the head-insertion trick restricted
to the window."

Algorithm:
1. dummy -> head. Walk `left - 1` steps to pre.
2. cur = pre.next.
3. Repeat (right - left) times:
   - nxt = cur.next
   - cur.next = nxt.next      (skip nxt in the chain)
   - nxt.next = pre.next       (nxt points to old first of window)
   - pre.next = nxt             (pre points to nxt, new first)
4. Return dummy.next.

Edge Cases:
- left == right: nothing to do.
- left == 1: pre is the dummy.
- right == n: cur.next is None after window.

KEY TRICK:
The head-insertion trick within a bounded window. Each iteration moves the
node after `cur` to the front of the window. After (right - left) iterations,
the window is reversed.

RELATED PROBLEMS:
- Reverse Linked List (LC 206).
- Reverse Nodes in k-Group (LC 25).
- Swapping Nodes in a Linked List (LC 1721).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([1, 2, 3, 4, 5], 2, 4, [1, 4, 3, 2, 5], "Standard LC92"),
        ([5], 1, 1, [5], "Single"),
        ([1, 2, 3, 4, 5], 1, 5, [5, 4, 3, 2, 1], "Full reverse"),
        ([1, 2, 3, 4, 5], 1, 2, [2, 1, 3, 4, 5], "Reverse at start"),
        ([1, 2, 3, 4, 5], 4, 5, [1, 2, 3, 5, 4], "Reverse at end"),
        ([3, 5], 1, 2, [5, 3], "Two nodes"),
    ]

    implementations = [
        ("Way 1: Head-insertion (BEST)", reverse_between_1),
        ("Way 2: Standard reverse", reverse_between_2),
        ("Way 3: Array rebuild", reverse_between_3),
        ("Way 4: Recursive", reverse_between_4),
        ("Way 5: Stack", reverse_between_5),
        ("Way 6: Index map", reverse_between_6),
        ("Way 7: Class-based", reverse_between_7),
        ("Way 8: Reverse-all then map", reverse_between_8),
        ("Way 9: Hash + relink", reverse_between_9),
        ("Way 10: Final cleanest", reverse_between_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for inp, left, right, expected, desc in test_cases:
            try:
                head = list_from_array(copy.deepcopy(inp))
                result = fn(head, left, right)
                got = list_to_array(result)
                if got == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: input={inp} l={left} r={right} expected={expected} got={got}")
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