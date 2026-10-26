"""Product of Array Except Self — output[i] = product of all elements except nums[i].

Time:  O(n) — two passes (prefix and suffix)
Space: O(1) extra — output array doesn't count
"""


def solve_product_except_self(nums):
    """Return the product of every other element, in O(n) and O(1) extra space.

    >>> solve_product_except_self([1, 2, 3, 4])
    [24, 12, 8, 6]
    """
    n = len(nums)
    out = [1] * n
    # Prefix products: out[i] = product of nums[:i].
    prefix = 1
    for i in range(n):
        out[i] = prefix
        prefix *= nums[i]
    # Suffix products: multiply by product of nums[i+1:].
    suffix = 1
    for i in range(n - 1, -1, -1):
        out[i] *= suffix
        suffix *= nums[i]
    return out


if __name__ == "__main__":
    print(solve_product_except_self([1, 2, 3, 4]))
