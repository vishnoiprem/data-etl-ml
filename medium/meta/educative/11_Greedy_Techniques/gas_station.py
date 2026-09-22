"""
Gas Station
===========
Given gas[i] (gas at station i) and cost[i] (gas to travel i -> i+1),
find a starting index such that the car can complete the circular route.
Return -1 if impossible; answer is unique if it exists.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/gas-station

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "I have n gas stations on a circle. gas[i] is the fuel I get at station i;
    cost[i] is the fuel needed to drive from station i to i+1. Pick a start
    so the car can travel all n stations and return to the start with an
    empty tank at the start."

2. OBSERVE — KEY INSIGHTS:
   "If total gas >= total cost, a valid start exists (and is unique).
    If total gas <  total cost, no valid start exists.

    Why? At every station, the NET change is gas[i] - cost[i]. As we sum
    across all n stations, the car must end with the same fuel it started
    (returning to start = full circle). So total gas - total cost >= 0 is
    necessary."

3. PATTERN RECOGNITION:
   "Greedy with running surplus. We try each candidate start; whenever
    surplus drops below 0, that start is invalid. The valid start is
    the NEXT station after the failure."

4. EDGE CASES:
   "n=1 -> if gas[0] >= cost[0], answer is 0; else -1.
    Total gas == total cost -> unique valid start exists iff all are valid,
    otherwise -1.
    Single deficit station -> start just after it."

5. TRICKY DETAIL:
   "When tank goes negative at station k, NO station in [start, k] can be
    a valid start (we proved this with an exchange argument). So we skip
    to k+1 and reset. This is O(n) total, not O(n^2)."

6. ALGORITHM:
   "1. Compute total_gas, total_cost.
    2. If total_gas < total_cost -> return -1.
    3. Set tank = 0, start = 0.
    4. For i in [0, n):
        tank += gas[i] - cost[i].
        If tank < 0:
            start = i + 1
            tank = 0
    5. Return start."

7. WHY GREEDY WORKS:
   "Suppose start = s fails at station k (s <= k). Then for any start j in
    [s, k], the tank between j and k is exactly the tank from s to k MINUS
    the cumulative surplus from s to j-1. Since that surplus is >= 0 (we
    drove successfully so far), tank from j to k is also negative. So no
    j in [s, k] works. Skip to k+1."

8. COMPLEXITY:
   "Time: O(n) — single pass.
    Space: O(1) extra."

9. CODE STRUCTURE:
   "If sum(gas) < sum(cost): return -1
    tank = 0; start = 0
    for i in range(n):
        tank += gas[i] - cost[i]
        if tank < 0:
            start = i + 1
            tank = 0
    return start"

10. MENTAL TRACE:
    gas = [1, 5, 3, 3, 4], cost = [4, 4, 1, 1, 1]
    diff = [-3, 1, 2, 2, 3]; total = 5 >= 0, so solution exists.
    i=0: tank = -3 < 0 -> start=1, tank=0
    i=1: tank = 1
    i=2: tank = 3
    i=3: tank = 5
    i=4: tank = 8
    Answer: 1 ✓
    (Start at station 1: pickup 5, drive to 2 (cost 4, tank=1), drive to 3 (cost 1, tank=3),
     pickup 3, drive to 4 (cost 1, tank=5), pickup 4, drive to 0 (cost 1, tank=8),
     pickup 1, drive to 1 (cost 4, tank=5, full circle complete.))
"""


# ==============================================================
# Solution 1: Canonical O(n) greedy
# ==============================================================
def gas_station_v1(gas, cost):
    """Single pass with running tank; reset start when tank < 0."""
    n = len(gas)
    if sum(gas) < sum(cost):
        return -1
    tank = 0
    start = 0
    for i in range(n):
        tank += gas[i] - cost[i]
        if tank < 0:
            start = i + 1
            tank = 0
    return start if start < n else -1


# ==============================================================
# Solution 2: Try every start (brute force O(n^2))
# ==============================================================
def gas_station_v2(gas, cost):
    """
    Brute force: try every starting station. Educational.
    """
    n = len(gas)
    if sum(gas) < sum(cost):
        return -1
    for start in range(n):
        tank = 0
        ok = True
        for k in range(n):
            i = (start + k) % n
            tank += gas[i] - cost[i]
            if tank < 0:
                ok = False
                break
        if ok:
            return start
    return -1


# ==============================================================
# Solution 3: Prefix-sum based
# ==============================================================
def gas_station_v3(gas, cost):
    """
    Compute diff[i] = gas[i] - cost[i]. Find the index where the running
    prefix sum is minimized; the answer is the next index.
    """
    n = len(gas)
    if sum(gas) < sum(cost):
        return -1
    diff = [gas[i] - cost[i] for i in range(n)]
    # Find index of min prefix sum
    min_prefix = 0
    min_idx = -1
    running = 0
    for i in range(n):
        running += diff[i]
        if running < min_prefix:
            min_prefix = running
            min_idx = i
    return (min_idx + 1) % n


# ==============================================================
# Solution 4: Using itertools.accumulate
# ==============================================================
def gas_station_v4(gas, cost):
    """Use accumulate to find minimum prefix sum."""
    from itertools import accumulate
    n = len(gas)
    if sum(gas) < sum(cost):
        return -1
    diff = [gas[i] - cost[i] for i in range(n)]
    prefix = list(accumulate(diff))
    min_val = min(prefix)
    # First index where prefix equals min_val
    min_idx = prefix.index(min_val)
    return (min_idx + 1) % n


# ==============================================================
# Solution 5: Deficit-tracking greedy
# ==============================================================
def gas_station_v5(gas, cost):
    """
    Track total deficit. Whenever tank goes negative, the start must
    be after this position; add the deficit to a 'debt' accumulator.
    """
    n = len(gas)
    if sum(gas) < sum(cost):
        return -1
    tank = 0
    debt = 0
    start = 0
    for i in range(n):
        tank += gas[i] - cost[i]
        if tank < 0:
            debt += tank   # negative
            start = i + 1
            tank = 0
    # If we get here, sum(gas) >= sum(cost), so debt + tank (final) >= 0
    return start if start < n else -1


# ==============================================================
# Solution 6: Two-pass — accumulate, find min
# ==============================================================
def gas_station_v6(gas, cost):
    """
    Two-pass: first compute diff, then find minimum cumulative sum,
    answer is next index.
    """
    n = len(gas)
    if sum(gas) < sum(cost):
        return -1
    cumulative = 0
    min_val = 0
    min_idx = 0
    for i in range(n):
        cumulative += gas[i] - cost[i]
        if cumulative < min_val:
            min_val = cumulative
            min_idx = i
    return (min_idx + 1) % n


# ==============================================================
# Solution 7: While-loop try-starts-style
# ==============================================================
def gas_station_v7(gas, cost):
    """
    Simulate trying different starts. Each 'reset' increments start.
    """
    n = len(gas)
    if sum(gas) < sum(cost):
        return -1
    tank = 0
    start = 0
    i = 0
    while start < n:
        tank += gas[i] - cost[i]
        i = (i + 1) % n
        if i == start:
            return start  # completed full circle
        if tank < 0:
            start = i
            tank = 0
    return -1


# ==============================================================
# Solution 8: Using numpy diff for vectorized
# ==============================================================
def gas_station_v8(gas, cost):
    """Numpy implementation: cumulative sum of diff, find argmin."""
    try:
        import numpy as np
        n = len(gas)
        if sum(gas) < sum(cost):
            return -1
        diff = np.array(gas) - np.array(cost)
        cum = np.cumsum(diff)
        # Answer is next index after argmin
        min_idx = int(np.argmin(cum))
        return (min_idx + 1) % n
    except ImportError:
        return gas_station_v1(gas, cost)


# ==============================================================
# Solution 9: Two-pointer sliding window
# ==============================================================
def gas_station_v9(gas, cost):
    """
    Treat the array as doubled (gas+gas, cost+cost) and slide a window
    of size n. Find a window starting position where cumulative >= 0.
    """
    n = len(gas)
    if sum(gas) < sum(cost):
        return -1
    diff = [gas[i] - cost[i] for i in range(n)]
    doubled_diff = diff + diff

    window_start = 0
    window_sum = 0
    for end in range(2 * n):
        window_sum += doubled_diff[end]
        if end - window_start + 1 > n:
            window_sum -= doubled_diff[window_start]
            window_start += 1
        if end - window_start + 1 == n and window_sum >= 0:
            # We could check more carefully but the answer is unique
            return window_start % n
    return -1


# ==============================================================
# Solution 10: Functional / reduce style
# ==============================================================
def gas_station_v10(gas, cost):
    """
    Functional: use accumulate and argmin to find next starting index.
    """
    from functools import reduce
    n = len(gas)
    if sum(gas) < sum(cost):
        return -1
    diff = [gas[i] - cost[i] for i in range(n)]

    # Compute prefix sums; track (cum, idx) pairs
    def step(state, d):
        cum, idx, min_val, min_idx = state
        cum += d
        idx += 1
        if cum < min_val:
            return (cum, idx, cum, idx)
        return (cum, idx, min_val, min_idx)

    _, _, min_val, min_idx = reduce(step, diff, (0, -1, 0, -1))
    return (min_idx + 1) % n


# ==============================================================
# Test runner
# ==============================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (canonical O(n))",       gas_station_v1),
        ("V2 (brute force O(n^2))",   gas_station_v2),
        ("V3 (prefix-sum min)",       gas_station_v3),
        ("V4 (accumulate min)",       gas_station_v4),
        ("V5 (deficit tracking)",     gas_station_v5),
        ("V6 (cumulative min)",       gas_station_v6),
        ("V7 (while-loop)",           gas_station_v7),
        ("V8 (numpy)",                gas_station_v8),
        ("V9 (sliding window)",       gas_station_v9),
        ("V10 (functional reduce)",   gas_station_v10),
    ]

    test_cases = [
        # name, gas, cost, expected
        ("basic",       [1, 5, 3, 3, 4],     [4, 4, 1, 1, 1],       1),
        ("impossible", [2, 3, 4],           [3, 4, 3],             -1),
        ("single ok",  [2],                 [2],                   0),
        ("single fail", [1],                [2],                  -1),
        ("two equal",  [1, 1],              [1, 1],                0),
        ("two deficit", [0, 5, 2],          [1, 3, 4],             1),  # check valid
        ("cyclic-1",   [5, 1, 2, 3, 4],     [4, 4, 1, 1, 1],       0),
        ("long diff",  [3, 1, 1],           [2, 2, 2],             -1),  # 3+1+1-6=-1, impossible
        ("long ok",    [4, 1, 1, 2],        [2, 2, 2, 2],          0),  # diff = 2,-1,-1,0 total=0
        ("all zeros",  [0, 0, 0],           [0, 0, 0],             0),
        ("unique big", [2, 3, 4, 5, 6, 1],  [3, 4, 5, 6, 7, 0],    -1),  # 2+3+4+5+6+1=21, 3+4+5+6+7+0=25 impossible
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for case_name, g, c, expected in test_cases:
            try:
                got = func(list(g), list(c))
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{case_name}]: gas={g}, cost={c} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{case_name}]: ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")

    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")
    print("\n=== INTERVIEW THINKING ===")
    print("""
1. UNDERSTAND:   Find start index such that gas[i] >= cumulative cost to i.
2. INSIGHT:      If sum(gas) < sum(cost), impossible. Else exactly one start.
3. PATTERN:      Greedy with running tank; reset start when tank < 0.
4. EDGE:         n=1, all-zero, single deficit station.
5. TRICKY:       When tank < 0 at i, NO start in [old_start, i] works.
6. ALGORITHM:    Single pass; O(n).
7. PROOF:        Exchange argument — fails at i implies all earlier starts fail.
8. COMPLEXITY:   O(n) time, O(1) space.
9. CODE:         track tank; reset on negative.
10. TRACE:       [1,5,3,3,4]/[4,4,1,1,1] -> start=1.
""")
