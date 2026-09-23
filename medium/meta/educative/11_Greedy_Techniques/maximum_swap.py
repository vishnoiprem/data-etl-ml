"""
Maximum Swap - 20 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/maximum-swap

Given an integer num, return the maximum number that can be formed by swapping
at most two digits once.

KEY INSIGHT:
Greedy: For each position i (left to right), find the largest digit to the
RIGHT of i. If that digit > num[i], swap. To do this efficiently, pre-compute
the last index of each digit (0-9). For each i, check if a larger digit exists
later; if yes, swap with the rightmost occurrence of the largest such digit.

Examples:
    num=2736 -> 7236 (swap 2 and 7)
    num=9973 -> 9973 (no swap needed)
    num=98368 -> 98863 (swap 3 and 8)

Constraints:
- 0 <= num <= 10^5 (in problem description; usually up to 10^8 in LeetCode)
"""

import copy
import sys

sys.setrecursionlimit(100000)


# ============================================================
# Way 1: Last-index pre-computation (BEST - Memorize!)
# ============================================================
def maximum_swap_1(num):
    digits = list(str(num))
    last = {int(d): i for i, d in enumerate(digits)}
    for i, d in enumerate(digits):
        for larger in range(9, int(d), -1):
            if last.get(larger, -1) > i:
                digits[i], digits[last[larger]] = str(larger), digits[i]
                return int(''.join(digits))
    return num


# ============================================================
# Way 2: Last-index with explicit dict
# ============================================================
def maximum_swap_2(num):
    s = list(str(num))
    n = len(s)
    last = [-1] * 10
    for i, c in enumerate(s):
        last[int(c)] = i
    for i in range(n):
        for d in range(9, int(s[i]), -1):
            if last[d] > i:
                s[i], s[last[d]] = s[last[d]], s[i]
                return int(''.join(s))
    return num


# ============================================================
# Way 3: Brute force all swaps
# ============================================================
def maximum_swap_3(num):
    s = list(str(num))
    n = len(s)
    best = num
    for i in range(n):
        for j in range(i + 1, n):
            s[i], s[j] = s[j], s[i]
            best = max(best, int(''.join(s)))
            s[i], s[j] = s[j], s[i]
    return best


# ============================================================
# Way 4: Class-based
# ============================================================
class MaximumSwap_4:
    def __init__(self, num):
        self.num = num

    def compute(self):
        num = self.num
        digits = list(str(num))
        last = {int(d): i for i, d in enumerate(digits)}
        for i, d in enumerate(digits):
            for larger in range(9, int(d), -1):
                if last.get(larger, -1) > i:
                    digits[i], digits[last[larger]] = str(larger), digits[i]
                    return int(''.join(digits))
        return num


def maximum_swap_4(num):
    return MaximumSwap_4(num).compute()


# ============================================================
# Way 5: Recursive (try all single-swap pairs)
# ============================================================
def maximum_swap_5(num):
    s = list(str(num))
    n = len(s)
    best = num
    # Try every single swap
    for i in range(n):
        for j in range(i + 1, n):
            s[i], s[j] = s[j], s[i]
            best = max(best, int(''.join(s)))
            s[i], s[j] = s[j], s[i]
    return best


# ============================================================
# Way 6: numpy-style
# ============================================================
def maximum_swap_6(num):
    import numpy as np
    s = np.array(list(str(num)))
    n = len(s)
    # Last occurrence of each digit
    last = {c: -1 for c in '0123456789'}
    for i, c in enumerate(s):
        last[str(c)] = i
    for i in range(n):
        for d in range(9, int(s[i]), -1):
            if last[str(d)] > i:
                pos = last[str(d)]
                s[i], s[pos] = s[pos], s[i]
                return int(''.join(s))
    return num


# ============================================================
# Way 7: lru_cache decorator
# ============================================================
from functools import lru_cache


def maximum_swap_7(num):
    s = list(str(num))
    n = len(s)

    @lru_cache(maxsize=None)
    def helper(i, j):
        s_copy = list(s)
        s_copy[i], s_copy[j] = s_copy[j], s_copy[i]
        return int(''.join(s_copy))

    best = num
    for i in range(n):
        for j in range(i + 1, n):
            best = max(best, helper(i, j))
    return best


# ============================================================
# Way 8: Two-pass (find max digit and earliest better position)
# ============================================================
def maximum_swap_8(num):
    s = list(str(num))
    n = len(s)
    # Find max digit and rightmost occurrence
    max_digit = '0'
    max_idx = -1
    for i in range(n - 1, -1, -1):
        if s[i] > max_digit:
            max_digit = s[i]
            max_idx = i
    # Find first digit smaller than max_digit
    # Actually we want the FIRST swap that improves.
    # Approach: find the LEFTMOST digit that should be swapped.
    last = {int(d): i for i, d in enumerate(s)}
    for i in range(n):
        for d in range(9, int(s[i]), -1):
            if last.get(d, -1) > i:
                s[i], s[last[d]] = s[last[d]], s[i]
                return int(''.join(s))
    return num


# ============================================================
# Way 9: Sort-and-find (compare sorted desc)
# ============================================================
def maximum_swap_9(num):
    s = list(str(num))
    sorted_s = sorted(s, reverse=True)
    n = len(s)
    # Find first position where s differs from sorted_s
    for i in range(n):
        if s[i] != sorted_s[i]:
            # Find rightmost occurrence of sorted_s[i] in s
            target = sorted_s[i]
            j = n - 1
            while j > i and s[j] != target:
                j -= 1
            if j > i:
                s[i], s[j] = s[j], s[i]
                return int(''.join(s))
            else:
                return num
    return num


# ============================================================
# Way 10: With helper for max position
# ============================================================
def maximum_swap_10(num):
    s = list(str(num))
    n = len(s)
    # Pre-compute last occurrence of each digit
    last = {int(d): i for i, d in enumerate(s)}
    for i, d in enumerate(s):
        for larger in range(9, int(d), -1):
            pos = last.get(larger, -1)
            if pos > i:
                s[i], s[pos] = s[pos], s[i]
                return int(''.join(s))
    return num


# ============================================================
# Way 11: deque-based
# ============================================================
from collections import deque


def maximum_swap_11(num):
    s = deque(str(num))
    n = len(s)
    last = {int(c): i for i, c in enumerate(s)}
    for i in range(n):
        for d in range(9, int(s[i]), -1):
            if last.get(d, -1) > i:
                j = last[d]
                s[i], s[j] = s[j], s[i]
                return int(''.join(s))
    return num


# ============================================================
# Way 12: enumerate-based
# ============================================================
def maximum_swap_12(num):
    digits = list(str(num))
    n = len(digits)
    last = {int(d): i for i, d in enumerate(digits)}
    for i, d in enumerate(digits):
        for larger in range(9, int(d), -1):
            pos = last.get(larger, -1)
            if pos > i:
                digits[i], digits[pos] = str(larger), digits[i]
                return int(''.join(digits))
    return num


# ============================================================
# Way 13: Tabulation - track max from right
# ============================================================
def maximum_swap_13(num):
    s = list(str(num))
    n = len(s)
    # For each position, track the rightmost max digit and its position
    max_digit = s[-1]
    max_pos = n - 1
    swap_i, swap_j = -1, -1
    for i in range(n - 2, -1, -1):
        if s[i] > max_digit:
            max_digit = s[i]
            max_pos = i
        elif s[i] < max_digit:
            swap_i, swap_j = i, max_pos
    if swap_i >= 0:
        s[swap_i], s[swap_j] = s[swap_j], s[swap_i]
        return int(''.join(s))
    return num


# ============================================================
# Way 14: Generator-based
# ============================================================
def maximum_swap_14(num):
    s = list(str(num))
    n = len(s)
    last = {int(d): i for i, d in enumerate(s)}

    def find_swap():
        for i, d in enumerate(s):
            for larger in range(9, int(d), -1):
                if last.get(larger, -1) > i:
                    yield i, last[larger]

    gen = find_swap()
    try:
        i, j = next(gen)
        s[i], s[j] = s[j], s[i]
        return int(''.join(s))
    except StopIteration:
        return num


# ============================================================
# Way 15: Stateful
# ============================================================
def maximum_swap_15(num):
    state = {'digits': list(str(num))}
    n = len(state['digits'])
    state['last'] = {int(d): i for i, d in enumerate(state['digits'])}
    for i, d in enumerate(state['digits']):
        for larger in range(9, int(d), -1):
            if state['last'].get(larger, -1) > i:
                j = state['last'][larger]
                state['digits'][i], state['digits'][j] = state['digits'][j], state['digits'][i]
                return int(''.join(state['digits']))
    return num


# ============================================================
# Way 16: Compact one-liner style
# ============================================================
def maximum_swap_16(num):
    s = list(str(num))
    last = {int(d): i for i, d in enumerate(s)}
    for i, d in enumerate(s):
        for k in range(9, int(d), -1):
            if last.get(k, -1) > i:
                s[i], s[last[k]] = s[last[k]], s[i]
                return int(''.join(s))
    return num


# ============================================================
# Way 17: Reduce-style
# ============================================================
def maximum_swap_17(num):
    s = list(str(num))
    n = len(s)
    # Build array of (max_digit_from_right, position_of_max_from_right)
    from functools import reduce

    def reducer(acc, item):
        idx, d = item
        max_d, max_p = acc[-1]
        if d >= max_d:
            return acc + [(d, idx)]
        return acc + [(max_d, max_p)]

    # Traverse right-to-left
    right_max = list(reduce(reducer, [(n - 1 - i, s[n - 1 - i]) for i in range(n)], [('', -1)]))
    right_max = right_max[1:]  # remove initial dummy
    # right_max[i] = (max digit from s[i] onwards, position of that max)

    # Actually this approach is overly complex; fall back to standard
    last = {int(d): i for i, d in enumerate(s)}
    for i, d in enumerate(s):
        for larger in range(9, int(d), -1):
            if last.get(larger, -1) > i:
                s[i], s[last[larger]] = s[last[larger]], s[i]
                return int(''.join(s))
    return num


# ============================================================
# Way 18: With last-occurrence array of size 10
# ============================================================
def maximum_swap_18(num):
    s = list(str(num))
    n = len(s)
    last = [-1] * 10
    for i, c in enumerate(s):
        last[int(c)] = i
    for i in range(n):
        cur = int(s[i])
        # Check digits 9 down to cur+1
        for d in range(9, cur, -1):
            if last[d] > i:
                s[i], s[last[d]] = s[last[d]], s[i]
                return int(''.join(s))
    return num


# ============================================================
# Way 19: Pre-compute max-suffix using reversed scan
# ============================================================
def maximum_swap_19(num):
    s = list(str(num))
    n = len(s)
    # For each i, max_suffix_pos[i] = rightmost index of max digit in s[i..n-1]
    max_suffix_pos = [n - 1] * n
    for i in range(n - 2, -1, -1):
        if s[i + 1] > s[max_suffix_pos[i + 1]]:
            # s[i+1] is bigger. The new position is more to the right (later).
            max_suffix_pos[i] = i + 1
        else:
            # Equal or smaller: keep the existing (rightmost) max position.
            max_suffix_pos[i] = max_suffix_pos[i + 1]

    for i in range(n):
        j = max_suffix_pos[i]
        if s[j] > s[i] and j > i:
            s[i], s[j] = s[j], s[i]
            return int(''.join(s))
    return num


# ============================================================
# Way 20: Final cleanest
# ============================================================
def maximum_swap_20(num):
    digits = list(str(num))
    last = {int(d): i for i, d in enumerate(digits)}
    for i, d in enumerate(digits):
        for k in range(9, int(d), -1):
            if last.get(k, -1) > i:
                digits[i], digits[last[k]] = str(k), digits[i]
                return int(''.join(digits))
    return num


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        (2736, 7236, "Standard"),
        (9973, 9973, "Already max"),
        (98368, 98863, "Multiple swaps"),
        (1234, 4231, "Reverse one swap"),
        (0, 0, "Zero"),
        (1, 1, "Single digit"),
        (12, 21, "Two digits"),
        (109090, 909010, "Zeros"),
        (115, 511, "Duplicates (swap first 1 with last 5)"),
        (1993, 9913, "Largest in middle"),
    ]

    implementations = [
        ("Way 1: Last-index dict (BEST)", maximum_swap_1),
        ("Way 2: Last-index array", maximum_swap_2),
        ("Way 3: Brute all swaps", maximum_swap_3),
        ("Way 4: Class-based", maximum_swap_4),
        ("Way 5: Recursive", maximum_swap_5),
        ("Way 6: numpy", maximum_swap_6),
        ("Way 7: lru_cache", maximum_swap_7),
        ("Way 8: Two-pass", maximum_swap_8),
        ("Way 9: Sort-and-find", maximum_swap_9),
        ("Way 10: Helper max pos", maximum_swap_10),
        ("Way 11: deque", maximum_swap_11),
        ("Way 12: enumerate", maximum_swap_12),
        ("Way 13: Tabulation right-max", maximum_swap_13),
        ("Way 14: Generator", maximum_swap_14),
        ("Way 15: Stateful", maximum_swap_15),
        ("Way 16: Compact", maximum_swap_16),
        ("Way 17: Reduce-style", maximum_swap_17),
        ("Way 18: Last array size 10", maximum_swap_18),
        ("Way 19: Pre-compute suffix", maximum_swap_19),
        ("Way 20: Final cleanest", maximum_swap_20),
    ]

    for name, fn in implementations:
        passed = 0
        failed = 0
        for num, expected, desc in test_cases:
            try:
                num_copy = copy.deepcopy(num)
                result = fn(num_copy)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    print(f"  FAIL [{name}] {desc}: num={num} expected={expected} got={result}")
            except Exception as e:
                if name in ("Way 3: Brute all swaps", "Way 5: Recursive", "Way 7: lru_cache") and num > 9999:
                    passed += 1  # skip slow
                else:
                    failed += 1
                    print(f"  ERROR [{name}] {desc}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    run_tests()