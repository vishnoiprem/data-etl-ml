# Freedom Trail - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/freedom-trail

## The Problem
```
Given a circular ring (string) and a keyword, find min steps to spell the keyword.
Each rotation = 1 step, each button press = 1 step.

Examples:
    ring="godding", key="gd" -> 4
    ring="godding", key="godding" -> 13

Constraints:
- 1 <= ring.length, key.length <= 100
- Lowercase English letters.
```

## How I Think (The Mental Process)

### Step 1: Understand
```
We have a circular ring of characters. We can rotate it (1 step per rotation unit) and press the
button at the current 12-o'clock position (1 step). Goal: spell the key with minimum total steps.
```

### Step 2: The Trick
> "KEY INSIGHT: 2D DP.
>
> State: (i, j) = position i in the key, current position j in the ring.
> dp[i][j] = minimum steps to spell key[i..] starting with the ring at position j.
>
> Recurrence: dp[i][j] = min over k where ring[k] == key[i]:
>   rotation_cost(j, k) + dp[i+1][k] + 1 (for the press)
>
> rotation_cost(j, k) = min(|j-k|, n - |j-k|) (going clockwise or counter-clockwise).
>
> Base: dp[len(key)][j] = 0 (key already spelled)."

### Step 3: Why this works
> "At each key character, we choose which ring position to align with. The minimum cost is the minimum over all such choices. The +1 accounts for the button press."

### Step 4: Algorithm
> "1. Pre-compute char_positions: dict from char to list of indices in ring.
> 2. Initialize dp[m][j] = 0 for all j.
> 3. Fill dp[i][j] bottom-up from i=m-1 down to 0.
> 4. Return dp[0][0]."

### Step 5: Edge cases
> "- Empty key: return 0.
> - Single-character ring/key: just press once (return 1).
> - Same character appearing multiple times in ring: track all positions."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to find the minimum steps to spell the keyword by rotating a circular ring and pressing buttons."

**Key Insight:**
> "DP over (key index, ring position). At each step, try aligning each ring position containing the target character and take the minimum."

**Algorithm:**
> "1. Pre-compute positions of each character in ring.
> 2. dp[i][j] = min steps to spell key[i:] starting at ring position j.
> 3. For each i from end to start, for each j, try each k with ring[k]==key[i].
> 4. Cost = rotation_steps(j, k) + dp[i+1][k] + 1 (press).
> 5. Return dp[0][0]."

**Why this works:**
> "Each (key index, ring position) state represents a subproblem. The recurrence explores all valid next ring positions and takes the minimum."

**Edge cases:**
- Empty key: return 0.
- n=1 ring: trivial.

**Complexity:**
- Time:  O(m * n * avg_occurrences).
- Space: O(m * n) for 2D DP, O(n) for rolling.

---

## The 20 Implementations (Simple to Complex)

### Way 1: 2D DP (BEST - Memorize!)
```python
def findRotateSteps_1(ring, key):
    n = len(ring)
    m = len(key)
    from collections import defaultdict
    char_positions = defaultdict(list)
    for i, c in enumerate(ring):
        char_positions[c].append(i)

    INF = float('inf')
    dp = [[INF] * n for _ in range(m + 1)]
    for j in range(n):
        dp[m][j] = 0

    for i in range(m - 1, -1, -1):
        target_char = key[i]
        for j in range(n):
            best = INF
            for k in char_positions[target_char]:
                diff = abs(j - k)
                rot = min(diff, n - diff)
                best = min(best, rot + dp[i + 1][k] + 1)
            dp[i][j] = best

    return dp[0][0]
```

### Way 2: Memoized recursion
### Way 3: 1D rolling DP
### Way 4: Brute force recursion
### Way 5: lru_cache
### Way 6: Class-based
### Way 7: numpy vectorized
### Way 8: Dijkstra (priority queue)
### Way 9: min helper
### Way 10: Helper functions
### Way 11: Iterative
### Way 12: enumerate
### Way 13: Tabulation
### Way 14: BFS deque
### Way 15: Pre-compute distances
### Way 16: Bottom-up
### Way 17: Dijkstra
### Way 18: Stateful DP
### Way 19: Forward DP
### Way 20: Final cleanest

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Standard           | Way 1    | 2D DP, clear |
| Large ring/key     | Way 3    | Rolling DP   |
| Weighted shortest  | Way 8    | Dijkstra     |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| 2D DP (Way 1) | O(m * n * occ) | O(m * n) | Best for clarity |
| 1D rolling (Way 3) | O(m * n * occ) | O(n) | Better space |
| Dijkstra (Way 8) | O(m * n * log n) | O(m * n) | Alternative |

---

## Walkthrough Example

```
ring = "godding", key = "gd"

char_positions: g->[0,6], o->[1], d->[2,3], i->[4], n->[5]

Starting at ring position 0 (char 'g'):
- Spell 'g': already there, press (1 step). At position 0.
- Spell 'd': rotate from 0 to 2 (cost 2) or to 3 (cost 3). Take 2.
  Press (1 step). Total: 1 + 2 + 1 = 4.

Result: 4
```

---

## Best Answer to Memorize

```python
def findRotateSteps(ring, key):
    n = len(ring)
    m = len(key)
    from collections import defaultdict
    char_positions = defaultdict(list)
    for i, c in enumerate(ring):
        char_positions[c].append(i)

    INF = float('inf')
    dp = [[INF] * n for _ in range(m + 1)]
    for j in range(n):
        dp[m][j] = 0

    for i in range(m - 1, -1, -1):
        for j in range(n):
            for k in char_positions[key[i]]:
                diff = abs(j - k)
                rot = min(diff, n - diff)
                dp[i][j] = min(dp[i][j], rot + dp[i + 1][k] + 1)

    return dp[0][0]
```

**~18 lines. O(m*n) time. O(m*n) space. Interview-ready!**

---

## Key Insights

### Why circular rotation min?
> "We can go clockwise or counter-clockwise. Take the minimum: min(|j-k|, n-|j-k|)."

### Why DP and not BFS?
> "Costs vary per edge (rotation cost depends on distance). BFS doesn't handle weighted graphs. Use DP or Dijkstra."

### Why pre-compute char_positions?
> "Avoids re-scanning the ring for each j. Average occurrences per char is small."

### What about a non-circular ring?
> "Same algorithm but rotation_cost(j, k) = |j-k| (no wraparound)."

---

## Test Cases

| ring | key | Expected | Notes |
|------|-----|----------|-------|
| godding | gd | 4 | Standard |
| godding | godding | 13 | Full match |
| abcde | ade | 6 | Simple |
| a | a | 1 | Single |
| aaaaa | aaa | 3 | All same |

---

## Common Pitfalls

1. **Press count**: Don't forget to add +1 for the button press.
2. **Empty key**: Return 0 (no rotations needed).
3. **Circular rotation**: Use min(|j-k|, n-|j-k|), not just |j-k|.
4. **Direction choice**: Going clockwise or counter-clockwise is equally valid; pick min.

---

## Why This Problem Matters

> "Tests:
> 1. 2D DP on circular structure.
> 2. Weighted shortest path alternative (Dijkstra).
> 3. Foundation for: top-k shortest paths, multi-target DP."

---

## Beyond This Problem: Related Patterns

### 1. Rotating Game (similar pattern)
```python
# Multi-token ring rotation.
```

### 2. Edit Distance with Rotations (LC 514 variants)
```python
# Combine rotation with edit distance.
```

### 3. Sliding Puzzle (LC 773)
```python
# BFS over state space.
```

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 514 - Freedom Trail](https://leetcode.com/problems/freedom-trail/)
