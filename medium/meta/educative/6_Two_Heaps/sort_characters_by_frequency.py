"""
Sort Characters By Frequency - 10 Ways
Medium | 20 min
https://leetcode.com/problems/sort-characters-by-frequency/

Given a string s, sort it in decreasing order based on the frequency of the
characters. The frequency of a character is the number of times it appears
in the string. Return the sorted string. If there are multiple answers,
return any of them.

KEY INSIGHT:
Count frequencies, then sort chars by frequency descending. Use Counter +
heap, or Counter + sorted, or bucket sort.

Examples:
    "tree"  -> "eert" or "eetr"  (e=2, r=1, t=1)
    "cccaaa" -> "cccaaa" or "aaaccc"  (c=3, a=3, tie)
    "Aabb"   -> "bbAa" or "bbaA"  (b=2, A=1, a=1)

Constraints:
- 1 <= s.length <= 5 * 10^5
- s consists of uppercase and lowercase English letters and digits.
"""

import heapq
import sys
from collections import Counter

sys.setrecursionlimit(100000)


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT SORT CHARACTERS BY FREQUENCY:

1. WHAT IS THE PROBLEM?
   "Sort a string's characters by frequency (descending)."

2. WHY COUNTER + SORT?
   "Count frequencies with Counter, then sort characters by count descending.
    Use heapq.nlargest, sorted(), or bucket sort (since char set is small)."

3. ALGORITHM:
   "1. counts = Counter(s).
    2. heap = [(-count, char) for char, count in counts.items()].
    3. heapify.
    4. While heap: pop top, append char * count to result.
    5. Return ''.join(result)."

4. ALTERNATIVE: BUCKET SORT
   "Since char count <= len(s), use buckets indexed by count:
    bucket[i] = list of chars with count i.
    Walk buckets in reverse."

5. WHEN TO USE:
   - Frequency-based sorting.
   - Top-K elements.

6. COMMON TRAPS:
   - Returning unstable order (any order is fine, but stable not required).
   - Not handling single-char input.

7. COMPLEXITY:
   +------------+--------+--------+
   | Approach  | Time   | Notes  |
   +------------+--------+--------+
   | Counter + | O(n + k log k) | k distinct chars |
   | heap      |                  |       |
   | Counter + | O(n + k log k) |      |
   | sorted    |                  |       |
   | Bucket    | O(n + k)        | k = max freq |
   +------------+--------+--------+
"""


# =============================================================================
# WAY 1: Counter + heap (BEST - Memorize!)
# =============================================================================
def frequency_sort_1(s):
    """Use Counter and heap for top-frequency chars."""
    counts = Counter(s)
    heap = [(-cnt, ch) for ch, cnt in counts.items()]
    heapq.heapify(heap)
    result = []
    while heap:
        cnt, ch = heapq.heappop(heap)
        result.append(ch * -cnt)
    return ''.join(result)


# =============================================================================
# WAY 2: Counter + sorted
# =============================================================================
def frequency_sort_2(s):
    """Counter, then sort by count descending."""
    counts = Counter(s)
    chars = sorted(counts.keys(), key=lambda c: -counts[c])
    return ''.join(c * counts[c] for c in chars)


# =============================================================================
# WAY 3: Counter + heapq.nlargest
# =============================================================================
def frequency_sort_3(s):
    """Use heapq.nlargest for top-frequency chars."""
    counts = Counter(s)
    top_chars = heapq.nlargest(len(counts), counts.keys(), key=lambda c: counts[c])
    return ''.join(c * counts[c] for c in top_chars)


# =============================================================================
# WAY 4: Bucket sort
# =============================================================================
def frequency_sort_4(s):
    """Bucket sort by count."""
    counts = Counter(s)
    n = len(s)
    buckets = [[] for _ in range(n + 1)]
    for ch, cnt in counts.items():
        buckets[cnt].append(ch)
    result = []
    for cnt in range(n, 0, -1):
        for ch in buckets[cnt]:
            result.append(ch * cnt)
    return ''.join(result)


# =============================================================================
# WAY 5: Class-based wrapper
# =============================================================================
class FrequencySorter_5:
    def __init__(self, s):
        self.s = s

    def sort(self):
        return frequency_sort_1(self.s)


def frequency_sort_5(s):
    return FrequencySorter_5(s).sort()


# =============================================================================
# WAY 6: Manual frequency counting
# =============================================================================
def frequency_sort_6(s):
    """Manual freq dict instead of Counter."""
    freq = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    chars = sorted(freq.keys(), key=lambda c: -freq[c])
    return ''.join(c * freq[c] for c in chars)


# =============================================================================
# WAY 7: heapq with tuples (count, char)
# =============================================================================
def frequency_sort_7(s):
    counts = Counter(s)
    # Use a list of (count, char) sorted desc
    pairs = sorted(((cnt, ch) for ch, cnt in counts.items()), reverse=True)
    return ''.join(ch * cnt for cnt, ch in pairs)


# =============================================================================
# WAY 8: Most_common
# =============================================================================
def frequency_sort_8(s):
    counts = Counter(s)
    # most_common returns list of (elem, count) sorted by count desc
    return ''.join(ch * cnt for ch, cnt in counts.most_common())


# =============================================================================
# WAY 9: Sort indices by count
# =============================================================================
def frequency_sort_9(s):
    counts = Counter(s)
    sorted_chars = sorted(counts.keys(), key=lambda c: counts[c], reverse=True)
    return ''.join(c * counts[c] for c in sorted_chars)


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def frequencySort(s):
    """
    THE ONE TO MEMORIZE.

    1. counts = Counter(s).
    2. Sort chars by count desc.
    3. Return ''.join(c * counts[c] for c in sorted_chars).

    Time:  O(n + k log k) where k = distinct chars.
    Space: O(n).
    """
    counts = Counter(s)
    chars = sorted(counts.keys(), key=lambda c: -counts[c])
    return ''.join(c * counts[c] for c in chars)


# =============================================================================
# TEST
# =============================================================================
def is_valid_frequency_sort(s, expected_freq):
    """Check if s is a valid sorted-by-frequency string."""
    return sorted(s) == sorted(expected_freq)


def run_tests():
    implementations = [
        ("Way 1: Counter + heap (BEST)", frequency_sort_1),
        ("Way 2: Counter + sorted", frequency_sort_2),
        ("Way 3: nlargest", frequency_sort_3),
        ("Way 4: Bucket sort", frequency_sort_4),
        ("Way 5: Class wrapper", frequency_sort_5),
        ("Way 6: Manual dict", frequency_sort_6),
        ("Way 7: Sort desc", frequency_sort_7),
        ("Way 8: most_common", frequency_sort_8),
        ("Way 9: Sort by count", frequency_sort_9),
        ("Way 10: Final cleanest", frequencySort),
    ]

    test_cases = [
        ("tree", "eert"),
        ("cccaaa", "cccaaa"),
        ("Aabb", "bbAa"),
        ("a", "a"),
        ("aaabbbcc", "aaabbbcc"),
        ("abc", "abc"),
        ("", ""),
        ("aabbcc", "aabbcc"),
    ]

    print("=" * 70)
    print("SORT CHARACTERS BY FREQUENCY - 10 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for inp, expected in test_cases:
            try:
                result = fn(inp)
                # Check if result is a valid permutation of expected
                if sorted(result) == sorted(expected):
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] input={inp!r}, expected={expected!r}, got={result!r}")
            except Exception as e:
                failed += 1
                all_pass = False
                print(f"  ERROR [{name}] input={inp!r}: {e}")
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
