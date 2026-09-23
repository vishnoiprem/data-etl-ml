"""
Construct Target Array With Multiple Sums - 10 Ways
Hard | 35 min
https://leetcode.com/problems/construct-target-array-with-multiple-sums/

You are given an array target of n integers. Starting from an array arr of
n 1's (i.e., arr = [1, 1, ..., 1]), at each step:
  - Pick any index i and set arr[i] = sum(arr) (the total sum of arr).
Return true if it's possible to construct the target array, false otherwise.

KEY INSIGHT:
Reverse the process. If target is the result, work backwards: at each step,
the largest element in current array was the one that just got replaced.
Specifically, if max = m and total = s, then before the step:
  m' = m - (s - m) ... wait, let me think.
  After step: new_arr[i] = old_sum. So m = old_sum. The other elements are unchanged.
  Total after = old_sum + (old_sum - old_arr[i]) = 2*old_sum - old_arr[i].
  So old_total = 2*old_sum - m. But we want old_arr[i] = old_total - (s - m).
  Hmm, let me redo.
  Before: arr[i] = x, total = T. Other elements sum = T - x. After: arr[i] = T, total = T + (T - x) = 2T - x.
  So old_total = T (the sum before). The new max element is T (just inserted).
  Other elements unchanged.
  Inverse: if current is (m, others) with sum S, then before step:
    m' = m - S (since other elements still sum to S - m, but m' = S - (S - m) = m. Hmm.)

Let me redo:
  Before: arr with max element m at position i. Old sum = T. So m = arr[i] = some value.
  After: arr[i] = T. New sum = T + (T - arr[i]) = 2T - arr[i] = 2T - m.

  Wait that's wrong. The other elements are unchanged. New sum = (sum of others) + arr[i]_new
                                              = (T - m) + T = 2T - m.

  Hmm but then new_sum > T always.

  Reverse: given current state with sum S, find prior state.
  In prior state, arr[i] = x (some value), sum = T. After: arr[i] = T, sum = 2T - x = S.
  So 2T - x = S, and x = T - (S - T) = 2T - S.
  But x must be >= 1 (since we start with 1s and always replace with sum which is >= n).
  Actually x could be 1 (initial state). Let's check: if S = n (all 1s), no prior state.

  The largest element in current state was the one just replaced. So max = T.
  Other elements are unchanged from prior state: they sum to S - T.
  Prior state: arr = (S - T, S - T, ..., T' = ...  no wait).

  Let me try again. After step, arr[i] = T (old sum). So new_max = T if T >= all other elements.
  Other elements = (S - T) total. In prior state, these same elements existed with same values,
  sum T - m (where m = prior max). But wait, in prior state, arr[i] = m, so sum = (T - m) + m = T.
  So prior sum = T = new_max.

  Now: S = 2T - m → m = 2T - S.

  So: given current (with max = T, sum = S), the prior state had:
    - arr[i] = m = 2T - S (at the position of max).
    - All other elements unchanged.
    - Sum = T.

  We continue as long as 2T - S >= 1 (since arr values are always >= 1 in the prior state).
  And we stop when target == [1, 1, ..., 1] (length n).

  We can use a max-heap (negate for Python) for efficient max extraction.

Examples:
    target = [9, 3, 5] -> true
    target = [1, 1, 1, 2] -> false (can't go from 1s to this)
    target = [8, 5] -> true

Constraints:
- n == target.length
- 1 <= target.length <= 5 * 10^3
- 1 <= target[i] <= 10^9
"""

import heapq
import sys

sys.setrecursionlimit(100000)


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT CONSTRUCT TARGET ARRAY WITH MULTIPLE SUMS:

1. WHAT IS THE PROBLEM?
   "Starting from [1, 1, ..., 1], repeatedly replace one element with the
    total sum. Can we reach target?"

2. WHY REVERSE + MAX-HEAP?
   "Forward simulation is intractable (too many steps possible). Reverse is
   cleaner: at each reverse step, the largest element of current array was
    just set. Recover prior state:
       - current max = T (sum before the forward step)
       - current sum = S
       - prior element at max position: m = 2T - S
       - other elements unchanged.
    Use max-heap to find max in O(log n)."

3. ALGORITHM:
   "1. max-heap = [-x for x in target]; sum = sum(target).
    2. While max > 1:
       a. m = -heappop(heap).
       b. If m == 1: return False (would need prior sum T=1, impossible).
       c. T = sum - (sum - m) / ... actually: T = sum - (sum - m) ... hmm.
          Correct: prior_sum T = m (the just-set element). Other elements sum to S - m.
          But wait, prior sum = T, and current sum = S = 2T - m, so T = (S + m) / 2.
          Hmm but T should equal m... let me re-check.

          Wait, T = prior_sum = current_max (since current_max was set to T).
          So current_max = T. And S = current_sum = 2T - prior_max = 2*m - m = m?

          I confused myself. Let me redo:

          Before: arr = [a, b, c], sum = T. After: arr = [T, b, c], sum = T + b + c = T + (T - a) = 2T - a.
          So new sum S = 2T - a. And max of new array is T (if T >= b and T >= c).

          Given current (with max m = T, sum S), recover prior:
            a = 2T - S = 2m - S. Other elements unchanged.
            Prior sum = T = m.

       a. m = -heappop(heap).
       b. If m == 1: return False (no further steps possible).
       c. T = m (this is the prior sum).
       d. rest = S - m (sum of other elements).
       e. If rest == 0: return False (no other elements means can't divide).
       f. m_new = m % rest  # We can shortcut: instead of one step, do many.
          Actually, m_new = m - k*rest where k is the number of times we'd do the same op.
          m - (k+1)*rest >= 1 (else we'd go below 1).
          So k = (m - 1) // rest, then m_new = m - k * rest.
       g. Update S -= (m - m_new); push -m_new.
    3. Return True if we successfully reduce all to 1."

4. WHY SHORTCUT (k = (m-1)//rest)?
   "If m is huge, doing one reverse step at a time is slow. We can compute the
   number of 'equivalent' steps in O(1): k = (m - 1) // rest, then m_new = m - k*rest."

5. EDGE CASES:
   - Already [1, 1, ..., 1]: return True.
   - Any element > total_sum_other: impossible.
   - Total < n: impossible.

6. WHEN TO USE:
   - Reverse simulation with heap.
   - Modular arithmetic shortcuts.

7. COMMON TRAPS:
   - Wrong inverse formula (mix up forward/backward).
   - Off-by-one in the modulo operation.
   - Not handling the case where rest is 0.

8. COMPLEXITY:
   +------------+--------+--------+
   | Operation  | Time   | Notes  |
   +------------+--------+--------+
   | Build heap | O(n)            |
   | Each step  | O(log n)        |
   | Total      | O(n + log(max) * log n) |
   | Space      | O(n)            |
   +------------+--------+--------+
"""


# =============================================================================
# WAY 1: Max-heap reverse with shortcut (BEST - Memorize!)
# =============================================================================
def is_possible_1(target):
    """Reverse + max-heap with modulo shortcut."""
    n = len(target)
    if n == 1:
        return target[0] == 1
    if sum(target) < n:
        return False

    # Max-heap (negate)
    heap = [-x for x in target]
    heapq.heapify(heap)
    total = sum(target)

    while True:
        m = -heapq.heappop(heap)
        if m == 1:
            return True
        rest = total - m
        if rest <= 0:
            return False
        # How many times can we "undo" before m_new would be < 1?
        # After k undos: m_k = m - k*rest. We need m_k >= 1, so k <= (m-1)/rest.
        # Final m_new = m - k*rest = m % rest, unless m % rest == 0, then it's rest.
        # Actually: m_new = ((m - 1) % rest) + 1.
        m_new = (m - 1) % rest + 1
        if m_new >= m:
            return False  # no progress
        total = total - m + m_new
        heapq.heappush(heap, -m_new)


# =============================================================================
# WAY 2: Same logic, no shortcut (slower)
# =============================================================================
def is_possible_2(target):
    """Reverse without modulo shortcut."""
    n = len(target)
    if n == 1:
        return target[0] == 1
    if sum(target) < n:
        return False

    heap = [-x for x in target]
    heapq.heapify(heap)
    total = sum(target)

    while True:
        m = -heapq.heappop(heap)
        if m == 1:
            return True
        rest = total - m
        if rest <= 0:
            return False
        m_new = m - rest
        if m_new < 1:
            return False
        total = total - m + m_new
        heapq.heappush(heap, -m_new)


# =============================================================================
# WAY 3: Sort instead of heap (slow for large inputs)
# =============================================================================
def is_possible_3(target):
    """Use sorted list instead of heap."""
    arr = sorted(target)  # ascending; max is arr[-1]
    n = len(arr)
    if n == 1:
        return arr[0] == 1
    if sum(arr) < n:
        return False

    while arr[-1] > 1:
        m = arr[-1]
        rest = sum(arr) - m
        if rest == 0:
            return False
        m_new = (m - 1) % rest + 1
        if m_new >= m:
            return False
        arr[-1] = m_new
        # Re-sort: only the changed element
        # Use insertion sort
        i = n - 1
        while i > 0 and arr[i] < arr[i - 1]:
            arr[i], arr[i - 1] = arr[i - 1], arr[i]
            i -= 1
        if arr[-1] < 1:
            return False
    return True


# =============================================================================
# WAY 4: Class-based wrapper
# =============================================================================
class TargetArrayBuilder_4:
    def __init__(self, target):
        self.target = target

    def is_possible(self):
        return is_possible_1(self.target)


def is_possible_4(target):
    return TargetArrayBuilder_4(target).is_possible()


# =============================================================================
# WAY 5: Use max() each iteration (brute)
# =============================================================================
def is_possible_5(target):
    """Brute: use max() instead of heap."""
    arr = list(target)
    n = len(arr)
    if n == 1:
        return arr[0] == 1
    if sum(arr) < n:
        return False

    while max(arr) > 1:
        m = max(arr)
        i = arr.index(m)
        rest = sum(arr) - m
        if rest == 0:
            return False
        m_new = (m - 1) % rest + 1
        if m_new >= m:
            return False
        arr[i] = m_new
        if sum(arr) < n:
            return False
    return True


# =============================================================================
# WAY 6: Use heap but no modulo shortcut
# =============================================================================
def is_possible_6(target):
    heap = [-x for x in target]
    heapq.heapify(heap)
    total = sum(target)
    n = len(target)

    if total < n:
        return False

    while -heap[0] > 1:
        m = -heapq.heappop(heap)
        rest = total - m
        if rest == 0:
            return False
        m_new = m - rest
        if m_new < 1:
            return False
        total = total - m + m_new
        heapq.heappush(heap, -m_new)
    return True


# =============================================================================
# WAY 7: With explicit modulo formula
# =============================================================================
def is_possible_7(target):
    heap = [-x for x in target]
    heapq.heapify(heap)
    total = sum(target)
    n = len(target)

    if total < n:
        return False

    while -heap[0] > 1:
        m = -heapq.heappop(heap)
        rest = total - m
        if rest <= 0:
            return False
        # m_new must be in [1, m)
        # We can shortcut: m_new = ((m - 1) % rest) + 1
        m_new = ((m - 1) % rest) + 1
        if m_new >= m:
            return False
        total = total - m + m_new
        heapq.heappush(heap, -m_new)
    return True


# =============================================================================
# WAY 8: Variant with tuple (max, neg) in heap
# =============================================================================
def is_possible_8(target):
    heap = [(-x, i) for i, x in enumerate(target)]
    heapq.heapify(heap)
    total = sum(target)
    arr = list(target)

    if total < len(target):
        return False

    while -heap[0][0] > 1:
        neg_m, i = heapq.heappop(heap)
        m = -neg_m
        rest = total - m
        if rest == 0:
            return False
        m_new = ((m - 1) % rest) + 1
        if m_new >= m:
            return False
        arr[i] = m_new
        total = total - m + m_new
        heapq.heappush(heap, (-m_new, i))
    return True


# =============================================================================
# WAY 9: Simple while loop without heap (use sort)
# =============================================================================
def is_possible_9(target):
    arr = sorted(target, reverse=True)  # descending; max is arr[0]
    total = sum(target)
    n = len(arr)

    if total < n:
        return False

    while arr[0] > 1:
        m = arr[0]
        rest = total - m
        if rest == 0:
            return False
        m_new = ((m - 1) % rest) + 1
        if m_new >= m:
            return False
        arr[0] = m_new
        total = total - m + m_new
        # Re-sort: insert m_new into sorted descending position
        arr.sort(reverse=True)
    return True


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def isPossible(target):
    """
    THE ONE TO MEMORIZE.

    1. max-heap of target (negated); total = sum(target).
    2. While max > 1:
       a. m = -heappop(heap).
       b. rest = total - m.
       c. m_new = (m - 1) % rest + 1   (shortcut).
       d. total = total - m + m_new; push -m_new.
    3. Return True if all reduce to 1.

    Time:  O(n + log(max) * log n).
    Space: O(n).
    """
    n = len(target)
    if n == 1:
        return target[0] == 1
    total = sum(target)
    if total < n:
        return False

    heap = [-x for x in target]
    heapq.heapify(heap)

    while -heap[0] > 1:
        m = -heapq.heappop(heap)
        rest = total - m
        if rest == 0:
            return False
        m_new = (m - 1) % rest + 1
        if m_new >= m:
            return False
        total = total - m + m_new
        heapq.heappush(heap, -m_new)
    return True


# =============================================================================
# TEST
# =============================================================================
def run_tests():
    implementations = [
        ("Way 1: Max-heap + shortcut (BEST)", is_possible_1),
        ("Way 2: No shortcut", is_possible_2),
        ("Way 3: Sorted list", is_possible_3),
        ("Way 4: Class wrapper", is_possible_4),
        ("Way 5: Brute max()", is_possible_5),
        ("Way 6: Heap no shortcut", is_possible_6),
        ("Way 7: Explicit modulo", is_possible_7),
        ("Way 8: Heap with index", is_possible_8),
        ("Way 9: Desc sort", is_possible_9),
        ("Way 10: Final cleanest", isPossible),
    ]

    test_cases = [
        ([9, 3, 5], True),
        ([1, 1, 1, 2], False),
        ([8, 5], True),
        ([1, 1], True),
        ([2, 1], True),
        ([1], True),
        ([2], False),
    ]

    print("=" * 70)
    print("CONSTRUCT TARGET ARRAY WITH MULTIPLE SUMS - 10 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for inp, expected in test_cases:
            try:
                inp_copy = list(inp)
                result = fn(inp_copy)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] target={inp}, expected={expected}, got={result}")
            except Exception as e:
                failed += 1
                all_pass = False
                print(f"  ERROR [{name}] target={inp}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)


if __name__ == "__main__":
    run_tests()
