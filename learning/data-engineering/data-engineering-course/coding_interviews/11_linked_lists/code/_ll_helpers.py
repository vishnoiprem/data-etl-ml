"""Linked-list node + helpers for Module 11 — Linked Lists."""

from __future__ import annotations
from typing import List, Optional


class ListNode:
    """A singly linked-list node with an integer value."""

    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def from_list(values):
    """Build a linked list from a Python list and return the head.

    >>> from_list([1, 2, 3]).val
    1
    """
    head = None
    tail = None
    for v in values:
        node = ListNode(v)
        if head is None:
            head = node
            tail = node
        else:
            tail.next = node
            tail = node
    return head


def to_list(head):
    """Convert a linked list back to a Python list.

    >>> to_list(from_list([1, 2, 3]))
    [1, 2, 3]
    """
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out
