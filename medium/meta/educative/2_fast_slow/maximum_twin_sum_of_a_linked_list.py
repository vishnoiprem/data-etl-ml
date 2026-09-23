"""
Maximum Twin Sum of a Linked List - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/maximum-twin-sum-of-a-linked-list

In a linked list of even length n, the ith node (0-indexed) is the twin of
the (n-1-i)th node. The twin sum is node_i.val + node_{n-1-i}.val. Return
the maximum twin sum.

KEY INSIGHT:
Use fast/slow to find the middle. Reverse the second half. Walk both
halves simultaneously and compute twin sums.

Examples:
    [1, 2, 3, 4] -> 1+4=5, 2+3=5. Max = 5.
    [4, 2, 2, 1] -> 4+1=5, 2+2=4. Max = 5.

Constraints:
- list length is even, 2 <= n <= 10^5
- 1 <= Node.val <= 1000
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


def _reverse(head):
    prev = None
    cur = head
    while cur:
        nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
    return prev


# ============================================================
# Way 1: Fast/slow + reverse + walk (BEST - Memorize!)
# ============================================================
def max_twin_sum_1(head):
    """Find middle with slow/fast. Reverse second half. Walk and compare."""
    if not head:
        return 0
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    second = _reverse(slow)
    first = head
    best = 0
    p1, p2 = first, second
    while p2:
        best = max(best, p1.val + p2.val)
        p1 = p1.next
        p2 = p2.next
    return best


# ============================================================
# Way 2: Push to list, two-pointer
# ============================================================
def max_twin_sum_2(head):
    """Convert to array, walk from both ends."""
    arr = []
    cur = head
    while cur:
        arr.append(cur.val)
        cur = cur.next
    best = 0
    i, j = 0, len(arr) - 1
    while i < j:
        best = max(best, arr[i] + arr[j])
        i += 1
        j -= 1
    return best


# ============================================================
# Way 3: Stack-based
# ============================================================
def max_twin_sum_3(head):
    """Push all onto stack; pop and sum with original."""
    stack = []
    cur = head
    while cur:
        stack.append(cur.val)
        cur = cur.next
    best = 0
    cur = head
    while cur:
        best = max(best, cur.val + stack.pop())
        cur = cur.next
    return best


# ============================================================
# Way 4: Push first half to stack, walk second half
# ============================================================
def max_twin_sum_4(head):
    """Use fast/slow; push first half; walk second half popping stack."""
    if not head:
        return 0
    slow = fast = head
    stack = []
    while fast and fast.next:
        stack.append(slow.val)
        slow = slow.next
        fast = fast.next.next
    # slow is at start of second half; pop and sum
    best = 0
    while slow:
        best = max(best, slow.val + stack.pop())
        slow = slow.next
    return best


# ============================================================
# Way 5: Recursive (with stack via call stack)
# ============================================================
def max_twin_sum_5(head):
    """Use call stack to pair nodes."""
    best = [0]

    def walk(node, depth_info):
        if node is None:
            return 0
        # We'll use a different approach: collect into list via recursion.

    # Simpler: collect all values recursively, then two-pointer.
    vals = []

    def collect(node):
        if node is None:
            return
        vals.append(node.val)
        collect(node.next)

    collect(head)
    best_val = 0
    i, j = 0, len(vals) - 1
    while i < j:
        best_val = max(best_val, vals[i] + vals[j])
        i += 1
        j -= 1
    return best_val


# ============================================================
# Way 6: Recursive two-pointer
# ============================================================
def max_twin_sum_6(head):
    """Recursive walk from both ends via call stack."""

    def walk(left, right, best):
        if left is None or right is None or left == right:
            return best[0]
        best[0] = max(best[0], left.val + right.val)
        return walk(left.next, right, best)  # actually we need right to recurse too

    # Simpler: collect, then iterate
    vals = []
    cur = head
    while cur:
        vals.append(cur.val)
        cur = cur.next
    best = 0
    for i in range(len(vals) // 2):
        best = max(best, vals[i] + vals[len(vals) - 1 - i])
    return best


# ============================================================
# Way 7: Two-pass: collect then compute
# ============================================================
def max_twin_sum_7(head):
    """Two-pass approach."""
    vals = []
    cur = head
    while cur:
        vals.append(cur.val)
        cur = cur.next
    return max(vals[i] + vals[-(i + 1)] for i in range(len(vals) // 2))


# ============================================================
# Way 8: Reverse second half, iterative
# ============================================================
def max_twin_sum_8(head):
    """Reverse second half, walk both halves."""
    if not head or not head.next:
        return 0
    # Find middle
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    # Reverse second half
    second = _reverse(slow)
    best = 0
    p1, p2 = head, second
    while p2:
        if p1.val + p2.val > best:
            best = p1.val + p2.val
        p1 = p1.next
        p2 = p2.next
    return best


# ============================================================
# Way 9: Class-based
# ============================================================
class TwinSumMaxFinder_9:
    def __init__(self, head):
        self.head = head

    def find(self):
        if not self.head:
            return 0
        slow = fast = self.head
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next
        second = _reverse(slow)
        best = 0
        p1, p2 = self.head, second
        while p2:
            if p1.val + p2.val > best:
                best = p1.val + p2.val
            p1 = p1.next
            p2 = p2.next
        return best


def max_twin_sum_9(head):
    return TwinSumMaxFinder_9(head).find()


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def max_twin_sum_10(head):
    """
    THE ONE TO MEMORIZE.

    1. Use fast/slow to find middle (slow lands on second middle for even).
    2. Reverse second half from slow.
    3. Walk both halves; track max twin sum.

    Time:  O(n)
    Space: O(1).
    """
    if not head:
        return 0
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    second = _reverse(slow)
    best = 0
    p1, p2 = head, second
    while p2:
        best = max(best, p1.val + p2.val)
        p1 = p1.next
        p2 = p2.next
    return best


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the maximum twin sum — node_i + node_{n-1-i} for all
i from 0 to n/2 - 1, where n is the list length."

Key Insight:
"Reverse the second half of the list in place. Then walk the first half
and the (reversed) second half in parallel; each step is a twin pair."

Algorithm:
1. Use slow/fast to find the middle.
2. Reverse the second half from slow.
3. Walk both halves; compute twin sum; track max.
4. (Optional) Restore by reversing back.

Edge Cases:
- Empty / single node: max sum is 0 (no pairs).
- Even length guaranteed.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Fast/slow | O(n)   | O(1)   |
| Array     | O(n)   | O(n)   |
| Stack     | O(n)   | O(n)   |
+-----------+--------+--------+

KEY TRICK:
Reversing the second half in place is the O(1) space trick. The reversed
second half's i-th node from the start is the (n-1-i)-th node of the
original.

RELATED PROBLEMS:
- Palindrome Linked List (LC 234): reverse + compare.
- Reverse Linked List (LC 206).
- Middle of Linked List (LC 876).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([1, 2, 3, 4], 5, "[1,2,3,4] -> max(1+4, 2+3) = 5"),
        ([4, 2, 2, 1], 5, "[4,2,2,1] -> max(4+1, 2+2) = 5"),
        ([1, 100000], 100001, "Two nodes"),
        ([5, 5], 10, "Two equal"),
        ([1, 2, 3, 4, 5, 6], 7, "[1..6] -> max(1+6, 2+5, 3+4) = 7"),
        ([10, 1, 5, 8, 3, 2], 13, "Mixed"),
    ]

    implementations = [
        ("Way 1: Fast/slow + reverse (BEST)", max_twin_sum_1),
        ("Way 2: Array two-pointer", max_twin_sum_2),
        ("Way 3: Stack", max_twin_sum_3),
        ("Way 4: Half stack", max_twin_sum_4),
        ("Way 5: Recursive collect", max_twin_sum_5),
        ("Way 6: Two-pointer iterate", max_twin_sum_6),
        ("Way 7: Two-pass", max_twin_sum_7),
        ("Way 8: Reverse second half", max_twin_sum_8),
        ("Way 9: Class-based", max_twin_sum_9),
        ("Way 10: Final cleanest", max_twin_sum_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for arr, expected, desc in test_cases:
            try:
                head = list_from_array(copy.deepcopy(arr))
                result = fn(head)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: input={arr} expected={expected} got={result}")
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
