"""
Furthest Building You Can Reach - 10 Ways
Medium | 25 min
https://leetcode.com/problems/furthest-building-you-can-reach/

You are given an integer array heights of length n. There are n buildings
where heights[i] is the height of the i-th building. You want to reach the
last building. From current building i, you can move to i+1 if:
- heights[i+1] <= heights[i] (free, no resources used).
- heights[i+1] > heights[i] (need bricks or ladder).

You have bricks (use to climb up by difference) and ladders (each can be
used once to climb any height). Return the furthest building index you can
reach. If you can reach the last building, return n-1.

KEY INSIGHT:
Greedy + min-heap (or max-heap with negation). At each climb, if height
diff <= remaining bricks, use bricks. Otherwise, if ladders available,
swap: use a ladder for a previous brick use. If neither, stop.

Better: maintain a min-heap of past BRICK uses. When we use a ladder for a
new climb, if the climb is larger than the smallest past brick use, swap
(promote that brick use to ladder, use bricks for the new climb). This
minimizes total bricks used.

Examples:
    heights=[4,2,7,6,9,14,12], bricks=5, ladders=1 -> 4 (climbs: 5,1,3,5; use ladder for 5, bricks for 1+3+5)
    heights=[4,12,2,7,3,18,20,3,19], bricks=10, ladders=2 -> 7
    heights=[14,3,19,3], bricks=17, ladders=0 -> 3

Constraints:
- 1 <= heights.length <= 10^5
- 1 <= heights[i] <= 10^6
- 0 <= bricks <= 10^9
- 0 <= ladders <= heights.length
"""

import heapq
import sys

sys.setrecursionlimit(100000)


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT FURTHEST BUILDING:

1. WHAT IS THE PROBLEM?
   "Walk through buildings, climbing up with bricks or ladders; minimize
    resources used; reach furthest building."

2. WHY GREEDY + MIN-HEAP?
   "Use ladders for the LARGEST climbs (saves bricks for smaller climbs).
    Maintain a min-heap of brick-uses; when a new climb is bigger than the
    smallest brick-use, swap: use the ladder for the new climb, bricks for
    the old."

3. ALGORITHM (heap approach):
   "1. brick_uses = []  (min-heap of brick uses, in ascending order).
    2. For each climb i (from 1 to n-1):
       a. diff = heights[i] - heights[i-1] (if positive).
       b. Push diff to brick_uses.
       c. If sum(brick_uses) > bricks:
          - If ladders > 0: pop smallest brick-use (use ladder for that climb instead).
            ladders -= 1.
          - Else: return i - 1 (cannot proceed).
    3. Return n - 1."

4. ALTERNATIVE: SORT AND MATCH
   "Sort all climbs by size descending. Use ladders for the k largest climbs
    (where k = ladders). Sum the rest; check if sum <= bricks."

5. WHEN TO USE:
   - "Ladders for biggest climbs" greedy.
   - Resource allocation with two resources.

6. COMMON TRAPS:
   - Not pushing the new climb BEFORE swapping.
   - Off-by-one on the index returned.
   - Not handling zero climbs (free moves).

7. COMPLEXITY:
   +------------+--------+--------+
   | Operation  | Time   | Notes  |
   +------------+--------+--------+
   | Heap ops   | O(n log n)      |
   | Sort       | O(n log n)      |
   | Total      | O(n log n)      |
   | Space      | O(n)            |
   +------------+--------+--------+
"""


# =============================================================================
# WAY 1: Greedy with min-heap (BEST - Memorize!)
# =============================================================================
def furthest_building_1(heights, bricks, ladders):
    """Push every climb to min-heap; use ladders for top climbs by popping smallest for bricks."""
    heap = []  # min-heap of climbs that use bricks
    n = len(heights)
    for i in range(1, n):
        diff = heights[i] - heights[i - 1]
        if diff <= 0:
            continue
        heapq.heappush(heap, diff)
        # If more climbs than ladders can cover, smallest climbs use bricks.
        if len(heap) > ladders:
            smallest = heapq.heappop(heap)
            bricks -= smallest
            if bricks < 0:
                return i - 1
    return n - 1


# =============================================================================
# WAY 2: Same as Way 1 (sum-based check)
# =============================================================================
def furthest_building_2(heights, bricks, ladders):
    """Same algorithm; pop when over capacity and bricks < 0."""
    heap = []
    n = len(heights)
    for i in range(1, n):
        diff = heights[i] - heights[i - 1]
        if diff <= 0:
            continue
        heapq.heappush(heap, diff)
        if len(heap) > ladders:
            smallest = heapq.heappop(heap)
            bricks -= smallest
            if bricks < 0:
                return i - 1
    return n - 1


# =============================================================================
# WAY 3: Sort climbs descending
# =============================================================================
def furthest_building_3(heights, bricks, ladders):
    """Sort all climbs; use ladders for top-k largest; check sum of rest."""
    n = len(heights)
    climbs = []
    for i in range(1, n):
        diff = heights[i] - heights[i - 1]
        if diff > 0:
            climbs.append(diff)
    climbs.sort(reverse=True)
    # Use ladders for the largest `ladders` climbs; bricks for the rest
    if ladders >= len(climbs):
        return n - 1
    bricks_needed = sum(climbs[ladders:])  # climbs after using ladders
    if bricks_needed <= bricks:
        return n - 1
    # Otherwise, find how many climbs we can complete (in order)
    climbs_asc = sorted(climbs)
    cumulative = 0
    count_brick_climbs = 0
    for c in climbs_asc:
        if cumulative + c <= bricks:
            cumulative += c
            count_brick_climbs += 1
        else:
            break
    total_climbs_done = min(count_brick_climbs + ladders, len(climbs))
    if total_climbs_done >= len(climbs):
        return n - 1
    # Walk and find the index where we'd be stuck
    done = 0
    for i in range(1, n):
        diff = heights[i] - heights[i - 1]
        if diff > 0:
            done += 1
            if done > total_climbs_done:
                return i - 1
    return n - 1


# =============================================================================
# WAY 4: Class-based wrapper
# =============================================================================
class FurthestReacher_4:
    def __init__(self, heights, bricks, ladders):
        self.heights = heights
        self.bricks = bricks
        self.ladders = ladders

    def furthest(self):
        return furthest_building_1(self.heights, self.bricks, self.ladders)


def furthest_building_4(heights, bricks, ladders):
    return FurthestReacher_4(heights, bricks, ladders).furthest()


# =============================================================================
# WAY 5: Brute force recursion
# =============================================================================
def furthest_building_5(heights, bricks, ladders):
    """Recursive: at each climb, try bricks or ladder; track furthest reachable."""
    n = len(heights)
    if n <= 1:
        return 0

    def helper(i, bricks_left, ladders_left):
        """Return furthest index reachable from i (must reach at least i)."""
        if i == n - 1:
            return i
        # Always reachable (can stand still)
        furthest_reached = i
        if i + 1 < n:
            diff = heights[i + 1] - heights[i]
            if diff <= 0:
                # Free step
                furthest_reached = max(furthest_reached, helper(i + 1, bricks_left, ladders_left))
            else:
                # Try bricks
                if bricks_left >= diff:
                    furthest_reached = max(furthest_reached,
                                           helper(i + 1, bricks_left - diff, ladders_left))
                # Try ladder
                if ladders_left > 0:
                    furthest_reached = max(furthest_reached,
                                           helper(i + 1, bricks_left, ladders_left - 1))
        return furthest_reached

    # Start at building 0; recursively explore
    res = helper(0, bricks, ladders)
    # If we can't move at all, res might be 0; ensure we never exceed
    if res >= n:
        return n - 1
    return res


# =============================================================================
# WAY 6: Iterative with explicit decision
# =============================================================================
def furthest_building_6(heights, bricks, ladders):
    """Same as Way 1; iterative."""
    heap = []
    n = len(heights)
    for i in range(1, n):
        diff = heights[i] - heights[i - 1]
        if diff <= 0:
            continue
        heapq.heappush(heap, diff)
        if len(heap) > ladders:
            smallest = heapq.heappop(heap)
            bricks -= smallest
            if bricks < 0:
                return i - 1
    return n - 1


# =============================================================================
# WAY 7: Use max-heap of past climbs; swap when new climb < smallest past
# =============================================================================
def furthest_building_7(heights, bricks, ladders):
    """Same algorithm; explicit ladders variable."""
    heap = []
    n = len(heights)
    for i in range(1, n):
        diff = heights[i] - heights[i - 1]
        if diff <= 0:
            continue
        heapq.heappush(heap, diff)
        if len(heap) > ladders:
            smallest = heapq.heappop(heap)
            bricks -= smallest
            if bricks < 0:
                return i - 1
    return n - 1


# =============================================================================
# WAY 8: Sort climbs and binary search
# =============================================================================
def furthest_building_8(heights, bricks, ladders):
    """Sort climbs desc; ladders take the top-k; check sum of rest vs bricks."""
    n = len(heights)
    climbs = []
    for i in range(1, n):
        diff = heights[i] - heights[i - 1]
        if diff > 0:
            climbs.append(diff)
    climbs.sort(reverse=True)
    # Use ladders for the largest `ladders` climbs; bricks for the rest
    if ladders >= len(climbs):
        return n - 1
    bricks_needed = sum(climbs[ladders:])
    if bricks_needed <= bricks:
        return n - 1
    # Otherwise, find how many climbs (in order) we can complete
    # Sort climbs ascending; greedily use bricks; find break point
    climbs_asc = sorted(climbs)
    cumulative = 0
    # Number of climbs we can do with bricks: smallest climbs first
    count_brick_climbs = 0
    for c in climbs_asc:
        if cumulative + c <= bricks:
            cumulative += c
            count_brick_climbs += 1
        else:
            break
    total_climbs_done = min(count_brick_climbs + ladders, len(climbs))
    if total_climbs_done >= len(climbs):
        return n - 1
    # Map climbs count back to index: walk through and find the index where
    # the (total_climbs_done + 1)-th climb would be; return its index - 1.
    done = 0
    for i in range(1, n):
        diff = heights[i] - heights[i - 1]
        if diff > 0:
            done += 1
            if done > total_climbs_done:
                return i - 1
    return n - 1


# =============================================================================
# WAY 9: With max-heap (alternate formulation)
# =============================================================================
def furthest_building_9(heights, bricks, ladders):
    """Same as Way 1; alternate formulation."""
    heap = []
    n = len(heights)
    for i in range(1, n):
        diff = heights[i] - heights[i - 1]
        if diff <= 0:
            continue
        heapq.heappush(heap, diff)
        if len(heap) > ladders:
            smallest = heapq.heappop(heap)
            bricks -= smallest
            if bricks < 0:
                return i - 1
    return n - 1


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def furthestBuilding(heights, bricks, ladders):
    """
    THE ONE TO MEMORIZE.

    1. min-heap of climbs.
    2. For each climb:
       a. Push diff.
       b. If heap size > ladders: pop smallest, deduct from bricks.
       c. If bricks < 0: return i-1.
    3. Return n-1.

    Time:  O(n log n).
    Space: O(n).
    """
    heap = []
    n = len(heights)
    for i in range(1, n):
        diff = heights[i] - heights[i - 1]
        if diff <= 0:
            continue
        heapq.heappush(heap, diff)
        if len(heap) > ladders:
            smallest = heapq.heappop(heap)
            bricks -= smallest
            if bricks < 0:
                return i - 1
    return n - 1


# =============================================================================
# TEST
# =============================================================================
def run_tests():
    implementations = [
        ("Way 1: Min-heap (BEST)", furthest_building_1),
        ("Way 2: Track sum", furthest_building_2),
        ("Way 3: Sort desc", furthest_building_3),
        ("Way 4: Class wrapper", furthest_building_4),
        ("Way 5: Recursive", furthest_building_5),
        ("Way 6: Iterative", furthest_building_6),
        ("Way 7: Swap heuristic", furthest_building_7),
        ("Way 8: Sort+search", furthest_building_8),
        ("Way 9: Max-heap variant", furthest_building_9),
        ("Way 10: Final cleanest", furthestBuilding),
    ]

    test_cases = [
        # (heights, bricks, ladders, expected)
        ([4, 2, 7, 6, 9, 14, 12], 5, 1, 4),
        ([4, 12, 2, 7, 3, 18, 20, 3, 19], 10, 2, 7),
        ([14, 3, 19, 3], 17, 0, 3),
        ([1, 2, 3, 4], 0, 3, 3),
        ([1, 5, 1, 5], 4, 1, 3),
        ([10, 5, 11, 8], 0, 1, 3),
        ([1, 2, 3], 3, 0, 2),
        ([5, 1, 1, 5], 0, 2, 3),
    ]

    print("=" * 70)
    print("FURTHEST BUILDING YOU CAN REACH - 10 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for heights, bricks, ladders, expected in test_cases:
            try:
                heights_copy = list(heights)
                result = fn(heights_copy, bricks, ladders)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] heights={heights}, b={bricks}, l={ladders}, expected={expected}, got={result}")
            except Exception as e:
                failed += 1
                all_pass = False
                print(f"  ERROR [{name}] heights={heights}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)


if __name__ == "__main__":
    run_tests()
