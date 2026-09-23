"""
Longest Happy String - 10 Ways
Medium | 30 min
https://leetcode.com/problems/longest-happy-string/

A string is called "happy" if it doesn't have any of the following substrings:
"aaa", "bbb", "ccc".

Given three integers a, b, c, return any longest happy string using 'a', 'b',
'c' at most a, b, c times respectively. If there is no such string, return "".

KEY INSIGHT:
Greedy + max-heap. At each step, pick the character with the most remaining
count. To avoid 3-in-a-row: if the last 2 chars equal this char, pick the
second most instead. Otherwise use two of the top (if safe) or just one.

Examples:
    a=1, b=1, c=7  => "ccaccbcc" or "ccbccacc"
    a=2, b=2, c=1  => "aabbc"
    a=7, b=1, c=0  => "aabaa"

Constraints:
- 0 <= a, b, c <= 100
- a + b + c > 0
"""

import heapq
import sys

sys.setrecursionlimit(100000)


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT LONGEST HAPPY STRING:

1. WHAT IS THE PROBLEM?
   "Build the longest string using 'a', 'b', 'c' (up to a, b, c times each),
    avoiding three consecutive same characters."

2. WHY MAX-HEAP?
   "Greedy: always use the character with the MOST remaining count, to make
   the string as long as possible. Use a max-heap (negate counts) of
   (count, char)."

3. ALGORITHM:
   "1. heap = max-heap of (count, char) for a, b, c with count > 0.
    2. result = [].
    3. While heap not empty:
       a. Pop top (count1, char1).
       b. If last 2 chars in result == char1: pick the next most (peek; pop+push).
          - If heap empty: break (can't continue).
          - Add char2 once. Decrement its count. Push back if count > 0.
          - Push back char1.
       c. Else: use up to min(2, count1) chars of char1 (two is safe; we never
          already have 2 of char1 at the end). Update count. Push back if > 0.
    4. Return ''.join(result)."

4. WHY UP TO 2 AT A TIME?
   "If the previous two chars aren't char1, we can safely add 2 of char1
    without forming three. Adding just 1 is also safe. Use 2 to maximize use."

5. WHEN TO USE:
   - String construction with constraints.
   - Greedy with priority of remaining counts.
   - Avoiding patterns in sequences.

6. COMMON TRAPS:
   - Forgetting to handle "heap empty" when the top would form a triple.
   - Using only 1 char when 2 is safe.
   - Using sort instead of heap.

7. COMPLEXITY:
   +------------+--------+--------+
   | Operation  | Time   | Notes  |
   +------------+--------+--------+
   | Each step  | O(log 3) ~ O(1) | heap of 3 |
   | Total      | O(a+b+c) |      |
   | Space      | O(1)    | 3 chars  |
   +------------+--------+--------+
"""


# =============================================================================
# WAY 1: Max-heap greedy (BEST - Memorize!)
# =============================================================================
def longest_happy_string_1(a, b, c):
    """Use max-heap of (-count, char). Greedy with triple avoidance."""
    heap = []
    for cnt, ch in [(-a, 'a'), (-b, 'b'), (-c, 'c')]:
        if cnt != 0:
            heapq.heappush(heap, (cnt, ch))
    result = []

    while heap:
        cnt1, ch1 = heapq.heappop(heap)
        # If last two chars in result are ch1, can't use ch1
        if len(result) >= 2 and result[-1] == result[-2] == ch1:
            if not heap:
                break
            cnt2, ch2 = heapq.heappop(heap)
            result.append(ch2)
            cnt2 += 1  # cnt2 is negative
            if cnt2 < 0:
                heapq.heappush(heap, (cnt2, ch2))
            heapq.heappush(heap, (cnt1, ch1))
        else:
            # Use up to 2 of ch1
            use = min(-cnt1, 2)
            result.extend([ch1] * use)
            cnt1 += use
            if cnt1 < 0:
                heapq.heappush(heap, (cnt1, ch1))

    return ''.join(result)


# =============================================================================
# WAY 2: Use heapreplace for cleaner code
# =============================================================================
def longest_happy_string_2(a, b, c):
    heap = []
    for cnt, ch in [(-a, 'a'), (-b, 'b'), (-c, 'c')]:
        if cnt != 0:
            heapq.heappush(heap, (cnt, ch))
    result = []

    while heap:
        cnt1, ch1 = heapq.heappop(heap)
        if len(result) >= 2 and result[-1] == result[-2] == ch1:
            if not heap:
                break
            cnt2, ch2 = heapq.heappop(heap)
            result.append(ch2)
            if cnt2 + 1 < 0:
                heapq.heappush(heap, (cnt2 + 1, ch2))
            heapq.heappush(heap, (cnt1, ch1))
        else:
            use = min(-cnt1, 2)
            result.extend([ch1] * use)
            if cnt1 + use < 0:
                heapq.heappush(heap, (cnt1 + use, ch1))

    return ''.join(result)


# =============================================================================
# WAY 3: Sort-based approach
# =============================================================================
def longest_happy_string_3(a, b, c):
    """Sort by count descending each iteration; pick top."""
    counts = [(-a, 'a'), (-b, 'b'), (-c, 'c')]
    counts = [(neg, ch) for neg, ch in counts if neg != 0]
    result = []

    while counts:
        counts.sort()  # Most negative first (largest count)
        c1, ch1 = counts[0]
        if len(result) >= 2 and result[-1] == result[-2] == ch1:
            if len(counts) < 2:
                break
            c2, ch2 = counts[1]
            result.append(ch2)
            counts[1] = (c2 + 1, ch2)
        else:
            use = min(-c1, 2)
            result.extend([ch1] * use)
            counts[0] = (c1 + use, ch1)
        counts = [(neg, ch) for neg, ch in counts if neg != 0]

    return ''.join(result)


# =============================================================================
# WAY 4: Always add 1 at a time (simpler but slower)
# =============================================================================
def longest_happy_string_4(a, b, c):
    heap = []
    for cnt, ch in [(-a, 'a'), (-b, 'b'), (-c, 'c')]:
        if cnt != 0:
            heapq.heappush(heap, (cnt, ch))
    result = []

    while heap:
        cnt1, ch1 = heapq.heappop(heap)
        if len(result) >= 2 and result[-1] == result[-2] == ch1:
            if not heap:
                break
            cnt2, ch2 = heapq.heappop(heap)
            result.append(ch2)
            if cnt2 + 1 < 0:
                heapq.heappush(heap, (cnt2 + 1, ch2))
            heapq.heappush(heap, (cnt1, ch1))
        else:
            result.append(ch1)
            if cnt1 + 1 < 0:
                heapq.heappush(heap, (cnt1 + 1, ch1))

    return ''.join(result)


# =============================================================================
# WAY 5: Class-based wrapper
# =============================================================================
class HappyStringBuilder_5:
    def __init__(self, a, b, c):
        self.a, self.b, self.c = a, b, c

    def build(self):
        return longest_happy_string_1(self.a, self.b, self.c)


def longest_happy_string_5(a, b, c):
    return HappyStringBuilder_5(a, b, c).build()


# =============================================================================
# WAY 6: Recursive
# =============================================================================
def longest_happy_string_6(a, b, c):
    def helper(remaining, result):
        heap = []
        for cnt, ch in [(-remaining[0], 'a'), (-remaining[1], 'b'), (-remaining[2], 'c')]:
            if cnt != 0:
                heapq.heappush(heap, (cnt, ch))
        if not heap:
            return result
        cnt1, ch1 = heapq.heappop(heap)
        if len(result) >= 2 and result[-1] == result[-2] == ch1:
            if not heap:
                return result
            cnt2, ch2 = heapq.heappop(heap)
            result.append(ch2)
            new_rem = list(remaining)
            new_rem['abc'.index(ch2)] -= 1
            return helper(new_rem, result)
        else:
            use = min(-cnt1, 2)
            result.extend([ch1] * use)
            new_rem = list(remaining)
            new_rem['abc'.index(ch1)] -= use
            return helper(new_rem, result)

    # Convert to a recursive form with a mutable list
    def helper2(ia, ib, ic, result):
        heap = []
        for cnt, ch in [(-ia, 'a'), (-ib, 'b'), (-ic, 'c')]:
            if cnt != 0:
                heapq.heappush(heap, (cnt, ch))
        if not heap:
            return result
        cnt1, ch1 = heapq.heappop(heap)
        if len(result) >= 2 and result[-1] == result[-2] == ch1:
            if not heap:
                return result
            cnt2, ch2 = heapq.heappop(heap)
            result.append(ch2)
            if ch2 == 'a':
                return helper2(ia - 1, ib, ic, result)
            elif ch2 == 'b':
                return helper2(ia, ib - 1, ic, result)
            else:
                return helper2(ia, ib, ic - 1, result)
        else:
            use = min(-cnt1, 2)
            result.extend([ch1] * use)
            if ch1 == 'a':
                return helper2(ia - use, ib, ic, result)
            elif ch1 == 'b':
                return helper2(ia, ib - use, ic, result)
            else:
                return helper2(ia, ib, ic - use, result)

    return helper2(a, b, c, [])


# =============================================================================
# WAY 7: Counter approach with sorted
# =============================================================================
def longest_happy_string_7(a, b, c):
    """Use Counter-like dict; rebuild sorted list each iteration."""
    counts = {'a': -a, 'b': -b, 'c': -c}  # negative for sorting
    result = []

    while True:
        available = [(neg, ch) for ch, neg in counts.items() if neg != 0]
        if not available:
            break
        available.sort()  # most negative first (highest count)
        neg1, ch1 = available[0]
        if len(result) >= 2 and result[-1] == result[-2] == ch1:
            if len(available) < 2:
                break
            _, ch2 = available[1]
            result.append(ch2)
            counts[ch2] += 1  # counts[ch2] is negative
        else:
            use = min(-neg1, 2)
            result.extend([ch1] * use)
            counts[ch1] += use

    return ''.join(result)


# =============================================================================
# WAY 8: Predefined patterns based on ratio
# =============================================================================
def longest_happy_string_8(a, b, c):
    """Smarter: always add 2 of most unless it would exceed 2x second."""
    counts = {'a': a, 'b': b, 'c': c}
    result = []

    while any(c > 0 for c in counts.values()):
        sorted_chars = sorted(counts.keys(), key=lambda ch: -counts[ch])
        top, second = sorted_chars[0], sorted_chars[1] if len(sorted_chars) > 1 else None
        # If adding top would create triple, use second
        if len(result) >= 2 and result[-1] == result[-2] == top:
            if second is None or counts[second] == 0:
                break
            result.append(second)
            counts[second] -= 1
        else:
            use = min(counts[top], 2)
            result.extend([top] * use)
            counts[top] -= use

    return ''.join(result)


# =============================================================================
# WAY 9: While loop with explicit ordering
# =============================================================================
def longest_happy_string_9(a, b, c):
    """Use list instead of heap for clarity."""
    counts = [(-a, 'a'), (-b, 'b'), (-c, 'c')]
    counts = [(neg, ch) for neg, ch in counts if neg != 0]
    result = []

    while counts:
        counts.sort()  # Most negative first
        cnt1, ch1 = counts[0]
        if len(result) >= 2 and result[-1] == result[-2] == ch1:
            if len(counts) < 2:
                break
            cnt2, ch2 = counts[1]
            result.append(ch2)
            counts[1] = (cnt2 + 1, ch2)
        else:
            use = min(-cnt1, 2)
            result.extend([ch1] * use)
            counts[0] = (cnt1 + use, ch1)
        counts = [(neg, ch) for neg, ch in counts if neg != 0]

    return ''.join(result)


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def longestHappyString(a, b, c):
    """
    THE ONE TO MEMORIZE.

    1. Max-heap (negative counts) of (count, char).
    2. While heap:
       a. Pop top.
       b. If last 2 in result == top char:
          - Pop next, add it, decrement, push both back.
       c. Else: add up to 2 of top char, decrement, push back if remaining.
    3. Return ''.join(result).

    Time:  O(a + b + c) (heap of 3 elements).
    Space: O(a + b + c) for result.
    """
    heap = []
    for cnt, ch in [(-a, 'a'), (-b, 'b'), (-c, 'c')]:
        if cnt != 0:
            heapq.heappush(heap, (cnt, ch))
    result = []

    while heap:
        cnt1, ch1 = heapq.heappop(heap)
        if len(result) >= 2 and result[-1] == result[-2] == ch1:
            if not heap:
                break
            cnt2, ch2 = heapq.heappop(heap)
            result.append(ch2)
            if cnt2 + 1 < 0:
                heapq.heappush(heap, (cnt2 + 1, ch2))
            heapq.heappush(heap, (cnt1, ch1))
        else:
            use = min(-cnt1, 2)
            result.extend([ch1] * use)
            if cnt1 + use < 0:
                heapq.heappush(heap, (cnt1 + use, ch1))

    return ''.join(result)


# =============================================================================
# TEST
# =============================================================================
def is_valid_happy(s, a, b, c):
    """Check if s is a valid happy string with given char limits."""
    if 'aaa' in s or 'bbb' in s or 'ccc' in s:
        return False
    return s.count('a') <= a and s.count('b') <= b and s.count('c') <= c


def run_tests():
    implementations = [
        ("Way 1: Max-heap greedy (BEST)", longest_happy_string_1),
        ("Way 2: heapreplace", longest_happy_string_2),
        ("Way 3: Sort approach", longest_happy_string_3),
        ("Way 4: Add 1 at a time", longest_happy_string_4),
        ("Way 5: Class wrapper", longest_happy_string_5),
        ("Way 6: Recursive", longest_happy_string_6),
        ("Way 7: Counter + sort", longest_happy_string_7),
        ("Way 8: Ratio-based", longest_happy_string_8),
        ("Way 9: List-based", longest_happy_string_9),
        ("Way 10: Final cleanest", longestHappyString),
    ]

    test_cases = [
        # (a, b, c, expected_len)
        (1, 1, 7, 8),  # LC example: "ccbccacc" (7c+1a+1b-1 not used?)
        (2, 2, 1, 5),
        (7, 1, 0, 5),  # "aabaa"
        (0, 0, 0, 0),
        (1, 0, 0, 1),
        (4, 4, 4, 12),  # alternating
        (10, 1, 1, 8),  # "aabaacaa" (6a+1b+1c)
        (0, 5, 3, 8),
    ]

    print("=" * 70)
    print("LONGEST HAPPY STRING - 10 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for a, b, c, expected_len in test_cases:
            try:
                result = fn(a, b, c)
                # Check validity and length
                if is_valid_happy(result, a, b, c) and len(result) == expected_len:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] a={a},b={b},c={c}: got={result!r}, len={len(result)}, expected_len={expected_len}")
            except Exception as e:
                failed += 1
                all_pass = False
                print(f"  ERROR [{name}] a={a},b={b},c={c}: {e}")
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
