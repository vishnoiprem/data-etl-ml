"""
Next Greater Element I
Easy | 15 min

Given two arrays:
- nums1: subset of nums2 (unique elements)
- nums2: larger array

For each nums1[i], find the FIRST element in nums2 that is:
- To the right of nums1[i]'s position in nums2
- Strictly greater than nums1[i]

If no such element, return -1.

Return the result array.

Examples:
    nums1 = [4,1,2], nums2 = [1,3,4,2]
        -> [-1, 3, -1]
        (4 has no greater after, 1 -> 3 (next greater), 2 -> no greater)

    nums1 = [2,4], nums2 = [1,2,3,4]
        -> [3, -1]

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/next-greater-element-i

Constraints:
- 1 <= nums1.length <= nums2.length <= 1000
- 0 <= nums1[i], nums2[i] <= 10^4
- All integers in nums1 and nums2 are unique
- All integers of nums1 also appear in nums2
"""


# =============================================================================
# WAY 1: Monotonic stack for nums2, then lookup (BEST - Memorize!)
# =============================================================================
def next_greater_element_1(nums1, nums2):
    # Build next_greater map for nums2 using monotonic stack
    next_greater = {}
    stack = []  # indices or values in decreasing order
    for num in nums2:
        # Pop smaller elements and record this num as their next greater
        while stack and stack[-1] < num:
            next_greater[stack.pop()] = num
        stack.append(num)
    # Remaining elements have no next greater
    return [next_greater.get(num, -1) for num in nums1]


# =============================================================================
# WAY 2: Same with index-based stack
# =============================================================================
def next_greater_element_2(nums1, nums2):
    next_greater = {}
    stack = []  # indices
    for i, num in enumerate(nums2):
        while stack and nums2[stack[-1]] < num:
            next_greater[nums2[stack.pop()]] = num
        stack.append(i)
    return [next_greater.get(num, -1) for num in nums1]


# =============================================================================
# WAY 3: Brute force O(n*m)
# =============================================================================
def next_greater_element_3(nums1, nums2):
    result = []
    for num in nums1:
        idx = nums2.index(num)
        found = -1
        for j in range(idx + 1, len(nums2)):
            if nums2[j] > num:
                found = nums2[j]
                break
        result.append(found)
    return result


# =============================================================================
# WAY 4: Pre-compute next greater for all of nums2
# =============================================================================
def next_greater_element_4(nums1, nums2):
    # Pre-compute next greater for each index in nums2
    n = len(nums2)
    next_idx = [-1] * n
    stack = []  # indices
    for i in range(n):
        while stack and nums2[stack[-1]] < nums2[i]:
            next_idx[stack.pop()] = i
        stack.append(i)
    # Build map
    pos_to_next = {nums2[i]: nums2[next_idx[i]] if next_idx[i] != -1 else -1 for i in range(n)}
    return [pos_to_next.get(num, -1) for num in nums1]


# =============================================================================
# WAY 5: Using deque
# =============================================================================
def next_greater_element_5(nums1, nums2):
    from collections import deque
    next_greater = {}
    stack = deque()
    for num in nums2:
        while stack and stack[-1] < num:
            next_greater[stack.pop()] = num
        stack.append(num)
    return [next_greater.get(num, -1) for num in nums1]


# =============================================================================
# WAY 6: Functional with map
# =============================================================================
def next_greater_element_6(nums1, nums2):
    # Build next_greater dict
    next_greater = {}
    for i in range(len(nums2)):
        # Find next greater for nums2[i]
        for j in range(i + 1, len(nums2)):
            if nums2[j] > nums2[i]:
                next_greater[nums2[i]] = nums2[j]
                break
    return [next_greater.get(num, -1) for num in nums1]


# =============================================================================
# WAY 7: Stack with explicit lookup
# =============================================================================
def next_greater_element_7(nums1, nums2):
    # Compute map of value -> next greater
    next_greater_map = {}
    stack = []
    for v in nums2:
        while stack and stack[-1] < v:
            val = stack.pop()
            next_greater_map[val] = v
        stack.append(v)
    # For each in nums1, look up
    return [-1 if num not in next_greater_map else next_greater_map[num] for num in nums1]


# =============================================================================
# WAY 8: Most concise
# =============================================================================
def next_greater_element_8(nums1, nums2):
    ng = {}
    stack = []
    for n in nums2:
        while stack and stack[-1] < n:
            ng[stack.pop()] = n
        stack.append(n)
    return [ng.get(n, -1) for n in nums1]


# =============================================================================
# WAY 9: With reverse iteration (alternative)
# =============================================================================
def next_greater_element_9(nums1, nums2):
    # Build next greater dict by iterating in reverse
    next_greater = {}
    stack = []
    for num in reversed(nums2):
        # Pop smaller or equal to maintain decreasing stack
        while stack and stack[-1] <= num:
            stack.pop()
        if stack:
            next_greater[num] = stack[-1]
        else:
            next_greater[num] = -1
        stack.append(num)
    return [next_greater[num] for num in nums1]


# =============================================================================
# WAY 10: With explicit index list
# =============================================================================
def next_greater_element_10(nums1, nums2):
    n = len(nums2)
    pos = {v: i for i, v in enumerate(nums2)}
    next_greater = [-1] * n
    stack = []
    for i in range(n):
        while stack and nums2[stack[-1]] < nums2[i]:
            next_greater[stack.pop()] = nums2[i]
        stack.append(i)
    # Map value to next greater
    val_to_ng = {nums2[i]: next_greater[i] for i in range(n)}
    return [val_to_ng[num] for num in nums1]


# =============================================================================
# WAY 11: Class-based
# =============================================================================
class NextGreaterFinder:
    def __init__(self, nums2):
        self.next_greater = {}
        self._build(nums2)

    def _build(self, nums2):
        stack = []
        for v in nums2:
            while stack and stack[-1] < v:
                self.next_greater[stack.pop()] = v
            stack.append(v)

    def find(self, num):
        return self.next_greater.get(num, -1)


def next_greater_element_11(nums1, nums2):
    finder = NextGreaterFinder(nums2)
    return [finder.find(num) for num in nums1]


# =============================================================================
# WAY 12: Two-pass style
# =============================================================================
def next_greater_element_12(nums1, nums2):
    # First pass: compute all next greater
    ng_map = {}
    stack = []
    for n in nums2:
        while stack and stack[-1] < n:
            ng_map[stack.pop()] = n
        stack.append(n)
    # Second pass: lookup
    return [ng_map.get(n, -1) for n in nums1]


# =============================================================================
# WAY 13: With enumerate
# =============================================================================
def next_greater_element_13(nums1, nums2):
    ng_map = {}
    stack = []
    for i, n in enumerate(nums2):
        while stack and nums2[stack[-1]] < n:
            ng_map[nums2[stack.pop()]] = n
        stack.append(i)
    return [ng_map.get(n, -1) for n in nums1]


# =============================================================================
# WAY 14: Most readable
# =============================================================================
def next_greater_element_14(nums1, nums2):
    ng = {}
    decreasing_stack = []
    for num in nums2:
        while decreasing_stack and decreasing_stack[-1] < num:
            smaller = decreasing_stack.pop()
            ng[smaller] = num
        decreasing_stack.append(num)
    return [ng.get(num, -1) for num in nums1]


# =============================================================================
# WAY 15: Using list comprehension for lookup
# =============================================================================
def next_greater_element_15(nums1, nums2):
    ng = {}
    stack = []
    for v in nums2:
        while stack and stack[-1] < v:
            ng[stack.pop()] = v
        stack.append(v)
    return list(map(lambda n: ng.get(n, -1), nums1))


# =============================================================================
# WAY 16: With defaultdict for safety
# =============================================================================
def next_greater_element_16(nums1, nums2):
    from collections import defaultdict
    ng = defaultdict(lambda: -1)
    stack = []
    for v in nums2:
        while stack and stack[-1] < v:
            ng[stack.pop()] = v
        stack.append(v)
    return [ng[n] for n in nums1]


# =============================================================================
# WAY 17: With explicit try/except
# =============================================================================
def next_greater_element_17(nums1, nums2):
    ng = {}
    stack = []
    for v in nums2:
        while stack and stack[-1] < v:
            ng[stack.pop()] = v
        stack.append(v)
    result = []
    for n in nums1:
        try:
            result.append(ng[n])
        except KeyError:
            result.append(-1)
    return result


# =============================================================================
# WAY 18: Using generator expression
# =============================================================================
def next_greater_element_18(nums1, nums2):
    ng = {}
    stack = []
    for v in nums2:
        while stack and stack[-1] < v:
            ng[stack.pop()] = v
        stack.append(v)
    return [ng[v] if v in ng else -1 for v in nums1]


# =============================================================================
# WAY 19: Verbose with comments
# =============================================================================
def next_greater_element_19(nums1, nums2):
    # Build next_greater map: for each element in nums2, find first greater to right
    next_greater = {}
    # Stack stores elements that haven't found their next greater yet
    stack = []
    for v in nums2:
        # Current v is greater than stack top - so it's the next greater for stack top
        while stack and stack[-1] < v:
            # Found next greater for stack top
            next_greater[stack.pop()] = v
        # Push v as a potential next greater for future elements
        stack.append(v)
    # Stack now has elements with no next greater; they default to -1
    return [next_greater.get(num, -1) for num in nums1]


# =============================================================================
# WAY 20: Final cleanest
# =============================================================================
def next_greater_element_20(nums1, nums2):
    ng = {}
    stack = []
    for n in nums2:
        while stack and stack[-1] < n:
            ng[stack.pop()] = n
        stack.append(n)
    return [ng.get(n, -1) for n in nums1]


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I have two arrays. nums1 is a subset of nums2. For each element in
nums1, I need to find the next greater element to its right in nums2."

Key Insight:
"Use a MONOTONIC DECREASING STACK on nums2!
- For each element v in nums2:
  - While stack non-empty and stack top < v:
    * POP top, set next_greater[top] = v (this is the next greater for top)
  - Push v onto stack
- At the end, elements still in stack have no next greater (-1)
- Then look up each num in nums1 from the map."

Algorithm:
"1. Initialize empty stack and ng map
2. For each v in nums2:
   - While stack and stack[-1] < v:
     * ng[stack.pop()] = v
   - stack.append(v)
3. Return [ng.get(num, -1) for num in nums1]"

Why this works:
"The stack maintains elements WAITING for their next greater.
When we see a value v, it's the next greater for ALL stack tops smaller
than it. We pop those, recording v as their next greater.
Then v goes on the stack to wait for ITS next greater."

Edge cases:
- All decreasing: nothing pops, all -1
- All increasing: each gets next greater
- nums1 subset of nums2: lookup works

COMPLEXITY:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Stack     | O(n+m) | O(n)   |
| Brute     | O(n*m) | O(1)   |
+-----------+--------+--------+
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Stack + lookup", next_greater_element_1),
        ("Way 2: Index stack", next_greater_element_2),
        ("Way 3: Brute force", next_greater_element_3),
        ("Way 4: Pre-compute indices", next_greater_element_4),
        ("Way 5: Deque", next_greater_element_5),
        ("Way 6: Functional map", next_greater_element_6),
        ("Way 7: With lookup", next_greater_element_7),
        ("Way 8: Most concise", next_greater_element_8),
        ("Way 9: Reverse iteration", next_greater_element_9),
        ("Way 10: Position dict", next_greater_element_10),
        ("Way 11: Class-based", next_greater_element_11),
        ("Way 12: Two-pass", next_greater_element_12),
        ("Way 13: With enumerate", next_greater_element_13),
        ("Way 14: Most readable", next_greater_element_14),
        ("Way 15: List comp + map", next_greater_element_15),
        ("Way 16: defaultdict", next_greater_element_16),
        ("Way 17: Try/except", next_greater_element_17),
        ("Way 18: Generator", next_greater_element_18),
        ("Way 19: Verbose", next_greater_element_19),
        ("Way 20: Final cleanest", next_greater_element_20),
    ]

    test_cases = [
        ([4, 1, 2], [1, 3, 4, 2], [-1, 3, -1]),
        ([2, 4], [1, 2, 3, 4], [3, -1]),
        ([1], [1], [-1]),
        ([1], [1, 2], [2]),
        ([2], [2, 1], [-1]),
        ([1, 2, 3], [3, 2, 1], [-1, -1, -1]),  # All decreasing in nums2, no next greater
        ([3, 2, 1], [1, 2, 3], [-1, 3, 2]),  # Increasing nums2:
        # 3 -> -1 (3 is largest)
        # 2 -> 3 (next greater)
        # 1 -> 2 (next greater)
        ([4, 1, 2, 3], [1, 3, 4, 2], [-1, 3, -1, 4]),
        # 4 -> -1 (no greater after position of 4 in nums2, which is idx 2)
        # 1 -> 3 (at idx 0, next greater is 3 at idx 1)
        # 2 -> -1 (at idx 3, no greater after)
        # 3 -> 4 (at idx 1, next greater is 4 at idx 2)
    ]

    print("=" * 70)
    print("NEXT GREATER ELEMENT I - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/next-greater-element-i")
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
                    print(f"  X {name}: nums1={nums1}, nums2={nums2} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on nums1={nums1} - {e}")
        print(f"  {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
