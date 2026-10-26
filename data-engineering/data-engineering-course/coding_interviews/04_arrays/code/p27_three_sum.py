"""3Sum — all unique triplets that sum to zero.

Time:  O(n²) — sort + outer loop + two-pointer inner
Space: O(1) extra (output aside)
"""


def solve_three_sum(nums):
    """Return all unique triplets [a, b, c] with a + b + c == 0.

    >>> sorted(solve_three_sum([-1, 0, 1, 2, -1, -4]))
    [[-1, -1, 2], [-1, 0, 1]]
    """
    nums = sorted(nums)
    n = len(nums)
    out = []
    for i in range(n - 2):
        # Skip duplicates for the outer loop.
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        # If the smallest possible sum is already > 0, we can stop.
        if nums[i] + nums[i + 1] + nums[i + 2] > 0:
            break
        # If the largest possible sum is still < 0, this i can't work.
        if nums[i] + nums[n - 2] + nums[n - 1] < 0:
            continue
        left, right = i + 1, n - 1
        while left < right:
            total = nums[i] + nums[left] + nums[right]
            if total == 0:
                out.append([nums[i], nums[left], nums[right]])
                # Skip duplicates for the inner pointers.
                left_val, right_val = nums[left], nums[right]
                while left < right and nums[left] == left_val:
                    left += 1
                while left < right and nums[right] == right_val:
                    right -= 1
            elif total < 0:
                left += 1
            else:
                right -= 1
    return out


if __name__ == "__main__":
    print(solve_three_sum([-1, 0, 1, 2, -1, -4]))
