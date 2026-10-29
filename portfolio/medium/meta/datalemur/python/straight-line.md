## Problem
**Straight Line [Easy]** — Given a list of `(x, y)` coordinate points, determine whether they all lie on a single straight line. Return `True` if they do, else `False`.

The list can have 0, 1, or 2 points (always trivially a line), or many points. Assume inputs are integers.

---

## 1. Simple way to think
- Two points always make a line.
- To check a third (and beyond), see if it sits on the line made by the first two.
- The slope from point A to point B equals `(y2 - y1) / (x2 - x1)`. For a third point C, the slope from A to C must be the same.
- Watch out for **vertical lines** where `x2 == x1` — slope division blows up. Handle that case separately: all `x`s must be equal.
- Equivalently, use the cross-multiplication trick: `(y3 - y1)*(x2 - x1) == (y2 - y1)*(x3 - x1)`. No division, no floating-point errors.

## 2. Interview write-up (how to solve it)
I'll handle edge cases first, then use the cross-multiplication slope equality check.

```python
def on_straight_line(coordinates):
    n = len(coordinates)
    # 0, 1, or 2 points are always on a straight line
    if n <= 2:
        return True

    x0, y0 = coordinates[0]
    x1, y1 = coordinates[1]
    dx = x1 - x0
    dy = y1 - y0

    # iterate over remaining points
    for x, y in coordinates[2:]:
        # check (y - y0) * dx == (x - x0) * dy
        if (y - y0) * dx != (x - x0) * dy:
            return False
    return True
```

Why this works: the equation of the line through `(x0, y0)` and `(x1, y1)` is `(y - y0) * dx == (x - x0) * dy`. Any other point on the line satisfies it. Using integer multiplication avoids floating-point precision issues.

## 3. Best optimized solution
```python
def on_straight_line(coordinates):
    n = len(coordinates)
    if n <= 2:
        return True

    (x0, y0), (x1, y1) = coordinates[0], coordinates[1]
    dx, dy = x1 - x0, y1 - y0

    return all(
        (y - y0) * dx == (x - x0) * dy
        for (x, y) in coordinates[2:]
    )
```

Quick test:
```python
assert on_straight_line([]) == True
assert on_straight_line([(0,0)]) == True
assert on_straight_line([(0,0),(1,1),(2,2),(3,3)]) == True
assert on_straight_line([(0,0),(1,1),(2,3)]) == False
assert on_straight_line([(1,5),(3,5),(7,5)]) == True     # horizontal
assert on_straight_line([(2,0),(2,1),(2,9)]) == True     # vertical
```

### Why it's optimal
- **O(n)** time — one pass after computing the reference slope.
- **O(1)** extra space — only the reference slope is stored.
- No floating point; integer arithmetic stays exact for any integer inputs.

### Common mistakes & interviewer tips
Common mistake: using float division for slope and then comparing with a tolerance — that fails on huge or near-collinear points. The cross-multiplication form `(y - y0)*dx == (x - x0)*dy` is bulletproof. Tip: always handle the n ≤ 2 case explicitly; some candidates forget that empty input or a single point should return True.