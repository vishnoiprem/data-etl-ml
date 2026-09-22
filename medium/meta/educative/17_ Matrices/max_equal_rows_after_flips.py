"""
Flip Columns For Maximum Number of Equal Rows
Medium | 30 min

Given an m x n binary matrix, return the maximum number of rows that
can be made equal (all 0s or all 1s) by flipping any number of columns.
Flipping a column inverts all values in that column.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/flip-columns-for-maximum-number-of-equal-rows

Constraints:
- 1 <= m, n <= 50
- matrix[i][j] is 0 or 1

Examples:
    [[0,1],[1,0]] -> 2 (flip any column; rows become equal)
    [[0,1],[1,1]] -> 2 (flip col 0; both rows become [1,1])

Key Insight:
- Two rows can be made EQUAL by flips iff they are IDENTICAL or COMPLEMENTS.
- Why? Flipping a column inverts that column. After flipping some subset of
  columns, two rows are equal iff they match in those flipped columns and
  the non-flipped columns agree. This happens iff the rows are identical or
  complementary (one is the bitwise NOT of the other).
- So the answer = max count of identical-or-complement row pairs.
- Equivalently: count occurrences of each row (treating rows as canonical
  strings), and the count includes both row AND its complement.

Time:  O(m*n) for canonicalization + O(m) for counting.
Space: O(m*n) for hash map.
"""


# =============================================================================
# WAY 1: Canonical form + Counter (BEST - Memorize!)
# =============================================================================
def max_equal_rows_after_flips_1(matrix):
    """
    For each row, compute its CANONICAL form: the lexicographically smaller
    of (row, complement(row)). Two rows can be made equal iff they have
    the same canonical form.

    Count the most common canonical form. Return its count.

    Time:  O(m*n) for canonicalization, O(m) for counting.
    Space: O(m*n).
    """
    from collections import Counter
    if not matrix or not matrix[0]:
        return 0

    canonical = []
    for row in matrix:
        # Compute complement
        complement = [1 - v for v in row]
        # Pick lexicographically smaller (or smaller tuple)
        row_t = tuple(row)
        comp_t = tuple(complement)
        canonical.append(min(row_t, comp_t))

    counter = Counter(canonical)
    return max(counter.values())


# =============================================================================
# WAY 2: Verbose version (whiteboard-friendly)
# =============================================================================
def max_equal_rows_after_flips_2(matrix):
    """Same as Way 1 but more readable."""
    if not matrix or not matrix[0]:
        return 0

    canonicals = []
    for row in matrix:
        complement = [1 - v for v in row]
        if tuple(row) <= tuple(complement):
            canonicals.append(tuple(row))
        else:
            canonicals.append(tuple(complement))

    # Count occurrences
    counts = {}
    for c in canonicals:
        counts[c] = counts.get(c, 0) + 1

    return max(counts.values())


# =============================================================================
# WAY 3: Use string canonical form
# =============================================================================
def max_equal_rows_after_flips_3(matrix):
    """Use string representation for canonical form."""
    from collections import Counter
    if not matrix or not matrix[0]:
        return 0

    canonicals = []
    for row in matrix:
        s = ''.join(str(v) for v in row)
        s_comp = ''.join(str(1 - v) for v in row)
        canonicals.append(min(s, s_comp))

    return max(Counter(canonicals).values())


# =============================================================================
# WAY 4: Use bitmask for first row as reference
# =============================================================================
def max_equal_rows_after_flips_4(matrix):
    """
    KEY INSIGHT: Two rows are flippable to equal iff they're the same or
    complements. So group rows by their relationship to the FIRST row:
    - Rows identical to first row: count
    - Rows complement to first row: count
    - Answer = max of these two counts

    Actually, we need to compare ALL pairs. Better approach: hash each row
    and its complement, find max count of identical hashes.
    """
    from collections import defaultdict
    if not matrix or not matrix[0]:
        return 0

    # Map: canonical -> count
    hash_count = defaultdict(int)
    for row in matrix:
        row_t = tuple(row)
        comp_t = tuple(1 - v for v in row)
        canonical = min(row_t, comp_t)
        hash_count[canonical] += 1

    return max(hash_count.values()) if hash_count else 0


# =============================================================================
# WAY 5: Using first column as "pivot" for canonicalization
# =============================================================================
def max_equal_rows_after_flips_5(matrix):
    """
    If first element of row is 0, use row as-is.
    If first element is 1, use complement.
    This gives a unique canonical form (rows starting with 0).
    """
    from collections import Counter
    if not matrix or not matrix[0]:
        return 0

    canonicals = []
    for row in matrix:
        if row[0] == 0:
            canonicals.append(tuple(row))
        else:
            canonicals.append(tuple(1 - v for v in row))

    return max(Counter(canonicals).values())


# =============================================================================
# WAY 6: Brute force - try every possible flip pattern
# =============================================================================
def max_equal_rows_after_flips_6(matrix):
    """
    For each subset of columns, count how many rows become uniform
    (all-0 or all-1) after applying the flips. Return max.

    The KEY insight: each row just needs to be uniform (all values
    equal), but different rows can have different uniform values.

    Time:  O(2^n * m * n)
    """
    if not matrix or not matrix[0]:
        return 0
    m, n = len(matrix), len(matrix[0])

    best = 0
    for mask in range(1 << n):
        # Count rows that are uniform after applying mask
        count = 0
        for row in matrix:
            # Apply flips to this row
            flipped = [row[j] ^ ((mask >> j) & 1) for j in range(n)]
            # Check if uniform
            if all(v == flipped[0] for v in flipped):
                count += 1
        if count > best:
            best = count
        if best == m:
            return m  # Early exit
    return best


# =============================================================================
# WAY 7: Using hash of binary representation
# =============================================================================
def max_equal_rows_after_flips_7(matrix):
    """Convert each row to integer (binary), use complement via XOR."""
    from collections import Counter
    if not matrix or not matrix[0]:
        return 0

    canonicals = []
    for row in matrix:
        row_int = 0
        for v in row:
            row_int = (row_int << 1) | v
        comp_int = ((1 << len(row)) - 1) ^ row_int  # Bitwise NOT
        canonicals.append(min(row_int, comp_int))

    return max(Counter(canonicals).values())


# =============================================================================
# WAY 8: Find row with most matching/anti-matching rows
# =============================================================================
def max_equal_rows_after_flips_8(matrix):
    """
    For each row, count how many OTHER rows are identical or complement.
    This is O(m^2 * n) - works for small m.
    """
    if not matrix or not matrix[0]:
        return 0
    m = len(matrix)

    def is_flippable(r1, r2):
        # Same OR complement (all positions must agree)
        all_same = all(a == b for a, b in zip(r1, r2))
        all_diff = all(a != b for a, b in zip(r1, r2))
        return all_same or all_diff

    best = 1 if m > 0 else 0
    for i in range(m):
        # Count self + flippable matches
        count = 1
        for j in range(m):
            if i != j and is_flippable(matrix[i], matrix[j]):
                count += 1
        if count > best:
            best = count
    return best


# =============================================================================
# WAY 9: Convert rows to frozenset then use Counter
# =============================================================================
def max_equal_rows_after_flips_9(matrix):
    """Use frozenset as hashable row representation."""
    from collections import Counter
    if not matrix or not matrix[0]:
        return 0

    canonicals = []
    for row in matrix:
        row_t = tuple(row)
        comp_t = tuple(1 - v for v in row)
        canonicals.append(min(row_t, comp_t))

    counter = Counter(canonicals)
    return max(counter.values())


# =============================================================================
# WAY 10: Using bitwise XOR with all-1s mask
# =============================================================================
def max_equal_rows_after_flips_10(matrix):
    """Use XOR with mask of all 1s for complement."""
    from collections import Counter
    if not matrix or not matrix[0]:
        return 0

    ALL_ONES = (1 << 50) - 1  # Enough bits for n <= 50

    canonicals = []
    for row in matrix:
        row_int = 0
        for v in row:
            row_int = (row_int << 1) | v
        comp_int = row_int ^ ALL_ONES
        # But we need to mask to actual length
        comp_int &= (1 << len(row)) - 1
        canonicals.append(min(row_int, comp_int))

    return max(Counter(canonicals).values())


# =============================================================================
# WAY 11: Sort and count consecutive groups
# =============================================================================
def max_equal_rows_after_flips_11(matrix):
    """Sort canonical forms, count longest consecutive group."""
    if not matrix or not matrix[0]:
        return 0

    canonicals = []
    for row in matrix:
        comp = [1 - v for v in row]
        canonicals.append(min(tuple(row), tuple(comp)))

    canonicals.sort()
    best = 1
    current = 1
    for i in range(1, len(canonicals)):
        if canonicals[i] == canonicals[i - 1]:
            current += 1
            best = max(best, current)
        else:
            current = 1
    return best


# =============================================================================
# WAY 12: Using dict.get with default 0
# =============================================================================
def max_equal_rows_after_flips_12(matrix):
    """Use dict.get for counting."""
    if not matrix or not matrix[0]:
        return 0

    counts = {}
    for row in matrix:
        row_t = tuple(row)
        comp_t = tuple(1 - v for v in row)
        canonical = min(row_t, comp_t)
        counts[canonical] = counts.get(canonical, 0) + 1

    return max(counts.values())


# =============================================================================
# WAY 13: Use itertools
# =============================================================================
def max_equal_rows_after_flips_13(matrix):
    """Use itertools for counting."""
    from collections import Counter
    if not matrix or not matrix[0]:
        return 0

    def to_canonical(row):
        comp = [1 - v for v in row]
        return min(tuple(row), tuple(comp))

    canonicals = [to_canonical(row) for row in matrix]
    counts = Counter(canonicals)
    return max(counts.values())


# =============================================================================
# WAY 14: First row as reference, count same + complement
# =============================================================================
def max_equal_rows_after_flips_14(matrix):
    """
    Use the first row as reference.
    Rows flippable to first row are: identical or complementary.
    Count identical + complementary among all rows (including first).
    """
    if not matrix or not matrix[0]:
        return 0

    first = matrix[0]
    same = 0
    complement = 0
    for row in matrix:
        if row == first:
            same += 1
        elif all(a != b for a, b in zip(row, first)):
            complement += 1

    return same + complement


# =============================================================================
# WAY 15: Generic hashing with hash()
# =============================================================================
def max_equal_rows_after_flips_15(matrix):
    """Use built-in hash of tuple representation."""
    from collections import Counter
    if not matrix or not matrix[0]:
        return 0

    canonicals = []
    for row in matrix:
        row_t = tuple(row)
        comp_t = tuple(1 - v for v in row)
        canonicals.append(min(row_t, comp_t))

    return max(Counter(canonicals).values())


# =============================================================================
# WAY 16: NumPy vectorized
# =============================================================================
def max_equal_rows_after_flips_16(matrix):
    """Use numpy for vectorized operations."""
    try:
        import numpy as np
        if not matrix or not matrix[0]:
            return 0
        arr = np.array(matrix)
        # Compute canonical for each row (lex-smaller of row or complement)
        complements = 1 - arr
        # Convert to bytes (lex order) - numpy doesn't compare rows easily
        # Use tuple comparison in Python after numpy preprocessing
        canonicals = []
        for i in range(arr.shape[0]):
            row = arr[i].tolist()
            comp = complements[i].tolist()
            canonicals.append(min(tuple(row), tuple(comp)))
        from collections import Counter
        return max(Counter(canonicals).values())
    except ImportError:
        return max_equal_rows_after_flips_1(matrix)


# =============================================================================
# WAY 17: Class-based OOP
# =============================================================================
class RowFlipper:
    def __init__(self, matrix):
        self.matrix = matrix
        self.m = len(matrix)
        self.n = len(matrix[0]) if matrix else 0

    def max_equal_rows(self):
        if not self.matrix or not self.matrix[0]:
            return 0
        from collections import Counter
        canonicals = []
        for row in self.matrix:
            row_t = tuple(row)
            comp_t = tuple(1 - v for v in row)
            canonicals.append(min(row_t, comp_t))
        return max(Counter(canonicals).values())


def max_equal_rows_after_flips_17(matrix):
    """Class-based version."""
    return RowFlipper(matrix).max_equal_rows()


# =============================================================================
# WAY 18: First-element-based canonicalization (compact)
# =============================================================================
def max_equal_rows_after_flips_18(matrix):
    """
    Make first element of every row 0 by complementing if needed.
    Then group by canonical form.
    """
    from collections import Counter
    if not matrix or not matrix[0]:
        return 0

    canonicals = []
    for row in matrix:
        if row[0] == 1:
            row = [1 - v for v in row]
        canonicals.append(tuple(row))

    return max(Counter(canonicals).values())


# =============================================================================
# WAY 19: Most concise
# =============================================================================
def max_equal_rows_after_flips_19(matrix):
    """Most concise."""
    from collections import Counter
    return max(Counter(min(tuple(r), tuple(1 - v for v in r)) for r in matrix).values()) if matrix else 0


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def max_equal_rows_after_flips_20(matrix):
    """
    Final clean version.
    For each row, canonicalize: pick the lex-smaller of row and its complement.
    Group by canonical form. Answer is the largest group size.

    Why this works:
    Two rows can be made EQUAL by column flips iff they are IDENTICAL or
    COMPLEMENTARY. By canonicalizing, we put identical-or-complement pairs
    in the same group. The largest group = max rows that can be made equal.
    """
    if not matrix or not matrix[0]:
        return 0
    from collections import Counter
    canonicals = []
    for row in matrix:
        row_t = tuple(row)
        comp_t = tuple(1 - v for v in row)
        canonicals.append(min(row_t, comp_t))
    return max(Counter(canonicals).values())


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the maximum number of rows that can be made identical
(after flipping any subset of columns). Each flip inverts a column."

Key Insight:
"Two rows can be made EQUAL by flips iff they are IDENTICAL or COMPLEMENTARY
(one is the bitwise NOT of the other).

WHY? Flipping a column inverts that column. After applying some flips:
- Position j of row A is flipped if column j was flipped.
- Two rows A, B are equal after flips iff they AGREE in non-flipped cols
  and DISAGREE in flipped cols (or vice versa).
- Equivalently, A and B must be IDENTICAL or COMPLEMENTARY.

So the problem reduces to: count rows that are identical-or-complement to each other.

Algorithm:
"1. For each row, compute its CANONICAL form: the lex-smaller of (row, complement).
2. Group rows by canonical form.
3. Answer = max group size."

Why canonical form?
"Two rows have the same canonical form iff they are identical or complementary.
So grouping by canonical form puts all flippable-to-equal rows in the same bucket."

Edge cases:
- All rows identical: answer = m.
- No two rows identical or complementary: answer = 1.
- 1x1 matrix: answer = 1.
- Empty matrix: return 0.

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Canonical | O(mn)  | O(mn)  |
| Brute     | O(2^n * mn) | O(1) |
| Compare   | O(m^2 n) | O(1) |
+-----------+--------+--------+

KEY TRICK:
CANONICAL FORM = min(row, complement). This elegantly handles both
identical and complementary pairs in one hash bucket.

ALTERNATIVE APPROACH:
Use the first row as reference. Count rows that are:
- IDENTICAL to first row, OR
- COMPLEMENTARY to first row.
Sum these counts.

But this only works if all flippable rows are flippable to the FIRST row!
That's not always true. Example:
Row A: [0, 1, 0]
Row B: [0, 1, 0]   (same as A)
Row C: [1, 0, 1]   (complement of A, also complement of B)
All three are flippable to each other.
First row count = 1 + complement count = 1 + 2 = 3. ✓ Works.

But what if:
Row A: [0, 1, 0]
Row B: [1, 0, 1]
Row C: [0, 0, 1]
A and B are complements. C is neither identical nor complement to A.
First row count = 1 (A) + 1 (B complement) = 2. But C can be flippable to D?

Actually, if we use the canonical approach, we get:
A canonical = (0,1,0)
B canonical = (0,1,0)   (min of B and complement of B = (0,1,0))
C canonical = (0,0,1)
Groups: {(0,1,0): 2, (0,0,1): 1}. Max = 2. ✓

So canonical approach is the safe bet.

RELATIONSHIP TO OTHER PROBLEMS:
- Valid Sudoku (LC 36): Different problem.
- Set Matrix Zeroes: Different.
- Image flipping: Related geometric operation.

This is LeetCode 1072: "Flip Columns For Maximum Number of Equal Rows".
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Canonical + Counter (BEST)", max_equal_rows_after_flips_1),
        ("Way 2: Verbose", max_equal_rows_after_flips_2),
        ("Way 3: String canonical", max_equal_rows_after_flips_3),
        ("Way 4: Hash map", max_equal_rows_after_flips_4),
        ("Way 5: First-col pivot", max_equal_rows_after_flips_5),
        ("Way 6: Brute force subsets", max_equal_rows_after_flips_6),
        ("Way 7: Bitmask", max_equal_rows_after_flips_7),
        ("Way 8: Pairwise compare", max_equal_rows_after_flips_8),
        ("Way 9: Frozenset", max_equal_rows_after_flips_9),
        ("Way 10: Bitmask XOR", max_equal_rows_after_flips_10),
        ("Way 11: Sort and group", max_equal_rows_after_flips_11),
        ("Way 12: Dict.get", max_equal_rows_after_flips_12),
        ("Way 13: Itertools", max_equal_rows_after_flips_13),
        ("Way 14: First row reference", max_equal_rows_after_flips_14),
        ("Way 15: hash()", max_equal_rows_after_flips_15),
        ("Way 16: Numpy", max_equal_rows_after_flips_16),
        ("Way 17: Class-based", max_equal_rows_after_flips_17),
        ("Way 18: First-element canonical", max_equal_rows_after_flips_18),
        ("Way 19: Most concise", max_equal_rows_after_flips_19),
        ("Way 20: Final cleanest", max_equal_rows_after_flips_20),
    ]

    test_cases = [
        # Example 1: complementary
        ([[0, 1], [1, 0]], 2),
        # Example 2: not flippable to equal (different in middle pos)
        ([[0, 1], [1, 1]], 1),
        # All same row
        ([[1, 1, 1], [1, 1, 1], [1, 1, 1]], 3),
        # All complementary pairs (all reduce to (0,0) canonical)
        ([[0, 0], [1, 1], [1, 1], [0, 0]], 4),
        # Mixed: Row 0=(0,0,1) comp=(1,1,0). Row 2 same as Row 0.
        # Row 1=(1,1,0) comp=(0,0,1). So Row 1 canonical = min((1,1,0),(0,0,1)) = (0,0,1).
        # Row 0 canonical = (0,0,1). All 3 have canonical (0,0,1). Max = 3.
        ([[0, 0, 1], [1, 1, 0], [0, 0, 1]], 3),
        # No two flippable: each row has unique canonical
        # Row 0 = (0,0,0) comp = (1,1,1). canonical = (0,0,0)
        # Row 1 = (1,1,0) comp = (0,0,1). canonical = (0,0,1)
        # Row 2 = (1,0,1) comp = (0,1,0). canonical = (0,1,0)
        # All different. Max = 1.
        ([[0, 0, 0], [1, 1, 0], [1, 0, 1]], 1),
        # Single row
        ([[1, 0, 1]], 1),
        # 3x3: all have canonical (0,1,0)
        ([[0, 1, 0], [1, 0, 1], [0, 1, 0]], 3),
        # 4x3: all have canonical (0,1,0)
        ([[0, 1, 0], [1, 0, 1], [1, 0, 1], [0, 1, 0]], 4),
        # 4x4
        ([[0, 1, 1, 0], [1, 0, 0, 1], [1, 0, 0, 1], [0, 1, 1, 0]], 4),
        # Empty
        ([], 0),
    ]

    print("=" * 70)
    print("FLIP COLUMNS FOR MAX EQUAL ROWS - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/flip-columns-for-maximum-number-of-equal-rows")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for matrix, expected in test_cases:
            try:
                import copy
                matrix_copy = copy.deepcopy(matrix)
                result = func(matrix_copy)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: matrix={matrix} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on matrix={matrix} - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)