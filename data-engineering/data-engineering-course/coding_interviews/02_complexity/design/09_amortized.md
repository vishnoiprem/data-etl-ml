# 09 — Amortized Analysis

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

Amortized analysis averages the cost of an operation over many calls. A single call may be expensive, but the *average* is cheap.

## Classic example: dynamic array append

In Python, `list.append` is amortized O(1). Occasionally the list is full and must be resized (O(n)), but that happens rarely enough that n appends cost O(n) total — averaging to O(1) per append.

## How to talk about it in an interview

- "Building the prefix sum is O(n) overall, amortized O(1) per element."
- "The hash map operations are amortized O(1) — a single resize can be expensive, but spread out it's constant."

## When it matters

When a problem says "n operations in sequence" and you need to defend your time bound, amortized analysis lets you cite a tight bound on the *total* work.
