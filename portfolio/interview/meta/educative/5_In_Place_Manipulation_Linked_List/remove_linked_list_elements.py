"""
Remove Linked List Elements - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/remove-linked-list-elements

Given the head of a linked list and an integer val, remove all the nodes
that have Node.val == val, and return the new head.

KEY INSIGHT:
Use a dummy to handle head removal. Walk with cur.next; if cur.next.val
matches, skip it.

Examples:
    1->2->6->3->4->5->6, val=6  =>  1->2->3->4->5

Constraints:
- 0 <= number of nodes <= 10^4
- 0 <= Node.val <= 50
- 0 <= val <= 50
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
# Way 1: Dummy + cur.next check (BEST - Memorize!)
# ============================================================
def remove_elements_1(head, val):
    """Use dummy to handle head; walk cur.next and skip matches."""
    dummy = ListNode(0)
    dummy.next = head
    cur = dummy
    while cur.next:
        if cur.next.val == val:
            cur.next = cur.next.next
        else:
            cur = cur.next
    return dummy.next


# ============================================================
# Way 2: Walk with prev pointer
# ============================================================
def remove_elements_2(head, val):
    """Walk prev/cur; if match, prev.next = cur.next."""
    if not head:
        return head
    dummy = ListNode(0)
    dummy.next = head
    prev = dummy
    cur = head
    while cur:
        if cur.val == val:
            prev.next = cur.next
        else:
            prev = cur
        cur = cur.next
    return dummy.next


# ============================================================
# Way 3: Build into array, filter, rebuild
# ============================================================
def remove_elements_3(head, val):
    """Collect values, filter, rebuild."""
    vals = []
    cur = head
    while cur:
        if cur.val != val:
            vals.append(cur.val)
        cur = cur.next
    return list_from_array(vals)


# ============================================================
# Way 4: Recursive
# ============================================================
def remove_elements_4(head, val):
    """Recursively remove matching nodes."""
    if not head:
        return head
    head.next = remove_elements_4(head.next, val)
    if head.val == val:
        return head.next
    return head


# ============================================================
# Way 5: Class-based wrapper
# ============================================================
class ElementRemover_5:
    def __init__(self, head, val):
        self.head = head
        self.val = val

    def remove(self):
        return remove_elements_1(self.head, self.val)


def remove_elements_5(head, val):
    return ElementRemover_5(head, val).remove()


# ============================================================
# Way 6: Two-pass: count matches, rebuild
# ============================================================
def remove_elements_6(head, val):
    """Two-pass: count matches, then walk and skip."""
    count = 0
    cur = head
    while cur:
        if cur.val == val:
            count += 1
        cur = cur.next
    if count == 0:
        return head
    dummy = ListNode(0)
    dummy.next = head
    cur = dummy
    while cur.next:
        if cur.next.val == val:
            cur.next = cur.next.next
            count -= 1
            if count == 0:
                return dummy.next
        else:
            cur = cur.next
    return dummy.next


# ============================================================
# Way 7: Stack-based
# ============================================================
def remove_elements_7(head, val):
    """Push non-matching onto stack; pop to rebuild."""
    stack = []
    cur = head
    while cur:
        if cur.val != val:
            stack.append(cur.val)
        cur = cur.next
    return list_from_array(stack)


# ============================================================
# Way 8: Hash set (when val range is small)
# ============================================================
def remove_elements_8(head, val):
    """Use set for O(1) membership."""
    skip = {val}
    dummy = ListNode(0)
    dummy.next = head
    cur = dummy
    while cur.next:
        if cur.next.val in skip:
            cur.next = cur.next.next
        else:
            cur = cur.next
    return dummy.next


# ============================================================
# Way 9: Filter list into new list (no dummy)
# ============================================================
def remove_elements_9(head, val):
    """Build new list of non-matching values."""
    if not head:
        return head
    new_head = None
    tail = None
    cur = head
    while cur:
        if cur.val != val:
            new_node = ListNode(cur.val)
            if not new_head:
                new_head = new_node
                tail = new_node
            else:
                tail.next = new_node
                tail = new_node
        cur = cur.next
    return new_head


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def remove_elements_10(head, val):
    """
    THE ONE TO MEMORIZE.

    1. dummy -> head.
    2. cur = dummy.
    3. While cur.next:
       a. If cur.next.val == val: cur.next = cur.next.next.
       b. Else: cur = cur.next.
    4. Return dummy.next.

    Time:  O(n)
    Space: O(1).
    """
    dummy = ListNode(0)
    dummy.next = head
    cur = dummy
    while cur.next:
        if cur.next.val == val:
            cur.next = cur.next.next
        else:
            cur = cur.next
    return dummy.next


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to remove all nodes with value == val from a linked list and
return the new head."

Key Insight:
"Use a dummy node pointing to head. Walk with cur starting at dummy.
If cur.next.val == val, redirect cur.next to skip the match. Otherwise
advance cur."

Algorithm:
1. dummy -> head. cur = dummy.
2. While cur.next:
   a. If cur.next.val == val: cur.next = cur.next.next.
   b. Else: cur = cur.next.
3. Return dummy.next.

Edge Cases:
- Empty list: return None.
- All match: return None.
- Head matches: dummy handles this.
- No matches: return as-is.

KEY TRICK:
The dummy node ensures that if the head is removed, we still have a
reference to the new head. Don't advance cur when removing (the new
cur.next might also match).

RELATED PROBLEMS:
- Remove Duplicates from Sorted List (LC 83).
- Remove Duplicates II (LC 82).
- Delete Node in a Linked List (LC 237).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([1, 2, 6, 3, 4, 5, 6], 6, [1, 2, 3, 4, 5], "Standard LC203"),
        ([], 1, [], "Empty"),
        ([1], 1, [], "Single match"),
        ([1], 2, [1], "Single no match"),
        ([7, 7, 7, 7], 7, [], "All match"),
        ([1, 2, 3], 1, [2, 3], "Match at head"),
    ]

    implementations = [
        ("Way 1: Dummy + cur.next (BEST)", remove_elements_1),
        ("Way 2: prev/cur", remove_elements_2),
        ("Way 3: Array filter", remove_elements_3),
        ("Way 4: Recursive", remove_elements_4),
        ("Way 5: Class-based", remove_elements_5),
        ("Way 6: Count + rebuild", remove_elements_6),
        ("Way 7: Stack", remove_elements_7),
        ("Way 8: Hash set", remove_elements_8),
        ("Way 9: Filter new list", remove_elements_9),
        ("Way 10: Final cleanest", remove_elements_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for inp, val, expected, desc in test_cases:
            try:
                head = list_from_array(copy.deepcopy(inp))
                result = fn(head, val)
                got = list_to_array(result)
                if got == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: input={inp} val={val} expected={expected} got={got}")
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