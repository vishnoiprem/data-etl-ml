"""
Minimum Cost to Connect Sticks - 10 Ways
Medium | 20 min
https://leetcode.com/problems/minimum-cost-to-connect-sticks/

You have some number of sticks of positive lengths. You can connect any two
sticks with cost equal to the sum of their lengths; the resulting stick has
length equal to that sum. Find the minimum total cost to connect all sticks
into one stick.

KEY INSIGHT:
Greedy + min-heap. Always connect the two SHORTEST sticks first (Huffman-like).
Why? Because the shortest sticks contribute least to future costs. This is
exactly the Huffman tree / optimal merge pattern problem.

Examples:
    sticks=[2,4,3] -> 14
      (2,3)=5; [5,4]; (4,5)=9; total = 5+9 = 14
    sticks=[1,8,3,5] -> 30
      (1,3)=4; [8,5,4] -> (4,5)=9; [8,9] -> (8,9)=17; total = 4+9+17 = 30
    sticks=[5] -> 0
    sticks=[] -> 0

Constraints:
- 1 <= sticks.length <= 10^4
- 0 <= sticks[i] <= 10^4
"""

import heapq
import sys

sys.setrecursionlimit(100000)


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT MINIMUM COST TO CONNECT STICKS:

1. WHAT IS THE PROBLEM?
   "Combine sticks in pairs; each combination costs the sum. Find minimum total."

2. WHY GREEDY (MIN-HEAP)?
   "Combining two short sticks first means their sum stays small in future
   combinations. This is exactly Huffman coding / optimal merge pattern.
   A min-heap gives us the two smallest sticks in O(log n) each step."

3. ALGORITHM:
   "1. heapify sticks (min-heap).
    2. total = 0.
    3. While heap has 2+ elements:
       a. a = heappop(heap)
       b. b = heappop(heap)
       c. total += a + b
       d. heappush(heap, a + b)
    4. Return total."

4. EDGE CASES:
   - 0 or 1 sticks: cost is 0.
   - All same length: simple.
   - One huge stick + many tiny: tiny ones get merged first.

5. WHEN TO USE:
   - Optimal merge pattern.
   - Huffman-like tree construction.
   - File merging with cost = sum.
   - Any "minimize sum" pairwise combination problem.

6. COMMON TRAPS:
   - Using max-heap or no heap (sort each iteration O(n^2)).
   - Forgetting to push the combined stick back.
   - Not handling empty/single-stick cases.

7. COMPLEXITY:
   +------------+--------+--------+
   | Operation  | Time   | Notes  |
   +------------+--------+--------+
   | heapify    | O(n)            |
   | Each step  | O(log n)        |
   | n-1 steps  | O(n log n)      |
   | Space      | O(n)            |
   +------------+--------+--------+
"""


# =============================================================================
# WAY 1: Min-heap greedy (BEST - Memorize!)
# =============================================================================
def connect_sticks_1(sticks):
    """Greedy: always combine two smallest sticks."""
    if len(sticks) < 2:
        return 0
    heapq.heapify(sticks)
    total = 0
    while len(sticks) > 1:
        a = heapq.heappop(sticks)
        b = heapq.heappop(sticks)
        s = a + b
        total += s
        heapq.heappush(sticks, s)
    return total


# =============================================================================
# WAY 2: Same with heapreplace optimization
# =============================================================================
def connect_sticks_2(sticks):
    if len(sticks) < 2:
        return 0
    heapq.heapify(sticks)
    total = 0
    while len(sticks) > 1:
        a = heapq.heappop(sticks)
        b = heapq.heappop(sticks)
        total += a + b
        heapq.heappush(sticks, a + b)
    return total


# =============================================================================
# WAY 3: Sort each iteration (brute-ish)
# =============================================================================
def connect_sticks_3(sticks):
    if len(sticks) < 2:
        return 0
    arr = list(sticks)
    total = 0
    while len(arr) > 1:
        arr.sort()
        a = arr.pop(0)
        b = arr.pop(0)
        s = a + b
        total += s
        arr.append(s)
    return total


# =============================================================================
# WAY 4: Sort once and use two-pointer (similar to Huffman)
# =============================================================================
def connect_sticks_4(sticks):
    """Sort, then merge smallest. Less efficient."""
    if len(sticks) < 2:
        return 0
    arr = sorted(sticks)
    total = 0
    while len(arr) > 1:
        a = arr.pop(0)
        b = arr.pop(0)
        s = a + b
        total += s
        # Insert s back into sorted position
        import bisect
        bisect.insort(arr, s)
    return total


# =============================================================================
# WAY 5: Class-based wrapper
# =============================================================================
class StickConnector_5:
    def __init__(self, sticks):
        self.sticks = sticks

    def min_cost(self):
        return connect_sticks_1(self.sticks)


def connect_sticks_5(sticks):
    return StickConnector_5(sticks).min_cost()


# =============================================================================
# WAY 6: Recursive
# =============================================================================
def connect_sticks_6(sticks):
    """Recursive: pop two, combine, recurse."""
    if len(sticks) < 2:
        return 0

    def helper(heap):
        if len(heap) < 2:
            return 0
        a = heapq.heappop(heap)
        b = heapq.heappop(heap)
        s = a + b
        heapq.heappush(heap, s)
        return s + helper(heap)

    heapq.heapify(sticks)
    return helper(sticks)


# =============================================================================
# WAY 7: Use heapq.nsmallest instead of two pops
# =============================================================================
def connect_sticks_7(sticks):
    if len(sticks) < 2:
        return 0
    heapq.heapify(sticks)
    total = 0
    while len(sticks) > 1:
        two_smallest = heapq.nsmallest(2, sticks)
        a, b = two_smallest[0], two_smallest[1]
        # Remove them
        sticks.remove(a)
        sticks.remove(b)
        s = a + b
        total += s
        heapq.heappush(sticks, s)
    return total


# =============================================================================
# WAY 8: Using heapify repeatedly
# =============================================================================
def connect_sticks_8(sticks):
    if len(sticks) < 2:
        return 0
    arr = list(sticks)
    total = 0
    while len(arr) > 1:
        heapq.heapify(arr)
        a = heapq.heappop(arr)
        b = heapq.heappop(arr)
        s = a + b
        total += s
        arr.append(s)
    return total


# =============================================================================
# WAY 9: Maintain sorted list manually
# =============================================================================
def connect_sticks_9(sticks):
    """Manual sorted list (less efficient than heap)."""
    if len(sticks) < 2:
        return 0
    arr = sorted(sticks)
    total = 0
    while len(arr) > 1:
        a = arr.pop(0)
        b = arr.pop(0)
        s = a + b
        total += s
        # Manual insertion sort to maintain sorted order
        i = 0
        while i < len(arr) and arr[i] < s:
            i += 1
        arr.insert(i, s)
    return total


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def connectSticks(sticks):
    """
    THE ONE TO MEMORIZE.

    1. heapify sticks (min-heap).
    2. total = 0.
    3. While heap has 2+ elements:
       a, b = heappop, heappop
       total += a + b
       heappush(a + b)
    4. Return total.

    Time:  O(n log n).
    Space: O(n).
    """
    if len(sticks) < 2:
        return 0
    heapq.heapify(sticks)
    total = 0
    while len(sticks) > 1:
        a = heapq.heappop(sticks)
        b = heapq.heappop(sticks)
        total += a + b
        heapq.heappush(sticks, a + b)
    return total


# =============================================================================
# TEST
# =============================================================================
def run_tests():
    implementations = [
        ("Way 1: Min-heap greedy (BEST)", connect_sticks_1),
        ("Way 2: heapreplace", connect_sticks_2),
        ("Way 3: Sort each iter", connect_sticks_3),
        ("Way 4: Sort + bisect", connect_sticks_4),
        ("Way 5: Class wrapper", connect_sticks_5),
        ("Way 6: Recursive", connect_sticks_6),
        ("Way 7: nsmallest", connect_sticks_7),
        ("Way 8: heapify each", connect_sticks_8),
        ("Way 9: Manual sort", connect_sticks_9),
        ("Way 10: Final cleanest", connectSticks),
    ]

    test_cases = [
        ([], 0, "Empty"),
        ([5], 0, "Single"),
        ([2, 4, 3], 14, "Standard 3"),
        ([1, 8, 3, 5], 30, "Standard 4"),
        ([1, 2, 3, 4, 5], 33, "Sorted"),
        ([5, 5, 5, 5], 40, "All equal"),
        ([10, 1, 1, 1], 18, "Big + small"),
        ([2, 2, 2, 2, 2], 24, "5 equal"),
    ]

    print("=" * 70)
    print("MINIMUM COST TO CONNECT STICKS - 10 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for inp, expected, desc in test_cases:
            try:
                result = fn(list(inp))
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: input={inp}, expected={expected}, got={result}")
            except Exception as e:
                failed += 1
                all_pass = False
                print(f"  ERROR [{name}] {desc}: {e}")
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
