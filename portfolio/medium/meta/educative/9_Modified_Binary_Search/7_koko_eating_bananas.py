"""
Problem 7 (Medium) — Koko Eating Bananas
Pattern shape: D — Binary search on the answer

Koko loves to eat bananas. There are n piles of bananas, the ith pile
has piles[i] bananas. The guards have gone away and will come back in h
hours. Koko can decide her bananas-per-hour eating speed k. Each hour
she chooses a pile and eats k bananas from it (or the whole pile if it
has fewer than k). She eats at speed k per chosen hour, even if she
finishes a pile early.

Return the minimum integer k such that she can eat all the bananas
within h hours.

Examples
--------
>>> min_eating_speed([3, 6, 7, 11], 8)
4
>>> min_eating_speed([30, 11, 23, 4, 20], 5)
30
>>> min_eating_speed([30, 11, 23, 4, 20], 6)
23

How to think (interview script)
------------------------------
"This is the textbook 'binary search on the answer' problem.

Observation: the answer k lives in the range [1, max(piles)]. Below 1
doesn't make sense; above max(piles) she always finishes each pile in
one hour and the answer becomes 'number of piles'.

Monotonic predicate P(k) := 'with speed k, Koko finishes in <= h hours'.
If P(k) is true, then P(k+1) is also true (eating faster only helps).
If P(k) is false, then P(k-1) is also false. So P is monotone, which
means we can binary search.

feasibility(k): sum over piles of ceil(pile / k), compared to h.
  - if sum <= h: P(k) is True -> try smaller k
  - else:         P(k) is False -> need larger k

This is the lower_bound pattern: find the smallest k with P(k) True.

Implementation details: use integer ceiling math: (pile + k - 1) // k.

Total complexity: O(n * log(max(piles))) time, O(1) space."

Complexity: O(n log M) time where M = max(piles). O(1) space.

Edge cases
----------
- h == len(piles): answer is max(piles)
- h very large: answer is 1
- piles[i] == 0 not possible per problem (positive ints)
- Single pile, single hour -> answer = piles[0]

Follow-ups the interviewer may ask
-----------------------------------
- "What's the maximum possible k?"
  Answer: max(piles), since at that speed every pile takes <= 1 hour.
- "Can you parallelize across multiple Koko clones?"
  Answer: different problem — that becomes scheduling / capacity planning.
- "Same problem but Koko eats at most H hours, not exactly H?"
  Answer: usually identical, since earlier finish is always feasible.
- "How would you solve it with a different feasibility function?"
  Answer: only the predicate changes — the BS template is the same.
"""
import math
from typing import List


def min_eating_speed(piles: List[int], h: int) -> int:
    """Smallest integer eating speed k that lets Koko finish in h hours."""
    if h <= 0 or not piles:
        return 0

    def feasible(k: int) -> bool:
        # Hours needed at speed k across all piles.
        hours = 0
        for p in piles:
            # ceil(p / k) without using floats
            hours += (p + k - 1) // k
            if hours > h:        # short-circuit for speed
                return False
        return True

    lo, hi = 1, max(piles)
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if feasible(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


if __name__ == "__main__":
    f = min_eating_speed
    assert f([3, 6, 7, 11], 8) == 4
    assert f([30, 11, 23, 4, 20], 5) == 30
    assert f([30, 11, 23, 4, 20], 6) == 23
    assert f([1, 1, 1, 1], 4) == 1
    assert f([100], 1) == 100
    assert f([10, 20, 30], 100) == 1
    print("All tests passed for koko_eating_bananas.")
