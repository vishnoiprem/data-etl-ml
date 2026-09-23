"""
Maximize Capital (IPO) - 10 Ways
Hard | 25 min
https://www.educative.io/courses/grokking-coding-interview-in-python/maximize-capital

Suppose LeetCode will start its IPO soon. In order to sell a good price of
its shares to Venture Capital, LeetCode would like to work on some projects
to increase its capital before the IPO. There are at most k projects that
can be selected. Initially, you have w capital. Given w, k, profits and
capital (length n), find the maximum capital after finishing at most k
projects.

Each project i has:
- profits[i]: the profit you gain after doing it.
- capital[i]: the minimum capital required to start it.

KEY INSIGHT:
Greedy + max-heap. At each step, push all projects whose capital <= w into
a max-heap of profits. Pop the highest-profit project and add it to w.
Repeat up to k times.

Examples:
    w=2, k=3, profits=[1,2,3], capital=[1,3,4]  =>  8

Constraints:
- 1 <= k <= 10^5
- 0 <= w <= 10^9
- n == profits.length == capital.length
- 1 <= n <= 10^5
- 0 <= profits[i] <= 10^4
- 0 <= capital[i] <= 10^9
"""

import heapq
import sys

sys.setrecursionlimit(100000)


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT MAXIMIZE CAPITAL (IPO):

1. WHAT IS THE PROBLEM?
   "Pick up to k projects to maximize final capital. Each project requires
   a minimum capital and yields a profit."

2. WHY GREEDY + MAX-HEAP?
   "At each step, among affordable projects (capital <= current w), pick the
    one with the highest profit. This maximizes capital for future steps.
    Use a max-heap of profits of affordable projects."

3. ALGORITHM:
   "1. Sort projects by capital (or zip and sort).
    2. For up to k iterations:
       a. Push profits of all projects with capital <= w into max-heap.
       b. If max-heap empty: break (can't afford anything).
       c. Pop the max profit and add to w."

4. EDGE CASES:
   - No projects affordable at start: w unchanged.
   - profits and capital may have duplicates.
   - k may be larger than number of affordable projects.

5. WHEN TO USE:
   - Job scheduling with prerequisites and rewards.
   - "Pick k best items I can afford right now" type problems.

6. COMMON TRAPS:
   - Forgetting to filter by capital.
   - Not breaking when no affordable projects left.
   - Using min-heap instead of max-heap (need negation).

7. COMPLEXITY:
   +------------+--------+--------+
   | Operation  | Time   | Notes  |
   +------------+--------+--------+
   | Sort       | O(n log n)      |
   | k iterations | O(k log n)    |
   | Overall    | O((n + k) log n)|
   | Space      | O(n)            |
   +------------+--------+--------+
"""


# =============================================================================
# WAY 1: Greedy + max-heap (BEST - Memorize!)
# =============================================================================
def maximize_capital_1(k, w, profits, capital):
    """Greedy: each step take the highest-profit affordable project."""
    n = len(profits)
    projects = sorted(zip(capital, profits))  # sort by capital
    max_profit = []
    i = 0
    for _ in range(k):
        # Push all affordable into max-heap
        while i < n and projects[i][0] <= w:
            heapq.heappush(max_profit, -projects[i][1])
            i += 1
        if not max_profit:
            break
        w += -heapq.heappop(max_profit)
    return w


# =============================================================================
# WAY 2: Same as 1, but use heapify on the slice
# =============================================================================
def maximize_capital_2(k, w, profits, capital):
    n = len(profits)
    pairs = sorted(zip(capital, profits))
    max_profit = []
    i = 0
    for _ in range(k):
        while i < n and pairs[i][0] <= w:
            heapq.heappush(max_profit, -pairs[i][1])
            i += 1
        if max_profit:
            w += -heapq.heappop(max_profit)
        else:
            break
    return w


# =============================================================================
# WAY 3: Sort projects with index, then walk
# =============================================================================
def maximize_capital_3(k, w, profits, capital):
    n = len(profits)
    order = sorted(range(n), key=lambda x: capital[x])
    max_profit = []
    i = 0
    for _ in range(k):
        while i < n and capital[order[i]] <= w:
            heapq.heappush(max_profit, -profits[order[i]])
            i += 1
        if not max_profit:
            break
        w += -heapq.heappop(max_profit)
    return w


# =============================================================================
# WAY 4: Recursive with heap (passes through remaining heap)
# =============================================================================
def maximize_capital_4(k, w, profits, capital):
    """Greedy but recursive - tracking position in sorted list and heap."""
    pairs = sorted(zip(capital, profits))
    n = len(pairs)

    def helper(rem, w, idx, heap):
        if rem == 0:
            return w
        new_idx = idx
        while new_idx < n and pairs[new_idx][0] <= w:
            heapq.heappush(heap, -pairs[new_idx][1])
            new_idx += 1
        if not heap:
            return w
        w += -heapq.heappop(heap)
        return helper(rem - 1, w, new_idx, heap)

    return helper(k, w, 0, [])


# =============================================================================
# WAY 5: Class-based wrapper
# =============================================================================
class IPOMaximizer_5:
    def __init__(self, k, w, profits, capital):
        self.k = k
        self.w = w
        self.profits = profits
        self.capital = capital

    def compute(self):
        return maximize_capital_1(self.k, self.w, self.profits, self.capital)


def maximize_capital_5(k, w, profits, capital):
    return IPOMaximizer_5(k, w, profits, capital).compute()


# =============================================================================
# WAY 6: Sort by capital, then greedy with priority queue
# =============================================================================
def maximize_capital_6(k, w, profits, capital):
    pairs = sorted(zip(capital, profits))
    pq = []  # max-heap of profits
    idx = 0
    for _ in range(k):
        while idx < len(pairs) and pairs[idx][0] <= w:
            heapq.heappush(pq, -pairs[idx][1])
            idx += 1
        if pq:
            w += -heapq.heappop(pq)
    return w


# =============================================================================
# WAY 7: Brute force with sort each iteration (slow but correct)
# =============================================================================
def maximize_capital_7(k, w, profits, capital):
    """Each iteration: pick affordable, choose max-profit."""
    done = [False] * len(profits)
    for _ in range(k):
        best = -1
        best_profit = 0
        for i in range(len(profits)):
            if not done[i] and capital[i] <= w and profits[i] > best_profit:
                best = i
                best_profit = profits[i]
        if best == -1:
            break
        w += best_profit
        done[best] = True
    return w


# =============================================================================
# WAY 8: Use heapq.heapify on each insertion batch
# =============================================================================
def maximize_capital_8(k, w, profits, capital):
    pairs = sorted(zip(capital, profits))
    available = []  # max-heap of profits
    i = 0
    for _ in range(k):
        while i < len(pairs) and pairs[i][0] <= w:
            heapq.heappush(available, -pairs[i][1])
            i += 1
        if not available:
            break
        w -= heapq.heappop(available)  # heappop returns smallest; negate
    return w


# =============================================================================
# WAY 9: Use tuple in heap for tie-breaking
# =============================================================================
def maximize_capital_9(k, w, profits, capital):
    pairs = sorted(zip(capital, profits))
    pq = []  # max-heap: (-profit, index) for tie-breaking
    i = 0
    for _ in range(k):
        while i < len(pairs) and pairs[i][0] <= w:
            heapq.heappush(pq, (-pairs[i][1], i))
            i += 1
        if not pq:
            break
        profit, _ = heapq.heappop(pq)
        w += -profit
    return w


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def maximize_capital(k, w, profits, capital):
    """
    THE ONE TO MEMORIZE.

    1. Sort projects by capital.
    2. For up to k iterations:
       a. Push all profits of projects with capital <= w into max-heap.
       b. If heap is empty, break.
       c. w += -heappop(max-heap).

    Time:  O((n + k) log n).
    Space: O(n).
    """
    pairs = sorted(zip(capital, profits))
    pq = []
    i = 0
    for _ in range(k):
        while i < len(pairs) and pairs[i][0] <= w:
            heapq.heappush(pq, -pairs[i][1])
            i += 1
        if not pq:
            break
        w += -heapq.heappop(pq)
    return w


# =============================================================================
# TEST
# =============================================================================
def run_tests():
    implementations = [
        ("Way 1: Greedy + heap (BEST)", maximize_capital_1),
        ("Way 2: Same w/ neg", maximize_capital_2),
        ("Way 3: Sort by index", maximize_capital_3),
        ("Way 4: Recursive", maximize_capital_4),
        ("Way 5: Class wrapper", maximize_capital_5),
        ("Way 6: PQ greedy", maximize_capital_6),
        ("Way 7: Brute force", maximize_capital_7),
        ("Way 8: heapify variant", maximize_capital_8),
        ("Way 9: Tie-breaking", maximize_capital_9),
        ("Way 10: Final cleanest", maximize_capital),
    ]

    test_cases = [
        # (k, w, profits, capital, expected)
        (1, 0, [1, 2, 3], [0, 1, 1], 1),
        (2, 0, [1, 2, 3], [0, 1, 1], 4),  # take 1 (cap 0), then 3 (cap 1) -> 0+1+3=4
        (3, 0, [1, 2, 3], [0, 1, 1], 6),  # 1+2+3
        (3, 2, [1, 2, 3], [1, 3, 4], 8),  # greedy: 1+2+3 = 2+1+2+3 = 8
        (1, 100, [1, 2, 3], [0, 1, 1], 103),  # take 3
        (2, 0, [1, 2, 3], [1, 2, 3], 0),
        (10, 5, [1, 5, 10, 50], [0, 1, 5, 10], 71),  # all 4 projects: 5+1+5+10+50=71
        (2, 7, [4, 6, 8], [3, 5, 7], 21),  # take 8 and 6
    ]

    print("=" * 70)
    print("MAXIMIZE CAPITAL (IPO) - 10 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for k, w, profits, capital, expected in test_cases:
            try:
                result = fn(k, w, list(profits), list(capital))
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] k={k}, w={w}, profits={profits}, capital={capital}, expected={expected}, got={result}")
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