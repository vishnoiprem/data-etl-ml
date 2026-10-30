"""
Delete N Nodes After M Nodes of a Linked List - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/delete-n-nodes-after-m-nodes-of-a-linked-list

Given the head of a linked list and two integers m and n, traverse the
linked list and keep the first m nodes, then delete the next n nodes.
Repeat until end of list. Return the head.

KEY INSIGHT:
Walk group-by-group: keep m nodes, skip n nodes. The trick is to handle
the boundary carefully so the skip lands correctly.

Examples:
    1->2->3->4->5->6->7->8->9->10->11->12, m=2, n=3  =>  1->2->6->7->12

Constraints:
- 1 <= number of nodes <= 10^4
- 1 <= m, n <= 1000
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
# Way 1: Walk m + skip n, repeat (BEST - Memorize!)
# ============================================================
def delete_n_after_m_1(head, m, n):
    """Walk m nodes, skip n nodes, repeat."""
    cur = head
    while cur:
        # Walk m-1 steps to find end of "keep" segment
        for _ in range(m - 1):
            if not cur.next:
                return head
            cur = cur.next
        # cur is at the last kept node. cur.next is first to delete.
        if not cur.next:
            return head
        to_delete = cur.next
        for _ in range(n - 1):
            if not to_delete.next:
                break
            to_delete = to_delete.next
        # to_delete is the last to delete; its next is what we keep next.
        cur.next = to_delete.next
        # Move cur to start of next keep segment
        cur = cur.next
    return head


# ============================================================
# Way 2: Walk with explicit prev
# ============================================================
def delete_n_after_m_2(head, m, n):
    """Walk prev; skip n nodes after m kept."""
    if not head:
        return head
    cur = head
    while cur:
        # Skip m - 1 more (we are already at first)
        for _ in range(m - 1):
            if not cur.next:
                return head
            cur = cur.next
        # cur is at last kept; delete next n
        target = cur.next
        for _ in range(n):
            if not target:
                break
            target = target.next
        cur.next = target
        cur = target
    return head


# ============================================================
# Way 3: Recursive
# ============================================================
def delete_n_after_m_3(head, m, n):
    """Recursive helper."""
    if not head:
        return head
    # Walk m nodes; cur is at the last kept
    cur = head
    for _ in range(m - 1):
        if not cur.next:
            return head
        cur = cur.next
    # Skip n nodes
    to_delete = cur.next
    for _ in range(n):
        if not to_delete:
            break
        to_delete = to_delete.next
    cur.next = delete_n_after_m_3(to_delete, m, n)
    return head


# ============================================================
# Way 4: Collect into array; rebuild
# ============================================================
def delete_n_after_m_4(head, m, n):
    """Build values; alternate keep m/drop n; rebuild."""
    vals = []
    cur = head
    while cur:
        vals.append(cur.val)
        cur = cur.next
    out = []
    i = 0
    while i < len(vals):
        out.extend(vals[i:i + m])
        i += m + n
    return list_from_array(out)


# ============================================================
# Way 5: Class-based wrapper
# ============================================================
class NodeKeeper_5:
    def __init__(self, head, m, n):
        self.head = head
        self.m = m
        self.n = n

    def process(self):
        return delete_n_after_m_1(self.head, self.m, self.n)


def delete_n_after_m_5(head, m, n):
    return NodeKeeper_5(head, m, n).process()


# ============================================================
# Way 6: Count then walk
# ============================================================
def delete_n_after_m_6(head, m, n):
    """Count total length; rebuild keep list."""
    vals = []
    cur = head
    while cur:
        vals.append(cur.val)
        cur = cur.next
    out = []
    i = 0
    while i < len(vals):
        out.extend(vals[i:i + m])
        i += m + n
    return list_from_array(out)


# ============================================================
# Way 7: Hash map by index
# ============================================================
def delete_n_after_m_7(head, m, n):
    """Use index map to filter."""
    nodes = []
    cur = head
    while cur:
        nodes.append(cur)
        cur = cur.next
    keep_indices = set()
    i = 0
    while i < len(nodes):
        for j in range(i, min(i + m, len(nodes))):
            keep_indices.add(j)
        i += m + n
    kept = [nodes[i] for i in sorted(keep_indices)]
    if not kept:
        return None
    for j in range(len(kept) - 1):
        kept[j].next = kept[j + 1]
    kept[-1].next = None
    return kept[0]


# ============================================================
# Way 8: Two-pointer walk with explicit keep/skip counters
# ============================================================
def delete_n_after_m_8(head, m, n):
    """Use counters; walk."""
    if not head:
        return head
    dummy = ListNode(0)
    dummy.next = head
    cur = head
    while cur:
        # Walk m-1 steps from cur (cur is at last kept)
        for _ in range(m - 1):
            if not cur.next:
                return dummy.next
            cur = cur.next
        # cur is at last kept; cur.next is first to delete (or None)
        target = cur.next
        for _ in range(n):
            if not target:
                break
            target = target.next
        cur.next = target
        cur = target
    return dummy.next


# ============================================================
# Way 9: Walk with chunk boundaries
# ============================================================
def delete_n_after_m_9(head, m, n):
    """Walk with explicit boundary tracking."""
    if not head:
        return head
    cur = head
    while cur:
        # Advance m nodes
        for _ in range(m - 1):
            if not cur.next:
                return head
            cur = cur.next
        # cur is at the last kept
        # Skip n nodes by walking n steps from cur.next
        next_start = cur.next
        for _ in range(n):
            if not next_start:
                break
            next_start = next_start.next
        cur.next = next_start
        cur = next_start
    return head


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def delete_n_after_m_10(head, m, n):
    """
    THE ONE TO MEMORIZE.

    1. cur = head.
    2. While cur:
       a. Advance m-1 steps (cur is now at the last kept node).
       b. If cur.next is None: return.
       c. Walk n-1 steps from cur.next; the (n-1)-th node is the last to delete.
       d. cur.next = last_to_delete.next.
       e. cur = cur.next (start of next keep segment).

    Time:  O(n)
    Space: O(1).
    """
    cur = head
    while cur:
        for _ in range(m - 1):
            if not cur.next:
                return head
            cur = cur.next
        if not cur.next:
            return head
        to_delete = cur.next
        for _ in range(n - 1):
            if not to_delete.next:
                break
            to_delete = to_delete.next
        cur.next = to_delete.next
        cur = cur.next
    return head


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to delete n nodes after every m nodes of a linked list."

Key Insight:
"Walk group-by-group: keep m nodes (advance cur m-1 steps), then skip n
nodes (walk n-1 steps from cur.next to find last to delete). Then
connect cur.next to last_to_delete.next and move cur to next segment."

Algorithm:
1. cur = head.
2. While cur:
   a. Advance m-1 steps (cur is at last kept).
   b. If cur.next is None: return.
   c. Walk n-1 steps from cur.next (to_delete is last to delete).
   d. cur.next = to_delete.next.
   e. cur = cur.next (start of next keep).

Edge Cases:
- m + n covers entire list: end may end early.
- Last segment has fewer than m nodes: just return.
- Last segment has fewer than n to delete: skip what's there.

KEY TRICK:
Walk m-1 steps to position at last kept, then n-1 steps from cur.next to
find last to delete. The skip lands correctly when cur.next = to_delete.next.

RELATED PROBLEMS:
- Remove Duplicates from Sorted List (LC 83).
- Remove Nth Node From End (LC 19).
- Delete Node in a Linked List (LC 237).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        (list(range(1, 13)), 2, 3, [1, 2, 6, 7, 11, 12], "Standard LC1474"),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], 1, 3, [1, 5, 9], "m=1, n=3"),
        ([1, 2, 3, 4, 5], 5, 0, [1, 2, 3, 4, 5], "n=0 no delete"),
        ([1, 2, 3], 1, 1, [1, 3], "Alternating"),
        ([1, 2, 3, 4, 5], 3, 1, [1, 2, 3, 5], "End partial"),
        ([], 1, 1, [], "Empty"),
    ]

    implementations = [
        ("Way 1: Walk m+n (BEST)", delete_n_after_m_1),
        ("Way 2: prev + skip", delete_n_after_m_2),
        ("Way 3: Recursive", delete_n_after_m_3),
        ("Way 4: Array rebuild", delete_n_after_m_4),
        ("Way 5: Class-based", delete_n_after_m_5),
        ("Way 6: Count + walk", delete_n_after_m_6),
        ("Way 7: Hash map", delete_n_after_m_7),
        ("Way 8: Dummy + counters", delete_n_after_m_8),
        ("Way 9: Boundary track", delete_n_after_m_9),
        ("Way 10: Final cleanest", delete_n_after_m_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for inp, m, n, expected, desc in test_cases:
            try:
                head = list_from_array(copy.deepcopy(inp))
                result = fn(head, m, n)
                got = list_to_array(result)
                if got == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: input={inp} m={m} n={n} expected={expected} got={got}")
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