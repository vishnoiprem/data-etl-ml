"""
Reverse Nodes in Even Length Groups - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/reverse-nodes-in-even-length-groups

Given the head of a linked list, reverse nodes in each group of size k where
k is even; odd-sized groups are left as-is. Group sizes alternate: 1, 2, 3, ...

Wait, more carefully: starting at index 1, groups of consecutive increasing
length. Reverse only groups whose length is even.

Examples:
    [1,2,3,4] -> [1,2,3,4] (group sizes 1, 2, 3 -> only reverse size 2 -> [1,3,2,4]? Let me re-check)
    Actually: indices 0..n-1, groups of size 1, 2, 3, 4, ...
    [1,2,3,4]: group 1 = [1], group 2 = [2,3] (size 2 -> reverse -> [3,2]), group 3 = [4] (size 1).
    So result: [1,3,2,4].

Constraints:
- 1 <= n <= 10^5
- 1 <= Node.val <= 10^5
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
# Way 1: Group-by-group with size detection (BEST - Memorize!)
# ============================================================
def reverse_even_groups_1(head):
    """For each group, detect actual size; reverse only if even."""
    if not head or not head.next:
        return head
    dummy = ListNode(0)
    dummy.next = head
    pre = dummy
    group_size = 1
    while pre.next:
        # Find actual group size
        cur = pre.next
        k = 0
        while cur and k < group_size:
            cur = cur.next
            k += 1
        # k is actual group size; cur is first node after group
        if k % 2 == 0 and k == group_size:
            # Reverse this group using head-insertion
            first = pre.next
            cur = first
            for _ in range(group_size - 1):
                nxt = cur.next
                cur.next = nxt.next
                nxt.next = pre.next
                pre.next = nxt
            pre = first
        else:
            # Don't reverse; advance pre past the k nodes of this group
            for _ in range(k):
                pre = pre.next
        group_size += 1
    return dummy.next


# ============================================================
# Way 2: Collect into array, process groups, rebuild
# ============================================================
def reverse_even_groups_2(head):
    """Collect values; reverse even-sized groups; rebuild."""
    vals = []
    cur = head
    while cur:
        vals.append(cur.val)
        cur = cur.next
    n = len(vals)
    out = []
    i = 0
    group_size = 1
    while i < n:
        end = min(i + group_size, n)
        group = vals[i:end]
        if len(group) % 2 == 0 and len(group) == group_size:
            out.extend(group[::-1])
        else:
            out.extend(group)
        i = end
        group_size += 1
    return list_from_array(out)


# ============================================================
# Way 3: Recursive
# ============================================================
def reverse_even_groups_3(head):
    """Recursive helper."""
    if not head:
        return None
    # Find the k-th node from start (group_size k)
    cur = head
    count = 0
    while cur and count < 1:
        count += 1
        cur = cur.next
    # Actually, we need to detect actual group size. Pass group_size = 1 initially.
    return _helper(head, 1)


def _helper(node, group_size):
    if not node:
        return None
    # Find actual group size
    cur = node
    k = 0
    while cur and k < group_size:
        cur = cur.next
        k += 1
    # If odd size or incomplete, advance
    if k % 2 == 1 or k < group_size:
        # Connect to recursive call
        last_in_group = node
        for _ in range(k - 1):
            last_in_group = last_in_group.next
        last_in_group.next = _helper(cur, group_size + 1)
        return node
    # Reverse group of size k
    new_head = None
    tail = node
    for _ in range(k):
        nxt = node.next
        node.next = new_head
        new_head = node
        node = nxt
    # tail is now the last of reversed group
    tail.next = _helper(node, group_size + 1)
    return new_head


# ============================================================
# Way 4: Hash map + relink
# ============================================================
def reverse_even_groups_4(head):
    """Use index map; reverse even-sized groups; relink."""
    if not head or not head.next:
        return head
    nodes = []
    cur = head
    while cur:
        nodes.append(cur)
        cur = cur.next
    n = len(nodes)
    i = 0
    group_size = 1
    while i < n:
        end = min(i + group_size, n)
        if (end - i) % 2 == 0 and (end - i) == group_size:
            sub = nodes[i:end][::-1]
            nodes[i:end] = sub
        i = end
        group_size += 1
    # Relink
    for j in range(n - 1):
        nodes[j].next = nodes[j + 1]
    nodes[-1].next = None
    return nodes[0]


# ============================================================
# Way 5: Walk with explicit pointer math
# ============================================================
def reverse_even_groups_5(head):
    """Walk pointer-by-pointer; reverse even groups."""
    if not head or not head.next:
        return head
    dummy = ListNode(0)
    dummy.next = head
    pre = dummy
    group_size = 1
    while True:
        cur = pre.next
        k = 0
        while cur and k < group_size:
            cur = cur.next
            k += 1
        if k == 0:
            break
        if k % 2 == 0 and k == group_size:
            first = pre.next
            cur = first
            for _ in range(group_size - 1):
                nxt = cur.next
                cur.next = nxt.next
                nxt.next = pre.next
                pre.next = nxt
            pre = first
        else:
            for _ in range(k):
                pre = pre.next
        group_size += 1
    return dummy.next


# ============================================================
# Way 6: Two-pass with prev/cur/nxt
# ============================================================
def reverse_even_groups_6(head):
    """Walk prev/cur/nxt; reverse even groups in place."""
    if not head or not head.next:
        return head
    dummy = ListNode(0)
    dummy.next = head
    pre = dummy
    group_size = 1
    while pre.next:
        cur = pre.next
        k = 0
        end = cur
        while end and k < group_size:
            end = end.next
            k += 1
        if k % 2 == 0 and k == group_size:
            first = cur
            prev = None
            for _ in range(k):
                nxt = cur.next
                cur.next = prev
                prev = cur
                cur = nxt
            pre.next = prev
            first.next = cur
            pre = first
        else:
            for _ in range(k):
                if pre.next:
                    pre = pre.next
        group_size += 1
    return dummy.next


# ============================================================
# Way 7: Class-based wrapper
# ============================================================
class EvenGroupReverser_7:
    def __init__(self, head):
        self.head = head

    def reverse(self):
        return reverse_even_groups_1(self.head)


def reverse_even_groups_7(head):
    return EvenGroupReverser_7(head).reverse()


# ============================================================
# Way 8: Use a helper function for "reverse k nodes"
# ============================================================
def reverse_even_groups_8(head):
    """Use helper to reverse k nodes."""
    def reverse_k(start, k):
        prev = None
        cur = start
        for _ in range(k):
            nxt = cur.next
            cur.next = prev
            prev = cur
            cur = nxt
        return prev, start  # new_start, new_end

    if not head or not head.next:
        return head
    dummy = ListNode(0)
    dummy.next = head
    pre = dummy
    group_size = 1
    while pre.next:
        cur = pre.next
        k = 0
        while cur and k < group_size:
            cur = cur.next
            k += 1
        if k == 0:
            break
        if k % 2 == 0 and k == group_size:
            new_start, new_end = reverse_k(pre.next, k)
            pre.next = new_start
            new_end.next = cur
            pre = new_end
        else:
            for _ in range(k):
                if pre.next:
                    pre = pre.next
        group_size += 1
    return dummy.next


# ============================================================
# Way 9: Iterative with stack
# ============================================================
def reverse_even_groups_9(head):
    """Use stack for each group; pop if even-sized complete group."""
    if not head or not head.next:
        return head
    dummy = ListNode(0)
    dummy.next = head
    pre = dummy
    cur = head
    group_size = 1
    while cur:
        stack = []
        end = cur
        k = 0
        while end and k < group_size:
            stack.append(end)
            end = end.next
            k += 1
        if k % 2 == 0 and k == group_size:
            new_head = stack.pop()
            new_tail = new_head
            while stack:
                new_tail.next = stack.pop()
                new_tail = new_tail.next
            new_tail.next = end
            pre.next = new_head
            pre = new_tail
            cur = end
        else:
            for _ in range(k):
                if pre.next:
                    pre = pre.next
            cur = end
        group_size += 1
    return dummy.next


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def reverse_even_groups_10(head):
    """
    THE ONE TO MEMORIZE.

    1. dummy -> head. pre = dummy. group_size = 1.
    2. While pre.next exists:
       a. Walk k=group_size steps from pre.next to find the actual group end.
       b. If k == group_size and k is even:
          - Reverse this group using head-insertion.
          - pre = first (now last of reversed group).
       c. Else: advance pre past the k nodes; don't reverse.
       d. group_size += 1.
    3. Return dummy.next.

    Time:  O(n)
    Space: O(1).
    """
    if not head or not head.next:
        return head
    dummy = ListNode(0)
    dummy.next = head
    pre = dummy
    group_size = 1
    while pre.next:
        cur = pre.next
        k = 0
        while cur and k < group_size:
            cur = cur.next
            k += 1
        if k == 0:
            break
        if k % 2 == 0 and k == group_size:
            first = pre.next
            cur = first
            for _ in range(group_size - 1):
                nxt = cur.next
                cur.next = nxt.next
                nxt.next = pre.next
                pre.next = nxt
            pre = first
        else:
            for _ in range(k):
                if pre.next:
                    pre = pre.next
        group_size += 1
    return dummy.next


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to reverse nodes in groups of consecutive increasing size (1, 2, 3, ...).
But only reverse groups whose actual size is even (and complete)."

Key Insight:
"Walk through the list group by group. For each group of expected size
`group_size`, count how many nodes actually remain. If the count equals
group_size AND group_size is even, reverse the group. Otherwise, leave
it alone."

Algorithm:
1. dummy -> head. pre = dummy. group_size = 1.
2. While pre.next:
   a. Walk k=group_size steps from pre.next; cur is first after group.
   b. If k == group_size and k is even: reverse the group.
      Use head-insertion: for each of (group_size - 1) steps, move next to front.
      pre becomes the new tail (originally first of group).
   c. Else: advance pre past the k nodes.
   d. group_size += 1.

Edge Cases:
- Single node: return as-is.
- Last group incomplete: don't reverse.
- Even-sized groups: reverse.
- Odd-sized complete groups: leave alone.

KEY TRICK:
Detecting actual group size matters because the last group may be smaller
than expected. Only reverse if actual size equals expected AND even.

RELATED PROBLEMS:
- Reverse Nodes in k-Group (LC 25).
- Swap Nodes in Pairs (LC 24).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([1, 2, 3, 4], [1, 3, 2, 4], "LC2074 standard"),
        ([1, 2, 3, 4, 5], [1, 3, 2, 4, 5], "5 nodes (group 3 incomplete)"),
        ([1, 1, 2, 2, 3, 3, 4, 4], [1, 2, 1, 2, 3, 3, 4, 4], "8 nodes (groups 1,2,3,2)"),
        ([5], [5], "Single"),
        ([1, 2], [1, 2], "Two nodes (group 1=1, group 2 incomplete)"),
        ([1, 2, 3, 4, 5, 6, 7, 8], [1, 3, 2, 4, 5, 6, 7, 8], "8 nodes (groups 1,2,3,2 incomplete)"),
    ]

    implementations = [
        ("Way 1: Head-insert (BEST)", reverse_even_groups_1),
        ("Way 2: Array rebuild", reverse_even_groups_2),
        ("Way 3: Recursive", reverse_even_groups_3),
        ("Way 4: Hash map", reverse_even_groups_4),
        ("Way 5: Pointer walk", reverse_even_groups_5),
        ("Way 6: prev/cur/nxt", reverse_even_groups_6),
        ("Way 7: Class-based", reverse_even_groups_7),
        ("Way 8: Reverse helper", reverse_even_groups_8),
        ("Way 9: Stack", reverse_even_groups_9),
        ("Way 10: Final cleanest", reverse_even_groups_10),
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