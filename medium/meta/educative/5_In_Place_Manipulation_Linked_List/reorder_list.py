"""
Reorder List - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/reorder-list

Given a singly linked list L: L0 -> L1 -> ... -> Ln-1, reorder it to:
L0 -> Ln-1 -> L1 -> Ln-2 -> L2 -> Ln-3 -> ...

KEY INSIGHT:
1. Find the middle (slow/fast).
2. Reverse the second half.
3. Merge the two halves alternately.

Examples:
    1 -> 2 -> 3 -> 4  =>  1 -> 4 -> 2 -> 3
    1 -> 2 -> 3 -> 4 -> 5  =>  1 -> 5 -> 2 -> 4 -> 3

Constraints:
- Number of nodes in range [0, 5 * 10^4]
- Modifying the list in-place is required.
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
# Way 1: Middle + reverse + merge (BEST - Memorize!)
# ============================================================
def reorder_list_1(head):
    """Find middle, reverse second half, merge alternately."""
    if not head or not head.next:
        return head

    def middle(h):
        slow = fast = h
        while fast.next and fast.next.next:
            slow = slow.next
            fast = fast.next.next
        return slow

    def reverse(h):
        prev = None
        cur = h
        while cur:
            nxt = cur.next
            cur.next = prev
            prev = cur
            cur = nxt
        return prev

    mid = middle(head)
    second = reverse(mid.next)
    mid.next = None

    # Merge: take from first, then from second, alternately
    first = head
    while second:
        t1 = first.next
        t2 = second.next
        first.next = second
        second.next = t1
        first = t1
        second = t2
    return head


# ============================================================
# Way 2: Collect values; rebuild in interleaved order
# ============================================================
def reorder_list_2(head):
    """Collect values, build new list in interleaved order."""
    if not head or not head.next:
        return head
    vals = []
    cur = head
    while cur:
        vals.append(cur.val)
        cur = cur.next
    n = len(vals)
    half = (n + 1) // 2  # first half has the extra if odd
    first = vals[:half]
    second = vals[half:][::-1]
    out = []
    for i in range(half):
        out.append(first[i])
        if i < len(second):
            out.append(second[i])
    return list_from_array(out)


# ============================================================
# Way 3: Recursive
# ============================================================
def reorder_list_3(head):
    """Recursive merge: take tail, then recurse on middle."""
    if not head or not head.next:
        return head

    def find_tail(node):
        prev = None
        cur = node
        while cur.next:
            prev = cur
            cur = cur.next
        return prev, cur  # prev is the new tail, cur is the actual last

    def helper(node):
        if not node or not node.next:
            return node
        prev, tail = find_tail(node)
        # If prev is the same as node, the list has only two nodes — done.
        if prev is node:
            return node
        next_node = node.next
        prev.next = None  # detach tail (prev is now the new last of inner)
        inner = helper(next_node)
        tail.next = inner
        node.next = tail
        return node

    return helper(head)


# ============================================================
# Way 4: Find middle with count, slice
# ============================================================
def reorder_list_4(head):
    """Count nodes; split at midpoint; reverse second; merge."""
    if not head or not head.next:
        return head
    n = 0
    cur = head
    while cur:
        n += 1
        cur = cur.next
    half = (n + 1) // 2
    cur = head
    for _ in range(half - 1):
        cur = cur.next
    second = cur.next
    cur.next = None

    # Reverse second
    prev = None
    cur = second
    while cur:
        nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
    second = prev

    # Merge
    first = head
    while second:
        t1 = first.next
        t2 = second.next
        first.next = second
        second.next = t1
        first = t1
        second = t2
    return head


# ============================================================
# Way 5: Use deque for alternating picks
# ============================================================
def reorder_list_5(head):
    """Store nodes in deque; alternately pop front and back."""
    if not head or not head.next:
        return head
    from collections import deque
    dq = deque()
    cur = head
    while cur:
        dq.append(cur)
        cur = cur.next
    new_head = dq.popleft()
    cur = new_head
    # Alternate: from left then from right
    from_right = True
    while dq:
        if from_right:
            nxt = dq.pop()
        else:
            nxt = dq.popleft()
        cur.next = nxt
        cur = nxt
        from_right = not from_right
    cur.next = None
    return new_head


# ============================================================
# Way 6: Stack-based
# ============================================================
def reorder_list_6(head):
    """Push values onto stack; rebuild interleaved."""
    if not head or not head.next:
        return head
    vals = []
    cur = head
    while cur:
        vals.append(cur.val)
        cur = cur.next
    n = len(vals)
    half = (n + 1) // 2
    first = vals[:half]
    second = vals[half:][::-1]
    out = []
    for i in range(half):
        out.append(first[i])
        if i < len(second):
            out.append(second[i])
    return list_from_array(out)


# ============================================================
# Way 7: Class-based wrapper
# ============================================================
class ListReorderer_7:
    def __init__(self, head):
        self.head = head

    def reorder(self):
        return reorder_list_1(self.head)


def reorder_list_7(head):
    return ListReorderer_7(head).reorder()


# ============================================================
# Way 8: Hash map by index
# ============================================================
def reorder_list_8(head):
    """Use dict to access by index; relink."""
    if not head or not head.next:
        return head
    nodes = []
    cur = head
    while cur:
        nodes.append(cur)
        cur = cur.next
    n = len(nodes)
    half = (n + 1) // 2
    # New order: 0, n-1, 1, n-2, 2, n-3, ...
    indices = []
    for i in range(half):
        indices.append(i)
        if n - 1 - i > i:
            indices.append(n - 1 - i)
    for k in range(len(indices) - 1):
        nodes[indices[k]].next = nodes[indices[k + 1]]
    nodes[indices[-1]].next = None
    return nodes[indices[0]]


# ============================================================
# Way 9: Iterative with arrays of pointers
# ============================================================
def reorder_list_9(head):
    """Build array of nodes; interleave; relink."""
    if not head or not head.next:
        return head
    nodes = []
    cur = head
    while cur:
        nodes.append(cur)
        cur = cur.next
    n = len(nodes)
    half = (n + 1) // 2
    left = nodes[:half]
    right = nodes[half:][::-1]
    cur = left[0]
    for i in range(half):
        cur.next = right[i] if i < len(right) else None
        cur = cur.next
        if cur is None:
            break
        cur.next = left[i + 1] if i + 1 < len(left) else None
        cur = cur.next
        if cur is None:
            break
    return left[0]


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def reorder_list_10(head):
    """
    THE ONE TO MEMORIZE.

    1. Find middle with slow/fast (slow ends at first half's tail).
    2. Reverse second half starting at mid.next.
    3. Merge the two halves alternately: first[0] -> second[0] -> first[1] -> ...

    Time:  O(n)
    Space: O(1).
    """
    if not head or not head.next:
        return head
    # 1. Middle
    slow = fast = head
    while fast.next and fast.next.next:
        slow = slow.next
        fast = fast.next.next
    # 2. Reverse second half
    second = slow.next
    slow.next = None
    prev = None
    cur = second
    while cur:
        nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
    second = prev
    # 3. Merge alternately
    first = head
    while second:
        t1 = first.next
        t2 = second.next
        first.next = second
        second.next = t1
        first = t1
        second = t2
    return head


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to reorder a linked list as L0, Ln-1, L1, Ln-2, L2, Ln-3, ..."

Key Insight:
"Three steps: (1) Find middle with slow/fast. (2) Reverse the second half.
(3) Merge the two halves alternately by taking one node from first, then
one from second, until second is exhausted."

Algorithm:
1. slow = fast = head. While fast.next and fast.next.next: advance.
2. Cut at slow.next; reverse second half.
3. Walk first and second in lockstep, interleave.

Edge Cases:
- Empty / single node: return as-is.
- Two nodes: stays the same.
- Odd length: middle node ends up at end.
- Even length: clean split.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| 3-step    | O(n)   | O(1)   |
| Recursive | O(n^2) | O(n)   |
| Array     | O(n)   | O(n)   |
+-----------+--------+--------+

KEY TRICK:
After reverse, the second half is shorter or equal in length to the first
(if even) or one shorter (if odd). Always advance `second` after linking;
it's the loop terminator.

RELATED PROBLEMS:
- Reverse Linked List II (LC 92).
- Palindrome Linked List (LC 234).
- Odd Even Linked List (LC 328).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([1, 2, 3, 4], [1, 4, 2, 3], "Standard even LC143"),
        ([1, 2, 3, 4, 5], [1, 5, 2, 4, 3], "Standard odd LC143"),
        ([], [], "Empty"),
        ([1], [1], "Single"),
        ([1, 2], [1, 2], "Two nodes"),
        ([1, 2, 3], [1, 3, 2], "Three nodes"),
    ]

    implementations = [
        ("Way 1: 3-step (BEST)", reorder_list_1),
        ("Way 2: Array rebuild", reorder_list_2),
        ("Way 3: Recursive", reorder_list_3),
        ("Way 4: Count + slice", reorder_list_4),
        ("Way 5: Deque", reorder_list_5),
        ("Way 6: Stack", reorder_list_6),
        ("Way 7: Class-based", reorder_list_7),
        ("Way 8: Hash by index", reorder_list_8),
        ("Way 9: Iterative arrays", reorder_list_9),
        ("Way 10: Final cleanest", reorder_list_10),
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
