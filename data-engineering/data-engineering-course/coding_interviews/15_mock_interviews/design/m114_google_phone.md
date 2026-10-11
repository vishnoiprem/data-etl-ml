# Mock 114 — L5 Google Phone Screen (1 problem + complexity)

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

## Format

- 45 minutes, 1 problem (Medium-Hard), 1 interviewer.
- 5 minutes at the end for "what's the time/space complexity? could you do better?"

## Problem — Longest Substring with At Most 2 Distinct Characters

Same as lesson 50 but with k=2 fixed.

Time: O(n), Space: O(1) — only a small map of distinct chars.

## Talking points

- "If I fix k=2, the implementation is just a sliding window with a per-character counter."
- "What if I generalized to k? Same idea — just keep a counter dict."
- "Edge cases: empty string → 0; one char string → 1."

## Grading rubric

- **Strong Hire**: optimal, clean, generalizes to k without prompting.
- **Hire**: optimal for k=2, talks through generalization.
- **Lean Hire**: works but doesn't notice the constant-space optimization until prompted.
- **No Hire**: not optimal, e.g. tries a hashmap of all substrings.
