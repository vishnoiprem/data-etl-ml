"""
Swapping Nodes in a Linked List - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/swapping-nodes-in-a-linked-list

Given the head of a linked list and an integer k, swap the values of the
k-th node from the beginning and the k-th node from the end.

KEY INSIGHT:
Walk once to find the k-th from start. Then use a slow/fast pair: fast
advances k steps; then both advance together until fast is at end. The
slow pointer is now at k-th from end. Swap their values.

Examples:
    1->2->3->4->5, k=2  =>  swap 2 and 4 =>  1->4->3->2->5

Constraints:
- 1 <= k <= n <= 10^5
- 1 <= Node.val <= 100
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
# Way 1: Slow/fast pair (BEST - Memorize!)
# ============================================================
def swap_nodes_1(head, k):
    """Slow/fast: fast advances k steps; then walk both until fast at end."""
    slow = head
    fast = head
    for _ in range(k):
        fast = fast.next
    # Now we want to find the k-th from end. Walk slow and fast together.
    while fast:
        slow = slow.next
        fast = fast.next
    # slow is now at (n - k)-th position from start (1-indexed: n-k+1)
    # But we want the k-th from end, which is the (n-k+1)-th from start.
    # Wait: when fast is at end (None), slow was at position (n-k+1)-1 = n-k from start.
    # So slow is at (n-k)-th node (1-indexed). The k-th from end = (n-k+1)-th from start.
    # Hmm, let me re-check.
    # Actually after the while loop, slow has been advanced (n-k) times, starting
    # at position 1. So slow is now at position (n-k+1) (1-indexed) from start.
    # Yes, that's the k-th from end (since (n-k+1) + (k-1) = n, i.e., k-th from end).
    # Now find the k-th from start: it's at position k. Let me get it via separate walk.
    kth_from_start = head
    for _ in range(k - 1):
        kth_from_start = kth_from_start.next
    # Swap values
    kth_from_start.val, slow.val = slow.val, kth_from_start.val
    return head


# ============================================================
# Way 2: Two passes with array
# ============================================================
def swap_nodes_2(head, k):
    """Convert to array, swap, rebuild."""
    vals = []
    cur = head
    while cur:
        vals.append(cur.val)
        cur = cur.next
    n = len(vals)
    if 1 <= k <= n:
        vals[k - 1], vals[n - k] = vals[n - k], vals[k - 1]
    return list_from_array(vals)


# ============================================================
# Way 3: Two-pass with pointers
# ============================================================
def swap_nodes_3(head, k):
    """First pass: find length. Then find k-th from start and end."""
    if not head:
        return head
    n = 0
    cur = head
    while cur:
        n += 1
        cur = cur.next
    target_last = n - k + 1  # 1-indexed position of k-th from end
    first = head
    for _ in range(k - 1):
        first = first.next
    last = head
    for _ in range(target_last - 1):
        last = last.next
    first.val, last.val = last.val, first.val
    return head


# ============================================================
# Way 4: Slow/fast with k+1 lead
# ============================================================
def swap_nodes_4(head, k):
    """Fast starts at head, slow at head. Fast advances k steps first."""
    if not head:
        return head
    fast = head
    for _ in range(k):
        fast = fast.next
    # fast is now k steps from head (1-indexed: at position k+1)
    # We need slow to land at position n-k+1 (the k-th from end).
    slow = head
    while fast:
        slow = slow.next
        fast = fast.next
    # slow is at position (n-k+1) (1-indexed) from start.
    # But we want to compare with the k-th from start, not from end of list.
    # The k-th from start is the one we need to swap with.
    kth_from_start = head
    for _ in range(k - 1):
        kth_from_start = kth_from_start.next
    # slow is kth from end (assuming kth_from_start != slow in some cases)
    kth_from_start.val, slow.val = slow.val, kth_from_start.val
    return head


# ============================================================
# Way 5: Walk and store nodes
# ============================================================
def swap_nodes_5(head, k):
    """Store all nodes in array; access by index; swap values."""
    if not head:
        return head
    nodes = []
    cur = head
    while cur:
        nodes.append(cur)
        cur = cur.next
    n = len(nodes)
    if 1 <= k <= n:
        nodes[k - 1].val, nodes[n - k].val = nodes[n - k].val, nodes[k - 1].val
    return head


# ============================================================
# Way 6: Single pass using deque
# ============================================================
def swap_nodes_6(head, k):
    """Walk once; maintain deque of last k nodes. The k-th seen -> swap with last."""
    from collections import deque
    if not head:
        return head
    dq = deque(maxlen=k)  # holds last k nodes
    first_kth = None
    cur = head
    pos = 0
    last_kth = None
    while cur:
        pos += 1
        if pos == k:
            first_kth = cur
        if len(dq) == k:
            # the front is the (pos-k+1)-th node; we want k-th from end
            # i.e., when we're at position n, we want the (n-k+1)-th.
            # last_kth: when pos = n, the k-th from end is dq[0].
            pass
        dq.append(cur)
        cur = cur.next
    # After loop, dq[-1] is the last node; dq[0] is the (n-k)-th from start, which
    # means dq[0] is the (k+1)-th from end. That's not what we want.
    # We want k-th from end. If k=2 and n=5: nodes at pos 1,2,3,4,5. k-th from end = pos 4.
    # dq at end holds: dq[0]=pos 4, dq[1]=pos 5. So dq[0] is k-th from end!
    # In general, dq[0] is the (n-k+1)-th = k-th from end.
    last_kth = dq[0]
    if first_kth and last_kth:
        first_kth.val, last_kth.val = last_kth.val, first_kth.val
    return head


# ============================================================
# Way 7: Class-based wrapper
# ============================================================
class NodeSwapper_7:
    def __init__(self, head, k):
        self.head = head
        self.k = k

    def swap(self):
        return swap_nodes_1(self.head, self.k)


def swap_nodes_7(head, k):
    return NodeSwapper_7(head, k).swap()


# ============================================================
# Way 8: Find k-th from start and from end in two walks (alt)
# ============================================================
def swap_nodes_8(head, k):
    """Find k-th from start, then walk from there to find length, then walk from head."""
    if not head:
        return head
    # Walk to find k-th from start
    first = head
    for _ in range(k - 1):
        first = first.next
    # Walk from first to end; count remaining nodes after first
    n_after_first = 0
    cur = first
    while cur:
        n_after_first += 1
        cur = cur.next
    total = (k - 1) + n_after_first  # total length
    # Walk from head to find total - k + 1 -th node (1-indexed from start)
    target = total - k + 1  # 1-indexed from start
    last = head
    for _ in range(target - 1):
        last = last.next
    first.val, last.val = last.val, first.val
    return head


# ============================================================
# Way 9: Hash map
# ============================================================
def swap_nodes_9(head, k):
    """Use dict to map index to node."""
    if not head:
        return head
    nodes = {}
    cur = head
    i = 0
    while cur:
        i += 1
        nodes[i] = cur
        cur = cur.next
    n = i
    if 1 <= k <= n:
        nodes[k].val, nodes[n - k + 1].val = nodes[n - k + 1].val, nodes[k].val
    return head


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def swap_nodes_10(head, k):
    """
    THE ONE TO MEMORIZE.

    1. slow = head, fast = head.
    2. Advance fast by k steps.
    3. While fast is not None:
       slow = slow.next
       fast = fast.next
    4. After loop, slow is the k-th from end.
    5. Walk again to find the k-th from start.
    6. Swap their values.

    Time:  O(n)
    Space: O(1).
    """
    if not head:
        return head
    slow = head
    fast = head
    for _ in range(k):
        fast = fast.next
    while fast:
        slow = slow.next
        fast = fast.next
    kth_from_start = head
    for _ in range(k - 1):
        kth_from_start = kth_from_start.next
    kth_from_start.val, slow.val = slow.val, kth_from_start.val
    return head


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to swap the values of the k-th node from the start and the k-th
node from the end of a linked list."

Key Insight:
"Use slow/fast pointers. Advance fast by k steps first. Then walk slow and
fast together until fast reaches the end. When fast is None, slow is at
the k-th node from the end."

Algorithm:
1. slow = head, fast = head.
2. Advance fast by k steps.
3. While fast is not None: advance both.
4. slow is now the k-th from end.
5. Walk again from head to find k-th from start.
6. Swap their values.

Edge Cases:
- k == 1: swap head with tail (might be same node).
- k == n/2 (and n even): the two nodes may be the same. No swap needed.
- k == n: swap head and tail.

KEY TRICK:
The slow/fast pattern finds the k-th from end in one pass. The second walk
to find k-th from start is necessary because we need both pointers.

RELATED PROBLEMS:
- Remove Nth Node From End (LC 19).
- Middle of the Linked List (LC 876).
- Linked List Cycle II (LC 142).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([1, 2, 3, 4, 5], 2, [1, 4, 3, 2, 5], "Standard LC1721"),
        ([7, 9, 6, 6, 7, 8, 3, 0, 9, 5], 5, [7, 9, 6, 6, 8, 7, 3, 0, 9, 5], "LC1721 official"),
        ([1], 1, [1], "Single"),
        ([1, 2], 1, [2, 1], "k=1 swap head and tail"),
        ([1, 2, 3], 2, [1, 2, 3], "k=2 middle, same node"),
        ([1, 2, 3, 4, 5], 3, [1, 2, 3, 4, 5], "k=3 middle, same node"),
    ]

    implementations = [
        ("Way 1: Slow/fast (BEST)", swap_nodes_1),
        ("Way 2: Array rebuild", swap_nodes_2),
        ("Way 3: Two-pass pointers", swap_nodes_3),
        ("Way 4: Slow/fast k+1", swap_nodes_4),
        ("Way 5: Store nodes", swap_nodes_5),
        ("Way 6: Deque", swap_nodes_6),
        ("Way 7: Class-based", swap_nodes_7),
        ("Way 8: Two walks alt", swap_nodes_8),
        ("Way 9: Hash map", swap_nodes_9),
        ("Way 10: Final cleanest", swap_nodes_10),
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