def missing_number(nums):
    x = 0
    for i in range(len(nums)+1):
        x = x^i
        print(x)
    for v in nums:
        x ^= v
    return x
# Test: [3,0,1] -> 2

print(missing_number([3,0,1]))