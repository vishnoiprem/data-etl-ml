"""
Problem 8 (Medium) — Find K Closest Elements
Pattern shape: B — Boundary / BS on the left edge of a window

Given a sorted integer array arr, two integers k and x, find the k
closest elements to x in the array. The result should also be sorted in
ascending order. The difference between arr[i] and x is the absolute
value |arr[i] - x|; ties go to the smaller value.

Examples
--------
>>> find_closest_elements([1, 2, 3, 4, 5], 4, 3)
[1, 2, 3, 4]
>>> find_closest_elements([1, 1, 2, 3, 4, 5], 4, -1)
[1, 1, 2, 3]

How to think (interview script)
------------------------------
"The answer is a contiguous window of length k in arr (because arr is
sorted, the k closest elements always form a contiguous block — I should
state that as a lemma in the interview).

So the problem reduces to: where does the window START? If I parametrize
the answer as `left`, then `left` lives in [0, n - k]. I need to
binary-search for the best `left`.

Two adjacent starting positions compete: `left` and `left + 1`. The
window starting at `left` is 'better' iff moving the right edge inward
(by losing arr[left]) doesn't beat moving the left edge outward (by
gaining arr[left + k]). Formally:

  dist(left) = x - arr[left]
  dist(left + k) = arr[left + k] - x

If dist(left) > dist(left + k), then arr[left + k] is closer to x than
arr[left], so we should slide the window right: left += 1.
Otherwise the current left is fine: keep it (hi = mid).

This gives us the SAME lower_bound template: discard the half that is
provably NOT the best starting position.

  P(left) := 'the window starting at `left` is at least as good as
             starting at `left + 1`'

That predicate is monotonic in `left`:
  - P(left) is True means the current window wins; we could move left
    further left without losing (True on the right side of the boundary).
  - P(left) is False means the next window is strictly better; move left
    rightward.

Loop: while lo < hi:
    mid = lo + (hi - lo) // 2
    if x - arr[mid] > arr[mid + k] - x:
        lo = mid + 1
    else:
        hi = mid

Return arr[lo : lo + k]."

Complexity: O(log(n - k) + k) time, O(1) extra space (output excluded).

Edge cases
----------
- k == 0: return []
- k == n: return arr
- x smaller than everything: window is the leftmost k elements
- x larger than everything: window is the rightmost k elements
- Equal distance: tie-break goes to the smaller element (handled by the
  strict inequality in our check)

Follow-ups the interviewer may ask
-----------------------------------
- "Why is the answer always a contiguous block?"
  Answer: If two chosen elements a, b with a < b had a non-chosen c
  between them with a < c < b, then |c - x| < max(|a-x|, |b-x|), so c
  should also be chosen. Contradiction.
- "How would you solve this with two pointers instead?"
  Answer: extend a window around x until it has size k. O(n) time.
- "Can you avoid the sort step at the end?"
  Answer: the answer is always sorted in ascending order; we just slice.
"""
from typing import List


def find_closest_elements(arr: List[int], k: int, x: int) -> List[int]:
    """Return the k elements of arr closest to x, sorted ascending."""
    n = len(arr)
    if k == 0:
        return []
    if k >= n:
        return arr[:]

    # Binary search for the best starting index of the window of size k.
    lo, hi = 0, n - k
    while lo < hi:
        mid = lo + (hi - lo) // 2
        # Is the next window strictly better than this one?
        if x - arr[mid] > arr[mid + k] - x:
            lo = mid + 1
        else:
            hi = mid
    return arr[lo : lo + k]


if __name__ == "__main__":
    f = find_closest_elements
    assert f([1, 2, 3, 4, 5], 4, 3) == [1, 2, 3, 4]
    assert f([1, 1, 2, 3, 4, 5], 4, -1) == [1, 1, 2, 3]
    assert f([1, 2, 3, 4, 5], 4, 6) == [2, 3, 4, 5]
    assert f([1, 2, 3, 4, 5], 4, -10) == [1, 2, 3, 4]
    assert f([0, 0, 1, 2, 3, 3, 4, 7, 7, 8], 3, 5) == [3, 3, 4]
    assert f([1], 1, 1) == [1]
    assert f([1, 2], 1, 1) == [1]
    print("All tests passed for find_k_closest_elements.")
