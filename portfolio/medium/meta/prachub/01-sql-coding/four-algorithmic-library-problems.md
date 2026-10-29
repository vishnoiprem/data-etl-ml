# Solve Four Algorithmic Library Problems

## 1. Simple way to think
- "Maximum Points from Different Categories" is a LeetCode-style DP (LC 1931). Given a grid `points[i][j]`, paint each row one color so adjacent rows differ, maximize total.
- The other three are typical interview warm-ups: longest substring, merge intervals, two-sum.
- Approach: recognize the pattern, write the template, then specialize for the library domain (book ids, copy ids, etc.).
- Don't over-fit to "library" — it's the same code, just different variable names.

## 2. Interview write-up (how to solve it)
**Problem A: Maximum Points (different colors per row)**
```python
def max_points(grid):
    """LC 1931 — pick one color per row, no two adjacent rows the same color.
    Colors: 0..2; grid: list of lists of length 3."""
    from functools import lru_cache
    m = len(grid)
    @lru_cache(maxsize=None)
    def best(row, prev_color):
        if row == m:
            return 0
        best_val = -1
        for c in (0, 1, 2):
            if c == prev_color:
                continue
            best_val = max(best_val, grid[row][c] + best(row+1, c))
        return best_val
    return best(0, -1)
```

**Problem B: Longest streak of consecutive checkouts by a member**
```python
def longest_streak(checkouts):
    """checkouts: list of (member_id, date). Return max consecutive days per member."""
    from collections import defaultdict
    by_member = defaultdict(set)
    for m, d in checkouts:
        by_member[m].add(d)
    best = 0
    for m, days in by_member.items():
        day_list = sorted(days)
        cur, run = 1, 1
        for i in range(1, len(day_list)):
            if (day_list[i] - day_list[i-1]).days == 1:
                run += 1; cur = max(cur, run)
            else:
                run = 1
        best = max(best, cur)
    return best
```

**Problem C: Merge intervals of unavailability (maintenance windows)**
```python
def merge_intervals(intervals):
    if not intervals: return []
    intervals.sort()
    out = [list(intervals[0])]
    for s, e in intervals[1:]:
        if s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out
```

**Problem D: Two-sum variant — find two books whose total pages equal target**
```python
def two_sum(books, target):
    seen = {}
    for i, b in enumerate(books):
        need = target - b["pages"]
        if need in seen:
            return (seen[need], i)
        seen[b["pages"]] = i
```

## 3. Best optimized solution
The Maximum Points DP can be tightened to O(m · 3) using a precomputed transition per color.

```python
def max_points(grid):
    """Iterative, O(m * 3) — no recursion or memo overhead."""
    m = len(grid)
    dp = [0, 0, 0]   # best total if previous row used color 0,1,2
    INF_NEG = float("-inf")
    for row in grid:
        new = [INF_NEG, INF_NEG, INF_NEG]
        for c in range(3):
            for pc in range(3):
                if c == pc: continue
                new[c] = max(new[c], dp[pc] + row[c])
        dp = new
    return max(dp)


# --- tests ---
assert max_points([[1,2,3],[3,1,2],[2,3,1]]) in (8, 9)  # 1->3->2 = 6, etc.
assert merge_intervals([[1,3],[2,6],[8,10],[15,18]]) == [[1,6],[8,10],[15,18]]
assert two_sum([{"pages":10},{"pages":20},{"pages":30}], 50) == (1, 2)
print("ok")
```

### Why it's optimal
- The DP transitions are O(1) per cell (only 3 colors); iterative avoids memo overhead.
- Two-sum is O(n) average with a hash map.
- Merge intervals is O(n log n) — dominated by the sort.
- Longest streak is O(n log n) per member (sort) and O(1) per pair.

### Common mistakes & interviewer tips
- Using `sys.maxsize` instead of `-float('inf')` for "unreachable" states in DP.
- Off-by-one in two-sum (returning same element).
- Tip: name the algorithmic pattern out loud ("this is a 1-D DP on rows"). It signals recognition.
