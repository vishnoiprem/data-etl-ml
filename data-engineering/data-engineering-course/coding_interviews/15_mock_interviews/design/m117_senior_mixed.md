# Mock 117 — Senior/Staff Mixed

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>

## Format

- 60 minutes, 2 problems back-to-back (Medium then Hard).
- The "Hard" problem tests whether you can spot a clean abstraction.

## Problem 1 — LRU Cache (Medium)

Same as lesson 35, but as a 10-minute refresher.

## Problem 2 — LFU Cache (Hard)

Implement a cache that evicts the least-frequently-used key. On ties, evict the LRU among those.

## Talking points

- "Two maps: key → (freq, value), and freq → (ordered) dict of keys."
- "Why ordered? To break ties with LRU."
- "Alternative: a doubly linked list with embedded freq counters — more code, same complexity."

## Grading rubric

- **Strong Hire**: clean abstraction, O(1) all ops, discusses tradeoffs.
- **Hire**: works; small implementation debt.
- **Lean Hire**: gets there with hints.
- **No Hire**: can't see the freq→LRU tiebreak.
