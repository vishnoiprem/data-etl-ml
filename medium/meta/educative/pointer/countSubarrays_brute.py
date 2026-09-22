def countSubarrays(nums, minK, maxK):
    # Replace this placeholder return statement with your code
    count = 0
    for i in range(len(nums)):
        for j in range(i, len(nums)):
            sub_array = nums[i:j + 1]
            min_value = min(sub_array)
            max_value = max(sub_array)

            if min_value == minK and max_value == maxK:
                count = count + 1
    return count


nums=[1,3,5,2,7,5]
minK=1
maxK=5
print(countSubarrays(nums, minK, maxK))


def countSubarrays(nums, minK, maxK):
    last_min = -1  # last index where nums[i] == minK
    last_max = -1  # last index where nums[i] == maxK
    last_invalid = -1  # last index where nums[i] is out of [minK, maxK]
    count = 0

    for i in range(len(nums)):
        num = nums[i]

        # If current element is out of bounds, it's a wall
        if num < minK or num > maxK:
            last_invalid = i

        # Update positions of minK and maxK
        if num == minK:
            last_min = i
        if num == maxK:
            last_max = i

        # Count valid subarrays ending at index i
        # Start must be after last_invalid, end must include both minK and maxK
        valid_starts = min(last_min, last_max) - last_invalid
        if valid_starts > 0:
            count += valid_starts

    return count


# Test cases
print(countSubarrays([1, 3, 5, 2, 7, 5], 1, 5))  # 2
print(countSubarrays([1, 1, 1, 1], 1, 1))  # 10 (all subarrays)
print(countSubarrays([1, 5, 1], 1, 5))  # 1
