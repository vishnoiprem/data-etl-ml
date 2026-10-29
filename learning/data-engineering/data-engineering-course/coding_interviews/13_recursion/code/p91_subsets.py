"""Subsets — all subsets (the power set).

Time:  O(n · 2^n) — there are 2^n subsets, each built in O(n)
Space: O(n) — recursion stack (output not counted)
"""


def solve_subsets(nums):
    """Return every subset of nums.

    >>> sorted([sorted(s) for s in solve_subsets([1, 2, 3])])
    [[], [1], [1, 2], [1, 2, 3], [1, 3], [2], [2, 3], [3]]
    """
    out = [[]]

    def backtrack(start, current):
        for i in range(start, len(nums)):
            current.append(nums[i])
            out.append(current[:])
            backtrack(i + 1, current)
            current.pop()

    backtrack(0, [])
    return out


if __name__ == "__main__":
    print(solve_subsets([1, 2, 3]))
