"""Merge Two Sorted Linked Lists.

Time:  O(m + n)
Space: O(1) — we reuse the input nodes
"""


def solve_merge_two_sorted(l1, l2):
    """Merge two sorted lists and return the head of the result.

    >>> from _ll_helpers import from_list, to_list
    >>> to_list(solve_merge_two_sorted(from_list([1,2,4]), from_list([1,3,4])))
    [1, 1, 2, 3, 4, 4]
    """
    dummy = ListNode(0)
    tail = dummy
    while l1 is not None and l2 is not None:
        if l1.val <= l2.val:
            tail.next = l1
            l1 = l1.next
        else:
            tail.next = l2
            l2 = l2.next
        tail = tail.next
    tail.next = l1 if l1 is not None else l2
    return dummy.next


from _ll_helpers import ListNode  # type: ignore  # re-export


if __name__ == "__main__":
    from _ll_helpers import from_list, to_list  # type: ignore
    print(to_list(solve_merge_two_sorted(from_list([1, 2, 4]), from_list([1, 3, 4]))))
