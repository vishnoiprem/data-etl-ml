# 13 — Fast & Slow Pointers

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

A "tortoise and hare" pattern: two pointers move at different speeds through a sequence.

## When to use

- Detect a cycle in a linked list (slow moves 1, fast moves 2; if they meet, there's a cycle)
- Find the middle of a linked list (when fast hits the end, slow is at the middle)
- Find the start of a cycle (after meeting, reset one pointer to head; both move 1 at a time)

## Examples in this course

- 82 Linked List Cycle
