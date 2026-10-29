"""
Minimum Space Wasted from Packaging
Hard | 40 min

You have n packages to place into boxes (one package per box). There are m
suppliers, each offering boxes of various sizes (infinite supply of each).
A package fits in a box if box_size >= package_size.

Each supplier has different box sizes. Choose ONE supplier to minimize total
wasted space (= box_size - package_size summed).

Return the minimum wasted space modulo 10^9 + 7, or -1 if no supplier can fit
all packages.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-space-wasted-from-packaging

Constraints:
- 1 <= n, m <= 50
- 1 <= packages[i] <= 10^3
- 1 <= boxes[j].length <= 30
- sum(boxes[j].length) <= 10^5
- 1 <= boxes[j][k] <= 10^3
- Boxes within a supplier are distinct.

Examples:
    packages=[2,3,5], boxes=[[3,5,7]] -> 3 (2->3 w=1, 3->5 w=2, 5->5 w=0)
    packages=[2,3,5], boxes=[[3,5],[4,6]] -> 1 or 2

Key Insight:
For a single supplier:
- Sort packages and the supplier's boxes.
- For each package, use binary search to find the smallest box >= package.
- This is optimal because using a larger box for a small package wastes more
  and doesn't help a larger package (which needs an even larger box).

Total wasted space for a supplier = sum(smallest_box_geq(p) - p for p in packages).

If max(package) > max(box of supplier), supplier can't fit all packages.

Try all suppliers, return the minimum waste.

Time:  O(n*m*log(n) + total_boxes*log(total_boxes))
       = O(m*n*log(n)) for the search, O(sum(boxes[j].length)*log(...)) for sorting.
Space: O(1) extra (besides sorted arrays).
"""


# =============================================================================
# WAY 1: Sort + binary search per supplier (BEST - Memorize!)
# =============================================================================
def min_wasted_space_1(packages, boxes):
    """
    For each supplier:
    - Sort their boxes.
    - Use binary search to find smallest box >= each package.
    - Sum the waste.
    Return the minimum waste.
    """
    MOD = 10**9 + 7
    packages.sort()
    n = len(packages)

    best = float('inf')
    for supplier_boxes in boxes:
        supplier_boxes = sorted(supplier_boxes)
        # Check if supplier can fit the largest package
        if supplier_boxes[-1] < packages[-1]:
            continue
        waste = 0
        for pkg in packages:
            # Find smallest box >= pkg
            import bisect
            idx = bisect.bisect_left(supplier_boxes, pkg)
            waste += supplier_boxes[idx] - pkg
        best = min(best, waste)

    return best % MOD if best != float('inf') else -1


# =============================================================================
# WAY 2: Verbose version with manual binary search
# =============================================================================
def min_wasted_space_2(packages, boxes):
    """Manual binary search instead of bisect."""
    MOD = 10**9 + 7
    packages.sort()
    n = len(packages)

    def lower_bound(arr, target):
        """Find first index where arr[idx] >= target."""
        lo, hi = 0, len(arr)
        while lo < hi:
            mid = (lo + hi) // 2
            if arr[mid] < target:
                lo = mid + 1
            else:
                hi = mid
        return lo

    best = float('inf')
    for supplier_boxes in boxes:
        supplier_boxes = sorted(supplier_boxes)
        if supplier_boxes[-1] < packages[-1]:
            continue
        waste = 0
        for pkg in packages:
            idx = lower_bound(supplier_boxes, pkg)
            waste += supplier_boxes[idx] - pkg
        best = min(best, waste)

    return best % MOD if best != float('inf') else -1


# =============================================================================
# WAY 3: Using bisect_right
# =============================================================================
def min_wasted_space_3(packages, boxes):
    """Use bisect_right - 1 for the smallest box >= pkg."""
    MOD = 10**9 + 7
    packages.sort()
    n = len(packages)

    best = float('inf')
    for supplier_boxes in boxes:
        supplier_boxes = sorted(set(supplier_boxes))  # dedupe (input says distinct but be safe)
        if supplier_boxes[-1] < packages[-1]:
            continue
        import bisect
        waste = 0
        for pkg in packages:
            idx = bisect.bisect_right(supplier_boxes, pkg) - 1
            # If idx is at position where box < pkg, take next... wait
            # We want smallest box >= pkg, so idx should point to box >= pkg
            # bisect_right(arr, pkg) returns insertion point AFTER all pkg's
            # So bisect_right - 1 is the LAST box <= pkg.
            # We need first box >= pkg, which is bisect_left.
            idx = bisect.bisect_left(supplier_boxes, pkg)
            waste += supplier_boxes[idx] - pkg
        best = min(best, waste)

    return best % MOD if best != float('inf') else -1


# =============================================================================
# WAY 4: Two-pointer approach
# =============================================================================
def min_wasted_space_4(packages, boxes):
    """
    Two-pointer: For sorted packages and sorted boxes, walk both.
    But since we have infinite supply, we can reuse boxes — really we just
    need the box size for each package, which is bisect.
    """
    MOD = 10**9 + 7
    packages.sort()
    best = float('inf')

    for supplier_boxes in boxes:
        supplier_boxes = sorted(supplier_boxes)
        if supplier_boxes[-1] < packages[-1]:
            continue
        # For each package, find smallest box >= pkg
        waste = 0
        import bisect
        for pkg in packages:
            idx = bisect.bisect_left(supplier_boxes, pkg)
            waste += supplier_boxes[idx] - pkg
        best = min(best, waste)

    return best % MOD if best != float('inf') else -1


# =============================================================================
# WAY 5: Use sortedcontainers (if available)
# =============================================================================
def min_wasted_space_5(packages, boxes):
    """Use SortedList from sortedcontainers (or fallback)."""
    MOD = 10**9 + 7
    try:
        from sortedcontainers import SortedList
        packages.sort()
        best = float('inf')
        for supplier_boxes in boxes:
            sl = SortedList(sorted(supplier_boxes))
            if sl[-1] < packages[-1]:
                continue
            waste = 0
            for pkg in packages:
                idx = sl.bisect_left(pkg)
                waste += sl[idx] - pkg
            best = min(best, waste)
        return best % MOD if best != float('inf') else -1
    except ImportError:
        return min_wasted_space_1(packages, boxes)


# =============================================================================
# WAY 6: With intermediate sorting
# =============================================================================
def min_wasted_space_6(packages, boxes):
    """Pre-sort all supplier boxes once."""
    MOD = 10**9 + 7
    packages.sort()
    sorted_boxes = [sorted(b) for b in boxes]
    best = float('inf')
    import bisect

    for s_boxes in sorted_boxes:
        if s_boxes[-1] < packages[-1]:
            continue
        waste = 0
        for pkg in packages:
            idx = bisect.bisect_left(s_boxes, pkg)
            waste += s_boxes[idx] - pkg
        if waste < best:
            best = waste

    return best % MOD if best != float('inf') else -1


# =============================================================================
# WAY 7: Class-based
# =============================================================================
class WastedSpaceCalculator:
    MOD = 10**9 + 7

    def __init__(self, packages, boxes):
        self.packages = sorted(packages)
        self.boxes = [sorted(b) for b in boxes]

    def min_wasted(self):
        import bisect
        best = float('inf')
        for s_boxes in self.boxes:
            if s_boxes[-1] < self.packages[-1]:
                continue
            waste = 0
            for pkg in self.packages:
                idx = bisect.bisect_left(s_boxes, pkg)
                waste += s_boxes[idx] - pkg
            best = min(best, waste)
        return best % self.MOD if best != float('inf') else -1


def min_wasted_space_7(packages, boxes):
    """Class-based."""
    return WastedSpaceCalculator(packages, boxes).min_wasted()


# =============================================================================
# WAY 8: Numpy-based
# =============================================================================
def min_wasted_space_8(packages, boxes):
    """Use numpy searchsorted for vectorized lookups."""
    MOD = 10**9 + 7
    try:
        import numpy as np
        import bisect
        packages_arr = np.array(sorted(packages))
        best = float('inf')
        for supplier_boxes in boxes:
            s_boxes = np.array(sorted(supplier_boxes))
            if s_boxes[-1] < packages_arr[-1]:
                continue
            # np.searchsorted with 'left' finds first idx where s_boxes[idx] >= pkg
            indices = np.searchsorted(s_boxes, packages_arr, side='left')
            waste = int(np.sum(s_boxes[indices] - packages_arr))
            best = min(best, waste)
        return best % MOD if best != float('inf') else -1
    except ImportError:
        return min_wasted_space_1(packages, boxes)


# =============================================================================
# WAY 9: Recursive helper
# =============================================================================
def min_wasted_space_9(packages, boxes):
    """Recursive approach to compute waste for one supplier."""
    MOD = 10**9 + 7
    packages.sort()
    best = [float('inf')]

    def supplier_waste(s_boxes, idx=0, waste=0):
        if idx == len(packages):
            if waste < best[0]:
                best[0] = waste
            return
        # Prune: if current waste already > best, skip
        if waste >= best[0]:
            return
        import bisect
        s_boxes_sorted = sorted(s_boxes)
        if s_boxes_sorted[-1] < packages[idx]:
            return
        # Try each box that fits
        box_idx = bisect.bisect_left(s_boxes_sorted, packages[idx])
        if box_idx < len(s_boxes_sorted):
            supplier_waste(s_boxes_sorted, idx + 1, waste + s_boxes_sorted[box_idx] - packages[idx])

    for s_boxes in boxes:
        supplier_waste(s_boxes)

    return best[0] % MOD if best[0] != float('inf') else -1


# =============================================================================
# WAY 10: One-pass with sorted boxes combined
# =============================================================================
def min_wasted_space_10(packages, boxes):
    """Combine all boxes into one list per supplier (already done in input)."""
    MOD = 10**9 + 7
    import bisect
    packages.sort()
    best = float('inf')
    for s_boxes in boxes:
        s_boxes = sorted(s_boxes)
        if s_boxes[-1] < packages[-1]:
            continue
        waste = sum(
            s_boxes[bisect.bisect_left(s_boxes, pkg)] - pkg
            for pkg in packages
        )
        if waste < best:
            best = waste
    return best % MOD if best != float('inf') else -1


# =============================================================================
# WAY 11: With reduce
# =============================================================================
def min_wasted_space_11(packages, boxes):
    """Use functools.reduce to compute total waste."""
    MOD = 10**9 + 7
    import bisect
    from functools import reduce
    packages.sort()
    best = float('inf')

    def total_waste(s_boxes):
        return reduce(
            lambda acc, pkg: acc + (s_boxes[bisect.bisect_left(s_boxes, pkg)] - pkg),
            packages,
            0
        )

    for s_boxes in boxes:
        s_boxes = sorted(s_boxes)
        if s_boxes[-1] < packages[-1]:
            continue
        w = total_waste(s_boxes)
        if w < best:
            best = w

    return best % MOD if best != float('inf') else -1


# =============================================================================
# WAY 12: Using map
# =============================================================================
def min_wasted_space_12(packages, boxes):
    """Use map for per-package waste computation."""
    MOD = 10**9 + 7
    import bisect
    packages.sort()
    best = float('inf')

    for s_boxes in boxes:
        s_boxes = sorted(s_boxes)
        if s_boxes[-1] < packages[-1]:
            continue
        # Sum of (smallest box >= pkg - pkg) over all packages
        waste = sum(map(
            lambda p: s_boxes[bisect.bisect_left(s_boxes, p)] - p,
            packages
        ))
        if waste < best:
            best = waste

    return best % MOD if best != float('inf') else -1


# =============================================================================
# WAY 13: With cache / memoization
# =============================================================================
def min_wasted_space_13(packages, boxes):
    """Cache supplier calculations."""
    MOD = 10**9 + 7
    import bisect
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def waste_for_supplier(tuple_boxes):
        sb = sorted(tuple_boxes)
        if sb[-1] < packages[-1]:
            return float('inf')
        return sum(sb[bisect.bisect_left(sb, pkg)] - pkg for pkg in packages)

    packages.sort()
    best = float('inf')
    for s_boxes in boxes:
        w = waste_for_supplier(tuple(sorted(s_boxes)))
        if w < best:
            best = w

    return best % MOD if best != float('inf') else -1


# =============================================================================
# WAY 14: Enumerate-based
# =============================================================================
def min_wasted_space_14(packages, boxes):
    """Enumerate for clarity."""
    MOD = 10**9 + 7
    import bisect
    packages.sort()
    best = float('inf')

    for i, s_boxes in enumerate(boxes):
        s_boxes = sorted(s_boxes)
        if s_boxes[-1] < packages[-1]:
            continue
        waste = 0
        for j, pkg in enumerate(packages):
            idx = bisect.bisect_left(s_boxes, pkg)
            waste += s_boxes[idx] - pkg
        if waste < best:
            best = waste

    return best % MOD if best != float('inf') else -1


# =============================================================================
# WAY 15: Direct loops without bisect
# =============================================================================
def min_wasted_space_15(packages, boxes):
    """Manually search through boxes for each package."""
    MOD = 10**9 + 7
    packages.sort()
    best = float('inf')

    for s_boxes in boxes:
        s_boxes = sorted(s_boxes)
        if s_boxes[-1] < packages[-1]:
            continue
        waste = 0
        for pkg in packages:
            # Linear scan for smallest box >= pkg
            for box in s_boxes:
                if box >= pkg:
                    waste += box - pkg
                    break
        if waste < best:
            best = waste

    return best % MOD if best != float('inf') else -1


# =============================================================================
# WAY 16: Precompute box assignments
# =============================================================================
def min_wasted_space_16(packages, boxes):
    """Precompute box index for each package size (memoization by size)."""
    MOD = 10**9 + 7
    import bisect
    packages.sort()

    def compute_supplier_waste(s_boxes):
        s_boxes = sorted(s_boxes)
        if s_boxes[-1] < packages[-1]:
            return float('inf')
        # Cache: for each pkg size, find smallest box >= pkg
        cache = {}
        waste = 0
        for pkg in packages:
            if pkg not in cache:
                cache[pkg] = bisect.bisect_left(s_boxes, pkg)
            idx = cache[pkg]
            waste += s_boxes[idx] - pkg
        return waste

    best = float('inf')
    for s_boxes in boxes:
        w = compute_supplier_waste(s_boxes)
        if w < best:
            best = w

    return best % MOD if best != float('inf') else -1


# =============================================================================
# WAY 17: Use any/all for early termination
# =============================================================================
def min_wasted_space_17(packages, boxes):
    """Use any/all for cleaner checks."""
    MOD = 10**9 + 7
    import bisect
    packages.sort()
    best = float('inf')

    for s_boxes in boxes:
        s_boxes = sorted(s_boxes)
        # Skip if any package too large
        if any(s_boxes[-1] < pkg for pkg in packages):
            continue
        waste = 0
        for pkg in packages:
            idx = bisect.bisect_left(s_boxes, pkg)
            waste += s_boxes[idx] - pkg
        if waste < best:
            best = waste

    return best % MOD if best != float('inf') else -1


# =============================================================================
# WAY 18: Most concise
# =============================================================================
def min_wasted_space_18(packages, boxes):
    """Most concise version."""
    MOD = 10**9 + 7
    import bisect
    pkgs = sorted(packages)
    best = min(
        (
            sum(b[bisect.bisect_left(b, p)] - p for p in pkgs)
            for b in (sorted(sb) for sb in boxes)
            if b[-1] >= pkgs[-1]
        ),
        default=float('inf')
    )
    return best % MOD if best != float('inf') else -1


# =============================================================================
# WAY 19: With pre-computed bisect indices
# =============================================================================
def min_wasted_space_19(packages, boxes):
    """Use list of bisect indices for efficiency."""
    MOD = 10**9 + 7
    import bisect
    packages.sort()
    best = float('inf')

    for s_boxes in boxes:
        s_boxes = sorted(s_boxes)
        if s_boxes[-1] < packages[-1]:
            continue
        indices = [bisect.bisect_left(s_boxes, p) for p in packages]
        waste = sum(s_boxes[i] - p for i, p in zip(indices, packages))
        if waste < best:
            best = waste

    return best % MOD if best != float('inf') else -1


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def min_wasted_space_20(packages, boxes):
    """
    Final clean version.

    Algorithm:
    1. Sort packages.
    2. For each supplier:
       a. Sort their boxes.
       b. Skip if max(box) < max(package) - can't fit all.
       c. For each package, find smallest box >= package (binary search).
       d. Sum the waste.
    3. Return minimum waste, or -1 if no supplier works.

    Why this works:
    For each supplier independently, the optimal strategy is to assign each
    package to the smallest box that fits. This is because:
    - Using a larger box wastes more space.
    - Using a smaller box would not fit the package.
    - Independent per package: we have infinite supply, so reusing the same
      box size for different packages is fine.

    Why binary search: Find smallest box >= pkg in O(log k) where k = #boxes.

    Time:  O(n*log(n) + m*(k*log(k) + n*log(k))) where k is max box count.
           = O(m * n * log(n)) with the binary search.
    Space: O(1) extra (besides sorted arrays in place).
    """
    MOD = 10**9 + 7
    import bisect
    packages.sort()
    best = float('inf')

    for supplier_boxes in boxes:
        s_boxes = sorted(supplier_boxes)
        # Skip if can't fit largest package
        if s_boxes[-1] < packages[-1]:
            continue
        waste = 0
        for pkg in packages:
            idx = bisect.bisect_left(s_boxes, pkg)
            waste += s_boxes[idx] - pkg
        best = min(best, waste)

    return best % MOD if best != float('inf') else -1


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the supplier with minimum total wasted space when packing
all packages into boxes (one per box, infinite supply per size)."

Key Insight:
"For each supplier independently, the optimal assignment is: for each
package, use the SMALLEST box that fits it. This minimizes waste because
using a larger box would only waste more space."

Algorithm:
"1. Sort packages.
2. For each supplier:
   a. Sort their boxes.
   b. If max(box) < max(package): skip — can't fit.
   c. For each package, binary search for smallest box >= package.
   d. Sum (box - package) for all packages — that's the waste.
3. Return minimum waste, or -1 if no supplier works."

Why this works:
"Since boxes have infinite supply, we can use the same box size for many
packages. So the assignment is INDEPENDENT per package: just pick the
smallest box that fits. No 'consumption' of boxes."

Why binary search:
"Boxes are sorted. To find smallest box >= pkg, use bisect_left in O(log k)."

Edge cases:
- No supplier can fit max package: return -1.
- Only one supplier: return their waste (if feasible).
- All packages same size: single search per supplier.
- Empty packages or boxes: edge cases per problem constraints.

Complexity:
- Time:  O(n log n + m * (k log k + n log k))
        = O(n log n + m * n * log(k)) overall.
- Space: O(1) extra (besides sorting).

KEY TRICK:
For each supplier, find smallest box >= package using binary search on
sorted boxes. Sum wastes. Take min across suppliers.

ALTERNATIVE: Brute force O(n*k) per supplier
For each package, scan all boxes. O(n*k) per supplier, O(m*n*k) total.
Too slow for large inputs.

ALTERNATIVE: Precompute
Cache box indices per package size across suppliers (memoization).
Same complexity, slightly faster in practice.

RELATIONSHIP TO OTHER PROBLEMS:
- Assign Cookies (LC 455): Similar greedy matching, but 1-to-1 assignment.
- Minimum Number of Refueling Stops (LC 871): Different - scheduling.
- Two Sum II (LC 167): Binary search on sorted array.

INTERVIEW TIPS:
1. Mention the greedy choice (smallest fitting box per package).
2. Note that infinite supply means no 1-to-1 constraint.
3. Discuss binary search for finding smallest box >= package.
4. Handle the "no supplier works" case (-1).
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Sort + bisect (BEST)", min_wasted_space_1),
        ("Way 2: Manual binary search", min_wasted_space_2),
        ("Way 3: bisect_right approach", min_wasted_space_3),
        ("Way 4: Two-pointer concept", min_wasted_space_4),
        ("Way 5: sortedcontainers", min_wasted_space_5),
        ("Way 6: Pre-sort all", min_wasted_space_6),
        ("Way 7: Class-based", min_wasted_space_7),
        ("Way 8: numpy searchsorted", min_wasted_space_8),
        ("Way 9: Recursive", min_wasted_space_9),
        ("Way 10: One-pass", min_wasted_space_10),
        ("Way 11: functools.reduce", min_wasted_space_11),
        ("Way 12: map()", min_wasted_space_12),
        ("Way 13: LRU cache", min_wasted_space_13),
        ("Way 14: enumerate", min_wasted_space_14),
        ("Way 15: Linear scan no bisect", min_wasted_space_15),
        ("Way 16: Cache by pkg size", min_wasted_space_16),
        ("Way 17: any/all early exit", min_wasted_space_17),
        ("Way 18: Most concise", min_wasted_space_18),
        ("Way 19: Pre-compute bisect", min_wasted_space_19),
        ("Way 20: Final cleanest", min_wasted_space_20),
    ]

    # Note: results are modulo 10^9+7, but for small test cases the values
    # are small enough that the mod doesn't matter.
    MOD = 10**9 + 7

    test_cases = [
        # Example 1: packages=[2,3,5], boxes=[[3,5,7]]
        # 2->3(w=1), 3->3(w=0), 5->5(w=0). Total=1.
        ([2, 3, 5], [[3, 5, 7]], 1),

        # Two suppliers
        # S1: [3,5] -> 2->3(w=1), 3->3(w=0), 5->5(w=0). Total=1.
        # S2: [4,6] -> 2->4(w=2), 3->4(w=1), 5->6(w=1). Total=4.
        # Min = 1
        ([2, 3, 5], [[3, 5], [4, 6]], 1),

        # Three suppliers
        # S1: [4,7] -> 2->4(w=2), 3->4(w=1), 5->7(w=2). Total=5.
        # S2: [5,8] -> 2->5(w=3), 3->5(w=2), 5->5(w=0). Total=5.
        # S3: [6,9] -> 2->6(w=4), 3->6(w=3), 5->6(w=1). Total=8.
        # Min = 5
        ([2, 3, 5], [[4, 7], [5, 8], [6, 9]], 5),

        # Single package, single supplier
        ([5], [[10]], 5),

        # Single package, multiple suppliers
        ([5], [[3], [7], [10]], 2),  # 5->7(w=2) is best

        # No supplier can fit
        ([10], [[5], [6]], -1),

        # Larger package set
        # packages=[1,2,3,4,5]
        # S1: [2,4,6] -> 1->2(w=1), 2->2(w=0), 3->4(w=1), 4->4(w=0), 5->6(w=1). Total=3.
        # S2: [5,10] -> 1->5(w=4), 2->5(w=3), 3->5(w=2), 4->5(w=1), 5->5(w=0). Total=10.
        # Min = 3
        ([1, 2, 3, 4, 5], [[2, 4, 6], [5, 10]], 3),

        # Exact fit - no waste
        # packages=[3,5,7], boxes=[[3,5,7]]
        # 3->3(w=0), 5->5(w=0), 7->7(w=0). Total=0.
        ([3, 5, 7], [[3, 5, 7]], 0),

        # Single box, multiple packages
        # packages=[1,2,3], boxes=[[3]] -> 1->3(w=2), 2->3(w=1), 3->3(w=0). Total=3.
        ([1, 2, 3], [[3]], 3),

        # Two same-sized packages
        # packages=[5,5], boxes=[[7]]
        # 5->7(w=2), 5->7(w=2). Total=4.
        ([5, 5], [[7]], 4),

        # Multiple suppliers, one can't fit
        # packages=[10,20]
        # S1: [15,25] -> 10->15(w=5), 20->25(w=5). Total=10.
        # S2: [12] -> can't fit 20. SKIP.
        # S3: [10,20] -> 0 waste.
        ([10, 20], [[15, 25], [12], [10, 20]], 0),

        # Larger example
        # packages=[1,2,3,4,5,6,7,8,9,10]
        # S1: [10] -> all use box 10. (10-1)+(10-2)+...+(10-10) = 45.
        # S2: [1..10] -> 0 waste.
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], [[10], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]], 0),

        # Stress test
        ([1000], [[1000]], 0),
    ]

    print("=" * 70)
    print("MINIMUM SPACE WASTED FROM PACKAGING - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-space-wasted-from-packaging")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for packages, boxes, expected in test_cases:
            try:
                import copy
                result = func(copy.deepcopy(packages), copy.deepcopy(boxes))
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: pkgs={packages}, boxes={boxes} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on pkgs={packages} - {e}")
        if all_test_pass:
            print(f"  OK {name}: PASS")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)