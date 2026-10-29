# 15 — Cyclic Sort

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

Used when the input is the numbers `1..n` (or `0..n-1`) and you need to place each in its correct index.

## Pattern

For each index `i`, swap `arr[i]` with `arr[arr[i]]` until `arr[i] == i + 1`. O(n) total because each swap places one element in its final position.

## Examples in this course

- 30 First Missing Positive
- 42 Merge Sorted Array (variant)
