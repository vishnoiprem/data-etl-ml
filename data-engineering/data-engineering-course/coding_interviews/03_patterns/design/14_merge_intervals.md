# 14 — Merge Intervals

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>

A pattern for problems involving overlapping ranges.

## Template

1. Sort intervals by start time.
2. Iterate; keep a "current merged" interval.
3. If the next interval starts before the current merged ends, extend the current merged.
4. Otherwise, push the current merged to the result and start a new one.

## Examples in this course

- 90 Meeting Rooms II
