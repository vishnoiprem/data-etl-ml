"""
Reverse Nodes in k-Group - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/reverse-nodes-in-k-group

Given a linked list, reverse the nodes of a list k at a time and return the
modified list. k is a positive integer <= length of list. Nodes at the end
that don't form a full group remain as-is.

KEY INSIGHT:
Repeatedly reverse k nodes using head-insertion; advance by k. If fewer
than k nodes remain, leave them alone.

Examples:
    1->2->3->4->5, k=2  =>  2->1->4->3->5
    1->2->3->4->5, k=3  =>  3->2->1->4->5

Constraints:
- 0 <= number of nodes <= 5000
- 1 <= k <= length of list (caller respects this)
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
# Way 1: Group-by-group head-insertion (BEST - Memorize!)
# ============================================================
def reverse_k_group_1(head, k):
    """Repeatedly reverse each group of k with head-insertion."""
    dummy = ListNode(0)
    dummy.next = head
    pre = dummy
    while True:
        # Check if k nodes remain
        kth = pre
        for _ in range(k):
            kth = kth.next
            if not kth:
                return dummy.next
        # Reverse k nodes starting at pre.next
        cur = pre.next
        for _ in range(k - 1):
            nxt = cur.next
            cur.next = nxt.next
            nxt.next = pre.next
            pre.next = nxt
        pre = cur
    return dummy.next


# ============================================================
# Way 2: Count total length, then reverse groups
# ============================================================
def reverse_k_group_2(head, k):
    """Count length; reverse groups of k; leave remainder."""
    if k <= 1 or not head:
        return head
    n = 0
    cur = head
    while cur:
        n += 1
        cur = cur.next
    dummy = ListNode(0)
    dummy.next = head
    pre = dummy
    groups = n // k
    for _ in range(groups):
        cur = pre.next
        for _ in range(k - 1):
            nxt = cur.next
            cur.next = nxt.next
            nxt.next = pre.next
            pre.next = nxt
        pre = cur
    return dummy.next


# ============================================================
# Way 3: Recursive
# ============================================================
def reverse_k_group_3(head, k):
    """Recursively reverse first group, then recurse on the rest."""
    if k <= 1 or not head:
        return head
    # Check if k nodes remain
    cur = head
    count = 0
    while cur and count < k:
        cur = cur.next
        count += 1
    if count < k:
        return head
    # Reverse first k nodes
    new_head = None
    tail = head
    for _ in range(k):
        nxt = head.next
        head.next = new_head
        new_head = head
        head = nxt
    tail.next = reverse_k_group_3(head, k)
    return new_head


# ============================================================
# Way 4: Standard prev/cur/nxt reverse per group
# ============================================================
def reverse_k_group_4(head, k):
    """Walk group-by-group; reverse with prev/cur/nxt."""
    if k <= 1 or not head:
        return head
    dummy = ListNode(0)
    dummy.next = head
    pre = dummy
    while True:
        kth = pre
        for _ in range(k):
            kth = kth.next
            if not kth:
                return dummy.next
        # Standard reverse of k nodes
        cur = pre.next
        prev = None
        for _ in range(k):
            nxt = cur.next
            cur.next = prev
            prev = cur
            cur = nxt
        # pre.next is original first (now last); prev is new first
        pre.next.next = cur  # original first's next -> first after group
        pre.next = prev       # pre.next -> new first (original last)
        pre = pre.next.next if False else (pre.next.next if False else None)
        # Reset pre to original first (now last)
        # The pre variable is still pointing to original position; advance it to original first of group (now last)
        # We need pre to be the new last (which was the original first).
        # Original first was pre.next before; let's recompute.
        # Actually we overwrote pre.next. Let's do it differently.
        # Easier: track new_last.
        # Reset by walking dummy
        # Just restart the loop: pre has not been advanced correctly.
        # Let me fix this approach by using a different strategy.
        return dummy.next  # placeholder
    return dummy.next


# Re-write Way 4 cleanly:
def reverse_k_group_4(head, k):
    """Standard prev/cur/nxt reverse per group."""
    if k <= 1 or not head:
        return head
    dummy = ListNode(0)
    dummy.next = head
    pre = dummy
    while True:
        kth = pre
        for _ in range(k):
            kth = kth.next
            if not kth:
                return dummy.next
        # Reverse k nodes with prev/cur/nxt
        cur = pre.next
        prev = None
        first_of_group = cur
        for _ in range(k):
            nxt = cur.next
            cur.next = prev
            prev = cur
            cur = nxt
        # prev = new head of group, first_of_group = new tail
        pre.next = prev
        first_of_group.next = cur
        pre = first_of_group
    return dummy.next


# ============================================================
# Way 5: Stack-based
# ============================================================
def reverse_k_group_5(head, k):
    """Push group onto stack; pop to reverse."""
    if k <= 1 or not head:
        return head
    dummy = ListNode(0)
    dummy.next = head
    pre = dummy
    cur = head
    while cur:
        # Collect k nodes
        stack = []
        end = cur
        for _ in range(k):
            if not end:
                break
            stack.append(end)
            end = end.next
        if len(stack) < k:
            # leave as-is, just connect pre -> cur
            pre.next = cur
            break
        # Pop in reverse to form the new chain
        new_head = stack.pop()
        new_tail = new_head
        while stack:
            new_tail.next = stack.pop()
            new_tail = new_tail.next
        new_tail.next = end
        pre.next = new_head
        pre = new_tail
        cur = end
    return dummy.next


# ============================================================
# Way 6: Build into array; rebuild with group reverses
# ============================================================
def reverse_k_group_6(head, k):
    """Collect values; rebuild with reversed groups."""
    vals = []
    cur = head
    while cur:
        vals.append(cur.val)
        cur = cur.next
    n = len(vals)
    out = []
    for i in range(0, n, k):
        group = vals[i:i + k]
        if len(group) == k:
            out.extend(group[::-1])
        else:
            out.extend(group)
    return list_from_array(out)


# ============================================================
# Way 7: Class-based wrapper
# ============================================================
class KGroupReverser_7:
    def __init__(self, head, k):
        self.head = head
        self.k = k

    def reverse(self):
        return reverse_k_group_1(self.head, self.k)


def reverse_k_group_7(head, k):
    return KGroupReverser_7(head, k).reverse()


# ============================================================
# Way 8: Hash map by index
# ============================================================
def reverse_k_group_8(head, k):
    """Use dict to map index to node; relink groups."""
    if k <= 1 or not head:
        return head
    nodes = []
    cur = head
    while cur:
        nodes.append(cur)
        cur = cur.next
    n = len(nodes)
    groups = n // k
    for g in range(groups):
        s = g * k
        e = s + k - 1
        sub = nodes[s:e + 1][::-1]
        nodes[s:e + 1] = sub
    # Relink all
    for i in range(n - 1):
        nodes[i].next = nodes[i + 1]
    nodes[-1].next = None
    return nodes[0]


# ============================================================
# Way 9: Find k-th node first, then process
# ============================================================
def reverse_k_group_9(head, k):
    """Find k-th from start; if exists, reverse group and continue."""
    if k <= 1 or not head:
        return head
    dummy = ListNode(0)
    dummy.next = head
    pre = dummy
    while True:
        # Find k-th node (1-indexed from pre.next)
        kth = pre.next
        for _ in range(k - 1):
            if not kth:
                return dummy.next
            kth = kth.next
        if not kth:
            return dummy.next
        # Reverse from pre.next (inclusive) to kth (inclusive)
        cur = pre.next
        first_of_group = cur
        prev = None
        for _ in range(k):
            nxt = cur.next
            cur.next = prev
            prev = cur
            cur = nxt
        # prev is new head, first_of_group is new tail
        pre.next = prev
        first_of_group.next = cur  # cur is first node after group
        pre = first_of_group
    return dummy.next


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def reverse_k_group_10(head, k):
    """
    THE ONE TO MEMORIZE.

    1. dummy -> head.
    2. While there are k nodes starting at pre.next:
       a. cur = pre.next.
       b. Repeat k-1 times:
          nxt = cur.next
          cur.next = nxt.next
          nxt.next = pre.next
          pre.next = nxt
       c. pre = cur (advance past the reversed group).
    3. Return dummy.next.

    Time:  O(n)
    Space: O(1).
    """
    if k <= 1 or not head:
        return head
    dummy = ListNode(0)
    dummy.next = head
    pre = dummy
    while True:
        kth = pre
        for _ in range(k):
            kth = kth.next
            if not kth:
                return dummy.next
        cur = pre.next
        for _ in range(k - 1):
            nxt = cur.next
            cur.next = nxt.next
            nxt.next = pre.next
            pre.next = nxt
        pre = cur
    return dummy.next


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to reverse every consecutive group of k nodes in a linked list.
Groups that don't have k nodes remain unchanged."

Key Insight:
"Use a dummy node. Walk to find the k-th node from the current position.
If fewer than k remain, return. Otherwise, reverse the group using head-
insertion: each iteration moves the next node to the front of the window.
After k-1 iterations, the group is reversed; advance `pre` to the new tail."

Algorithm:
1. dummy -> head. pre = dummy.
2. Walk k steps from pre to find the k-th node. If k-th is None, return.
3. cur = pre.next.
4. Repeat k-1 times:
   - nxt = cur.next
   - cur.next = nxt.next
   - nxt.next = pre.next
   - pre.next = nxt
5. pre = cur. Repeat.

Edge Cases:
- k == 1: no-op.
- Empty list: return None.
- List shorter than k: return as-is.
- k == n: full reverse.

KEY TRICK:
The head-insertion within a window of k nodes. After k-1 iterations, the
window is reversed and `pre` becomes the new tail (which was the original
first).

RELATED PROBLEMS:
- Reverse Linked List II (LC 92).
- Swap Nodes in Pairs (LC 24).
- Reverse Nodes in Even Length Groups (LC 2074).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([1, 2, 3, 4, 5], 2, [2, 1, 4, 3, 5], "Standard LC25 k=2"),
        ([1, 2, 3, 4, 5], 3, [3, 2, 1, 4, 5], "Standard LC25 k=3"),
        ([1, 2, 3, 4, 5], 1, [1, 2, 3, 4, 5], "k=1 no-op"),
        ([1, 2, 3, 4, 5], 5, [5, 4, 3, 2, 1], "k=n full reverse"),
        ([], 2, [], "Empty"),
        ([1, 2], 3, [1, 2], "Shorter than k"),
        ([1, 2, 3, 4, 5, 6], 2, [2, 1, 4, 3, 6, 5], "k=2 even"),
    ]

    implementations = [
        ("Way 1: Head-insert (BEST)", reverse_k_group_1),
        ("Way 2: Count + groups", reverse_k_group_2),
        ("Way 3: Recursive", reverse_k_group_3),
        ("Way 4: Standard reverse", reverse_k_group_4),
        ("Way 5: Stack", reverse_k_group_5),
        ("Way 6: Array rebuild", reverse_k_group_6),
        ("Way 7: Class-based", reverse_k_group_7),
        ("Way 8: Hash map", reverse_k_group_8),
        ("Way 9: Find k-th", reverse_k_group_9),
        ("Way 10: Final cleanest", reverse_k_group_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for inp, k, expected, desc in test_cases:
            try:
                head = list_from_array(copy.deepcopy(inp))
                result = fn(head, k)
                got = list_to_array(result)
                if got == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: input={inp} k={k} expected={expected} got={got}")
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