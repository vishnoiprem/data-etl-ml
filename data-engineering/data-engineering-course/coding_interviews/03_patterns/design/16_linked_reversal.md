# 16 — In-place Reversal of a Linked List

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

The classic three-pointer pattern for reversing a singly linked list.

## Template

```python
prev = None
curr = head
while curr:
    nxt = curr.next
    curr.next = prev
    prev = curr
    curr = nxt
return prev
```

## Examples in this course

- 80 Reverse Linked List
- 83 Remove Nth From End
