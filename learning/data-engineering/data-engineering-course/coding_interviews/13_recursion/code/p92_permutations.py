"""Permutations — all orderings of nums.

Time:  O(n · n!) — n! permutations, each built in O(n)
Space: O(n) — recursion stack
"""


def solve_permutations(nums):
    """Return all permutations.

    >>> sorted(solve_permutations([1, 2, 3]))
    [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]
    """
    out = []
    used = [False] * len(nums)

    def backtrack(current):
        if len(current) == len(nums):
            out.append(current[:])
            return
        for i in range(len(nums)):
            if used[i]:
                continue
            used[i] = True
            current.append(nums[i])
            backtrack(current)
            current.pop()
            used[i] = False

    backtrack([])
    return out


if __name__ == "__main__":
    print(solve_permutations([1, 2, 3]))
