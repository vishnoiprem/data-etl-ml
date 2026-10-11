# 07 — Big-O Notation

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

Big-O describes the upper bound of an algorithm's running time or space as the input size grows. We drop constants and lower-order terms.

## The growth-rate hierarchy (slowest → fastest)

```
O(1) < O(log n) < O(n) < O(n log n) < O(n²) < O(n³) < O(2ⁿ) < O(n!)
```

## Quick rules

- A single loop over n items → O(n)
- A loop inside a loop → O(n²)
- Halving the input each step → O(log n)
- Two sorted lists merged → O(n log n) total

## Why constants don't matter (in theory)

`3n² + 5n + 7` is O(n²). The 3 and 7 don't change the asymptotic class. In practice, an O(n²) algorithm with a small constant can beat an O(n log n) one for n < 100, but for large n the growth rate wins.
