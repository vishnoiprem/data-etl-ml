"""
Next Greater Element I
Easy | 15 min

Given nums1 (subset) and nums2, for each element in nums1, find the next
greater element to its right in nums2.

If no greater element exists, return -1.

Constraints:
- 1 <= nums1.length <= nums2.length <= 10^3
- 0 <= nums1[i], nums2[i] <= 10^4
- All integers distinct in each array
- All elements of nums1 appear in nums2

Examples:
    nums1 = [4,1,2], nums2 = [1,3,4,2] -> [-1, 3, -1]
    nums1 = [2,4], nums2 = [1,2,3,4] -> [3, -1]
"""

from collections import defaultdict


# =============================================================================
# WAY 1: Stack + HashMap (BEST - Memorize!)
# =============================================================================
# THINKING: "Use monotonic stack to precompute next greater for all elements."
def next_greater_element_1(nums1, nums2):
    next_greater = {}
    stack = []

    for num in nums2:
        # Pop smaller elements - they found their next greater
        while stack and stack[-1] < num:
            smaller = stack.pop()
            next_greater[smaller] = num
        stack.append(num)

    # Remaining in stack have no greater
    for num in stack:
        next_greater[num] = -1

    return [next_greater[x] for x in nums1]


# =============================================================================
# WAY 2: Using enumerate for indices
# =============================================================================
def next_greater_element_2(nums1, nums2):
    next_greater = {}
    stack = []

    for i, num in enumerate(nums2):
        while stack and nums2[stack[-1]] < num:
            smaller_idx = stack.pop()
            next_greater[nums2[smaller_idx]] = num
        stack.append(i)

    for idx in stack:
        next_greater[nums2[idx]] = -1

    return [next_greater[x] for x in nums1]


# =============================================================================
# WAY 3: Brute Force
# =============================================================================
def next_greater_element_3(nums1, nums2):
    result = []

    for num in nums1:
        found = -1
        idx = nums2.index(num)
        for j in range(idx + 1, len(nums2)):
            if nums2[j] > num:
                found = nums2[j]
                break
        result.append(found)

    return result


# =============================================================================
# WAY 4: With dict comprehension for cleanup
# =============================================================================
def next_greater_element_4(nums1, nums2):
    stack = []
    next_greater = {}

    for num in nums2:
        while stack and stack[-1] < num:
            next_greater[stack.pop()] = num
        stack.append(num)

    while stack:
        next_greater[stack.pop()] = -1

    return [next_greater[x] for x in nums1]


# =============================================================================
# WAY 5: Using defaultdict with default -1
# =============================================================================
def next_greater_element_5(nums1, nums2):
    next_greater = defaultdict(lambda: -1)
    stack = []

    for num in nums2:
        while stack and stack[-1] < num:
            next_greater[stack.pop()] = num
        stack.append(num)

    return [next_greater[x] for x in nums1]


# =============================================================================
# WAY 6: Most compact with .get()
# =============================================================================
def next_greater_element_6(nums1, nums2):
    stack = []
    next_greater = {}

    for num in nums2:
        while stack and stack[-1] < num:
            next_greater[stack.pop()] = num
        stack.append(num)

    return [next_greater.get(x, -1) for x in nums1]


# =============================================================================
# WAY 7: Explicit loop for result
# =============================================================================
def next_greater_element_7(nums1, nums2):
    next_greater = {}
    stack = []

    for num in nums2:
        while stack and stack[-1] < num:
            next_greater[stack.pop()] = num
        stack.append(num)

    for num in stack:
        next_greater[num] = -1

    return [next_greater[x] for x in nums1]


# =============================================================================
# WAY 8: With index lookup
# =============================================================================
def next_greater_element_8(nums1, nums2):
    index = {num: i for i, num in enumerate(nums2)}
    result = []

    for num in nums1:
        idx = index[num]
        found = -1
        for j in range(idx + 1, len(nums2)):
            if nums2[j] > num:
                found = nums2[j]
                break
        result.append(found)

    return result


# =============================================================================
# WAY 9: Pre-compute all in stack
# =============================================================================
def next_greater_element_9(nums1, nums2):
    next_greater = {}
    stack = []

    for num in nums2:
        while stack and stack[-1] < num:
            smaller = stack.pop()
            next_greater[smaller] = num
        stack.append(num)

    # Build result with default -1
    result = []
    for x in nums1:
        if x in next_greater:
            result.append(next_greater[x])
        else:
            result.append(-1)

    return result


# =============================================================================
# WAY 10: One-liner with map
# =============================================================================
def next_greater_element_10(nums1, nums2):
    stack = []
    ng = {}
    for n in nums2:
        while stack and stack[-1] < n:
            ng[stack.pop()] = n
        stack.append(n)
    return list(map(lambda x: ng.get(x, -1), nums1))


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"For each element in nums1, I need to find the next greater element
to its right in nums2."

Key Insight:
"Two-step approach:
1. Precompute the next greater element for ALL elements in nums2
2. Then look up the answers for nums1 elements in O(1)"

Algorithm:
"I'll use a monotonic stack:
- Stack keeps elements waiting for their greater neighbor (in decreasing order)
- When I see a bigger element, I pop smaller ones - they found their next greater
- Any remaining elements in the stack have no greater neighbor"

Walkthrough:
"For nums2 = [1, 3, 4, 2]:
- 1: stack=[], push 1 -> stack=[1]
- 3: 1 < 3, pop 1, ng[1]=3, push 3 -> stack=[3]
- 4: 3 < 4, pop 3, ng[3]=4, push 4 -> stack=[4]
- 2: 4 > 2, just push -> stack=[4, 2]
- Remaining: ng[4]=-1, ng[2]=-1"

Edge cases:
- Last element always has -1
- All same: should not happen (distinct)
- Empty nums1: return []

COMPLEXITY:
+-----------+--------+----------+
| Approach  | Time   | Space    |
+-----------+--------+----------+
| Stack     | O(n+m) | O(n)     |
| Brute     | O(n*m) | O(1)     |
+-----------+--------+----------+
where n = len(nums1), m = len(nums2)
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Stack + HashMap", next_greater_element_1),
        ("Way 2: enumerate", next_greater_element_2),
        ("Way 3: Brute force", next_greater_element_3),
        ("Way 4: Dict comp", next_greater_element_4),
        ("Way 5: defaultdict", next_greater_element_5),
        ("Way 6: Most compact", next_greater_element_6),
        ("Way 7: Explicit loop", next_greater_element_7),
        ("Way 8: Index lookup", next_greater_element_8),
        ("Way 9: Pre-compute", next_greater_element_9),
        ("Way 10: One-liner", next_greater_element_10),
    ]

    test_cases = [
        ([4, 1, 2], [1, 3, 4, 2], [-1, 3, -1]),
        ([2, 4], [1, 2, 3, 4], [3, -1]),
        ([1, 3, 5, 2, 4], [6, 5, 4, 3, 2, 1, 7], [7, 7, 7, 7, 7]),
        ([1], [1, 2, 3], [2]),
        ([3, 2, 1], [1, 2, 3], [-1, 3, -1]),
    ]

    print("=" * 70)
    print("NEXT GREATER ELEMENT I - ALL 10 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for nums1, nums2, expected in test_cases:
            try:
                result = func(nums1, nums2)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                status = "✓" if result == expected else "✗"
                print(f"  {status} {name}: nums1={nums1}, nums2={nums2} -> {result} (expected {expected})")
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
