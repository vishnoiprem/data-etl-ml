def findNumberOfLIS(nums):
    """
    Return the number of longest strictly increasing subsequences.

    Two parallel DP arrays:
      length[i] = length of the longest increasing subsequence ending at i
      count[i]  = number of such subsequences of that length ending at i
    """
    if not nums:
        return 0

    n = len(nums)
    length = [1] * n      # LIS ending at each index (at least the element itself)
    count = [1] * n       # # of such subsequences

    for i in range(n):
        for j in range(i):
            if nums[j] < nums[i]:
                # If extending from j gives a longer LIS ending at i
                if length[j] + 1 > length[i]:
                    length[i] = length[j] + 1
                    count[i] = count[j]
                # If it ties, accumulate counts
                elif length[j] + 1 == length[i]:
                    count[i] += count[j]

    # Find the maximum length and sum counts for all positions with that length
    max_len = max(length)
    return sum(c for l, c in zip(length, count) if l == max_len)


if __name__ == "__main__":
    # Test cases
    print(findNumberOfLIS([1, 3, 5, 4, 7]))           # 2
    print(findNumberOfLIS([2, 2, 2, 2, 2]))           # 5
    print(findNumberOfLIS([1, 2, 4, 3, 5, 4, 7, 2])) # ?
    print(findNumberOfLIS([1]))                        # 1
    print(findNumberOfLIS([3, 1, 2]))                  # 1
