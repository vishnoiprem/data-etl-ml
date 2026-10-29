"""Linked List Cycle — fast/slow pointer detection.

Time:  O(n)
Space: O(1)
"""


def solve_has_cycle(head):
    """Return True if the linked list contains a cycle.

    >>> from _ll_helpers import ListNode
    >>> solve_has_cycle(None)
    False
    """
    slow = fast = head
    while fast is not None and fast.next is not None:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            return True
    return False


if __name__ == "__main__":
    from _ll_helpers import ListNode  # type: ignore
    a = ListNode(3)
    b = ListNode(2)
    c = ListNode(0)
    d = ListNode(-4)
    a.next, b.next, c.next, d.next = b, c, d, b  # cycle
    print(solve_has_cycle(a))  # True
    print(solve_has_cycle(ListNode(1)))  # False
