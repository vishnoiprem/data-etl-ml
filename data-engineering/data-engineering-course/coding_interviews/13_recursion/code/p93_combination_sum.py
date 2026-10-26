"""Combination Sum — reuse elements unlimited times.

Time:  O(2^n · n) worst case — each path has at most n additions
Space: O(n) — recursion stack
"""


def solve_combination_sum(candidates, target):
    """Return all unique combinations summing to ``target``.

    >>> sorted([sorted(c) for c in solve_combination_sum([2,3,6,7], 7)])
    [[7], [2, 2, 3]]
    """
    candidates = sorted(candidates)
    out = []

    def backtrack(start, remaining, current):
        if remaining == 0:
            out.append(current[:])
            return
        for i in range(start, len(candidates)):
            # If the candidate is larger than the remaining sum, prune.
            if candidates[i] > remaining:
                break
            current.append(candidates[i])
            # Reuse allowed: pass i, not i + 1.
            backtrack(i, remaining - candidates[i], current)
            current.pop()

    backtrack(0, target, [])
    return out


if __name__ == "__main__":
    print(solve_combination_sum([2, 3, 6, 7], 7))
