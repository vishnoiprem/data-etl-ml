"""
Problem 6 (Easy) — Search Insert Position
Pattern shape: B — Boundary / lower_bound

Given a sorted array of distinct integers and a target value, return the
index if the target is found. If not, return the index where it would be
if it were inserted in order. The algorithm must run in O(log n).

Examples
--------
>>> search_insert([1, 3, 5, 6], 5)
2
>>> search_insert([1, 3, 5, 6], 2)
1
>>> search_insert([1, 3, 5, 6], 7)
4
>>> search_insert([1, 3, 5, 6], 0)
0

How to think (interview script)
------------------------------
"I need the leftmost index where arr[i] >= target. That is exactly the
lower_bound definition. I can binary-search for it.

Search space: [0, n]. Inclusive on both sides. Answer is always defined
even if target is bigger than every element.

Predicate P(i): arr[i] >= target. This is True on the right side of the
answer, False on the left side — exactly the TTTF...FFFF pattern we want.

Loop: while lo < hi, mid = lo + (hi - lo) // 2.
  - If arr[mid] >= target: hi = mid   (mid might be the answer, keep it)
  - Else:                  lo = mid + 1 (mid is provably not the answer)

When lo == hi, that's the answer. Return it.

This is the same code as Python's bisect_left, by the way — I should
mention that to signal I know the standard library."

Complexity: O(log n) time, O(1) space.

Edge cases
----------
- Empty array → return 0
- Target smaller than every element → return 0
- Target larger than every element → return n
- Target equals an element → return that index (the FIRST occurrence if there were duplicates)

Follow-ups the interviewer may ask
-----------------------------------
- "What if there are duplicates? Make sure you return the FIRST occurrence."
  Answer: same code already does that — that's the definition of lower_bound.
- "Implement using bisect in one line." Answer: `bisect.bisect_left(arr, target)`.
- "What about a rotated array?" Answer: different problem (#1 in this folder).
"""


def search_insert(nums: list[int], target: int) -> int:
    """Return the index where `target` should be inserted to keep `nums` sorted."""
    lo, hi = 0, len(nums)  # hi is exclusive — it's the 'n' fallback position
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] >= target:
            hi = mid
        else:
            lo = mid + 1
    return lo


if __name__ == "__main__":
    # Quick sanity checks
    assert search_insert([1, 3, 5, 6], 5) == 2
    assert search_insert([1, 3, 5, 6], 2) == 1
    assert search_insert([1, 3, 5, 6], 7) == 4
    assert search_insert([1, 3, 5, 6], 0) == 0
    assert search_insert([], 5) == 0
    assert search_insert([1], 0) == 0
    assert search_insert([1], 1) == 0
    assert search_insert([1], 2) == 1
    print("All tests passed for search_insert_position.")
