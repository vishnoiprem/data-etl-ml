# Gas Station — 10 Solutions + Interview Thinking

## Problem
Given two integer arrays `gas` and `cost` of the same length `n`, where
`gas[i]` is the fuel available at station `i` and `cost[i]` is the fuel
needed to travel from station `i` to `i + 1` (circularly), find the
starting station such that the car can complete the full circuit and
return to the start. Return `-1` if impossible. If a valid start exists,
it is guaranteed to be unique.

Reference: LeetCode #134 / Educative Grokking — "Gas Station".

---

## Interview Thinking (10 Steps)

### 1. Understand
"I have `n` gas stations on a circle. At each station `i` I gain `gas[i]`
fuel, and to drive to station `i+1` I spend `cost[i]` fuel. I need to
find a starting index `s` such that — driving through all stations and
back to `s` — my tank never drops below zero."

### 2. Observe — Key Insights
- **Necessary condition:** `sum(gas) >= sum(cost)`. If we don't have
  enough total fuel, no start works.
- **Necessary AND sufficient when `sum(gas) > sum(cost)`:** exactly one
  valid start exists, and it can be found in `O(n)` with a greedy
  running-tally.
- **Tie-breaker for `sum(gas) == sum(cost)`:** The problem statement
  guarantees uniqueness — so the case of multiple valid starts cannot
  arise in test inputs.

### 3. Pattern Recognition
**Greedy with running surplus.** Walk around once. Keep a `tank` variable.
Whenever `tank < 0` after station `i`, no start in `[start, i]` can work
— so set `start = i + 1` and reset `tank = 0`.

### 4. Edge Cases
- `n == 0` → return `-1` (or any convention; the problem assumes `n ≥ 1`).
- `n == 1` → `0` if `gas[0] >= cost[0]`, else `-1`.
- All zeros → trivially `0` (start anywhere).
- `gas[i] == cost[i]` for all `i` → `0` (any start works; uniqueness says `0`).

### 5. Tricky Detail
**Why skip to `i + 1`?** Suppose start `s` failed at station `k` (i.e.,
`tank < 0` after visiting station `k`). For any start `j ∈ [s, k]`, the
cumulative surplus from `j` to `k` equals the cumulative surplus from
`s` to `k` **minus** the cumulative surplus from `s` to `j-1`. Since the
surplus from `s` to `j-1` is `≥ 0` (we drove successfully so far), the
surplus from `j` to `k` is also negative. So no `j ∈ [s, k]` works.

### 6. Algorithm
```
if sum(gas) < sum(cost): return -1
tank = 0; start = 0
for i in 0..n-1:
    tank += gas[i] - cost[i]
    if tank < 0:
        start = i + 1
        tank = 0
return start
```

### 7. Why Greedy Works (Proof Sketch)
**Exchange argument**: Let `s` be the start that fails at station `k`.
For any candidate start `j ∈ [s, k]`:
- The fuel from `s` to `k` is the sum of `gas[t] - cost[t]` over `[s, k]`.
- The fuel from `j` to `k` is the same sum **minus** the surplus from
  `s` to `j-1`, which is `≥ 0`.
- So the fuel from `j` to `k` is even more negative → `j` fails too.
- Hence we can skip all of `[s, k]` and resume from `k+1`.

### 8. Complexity
- **Time:** `O(n)` — single pass.
- **Space:** `O(1)` extra.

### 9. Code Structure
```python
def gas_station(gas, cost):
    if sum(gas) < sum(cost):
        return -1
    tank, start = 0, 0
    for i, (g, c) in enumerate(zip(gas, cost)):
        tank += g - c
        if tank < 0:
            start = i + 1
            tank = 0
    return start
```

### 10. Mental Trace
`gas = [1, 5, 3, 3, 4]`, `cost = [4, 4, 1, 1, 1]`:
- `diff = [-3, 1, 2, 2, 3]`. Sum = `5 > 0` → possible.
- i=0: tank = -3 < 0 → start = 1, tank = 0.
- i=1: tank = 1.
- i=2: tank = 3.
- i=3: tank = 5.
- i=4: tank = 8.
- **Answer: 1** ✓

Verify: Start at 1. Tank = 5 - 4 = 1 (after station 1→2).
At station 2: tank = 1 + 3 - 1 = 3. At station 3: 3 + 3 - 1 = 5.
At station 4: 5 + 4 - 1 = 8. At station 0: 8 + 1 - 4 = 5. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time      | Notes |
|----|---------------------------------------|-----------|-------|
| 1  | Canonical running-tank greedy         | O(n)      | ★★★★★ |
| 2  | Brute-force try every start           | O(n²)     | educational |
| 3  | Prefix-sum (last-min)                 | O(n)      | elegant |
| 4  | `itertools.accumulate`                | O(n)      | pythonic |
| 5  | Deficit tracking                      | O(n)      | tracks debt |
| 6  | Cumulative-min (last-occurrence)      | O(n)      | careful with ties |
| 7  | While-loop simulation                 | O(n)      | alternative style |
| 8  | Numpy vectorized                      | O(n)      | uses `np.cumsum` |
| 9  | Sliding window on doubled array       | O(n)      | last-min variant |
| 10 | `functools.reduce` functional         | O(n)      | FP style |

---

## Recommended Interview Answer
**Solution 1** — single-pass greedy. Clean, optimal, intuitive:

```python
def gas_station(gas, cost):
    if sum(gas) < sum(cost):
        return -1
    tank, start = 0, 0
    for i, (g, c) in enumerate(zip(gas, cost)):
        tank += g - c
        if tank < 0:
            start = i + 1
            tank = 0
    return start
```

---

## Common Pitfalls
1. **Forgetting the total-surplus check** — without it, you may return an
   index even when no valid start exists (e.g., `[2,3,4]/[3,4,3]`).
2. **Using `<` instead of `<=` when tracking minimum prefix** — when
   `sum(gas) == sum(cost)` and the minimum is hit at multiple indices,
   pick the LAST occurrence, not the first.
3. **Off-by-one in `start = i + 1`** — if `start` ends up equal to `n`,
   you've cycled past all stations, which means no valid start exists.
4. **Confusing `gas[i] - cost[i]` direction** — the *net gain* at station
   `i` is `gas[i] - cost[i]`, not the other way around.
5. **Trying to use a brute-force O(n²) approach when the unique-answer
   guarantee makes O(n) trivial** — the greedy is short and elegant.
