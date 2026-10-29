"""Reverse a Singly Linked List.

Time:  O(n)
Space: O(1)
"""


def solve_reverse_list(head):
    """Return the new head of the reversed list.

    >>> from _ll_helpers import from_list, to_list
    >>> to_list(solve_reverse_list(from_list([1,2,3,4])))
    [4, 3, 2, 1]
    """
    prev = None
    curr = head
    while curr is not None:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt
    return prev


if __name__ == "__main__":
    from _ll_helpers import from_list, to_list  # type: ignore
    print(to_list(solve_reverse_list(from_list([1, 2, 3, 4]))))
