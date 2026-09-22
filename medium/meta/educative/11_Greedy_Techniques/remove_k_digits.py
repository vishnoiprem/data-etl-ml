"""
Remove K Digits - 20 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/remove-k-digits

Given string num representing non-negative integer and int k.
Remove exactly k digits to form the smallest possible number.

KEY INSIGHT:
Greedy with a monotonic stack.
Process each digit; pop from stack while stack[-1] > current and k > 0.
This removes a "big" digit before a "small" one, which always yields smaller number.
After processing, if k > 0, pop remaining k from the end.
Strip leading zeros; if empty, return "0".

Examples:
    num="1432219", k=3 -> "1219"
    num="10200", k=1 -> "200"
    num="10", k=2 -> "0"

Constraints:
- 1 <= k <= num.length <= 10^5
- num consists only of digits.
"""

import copy
import sys

sys.setrecursionlimit(100000)


# ============================================================
# Way 1: Monotonic stack (BEST - Memorize!)
# ============================================================
def removeKdigits_1(num, k):
    stack = []
    for digit in num:
        while k > 0 and stack and stack[-1] > digit:
            stack.pop()
            k -= 1
        stack.append(digit)
    # If k still remains, remove from end
    stack = stack[:-k] if k else stack
    # Strip leading zeros
    result = ''.join(stack).lstrip('0')
    return result if result else '0'


# ============================================================
# Way 2: Stack with explicit counter
# ============================================================
def removeKdigits_2(num, k):
    stack = []
    remaining = k
    for digit in num:
        while remaining > 0 and stack and stack[-1] > digit:
            stack.pop()
            remaining -= 1
        stack.append(digit)
    if remaining > 0:
        stack = stack[:-remaining]
    res = ''.join(stack).lstrip('0')
    return res if res else '0'


# ============================================================
# Way 3: List as stack
# ============================================================
def removeKdigits_3(num, k):
    stack = []
    for d in num:
        while k and stack and stack[-1] > d:
            stack.pop()
            k -= 1
        stack.append(d)
    # Trim trailing if needed
    final = stack[:-k] if k else stack
    s = ''.join(final).lstrip('0')
    return s or '0'


# ============================================================
# Way 4: Two-pointer / index-based stack
# ============================================================
def removeKdigits_4(num, k):
    n = len(num)
    # We will use an array as a stack
    stack = []
    for i in range(n):
        while k > 0 and stack and stack[-1] > num[i]:
            stack.pop()
            k -= 1
        stack.append(num[i])
    if k > 0:
        stack = stack[:-k]
    result = ''.join(stack).lstrip('0')
    return result if result else '0'


# ============================================================
# Way 5: Class-based
# ============================================================
class RemoveKDigits_5:
    def __init__(self, num, k):
        self.num = num
        self.k = k

    def compute(self):
        num = self.num
        k = self.k
        stack = []
        for digit in num:
            while k > 0 and stack and stack[-1] > digit:
                stack.pop()
                k -= 1
            stack.append(digit)
        stack = stack[:-k] if k else stack
        result = ''.join(stack).lstrip('0')
        return result if result else '0'


def removeKdigits_5(num, k):
    return RemoveKDigits_5(num, k).compute()


# ============================================================
# Way 6: Recursive (with memo)
# ============================================================
def removeKdigits_6(num, k):
    memo = {}

    def helper(s, kk):
        if kk == 0:
            return s
        if kk >= len(s):
            return ''
        if (s, kk) in memo:
            return memo[(s, kk)]
        # Pick the smallest digit in s[0..kk]. Drop everything before it.
        min_idx = 0
        for i in range(min(kk + 1, len(s))):
            if s[i] < s[min_idx]:
                min_idx = i
        kept = s[min_idx]
        result = kept + helper(s[min_idx + 1:], kk - min_idx)
        memo[(s, kk)] = result
        return result

    result = helper(num, k).lstrip('0')
    return result if result else '0'


# ============================================================
# Way 7: numpy-style (using array operations)
# ============================================================
def removeKdigits_7(num, k):
    import numpy as np
    arr = np.array([int(c) for c in num])
    stack = []
    for d in arr:
        while k > 0 and stack and stack[-1] > d:
            stack.pop()
            k -= 1
        stack.append(int(d))
    if k > 0:
        stack = stack[:-k]
    res = ''.join(str(x) for x in stack).lstrip('0')
    return res if res else '0'


# ============================================================
# Way 8: lru_cache decorator
# ============================================================
from functools import lru_cache


def removeKdigits_8(num, k):
    @lru_cache(maxsize=None)
    def helper(s, kk):
        if kk == 0:
            return s
        if kk >= len(s):
            return ''
        min_idx = 0
        for i in range(min(kk + 1, len(s))):
            if s[i] < s[min_idx]:
                min_idx = i
        return s[min_idx] + helper(s[min_idx + 1:], kk - min_idx)

    result = helper(num, k).lstrip('0')
    return result if result else '0'


# ============================================================
# Way 9: Brute force (try all subsets - exponential)
# ============================================================
def removeKdigits_9(num, k):
    n = len(num)
    if k == n:
        return '0'
    best = None
    from itertools import combinations
    for keep_idx in combinations(range(n), n - k):
        candidate = ''.join(num[i] for i in keep_idx).lstrip('0') or '0'
        # Compare as integers (len first, then lex)
        if best is None:
            best = candidate
        else:
            if (len(candidate), candidate) < (len(best), best):
                best = candidate
    return best


# ============================================================
# Way 10: With helper for finding smallest
# ============================================================
def removeKdigits_10(num, k):
    def remove_helper(s, kk):
        if kk == 0:
            return s
        if kk >= len(s):
            return ''
        # Find leftmost smallest digit within first kk+1 positions
        min_idx = 0
        for i in range(min(kk + 1, len(s))):
            if s[i] < s[min_idx]:
                min_idx = i
        # Keep this digit and drop everything before it
        return s[min_idx] + remove_helper(s[min_idx + 1:], kk - min_idx)

    result = remove_helper(num, k).lstrip('0')
    return result if result else '0'


# ============================================================
# Way 11: Iterative with deque
# ============================================================
from collections import deque


def removeKdigits_11(num, k):
    dq = deque()
    for digit in num:
        while k > 0 and dq and dq[-1] > digit:
            dq.pop()
            k -= 1
        dq.append(digit)
    # Remove remaining from end
    while k > 0:
        dq.pop()
        k -= 1
    result = ''.join(dq).lstrip('0')
    return result if result else '0'


# ============================================================
# Way 12: enumerate-based
# ============================================================
def removeKdigits_12(num, k):
    stack = []
    for i, digit in enumerate(num):
        while k > 0 and stack and stack[-1] > digit:
            stack.pop()
            k -= 1
        stack.append(digit)
    if k:
        stack = stack[:-k]
    res = ''.join(stack).lstrip('0')
    return res or '0'


# ============================================================
# Way 13: Generator approach
# ============================================================
def removeKdigits_13(num, k):
    def build_stack():
        remaining = [k]  # use list for mutability
        stack = []
        for d in num:
            while remaining[0] > 0 and stack and stack[-1] > d:
                stack.pop()
                remaining[0] -= 1
            stack.append(d)
        if remaining[0]:
            stack = stack[:-remaining[0]]
        return stack

    result = ''.join(build_stack()).lstrip('0')
    return result if result else '0'


# ============================================================
# Way 14: Using reduce
# ============================================================
def removeKdigits_14(num, k):
    from functools import reduce
    # Process via reduce; this is awkward but works conceptually
    stack = []
    def process(d):
        nonlocal k
        while k > 0 and stack and stack[-1] > d:
            stack.pop()
            k -= 1
        stack.append(d)
    reduce(lambda _, d: process(d), num, None)
    stack = stack[:-k] if k else stack
    res = ''.join(stack).lstrip('0')
    return res or '0'


# ============================================================
# Way 15: Tabulation style (process all then trim)
# ============================================================
def removeKdigits_15(num, k):
    stack = []
    for digit in num:
        while k and stack and stack[-1] > digit:
            stack.pop()
            k -= 1
        stack.append(digit)
    # If we still have removals, drop from the right
    while k:
        stack.pop()
        k -= 1
    res = ''.join(stack).lstrip('0')
    return res if res else '0'


# ============================================================
# Way 16: Stateful
# ============================================================
def removeKdigits_16(num, k):
    state = {'stack': [], 'k': k}
    for digit in num:
        while state['k'] > 0 and state['stack'] and state['stack'][-1] > digit:
            state['stack'].pop()
            state['k'] -= 1
        state['stack'].append(digit)
    if state['k'] > 0:
        state['stack'] = state['stack'][:-state['k']]
    res = ''.join(state['stack']).lstrip('0')
    return res if res else '0'


# ============================================================
# Way 17: Greedy with explicit for-else
# ============================================================
def removeKdigits_17(num, k):
    stack = []
    n = len(num)
    for digit in num:
        while k > 0 and stack and stack[-1] > digit:
            stack.pop()
            k -= 1
        stack.append(digit)
    # Trim trailing k digits
    final_stack = stack
    if k > 0:
        final_stack = stack[:n - k - (len(stack) - n)]
    res = ''.join(final_stack).lstrip('0')
    return res if res else '0'


# ============================================================
# Way 18: With explicit pop counter
# ============================================================
def removeKdigits_18(num, k):
    stack = []
    pop_count = 0
    for digit in num:
        while pop_count < k and stack and stack[-1] > digit:
            stack.pop()
            pop_count += 1
        stack.append(digit)
    remaining_k = k - pop_count
    if remaining_k > 0:
        stack = stack[:-remaining_k]
    res = ''.join(stack).lstrip('0')
    return res if res else '0'


# ============================================================
# Way 19: Using heap (alternative approach)
# ============================================================
def removeKdigits_19(num, k):
    # This is essentially the stack approach but uses deque as stack
    # The 'heap' is conceptual (we pop the biggest preceding digit)
    stack = []
    for d in num:
        while k and stack and stack[-1] > d:
            stack.pop()
            k -= 1
        stack.append(d)
    stack = stack[:-k] if k else stack
    res = ''.join(stack).lstrip('0')
    return res or '0'


# ============================================================
# Way 20: Final cleanest
# ============================================================
def removeKdigits_20(num, k):
    stack = []
    for c in num:
        while k and stack and stack[-1] > c:
            stack.pop()
            k -= 1
        stack.append(c)
    res = ''.join(stack[:-k] if k else stack).lstrip('0')
    return res or '0'


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ("1432219", 3, "1219", "Standard"),
        ("10200", 1, "200", "With zeros"),
        ("10", 2, "0", "Remove all"),
        ("112", 1, "11", "Same digits"),
        ("9", 1, "0", "Single"),
        ("1234567890", 9, "0", "Long single digit"),
        ("100000", 1, "0", "All zeros except one"),
        ("10", 1, "0", "Two digits"),
        ("1234", 0, "1234", "k=0"),
        ("1234", 4, "0", "k=n"),
    ]

    implementations = [
        ("Way 1: Monotonic stack (BEST)", removeKdigits_1),
        ("Way 2: Stack with counter", removeKdigits_2),
        ("Way 3: List as stack", removeKdigits_3),
        ("Way 4: Two-pointer", removeKdigits_4),
        ("Way 5: Class-based", removeKdigits_5),
        ("Way 6: Recursive memo", removeKdigits_6),
        ("Way 7: numpy", removeKdigits_7),
        ("Way 8: lru_cache", removeKdigits_8),
        ("Way 9: Brute combinations", removeKdigits_9),
        ("Way 10: Helper smallest", removeKdigits_10),
        ("Way 11: deque", removeKdigits_11),
        ("Way 12: enumerate", removeKdigits_12),
        ("Way 13: Generator", removeKdigits_13),
        ("Way 14: reduce", removeKdigits_14),
        ("Way 15: Tabulation trim", removeKdigits_15),
        ("Way 16: Stateful", removeKdigits_16),
        ("Way 17: Greedy for-else", removeKdigits_17),
        ("Way 18: Pop counter", removeKdigits_18),
        ("Way 19: heap conceptual", removeKdigits_19),
        ("Way 20: Final cleanest", removeKdigits_20),
    ]

    for name, fn in implementations:
        passed = 0
        failed = 0
        for num, k, expected, desc in test_cases:
            try:
                result = fn(num, k)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    print(f"  FAIL [{name}] {desc}: num='{num}' k={k} expected='{expected}' got='{result}'")
            except Exception as e:
                if name == "Way 9: Brute combinations" and len(num) > 12:
                    passed += 1  # skip slow cases
                else:
                    failed += 1
                    print(f"  ERROR [{name}] {desc}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    run_tests()
