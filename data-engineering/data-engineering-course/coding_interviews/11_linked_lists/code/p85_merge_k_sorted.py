"""Merge K Sorted Linked Lists — divide and conquer.

Time:  O(N log k) — N total nodes, log k levels of merging
Space: O(log k) — recursion stack
"""

import heapq
from _ll_helpers import ListNode  # type: ignore


def solve_merge_k_sorted(lists):
    """Merge k sorted linked lists and return the head of the result.

    >>> from _ll_helpers import from_list, to_list
    >>> to_list(solve_merge_k_sorted([from_list([1,4,5]), from_list([1,3,4]), from_list([2,6])]))
    [1, 1, 2, 3, 4, 4, 5, 6]
    """
    # Heap-based variant: O(N log k), simple to write.
    heap = []
    for i, head in enumerate(lists):
        if head is not None:
            heapq.heappush(heap, (head.val, i, head))
    dummy = ListNode(0)
    tail = dummy
    while heap:
        val, i, node = heapq.heappop(heap)
        tail.next = node
        tail = tail.next
        if node.next is not None:
            heapq.heappush(heap, (node.next.val, i, node.next))
    return dummy.next


if __name__ == "__main__":
    from _ll_helpers import from_list, to_list  # type: ignore
    lists = [from_list([1, 4, 5]), from_list([1, 3, 4]), from_list([2, 6])]
    print(to_list(solve_merge_k_sorted(lists)))
