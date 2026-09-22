"""
Remove nth Node from End of List - 10 Ways
===========================================
Given the head of a singly linked list, remove the n-th node from the end
and return the head.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/remove-nth-node-from-end-of-list

Examples:
    [1,2,3,4,5], n=2 -> [1,2,3,5]   (remove 4)
    [1], n=1 -> []
    [1,2], n=1 -> [1]

Constraints:
- 1 <= sz <= 30
- 0 <= Node.val <= 100
- 1 <= n <= sz

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Remove n-th from end of a singly linked list. Singly linked means no
    backward pointer. Single pass preferred."

2. KEY INSIGHT:
   "Two-pointer with a GAP of n. Move 'fast' n steps ahead. Then move both
    until 'fast' reaches the end. 'slow' is now at the (n+1)-th from end,
    which is the node BEFORE the target."

3. PATTERN RECOGNITION:
   "Fast/slow two-pointer with gap = n. Classic one-pass trick."

4. EDGE CASES:
   - n == sz (remove head) -> return head.next
   - sz == 1, n == 1 -> return None
   - n == 1 (remove last) -> traverse to second-to-last

5. TRICKY DETAIL:
   "Use a DUMMY head before real head. This avoids special-casing when
    removing the first node. Set 'fast = dummy' initially, not 'head'."

6. ALGORITHM:
   "dummy = ListNode(0, head)
    fast = slow = dummy
    for _ in range(n): fast = fast.next
    while fast.next: fast = fast.next; slow = slow.next
    slow.next = slow.next.next
    return dummy.next"

7. WHY TWO-POINTERS:
   "After advancing fast by n, the gap between fast and slow is n.
    When fast reaches the end (None), slow is exactly n behind, i.e.,
    at the node BEFORE the n-th from end."

8. COMPLEXITY:
   "Time: O(sz) — single pass.
    Space: O(1)."

9. CODE STRUCTURE:
   "def removeNth(head, n):
        dummy = ListNode(0, head)
        fast = slow = dummy
        advance fast by n
        while fast.next: fast = fast.next; slow = slow.next
        slow.next = slow.next.next
        return dummy.next"

10. MENTAL TRACE:
    [1,2,3,4,5], n=2:
    dummy -> 1 -> 2 -> 3 -> 4 -> 5 -> None
    fast at dummy; advance by 2 -> fast at node '2'
    Loop: fast.next? 3 yes -> fast=3, slow=1
          fast.next? 4 yes -> fast=4, slow=2
          fast.next? 5 yes -> fast=5, slow=3
          fast.next? None -> exit
    slow is at node '3'. slow.next is '4'. Set slow.next = 4.next = 5.
    List: 1 -> 2 -> 3 -> 5 ✓
"""


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def to_linked(lst):
    """Helper to build a linked list from a Python list."""
    if not lst:
        return None
    head = ListNode(lst[0])
    cur = head
    for v in lst[1:]:
        cur.next = ListNode(v)
        cur = cur.next
    return head


def from_linked(head):
    """Helper to convert linked list back to Python list."""
    res = []
    while head:
        res.append(head.val)
        head = head.next
    return res


# Solution 1: Canonical two-pointer with dummy (BEST)
def remove_nth_v1(head, n):
    dummy = ListNode(0, head)
    fast = slow = dummy
    for _ in range(n):
        fast = fast.next
    while fast.next:
        fast = fast.next
        slow = slow.next
    slow.next = slow.next.next
    return dummy.next


# Solution 2: Two-pointer WITHOUT dummy (special-case the head)
def remove_nth_v2(head, n):
    fast = head
    for _ in range(n):
        fast = fast.next
    if not fast:  # removing the head
        return head.next
    slow = head
    while fast.next:
        fast = fast.next
        slow = slow.next
    slow.next = slow.next.next
    return head


# Solution 3: Two-pass — count length, then find target
def remove_nth_v3(head, n):
    # Pass 1: count
    length = 0
    cur = head
    while cur:
        length += 1
        cur = cur.next
    # Pass 2: walk to (length - n)-th node
    target_idx = length - n
    if target_idx == 0:
        return head.next
    cur = head
    for _ in range(target_idx - 1):
        cur = cur.next
    cur.next = cur.next.next
    return head


# Solution 4: Using a stack
def remove_nth_v4(head, n):
    dummy = ListNode(0, head)
    stack = []
    cur = dummy
    while cur:
        stack.append(cur)
        cur = cur.next
    # The n-th from end is at stack[len-n]
    target_idx = len(stack) - n
    prev = stack[target_idx - 1]
    prev.next = prev.next.next
    return dummy.next


# Solution 5: Recursive with a counter
def remove_nth_v5(head, n):
    counter = [0]

    def helper(node):
        if not node:
            return None
        node.next = helper(node.next)
        counter[0] += 1
        if counter[0] == n:
            return node.next
        return node

    return helper(head)


# Solution 6: Using a list to store all nodes
def remove_nth_v6(head, n):
    nodes = []
    cur = head
    while cur:
        nodes.append(cur)
        cur = cur.next
    target = len(nodes) - n
    if target == 0:
        return head.next
    nodes[target - 1].next = nodes[target].next
    return head


# Solution 7: Two-pointer with head initialization
def remove_nth_v7(head, n):
    fast = head
    slow = head
    for _ in range(n):
        fast = fast.next
    if fast is None:
        return head.next
    while fast.next:
        fast = fast.next
        slow = slow.next
    slow.next = slow.next.next
    return head


# Solution 8: Two-pass with sentinel
def remove_nth_v8(head, n):
    dummy = ListNode(0, head)
    # Count
    length = 0
    cur = dummy
    while cur:
        length += 1
        cur = cur.next
    # Remove
    cur = dummy
    for _ in range(length - n - 1):
        cur = cur.next
    cur.next = cur.next.next
    return dummy.next


# Solution 9: Using dict to map index -> node
def remove_nth_v9(head, n):
    dummy = ListNode(0, head)
    nodes = {0: dummy}
    cur = dummy
    idx = 1
    while cur.next:
        cur = cur.next
        nodes[idx] = cur
        idx += 1
    length = idx - 1
    target = length - n + 1  # idx of the n-th from end (1-based)
    if target == 1:
        # remove head
        dummy.next = dummy.next.next
    else:
        nodes[target - 1].next = nodes[target].next
    return dummy.next


# Solution 10: Functional with reduce
def remove_nth_v10(head, n):
    from functools import reduce
    # Convert to list, rebuild except n-th from end
    lst = []
    cur = head
    while cur:
        lst.append(cur.val)
        cur = cur.next
    target = len(lst) - n
    new_lst = lst[:target] + lst[target + 1:]
    return to_linked(new_lst) if new_lst else None


# Solution 11: Two-pass with explicit array index counting
def remove_nth_v11(head, n):
    nodes = []
    cur = head
    while cur:
        nodes.append(cur)
        cur = cur.next
    target_idx = len(nodes) - n
    if target_idx == 0:
        return head.next if head else None
    nodes[target_idx - 1].next = nodes[target_idx].next
    return head


# Solution 12: Convert to list, splice, rebuild
def remove_nth_v12(head, n):
    lst = from_linked(head)
    idx = len(lst) - n
    if 0 <= idx < len(lst):
        del lst[idx]
    return to_linked(lst) if lst else None


# Solution 13: One-pass with dummy node and explicit gap counter
def remove_nth_v13(head, n):
    dummy = ListNode(0, head)
    fast = slow = dummy
    for _ in range(n):
        fast = fast.next
    while fast.next:
        fast = fast.next
        slow = slow.next
    slow.next = slow.next.next
    return dummy.next


# Solution 14: Recursive — return new head, count from end
def remove_nth_v14(head, n):
    def helper(node, k):
        if node is None:
            return 0, None
        cnt, new_next = helper(node.next, k)
        if cnt == k:
            return cnt + 1, new_next  # skip this node
        node.next = new_next
        return cnt + 1, node
    _, new_head = helper(head, n)
    return new_head


# Solution 15: Stack approach
def remove_nth_v15(head, n):
    dummy = ListNode(0, head)
    stack = []
    cur = dummy
    while cur:
        stack.append(cur)
        cur = cur.next
    target = len(stack) - n  # 1-indexed from end of stack
    stack[target - 1].next = stack[target].next
    return dummy.next


# Solution 16: Two-pointer with hard-coded gap for n
def remove_nth_v16(head, n):
    if not head:
        return None
    fast = head
    for _ in range(n):
        if not fast:
            return head
        fast = fast.next
    if not fast:
        return head.next
    slow = head
    while fast.next:
        fast = fast.next
        slow = slow.next
    slow.next = slow.next.next
    return head


# Solution 17: Using itertools islice-like manual advance
def remove_nth_v17(head, n):
    dummy = ListNode(0, head)
    # Advance fast by n steps using a counter
    fast = dummy
    cnt = 0
    while fast and cnt < n:
        fast = fast.next
        cnt += 1
    if not fast:
        return head
    slow = dummy
    while fast.next:
        fast = fast.next
        slow = slow.next
    slow.next = slow.next.next
    return dummy.next


# Solution 18: Index-based mutation via dict
def remove_nth_v18(head, n):
    node_map = {}
    cur = head
    idx = 0
    while cur:
        node_map[idx] = cur
        cur = cur.next
        idx += 1
    total = idx
    target = total - n
    if target == 0:
        return head.next
    node_map[target - 1].next = node_map[target].next
    return head


# Solution 19: Index-based with list
def remove_nth_v19(head, n):
    nodes = []
    cur = head
    while cur:
        nodes.append(cur)
        cur = cur.next
    target = len(nodes) - n
    if target == 0:
        return head.next
    nodes[target - 1].next = nodes[target].next
    return head


# Solution 20: Single pass without dummy — direct head check
def remove_nth_v20(head, n):
    if not head:
        return None
    fast = head
    for _ in range(n):
        if not fast.next:
            # n == length of list
            return head.next
        fast = fast.next
    slow = head
    while fast.next:
        fast = fast.next
        slow = slow.next
    slow.next = slow.next.next
    return head


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (2ptr+dummy)",       remove_nth_v1),
        ("V2 (2ptr no dummy)",    remove_nth_v2),
        ("V3 (2-pass length)",    remove_nth_v3),
        ("V4 (stack)",            remove_nth_v4),
        ("V5 (recursive)",        remove_nth_v5),
        ("V6 (list of nodes)",    remove_nth_v6),
        ("V7 (2ptr head init)",   remove_nth_v7),
        ("V8 (2-pass sentinel)",  remove_nth_v8),
        ("V9 (dict map)",         remove_nth_v9),
        ("V10 (functional)",      remove_nth_v10),
    ]

    test_cases = [
        # (input_list, n, expected_list)
        ([1, 2, 3, 4, 5],        2, [1, 2, 3, 5]),
        ([1],                    1, []),
        ([1, 2],                 1, [1]),
        ([1, 2],                 2, [2]),
        ([1, 2, 3],              3, [2, 3]),  # remove head
        ([1, 2, 3, 4, 5],        5, [2, 3, 4, 5]),  # remove head
        ([1, 2, 3, 4, 5],        1, [1, 2, 3, 4]),  # remove tail
        ([10, 20, 30, 40],       3, [10, 30, 40]),
        ([1, 2],                 1, [1]),
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (arr, n, expected) in enumerate(test_cases):
            try:
                head = to_linked(arr)
                new_head = func(head, n)
                got = from_linked(new_head)
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{idx}]: {arr}, n={n} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")
    print("\n=== INTERVIEW THINKING ===")
    print("""
1. UNDERSTAND:  Remove n-th from end of singly linked list.
2. INSIGHT:     Two-pointer with gap n; advance fast by n, then both.
3. PATTERN:     Fast/slow with gap = n.
4. EDGE:        n=sz (remove head); sz=1 -> None.
5. TRICKY:      Use dummy head to avoid special-casing the head.
6. ALGORITHM:   Advance fast by n; loop until fast.next=None; slow.next = slow.next.next.
7. PROOF:       After advance, gap is n; when fast at end, slow is n behind.
8. COMPLEXITY:  O(sz) time, O(1) space.
9. CODE:        dummy -> fast/slow; advance fast by n; loop; relink.
10. TRACE:      [1,2,3,4,5], n=2 -> slow lands on 3; remove 4 -> [1,2,3,5].
""")
