# def sortedSquares(nums):
#     # Write your code here
#     result = []
#     for row in range(len(nums)):
#         result.append(nums[row] * nums[row])
#
#     return sorted(result)


def sortedSquares(nums):
    # Write your code here
    n=len(nums)
    l=0
    r=n-1
    result = [0]*n
    pos=n-1
    while l<=r:
        first=nums[l]*nums[l]
        last=nums[r]*nums[r]

        if first>last:
            result[pos]=first
            l=l+1
        else:
            result[pos] = last
            r -= 1
        pos -= 1
    return result

nums=[-3,-1,0,2,9]

print(sortedSquares(nums))