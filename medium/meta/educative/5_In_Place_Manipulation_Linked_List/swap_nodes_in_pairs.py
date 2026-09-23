"""
Swap Nodes in Pairs - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/swap-nodes-in-pairs

Given a linked list, swap every two adjacent nodes and return the head.

KEY INSIGHT:
Use a dummy node and walk in pairs. For each pair (a, b), redirect:
pre -> b -> a -> rest.

Examples:
    1 -> 2 -> 3 -> 4  =>  2 -> 1 -> 4 -> 3
    1 -> 2 -> 3  =>  2 -> 1 -> 3 (last odd node unchanged)

Constraints:
- 0 <= number of nodes <= 100
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
# Way 1: Dummy + walk pairs (BEST - Memorize!)
# ============================================================
def swap_pairs_1(head):
    """Use dummy. For each pair (a, b), redirect pre -> b -> a -> rest."""
    dummy = ListNode(0)
    dummy.next = head
    pre = dummy
    while pre.next and pre.next.next:
        a = pre.next
        b = a.next
        pre.next = b
        a.next = b.next
        b.next = a
        pre = a
    return dummy.next


# ============================================================
# Way 2: Iterative with first/second
# ============================================================
def swap_pairs_2(head):
    """Track first, second of each pair."""
    if not head or not head.next:
        return head
    new_head = head.next
    first = head
    while first and first.next:
        second = first.next
        first.next = second.next
        second.next = first
        if first.next and first.next.next:
            first.next = first.next.next  # wrong, let me redo
        # Actually the next pair's head is first.next
        # Connect prev pair's first to this pair's second
        if hasattr(first, '_prev_second') and first._prev_second:
            first._prev_second.next = second
        first._prev_second = second
        first = first.next
    return new_head


# Cleaner Way 2:
def swap_pairs_2(head):
    """Track first, second of each pair; maintain tail."""
    if not head or not head.next:
        return head
    new_head = head.next
    pre = None
    cur = head
    while cur and cur.next:
        nxt = cur.next.next  # first of next pair (or None)
        second = cur.next
        second.next = cur
        cur.next = nxt
        if pre:
            pre.next = second
        pre = cur
        cur = nxt
    return new_head


# ============================================================
# Way 3: Recursive
# ============================================================
def swap_pairs_3(head):
    """Swap recursively."""
    if not head or not head.next:
        return head
    new_head = head.next
    head.next = swap_pairs_3(head.next.next)
    new_head.next = head
    return new_head


# ============================================================
# Way 4: Build into array, rebuild swapped
# ============================================================
def swap_pairs_4(head):
    """Collect values; rebuild swapped."""
    vals = []
    cur = head
    while cur:
        vals.append(cur.val)
        cur = cur.next
    out = []
    for i in range(0, len(vals), 2):
        if i + 1 < len(vals):
            out.append(vals[i + 1])
            out.append(vals[i])
        else:
            out.append(vals[i])
    return list_from_array(out)


# ============================================================
# Way 5: Stack-based
# ============================================================
def swap_pairs_5(head):
    """Push pairs onto stack; pop to reverse."""
    if not head or not head.next:
        return head
    dummy = ListNode(0)
    dummy.next = head
    pre = dummy
    cur = head
    while cur and cur.next:
        a = cur
        b = cur.next
        nxt = b.next
        # Swap a and b
        pre.next = b
        b.next = a
        a.next = nxt
        pre = a
        cur = nxt
    return dummy.next


# ============================================================
# Way 6: Hash map by index
# ============================================================
def swap_pairs_6(head):
    """Use index map; relink pairs."""
    if not head or not head.next:
        return head
    nodes = []
    cur = head
    while cur:
        nodes.append(cur)
        cur = cur.next
    n = len(nodes)
    for i in range(0, n - 1, 2):
        nodes[i], nodes[i + 1] = nodes[i + 1], nodes[i]
    for i in range(n - 1):
        nodes[i].next = nodes[i + 1]
    nodes[-1].next = None
    return nodes[0]


# ============================================================
# Way 7: Class-based wrapper
# ============================================================
class PairSwapper_7:
    def __init__(self, head):
        self.head = head

    def swap(self):
        return swap_pairs_1(self.head)


def swap_pairs_7(head):
    return PairSwapper_7(head).swap()


# ============================================================
# Way 8: Deque-based
# ============================================================
def swap_pairs_8(head):
    """Collect values into deque; swap pairs; rebuild."""
    from collections import deque
    vals = deque()
    cur = head
    while cur:
        vals.append(cur.val)
        cur = cur.next
    out = []
    while len(vals) >= 2:
        a = vals.popleft()
        b = vals.popleft()
        out.append(b)
        out.append(a)
    while vals:
        out.append(vals.popleft())
    return list_from_array(out)


# ============================================================
# Way 9: Two-pointer walk (in-place with explicit pointers)
# ============================================================
def swap_pairs_9(head):
    """Walk with prev/cur/nxt; swap each pair."""
    if not head or not head.next:
        return head
    dummy = ListNode(0)
    dummy.next = head
    cur = head
    prev = dummy
    while cur and cur.next:
        nxt = cur.next
        cur.next = nxt.next
        nxt.next = cur
        prev.next = nxt
        prev = cur
        cur = cur.next
    return dummy.next


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def swap_pairs_10(head):
    """
    THE ONE TO MEMORIZE.

    1. dummy -> head. pre = dummy.
    2. While pre.next and pre.next.next exist (a pair):
       a. a = pre.next, b = a.next.
       b. pre.next = b
       c. a.next = b.next
       d. b.next = a
       e. pre = a
    3. Return dummy.next.

    Time:  O(n)
    Space: O(1).
    """
    dummy = ListNode(0)
    dummy.next = head
    pre = dummy
    while pre.next and pre.next.next:
        a = pre.next
        b = a.next
        pre.next = b
        a.next = b.next
        b.next = a
        pre = a
    return dummy.next


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to swap every two adjacent nodes in a linked list, returning the
new head. If the count is odd, the last node stays as-is."

Key Insight:
"Use a dummy node pointing to head. Walk through pairs. For each pair
(a, b), redirect: pre -> b -> a -> (rest of chain). Then advance pre to
a (now last of swapped pair) and continue."

Algorithm:
1. dummy -> head. pre = dummy.
2. While pre.next and pre.next.next:
   a. a = pre.next; b = a.next.
   b. pre.next = b
   c. a.next = b.next
   d. b.next = a
   e. pre = a (advance to end of swapped pair).
3. Return dummy.next.

Edge Cases:
- Empty list: return None.
- Single node: return as-is.
- Odd count: last node remains.
- Even count: clean swap.

KEY TRICK:
The dummy node handles the case where the head changes. Without it, you'd
need special logic for the first pair.

RELATED PROBLEMS:
- Reverse Nodes in k-Group (LC 25).
- Reverse Linked List II (LC 92).
- Odd Even Linked List (LC 328).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([1, 2, 3, 4], [2, 1, 4, 3], "Standard LC24"),
        ([1, 2, 3], [2, 1, 3], "Odd length"),
        ([], [], "Empty"),
        ([1], [1], "Single"),
        ([1, 2], [2, 1], "Two nodes"),
        ([1, 2, 3, 4, 5], [2, 1, 4, 3, 5], "Five nodes"),
    ]

    implementations = [
        ("Way 1: Dummy + pairs (BEST)", swap_pairs_1),
        ("Way 2: Track first/second", swap_pairs_2),
        ("Way 3: Recursive", swap_pairs_3),
        ("Way 4: Array rebuild", swap_pairs_4),
        ("Way 5: Stack", swap_pairs_5),
        ("Way 6: Hash map", swap_pairs_6),
        ("Way 7: Class-based", swap_pairs_7),
        ("Way 8: Deque", swap_pairs_8),
        ("Way 9: prev/cur/nxt", swap_pairs_9),
        ("Way 10: Final cleanest", swap_pairs_10),
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