"""
Palindrome Linked List - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/palindrome-linked-list

Determine if a singly linked list is a palindrome. O(n) time, O(1) space.

KEY INSIGHT:
Use fast/slow pointers to find the middle. Reverse the second half. Then
walk both halves simultaneously and compare.

Examples:
    1 -> 2 -> 2 -> 1 -> True
    1 -> 2 -> False

Constraints:
- 1 <= number of nodes <= 10^5
- 0 <= Node.val <= 9
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
# Way 1: Find middle + reverse second half + compare (BEST)
# ============================================================
def is_palindrome_1(head):
    if not head or not head.next:
        return True
    # Find middle (slow stops at second middle for even, or middle for odd)
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    # Reverse second half
    second = _reverse(slow)
    first = head
    # Compare
    result = True
    p1, p2 = first, second
    while p2:  # only need to check second half
        if p1.val != p2.val:
            result = False
            break
        p1 = p1.next
        p2 = p2.next
    # Restore (optional)
    _reverse(second)
    return result


# ============================================================
# Way 2: Copy to array, two-pointer
# ============================================================
def is_palindrome_2(head):
    arr = []
    cur = head
    while cur:
        arr.append(cur.val)
        cur = cur.next
    return arr == arr[::-1]


# ============================================================
# Way 3: Stack-based
# ============================================================
def is_palindrome_3(head):
    stack = []
    cur = head
    while cur:
        stack.append(cur.val)
        cur = cur.next
    cur = head
    while cur:
        if cur.val != stack.pop():
            return False
        cur = cur.next
    return True


# ============================================================
# Way 4: Push first half to stack, compare with second half
# ============================================================
def is_palindrome_4(head):
    slow = fast = head
    stack = []
    while fast and fast.next:
        stack.append(slow.val)
        slow = slow.next
        fast = fast.next.next
    # If odd length, skip middle
    if fast:
        slow = slow.next
    while slow:
        if slow.val != stack.pop():
            return False
        slow = slow.next
    return True


# ============================================================
# Way 5: Recursive
# ============================================================
def is_palindrome_5(head):
    front = head

    def helper(cur):
        if cur is None:
            return True
        if not helper(cur.next):
            return False
        if cur.val != front.val:
            return False
        nonlocal front
        front = front.next
        return True

    return helper(head)


# ============================================================
# Way 6: Recursive with stack
# ============================================================
def is_palindrome_6(head):
    def helper(node, stack):
        if node is None:
            return True
        stack.append(node.val)
        return helper(node.next, stack)

    stack = []
    helper(head, stack)
    # Now check by walking again
    cur = head
    while cur:
        if cur.val != stack.pop():
            return False
        cur = cur.next
    return True


# ============================================================
# Way 7: Deque-based
# ============================================================
def is_palindrome_7(head):
    from collections import deque
    dq = deque()
    cur = head
    while cur:
        dq.append(cur.val)
        cur = cur.next
    while len(dq) > 1:
        if dq.popleft() != dq.pop():
            return False
    return True


# ============================================================
# Way 8: Iterative with explicit second-half pointer
# ============================================================
def is_palindrome_8(head):
    if not head or not head.next:
        return True
    # Find length
    length = 0
    cur = head
    while cur:
        length += 1
        cur = cur.next
    # Walk to middle
    cur = head
    for _ in range(length // 2):
        cur = cur.next
    # Reverse second half
    second = _reverse(cur)
    # Compare
    p1, p2 = head, second
    result = True
    while p2:
        if p1.val != p2.val:
            result = False
            break
        p1 = p1.next
        p2 = p2.next
    _reverse(second)
    return result


# ============================================================
# Way 9: Class-based
# ============================================================
class PalindromeChecker_9:
    def __init__(self, head):
        self.head = head

    def is_palindrome(self):
        arr = []
        cur = self.head
        while cur:
            arr.append(cur.val)
            cur = cur.next
        return arr == arr[::-1]


def is_palindrome_9(head):
    return PalindromeChecker_9(head).is_palindrome()


# ============================================================
# Way 10: Final cleanest
# ============================================================
def is_palindrome_10(head):
    """Find middle with fast/slow, reverse second half, compare."""
    if not head or not head.next:
        return True
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    second = _reverse(slow)
    p1, p2 = head, second
    while p2:
        if p1.val != p2.val:
            return False
        p1 = p1.next
        p2 = p2.next
    return True


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to determine if a singly linked list is a palindrome in O(n)
time and O(1) space."

Key Insight:
"Use fast/slow pointers to find the middle. Reverse the second half.
Then walk both halves — they should mirror each other for a palindrome."

Algorithm:
1. slow = fast = head.
2. While fast and fast.next: slow = slow.next, fast = fast.next.next.
3. Reverse the list from slow.
4. Compare the first and reversed second halves.
5. (Optional) Restore by reversing back.

Edge Cases:
- Empty or single node: True.
- Two nodes: True iff equal.
- Odd length: skip the middle.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Fast/slow | O(n)   | O(1)   |
| Array     | O(n)   | O(n)   |
| Stack     | O(n)   | O(n)   |
| Recursive | O(n)   | O(n)   |
+-----------+--------+--------+

KEY TRICK:
The fast/slow trick finds the middle in O(n) with O(1) pointers — no need
to count length first.

RELATED PROBLEMS:
- Reverse Linked List (LC 206).
- Palindrome Valid (LC 125).
- Reverse Nodes in k-Group (LC 25).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([1, 2, 2, 1], True, "Even palindrome"),
        ([1, 2, 3, 2, 1], True, "Odd palindrome"),
        ([1, 2], False, "Two non-equal"),
        ([1], True, "Single"),
        ([1, 1], True, "Two equal"),
        ([], True, "Empty"),
        ([1, 2, 3], False, "Three non-palindrome"),
        ([1, 2, 3, 4, 5], False, "Five non-palindrome"),
        ([1, 2, 3, 4, 5, 4, 3, 2, 1], True, "Long palindrome"),
        ([0, 0], True, "Zeros"),
        ([1, 0, 1], True, "Three with zero"),
    ]

    implementations = [
        ("Way 1: Fast/slow + reverse (BEST)", is_palindrome_1),
        ("Way 2: Array + two-pointer", is_palindrome_2),
        ("Way 3: Stack", is_palindrome_3),
        ("Way 4: Half stack", is_palindrome_4),
        ("Way 5: Recursive", is_palindrome_5),
        ("Way 6: Recursive + stack", is_palindrome_6),
        ("Way 7: Deque", is_palindrome_7),
        ("Way 8: Length-based", is_palindrome_8),
        ("Way 9: Class-based", is_palindrome_9),
        ("Way 10: Final cleanest", is_palindrome_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for arr, expected, desc in test_cases:
            try:
                head = list_from_array(copy.deepcopy(arr))
                result = fn(head)
                # For Way 5, the linked list gets mutated (front advances).
                # We just verify the result.
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
