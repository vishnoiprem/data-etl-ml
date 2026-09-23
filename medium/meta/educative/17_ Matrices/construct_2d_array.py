"""
Convert 1D Array Into 2D Array
Easy | 15 min

Given a 0-indexed 1D integer array `original` and two integers `m` and
`n`, reshape the array into a 2D array with m rows and n columns while
preserving the order of elements. The first n elements populate the
first row, the next n the second row, etc.

If original.length != m * n, return an empty array.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/convert-1d-array-into-2d-array

Constraints:
- 1 <= original.length <= 10^3
- 1 <= original[i] <= 10^3
- 1 <= m, n <= 33

Examples:
    [1,2,3,4], m=2, n=2 -> [[1,2],[3,4]]
    [1,2,3], m=1, n=3 -> [[1,2,3]]
    [1,2,3], m=3, n=1 -> [[1],[2],[3]]
    [1,2,3], m=2, n=2 -> []  (3 != 4)

Key Insight:
- Check: len(original) == m * n. If not, return [].
- For each row i in [0, m), take original[i*n : i*n+n].

Time:  O(m*n).
Space: O(m*n) for the result.
"""


# =============================================================================
# WAY 1: List comprehension slicing (BEST - Memorize!)
# =============================================================================
def construct_2d_array_1(original, m, n):
    """
    Use list comprehension to slice original into chunks of size n.
    """
    if len(original) != m * n:
        return []
    return [original[i * n:(i + 1) * n] for i in range(m)]


# =============================================================================
# WAY 2: Build row by row with explicit index
# =============================================================================
def construct_2d_array_2(original, m, n):
    """Build row by row using a for loop."""
    if len(original) != m * n:
        return []
    result = []
    for i in range(m):
        row = []
        for j in range(n):
            row.append(original[i * n + j])
        result.append(row)
    return result


# =============================================================================
# WAY 3: Use enumerate with chunks
# =============================================================================
def construct_2d_array_3(original, m, n):
    """Enumerate over chunks of size n."""
    if len(original) != m * n:
        return []
    result = []
    for i in range(m):
        chunk = original[i * n:(i + 1) * n]
        result.append(list(chunk))
    return result


# =============================================================================
# WAY 4: Using zip to group into n-element rows
# =============================================================================
def construct_2d_array_4(original, m, n):
    """Use zip with strict grouping."""
    if len(original) != m * n:
        return []
    it = iter(original)
    return [list(chunk) for chunk in zip(*[it] * n)]


# =============================================================================
# WAY 5: Using list slicing with step
# =============================================================================
def construct_2d_array_5(original, m, n):
    """Slice with step."""
    if len(original) != m * n:
        return []
    return [original[i:i + n] for i in range(0, m * n, n)]


# =============================================================================
# WAY 6: Using iter() and islice
# =============================================================================
def construct_2d_array_6(original, m, n):
    """Use itertools.islice."""
    from itertools import islice
    if len(original) != m * n:
        return []
    it = iter(original)
    result = []
    for _ in range(m):
        result.append(list(islice(it, n)))
    return result


# =============================================================================
# WAY 7: Use numpy reshape
# =============================================================================
def construct_2d_array_7(original, m, n):
    """Use numpy reshape."""
    try:
        import numpy as np
        if len(original) != m * n:
            return []
        return np.array(original).reshape(m, n).tolist()
    except ImportError:
        return construct_2d_array_1(original, m, n)


# =============================================================================
# WAY 8: Pre-allocate result matrix
# =============================================================================
def construct_2d_array_8(original, m, n):
    """Pre-allocate result matrix and fill it."""
    if len(original) != m * n:
        return []
    result = [[0] * n for _ in range(m)]
    for i in range(m):
        for j in range(n):
            result[i][j] = original[i * n + j]
    return result


# =============================================================================
# WAY 9: Using map with operator.itemgetter
# =============================================================================
def construct_2d_array_9(original, m, n):
    """Use operator.itemgetter."""
    from operator import itemgetter
    if len(original) != m * n:
        return []
    if n == 1:
        return [[original[i]] for i in range(m)]
    return [list(itemgetter(*range(i * n, (i + 1) * n))(original))
            for i in range(m)]


# =============================================================================
# WAY 10: Use zip(*[iter(original)]*n) idiom
# =============================================================================
def construct_2d_array_10(original, m, n):
    """Classic Python chunking idiom."""
    if len(original) != m * n:
        return []
    return [list(c) for c in zip(*[iter(original)] * n)]


# =============================================================================
# WAY 11: Class-based solution
# =============================================================================
class ArrayReshaper:
    def __init__(self, original, m, n):
        self.original = original
        self.m = m
        self.n = n

    def can_reshape(self):
        return len(self.original) == self.m * self.n

    def reshape(self):
        if not self.can_reshape():
            return []
        result = []
        for i in range(self.m):
            start = i * self.n
            end = start + self.n
            result.append(self.original[start:end])
        return result


def construct_2d_array_11(original, m, n):
    """Class-based solution."""
    return ArrayReshaper(original, m, n).reshape()


# =============================================================================
# WAY 12: Functional with map
# =============================================================================
def construct_2d_array_12(original, m, n):
    """Functional with map."""
    if len(original) != m * n:
        return []
    return list(map(list, zip(*[iter(original)] * n)))


# =============================================================================
# WAY 13: Using lambda
# =============================================================================
def construct_2d_array_13(original, m, n):
    """Using lambda for slicing."""
    if len(original) != m * n:
        return []
    get_row = lambda i: original[i * n:(i + 1) * n]
    return [get_row(i) for i in range(m)]


# =============================================================================
# WAY 14: Recursive slicing
# =============================================================================
def construct_2d_array_14(original, m, n):
    """Recursive slicing."""
    if len(original) != m * n:
        return []
    if m == 0:
        return []
    return [original[:n]] + construct_2d_array_14(original[n:], m - 1, n)


# =============================================================================
# WAY 15: Using collections.deque
# =============================================================================
def construct_2d_array_15(original, m, n):
    """Use deque for efficient pops from left."""
    from collections import deque
    if len(original) != m * n:
        return []
    d = deque(original)
    result = []
    for _ in range(m):
        row = []
        for _ in range(n):
            row.append(d.popleft())
        result.append(row)
    return result


# =============================================================================
# WAY 16: Generator-based
# =============================================================================
def construct_2d_array_16(original, m, n):
    """Generator-based approach."""
    if len(original) != m * n:
        return []

    def gen():
        for i in range(m):
            yield original[i * n:(i + 1) * n]

    return [row for row in gen()]


# =============================================================================
# WAY 17: Use range with index calculation
# =============================================================================
def construct_2d_array_17(original, m, n):
    """Index calculation approach."""
    if len(original) != m * n:
        return []
    result = []
    for i in range(m):
        start = i * n
        result.append(list(original[start:start + n]))
    return result


# =============================================================================
# WAY 18: Use enumerate on row indices
# =============================================================================
def construct_2d_array_18(original, m, n):
    """Enumerate row indices."""
    if len(original) != m * n:
        return []
    result = []
    for i, _ in enumerate(range(m)):
        result.append(original[i * n:(i + 1) * n])
    return result


# =============================================================================
# WAY 19: One-liner
# =============================================================================
def construct_2d_array_19(original, m, n):
    """One-liner style."""
    if len(original) != m * n:
        return []
    return [original[i * n:(i + 1) * n] for i in range(m)]


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def construct_2d_array_20(original, m, n):
    """
    Final clean version.
    1. Check if reshape is possible: len(original) == m * n.
    2. If not, return [].
    3. Otherwise, slice original into chunks of size n.

    Time:  O(m*n)
    Space: O(m*n)
    """
    if len(original) != m * n:
        return []
    return [original[i * n:(i + 1) * n] for i in range(m)]


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to reshape a 1D array into a 2D array with m rows and n columns."

Key Insight:
"First, check if reshape is possible: len(original) == m * n.
If not, return empty. Otherwise, slice the array into chunks of n."

Algorithm:
"1. If len(original) != m * n: return [].
2. For each row i in [0, m): result[i] = original[i*n : (i+1)*n]
3. Return result."

Why this works:
"The 1D array fills the 2D array row by row, left to right.
Row i contains elements at indices i*n, i*n+1, ..., i*n+n-1.
So row i = original[i*n : (i+1)*n]."

Edge cases:
- Empty original with m=0 or n=0: return [] (since len=0 != m*n if m,n>0).
- original.length == m*n: reshape.
- 1x1 result: return [[original[0]]].
- Single row (m=1): one chunk.

Complexity:
- Time:  O(m*n) - linear in number of elements.
- Space: O(m*n) - for the result.

KEY TRICK:
Slicing original[i*n : (i+1)*n] is the cleanest approach.
Alternative: zip(*[iter(original)]*n) is the Python chunking idiom.

ALTERNATIVE: numpy reshape
arr = np.array(original).reshape(m, n).tolist()
Same idea, but uses numpy for efficient reshaping.

ALTERNATIVE: deque
Pop n elements at a time from the front.
O(n) extra work due to pops, but same complexity.

RELATIONSHIP TO OTHER PROBLEMS:
- Reshape Matrix (LC 566): Similar concept.
- Matrix Flattening (LC 542): Reverse operation.
- Image as 1D Array: Different data structure.

INTERVIEW TIPS:
1. Always mention the size check first.
2. Explain the index calculation: i*n + j.
3. Show slicing cleanly.
4. Discuss numpy as alternative for very large arrays.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: List comprehension slicing (BEST)", construct_2d_array_1),
        ("Way 2: Build row by row", construct_2d_array_2),
        ("Way 3: enumerate with chunks", construct_2d_array_3),
        ("Way 4: zip group", construct_2d_array_4),
        ("Way 5: slice with step", construct_2d_array_5),
        ("Way 6: islice", construct_2d_array_6),
        ("Way 7: numpy reshape", construct_2d_array_7),
        ("Way 8: pre-allocate", construct_2d_array_8),
        ("Way 9: itemgetter", construct_2d_array_9),
        ("Way 10: zip idiom", construct_2d_array_10),
        ("Way 11: Class-based", construct_2d_array_11),
        ("Way 12: Functional map", construct_2d_array_12),
        ("Way 13: Lambda", construct_2d_array_13),
        ("Way 14: Recursive", construct_2d_array_14),
        ("Way 15: deque", construct_2d_array_15),
        ("Way 16: Generator", construct_2d_array_16),
        ("Way 17: Range index", construct_2d_array_17),
        ("Way 18: enumerate", construct_2d_array_18),
        ("Way 19: One-liner", construct_2d_array_19),
        ("Way 20: Final cleanest", construct_2d_array_20),
    ]

    test_cases = [
        # Educative example
        ([1, 2, 3, 4], 2, 2, [[1, 2], [3, 4]]),
        # Single row
        ([1, 2, 3], 1, 3, [[1, 2, 3]]),
        # Single column
        ([1, 2, 3], 3, 1, [[1], [2], [3]]),
        # Impossible (3 != 4)
        ([1, 2, 3], 2, 2, []),
        # 1x1
        ([5], 1, 1, [[5]]),
        # 2x3
        ([1, 2, 3, 4, 5, 6], 2, 3, [[1, 2, 3], [4, 5, 6]]),
        # 3x2
        ([1, 2, 3, 4, 5, 6], 3, 2, [[1, 2], [3, 4], [5, 6]]),
        # 1x4
        ([1, 2, 3, 4], 1, 4, [[1, 2, 3, 4]]),
        # Impossible (large m*n)
        ([1, 2, 3], 5, 5, []),
    ]

    print("=" * 70)
    print("CONVERT 1D ARRAY INTO 2D ARRAY - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/convert-1d-array-into-2d-array")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for original, m, n, expected in test_cases:
            try:
                import copy
                original_copy = copy.deepcopy(original)
                result = func(original_copy, m, n)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: original={original}, m={m}, n={n} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on original={original}, m={m}, n={n} - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)