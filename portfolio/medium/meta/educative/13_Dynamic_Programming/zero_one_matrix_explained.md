# 01 Matrix

## Problem
Given an `m × n` binary matrix, for each cell compute the distance to
the nearest `0` cell. Adjacency is up/down/left/right; each step costs 1.

## Approach: Multi-Source BFS

### Key Insight
All `0` cells are sources. Starting a BFS simultaneously from every
`0` lets the wave-front expand uniformly; the first time we reach a
cell, that distance is the minimum distance to ANY zero.

### Algorithm
1. Build a `dist` matrix initialized to `-1` (unvisited).
2. Set `dist[i][j] = 0` for every `0` cell; enqueue all of them.
3. BFS: for each popped cell `(i, j)`, for each unvisited neighbor
   `(ni, nj)`, set `dist[ni][nj] = dist[i][j] + 1` and enqueue it.
4. Return `dist`.

### Why BFS (not DFS)?
BFS guarantees the **first** time a cell is visited is via the
shortest path. DFS could find a longer path first.

## Walkthrough: `[[0,0,0],[0,1,0],[1,1,1]]`

Initial queue: all `0` cells (0,0), (0,1), (0,2), (1,0), (1,2).

BFS layers:
- Layer 0 (distance 0): the 5 zeros
- Layer 1 (distance 1): (1,1) — reached from (0,1) or (1,0) or (1,2); (2,0) from (1,0)
- Layer 2 (distance 2): (2,1) from (2,0) or (1,1); (2,2) from (1,2) or (2,1)... etc.

Result:
```
0 0 0
0 1 0
1 2 1
```

## Complexity
- **Time:** `O(m * n)` — each cell enqueued once
- **Space:** `O(m * n)` for `dist` + queue

## Alternative: 2-Pass DP
Could also do DP by scanning top-left to bottom-right (using top
and left neighbors), then bottom-right to top-left (using bottom
and right neighbors). Same `O(mn)` time but slightly more code.
BFS is cleaner.
