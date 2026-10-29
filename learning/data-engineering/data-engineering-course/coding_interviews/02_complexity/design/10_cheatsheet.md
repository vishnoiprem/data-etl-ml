# 10 — The Complexity Cheatsheet

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

A reference table for the patterns in this course.

| Operation | Time | Space |
| --- | --- | --- |
| Array lookup by index | O(1) | O(1) |
| Array linear scan | O(n) | O(1) |
| Hash set/map lookup | O(1) avg | O(n) |
| Binary search | O(log n) | O(1) |
| Quicksort / mergesort | O(n log n) avg | O(n) for merge, O(log n) for quick |
| Heap push/pop | O(log n) | O(1) |
| BFS/DFS over graph with n nodes, e edges | O(n + e) | O(n) |
| Recursion depth on balanced tree | — | O(log n) |
| String concatenation with `+` (k parts) | O(k · len) | O(k · len) |
| Two-pointer on sorted array | O(n) | O(1) |
| Sliding window over n items | O(n) | O(1) |
