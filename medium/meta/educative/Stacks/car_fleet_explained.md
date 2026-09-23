# Car Fleet - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/car-fleet

## The Problem
```
There are n cars going to the same destination at TARGET miles.
Each car has:
- position[i]: starting position (miles)
- speed[i]: speed (mph)

Cars CANNOT pass each other. When a faster car catches up to a slower
car ahead, it joins that fleet (moves at the slower speed).

A fleet is a group of one or more cars driving at the speed of the
slowest (front-most) car.

Return the number of fleets that will arrive at the destination.

Examples:
    target = 12, position = [10,8,0,5,3], speed = [2,4,1,1,3]  -> 3
    target = 10, position = [3], speed = [3]                    -> 1
    target = 100, position = [0,2,4], speed = [4,2,1]           -> 1

Constraints:
- n == position.length == speed.length
- 1 <= n <= 10^5
- 0 < target <= 10^6
- 0 <= position[i] < target
- 0 < speed[i] <= 10^6
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
target=12, position=[10,8,0,5,3], speed=[2,4,1,1,3]

Compute time to target for each car:
- pos 10, spd 2: time = (12-10)/2 = 1
- pos 8,  spd 4: time = (12-8)/4 = 1
- pos 0,  spd 1: time = (12-0)/1 = 12
- pos 5,  spd 1: time = (12-5)/1 = 7
- pos 3,  spd 3: time = (12-3)/3 = 3

Sort by position DESCENDING (closest to target first):
  (10, 2, t=1), (8, 4, t=1), (5, 1, t=7), (3, 3, t=3), (0, 1, t=12)
```

### Step 2: The Trick
> "Process cars from CLOSEST to target to FARTHEST.
> A car STARTS a new fleet iff its time > slowest_time_seen.
> If time <= slowest, it merges into the fleet ahead."

### Step 3: Why This Works
> "Cars can't pass. So a car can ONLY join a fleet if it's slower
> (or equal) to the slowest car ahead (the one with the highest time).
>
> When we process in order of decreasing position:
> - The car CLOSEST to target can never merge behind (no one ahead).
> - Each subsequent car: if its time > slowest_seen, no one ahead is
>   slower, so it forms its own fleet.
> - If its time <= slowest_seen, it WILL catch up."

---

## What to Say Aloud in the Interview

**Opening:**
> "There are n cars going to a target. Each has a position and speed.
> Cars can't pass - if a faster one catches a slower one ahead, they
> merge into a fleet. Return the number of fleets."

**Key Insight:**
> "Compute TIME TO TARGET for each car: (target - position) / speed.
> Sort cars by position DESCENDING (closest first).
> Walk through: a car starts a new fleet iff its time > slowest_time
> seen so far. Otherwise it merges into the fleet ahead."

**Algorithm:**
> "1. Pair (position, speed), sort by position descending
> 2. Initialize fleets = 0, slowest = 0
> 3. For each (pos, spd):
>    - time = (target - pos) / spd
>    - If time > slowest: fleets += 1, slowest = time
> 4. Return fleets"

**Why this works:**
> "When we process in order from closest to target to farthest:
> - The closest car has no one ahead - it always forms a fleet.
> - Each later car: if it's slower (more time) than the slowest car
>   ahead of it, it can't catch up - new fleet.
> - If it's faster or equal, it WILL catch up - merge."

**Edge cases:**
- Equal times: cars arrive at same time. They DO catch up (or arrive together) - 1 fleet.
- Single car: 1 fleet
- Same position, same speed: 1 fleet
- Already sorted input: still works

**Complexity:**
- Time: O(n log n) for sort
- Space: O(n) for the pairs

---

## The 20 Implementations (Simple to Complex)

### Way 1: Stack on time (BEST - Memorize!)
```python
def carFleet(target, position, speed):
    pairs = sorted(zip(position, speed), reverse=True)
    stack = []
    for pos, spd in pairs:
        time = (target - pos) / spd
        if not stack or time > stack[-1]:
            stack.append(time)
    return len(stack)
```

### Way 2-4: Variations with counter
```python
def carFleet(target, position, speed):
    pairs = sorted(zip(position, speed), reverse=True)
    fleets = 0
    slowest = 0.0
    for pos, spd in pairs:
        time = (target - pos) / spd
        if time > slowest:
            fleets += 1
            slowest = time
    return fleets
```

### Way 5: Using max-heap
```python
heap = []  # max-heap on position
for i in range(len(position)):
    heapq.heappush(heap, (-position[i], ...))
```

### Way 6-7: Variations
- Way 6: Pre-compute times list
- Way 7: Most concise version of Way 2

### Way 8: Using Fraction for exact arithmetic
- Avoids floating-point precision issues.

### Way 9: Sort indices
- Sort by index by position, then iterate.

### Way 10: Numpy
- Vectorized computation, then iterate.

### Way 11-12: Stack-based variations

### Way 13: Group sort

### Way 14: Most elegant (key=lambda)

### Way 15: Sort ascending then reverse slice
```python
pairs = sorted(zip(position, speed))[::-1]
```

### Way 16: Deque

### Way 17: Lead changes counter

### Way 18: Max-heap with negative positions

### Way 19: Class-based
```python
class CarFleetCounter:
    def __init__(self, target):
        self.target = target
        self.fleets = 0
        self.slowest = 0.0
    def add(self, position, speed): ...
```

### Way 20: Final cleanest

---

## Decision Tree

```
+------------------+----------+--------------+
| Scenario         | Best     | Why          |
+------------------+----------+--------------+
| Standard         | Way 1/2  | Clean O(nlogn)|
| Exact arithmetic | Way 8    | No float     |
+------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Sort + iterate | O(n log n) | O(n) |
| Heap | O(n log n) | O(n) |

---

## Walkthrough Example

```
target = 12, position = [10,8,0,5,3], speed = [2,4,1,1,3]

Pairs sorted desc by position:
(10,2), (8,4), (5,1), (3,3), (0,1)

Times: 1, 1, 7, 3, 12

Process (slowest=0, fleets=0):
- (10,2): time=1. 1 > 0: new fleet. fleets=1, slowest=1
- (8,4):  time=1. 1 > 1? No. Merge. fleets=1, slowest=1
- (5,1):  time=7. 7 > 1: new fleet. fleets=2, slowest=7
- (3,3):  time=3. 3 > 7? No. Merge. fleets=2, slowest=7
- (0,1):  time=12. 12 > 7: new fleet. fleets=3, slowest=12

Result: 3 fleets ✓
```

## Best Answer to Memorize

```python
def carFleet(target, position, speed):
    pairs = sorted(zip(position, speed), reverse=True)
    fleets = 0
    slowest = 0.0
    for pos, spd in pairs:
        time = (target - pos) / spd
        if time > slowest:
            fleets += 1
            slowest = time
    return fleets
```

**8 lines. O(n log n) time. Clean. Interview-ready!**

---

## Key Insights

### Why sort by position descending?
> "Closest to target first means we can determine if a car catches up.
> A car can only merge with the fleet AHEAD of it (smaller position
> means closer to target)."

### Why ">" not ">="?
> "Equal times: the car arrives EXACTLY when the fleet ahead arrives.
> They form ONE fleet (catch up at the target line)."

### Why not actual simulation?
> "Simulating positions would be O(n^2) or O(nt) where t is time.
> Time-to-target approach is O(n log n)."

### Why use floating point?
> "Time = (target - pos) / speed. With reasonable constraints, double
> precision is sufficient. For exact comparison, use Fractions."

---

## Test Cases

| target | position | speed | Expected |
|--------|----------|-------|----------|
| 12 | [10,8,0,5,3] | [2,4,1,1,3] | 3 |
| 10 | [3] | [3] | 1 |
| 100 | [0,2,4] | [4,2,1] | 1 |
| 10 | [0,4,6] | [2,1,3] | 2 |
| 10 | [6,2,9] | [3,1,4] | 3 |

## Common Pitfalls

1. **Wrong sort direction**: Sort by position DESCENDING (closest first).
2. **Wrong comparison**: Use ">" not ">=" for new fleet.
3. **Confusing time with speed**: Time = distance / speed.
4. **Forgetting equal times**: They merge into 1 fleet.
5. **Float precision**: For large inputs, consider Fractions.

## Why This Problem Matters

> "Tests:
> 1. Sort + greedy (CRITICAL pattern)
> 2. Stack vs counter - both work for tracking 'slowest'
> 3. Time computation with care for floats
> 4. Pattern similar to: merging intervals, leader count, monotonic stack
> 5. Real-world physics modeling"
