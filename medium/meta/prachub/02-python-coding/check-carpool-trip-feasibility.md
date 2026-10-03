# Check Carpool Trip Feasibility (Sweep Line)

## 1. Simple way to think
- Same shape as the LeetCode 1094 car-pooling problem, but the candidate is expected to recognize it as a sweep line problem.
- "Feasibility" means: at every point on the 1D route, the in-vehicle passenger count never exceeds capacity.
- Each trip contributes +p at `start`, -p at `end`. A sweep that maintains a running count answers the question in one pass.
- Sorted events guarantee that at any point, we know exactly how many passengers are in the car.

## 2. Interview write-up (how to solve it)

```python
def can_fulfill(trips, capacity):
    """
    trips: [(passengers, start, end), ...]
    Returns True if a single vehicle of given capacity can serve all trips.
    """
    events = []
    for p, s, e in trips:
        events.append((s, p))   # boarding
        events.append((e, -p))  # alighting

    # Sort: by position, and for equal position drop-offs (negative) first
    events.sort(key=lambda x: (x[0], x[1]))

    cur = 0
    for _, delta in events:
        cur += delta
        if cur > capacity:
            return False
    return True
```

The `key=lambda (pos, delta)` sort places drop-offs before pickups at the same coordinate, so a passenger getting off at point 5 frees the seat for a passenger boarding at point 5.

## 3. Best optimized solution

```python
def can_fulfill(trips, capacity):
    # O(n log n) sweep
    events = []
    for p, s, e in trips:
        events.append((s, p))
        events.append((e, -p))
    events.sort()                          # tuples sort lexicographically
    cur = 0
    for _, d in events:
        cur += d
        if cur > capacity:
            return False
    return True


# O(n + R) version for bounded integer coordinates
def can_fulfill_counting(trips, capacity, R=1001):
    diff = [0] * (R + 1)
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
assert can_fulfill([(2,1,5),(3,3,7)], 4) is False
assert can_fulfill([(2,1,5),(3,3,7)], 5) is True
assert can_fulfill([(2,1,5),(3,5,7)], 3) is True
assert can_fulfill([(3,0,3)], 3) is True
assert can_fulfill([(4,0,3)], 3) is False
print("ok")
```

### Why it's optimal
- O(n log n) sweep is the standard optimal approach.
- When coordinates are bounded (typical constraint), the diff-array version is O(n + R), beating any comparator sort.
- Single pass after sort; constant extra memory.

### Common mistakes & interviewer tips
- Sorting only by position and not handling the equal-position case — a passenger at point 5 needs to leave before a new one boards at 5.
- Forgetting that `start < end` is the assumed invariant; if not, validate first.
- Tip: state the invariant out loud and walk through a small example on the whiteboard. It shows process.
