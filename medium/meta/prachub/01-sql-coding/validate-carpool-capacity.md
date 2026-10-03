# Validate Carpool Capacity (LeetCode 1094)

## 1. Simple way to think
- Each trip is `[passengers, start, end]`. A vehicle has fixed capacity (default 4 in the LeetCode problem; here treat capacity as a parameter).
- At every point on the 1D route, the number of passengers in the car must be ≤ capacity.
- This is a "sweep line" problem: at `start`, passengers get on; at `end`, they get off.
- Sort all events, sweep left to right, track current load. If load > capacity, return `False`.

## 2. Interview write-up (how to solve it)
```python
def car_pooling(trips, capacity=4):
    """
    trips: list of [num_passengers, start_location, end_location]
    capacity: max passengers the vehicle can hold
    Returns True if every trip can be served without exceeding capacity.
    """
    events = []  # (position, delta_passengers)
    for p, s, e in trips:
        events.append((s,  p))   # pickups
        events.append((e, -p))   # drop-offs (handled BEFORE pickups at same point)

    # Sort: position asc; for equal position, drop-offs come first (smaller delta)
    events.sort(key=lambda x: (x[0], x[1]))

    current = 0
    for _, delta in events:
        current += delta
        if current > capacity:
            return False
    return True
```

## 3. Best optimized solution
Same approach but tightened: separate the two event types so the order at equal positions is unambiguous.

```python
def car_pooling(trips, capacity=4):
    events = []
    for p, s, e in trips:
        events.append((s, p))
        events.append((e, -p))

    # In-place sort: O(n log n). For very large n, use counting sort if coords
    # are bounded integers (common LeetCode constraint: 0 <= s,e < 1001).
    events.sort()

    cur = 0
    for _, delta in events:
        cur += delta
        if cur > capacity:
            return False
    return True


# Counting-sort version: O(n + R) where R is coordinate range
def car_pooling_counting(trips, capacity=4, max_coord=1000):
    diff = [0] * (max_coord + 2)
    for p, s, e in trips:
        diff[s] += p
        diff[e] -= p
    cur = 0
    for d in diff:
        cur += d
        if cur > capacity:
            return False
    return True


# --- tests ---
assert car_pooling([[2,1,5],[3,3,7]], 4) is False
assert car_pooling([[2,1,5],[3,3,7]], 5) is True
assert car_pooling([[2,1,5],[3,5,7]], 3) is True   # 2 on at 1, off at 5 just as 3 board
assert car_pooling([], 4) is True
print("ok")
```

### Why it's optimal
- Sweep line is the standard optimal approach: O(n log n) sort, O(n) sweep.
- When coordinates are bounded integers, the diff-array version is O(n + R), beating any comparator-based sort.
- The sort key `(position, delta)` ensures drop-offs happen before pickups at the same point.

### Common mistakes & interviewer tips
- Off-by-one: if a trip ends at position 5, another starts at 5 — they should NOT overlap. The sweep handles this if drop-offs sort before pickups.
- Using `min`/`max` updates instead of sweep — wrong, you need true ordering.
- Tip: state the invariant out loud: "At any position along the route, the running passenger count must stay ≤ capacity."
