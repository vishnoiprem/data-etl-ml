"""
Diet Plan Performance - 10 Ways
================================
A dieter consumes calories[i] calories on the i-th day.

Given a 1-day calorie upper bound, lower bound, and an integer k,
return the total number of points the dieter gets:

For each consecutive k days (a sliding window of size k):
- If total calories > upper: lose 1 point.
- Else if total < lower: gain 1 point.
- Else: no change.

Sum up the points across all windows.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/diet-plan-performance
          (LeetCode #1176)

Examples:
    calories = [1, 2, 3, 4, 5], k = 1, lower = 3, upper = 3
      -> 0
        (each day: 1<3 gain, 2<3 gain, 3 in [3,3] no change,
         4>3 lose, 5>3 lose. But points aren't summed over individual
         days; each window of size 1 is evaluated. So:
         Day 0: 1<3 gain -> 1
         Day 1: 2<3 gain -> 1
         Day 2: 3 in range -> 0
         Day 3: 4>3 lose -> -1
         Day 4: 5>3 lose -> -1
         Total: 0. ✓)
    calories = [6, 5, 0, 0], k = 2, lower = 1, upper = 5
      -> 0
        (window [6,5] sum=11 > 5: -1
         window [5,0] sum=5 in [1,5]: 0
         window [0,0] sum=0 < 1: +1
         Total: 0)
    calories = [6, 5, 0, 0], k = 3, lower = 1, upper = 5
      -> -1
        (window [6,5,0] sum=11 > 5: -1
         window [5,0,0] sum=5 in [1,5]: 0
         Total: -1)

Constraints:
- 1 <= k <= calories.length <= 10^5
- 0 <= calories[i] <= 20000
- 0 <= lower <= upper

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "For each consecutive k-day window, give +1/-1/0 based on total
    calories vs. lower/upper bounds. Sum points."

2. KEY INSIGHT:
   "Sliding window of size k. Track running sum. Compute points per
    window. Accumulate."

3. PATTERN RECOGNITION:
   "Fixed-size sliding window with running sum."

4. EDGE CASES:
   - k == n: single window.
   - k == 1: each day.
   - All in range: 0.
   - All above: -n+k-1 (number of windows).

5. TRICKY DETAIL:
   "The SUM (not average) of calories is compared to bounds."

6. ALGORITHM:
   "cur = sum(calories[0..k-1])
    points = score(cur)
    for i in range(k, n):
        cur += calories[i] - calories[i - k]
        points += score(cur)
    return points"

7. WHY IT WORKS:
   "Each window has a unique sum. We evaluate it once."

8. COMPLEXITY:
   "Time: O(n) - one pass.
    Space: O(1)."

9. CODE STRUCTURE:
   "Compute initial sum, score it. Slide, score each new sum."

10. MENTAL TRACE:
    calories = [6, 5, 0, 0], k = 2, lower = 1, upper = 5:
    Initial: sum = 6+5 = 11 > 5 -> -1. points = -1.
    i=2 (0): cur = 11 + 0 - 6 = 5. In [1,5] -> 0. points = -1.
    i=3 (0): cur = 5 + 0 - 5 = 0. < 1 -> +1. points = 0.
    Returns 0. ✓
"""


# Solution 1: Fixed sliding window with scoring (BEST)
def diet_plan_v1(calories, k, lower, upper):
    n = len(calories)
    cur = sum(calories[:k])
    points = 0

    def score(s):
        if s > upper:
            return -1
        if s < lower:
            return 1
        return 0

    points += score(cur)
    for i in range(k, n):
        cur += calories[i] - calories[i - k]
        points += score(cur)
    return points


# Solution 2: Same logic, inline score
def diet_plan_v2(calories, k, lower, upper):
    n = len(calories)
    cur = sum(calories[:k])
    points = 0
    if cur > upper:
        points -= 1
    elif cur < lower:
        points += 1
    for i in range(k, n):
        cur += calories[i] - calories[i - k]
        if cur > upper:
            points -= 1
        elif cur < lower:
            points += 1
    return points


# Solution 3: Using prefix sums
def diet_plan_v3(calories, k, lower, upper):
    n = len(calories)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + calories[i]
    points = 0
    for i in range(k, n + 1):
        s = prefix[i] - prefix[i - k]
        if s > upper:
            points -= 1
        elif s < lower:
            points += 1
    return points


# Solution 4: itertools.accumulate
def diet_plan_v4(calories, k, lower, upper):
    from itertools import accumulate
    n = len(calories)
    prefix = [0] + list(accumulate(calories))
    points = 0
    for i in range(k, n + 1):
        s = prefix[i] - prefix[i - k]
        if s > upper:
            points -= 1
        elif s < lower:
            points += 1
    return points


# Solution 5: Brute force O(n*k)
def diet_plan_v5(calories, k, lower, upper):
    n = len(calories)
    points = 0
    for i in range(n - k + 1):
        s = sum(calories[i:i + k])
        if s > upper:
            points -= 1
        elif s < lower:
            points += 1
    return points


# Solution 6: numpy version
def diet_plan_v6(calories, k, lower, upper):
    try:
        import numpy as np
        arr = np.array(calories)
        from numpy.lib.stride_tricks import sliding_window_view
        windows = sliding_window_view(arr, k)
        sums = windows.sum(axis=1)
        points = int(np.sum(sums > upper) * -1 + np.sum(sums < lower))
        return points
    except (ImportError, AttributeError):
        return diet_plan_v1(calories, k, lower, upper)


# Solution 7: Use deque (overkill)
def diet_plan_v7(calories, k, lower, upper):
    from collections import deque
    n = len(calories)
    if k > n:
        return 0
    dq = deque(calories[:k])
    cur = sum(calories[:k])
    points = 0
    if cur > upper:
        points -= 1
    elif cur < lower:
        points += 1
    for i in range(k, n):
        cur += calories[i] - dq.popleft()
        dq.append(calories[i])
        if cur > upper:
            points -= 1
        elif cur < lower:
            points += 1
    return points


# Solution 8: Recursive
def diet_plan_v8(calories, k, lower, upper):
    n = len(calories)

    def helper(i, cur, points):
        if i == n:
            return points
        if i < k:
            cur += calories[i]
            if i == k - 1:
                # Score the initial window
                if cur > upper:
                    points -= 1
                elif cur < lower:
                    points += 1
                return helper(i + 1, cur, points)
            return helper(i + 1, cur, points)
        else:
            # Slide window
            cur += calories[i] - calories[i - k]
            if cur > upper:
                points -= 1
            elif cur < lower:
                points += 1
            return helper(i + 1, cur, points)

    return helper(0, 0, 0)


# Solution 9: Using window slice (slow)
def diet_plan_v9(calories, k, lower, upper):
    n = len(calories)
    points = 0
    for i in range(n - k + 1):
        window = calories[i:i + k]
        s = sum(window)
        if s > upper:
            points -= 1
        elif s < lower:
            points += 1
    return points


# Solution 10: Final cleanest
def diet_plan_v10(calories, k, lower, upper):
    cur = sum(calories[:k])
    points = 0
    points += (cur < lower) - (cur > upper)
    for i in range(k, len(calories)):
        cur += calories[i] - calories[i - k]
        points += (cur < lower) - (cur > upper)
    return points


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (BEST)",                  diet_plan_v1),
        ("V2 (inline)",                diet_plan_v2),
        ("V3 (prefix sum)",            diet_plan_v3),
        ("V4 (accumulate)",            diet_plan_v4),
        ("V5 (brute)",                 diet_plan_v5),
        ("V6 (numpy)",                 diet_plan_v6),
        ("V7 (deque)",                 diet_plan_v7),
        ("V8 (recursive)",             diet_plan_v8),
        ("V9 (slice slow)",            diet_plan_v9),
        ("V10 (boolean math)",         diet_plan_v10),
    ]

    test_cases = [
        # (calories, k, lower, upper, expected)
        ([1, 2, 3, 4, 5], 1, 3, 3, 0),
        ([6, 5, 0, 0], 2, 1, 5, 0),
        ([6, 5, 0, 0], 3, 1, 5, -1),
        ([1, 1, 1, 1], 2, 2, 2, 0),  # each window sum = 2, in [2,2]
        ([10, 10, 10], 1, 0, 5, -3),  # each day > 5, k=1: -1 each = -3
        ([1, 1, 1, 1, 1], 5, 5, 5, 0),  # sum = 5, in range
        ([0, 0, 0, 0, 0], 3, 1, 10, 3),  # each window sum = 0 < 1: +1 each = 3
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (calories, k, lower, upper, expected) in enumerate(test_cases):
            try:
                got = func(calories[:], k, lower, upper)
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{idx}]: calories={calories}, k={k} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")