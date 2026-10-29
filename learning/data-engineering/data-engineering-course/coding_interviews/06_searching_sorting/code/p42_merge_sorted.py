"""Merge Sorted Array — merge nums2 into nums1 in-place.

Time:  O(m + n) — fill from the back
Space: O(1)
"""


def solve_merge_sorted(nums1, m, nums2, n):
    """Merge nums2 into nums1 in-place; result stored in nums1.

    >>> solve_merge_sorted([1,2,3,0,0,0], 3, [2,5,6], 3)
    [1, 2, 2, 3, 5, 6]
    """
    write = m + n - 1
    i, j = m - 1, n - 1
    while j >= 0:
        if i >= 0 and nums1[i] > nums2[j]:
            nums1[write] = nums1[i]
            i -= 1
        else:
            nums1[write] = nums2[j]
            j -= 1
        write -= 1
    return nums1


if __name__ == "__main__":
    a = [1, 2, 3, 0, 0, 0]
    print(solve_merge_sorted(a, 3, [2, 5, 6], 3))
