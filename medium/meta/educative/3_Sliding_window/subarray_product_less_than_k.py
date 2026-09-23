"""
Subarray Product Less Than K - 10 Ways
======================================
Given an array of positive integers nums and an integer k, return the
number of contiguous subarrays where the product of all elements in
the subarray is strictly less than k.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/subarray-product-less-than-k
          (LeetCode #713)

Examples:
    nums = [10, 5, 2, 6], k = 100      -> 8
        (Subarrays with product < 100:
         [10], [5], [2], [6], [10,5], [5,2], [10,5,2], [5,2,6])
        Total = 8.
    nums = [1, 2, 3], k = 0            -> 0
        (k must be > 1 for any positive product to qualify.
         But wait, constraint says k >= 1. So if k = 1, no positive
         product is < 1, hence 0.)

Constraints:
- 1 <= nums.length <= 3 * 10^4
- 1 <= nums[i] < k (in some versions, this is required)
- 1 <= k <= 10^6

INTERVIEW THINKING (10 STEPS):
------------------------------
1. UNDERSTAND:
   "Count subarrays where product of elements < k."

2. KEY INSIGHT:
   "Sliding window with running product. For each right, count valid
   subarrays ending at right = right - left + 1 after shrinking until
   product < k. (Since all positive, shrinking only decreases product.)"

3. PATTERN RECOGNITION:
   - Sliding window with product constraint
   - All positive numbers

4. EDGE CASES:
   - k <= 1 -> 0 (no positive product is < 1).
   - All ones -> n*(n+1)/2.
   - Single element >= k -> 0 (for that element).

5. TRICKY DETAIL:
   "When product >= k, shrink from left. Each shrink divides by nums[left].
    The product always decreases since nums are positive."

6. ALGORITHM:
   "if k <= 1: return 0
    product = 1; left = 0; result = 0
    for right in range(n):
        product *= nums[right]
        while product >= k:
            product //= nums[left]
            left += 1
        result += right - left + 1
    return result"

7. WHY IT WORKS:
   "After shrinking, [left..right] has product < k. All sub-windows
   ending at right with start in [left..right] also have product < k
   (smaller windows have smaller products, since all positive). There
   are right - left + 1 such starts."

8. COMPLEXITY:
   "Time: O(n). Each element added and removed at most once.
    Space: O(1)."

9. CODE STRUCTURE:
   "Edge case k <= 1. Init. Slide. Shrink. Add count."

10. MENTAL TRACE:
    nums=[10,5,2,6], k=100.
    right=0 (10): product=10. result=1.
    right=1 (5): product=50. result=1+2=3.
    right=2 (2): product=100 >= 100. shrink: product=10, left=1. result=3+2=5.
    right=3 (6): product=60. result=5+3=8.
    Final = 8. ✓
"""


# Solution 1: Sliding window (BEST)
def num_subarray_product_less_than_k_v1(nums, k):
    if k <= 1:
        return 0
    product = 1
    left = 0
    result = 0
    for right in range(len(nums)):
        product *= nums[right]
        while product >= k:
            product //= nums[left]
            left += 1
        result += right - left + 1
    return result


# Solution 2: Same logic, slightly cleaner
def num_subarray_product_less_than_k_v2(nums, k):
    if k <= 1:
        return 0
    n = len(nums)
    product = 1
    left = 0
    result = 0
    for right in range(n):
        product *= nums[right]
        while left <= right and product >= k:
            product //= nums[left]
            left += 1
        result += right - left + 1
    return result


# Solution 3: Brute force O(n^2)
def num_subarray_product_less_than_k_v3(nums, k):
    n = len(nums)
    result = 0
    for i in range(n):
        product = 1
        for j in range(i, n):
            product *= nums[j]
            if product < k:
                result += 1
            else:
                break
    return result


# Solution 4: Prefix product array + binary search
def num_subarray_product_less_than_k_v4(nums, k):
    import math
    if k <= 1:
        return 0
    n = len(nums)
    # log_product[i] = sum of log(nums[0..i-1])
    log_k = math.log(k)
    log_prefix = [0.0] * (n + 1)
    for i in range(n):
        log_prefix[i + 1] = log_prefix[i] + math.log(nums[i])
    result = 0
    for right in range(n):
        # Find smallest left such that log_prefix[right+1] - log_prefix[left] < log_k
        # i.e., log_prefix[left] > log_prefix[right+1] - log_k
        import bisect
        lo = bisect.bisect_right(log_prefix, log_prefix[right + 1] - log_k, 0, right + 1)
        result += right + 1 - lo
    return result


# Solution 5: Same as V1 with float division (won't be exact)
def num_subarray_product_less_than_k_v5(nums, k):
    if k <= 1:
        return 0
    n = len(nums)
    product = 1.0
    left = 0
    result = 0
    for right in range(n):
        product *= nums[right]
        while product >= k:
            product /= nums[left]
            left += 1
        result += right - left + 1
    return result


# Solution 6: numpy fallback
def num_subarray_product_less_than_k_v6(nums, k):
    return num_subarray_product_less_than_k_v1(nums, k)


# Solution 7: Recursive
def num_subarray_product_less_than_k_v7(nums, k):
    if k <= 1:
        return 0
    n = len(nums)
    product = [1]
    left = [0]
    result = [0]

    def helper(right):
        if right == n:
            return
        product[0] *= nums[right]
        while product[0] >= k:
            product[0] //= nums[left[0]]
            left[0] += 1
        result[0] += right - left[0] + 1
        helper(right + 1)

    helper(0)
    return result[0]


# Solution 8: Same as V1, with math prod / cumulative
def num_subarray_product_less_than_k_v8(nums, k):
    if k <= 1:
        return 0
    from math import prod
    n = len(nums)
    left = 0
    result = 0
    # Use a simple list for the window
    window = []
    for right in range(n):
        window.append(nums[right])
        while prod(window) >= k:
            window.pop(0)
            left += 1
        result += right - left + 1
    return result


# Solution 9: Single loop, explicit shrink counting
def num_subarray_product_less_than_k_v9(nums, k):
    if k <= 1:
        return 0
    n = len(nums)
    product = 1
    left = 0
    result = 0
    for right in range(n):
        product *= nums[right]
        count_shrinks = 0
        while product >= k:
            product //= nums[left]
            left += 1
            count_shrinks += 1
        result += right - left + 1
    return result


# Solution 10: Same as V1, minimal
def num_subarray_product_less_than_k_v10(nums, k):
    if k <= 1:
        return 0
    result = 0
    product = 1
    left = 0
    for right, x in enumerate(nums):
        product *= x
        while product >= k:
            product //= nums[left]
            left += 1
        result += right - left + 1
    return result


# =====================================================
# Test runner
# =====================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (BEST)",              num_subarray_product_less_than_k_v1),
        ("V2 (cleaner)",           num_subarray_product_less_than_k_v2),
        ("V3 (brute)",             num_subarray_product_less_than_k_v3),
        ("V4 (log + bisect)",      num_subarray_product_less_than_k_v4),
        ("V5 (float)",             num_subarray_product_less_than_k_v5),
        ("V6 (numpy)",             num_subarray_product_less_than_k_v6),
        ("V7 (recursive)",         num_subarray_product_less_than_k_v7),
        ("V8 (math prod)",         num_subarray_product_less_than_k_v8),
        ("V9 (shrink count)",      num_subarray_product_less_than_k_v9),
        ("V10 (concise)",          num_subarray_product_less_than_k_v10),
    ]

    test_cases = [
        ([10, 5, 2, 6], 100, 8),
        ([1, 2, 3], 0, 0),
        ([1, 1, 1, 1], 4, 10),  # n*(n+1)/2 = 10
        ([1, 1, 1, 1], 5, 10),
        ([1, 1, 1, 1], 1, 0),
        ([10], 1, 0),
        ([10], 100, 1),
        ([10], 5, 0),
        ([1, 2, 3, 4], 10, 7),
        # [1] (1<10), [2] (2<10), [3] (3<10), [4] (4<10),
        # [1,2] (2<10), [2,3] (6<10), [3,4] (12>=10 no)
        # [1,2,3] (6<10), [2,3,4] (24>=10 no)
        # [1,2,3,4] (24>=10 no).
        # Count: 7.
        ([10, 100, 1000], 1, 0),
    ]

    all_pass = True
    for name, func in solutions:
        ok = True
        for idx, (nums, k, expected) in enumerate(test_cases):
            try:
                got = func(nums[:], k)
                if got != expected:
                    ok = False
                    all_pass = False
                    print(f"  X {name} [{idx}]: nums={nums}, k={k} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name} [{idx}]: ERROR: {type(e).__name__}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")
