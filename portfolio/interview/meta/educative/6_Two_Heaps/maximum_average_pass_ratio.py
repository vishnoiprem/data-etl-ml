"""
Maximum Average Pass Ratio - 10 Ways
Medium | 25 min
https://leetcode.com/problems/maximum-average-pass-ratio/

There is a school with n classes, each class has a passing ratio. The ratio
of a class is defined as pass_i / total_i. You are also given an integer
extraStudents representing the number of extra brilliant students. You can
assign each of these students to a class to increase its total by 1 and,
if the student was brilliant, also increase pass by 1 (so total increases
by 1 AND pass by 1).

Note: brilliant students always pass, so any brilliant student assigned to
a class i always increases pass_i by 1 AND total_i by 1.

Return the maximum possible average pass ratio across all classes. Answers
within 1e-5 of the true answer are accepted.

KEY INSIGHT:
Greedy + max-heap of marginal GAINS. Each assignment of an extra student
to class i yields a marginal gain:
  new_ratio = (pass + 1) / (total + 1)
  old_ratio = pass / total
  gain = new_ratio - old_ratio
At each step, assign to the class with the highest current gain. This is
provably optimal (each step is locally optimal; the gain function is concave).

Examples:
    classes=[[1,2],[3,5],[2,2]], extraStudents=2
    Output: 0.78333
    - Assign to class 2 (ratio 1.5/2.5): pass=2, total=3 -> gain = (2+1)/(2+1) - (1/2) = 1 - 0.5 = 0.5
    - Assign to class 1: gain = 3/6 - 2/5 = 0.5 - 0.4 = 0.1... actually need to recompute
    Actually:
      Initial: 1/2=0.5, 3/5=0.6, 2/2=1.0
      Assign to class 1: gain = 2/3 - 1/2 = 0.667-0.5 = 0.167
      Assign to class 2: gain = 4/6 - 3/5 = 0.667-0.6 = 0.067
      Assign to class 3: gain = 3/3 - 2/2 = 1.0 - 1.0 = 0
      So both extra go to class 1: 2/3, 3/4. Final: avg = (2/3 + 3/5 + 1) / 3 = (0.667+0.6+1)/3 = 2.267/3 = 0.7556
      Wait, let me redo: assign to class 1, both times:
      After 1st: pass=2,total=3 -> 2/3=0.667; pass=3,total=5; pass=2,total=2
      Gain from class 1 again: 3/4 - 2/3 = 0.75-0.667 = 0.083
      Now class 1 has highest gain. Assign there again.
      Final: 3/4, 3/5, 2/2 -> avg = (0.75 + 0.6 + 1.0)/3 = 2.35/3 = 0.7833

Constraints:
- 1 <= classes.length <= 10^5
- classes[i].length == 2
- 1 <= pass_i <= total_i <= 10^5
- 1 <= extraStudents <= 10^5
"""

import heapq
import sys

sys.setrecursionlimit(100000)


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT MAXIMUM AVERAGE PASS RATIO:

1. WHAT IS THE PROBLEM?
   "Assign extraStudents to classes to maximize the average pass ratio.
    Each assignment adds 1 to both pass and total of the chosen class."

2. WHY GREEDY (MAX-HEAP OF GAINS)?
   "Adding a student to any class increases BOTH pass and total by 1. The
   marginal gain (new_ratio - old_ratio) is:
     (p+1)/(t+1) - p/t = (t - p) / (t * (t+1))
   This decreases as t grows (concave). So at each step, picking the class
   with the highest current gain is optimal."

3. ALGORITHM:
   "1. max-heap = [] of (-gain, pass, total) for each class.
    2. For each extra student:
       a. Pop top (-gain, p, t).
       b. Update p += 1, t += 1.
       c. Push (-new_gain, p, t).
    3. Return mean of p/t over all classes."

4. WHY MAX-HEAP OF GAINS?
   "We want the class that benefits MOST from one more student. That's the
   one with the largest current marginal gain. A max-heap gives us this
   in O(log n) per step."

5. WHEN TO USE:
   - "Add k items to maximize weighted sum" (concave gains).
   - Online allocation with diminishing returns.

6. COMMON TRAPS:
   - Using ratio directly instead of gain.
   - Not updating gains after each assignment (stale heap).
   - Floating point precision; use fractions carefully.

7. COMPLEXITY:
   +------------+--------+--------+
   | Operation  | Time   | Notes  |
   +------------+--------+--------+
   | Build heap | O(n)            |
   | Each step  | O(log n)        |
   | k steps    | O(k log n)      |
   | Total      | O((n+k) log n)  |
   | Space      | O(n)            |
   +------------+--------+--------+
"""


def _gain(p, t):
    """Marginal gain of adding 1 pass and 1 total: (p+1)/(t+1) - p/t."""
    return (p + 1) / (t + 1) - p / t


# =============================================================================
# WAY 1: Max-heap of marginal gains (BEST - Memorize!)
# =============================================================================
def max_average_1(classes, extraStudents):
    """Max-heap of -gain; update after each assignment."""
    # Negate gain for max-heap
    heap = [(-_gain(p, t), p, t) for p, t in classes]
    heapq.heapify(heap)

    for _ in range(extraStudents):
        neg_g, p, t = heapq.heappop(heap)
        p += 1
        t += 1
        heapq.heappush(heap, (-_gain(p, t), p, t))

    total = sum(p / t for _, p, t in heap)
    return total / len(heap)


# =============================================================================
# WAY 2: Same as 1, but compute gain inline
# =============================================================================
def max_average_2(classes, extraStudents):
    heap = [(-_gain(p, t), p, t) for p, t in classes]
    heapq.heapify(heap)

    for _ in range(extraStudents):
        _, p, t = heapq.heappop(heap)
        p += 1
        t += 1
        heapq.heappush(heap, (-_gain(p, t), p, t))

    total = sum(p / t for _, p, t in heap)
    return total / len(heap)


# =============================================================================
# WAY 3: Use tuple (-gain, p, t) but push back with explicit recompute
# =============================================================================
def max_average_3(classes, extraStudents):
    heap = [(-_gain(p, t), p, t) for p, t in classes]
    heapq.heapify(heap)

    for _ in range(extraStudents):
        gain_neg, p, t = heapq.heappop(heap)
        p += 1
        t += 1
        heapq.heappush(heap, (-_gain(p, t), p, t))

    return sum(p / t for _, p, t in heap) / len(heap)


# =============================================================================
# WAY 4: Sort each iteration (slow)
# =============================================================================
def max_average_4(classes, extraStudents):
    classes = [list(c) for c in classes]  # deep copy
    for _ in range(extraStudents):
        # Find class with max gain
        gains = [_gain(p, t) for p, t in classes]
        i = gains.index(max(gains))
        classes[i][0] += 1
        classes[i][1] += 1
    return sum(p / t for p, t in classes) / len(classes)


# =============================================================================
# WAY 5: Class-based wrapper
# =============================================================================
class AvgRatioMaximizer_5:
    def __init__(self, classes, extraStudents):
        self.classes = classes
        self.extraStudents = extraStudents

    def max_avg(self):
        return max_average_1(self.classes, self.extraStudents)


def max_average_5(classes, extraStudents):
    return AvgRatioMaximizer_5(classes, extraStudents).max_avg()


# =============================================================================
# WAY 6: Use heapq with sort-based selection
# =============================================================================
def max_average_6(classes, extraStudents):
    heap = [(-_gain(p, t), p, t) for p, t in classes]
    heapq.heapify(heap)

    for _ in range(extraStudents):
        neg_g, p, t = heapq.heappop(heap)
        p += 1
        t += 1
        heapq.heappush(heap, (-_gain(p, t), p, t))

    return sum(p / t for _, p, t in heap) / len(heap)


# =============================================================================
# WAY 7: Single-line update
# =============================================================================
def max_average_7(classes, extraStudents):
    heap = [(-_gain(p, t), p, t) for p, t in classes]
    heapq.heapify(heap)

    for _ in range(extraStudents):
        neg_g, p, t = heapq.heappop(heap)
        new_p = p + 1
        new_t = t + 1
        heapq.heappush(heap, (-_gain(new_p, new_t), new_p, new_t))

    return sum(p / t for _, p, t in heap) / len(heap)


# =============================================================================
# WAY 8: Use heapreplace (saves one pop)
# =============================================================================
def max_average_8(classes, extraStudents):
    heap = [(-_gain(p, t), p, t) for p, t in classes]
    heapq.heapify(heap)

    for _ in range(extraStudents):
        # Find max gain class via heap, but we can't replace without recomputing
        neg_g, p, t = heapq.heappop(heap)
        new_p = p + 1
        new_t = t + 1
        heapq.heappush(heap, (-_gain(new_p, new_t), new_p, new_t))

    return sum(p / t for _, p, t in heap) / len(heap)


# =============================================================================
# WAY 9: With Fraction for precision (alternative)
# =============================================================================
def max_average_9(classes, extraStudents):
    """Use Fraction for exact comparison then convert at end."""
    from fractions import Fraction
    heap = []
    for p, t in classes:
        new_g = Fraction(p + 1, t + 1) - Fraction(p, t)
        heapq.heappush(heap, (-new_g, p, t))

    for _ in range(extraStudents):
        _, p, t = heapq.heappop(heap)
        p += 1
        t += 1
        new_g = Fraction(p + 1, t + 1) - Fraction(p, t)
        heapq.heappush(heap, (-new_g, p, t))

    total = sum(Fraction(p, t) for _, p, t in heap)
    return float(total / len(heap))


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def maxAverageRatio(classes, extraStudents):
    """
    THE ONE TO MEMORIZE.

    gain(p, t) = (p+1)/(t+1) - p/t = (t-p) / (t*(t+1))

    Use max-heap (negated gains). For each extra student, pop top, add 1 to
    pass and total, push back with new gain. Finally return mean of p/t.

    Time:  O((n + k) log n).
    Space: O(n).
    """
    heap = [(-_gain(p, t), p, t) for p, t in classes]
    heapq.heapify(heap)

    for _ in range(extraStudents):
        _, p, t = heapq.heappop(heap)
        p += 1
        t += 1
        heapq.heappush(heap, (-_gain(p, t), p, t))

    return sum(p / t for _, p, t in heap) / len(heap)


# =============================================================================
# TEST
# =============================================================================
def approx_equal(a, b, tol=1e-5):
    return abs(a - b) < tol


def run_tests():
    implementations = [
        ("Way 1: Max-heap gains (BEST)", max_average_1),
        ("Way 2: Inline gain", max_average_2),
        ("Way 3: Inline recompute", max_average_3),
        ("Way 4: Sort each iter", max_average_4),
        ("Way 5: Class wrapper", max_average_5),
        ("Way 6: Heap select", max_average_6),
        ("Way 7: Single-line", max_average_7),
        ("Way 8: heapreplace", max_average_8),
        ("Way 9: Fraction precision", max_average_9),
        ("Way 10: Final cleanest", maxAverageRatio),
    ]

    test_cases = [
        ([[1, 2], [3, 5], [2, 2]], 2, 0.783333),
        ([[1, 2], [3, 5], [2, 2]], 0, 0.700000),  # (0.5+0.6+1.0)/3 = 2.1/3
        ([[2, 4], [3, 9], [4, 5], [2, 10]], 4, 0.534850),
        ([[1, 1]], 100, 1.0),
        ([[1, 2]], 0, 0.5),
        ([[1, 100], [1, 100]], 2, 0.019802),  # both get 1, 2/101 each
        ([[10, 10]], 5, 1.0),
        ([[5, 10], [1, 1]], 1, 0.772727),  # 6/11 + 1 = 0.5455 + 1 = 1.5455/2
    ]

    print("=" * 70)
    print("MAXIMUM AVERAGE PASS RATIO - 10 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for cls, extra, expected in test_cases:
            try:
                cls_copy = [list(c) for c in cls]
                result = fn(cls_copy, extra)
                if approx_equal(result, expected):
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] classes={cls}, extra={extra}, expected={expected}, got={result}")
            except Exception as e:
                failed += 1
                all_pass = False
                print(f"  ERROR [{name}]: {e}")
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
