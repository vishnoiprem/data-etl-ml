# Mock 116 — L6 Google Onsite

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

## Format

- 60 minutes, 1 problem, 1 interviewer.
- Higher bar for clean abstractions, edge cases, and follow-ups.

## Problem — Random Pick with Weight

Given a list of positive weights, implement a class that picks an index with probability proportional to its weight.

## Talking points

- "I'll use prefix sums + binary search."
- "Why not iterate to find the cumulative sum? O(n) per pick. With binary search it's O(log n)."
- "Edge cases: single element, all equal weights, very large weights."

## Grading rubric

- **Strong Hire**: O(log n) pick using prefix sums; discusses tie-breaking and randomness.
- **Hire**: O(log n) but minor cleanup.
- **Lean Hire**: O(n) pick; gets to prefix sums on a hint.
- **No Hire**: doesn't see the binary search connection.
