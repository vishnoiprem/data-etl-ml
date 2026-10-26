"""Remove Nth Node From End of List.

Time:  O(n) — single pass with a gap of n
Space: O(1)
"""


def solve_remove_nth(head, n):
    """Remove the n-th node from the end and return the new head.

    >>> from _ll_helpers import from_list, to_list
    >>> to_list(solve_remove_nth(from_list([1,2,3,4,5]), 2))
    [1, 2, 3, 5]
    """
    dummy = ListNode(0, head)
    fast = dummy
    slow = dummy
    # Move fast n+1 steps ahead so slow ends up just before the target.
    for _ in range(n + 1):
        fast = fast.next
    while fast is not None:
        fast = fast.next
        slow = slow.next
    slow.next = slow.next.next
    return dummy.next


from _ll_helpers import ListNode  # type: ignore  # re-export


if __name__ == "__main__":
    from _ll_helpers import from_list, to_list  # type: ignore
    print(to_list(solve_remove_nth(from_list([1, 2, 3, 4, 5]), 2)))
