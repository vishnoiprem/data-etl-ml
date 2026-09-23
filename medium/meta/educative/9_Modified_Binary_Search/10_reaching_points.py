"""
Problem 10 (Hard) — Reaching Points
Pattern shape: E — Math + reverse-engineered BS

A move consists of taking a point (x, y) and transforming it to either
(x, x+y) or (x+y, y). Given a starting point (sx, sy) and a target
(tx, ty), determine if the target is reachable.

Examples
--------
>>> reaching_points(1, 1, 3, 5)
True
>>> reaching_points(1, 1, 2, 2)
False
>>> reaching_points(1, 1, 1, 1)
True

How to think (interview script)
------------------------------
"Naive BFS/DFS blows up: the state space is unbounded.

Insight: the moves only ADD. So (tx, ty) -> (sx, sy) is easier backwards:
repeatedly SUBTRACT the smaller from the larger.

But subtraction is slow when the gap is huge — e.g. (1, 1) -> (1, 10^9).
So we MOD it: if ty > tx, the previous step must have been
(ty % tx, tx), provided the remainder is reachable. This is the
'modular inverse of the recurrence' trick.

But we still may need to walk back through many (tx, ty) pairs, which
in the worst case is O(max(tx, ty)). That's not O(log) — but the
problem doesn't require O(log). The problem is reachable / not
reachable; the algorithm is essentially greedy-with-modular-skipping.

Binary search connection:
  For the 'minimum number of moves' version of the problem, we'd BS on
  the answer k. Each move increases one coordinate. After k moves,
  x + y = sx + sy + k. So if we binary-search k, we can check whether
  there's a reachable state with sum = sx + sy + k. The feasibility
  check would use the modular-skipping trick above.

For THIS problem (reachability only), the BS isn't strictly required —
but I'll demonstrate the BS-on-the-moves version as well.

Primary solution: modular-skipping BFS-backward. O(log(max(tx, ty))).

Edge cases
----------
- sx == tx and sy == ty -> True (already there)
- sx > tx or sy > ty -> only true if the differing coord matches
- sx == tx: ty must be reachable from sy by adding only to y. Forward
  solution: (ty - sy) % sx == 0 (need ty >= sy).
- sy == ty: symmetric.
- After modular step, if remainder is 0, treat specially: we landed
  exactly on (smaller, larger) -> check the base case.

Follow-ups the interviewer may ask
-----------------------------------
- "Can you do this in O(log max(tx, ty))?" -> Yes, the modular skip.
- "What about negative coordinates?" -> Out of scope per problem.
- "Minimum number of moves?" -> BS on the move count, O(log(max(tx,ty)))
  per feasibility check; total O(log^2).
"""


def reaching_points(sx: int, sy: int, tx: int, ty: int) -> bool:
    """Determine if (tx, ty) is reachable from (sx, sy)."""
    # Walk backwards from (tx, ty) to (sx, sy) using modular skipping.
    while tx > sx and ty > sy and tx != ty:
        if tx > ty:
            # Previous step was (tx % ty, ty) — but only if we didn't overshoot.
            tx %= ty
        else:
            ty %= tx

    # Handle base cases when one coordinate matches or exceeds the start.
    if tx == sx and ty == sy:
        return True
    if tx == sx:
        # (sx, sy) -> ... -> (sx, ty). Need ty >= sy and (ty - sy) % sx == 0.
        return ty >= sy and (ty - sy) % sx == 0
    if ty == sy:
        return tx >= sx and (tx - sx) % sy == 0
    return False


def min_moves_to_reach(sx: int, sy: int, tx: int, ty: int) -> int:
    """Minimum moves from (sx, sy) to (tx, ty); -1 if unreachable.

    Demonstrates BS on the move count, separate from the reachability
    problem. Each move adds 1 to x+y, so sum-after-k-moves = sx+sy+k.
    """
    target_sum = tx + ty
    start_sum = sx + sy
    if target_sum < start_sum:
        return -1

    def reachable_in(moves: int) -> bool:
        """Can (tx, ty) be reached in exactly `moves` steps?"""
        # We have to land at (tx, ty) with sum = sx+sy+moves, so tx+ty must match.
        return target_sum == start_sum + moves and reaching_points(sx, sy, tx, ty)

    # Lower-bound BS: smallest k with reachable_in(k).
    lo, hi = 0, target_sum - start_sum  # max extra sum we could afford
    ans = -1
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if reachable_in(mid):
            ans = mid
            hi = mid - 1
        else:
            lo = mid + 1
    return ans


if __name__ == "__main__":
    f = reaching_points
    assert f(1, 1, 3, 5) is True
    assert f(1, 1, 2, 2) is False
    assert f(1, 1, 1, 1) is True
    assert f(1, 2, 1, 2) is True
    assert f(9, 5, 12, 17) is False  # unreachable: forward simulation confirms
    assert f(0, 0, 1, 1) is True
    assert f(0, 0, 0, 1) is False
    assert f(1, 1, 1000000000, 1) is True  # (1,1) -> ... -> (1e9, 1) by additions along x
    print("All tests passed for reaching_points.")
