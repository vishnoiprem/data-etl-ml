"""House Robber — max loot with no two adjacent houses.

Time:  O(n)
Space: O(1) — two scalars
"""


def solve_house_robber(nums):
    """Return the max amount that can be robbed.

    >>> solve_house_robber([1, 2, 3, 1])
    4
    """
    if not nums:
        return 0
    if len(nums) == 1:
        return nums[0]
    prev, curr = 0, 0
    for val in nums:
        prev, curr = curr, max(curr, prev + val)
    return curr


if __name__ == "__main__":
    print(solve_house_robber([1, 2, 3, 1]))
