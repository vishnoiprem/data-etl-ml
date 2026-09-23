"""
Last Stone Weight
Easy | 15 min

We have a collection of stones, each stone has a positive integer weight.
Each turn, we choose the two heaviest stones and smash them together.
Suppose the stones have weights x and y with x <= y. The result is:
  - If x == y, both stones are destroyed.
  - If x != y, the stone of weight x is destroyed, and the stone of weight y
    has new weight y - x.

At the end, there is at most one stone left. Return its weight (0 if none).

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/last-stone-weight

Examples:
    [2,7,4,1,8,1] -> 1
        (8,7) -> 1; [1,4,1,2,1] (5 stones)
        (4,2) -> 2; [1,1,1,2] (4 stones)
        (2,1) -> 1; [1,1,1] (3 stones)
        (1,1) -> 0; [1] (1 stone)
        answer: 1
    [1] -> 1
    [2,2] -> 0

Constraints:
- 1 <= stones.length <= 30
- 1 <= stones[i] <= 1000

KEY INSIGHT:
Max-heap (priority queue). Always pick the two largest.
Pop top, pop next top. If different, push (top1 - top2).

Time:  O(n log n) — heap operations.
Space: O(n) — heap storage.
"""


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT LAST STONE WEIGHT:

1. UNDERSTAND THE PROBLEM:
   "Repeatedly smash the two heaviest stones. Return final weight."

2. KEY OBSERVATION:
   "We need efficient access to the TWO LARGEST elements repeatedly.
   This is the textbook use case for a max-heap (priority queue)."

3. HEAP ALGORITHM:
   "1. Build max-heap from stones (negate values for Python's min-heap).
    2. While heap has 2+ elements:
        y = pop max; x = pop max.
        If y > x: push (y - x).
    3. Return 0 if heap empty, else heap top."

4. WHY MAX-HEAP:
   "We always need the largest. After smash, the new stone might be smaller
   than the next heap top, so we re-insert. Heap gives O(log n) per op."

5. EDGE CASES:
   - Single stone: return it.
   - Two equal stones: return 0.
   - All same weights: depends on count parity.
   - Stones cancel out: return 0.

6. COMPLEXITY:
   +----------+--------+--------+
   | Approach | Time   | Space  |
   +----------+--------+--------+
   | Max-heap | O(n log n) | O(n) |
   | Sort each| O(n² log n) | O(n) |
   | Brute    | O(n²) | O(1) |
   +----------+--------+--------+

7. WHY HEAP IS OPTIMAL:
   "Each smash is O(log n) (push/pop).
   At most n smashes → O(n log n) total.
   Re-sorting would be O(n log n) per iteration → O(n² log n)."
"""


# =============================================================================
# WAY 1: Max-heap with negation (BEST - Memorize!)
# =============================================================================
def last_stone_weight_1(stones):
    """
    Use max-heap (negated values for Python's min-heap).
    Pop two largest, smash, push difference if non-zero.
    """
    import heapq
    heap = [-s for s in stones]
    heapq.heapify(heap)
    while len(heap) > 1:
        y = -heapq.heappop(heap)  # largest
        x = -heapq.heappop(heap)  # second largest
        if y > x:
            heapq.heappush(heap, -(y - x))
    return -heap[0] if heap else 0


# =============================================================================
# WAY 2: Sort each iteration
# =============================================================================
def last_stone_weight_2(stones):
    """Sort descending each iteration. Simpler but slower."""
    stones = sorted(stones, reverse=True)
    while len(stones) > 1:
        y = stones[0]
        x = stones[1]
        stones = stones[2:]
        if y > x:
            stones.append(y - x)
            stones.sort(reverse=True)
    return stones[0] if stones else 0


# =============================================================================
# WAY 3: Sort once, simulate with index
# =============================================================================
def last_stone_weight_3(stones):
    """Use sorted list, smash, re-insert with bisect."""
    import bisect
    stones = sorted(stones)
    while len(stones) > 1:
        y = stones.pop()  # largest
        x = stones.pop()  # second largest
        if y > x:
            bisect.insort(stones, y - x)
    return stones[0] if stones else 0


# =============================================================================
# WAY 4: heapq with explicit comparator
# =============================================================================
def last_stone_weight_4(stones):
    """Use heapq.nlargest repeatedly."""
    import heapq
    # Convert to list, sort descending.
    active = sorted(stones, reverse=True)
    while len(active) > 1:
        # Find two largest.
        largest = heapq.nlargest(1, active)[0]
        active.remove(largest)
        if not active:
            return largest
        second = heapq.nlargest(1, active)[0]
        active.remove(second)
        if largest > second:
            active.append(largest - second)
    return active[0] if active else 0


# =============================================================================
# WAY 5: Recursive
# =============================================================================
def last_stone_weight_5(stones):
    """Recursive: sort, smash, recurse."""

    def helper(s):
        if len(s) <= 1:
            return s[0] if s else 0
        s = sorted(s, reverse=True)
        y = s[0]
        x = s[1]
        rest = s[2:]
        if y == x:
            return helper(rest)
        return helper(rest + [y - x])

    return helper(stones)


# =============================================================================
# WAY 6: heapq with sorted container
# =============================================================================
def last_stone_weight_6(stones):
    """Use heapq directly on positive values with custom comparator."""
    import heapq
    # Use a wrapper to invert comparison.
    heap = []
    for s in stones:
        heapq.heappush(heap, MaxHeapItem(s))
    while len(heap) > 1:
        y = heapq.heappop(heap).val
        x = heapq.heappop(heap).val
        if y > x:
            heapq.heappush(heap, MaxHeapItem(y - x))
    return heap[0].val if heap else 0


class MaxHeapItem:
    def __init__(self, val):
        self.val = val

    def __lt__(self, other):
        return self.val > other.val  # reverse comparison


# =============================================================================
# WAY 7: Manual max-heap with sift-down
# =============================================================================
def last_stone_weight_7(stones):
    """Manually implement max-heap using sift-down. Educational."""
    heap = stones[:]
    n = len(heap)

    def sift_down(arr, size, i):
        """Restore max-heap property at index i."""
        while True:
            largest = i
            left = 2 * i + 1
            right = 2 * i + 2
            if left < size and arr[left] > arr[largest]:
                largest = left
            if right < size and arr[right] > arr[largest]:
                largest = right
            if largest != i:
                arr[i], arr[largest] = arr[largest], arr[i]
                i = largest
            else:
                break

    def pop_max():
        nonlocal n
        if n == 0:
            return None
        val = heap[0]
        heap[0] = heap[n - 1]
        n -= 1
        sift_down(heap, n, 0)
        return val

    def push(val):
        nonlocal n
        heap[n] = val
        i = n
        n += 1
        # Sift up.
        while i > 0:
            parent = (i - 1) // 2
            if heap[i] > heap[parent]:
                heap[i], heap[parent] = heap[parent], heap[i]
                i = parent
            else:
                break

    # Build heap in-place.
    for i in range(n // 2 - 1, -1, -1):
        sift_down(heap, n, i)
    # Smash.
    while n > 1:
        y = pop_max()
        x = pop_max()
        if y > x:
            push(y - x)
    return heap[0] if n == 1 else 0


# =============================================================================
# WAY 8: Class OOP
# =============================================================================
class StoneSmash:
    def __init__(self, stones):
        self.stones = stones

    def smash(self):
        import heapq
        heap = [-s for s in self.stones]
        heapq.heapify(heap)
        while len(heap) > 1:
            y = -heapq.heappop(heap)
            x = -heapq.heappop(heap)
            if y > x:
                heapq.heappush(heap, -(y - x))
        return -heap[0] if heap else 0


def last_stone_weight_8(stones):
    return StoneSmash(stones).smash()


# =============================================================================
# WAY 9: heapq.nlargest each step
# =============================================================================
def last_stone_weight_9(stones):
    """Use heapq.nlargest to get top 2, smash, push back."""
    import heapq
    heap = [-s for s in stones]
    heapq.heapify(heap)
    while len(heap) >= 2:
        # Get top 2.
        largest = -heapq.heappop(heap)
        if heap:
            second = -heapq.heappop(heap)
            if largest > second:
                heapq.heappush(heap, -(largest - second))
        else:
            heapq.heappush(heap, -largest)
    return -heap[0] if heap else 0


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def last_stone_weight_10(stones):
    """
    THE ONE TO MEMORIZE.

    Max-heap with negation (Python heapq is min-heap).
    Pop two largest, smash, push difference if positive.

    Time:  O(n log n).
    Space: O(n).
    """
    import heapq
    heap = [-s for s in stones]
    heapq.heapify(heap)
    while len(heap) > 1:
        y = -heapq.heappop(heap)
        x = -heapq.heappop(heap)
        if y > x:
            heapq.heappush(heap, -(y - x))
    return -heap[0] if heap else 0


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Max-heap neg (BEST)", last_stone_weight_1),
        ("Way 2: Sort each iter", last_stone_weight_2),
        ("Way 3: Sorted + bisect", last_stone_weight_3),
        ("Way 4: Counter", last_stone_weight_4),
        ("Way 5: Recursive", last_stone_weight_5),
        ("Way 6: MaxHeapItem class", last_stone_weight_6),
        ("Way 7: Manual heap", last_stone_weight_7),
        ("Way 8: Class OOP", last_stone_weight_8),
        ("Way 9: nlargest style", last_stone_weight_9),
        ("Way 10: Final cleanest", last_stone_weight_10),
    ]

    test_cases = [
        # (stones, expected)
        ([2, 7, 4, 1, 8, 1], 1),
        ([1], 1),
        ([2, 2], 0),
        ([1, 2, 3], 0),
        ([3, 3, 3], 3),
        ([1, 1, 1, 1, 1], 1),
        ([10, 4, 2, 10], 2),
        ([1, 3, 5, 7, 9], 1),
        ([5], 5),
        ([9, 3, 2, 10], 0),
    ]

    print("=" * 70)
    print("LAST STONE WEIGHT - 10 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/last-stone-weight")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for inp, expected in test_cases:
            try:
                result = func(list(inp))
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: stones={inp}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: stones={inp}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
