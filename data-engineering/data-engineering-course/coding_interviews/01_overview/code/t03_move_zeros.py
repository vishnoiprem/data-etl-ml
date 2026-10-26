"""Move all zeros in a list to the end while preserving the order of non-zero elements.

Time:  O(n) — single pass with a write pointer
Space: O(1) — in-place swaps
"""


def solve_move_zeros(nums):
    """Move all zeros to the end of the list, preserving order of non-zeros.

    >>> solve_move_zeros([0, 1, 0, 3, 12])
    [1, 3, 12, 0, 0]
    """
    write = 0  # next slot for the next non-zero element
    for read in range(len(nums)):
        if nums[read] != 0:
            # Swap into the write position. A plain assignment is
            # equivalent here because we've already moved any prior
            # non-zeros to their final homes; the only thing that
            # could be sitting at ``write`` is a zero.
            nums[write], nums[read] = nums[read], nums[write]
            write += 1
    return nums


if __name__ == "__main__":
    sample = [0, 1, 0, 3, 12]
    print(f"input:  {sample}")
    print(f"output: {solve_move_zeros(sample[:])}")
