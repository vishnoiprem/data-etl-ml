"""
Sum of Subarray Minimums
Medium | 30 min

Given an array arr of positive integers. Find the sum of min(b) for
every (contiguous) subarray b of arr.

The answer may be large - return mod 10^9 + 7.

Examples:
    arr = [3, 1, 2, 4]        -> 17
        Subarrays:
            [3] min=3, [1] min=1, [2] min=2, [4] min=4
            [3,1] min=1, [1,2] min=1, [2,4] min=2
            [3,1,2] min=1, [1,2,4] min=1
            [3,1,2,4] min=1
            Sum = 3+1+2+4+1+1+2+1+1+1 = 17

    arr = [11, 81, 94, 43, 3] -> 444

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/sum-of-subarray-minimums

Constraints:
- 1 <= arr.length <= 3 * 10^4
- 1 <= arr[i] <= 3 * 10^4
"""


# =============================================================================
# WAY 1: For each element, find its contribution using two stacks (BEST)
# =============================================================================
def sum_subarray_mins_1(arr):
    MOD = 10**9 + 7
    n = len(arr)

    # For each element, find the distance to a smaller element on left and right.
    # This element is the min for subarrays where it is the smallest.
    # count = left_dist * right_dist.

    # Previous less element (strictly less)
    left = [0] * n
    stack = []
    for i in range(n):
        # Number of subarrays ending at i where arr[i] is the new minimum
        count = 1
        while stack and arr[stack[-1]] > arr[i]:
            stack.pop()
        if stack:
            left[i] = i - stack[-1]
        else:
            left[i] = i + 1
        stack.append(i)

    # Next less element (less than OR equal)
    right = [0] * n
    stack = []
    for i in range(n - 1, -1, -1):
        count = 1
        while stack and arr[stack[-1]] >= arr[i]:
            stack.pop()
        if stack:
            right[i] = stack[-1] - i
        else:
            right[i] = n - i
        stack.append(i)

    total = 0
    for i in range(n):
        total = (total + arr[i] * left[i] * right[i]) % MOD
    return total


# =============================================================================
# WAY 2: Single pass with strict/non-strict handling
# =============================================================================
def sum_subarray_mins_2(arr):
    MOD = 10**9 + 7
    n = len(arr)

    left = [1] * n
    stack = []
    for i in range(n):
        cnt = 1
        while stack and arr[stack[-1]] > arr[i]:
            cnt += left[stack.pop()]
        left[i] = cnt
        stack.append(i)

    right = [1] * n
    stack = []
    for i in range(n - 1, -1, -1):
        cnt = 1
        while stack and arr[stack[-1]] >= arr[i]:
            cnt += right[stack.pop()]
        right[i] = cnt
        stack.append(i)

    total = 0
    for i in range(n):
        total = (total + arr[i] * left[i] * right[i]) % MOD
    return total


# =============================================================================
# WAY 3: Brute force O(n^2)
# =============================================================================
def sum_subarray_mins_3(arr):
    MOD = 10**9 + 7
    n = len(arr)
    total = 0
    for i in range(n):
        min_val = arr[i]
        for j in range(i, n):
            if arr[j] < min_val:
                min_val = arr[j]
            total = (total + min_val) % MOD
    return total


# =============================================================================
# WAY 4: With sentinel values
# =============================================================================
def sum_subarray_mins_4(arr):
    MOD = 10**9 + 7
    # Add sentinel 0 at start and end
    a = [0] + arr + [0]
    n = len(a)
    stack = []
    total = 0
    for i in range(n):
        while stack and a[stack[-1]] > a[i]:
            j = stack.pop()
            k = stack[-1] if stack else -1
            # a[j] is the minimum for subarrays from k+1 to i-1
            # count = (j - k) * (i - j)
            count = (j - k) * (i - j)
            total = (total + a[j] * count) % MOD
        stack.append(i)
    return total


# =============================================================================
# WAY 5: With sentinel (non-strict)
# =============================================================================
def sum_subarray_mins_5(arr):
    MOD = 10**9 + 7
    a = [0] + arr + [0]
    n = len(a)
    stack = []
    total = 0
    for i in range(n):
        while stack and a[stack[-1]] > a[i]:
            j = stack.pop()
            k = stack[-1] if stack else -1
            count = (j - k) * (i - j)
            total = (total + a[j] * count) % MOD
        stack.append(i)
    return total


# =============================================================================
# WAY 6: Cartesian tree style
# =============================================================================
def sum_subarray_mins_6(arr):
    MOD = 10**9 + 7
    n = len(arr)

    # For each element, count of subarrays where it's min = left * right
    # left[i] = number of subarrays ending at i with arr[i] as min
    # But this requires more care

    # Use 2 arrays
    left = [1] * n
    stack = []
    for i in range(n):
        cnt = 1
        while stack and arr[stack[-1]] > arr[i]:
            cnt += left[stack.pop()]
        left[i] = cnt
        stack.append(i)

    right = [1] * n
    stack = []
    for i in range(n - 1, -1, -1):
        cnt = 1
        while stack and arr[stack[-1]] >= arr[i]:
            cnt += right[stack.pop()]
        right[i] = cnt
        stack.append(i)

    total = 0
    for i in range(n):
        total = (total + arr[i] * left[i] * right[i]) % MOD
    return total


# =============================================================================
# WAY 7: Most concise (with sentinels)
# =============================================================================
def sum_subarray_mins_7(arr):
    MOD = 10**9 + 7
    a = [0] + arr + [0]
    stack = [0]
    total = 0
    for i in range(1, len(a)):
        while a[stack[-1]] > a[i]:
            j = stack.pop()
            total = (total + a[j] * (j - stack[-1]) * (i - j)) % MOD
        stack.append(i)
    return total


# =============================================================================
# WAY 8: Two arrays for prev_less and next_less
# =============================================================================
def sum_subarray_mins_8(arr):
    MOD = 10**9 + 7
    n = len(arr)
    # prev_less[i] = index of prev smaller element (strict)
    prev_less = [-1] * n
    stack = []
    for i in range(n):
        while stack and arr[stack[-1]] >= arr[i]:
            stack.pop()
        prev_less[i] = stack[-1] if stack else -1
        stack.append(i)

    # next_less[i] = index of next smaller element (non-strict)
    next_less = [n] * n
    stack = []
    for i in range(n - 1, -1, -1):
        while stack and arr[stack[-1]] > arr[i]:
            stack.pop()
        next_less[i] = stack[-1] if stack else n
        stack.append(i)

    total = 0
    for i in range(n):
        left_count = i - prev_less[i]
        right_count = next_less[i] - i
        total = (total + arr[i] * left_count * right_count) % MOD
    return total


# =============================================================================
# WAY 9: Direct contribution approach
# =============================================================================
def sum_subarray_mins_9(arr):
    MOD = 10**9 + 7
    n = len(arr)
    stack = []
    total = 0
    for i in range(n + 1):
        cur = arr[i] if i < n else 0
        while stack and arr[stack[-1]] > cur:
            j = stack.pop()
            k = stack[-1] if stack else -1
            count = (j - k) * (i - j)
            total = (total + arr[j] * count) % MOD
        stack.append(i)
    return total


# =============================================================================
# WAY 10: With explicit indices
# =============================================================================
def sum_subarray_mins_10(arr):
    MOD = 10**9 + 7
    n = len(arr)
    # Use a=[0]+arr+[0]
    a = [0] + arr + [0]
    N = n + 2
    stack = []
    total = 0
    for i in range(N):
        while stack and a[stack[-1]] > a[i]:
            j = stack.pop()
            k = stack[-1]
            count = (j - k) * (i - j)
            total = (total + a[j] * count) % MOD
        stack.append(i)
    return total


# =============================================================================
# WAY 11: Class-based
# =============================================================================
class SubarrayMinSum:
    def __init__(self, arr):
        self.arr = arr
        self.MOD = 10**9 + 7

    def compute(self):
        arr = self.arr
        n = len(arr)
        left = [1] * n
        stack = []
        for i in range(n):
            cnt = 1
            while stack and arr[stack[-1]] > arr[i]:
                cnt += left[stack.pop()]
            left[i] = cnt
            stack.append(i)

        right = [1] * n
        stack = []
        for i in range(n - 1, -1, -1):
            cnt = 1
            while stack and arr[stack[-1]] >= arr[i]:
                cnt += right[stack.pop()]
            right[i] = cnt
            stack.append(i)

        total = 0
        for i in range(n):
            total = (total + arr[i] * left[i] * right[i]) % self.MOD
        return total


def sum_subarray_mins_11(arr):
    return SubarrayMinSum(arr).compute()


# =============================================================================
# WAY 12: Using deque
# =============================================================================
def sum_subarray_mins_12(arr):
    MOD = 10**9 + 7
    from collections import deque
    n = len(arr)
    a = [0] + arr + [0]
    N = n + 2
    stack = deque()
    stack.append(0)
    total = 0
    for i in range(1, N):
        while stack and a[stack[-1]] > a[i]:
            j = stack.pop()
            k = stack[-1] if stack else 0
            count = (j - k) * (i - j)
            total = (total + a[j] * count) % MOD
        stack.append(i)
    return total


# =============================================================================
# WAY 13: With verbose counter calculation
# =============================================================================
def sum_subarray_mins_13(arr):
    MOD = 10**9 + 7
    n = len(arr)

    left = [0] * n
    stack = []
    for i in range(n):
        cnt = 1
        while stack and arr[stack[-1]] > arr[i]:
            stack.pop()
        if stack:
            cnt = i - stack[-1]
        else:
            cnt = i + 1
        left[i] = cnt
        stack.append(i)

    right = [0] * n
    stack = []
    for i in range(n - 1, -1, -1):
        cnt = 1
        while stack and arr[stack[-1]] >= arr[i]:
            stack.pop()
        if stack:
            cnt = stack[-1] - i
        else:
            cnt = n - i
        right[i] = cnt
        stack.append(i)

    total = 0
    for i in range(n):
        total = (total + arr[i] * left[i] * right[i]) % MOD
    return total


# =============================================================================
# WAY 14: Cleaner with helper
# =============================================================================
def sum_subarray_mins_14(arr):
    MOD = 10**9 + 7
    n = len(arr)

    def count_subarrays(arr, strict):
        """For each i, count subarrays where arr[i] is min."""
        # Returns left[i] = subarrays ending at i with arr[i] as min
        counts = [1] * n
        stack = []
        direction = 1 if strict else -1
        # Adjust based on strict or non-strict comparison
        for i in range(n) if strict else range(n - 1, -1, -1):
            cnt = 1
            while stack and (
                (strict and arr[stack[-1]] > arr[i]) or
                (not strict and arr[stack[-1]] >= arr[i])
            ):
                cnt += counts[stack.pop()]
            counts[i] = cnt
            stack.append(i)
        return counts

    left = count_subarrays(arr, True)
    right = count_subarrays(arr, False)
    total = 0
    for i in range(n):
        total = (total + arr[i] * left[i] * right[i]) % MOD
    return total


# =============================================================================
# WAY 15: Most elegant
# =============================================================================
def sum_subarray_mins_15(arr):
    MOD = 10**9 + 7
    stack = []
    total = 0
    for i, x in enumerate(arr + [0]):
        while stack and arr[stack[-1]] > x:
            j = stack.pop()
            k = stack[-1] if stack else -1
            total = (total + arr[j] * (j - k) * (i - j)) % MOD
        stack.append(i)
    return total


# =============================================================================
# WAY 16: Without special case for last element
# =============================================================================
def sum_subarray_mins_16(arr):
    MOD = 10**9 + 7
    a = arr + [0]
    stack = []
    total = 0
    for i, x in enumerate(a):
        while stack and a[stack[-1]] > x:
            j = stack.pop()
            k = stack[-1] if stack else -1
            total = (total + a[j] * (j - k) * (i - j)) % MOD
        stack.append(i)
    return total


# =============================================================================
# WAY 17: With explicit modulo inside loop
# =============================================================================
def sum_subarray_mins_17(arr):
    MOD = 10**9 + 7
    a = [0] + arr + [0]
    n = len(a)
    stack = []
    total = 0
    for i in range(n):
        while stack and a[stack[-1]] > a[i]:
            j = stack.pop()
            k = stack[-1]
            total = (total + (a[j] * (j - k) * (i - j)) % MOD) % MOD
        stack.append(i)
    return total


# =============================================================================
# WAY 18: Using pre-computed distances
# =============================================================================
def sum_subarray_mins_18(arr):
    MOD = 10**9 + 7
    n = len(arr)

    # Distance to previous strictly less
    prev_strict = [i + 1 for i in range(n)]  # default: distance to start
    stack = []
    for i in range(n):
        while stack and arr[stack[-1]] > arr[i]:
            stack.pop()
        prev_strict[i] = i - (stack[-1] if stack else -1)
        stack.append(i)

    # Distance to next less-or-equal
    next_le = [n - i for i in range(n)]  # default: distance to end
    stack = []
    for i in range(n - 1, -1, -1):
        while stack and arr[stack[-1]] >= arr[i]:
            stack.pop()
        next_le[i] = (stack[-1] if stack else n) - i
        stack.append(i)

    total = 0
    for i in range(n):
        total = (total + arr[i] * prev_strict[i] * next_le[i]) % MOD
    return total


# =============================================================================
# WAY 19: With helper functions
# =============================================================================
def _prev_less(arr):
    n = len(arr)
    left = [1] * n
    stack = []
    for i in range(n):
        cnt = 1
        while stack and arr[stack[-1]] > arr[i]:
            cnt += left[stack.pop()]
        left[i] = cnt
        stack.append(i)
    return left

def _next_less(arr):
    n = len(arr)
    right = [1] * n
    stack = []
    for i in range(n - 1, -1, -1):
        cnt = 1
        while stack and arr[stack[-1]] >= arr[i]:
            cnt += right[stack.pop()]
        right[i] = cnt
        stack.append(i)
    return right

def sum_subarray_mins_19(arr):
    MOD = 10**9 + 7
    left = _prev_less(arr)
    right = _next_less(arr)
    total = 0
    for i in range(len(arr)):
        total = (total + arr[i] * left[i] * right[i]) % MOD
    return total


# =============================================================================
# WAY 20: Final cleanest
# =============================================================================
def sum_subarray_mins_20(arr):
    MOD = 10**9 + 7
    n = len(arr)

    left = [1] * n
    stack = []
    for i in range(n):
        cnt = 1
        while stack and arr[stack[-1]] > arr[i]:
            cnt += left[stack.pop()]
        left[i] = cnt
        stack.append(i)

    right = [1] * n
    stack = []
    for i in range(n - 1, -1, -1):
        cnt = 1
        while stack and arr[stack[-1]] >= arr[i]:
            cnt += right[stack.pop()]
        right[i] = cnt
        stack.append(i)

    total = 0
    for i in range(n):
        total = (total + arr[i] * left[i] * right[i]) % MOD
    return total


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the sum of min(b) over all subarrays b of arr."

Key Insight:
"Each element arr[i] is the minimum for some set of subarrays.
For each i, count those subarrays and multiply by arr[i].
contribution = arr[i] * left * right
where:
- left = # subarrays ending at i with arr[i] as min
- right = # subarrays starting at i with arr[i] as min"

Algorithm:
"1. Compute left[i] = # subarrays ENDING at i with arr[i] as min
   Use stack (strict less comparison)
2. Compute right[i] = # subarrays STARTING at i with arr[i] as min
   Use stack (less-or-equal comparison)
3. Sum arr[i] * left[i] * right[i]"

Why strict vs non-strict:
"For left (going forward), use STRICT greater when popping
(arr[stack[-1]] > arr[i]).
For right (going backward), use GREATER OR EQUAL when popping
(arr[stack[-1]] >= arr[i]).
This avoids double-counting equal elements."

Edge cases:
- Single element: just return arr[0]
- All same: each is min for subarrays in its 'range'
- All increasing: smallest is min for many subarrays

COMPLEXITY:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| 2-pass    | O(n)   | O(n)   |
| Brute     | O(n^2) | O(1)   |
+-----------+--------+--------+

KEY TRICK:
Element arr[i] is min for left[i] * right[i] subarrays.
Need PREVIOUS LESS and NEXT LESS distances via monotonic stack.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Two stacks with distances", sum_subarray_mins_1),
        ("Way 2: With expanding counts", sum_subarray_mins_2),
        ("Way 3: Brute force O(n^2)", sum_subarray_mins_3),
        ("Way 4: With sentinels", sum_subarray_mins_4),
        ("Way 5: Sentinel non-strict", sum_subarray_mins_5),
        ("Way 6: Cartesian tree style", sum_subarray_mins_6),
        ("Way 7: Most concise sentinel", sum_subarray_mins_7),
        ("Way 8: With prev_less/next_less", sum_subarray_mins_8),
        ("Way 9: Direct contribution", sum_subarray_mins_9),
        ("Way 10: Explicit indices", sum_subarray_mins_10),
        ("Way 11: Class-based", sum_subarray_mins_11),
        ("Way 12: Deque", sum_subarray_mins_12),
        ("Way 13: Verbose counter", sum_subarray_mins_13),
        ("Way 14: With helper", sum_subarray_mins_14),
        ("Way 15: Most elegant", sum_subarray_mins_15),
        ("Way 16: No special case", sum_subarray_mins_16),
        ("Way 17: Explicit modulo", sum_subarray_mins_17),
        ("Way 18: Pre-computed distances", sum_subarray_mins_18),
        ("Way 19: With helper functions", sum_subarray_mins_19),
        ("Way 20: Final cleanest", sum_subarray_mins_20),
    ]

    test_cases = [
        ([3, 1, 2, 4], 17),
        ([11, 81, 94, 43, 3], 444),
        ([1], 1),
        ([1, 2, 3], 10),  # mins: 1, 1, 1, 2, 2, 3 = 1+1+1+2+2+3 = 10. Hmm wait:
        # [1,2,3] subarrays: [1]=1, [2]=2, [3]=3, [1,2]=1, [2,3]=2, [1,2,3]=1
        # Sum: 1+2+3+1+2+1 = 10. ✓
        ([3, 1, 2, 4, 1], 24),
        # Let me trace: [3,1,2,4,1]
        # Subarrays ending at each position with their mins:
        # ending at 0 (3): [3]=3
        # ending at 1 (1): [1]=1, [3,1]=1
        # ending at 2 (2): [2]=2, [1,2]=1, [3,1,2]=1
        # ending at 3 (4): [4]=4, [2,4]=2, [1,2,4]=1, [3,1,2,4]=1
        # ending at 4 (1): [1]=1, [4,1]=1, [2,4,1]=1, [1,2,4,1]=1, [3,1,2,4,1]=1
        # Sum: 3+1+1+2+1+1+4+2+1+1+1+1+1+1 = 23
        # Hmm. Let me recount.
        # Actually this is more complex. Let me just trust the algorithm.
        ([7], 7),
        ([1, 1], 4),  # [1]=1, [1]=1, [1,1]=1 = 3. Hmm, that's 3 not 4.
        # Actually for [1, 1], subarrays: [1], [1], [1,1]. Mins: 1, 1, 1. Sum = 3.
        # I had it as 4, that's wrong.
        ]

    # Use cases I'm sure of
    test_cases = [
        ([3, 1, 2, 4], 17),
        ([11, 81, 94, 43, 3], 444),
        ([1], 1),
        ([1, 2, 3], 10),
        ([7], 7),
        ([1, 1], 3),
        ([2, 1, 3], 9),
        # [2,1,3] subarrays: [2]=2, [1]=1, [3]=3, [2,1]=1, [1,3]=1, [2,1,3]=1
        # Sum: 2+1+3+1+1+1 = 9 ✓
    ]

    print("=" * 70)
    print("SUM OF SUBARRAY MINIMUMS - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/sum-of-subarray-minimums")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for arr, expected in test_cases:
            try:
                result = func(arr)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: arr={arr} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on arr={arr} - {e}")
        print(f"  {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
