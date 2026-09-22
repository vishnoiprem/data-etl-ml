def can_partition_array(nums):
    """
    Determine if nums can be partitioned into two subsets with equal sums.
    Equivalently: can we find a subset whose sum equals total/2?
    """
    total = sum(nums)
    # Odd total cannot be split into two equal integer sums
    if total % 2 != 0:
        return False

    target = total // 2

    # dp[i] = True if some subset of nums sums to exactly i
    dp = [False] * (target + 1)
    dp[0] = True  # empty subset

    for num in nums:
        # Iterate descending to avoid re-using same element
        for s in range(target, num - 1, -1):
            if dp[s - num]:
                dp[s] = True

    return dp[target]


if __name__ == "__main__":
    # Test cases
    print(can_partition_array([1, 5, 11, 5]))           # True  (1+5+5=11, {11})
    print(can_partition_array([1, 2, 3, 5]))              # False (sum=11, target=5.5)
    print(can_partition_array([1, 2, 5]))                 # False (sum=8, target=4)
    print(can_partition_array([2, 2]))                    # True
    print(can_partition_array([1, 1]))                    # True
    print(can_partition_array([3, 3, 3, 3]))              # True (3+3 and 3+3)
