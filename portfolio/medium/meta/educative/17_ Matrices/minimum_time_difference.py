"""
Minimum Time Difference
Medium | 30 min

Given timePoints (24-hour "HH:MM" format), find minimum difference in
MINUTES between any two time points.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-time-difference

Examples:
    timePoints=["23:59","00:00"] -> 1
    timePoints=["00:00","04:00","22:00"] -> 120
    timePoints=["23:59","00:00","12:34"] -> 1

Constraints:
- 2 <= timePoints.length <= 200
- timePoints[i] in "HH:MM" format.

KEY INSIGHT: Convert to minutes (0-1439), sort, find min diff. Also
consider WRAP-AROUND: (first + 1440) - last.
"""


def _to_minutes(t):
    """Convert 'HH:MM' to minutes since midnight."""
    h, m = t.split(':')
    return int(h) * 60 + int(m)


# =============================================================================
# WAY 1: Sort + scan with wrap-around (BEST - Memorize!)
# =============================================================================
def findMinDifference_1(timePoints):
    """
    Convert to minutes. Sort. Find min diff. Also check wrap-around.
    """
    minutes = sorted(_to_minutes(t) for t in timePoints)
    n = len(minutes)
    # Add wrap-around: (first + 1440) - last
    min_diff = (minutes[0] + 1440) - minutes[-1]
    for i in range(1, n):
        diff = minutes[i] - minutes[i - 1]
        if diff < min_diff:
            min_diff = diff
    return min_diff


# =============================================================================
# WAY 2: Sort + linear scan (verbose)
# =============================================================================
def findMinDifference_2(timePoints):
    minutes = sorted(_to_minutes(t) for t in timePoints)
    n = len(minutes)
    min_diff = float('inf')
    for i in range(n - 1):
        d = minutes[i + 1] - minutes[i]
        if d < min_diff:
            min_diff = d
    # Wrap-around
    wrap = (minutes[0] + 1440) - minutes[-1]
    return min(min_diff, wrap)


# =============================================================================
# WAY 3: Bucket sort - O(n) using 1440 buckets
# =============================================================================
def findMinDifference_3(timePoints):
    """Use boolean array of size 1440."""
    seen = [False] * 1440
    for t in timePoints:
        m = _to_minutes(t)
        if seen[m]:  # duplicate, diff = 0
            return 0
        seen[m] = True
    first = -1
    prev = -1
    min_diff = 1440
    for i in range(1440):
        if seen[i]:
            if first == -1:
                first = i
            else:
                d = i - prev
                if d < min_diff:
                    min_diff = d
            prev = i
    # Wrap-around
    wrap = (first + 1440) - prev
    return min(min_diff, wrap)


# =============================================================================
# WAY 4: Brute force - all pairs
# =============================================================================
def findMinDifference_4(timePoints):
    n = len(timePoints)
    minutes = [_to_minutes(t) for t in timePoints]
    min_diff = float('inf')
    for i in range(n):
        for j in range(i + 1, n):
            d = abs(minutes[j] - minutes[i])
            d = min(d, 1440 - d)  # wrap-around
            if d < min_diff:
                min_diff = d
                if min_diff == 0:
                    return 0
    return min_diff


# =============================================================================
# WAY 5: Sort + min with zip
# =============================================================================
def findMinDifference_5(timePoints):
    minutes = sorted(_to_minutes(t) for t in timePoints)
    # Pair consecutive minutes
    diffs = [minutes[i] - minutes[i - 1] for i in range(1, len(minutes))]
    wrap = (minutes[0] + 1440) - minutes[-1]
    return min(min(diffs), wrap) if diffs else wrap


# =============================================================================
# WAY 6: Set + iterate sorted
# =============================================================================
def findMinDifference_6(timePoints):
    minutes_set = set(_to_minutes(t) for t in timePoints)
    if len(minutes_set) < len(timePoints):
        return 0  # duplicate
    minutes = sorted(minutes_set)
    n = len(minutes)
    min_diff = (minutes[0] + 1440) - minutes[-1]
    for i in range(1, n):
        d = minutes[i] - minutes[i - 1]
        if d < min_diff:
            min_diff = d
    return min_diff


# =============================================================================
# WAY 7: Numpy approach
# =============================================================================
def findMinDifference_7(timePoints):
    import numpy as np
    arr = np.array([_to_minutes(t) for t in timePoints])
    arr.sort()
    diffs = np.diff(arr)
    wrap = (arr[0] + 1440) - arr[-1]
    return int(min(diffs.min() if len(diffs) > 0 else 1440, wrap))


# =============================================================================
# WAY 8: Sort + reduce
# =============================================================================
def findMinDifference_8(timePoints):
    from functools import reduce
    minutes = sorted(_to_minutes(t) for t in timePoints)
    n = len(minutes)

    def reducer(acc, i):
        d = minutes[i] - minutes[i - 1]
        return min(acc, d)

    if n < 2:
        return 0
    min_diff = reduce(reducer, range(1, n), float('inf'))
    wrap = (minutes[0] + 1440) - minutes[-1]
    return min(min_diff, wrap)


# =============================================================================
# WAY 9: Class OOP
# =============================================================================
class TimeDifferenceFinder:
    def __init__(self, timePoints):
        self.minutes = sorted(_to_minutes(t) for t in timePoints)

    def find_min(self):
        n = len(self.minutes)
        min_diff = (self.minutes[0] + 1440) - self.minutes[-1]
        for i in range(1, n):
            d = self.minutes[i] - self.minutes[i - 1]
            if d < min_diff:
                min_diff = d
        return min_diff


def findMinDifference_9(timePoints):
    return TimeDifferenceFinder(timePoints).find_min()


# =============================================================================
# WAY 10: Using itertools pairwise
# =============================================================================
def findMinDifference_10(timePoints):
    from itertools import pairwise
    minutes = sorted(_to_minutes(t) for t in timePoints)
    diffs = [b - a for a, b in pairwise(minutes)]
    wrap = (minutes[0] + 1440) - minutes[-1]
    return min(min(diffs) if diffs else 1440, wrap)


# =============================================================================
# WAY 11: Sort + manual min
# =============================================================================
def findMinDifference_11(timePoints):
    minutes = sorted(_to_minutes(t) for t in timePoints)
    min_diff = 1440
    for i in range(1, len(minutes)):
        d = minutes[i] - minutes[i - 1]
        if d < min_diff:
            min_diff = d
    wrap = (minutes[0] + 1440) - minutes[-1]
    return min(min_diff, wrap)


# =============================================================================
# WAY 12: With tuple unpacking from sorted
# =============================================================================
def findMinDifference_12(timePoints):
    minutes = sorted(_to_minutes(t) for t in timePoints)
    n = len(minutes)
    min_diff = 1440
    for prev, curr in zip(minutes, minutes[1:]):
        d = curr - prev
        if d < min_diff:
            min_diff = d
    wrap = (minutes[0] + 1440) - minutes[-1]
    return min(min_diff, wrap)


# =============================================================================
# WAY 13: Sort + generator
# =============================================================================
def findMinDifference_13(timePoints):
    minutes = sorted(_to_minutes(t) for t in timePoints)
    n = len(minutes)
    if n < 2:
        return 0

    def gen_diffs():
        for i in range(1, n):
            yield minutes[i] - minutes[i - 1]

    min_diff = min(gen_diffs())
    wrap = (minutes[0] + 1440) - minutes[-1]
    return min(min_diff, wrap)


# =============================================================================
# WAY 14: Sort + enumerate
# =============================================================================
def findMinDifference_14(timePoints):
    minutes = sorted(_to_minutes(t) for t in timePoints)
    min_diff = 1440
    for i, m in enumerate(minutes[1:], start=1):
        d = m - minutes[i - 1]
        if d < min_diff:
            min_diff = d
    wrap = (minutes[0] + 1440) - minutes[-1]
    return min(min_diff, wrap)


# =============================================================================
# WAY 15: Sorted with key
# =============================================================================
def findMinDifference_15(timePoints):
    minutes = sorted(timePoints, key=_to_minutes)
    n = len(minutes)
    min_diff = 1440
    for i in range(1, n):
        d = _to_minutes(minutes[i]) - _to_minutes(minutes[i - 1])
        if d < min_diff:
            min_diff = d
    wrap = _to_minutes(minutes[0]) + 1440 - _to_minutes(minutes[-1])
    return min(min_diff, wrap)


# =============================================================================
# WAY 16: Sort + filter
# =============================================================================
def findMinDifference_16(timePoints):
    minutes = sorted(_to_minutes(t) for t in timePoints)
    n = len(minutes)
    # Check for duplicates first (early exit for 0)
    if len(set(minutes)) < n:
        return 0
    # Use filter to get diffs < current min (early termination idea)
    min_diff = 1440
    for i in range(1, n):
        d = minutes[i] - minutes[i - 1]
        if 0 < d < min_diff:
            min_diff = d
            if min_diff == 1:
                return 1
    wrap = (minutes[0] + 1440) - minutes[-1]
    return min(min_diff, wrap)


# =============================================================================
# WAY 17: Sort + lambda
# =============================================================================
def findMinDifference_17(timePoints):
    minutes = sorted(_to_minutes(t) for t in timePoints)
    n = len(minutes)
    diffs = list(map(lambda i: minutes[i] - minutes[i - 1], range(1, n)))
    wrap = (minutes[0] + 1440) - minutes[-1]
    return min(min(diffs) if diffs else 1440, wrap)


# =============================================================================
# WAY 18: Sort + slice min
# =============================================================================
def findMinDifference_18(timePoints):
    minutes = sorted(_to_minutes(t) for t in timePoints)
    n = len(minutes)
    if n < 2:
        return 0
    # Direct min of slice differences
    pairs = [(minutes[i], minutes[i + 1]) for i in range(n - 1)]
    min_diff = min(b - a for a, b in pairs)
    wrap = (minutes[0] + 1440) - minutes[-1]
    return min(min_diff, wrap)


# =============================================================================
# WAY 19: Sort + recursion
# =============================================================================
def findMinDifference_19(timePoints):
    minutes = sorted(_to_minutes(t) for t in timePoints)
    n = len(minutes)

    def helper(i, current_min):
        if i >= n:
            return current_min
        d = minutes[i] - minutes[i - 1]
        return helper(i + 1, min(current_min, d))

    min_diff = helper(1, 1440)
    wrap = (minutes[0] + 1440) - minutes[-1]
    return min(min_diff, wrap)


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def findMinDifference_20(timePoints):
    """
    THE ONE TO MEMORIZE.

    1. Convert to minutes.
    2. Sort.
    3. Find min diff between consecutive.
    4. Don't forget wrap-around: (first + 1440) - last.

    Time:  O(n log n)
    Space: O(n)
    """
    minutes = sorted(_to_minutes(t) for t in timePoints)
    min_diff = (minutes[0] + 1440) - minutes[-1]  # wrap-around
    for i in range(1, len(minutes)):
        min_diff = min(min_diff, minutes[i] - minutes[i - 1])
    return min_diff


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the minimum difference in minutes between any two
time points in 'HH:MM' format."

Key Insight:
"Convert each time to minutes (0-1439). Sort. The minimum difference
between consecutive times in the sorted list is the answer.
BUT: I also need to consider WRAP-AROUND: from midnight to midnight
or from the LAST time back to the FIRST time + 24 hours."

Algorithm:
1. Convert all times to minutes: t -> int(t[:2])*60 + int(t[3:]).
2. Sort the minutes.
3. min_diff = (first + 1440) - last (wrap-around).
4. For i in 1..n-1: min_diff = min(min_diff, sorted[i] - sorted[i-1]).
5. Return min_diff.

Edge Cases:
- Duplicate times: return 0.
- Only 2 times: simple.
- Wrap-around: 23:59 and 00:00 -> 1 minute.

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| Sort+scan| O(nlogn| O(n)   |
|          | )      |        |
| Bucket   | O(n+144| O(1440)|
|          | 0)     |        |
| Brute    | O(n^2) | O(n)   |
+----------+--------+--------+

KEY TRICK:
After sort, consecutive differences capture all pairs. Plus wrap-around
for cyclic distance.

RELATED PROBLEMS:
- Car Pooling (LC 1094): time-based interval scheduling.
- Teemo Attacking (LC 495): time intervals with duration.
- Maximum Population Year (LC 1854): similar time tracking.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Sort+scan (BEST)", findMinDifference_1),
        ("Way 2: Sort+linear verbose", findMinDifference_2),
        ("Way 3: Bucket sort", findMinDifference_3),
        ("Way 4: Brute force", findMinDifference_4),
        ("Way 5: Sort+zip", findMinDifference_5),
        ("Way 6: Set+sorted", findMinDifference_6),
        ("Way 7: Numpy", findMinDifference_7),
        ("Way 8: Reduce", findMinDifference_8),
        ("Way 9: Class OOP", findMinDifference_9),
        ("Way 10: Itertools pairwise", findMinDifference_10),
        ("Way 11: Sort+manual", findMinDifference_11),
        ("Way 12: Zip unpack", findMinDifference_12),
        ("Way 13: Generator", findMinDifference_13),
        ("Way 14: Enumerate", findMinDifference_14),
        ("Way 15: Sorted with key", findMinDifference_15),
        ("Way 16: Filter+early", findMinDifference_16),
        ("Way 17: Lambda map", findMinDifference_17),
        ("Way 18: Slice min", findMinDifference_18),
        ("Way 19: Recursive", findMinDifference_19),
        ("Way 20: Final cleanest", findMinDifference_20),
    ]

    test_cases = [
        # (timePoints, expected)
        (["23:59", "00:00"], 1),
        (["00:00", "04:00", "22:00"], 120),
        (["23:59", "00:00", "12:34"], 1),
        (["00:00", "00:00"], 0),  # duplicates
        (["01:01", "02:02", "03:03"], 61),  # 01:01->02:02 = 61, 02:02->03:03 = 61, wrap = 01:01+1440-03:03 = 1438. min = 61.
        (["00:00", "12:00"], 720),  # wrap = 720. min = 720.
        (["01:00", "02:00", "03:00"], 60),  # wrap = 01:00+1440 - 03:00 = 22*60 = 1320. min = 60.
        (["12:00", "23:59", "00:00"], 1),  # sorted: [0, 720, 1439]. min = 720, 719, wrap = 1440-1439 = 1. min = 1.
        (["05:31", "22:08", "00:35"], 147),  # 05:31 = 331, 22:08 = 1328, 00:35 = 35. Sorted: [35, 331, 1328]. Diff = 296, 997, wrap = 35+1440-1328 = 147. min = 147.
        (["00:00", "23:59", "12:00"], 1),  # sorted: [0, 720, 1439]. Diff = 720, 719, wrap = 0+1440-1439 = 1. min = 1.
        (["01:00", "01:00"], 0),  # duplicates
    ]

    print("=" * 70)
    print("MINIMUM TIME DIFFERENCE - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-time-difference")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for tp, expected in test_cases:
            try:
                result = func(tp[:])
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: timePoints={tp}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
