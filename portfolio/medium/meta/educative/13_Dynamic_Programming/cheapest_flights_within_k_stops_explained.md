# Cheapest Flights Within K Stops

## Problem
Given `n` cities and a list of directed flights `[from, to, price]`, find
the minimum cost to fly from `src` to `dst` using **at most `k` stops**
(equivalently, **at most `k+1` flights**). Return `-1` if no valid
route exists.

## Approach: Bellman-Ford-Style DP

We don't want shortest paths in general — we want shortest paths
**with a flight-count limit**. Plain Dijkstra would not respect that
constraint.

### State
`dp[u]` = minimum cost to reach city `u` using at most the current
number of flights allowed so far.

### Key Idea: Layered Relaxation
Run `k+1` rounds (since at most `k+1` flights).
Each round, try to relax every edge using the **snapshot** from the
previous round:
```
dp_new[v] = min(dp_new[v], dp_old[u] + w(u, v))
```

Using the snapshot (not the freshly-updated `dp_new[u]`) ensures that
each round adds **at most one flight** to the path, enforcing the
stop count.

### Answer
After `k+1` rounds, `dp[dst]` is the minimum cost.
If unreachable → return `-1`.

## Walkthrough: `n=3`, `k=1`, flights `[[0,1,100],[1,2,100],[0,2,500]]`

Initial: `dp = [0, ∞, ∞]`

Round 1 (≤ 1 flight):
- Relax 0→1: `dp[1] = min(∞, 0+100) = 100`
- Relax 1→2: `dp[2]` stays ∞ (dp_old[1] was ∞)
- Relax 0→2: `dp[2] = min(∞, 0+500) = 500`

`dp = [0, 100, 500]`

Round 2 (≤ 2 flights):
- Relax 0→1: stays 100
- Relax 1→2: `dp[2] = min(500, 100+100) = 200`
- Relax 0→2: stays 200

`dp = [0, 100, 200]`

Answer: `dp[2] = 200` ✓

## Complexity
- **Time:** `O((k+1) * |E|)` = `O(k * |E|)`
- **Space:** `O(n)` for the `dp` array (with snapshot copy `O(n)` per round, but we can reuse a single list with copy)

## Edge Cases
- `src == dst` → 0 (but constraints say `src != dst`)
- No flights at all → `-1`
- Cheaper direct route vs cheaper routed path: DP correctly handles trade-off
