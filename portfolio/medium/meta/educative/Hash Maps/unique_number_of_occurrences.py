"""
Unique Number of Occurrences
Easy | 15 min

Given an array of integers, return True if each value has a unique
number of occurrences.

Constraints:
- 1 <= nums.length <= 1000
- -1000 <= nums[i] <= 1000

Examples:
    [1, 2, 2, 1, 1, 3] -> True
        Counts: {1:3, 2:2, 3:1} - all unique

    [1, 2, 2, 1, 1, 3, 3] -> False
        Counts: {1:3, 2:2, 3:2} - 2 appears twice

    [1, 1, 2, 2] -> False
        Counts: {1:2, 2:2} - both 2

    [-3,0,1,-3,1,1,1,-3,10,0] -> True
        Counts: {-3:3, 0:2, 1:4, 10:1} - all unique
"""

from collections import Counter, defaultdict
from functools import reduce


# =============================================================================
# WAY 1: Counter + set comparison (BEST - Memorize!)
# =============================================================================
# THINKING: "Count, then check if all counts are unique."
def unique_occurrences_1(nums):
    counts = Counter(nums)
    occurrences = list(counts.values())
    return len(occurrences) == len(set(occurrences))


# =============================================================================
# WAY 2: Manual dict + set with early return
# =============================================================================
def unique_occurrences_2(nums):
    counts = {}
    for num in nums:
        counts[num] = counts.get(num, 0) + 1

    seen = set()
    for count in counts.values():
        if count in seen:
            return False
        seen.add(count)
    return True


# =============================================================================
# WAY 3: Using defaultdict
# =============================================================================
def unique_occurrences_3(nums):
    counts = defaultdict(int)
    for num in nums:
        counts[num] += 1

    return len(set(counts.values())) == len(counts.values())


# =============================================================================
# WAY 4: One-liner
# =============================================================================
def unique_occurrences_4(nums):
    counts = Counter(nums)
    return len(set(counts.values())) == len(counts)


# =============================================================================
# WAY 5: Using dict comprehension
# =============================================================================
def unique_occurrences_5(nums):
    counts = {num: nums.count(num) for num in set(nums)}
    return len(set(counts.values())) == len(counts)


# =============================================================================
# WAY 6: Sort and check adjacent
# =============================================================================
def unique_occurrences_6(nums):
    counts = {}
    for num in nums:
        counts[num] = counts.get(num, 0) + 1

    sorted_counts = sorted(counts.values())
    for i in range(1, len(sorted_counts)):
        if sorted_counts[i] == sorted_counts[i-1]:
            return False
    return True


# =============================================================================
# WAY 7: Most compact
# =============================================================================
def unique_occurrences_7(nums):
    c = Counter(nums)
    return len(set(c.values())) == len(c)


# =============================================================================
# WAY 8: Using list comprehension
# =============================================================================
def unique_occurrences_8(nums):
    counts = Counter(nums).values()
    return len([x for x in counts]) == len(set(counts))


# =============================================================================
# WAY 9: With explicit comparison
# =============================================================================
def unique_occurrences_9(nums):
    counts = {}
    for num in nums:
        counts[num] = counts.get(num, 0) + 1

    freq = list(counts.values())
    return len(freq) == len(set(freq))


# =============================================================================
# WAY 10: Functional with reduce
# =============================================================================
def unique_occurrences_10(nums):
    counts = Counter(nums)
    occurrences = list(counts.values())
    unique_via_set = reduce(lambda acc, x: acc | {x}, occurrences, set())
    return len(unique_via_set) == len(occurrences)


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to check if all elements in the array have unique counts
of occurrences."

Approach:
"I'll use a hashmap to count occurrences of each number. Then I'll
check if all those counts are unique by comparing the length of the
counts list to the length of the counts set."

Why this works:
"If there are duplicates among the counts, then len(set) will be
smaller than len(list). If all counts are unique, they'll be equal."

Alternative:
"I could also sort the counts and check if any two adjacent counts
are equal. Or I could use a set while building to detect duplicates early."

Edge cases:
- Single element: trivially unique
- All same numbers: only one count, unique
- Two elements with same count: False

COMPLEXITY:
+-----------+--------+----------+
| Approach  | Time   | Space    |
+-----------+--------+----------+
| Counter   | O(n)   | O(n)     |
| Sort      | O(nlogn)| O(n)    |
+-----------+--------+----------+
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Counter + set", unique_occurrences_1),
        ("Way 2: Dict + early return", unique_occurrences_2),
        ("Way 3: defaultdict", unique_occurrences_3),
        ("Way 4: One-liner", unique_occurrences_4),
        ("Way 5: Dict comp", unique_occurrences_5),
        ("Way 6: Sort adjacent", unique_occurrences_6),
        ("Way 7: Most compact", unique_occurrences_7),
        ("Way 8: List comp", unique_occurrences_8),
        ("Way 9: Explicit", unique_occurrences_9),
        ("Way 10: Reduce", unique_occurrences_10),
    ]

    test_cases = [
        ([1, 2, 2, 1, 1, 3], True),
        ([1, 2, 2, 1, 1, 3, 3], False),
        ([1, 1, 2, 2], False),
        ([-3, 0, 1, -3, 1, 1, 1, -3, 10, 0], True),
        ([1], True),
        ([1, 2], True),
        ([1, 1, 2], True),
        ([1, 1, 2, 2, 3], False),
    ]

    print("=" * 70)
    print("UNIQUE NUMBER OF OCCURRENCES - ALL 10 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for nums, expected in test_cases:
            try:
                result = func(nums)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                status = "✓" if result == expected else "✗"
                print(f"  {status} {name}: {nums} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  ✗ {name}: ERROR - {e}")
        print(f"  Overall: {'PASS' if all_test_pass else 'FAIL'}\n")

    print("=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS! 🎉")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
