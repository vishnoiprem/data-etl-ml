"""Add Two Numbers — digits stored in reverse order in linked lists.

Time:  O(max(m, n))
Space:  O(max(m, n)) — output list
"""


def solve_add_two_numbers(l1, l2):
    """Add two numbers represented as reversed linked lists.

    >>> from _ll_helpers import from_list, to_list
    >>> to_list(solve_add_two_numbers(from_list([2,4,3]), from_list([5,6,4])))
    [7, 0, 8]
    """
    dummy = ListNode(0)
    tail = dummy
    carry = 0
    while l1 is not None or l2 is not None or carry:
        v1 = l1.val if l1 is not None else 0
        v2 = l2.val if l2 is not None else 0
        total = v1 + v2 + carry
        carry, digit = divmod(total, 10)
        tail.next = ListNode(digit)
        tail = tail.next
        l1 = l1.next if l1 is not None else None
        l2 = l2.next if l2 is not None else None
    return dummy.next


from _ll_helpers import ListNode  # type: ignore  # re-export


if __name__ == "__main__":
    from _ll_helpers import from_list, to_list  # type: ignore
    print(to_list(solve_add_two_numbers(from_list([2, 4, 3]), from_list([5, 6, 4]))))
