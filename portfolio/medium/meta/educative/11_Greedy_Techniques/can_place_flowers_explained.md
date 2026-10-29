# Can Place Flowers — 10 Solutions + Interview Thinking

## Problem
Given a flowerbed (0 = empty, 1 = planted) and integer `n`, determine
if `n` new flowers can be planted such that no two flowers are in
adjacent plots.

## Interview Thinking (10 Steps)

### 1. Understand
"Can I plant n more flowers in the bed without violating the no-adjacent rule?"

### 2. Observe — Key Insight
**Greedy: plant at the leftmost valid empty plot.** Each plant consumes
maximum empty space, leaving the most flexibility for future plants.

### 3. Pattern Recognition
This is a **single-pass greedy / one-pass scan** problem. We track
available empty plots and decide placements greedily.

### 4. Edge Cases
- `n == 0` → trivially True.
- Plot 0 has no left neighbor; plot `len-1` has no right neighbor (boundaries are easier).
- Single empty plot → can plant 1 flower.
- All plots already planted → `n == 0` only.

### 5. Tricky Detail
Plot `i` is plantable iff:
- `flowerbed[i] == 0`
- `flowerbed[i-1] == 0` (or `i == 0`)
- `flowerbed[i+1] == 0` (or `i == len-1`)

### 6. Algorithm (one pass)
```
for i in 0..len:
    if flowerbed[i] == 0 AND prev == 0 AND next == 0:
        flowerbed[i] = 1
        n -= 1
        if n == 0: return True
return n <= 0
```

### 7. Why Greedy Works
**Exchange argument**: planting leftmost never reduces the maximum
number of flowers plantable. Suppose optimal solution plants at
position `j > i`. We can swap to plant at `i` (which is also valid
in any solution that plants at `j`), and the rest of the optimal
solution still works.

### 8. Complexity
- **Time:** `O(len)` — single pass.
- **Space:** `O(1)` — in-place modification (or copy if input is immutable).

### 9. Code Structure
```python
for i in range(len(flowerbed)):
    if flowerbed[i] == 0:
        prev = flowerbed[i-1] if i > 0 else 0
        nxt = flowerbed[i+1] if i+1 < len(flowerbed) else 0
        if prev == 0 and nxt == 0:
            flowerbed[i] = 1
            n -= 1
            if n <= 0: return True
return n <= 0
```

### 10. Mental Trace
`[1,0,0,0,1], n=1`:
- i=0: planted, skip
- i=1: prev=1, skip
- i=2: prev=0, next=0, plant! → `[1,0,1,0,1]`, n=0, return True ✓

---

## 10 Solutions Summary

| #  | Approach                                  | Time  | Notes |
|----|-------------------------------------------|-------|-------|
| 1  | In-place greedy single-pass (CANONICAL)   | O(n)  | ★★★★★ |
| 2  | Non-mutating single pass                  | O(n)  | safe for input |
| 3  | Sentinel padding (cleaner boundaries)     | O(n)  | +2 zeros |
| 4  | Skip by 2 after planting                  | O(n)  | jumps |
| 5  | Formula-based (count max plantable)       | O(n)  | math-only |
| 6  | Recursive greedy                          | O(n²) | educational |
| 7  | Memoized recursion                        | O(n²) | educational |
| 8  | Enumerate-based                           | O(n)  | pythonic |
| 9  | While loop                                | O(n)  | alternative |
| 10 | `all()` check for neighborhood            | O(n)  | compact |

---

## Recommended Interview Answer
**Solution 1** (in-place greedy): clean, optimal, idiomatic.

```python
def can_place_flowers(flowerbed, n):
    if n <= 0: return True
    length = len(flowerbed)
    for i in range(length):
        if flowerbed[i] == 0:
            prev = flowerbed[i-1] if i > 0 else 0
            nxt = flowerbed[i+1] if i+1 < length else 0
            if prev == 0 and nxt == 0:
                flowerbed[i] = 1
                n -= 1
                if n <= 0: return True
    return n <= 0
```

---

## Common Pitfalls
1. **Forgetting boundary plots** — `i=0` has no left neighbor, `i=n-1` has no right.
2. **Planting and then re-checking** — after planting at `i`, the next valid position is `i+2` (because `i+1` is now blocked).
3. **Off-by-one in `n <= 0` check** — must use `<= 0`, not `== 0`.
4. **Mutating input** — depends on whether mutation is allowed.
