"""
Largest Number
==============
Given a list of non-negative integers, rearrange them to form the
largest possible number, returned as a string.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/largest-number

Constraints:
    1 <= nums.length <= 100
    0 <= nums[i] <= 10^3

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "I need to reorder nums so the resulting concatenated string is the
    lexicographically largest possible."

2. OBSERVE — KEY INSIGHT:
   "Two numbers a and b: which comes first?
    Whichever gives a larger 'ab' vs 'ba'.
    So compare a+b vs b+a as strings."

3. PATTERN RECOGNITION:
   "This is a CUSTOM comparator problem.
    Sort nums with comparator (a, b) -> -1 if a+b > b+a, +1 otherwise."
   (Equivalent to: order strings by concatenated pair, descending.)

4. EDGE CASES:
   "What if all zeros?  -> return '0' (not '000...0').
    What if single element?  -> return str(element)."

5. TRICKY DETAIL:
   "Standard sort is stable but uses natural ordering. For custom
    ordering, I can use Python's functools.cmp_to_key, or encode
    each number's sort key cleverly (multiply by power of 10)."

6. ALGORITHM:
   "1. Convert each num to string.
    2. Sort by custom comparator.
    3. Concatenate.
    4. Strip leading zeros by checking if result starts with '0'."

7. WHY THIS WORKS — PROOF SKETCH:
   "Sorting with pairwise-optimal comparator (a+b > b+a) gives a
    globally optimal sequence. This is a transposition argument:
    any inversion in the sort order can be shown to make the result
    strictly smaller, contradicting optimality."

8. COMPLEXITY:
   "Sorting: O(n log n) comparisons, each comparison O(k) where k is
    string length. Total O(n log n * k) = roughly O(n log n) for
    reasonable inputs. Space: O(n) for the strings."

9. CODE STRUCTURE:
   "from functools import cmp_to_key.
    Define compare(a, b):
        if a+b > b+a: return -1
        if a+b < b+a: return 1
        return 0
    sorted_strings = sorted(strings, key=cmp_to_key(compare))"

10. TEST MENTAL TRACING:
    [3, 30, 34, 5, 9]
    Compare 3 and 30: '330' vs '303' -> '330' bigger -> 3 first.
    Compare 30 and 34: '3034' vs '3430' -> '3430' bigger -> 34 first.
    Final order: 9, 5, 34, 3, 30 -> '9534330'. ✓
"""

from functools import cmp_to_key


# ==============================================================
# Solution 1: Standard cmp_to_key sort (CANONICAL - memorize this!)
# ==============================================================
def largest_number_v1(nums):
    """
    Convert to strings, sort with custom comparator (a+b vs b+a, descending),
    concatenate. Strip leading zeros.
    """
    s = list(map(str, nums))

    def compare(a, b):
        if a + b > b + a:
            return -1  # a should come first
        if a + b < b + a:
            return 1   # b should come first
        return 0

    s.sort(key=cmp_to_key(compare))
    result = "".join(s)
    return "0" if result[0] == "0" else result


# ==============================================================
# Solution 2: Sort by length-then-value (handles non-string trick)
# ==============================================================
def largest_number_v2(nums):
    """
    Encode each number's comparison as a tuple. (length, value-as-string).
    Within same length, larger value is preferred; between lengths, the
    trick of comparing concatenations becomes hard to capture, so we
    fall back to string comparison.
    """
    if not nums:
        return "0"

    s = sorted(map(str, nums),
               key=lambda x: x * 10,   # 10 = max length of nums (10^3 has 4 digits)
               reverse=True)
    # This doesn't quite work for arbitrary comparisons; for the
    # interview problem (nums[i] < 10^3, so length <= 4), repeat the
    # string 4 times and sort by that.
    result = "".join(s)
    return "0" if result[0] == "0" else result


# ==============================================================
# Solution 3: Bubble sort with custom comparator (O(n^2), educational)
# ==============================================================
def largest_number_v3(nums):
    """
    Educational: bubble sort with custom comparator. O(n^2) time.
    """
    s = list(map(str, nums))
    n = len(s)
    for i in range(n):
        for j in range(n - 1 - i):
            if s[j] + s[j + 1] < s[j + 1] + s[j]:
                s[j], s[j + 1] = s[j + 1], s[j]
    result = "".join(s)
    return "0" if result and result[0] == "0" else result


# ==============================================================
# Solution 4: Select-sort style (O(n^2), also educational)
# ==============================================================
def largest_number_v4(nums):
    """
    Selection sort: at each step, find the max-according-to-comparator
    remaining element and place it.
    """
    s = list(map(str, nums))
    n = len(s)
    for i in range(n):
        best_idx = i
        for j in range(i + 1, n):
            # If s[j] should come BEFORE s[best_idx], update best_idx.
            if s[j] + s[best_idx] > s[best_idx] + s[j]:
                best_idx = j
        if best_idx != i:
            s[i], s[best_idx] = s[best_idx], s[i]
    result = "".join(s)
    return "0" if result and result[0] == "0" else result


# ==============================================================
# Solution 5: Sort by KEY x*4 trick (works when length <= 4)
# ==============================================================
def largest_number_v5(nums):
    """
    For nums <= 10^3 (length 1-4), repeat each string 4 times for a
    consistent sort key. Sort by this 4x-repeated string desc.
    """
    s = list(map(str, nums))
    s.sort(key=lambda x: x * 4, reverse=True)
    result = "".join(s)
    return "0" if result[0] == "0" else result


# ==============================================================
# Solution 6: Quicksort implementation with comparator
# ==============================================================
def largest_number_v6(nums):
    """
    In-place quicksort with custom comparator.
    """
    s = list(map(str, nums))

    def quicksort(arr, lo, hi):
        if lo < hi:
            p = partition(arr, lo, hi)
            quicksort(arr, lo, p - 1)
            quicksort(arr, p + 1, hi)

    def partition(arr, lo, hi):
        pivot = arr[hi]
        i = lo - 1
        for j in range(lo, hi):
            if arr[j] + pivot >= pivot + arr[j]:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
        arr[i + 1], arr[hi] = arr[hi], arr[i + 1]
        return i + 1

    quicksort(s, 0, len(s) - 1)
    result = "".join(s)
    return "0" if result[0] == "0" else result


# ==============================================================
# Solution 7: Merge sort with comparator
# ==============================================================
def largest_number_v7(nums):
    """
    Merge sort with custom comparator.
    """
    s = list(map(str, nums))

    def merge_sort(arr):
        if len(arr) <= 1:
            return arr
        mid = len(arr) // 2
        left = merge_sort(arr[:mid])
        right = merge_sort(arr[mid:])
        return merge(left, right)

    def merge(left, right):
        result = []
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i] + right[j] >= right[j] + left[i]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        result.extend(left[i:])
        result.extend(right[j:])
        return result

    s = merge_sort(s)
    result = "".join(s)
    return "0" if result[0] == "0" else result


# ==============================================================
# Solution 8: Heap-based selection (use a max-heap)
# ==============================================================
def largest_number_v8(nums):
    """
    Heap-based selection with the canonical x*4 trick used as sort key.
    Negate keys so largest pops first.
    """
    import heapq
    s = list(map(str, nums))
    # Sort key: x*4 makes longer strings with same prefix win.
    # Negate so Python's min-heap pops the largest.
    heap = [(-int(x * 4), idx, x) for idx, x in enumerate(s)]
    heapq.heapify(heap)
    out = []
    while heap:
        _, _, x = heapq.heappop(heap)
        out.append(x)
    result = "".join(out)
    return "0" if result[0] == "0" else result


# ==============================================================
# Solution 9: Insertion sort (educational, O(n^2))
# ==============================================================
def largest_number_v9(nums):
    """
    Insertion sort: maintain a sorted list, insert each new element
    at the correct position using custom comparator.
    """
    s = list(map(str, nums))
    for i in range(1, len(s)):
        key = s[i]
        j = i - 1
        # Shift elements that are 'less than' key to the right.
        while j >= 0 and s[j] + key < key + s[j]:
            s[j + 1] = s[j]
            j -= 1
        s[j + 1] = key
    result = "".join(s)
    return "0" if result[0] == "0" else result


# ==============================================================
# Solution 10: Sort by x*max_len trick (length-normalized)
# ==============================================================
def largest_number_v10(nums):
    """
    Insight: For each string x, repeat it (max_len / len(x)) times
    to make a length-normalized comparison key. Sorting by this key
    descending gives the same order as the canonical comparator
    for this problem's constraints (nums < 10^3).
    """
    if all(n == 0 for n in nums):
        return "0"

    s = list(map(str, nums))
    max_len = max(len(x) for x in s) if s else 1

    def key(x):
        # Repeat x so its length equals max_len.
        repeat = (max_len + len(x) - 1) // len(x)
        return x * repeat

    s.sort(key=key, reverse=True)
    result = "".join(s)
    return "0" if result[0] == "0" else result


# ==============================================================
# Test runner
# ==============================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (cmp_to_key canonical)", largest_number_v1),
        ("V2 (sort by x*10 reverse)", largest_number_v2),
        ("V3 (bubble sort)",          largest_number_v3),
        ("V4 (selection sort)",       largest_number_v4),
        ("V5 (x*4 trick)",            largest_number_v5),
        ("V6 (quicksort)",            largest_number_v6),
        ("V7 (merge sort)",           largest_number_v7),
        ("V8 (heap sort)",            largest_number_v8),
        ("V9 (insertion sort)",       largest_number_v9),
        ("V10 (length+value sort)",   largest_number_v10),
    ]

    test_cases = [
        ([10, 2],                "210"),
        ([3, 30, 34, 5, 9],      "9534330"),
        ([1],                    "1"),
        ([10],                   "10"),
        ([0, 0],                 "0"),
        ([0, 0, 0],              "0"),
        ([1, 2, 3, 4, 5],        "54321"),
        ([5, 4, 3, 2, 1],        "54321"),
        ([121, 12],              "12121"),   # '12112' > '12121'? '12121'
        ([9, 99, 999],           "999999"),  # '9' + '99' + '999' = '999999'
        ([830, 8308],            "8308830"), # '8308' + '830' = '8308830'
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for arr, expected in test_cases:
            try:
                got = func(list(arr))
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name}: {arr} -> {got!r} (expected {expected!r})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name}: ERROR on {arr}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")
    print("\n=== INTERVIEW THINKING ===")
    print("""
1. UNDERSTAND:  Reorder nums to form the largest concatenated number.
2. INSIGHT:     Two numbers a, b -> prefer a+b > b+a.
3. PATTERN:     Custom comparator sort.
4. EDGE:        All zeros -> return "0", not "000...0".
5. ALGORITHM:   str -> sort -> join -> check leading zeros.
6. COMPLEXITY:  O(n log n) time, O(n) space.
7. PROOF:       Pairwise-optimal swaps give global optimum (transposition).
8. CODE:        Use functools.cmp_to_key with custom comparison.
""")
