"""
Rotate List - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/rotate-list

Given the head of a linked list, rotate the list to the right by k places.

KEY INSIGHT:
Make the list circular, then break the cycle at position (n - k % n - 1).
Walk to find the new tail, set its next to None, and return new head.

Examples:
    1 -> 2 -> 3 -> 4 -> 5, k=2  =>  4 -> 5 -> 1 -> 2 -> 3
    0 -> 1 -> 2, k=4  =>  2 -> 0 -> 1  (k % n = 1)

Constraints:
- 0 <= k <= 2 * 10^9
- 0 <= number of nodes <= 500
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
# Way 1: Make circular + break (BEST - Memorize!)
# ============================================================
def rotate_right_1(head, k):
    """Connect tail to head (circular), then break at new position."""
    if not head or not head.next or k == 0:
        return head
    # Find length and tail
    n = 1
    tail = head
    while tail.next:
        tail = tail.next
        n += 1
    k %= n
    if k == 0:
        return head
    # Make circular
    tail.next = head
    # Walk to new tail: n - k - 1 steps from head
    steps = n - k - 1
    new_tail = head
    for _ in range(steps):
        new_tail = new_tail.next
    new_head = new_tail.next
    new_tail.next = None
    return new_head


# ============================================================
# Way 2: Walk to (n-k%n)-th node, cut and prepend
# ============================================================
def rotate_right_2(head, k):
    """Walk to the cut point, then reattach."""
    if not head or not head.next or k == 0:
        return head
    n = 1
    cur = head
    while cur.next:
        cur = cur.next
        n += 1
    k %= n
    if k == 0:
        return head
    # cur is tail. Walk (n - k - 1) steps to find new tail.
    cur.next = head  # circular
    steps = n - k
    new_tail = head
    for _ in range(steps - 1):
        new_tail = new_tail.next
    new_head = new_tail.next
    new_tail.next = None
    return new_head


# ============================================================
# Way 3: Recursive (split into two lists)
# ============================================================
def rotate_right_3(head, k):
    """Recursive helper."""
    if not head or not head.next or k == 0:
        return head

    def split(node):
        """Return (head, tail, length)."""
        if not node:
            return None, None, 0
        h, t, n = node, node, 1
        while t.next:
            t = t.next
            n += 1
        return h, t, n

    h, t, n = split(head)
    k %= n
    if k == 0:
        return head
    # Find new tail position from head: n - k - 1
    new_tail = h
    for _ in range(n - k - 1):
        new_tail = new_tail.next
    new_head = new_tail.next
    new_tail.next = None
    t.next = h
    return new_head


# ============================================================
# Way 4: Build into array, rebuild rotated
# ============================================================
def rotate_right_4(head, k):
    """Collect values; rebuild rotated."""
    vals = []
    cur = head
    while cur:
        vals.append(cur.val)
        cur = cur.next
    n = len(vals)
    if n == 0 or k % n == 0:
        return list_from_array(vals)
    k %= n
    rotated = vals[-k:] + vals[:-k]
    return list_from_array(rotated)


# ============================================================
# Way 5: Two-pointer slow/fast (k-step apart)
# ============================================================
def rotate_right_5(head, k):
    """Advance fast by k steps, then walk both together."""
    if not head or not head.next or k == 0:
        return head
    # First find length
    n = 1
    tail = head
    while tail.next:
        tail = tail.next
        n += 1
    k %= n
    if k == 0:
        return head
    slow = fast = head
    for _ in range(k):
        fast = fast.next
    while fast.next:
        slow = slow.next
        fast = fast.next
    # slow is new tail, fast is old tail
    new_head = slow.next
    slow.next = None
    tail.next = head
    return new_head


# ============================================================
# Way 6: Stack-based
# ============================================================
def rotate_right_6(head, k):
    """Push values onto stack; rebuild rotated list."""
    if not head or not head.next or k == 0:
        return head
    stack = []
    cur = head
    while cur:
        stack.append(cur.val)
        cur = cur.next
    n = len(stack)
    k %= n
    if k == 0:
        return head
    # Last k elements become the front.
    rotated = stack[-k:] + stack[:-k]
    return list_from_array(rotated)


# ============================================================
# Way 7: Hash map by index
# ============================================================
def rotate_right_7(head, k):
    """Use dict to map index to node."""
    if not head or not head.next or k == 0:
        return head
    nodes = []
    cur = head
    while cur:
        nodes.append(cur)
        cur = cur.next
    n = len(nodes)
    k %= n
    if k == 0:
        return head
    # New head is nodes[n-k]; new tail is nodes[n-k-1]
    new_head = nodes[n - k]
    new_tail = nodes[n - k - 1]
    new_tail.next = None
    nodes[-1].next = nodes[0]
    return new_head


# ============================================================
# Way 8: Class-based wrapper
# ============================================================
class ListRotator_8:
    def __init__(self, head, k):
        self.head = head
        self.k = k

    def rotate(self):
        return rotate_right_1(self.head, self.k)


def rotate_right_8(head, k):
    return ListRotator_8(head, k).rotate()


# ============================================================
# Way 9: Iterative with explicit prev tracking
# ============================================================
def rotate_right_9(head, k):
    """Use prev pointer to walk to the cut point."""
    if not head or not head.next or k == 0:
        return head
    n = 1
    tail = head
    while tail.next:
        tail = tail.next
        n += 1
    k %= n
    if k == 0:
        return head
    # Walk to node at index n - k - 1
    prev = None
    cur = head
    target = n - k - 1
    for _ in range(target):
        prev = cur
        cur = cur.next
    # cur is new tail
    new_head = cur.next
    cur.next = None
    tail.next = head
    return new_head


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def rotate_right_10(head, k):
    """
    THE ONE TO MEMORIZE.

    1. Find length n and tail.
    2. k = k % n.
    3. If k == 0, return head.
    4. tail.next = head (make circular).
    5. Walk n - k - 1 steps to find new tail.
    6. new_head = new_tail.next; new_tail.next = None; return new_head.

    Time:  O(n)
    Space: O(1).
    """
    if not head or not head.next or k == 0:
        return head
    n = 1
    tail = head
    while tail.next:
        tail = tail.next
        n += 1
    k %= n
    if k == 0:
        return head
    tail.next = head
    steps = n - k - 1
    new_tail = head
    for _ in range(steps):
        new_tail = new_tail.next
    new_head = new_tail.next
    new_tail.next = None
    return new_head


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to rotate a linked list to the right by k positions."

Key Insight:
"Find the length n and the tail. The new tail is at index n - k%n - 1.
Make the list circular by connecting tail to head, then break at the new
tail. If k%n == 0, no rotation needed."

Algorithm:
1. Walk to find n and tail.
2. k = k % n. If k == 0, return head.
3. tail.next = head (circular).
4. Walk (n - k - 1) steps to find new_tail.
5. new_head = new_tail.next; new_tail.next = None; return new_head.

Edge Cases:
- Empty list or single node: return as-is.
- k == 0: return as-is.
- k >= n: use k % n.
- Two nodes: rotate works trivially.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Circular  | O(n)   | O(1)   |
| Array     | O(n)   | O(n)   |
| Slow/fast | O(n)   | O(1)   |
+-----------+--------+--------+

KEY TRICK:
The new tail is at index (n - k%n - 1). If k == 0, the list stays the same.
The circular trick avoids needing a separate "prev" pointer.

RELATED PROBLEMS:
- Reverse Linked List (LC 206).
- Split Linked List in Parts (LC 725).
- Reorder List (LC 143).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([1, 2, 3, 4, 5], 2, [4, 5, 1, 2, 3], "Standard LC61"),
        ([0, 1, 2], 4, [2, 0, 1], "k > n"),
        ([1, 2, 3, 4, 5], 0, [1, 2, 3, 4, 5], "k = 0"),
        ([], 1, [], "Empty"),
        ([1], 99, [1], "Single"),
        ([1, 2], 1, [2, 1], "Two nodes"),
        ([1, 2, 3, 4, 5], 5, [1, 2, 3, 4, 5], "k = n"),
    ]

    implementations = [
        ("Way 1: Circular (BEST)", rotate_right_1),
        ("Way 2: Walk + cut", rotate_right_2),
        ("Way 3: Recursive split", rotate_right_3),
        ("Way 4: Array rebuild", rotate_right_4),
        ("Way 5: Slow/fast", rotate_right_5),
        ("Way 6: Stack", rotate_right_6),
        ("Way 7: Hash by index", rotate_right_7),
        ("Way 8: Class-based", rotate_right_8),
        ("Way 9: Walk w/ prev", rotate_right_9),
        ("Way 10: Final cleanest", rotate_right_10),
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
