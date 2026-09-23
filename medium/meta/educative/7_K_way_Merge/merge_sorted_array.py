"""
Merge Sorted Array
Easy | 15 min

You are given two integer arrays nums1 and nums2, sorted in non-decreasing
order, and two integers m and n, representing the number of elements in
nums1 and nums2 respectively.

Merge nums1 and nums2 into a single array sorted in non-decreasing order.
The final sorted array should be stored inside the array nums1.

To accommodate this, nums1 has a length of m + n, where the first m
elements denote the elements that should be merged, and the last n
elements are set to 0 and should be ignored. nums2 has a length of n.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/merge-sorted-array

Examples:
    nums1=[1,2,3,0,0,0], m=3, nums2=[2,5,6], n=3 -> [1,2,2,3,5,6]
    nums1=[1], m=1, nums2=[] -> [1]
    nums1=[0], m=0, nums2=[1] -> [1]

Constraints:
- 0 <= m, n <= 200
- 1 <= m + n <= 200
- nums1.length == m + n
- nums2.length == n

KEY INSIGHT:
Three pointers from the END.
- p1 = m-1 (last valid in nums1).
- p2 = n-1 (last in nums2).
- p = m+n-1 (write position in nums1).
Compare nums1[p1] vs nums2[p2], write larger to nums1[p].
Move pointers backward. No extra space needed.

Time:  O(m+n).
Space: O(1) — in-place.
"""


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT MERGE SORTED ARRAY:

1. UNDERSTAND THE PROBLEM:
   "Merge nums1 (with trailing zeros) and nums2 in-place, sorted.
   nums1 has length m+n; first m are valid, last n are zeros to overwrite."

2. KEY OBSERVATION:
   "If we merge from the FRONT, we'd overwrite nums1's valid data
   we haven't read yet. Merging from the BACK avoids this."

3. THREE-POINTER TECHNIQUE:
   "p1 = m-1: walks nums1's valid region backward.
    p2 = n-1: walks nums2 backward.
    p = m+n-1: write position in nums1's total length.
    At each step, place the larger of nums1[p1], nums2[p2] at nums1[p]."

4. WHY BACKWARD MERGE:
   "The end of nums1 has empty slots. We can fill them with the
   largest remaining elements without disturbing unprocessed data."

5. ALGORITHM:
   "p1=m-1, p2=n-1, p=m+n-1.
    While p1>=0 and p2>=0:
      if nums1[p1] > nums2[p2]: nums1[p]=nums1[p1]; p1--.
      else: nums1[p]=nums2[p2]; p2--.
      p--.
    Drain remaining nums2 (if any) to nums1[p..0]."

6. EDGE CASES:
   - nums2 empty: nums1 unchanged.
   - m=0: just copy nums2 to nums1.
   - nums1 fully consumed: just copy remaining nums2.
   - nums2 fully consumed: nums1's remaining stays.

7. COMPLEXITY:
   +----------+--------+--------+
   | Approach | Time   | Space  |
   +----------+--------+--------+
   | 3-ptr back | O(m+n) | O(1) |
   | New array | O(m+n) | O(m+n)|
   | Front ptr | O(m+n) | O(m+n)|
   +----------+--------+--------+

8. WHY THREE POINTERS:
   - O(1) space (no extra array).
   - Single pass.
   - In-place merge (LeetCode requirement).
"""


# =============================================================================
# WAY 1: Three-pointer from end (BEST - Memorize!)
# =============================================================================
def merge_1(nums1, m, nums2, n):
    """
    Three pointers from end. Place largest at nums1[p] backward.
    In-place, O(1) space.
    """
    p1, p2, p = m - 1, n - 1, m + n - 1
    while p1 >= 0 and p2 >= 0:
        if nums1[p1] > nums2[p2]:
            nums1[p] = nums1[p1]
            p1 -= 1
        else:
            nums1[p] = nums2[p2]
            p2 -= 1
        p -= 1
    # Drain remaining nums2 (if any).
    while p2 >= 0:
        nums1[p] = nums2[p2]
        p -= 1
        p2 -= 1
    return nums1


# =============================================================================
# WAY 2: Three-pointer from end (slight variant)
# =============================================================================
def merge_2(nums1, m, nums2, n):
    """Same idea but cleaner with explicit comparison."""
    p1, p2, p = m - 1, n - 1, m + n - 1
    while p2 >= 0:
        if p1 >= 0 and nums1[p1] > nums2[p2]:
            nums1[p] = nums1[p1]
            p1 -= 1
        else:
            nums1[p] = nums2[p2]
            p2 -= 1
        p -= 1
    return nums1


# =============================================================================
# WAY 3: Use extra array, copy back
# =============================================================================
def merge_3(nums1, m, nums2, n):
    """Use extra array. Simpler but O(m+n) space."""
    merged = []
    i, j = 0, 0
    while i < m and j < n:
        if nums1[i] <= nums2[j]:
            merged.append(nums1[i])
            i += 1
        else:
            merged.append(nums2[j])
            j += 1
    merged.extend(nums1[i:m])
    merged.extend(nums2[j:n])
    for k in range(len(merged)):
        nums1[k] = merged[k]
    return nums1


# =============================================================================
# WAY 4: Two-pointer from front, shift nums1
# =============================================================================
def merge_4(nums1, m, nums2, n):
    """Merge from front. Shift nums1 elements as needed. O(m+n) but slower."""
    i, j = 0, 0
    while j < n:
        if i < m and nums1[i] <= nums2[j]:
            i += 1
        else:
            # Insert nums2[j] at position i, shift rest.
            nums1[i:m + 1] = [nums2[j]] + nums1[i:m]
            i += 1
            m += 1
            j += 1
    return nums1


# =============================================================================
# WAY 5: While loop variant
# =============================================================================
def merge_5(nums1, m, nums2, n):
    """Same as Way 1 but with while and explicit counter."""
    p = m + n - 1
    p1 = m - 1
    p2 = n - 1
    while p1 >= 0 and p2 >= 0:
        if nums1[p1] >= nums2[p2]:
            nums1[p] = nums1[p1]
            p1 -= 1
        else:
            nums1[p] = nums2[p2]
            p2 -= 1
        p -= 1
    # Copy remaining nums2.
    nums1[: p2 + 1] = nums2[: p2 + 1]
    return nums1


# =============================================================================
# WAY 6: heapq.merge for streaming
# =============================================================================
def merge_6(nums1, m, nums2, n):
    """Use heapq.merge (streaming). Copy back to nums1."""
    import heapq
    merged = list(heapq.merge(nums1[:m], nums2))
    for k in range(len(merged)):
        nums1[k] = merged[k]
    return nums1


# =============================================================================
# WAY 7: Sort after appending
# =============================================================================
def merge_7(nums1, m, nums2, n):
    """Append nums2's valid portion, then sort nums1's full length."""
    nums1[m:m + n] = nums2
    nums1.sort()
    return nums1


# =============================================================================
# WAY 8: Class OOP
# =============================================================================
class SortedMerger:
    def __init__(self, nums1, m, nums2, n):
        self.nums1 = nums1
        self.m = m
        self.nums2 = nums2
        self.n = n

    def merge(self):
        p1, p2, p = self.m - 1, self.n - 1, self.m + self.n - 1
        while p1 >= 0 and p2 >= 0:
            if self.nums1[p1] > self.nums2[p2]:
                self.nums1[p] = self.nums1[p1]
                p1 -= 1
            else:
                self.nums1[p] = self.nums2[p2]
                p2 -= 1
            p -= 1
        while p2 >= 0:
            self.nums1[p] = self.nums2[p2]
            p -= 1
            p2 -= 1
        return self.nums1


def merge_8(nums1, m, nums2, n):
    return SortedMerger(nums1, m, nums2, n).merge()


# =============================================================================
# WAY 9: Use sorted() with chain
# =============================================================================
def merge_9(nums1, m, nums2, n):
    """Use sorted on combined (just the relevant elements)."""
    nums1[:m + n] = sorted(nums1[:m] + nums2[:n])
    return nums1


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def merge_10(nums1, m, nums2, n):
    """
    THE ONE TO MEMORIZE.

    Three pointers from end. Place largest at nums1[p] working backward.
    After main loop, copy remaining nums2.

    Time:  O(m+n).
    Space: O(1).
    """
    p1, p2, p = m - 1, n - 1, m + n - 1
    while p1 >= 0 and p2 >= 0:
        if nums1[p1] > nums2[p2]:
            nums1[p] = nums1[p1]
            p1 -= 1
        else:
            nums1[p] = nums2[p2]
            p2 -= 1
        p -= 1
    # Drain remaining nums2.
    nums1[:p2 + 1] = nums2[:p2 + 1]
    return nums1


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: 3-ptr back (BEST)", merge_1),
        ("Way 2: 3-ptr back variant", merge_2),
        ("Way 3: Extra array", merge_3),
        ("Way 4: Front insert shift", merge_4),
        ("Way 5: While loop", merge_5),
        ("Way 6: heapq.merge", merge_6),
        ("Way 7: Append+sort", merge_7),
        ("Way 8: Class OOP", merge_8),
        ("Way 9: sorted combined", merge_9),
        ("Way 10: Final cleanest", merge_10),
    ]

    test_cases = [
        # (nums1, m, nums2, n, expected)
        ([1, 2, 3, 0, 0, 0], 3, [2, 5, 6], 3, [1, 2, 2, 3, 5, 6]),
        ([1], 1, [], 0, [1]),
        ([0], 0, [1], 1, [1]),
        ([4, 5, 6, 0, 0, 0], 3, [1, 2, 3], 3, [1, 2, 3, 4, 5, 6]),
        ([1, 2, 3, 0, 0, 0, 0], 3, [4, 5, 6, 7], 4, [1, 2, 3, 4, 5, 6, 7]),
        ([2, 0], 1, [1], 1, [1, 2]),
        ([-1, 0, 0, 3, 3, 3, 0, 0], 6, [1, 2], 2, [-1, 0, 0, 1, 2, 3, 3, 3]),
        ([0, 0, 0], 0, [1, 2, 3], 3, [1, 2, 3]),
    ]

    print("=" * 70)
    print("MERGE SORTED ARRAY - 10 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/merge-sorted-array")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for inp1, m, inp2, n, expected in test_cases:
            try:
                nums1_copy = list(inp1)
                nums2_copy = list(inp2)
                func(nums1_copy, m, nums2_copy, n)
                if nums1_copy != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: expected={expected}, got={nums1_copy}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
