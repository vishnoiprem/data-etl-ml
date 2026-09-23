"""
Problem 9 (Medium) — Kth Missing Positive Number
Pattern shape: E — Math formula + BS

Given an array of strictly increasing positive integers and an integer k,
return the kth missing positive integer. The algorithm must be O(log n).

Examples
--------
>>> kth_missing([2, 3, 4, 7, 11], 5)
9       # missing: 1, 5, 6, 8, 9, 10, ... -> 5th is 9
>>> kth_missing([1, 2, 3, 4], 5)
9       # no gaps in arr; 5th missing is 9 (after 1..4, missing are 5,6,7,8,9,...)
>>> kth_missing([2], 1)
1

How to think (interview script)
------------------------------
"Key observation: at any index i in a strictly-increasing sorted array
of positive ints, the number of missing positives up to (and including)
nums[i] is:
    missing(nums, i) = nums[i] - i - 1
Why? nums[i] itself is the (i+1)-th positive if there were no gaps, so
the gap count is nums[i] - (i+1). Equivalently: nums[i] - i - 1.

That formula is monotonic in i -- as i grows, missing(i) grows (or stays
equal when nums[i+1] == nums[i]+1). So I binary search for the first
index where missing(i) >= k.

Two cases at the end:
  - We never find such an index: the answer lives AFTER the array. By
    the time we reach arr[n-1], we've 'used up' arr[n-1] - n missing
    slots. The kth missing is therefore
    arr[n-1] + (k - missing(n-1)).
  - We found an index where missing(i) >= k: the kth missing sits in
    the gap ending at arr[i]. The number of integers 'consumed' before
    arr[i] is i (because indices 0..i-1 occupy i actual positive
    integers if no gaps, but with gaps we've consumed exactly i actual
    integers). So the answer is k + i.

A neat shortcut: answer = k + i, where i is the number of arr-elements
<= the answer. Equivalently: arr[j] <= answer for exactly i values of j.

Complexity: O(log n) time, O(1) space.

Edge cases
----------
- n == 0: every positive is missing; answer = k
- k smaller than the first gap: answer < arr[0]
- All elements consecutive: answer = k + n
- k much larger than arr[-1] - n: answer > arr[-1]

Follow-ups the interviewer may ask
-----------------------------------
- "Can you do this without binary search?"
  Answer: yes -- track the previous value and the running gap count,
  but that's O(n).
- "What if the array isn't strictly increasing?"
  Answer: not defined by the problem; you'd need to sort first, losing
  the O(log n) guarantee unless we exploit something else.
"""


def kth_missing(arr: list[int], k: int) -> int:
    """Return the k-th missing positive integer in `arr`."""
    n = len(arr)
    if n == 0:
        return k

    def missing(i: int) -> int:
        # Number of positives missing from 1 up to (and including) arr[i].
        return arr[i] - i - 1

    # Find the smallest index i such that missing(i) >= k.
    # 'lo' stays valid; 'hi' is the first such index (exclusive at end).
    lo, hi = 0, n  # hi exclusive — if no index qualifies, answer is past the array
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if missing(mid) >= k:
            hi = mid
        else:
            lo = mid + 1

    # After the loop, lo == hi == first index with missing(i) >= k, or n if none.
    if lo == n:
        # kth missing is past the array.
        return arr[n - 1] + (k - missing(n - 1))
    # kth missing sits in the gap just before arr[lo].
    # The lo elements before arr[lo] consume exactly lo positive integers
    # (they ARE those integers when there are no gaps in 1..arr[lo]-1).
    # Wait — they consume arr[lo] - (lo) actual positives up to arr[lo]-1.
    # The first missing is somewhere in [arr[lo-1]+1, arr[lo]-1] (or 1 if lo==0).
    # Cleanly: number of arr-elements <= answer is exactly lo (since arr[lo] is
    # the (lo+1)-th element and is > answer). So answer = k + lo.
    return k + lo


if __name__ == "__main__":
    f = kth_missing
    assert f([2, 3, 4, 7, 11], 5) == 9
    assert f([1, 2, 3, 4], 5) == 9
    assert f([2], 1) == 1
    assert f([2, 3], 2) == 4
    assert f([1, 3, 5, 7], 4) == 8
    assert f([], 5) == 5
    assert f([3, 5, 9], 4) == 6
    assert f([1, 2, 3, 4], 2) == 6   # missing: 5, 6 -> 2nd is 6
    assert f([2, 3, 7, 11], 5) == 9  # 1, 4, 5, 6, 8 -> 5th is 9 (after 11)
    print("All tests passed for kth_missing_positive.")
