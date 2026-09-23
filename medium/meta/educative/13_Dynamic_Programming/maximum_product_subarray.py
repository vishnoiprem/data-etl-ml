"""
Maximum Product Subarray
========================
Given an integer array nums, find a contiguous subarray with the largest
product, and return that product.

Constraints:
    1 <= nums.length <= 10^3
    -10 <= nums[i] <= 10
    Product fits in 32-bit int.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/maximum-product-subarray
"""

# ==============================================================
# Solution 1: Track Min and Max so far (canonical, O(n))
# ==============================================================
def max_product_v1(nums):
    """
    Track the max and min product ending at each position.
    Why min? Because a negative min can become the max when multiplied
    by a negative number.
    """
    if not nums:
        return 0
    max_so_far = min_so_far = result = nums[0]
    for num in nums[1:]:
        if num < 0:
            max_so_far, min_so_far = min_so_far, max_so_far
        max_so_far = max(num, max_so_far * num)
        min_so_far = min(num, min_so_far * num)
        result = max(result, max_so_far)
    return result


# ==============================================================
# Solution 2: DP with explicit prev arrays (clearer for interviews)
# ==============================================================
def max_product_v2(nums):
    """
    Build two arrays:
      max_prod[i] = max product of a subarray ending at i
      min_prod[i] = min product of a subarray ending at i
    """
    if not nums:
        return 0
    n = len(nums)
    max_prod = [0] * n
    min_prod = [0] * n
    max_prod[0] = min_prod[0] = nums[0]
    result = nums[0]
    for i in range(1, n):
        max_prod[i] = max(nums[i], nums[i] * max_prod[i - 1], nums[i] * min_prod[i - 1])
        min_prod[i] = min(nums[i], nums[i] * max_prod[i - 1], nums[i] * min_prod[i - 1])
        result = max(result, max_prod[i])
    return result


# ==============================================================
# Solution 3: Brute Force — O(n^2)
# ==============================================================
def max_product_v3(nums):
    """
    Try every subarray, compute its product, take max.
    Simple but slow.
    """
    if not nums:
        return 0
    best = nums[0]
    for i in range(len(nums)):
        product = 1
        for j in range(i, len(nums)):
            product *= nums[j]
            if product > best:
                best = product
    return best


# ==============================================================
# Solution 4: Prefix-product with zero-handling — O(n)
# ==============================================================
def max_product_v4(nums):
    """
    Compute prefix products; the max subarray product equals the
    max ratio of two prefix products (handling zeros by splitting).
    """
    if not nums:
        return 0
    prefix = []
    prod = 1
    for num in nums:
        prod *= num
        prefix.append(prod)

    # Max subarray product = max(prefix[j] / prefix[i-1]) for j >= i,
    # equivalently max(prefix[j] / min_prefix_so_far).
    best = max(prefix)  # subarray starting at index 0
    min_pref = float("inf")
    for j in range(len(prefix)):
        if prefix[j] > 0:
            if min_pref < 0:
                cand = prefix[j] / min_pref
                if cand > best:
                    best = cand
        else:
            # Reset: a negative prefix can't help us compute a max product
            # from index 0; but for ratios, we want the smallest (most
            # negative) prefix so far.
            if prefix[j] < min_pref:
                min_pref = prefix[j]
    # Reset on zero: re-scan from scratch
    best_global = max(prefix)
    cur_prod = 1
    for num in nums:
        cur_prod *= num
        if cur_prod > best_global:
            best_global = cur_prod
        if cur_prod == 0:
            cur_prod = 1
    return int(best_global)


# Simpler/cleaner version of Solution 4:
def max_product_v4_clean(nums):
    """
    The max product subarray either starts at index 0 or contains a zero.
    We scan left-to-right and right-to-left, taking the running product
    and resetting on zero. Take the max across all runs.
    """
    if not nums:
        return 0

    def max_from_one_direction(arr):
        best = float("-inf")
        cur = 1
        for x in arr:
            cur *= x
            if cur > best:
                best = cur
            if cur == 0:
                cur = 1
        return best

    return max(max_from_one_direction(nums), max_from_one_direction(nums[::-1]))


# ==============================================================
# Solution 5: O(n) with no array allocation (constant space)
# ==============================================================
def max_product_v5(nums):
    """
    Same logic as Solution 1, but uses three variables: running_max,
    running_min, and global_best. O(1) extra space.
    """
    if not nums:
        return 0
    rm, rn, best = nums[0], nums[0], nums[0]
    for x in nums[1:]:
        if x < 0:
            rm, rn = rn, rm
        rm = max(x, rm * x)
        rn = min(x, rn * x)
        if rm > best:
            best = rm
    return best


# ==============================================================
# Solution 6: Split on zeros, evaluate each segment
# ==============================================================
def max_product_v6(nums):
    """
    Zeros break any product. For each zero-free segment, the max
    product is either:
        - the whole segment
        - the segment with prefix up to and including the first negative removed
        - the segment with suffix from the last negative removed
    Note: when the only negative is at one of the ends, dropping
    the prefix/suffix leaves an empty product (= 1), but the original
    total is negative; in such cases, total is the better answer.
    """
    if not nums:
        return 0

    best = float("-inf")
    i = 0
    n = len(nums)
    while i < n:
        if nums[i] == 0:
            best = max(best, 0)
            i += 1
            continue
        j = i
        # Walk forward to find end of zero-free segment (stops AT zero or end)
        while j < n and nums[j] != 0:
            j += 1
        segment = nums[i:j]
        # segment is non-empty since nums[i] != 0
        total = 1
        for x in segment:
            total *= x
        neg_count = sum(1 for x in segment if x < 0)
        candidate = total
        if neg_count % 2 == 1 and len(segment) > 1:
            # Drop prefix up to and including first negative
            first_neg = next(k for k, x in enumerate(segment) if x < 0)
            prod_drop_pref = 1
            for x in segment[first_neg + 1:]:
                prod_drop_pref *= x
            # Drop suffix from last negative
            last_neg = max(k for k, x in enumerate(segment) if x < 0)
            prod_drop_suff = 1
            for x in segment[:last_neg]:
                prod_drop_suff *= x
            # Both products are positive (we removed one negative).
            candidate = max(prod_drop_pref, prod_drop_suff)
        best = max(best, candidate)
        # Move past zero if there is one
        if j < n:
            best = max(best, 0)
            i = j + 1
        else:
            i = j
    return best


# ==============================================================
# Solution 7: Recursion with memoization (top-down)
# ==============================================================
def max_product_v7(nums):
    """
    For each index, recursively compute the best subarray ending there.
    Cache results. Returns the best overall.
    """
    if not nums:
        return 0
    n = len(nums)
    memo_max = {}
    memo_min = {}

    def get_max(i):
        if i in memo_max:
            return memo_max[i]
        if i == 0:
            memo_max[0] = nums[0]
            memo_min[0] = nums[0]
            return memo_max[0]
        prev_max = get_max(i - 1)
        prev_min = get_min(i - 1)
        cur_max = max(nums[i], nums[i] * prev_max, nums[i] * prev_min)
        cur_min = min(nums[i], nums[i] * prev_max, nums[i] * prev_min)
        memo_max[i] = cur_max
        memo_min[i] = cur_min
        return cur_max

    def get_min(i):
        return memo_min.get(i, get_max(i))  # forces memo_min to be populated

    return max(get_max(i) for i in range(n))


# ==============================================================
# Solution 8: Kadane-style for products
# ==============================================================
def max_product_v8(nums):
    """
    A single-pass variant: maintain running max and min, swap on negative.
    Identical logic to Solution 1 but presented in a 'Kadane-like' style.
    """
    if not nums:
        return 0
    best = cur_max = cur_min = nums[0]
    for x in nums[1:]:
        if x < 0:
            cur_max, cur_min = cur_min, cur_max
        cur_max = max(x, cur_max * x)
        cur_min = min(x, cur_max * x if False else cur_min * x)  # uses prev cur_min
        if cur_max > best:
            best = cur_max
    return best


# ==============================================================
# Solution 9: Handle zeros by treating them as "reset points"
# ==============================================================
def max_product_v9(nums):
    """
    Like Solution 4_clean: scan twice (forward and backward), reset
    on zero, take the max of all running products. Works because
    the optimal subarray either starts at the beginning or ends at
    the end of some zero-free subarray.
    """
    if not nums:
        return 0
    best = float("-inf")
    cur = 1
    for x in nums:
        cur *= x
        if cur > best:
            best = cur
        if cur == 0:
            cur = 1
    cur = 1
    for x in reversed(nums):
        cur *= x
        if cur > best:
            best = cur
        if cur == 0:
            cur = 1
    return best


# ==============================================================
# Solution 10: Prefix-product ratio enumeration — O(n^2)
# ==============================================================
def max_product_v10(nums):
    """
    Compute prefix products. For each pair (i, j) with i < j, the
    product of nums[i:j] equals prefix[j] / prefix[i]. When prefix[i]
    is zero, the subarray product is zero (unless the subarray itself
    contains no zeros). Handle this by computing product directly
    when there's a zero in nums[i:j].
    """
    if not nums:
        return 0
    n = len(nums)
    prefix = [1] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] * nums[i]

    best = float("-inf")
    for j in range(1, n + 1):
        for i in range(j):
            if prefix[i] == 0:
                # Recompute product directly to handle zeros
                cand = 1
                for x in nums[i:j]:
                    cand *= x
            else:
                cand = prefix[j] // prefix[i]
            if cand > best:
                best = cand
    return best


# ==============================================================
# Test runner — verify all 10 implementations
# ==============================================================
if __name__ == "__main__":
    solutions = [
        ("V1 (canonical min/max)", max_product_v1),
        ("V2 (DP arrays)",          max_product_v2),
        ("V3 (brute force)",        max_product_v3),
        ("V4 (prefix products)",    max_product_v4_clean),
        ("V5 (O(1) space)",         max_product_v5),
        ("V6 (zero-split)",         max_product_v6),
        ("V7 (memoized recursion)", max_product_v7),
        ("V8 (Kadane-style)",       max_product_v8),
        ("V9 (forward/backward)",   max_product_v9),
        ("V10 (prefix ratios)",     max_product_v10),
    ]

    test_cases = [
        ([2, 3, -2, 4],                6),     # [2,3]
        ([-2, 0, -1],                  0),     # 0 breaks product; max(0, 0, -1, 0) = 0
        ([-2],                         -2),
        ([-1, -2, -3, -4],             24),    # whole array
        ([-1, -2, -3, 0, -4],          6),     # [-2,-3] = 6 is the max
        ([1, -2, 3, -4, 5],            120),   # whole
        ([0, 2],                       2),
        ([1],                          1),
        ([-1],                         -1),
        ([0],                          0),
        ([2, -1, 1, 1],                2),     # subarray [2]
        ([3, -1, 4],                   4),     # [4] or [3,-1,4] = -12
        ([-3, -1, -1],                 3),     # [-3,-1] = 3, [-1] = -1, etc.
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
                    print(f"  X {name}: {arr} -> {got} (expected {expected})")
            except Exception as e:
                ok = False
                all_pass = False
                print(f"  X {name}: ERROR on {arr}: {e}")
        if ok:
            print(f"  OK {name}: PASS")
    print()
    print("ALL PASS" if all_pass else "SOME FAILURES")
