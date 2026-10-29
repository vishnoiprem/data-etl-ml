"""
Car Fleet
Medium | 30 min

There are n cars going to the same destination at target miles.
Each car i has:
- position[i]: starting position (miles along road)
- speed[i]: speed (mph)

A car CANNOT pass another car ahead. When a faster car catches up to
a slower car ahead, it becomes part of that fleet (moves at slower speed).

A fleet is a group of one or more cars driving at the speed of the slowest
car in front.

Return the number of fleets that will arrive at the destination.

Examples:
    target = 12, position = [10,8,0,5,3], speed = [2,4,1,1,3]
        -> 3
        Explanation:
            Car at 10 (speed 2): time = (12-10)/2 = 1
            Car at 8 (speed 4): time = (12-8)/4 = 1
            Car at 5 (speed 1): time = (12-5)/1 = 7
            Car at 3 (speed 3): time = (12-3)/3 = 3
            Car at 0 (speed 1): time = (12-0)/1 = 12
        Sorted by position: 0(12), 3(3), 5(7), 8(1), 10(1)
        Time to target: 12, 3, 7, 1, 1
        From end:
            10: time=1, fleets=1
            8: time=1, would catch up to 10? Yes (same time). Merge. fleets=1
            5: time=7, slower than 8 (1)? No. New fleet. fleets=2
            3: time=3, slower than 5 (7)? Yes (3 < 7). Merge. fleets=2
            0: time=12, slower than 3 (3)? No. New fleet. fleets=3

    target = 10, position = [3], speed = [3]   -> 1
    target = 100, position = [0,2,4], speed = [4,2,1]  -> 1
        Car 0: time = 100/4 = 25
        Car 1: time = 98/2 = 49
        Car 2: time = 96/1 = 96
        All in one fleet - slowest is 96, all others arrive earlier.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/car-fleet

Constraints:
- n == position.length == speed.length
- 1 <= n <= 10^5
- 0 < target <= 10^6
- 0 <= position[i] < target
- 0 < speed[i] <= 10^6
- All values are integers
"""


# =============================================================================
# WAY 1: Sort by position descending + monotonic stack on time (BEST - Memorize!)
# =============================================================================
def car_fleet_1(target, position, speed):
    # Pair: (position, time_to_target)
    cars = sorted(zip(position, speed), reverse=True)
    # Compute time to target: (target - pos) / speed
    # Process from closest to target to farthest
    stack = []  # Stack of times
    for pos, spd in cars:
        time = (target - pos) / spd
        # If this car arrives before or AT the same time as a car ahead,
        # it merges into that fleet.
        # If stack is empty OR this time > top of stack, new fleet.
        if not stack or time > stack[-1]:
            stack.append(time)
    return len(stack)


# =============================================================================
# WAY 2: Sort by position descending, count fleets
# =============================================================================
def car_fleet_2(target, position, speed):
    pairs = sorted(zip(position, speed), reverse=True)
    fleets = 0
    slowest = 0.0
    for pos, spd in pairs:
        time = (target - pos) / spd
        if time > slowest:
            fleets += 1
            slowest = time
    return fleets


# =============================================================================
# WAY 3: Sort by position ascending + reverse iterate
# =============================================================================
def car_fleet_3(target, position, speed):
    pairs = sorted(zip(position, speed))  # ascending
    fleets = 0
    slowest = 0.0
    # Process from right (closest to target) to left
    for pos, spd in reversed(pairs):
        time = (target - pos) / spd
        if time > slowest:
            fleets += 1
            slowest = time
    return fleets


# =============================================================================
# WAY 4: With explicit sort key
# =============================================================================
def car_fleet_4(target, position, speed):
    pairs = sorted(zip(position, speed), key=lambda x: -x[0])
    fleets = 0
    max_time = 0.0
    for pos, spd in pairs:
        t = (target - pos) / spd
        if t > max_time:
            fleets += 1
            max_time = t
    return fleets


# =============================================================================
# WAY 5: Using heap (no real benefit, but for understanding)
# =============================================================================
def car_fleet_5(target, position, speed):
    import heapq
    # Max-heap of (position, time) - process closest first
    max_heap = []
    for i in range(len(position)):
        time = (target - position[i]) / speed[i]
        # Use negative position for max-heap
        heapq.heappush(max_heap, (-position[i], time))
    fleets = 0
    slowest = 0.0
    while max_heap:
        _, time = heapq.heappop(max_heap)
        if time > slowest:
            fleets += 1
            slowest = time
    return fleets


# =============================================================================
# WAY 6: Compute times as list, sort by position
# =============================================================================
def car_fleet_6(target, position, speed):
    n = len(position)
    times = [0.0] * n
    sorted_pos = sorted(enumerate(position), key=lambda x: -x[1])  # (orig_idx, pos)
    for orig_idx, pos in sorted_pos:
        times[orig_idx] = (target - pos) / speed[orig_idx]
    fleets = 0
    slowest = 0.0
    for orig_idx, _ in sorted_pos:
        if times[orig_idx] > slowest:
            fleets += 1
            slowest = times[orig_idx]
    return fleets


# =============================================================================
# WAY 7: Most concise
# =============================================================================
def car_fleet_7(target, position, speed):
    sorted_pairs = sorted(zip(position, speed), reverse=True)
    fleets = 0
    slowest = 0.0
    for p, s in sorted_pairs:
        t = (target - p) / s
        if t > slowest:
            fleets += 1
            slowest = t
    return fleets


# =============================================================================
# WAY 8: With explicit fraction (avoid floating point)
# =============================================================================
def car_fleet_8(target, position, speed):
    from fractions import Fraction
    pairs = sorted(zip(position, speed), reverse=True)
    fleets = 0
    slowest = Fraction(0)
    for p, s in pairs:
        t = Fraction(target - p, s)
        if t > slowest:
            fleets += 1
            slowest = t
    return fleets


# =============================================================================
# WAY 9: Group by index, sort by -position
# =============================================================================
def car_fleet_9(target, position, speed):
    cars = sorted(range(len(position)), key=lambda i: -position[i])
    fleets = 0
    slowest = 0.0
    for i in cars:
        t = (target - position[i]) / speed[i]
        if t > slowest:
            fleets += 1
            slowest = t
    return fleets


# =============================================================================
# WAY 10: Using numpy (for completeness, not interview)
# =============================================================================
def car_fleet_10(target, position, speed):
    import numpy as np
    pos = np.array(position)
    spd = np.array(speed)
    times = (target - pos) / spd
    # Sort indices by position descending
    order = np.argsort(-pos)
    fleets = 0
    slowest = 0.0
    for i in order:
        if times[i] > slowest:
            fleets += 1
            slowest = times[i]
    return fleets


# =============================================================================
# WAY 11: With stack (using list)
# =============================================================================
def car_fleet_11(target, position, speed):
    pairs = sorted(zip(position, speed), reverse=True)
    stack = []
    for p, s in pairs:
        t = (target - p) / s
        if not stack or t > stack[-1]:
            stack.append(t)
    return len(stack)


# =============================================================================
# WAY 12: Tuple-based approach
# =============================================================================
def car_fleet_12(target, position, speed):
    pairs = sorted(zip(position, speed), reverse=True)
    fleet_times = []
    for p, s in pairs:
        t = (target - p) / s
        if not fleet_times or t > fleet_times[-1]:
            fleet_times.append(t)
    return len(fleet_times)


# =============================================================================
# WAY 13: Group sort
# =============================================================================
def car_fleet_13(target, position, speed):
    # Same logic, different style
    cars = list(zip(position, speed))
    cars.sort(key=lambda x: -x[0])
    fleets = 0
    prev_time = 0.0
    for pos, spd in cars:
        time = (target - pos) / spd
        if time > prev_time:
            fleets += 1
            prev_time = time
    return fleets


# =============================================================================
# WAY 14: Most elegant (Way 1 with reversed sort)
# =============================================================================
def car_fleet_14(target, position, speed):
    pairs = sorted(zip(position, speed), key=lambda x: x[0], reverse=True)
    stack = []
    for p, s in pairs:
        t = (target - p) / s
        if not stack or t > stack[-1]:
            stack.append(t)
    return len(stack)


# =============================================================================
# WAY 15: Sort by position descending using reverse=True on the sort
# =============================================================================
def car_fleet_15(target, position, speed):
    # Sort by position descending
    pairs = sorted(zip(position, speed))[::-1]
    fleets = 0
    slowest = 0.0
    for p, s in pairs:
        t = (target - p) / s
        if t > slowest:
            fleets += 1
            slowest = t
    return fleets


# =============================================================================
# WAY 16: Using deque
# =============================================================================
def car_fleet_16(target, position, speed):
    from collections import deque
    pairs = sorted(zip(position, speed), reverse=True)
    q = deque()
    for p, s in pairs:
        t = (target - p) / s
        if not q or t > q[-1]:
            q.append(t)
    return len(q)


# =============================================================================
# WAY 17: Count the number of "lead changes"
# =============================================================================
def car_fleet_17(target, position, speed):
    pairs = sorted(zip(position, speed), reverse=True)
    count = 0
    cur_max = 0.0
    for p, s in pairs:
        time = (target - p) / s
        if time > cur_max:
            count += 1
            cur_max = time
    return count


# =============================================================================
# WAY 18: Using negative positions for max heap
# =============================================================================
def car_fleet_18(target, position, speed):
    import heapq
    heap = []
    for i in range(len(position)):
        heapq.heappush(heap, (-position[i], speed[i]))
    fleets = 0
    slowest = 0.0
    while heap:
        neg_pos, s = heapq.heappop(heap)
        t = (target + neg_pos) / s  # since neg_pos = -position
        if t > slowest:
            fleets += 1
            slowest = t
    return fleets


# =============================================================================
# WAY 19: Class-based
# =============================================================================
class CarFleetCounter:
    def __init__(self, target):
        self.target = target
        self.fleets = 0
        self.slowest = 0.0

    def add(self, position, speed):
        time = (self.target - position) / speed
        if time > self.slowest:
            self.fleets += 1
            self.slowest = time


def car_fleet_19(target, position, speed):
    pairs = sorted(zip(position, speed), reverse=True)
    counter = CarFleetCounter(target)
    for p, s in pairs:
        counter.add(p, s)
    return counter.fleets


# =============================================================================
# WAY 20: Final cleanest
# =============================================================================
def car_fleet_20(target, position, speed):
    pairs = sorted(zip(position, speed), reverse=True)
    fleets = 0
    slowest = 0.0
    for p, s in pairs:
        time = (target - p) / s
        if time > slowest:
            fleets += 1
            slowest = time
    return fleets


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"There are n cars going to the same destination. Each car has a
position and speed. Cars can't pass each other - if a faster car
catches a slower one ahead, they merge into a fleet."

Key Insight:
"For each car, compute TIME TO TARGET = (target - position) / speed.
Sort cars by position DESCENDING (closest to target first).
Process: a car STARTS a new fleet iff its time > slowest_time seen so far.
If time <= slowest_time, it merges into a fleet ahead."

Algorithm:
"1. Pair position and speed, sort descending by position
2. Initialize fleets = 0, slowest = 0
3. For each (pos, spd):
   - time = (target - pos) / spd
   - If time > slowest: new fleet, update slowest = time
4. Return fleets"

Why this works:
"The car CLOSEST to target can never merge behind (no one ahead).
When we see a new car, if it takes MORE time than slowest seen,
it can't catch up - it forms its own fleet.
If it takes LESS OR EQUAL time, it WILL catch up to the fleet ahead."

Note: equal times = same fleet (catch up exactly at target).

Edge cases:
- Single car: 1 fleet
- All same position, same speed: 1 fleet each? No, all merge since same time.
- Sorted by position descending avoids re-scanning

COMPLEXITY:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Sort+iter | O(nlogn) | O(n)|
| Heap      | O(nlogn) | O(n)|
+-----------+--------+--------+
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Stack on time", car_fleet_1),
        ("Way 2: Sort desc, count", car_fleet_2),
        ("Way 3: Sort asc, reverse", car_fleet_3),
        ("Way 4: Sort key", car_fleet_4),
        ("Way 5: Heap", car_fleet_5),
        ("Way 6: Compute times list", car_fleet_6),
        ("Way 7: Most concise", car_fleet_7),
        ("Way 8: Fractions", car_fleet_8),
        ("Way 9: Sort indices", car_fleet_9),
        ("Way 10: Numpy", car_fleet_10),
        ("Way 11: Stack list", car_fleet_11),
        ("Way 12: Tuple approach", car_fleet_12),
        ("Way 13: Group sort", car_fleet_13),
        ("Way 14: Most elegant", car_fleet_14),
        ("Way 15: Reverse slice", car_fleet_15),
        ("Way 16: Deque", car_fleet_16),
        ("Way 17: Lead changes", car_fleet_17),
        ("Way 18: Max heap", car_fleet_18),
        ("Way 19: Class", car_fleet_19),
        ("Way 20: Final cleanest", car_fleet_20),
    ]

    test_cases = [
        (12, [10, 8, 0, 5, 3], [2, 4, 1, 1, 3], 3),
        (10, [3], [3], 1),
        (100, [0, 2, 4], [4, 2, 1], 1),
        (10, [0, 4, 6], [2, 1, 3], 2),
        # Trace: target=10
        # 6, spd 3: time = (10-6)/3 = 4/3
        # 4, spd 1: time = 6/1 = 6. 6 > 4/3, new fleet. slow=6
        # 0, spd 2: time = 10/2 = 5. 5 < 6, merges. fleets=2
        # Result: 2
        (10, [6, 4, 0], [3, 1, 2], 2),
        (20, [6, 2, 15], [3, 4, 1], 2),
        # 15, spd 1: time = 5
        # 6, spd 3: time = 14/3 ≈ 4.67. < 5, merges
        # 2, spd 4: time = 18/4 = 4.5. < 5, merges
        # Hmm all merge into 1 fleet
        # Let me reconsider:
        # 15 -> 5
        # 6 -> 4.67 < 5, merges with 15
        # 2 -> 4.5 < 5, merges with 15
        # So 1 fleet
        # Expected: 1
        (5, [2, 0], [1, 4], 1),
        # 2 -> 3, 0 -> 1.25 < 3, merges. 1 fleet
    ]

    # Simple test cases
    test_cases = [
        (12, [10, 8, 0, 5, 3], [2, 4, 1, 1, 3], 3),
        (10, [3], [3], 1),
        (100, [0, 2, 4], [4, 2, 1], 1),
        (10, [0, 4, 6], [2, 1, 3], 2),
        (10, [6, 2, 15], [3, 1, 4], 1),
        # 15 -> (10)/4 = -1.25? No target=10, position=15 > target. Skip?
        # Actually position must be < target.
        # Let me adjust
        (10, [6, 2, 9], [3, 1, 4], 1),
        # 9 -> 1/4 = 0.25
        # 6 -> 4/3 ≈ 1.33 > 0.25, new fleet. slow = 1.33
        # 2 -> 8/1 = 8 > 1.33, new fleet. slow = 8
        # Result: 2
        # Hmm let me re-trace
        # (target=10, pos=9, spd=4): time = (10-9)/4 = 0.25
        # (target=10, pos=6, spd=3): time = (10-6)/3 = 1.333
        # (target=10, pos=2, spd=1): time = (10-2)/1 = 8
        # Sort by position desc: (9,4):0.25, (6,3):1.33, (2,1):8
        # Process:
        # slow=0
        # (9,4): 0.25 > 0, new fleet. slow=0.25. fleets=1
        # (6,3): 1.33 > 0.25, new fleet. slow=1.33. fleets=2
        # (2,1): 8 > 1.33, new fleet. slow=8. fleets=3
        # Result: 3 fleets
    ]

    test_cases = [
        (12, [10, 8, 0, 5, 3], [2, 4, 1, 1, 3], 3),
        (10, [3], [3], 1),
        (100, [0, 2, 4], [4, 2, 1], 1),
        (10, [0, 4, 6], [2, 1, 3], 2),
        (10, [6, 2, 9], [3, 1, 4], 3),
    ]

    print("=" * 70)
    print("CAR FLEET - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/car-fleet")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for target, pos, spd, expected in test_cases:
            try:
                result = func(target, pos, spd)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: target={target}, pos={pos}, spd={spd} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on target={target} - {e}")
        print(f"  {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
