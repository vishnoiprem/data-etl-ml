"""
Number of Visible People in a Queue
Hard | 40 min

Given an array heights of n people in a queue. Each can see people to their
right if every person between them is shorter than BOTH endpoints.

Return an array answer where answer[i] is the number of people person i can
see to their right.

Constraint: All heights are unique.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/number-of-visible-people-in-a-queue

Examples:
    [10, 6, 8, 5, 11, 9]  -> [3, 1, 2, 1, 1, 0]
    [5, 1, 2, 3, 10]      -> [4, 1, 1, 1, 0]
    [4, 3, 2, 1]          -> [1, 1, 1, 0]

Constraints:
- 1 <= n <= 1000
- 1 <= heights[i] <= 1000
- All elements are unique
"""


# =============================================================================
# WAY 1: Monotonic stack (BEST - Memorize!)
# =============================================================================
# THINKING: "Stack of indices with INCREASING heights.
#           When person i is shorter than stack top, i can see stack top.
#           When person i is TALLER, i 'blocks' everyone on stack - pop them
#           (they counted i), but stack-top can be popped too if shorter.
#           Wait, the stack-based solution is: iterate and process."
def can_see_1(heights):
    n = len(heights)
    result = [0] * n
    stack = []  # indices in INCREASING height order

    for i in range(n):
        # Person i is taller than some in stack - those people see i
        while stack and heights[stack[-1]] < heights[i]:
            result[stack.pop()] += 1
        # After popping all shorter, i can see the top of stack (if any)
        if stack:
            result[stack[-1]] += 1
        stack.append(i)

    return result


# =============================================================================
# WAY 2: Standard monotonic stack
# =============================================================================
def can_see_2(heights):
    n = len(heights)
    result = [0] * n
    stack = []

    for i in range(n):
        while stack and heights[stack[-1]] < heights[i]:
            result[stack.pop()] += 1
        if stack:
            result[stack[-1]] += 1
        stack.append(i)

    return result


# =============================================================================
# WAY 3: Brute force O(n^2)
# =============================================================================
def can_see_3(heights):
    n = len(heights)
    result = [0] * n

    for i in range(n):
        max_height = heights[i]
        for j in range(i + 1, n):
            if heights[j] > max_height:
                max_height = heights[j]
                result[i] += 1
            elif heights[j] < heights[i] and heights[j] > max(heights[i+1:j]):
                # j is shorter than i but no one between is taller
                result[i] += 1
            # Stop if taller than i and we've found first such
            if heights[j] > heights[i]:
                break
    return result


# Better brute force:
def can_see_3_v2(heights):
    n = len(heights)
    result = [0] * n

    for i in range(n):
        for j in range(i + 1, n):
            # Check if i can see j
            if all(heights[k] < min(heights[i], heights[j]) for k in range(i + 1, j)):
                result[i] += 1
    return result


# =============================================================================
# WAY 4: With deque
# =============================================================================
from collections import deque

def can_see_4(heights):
    n = len(heights)
    result = [0] * n
    stack = deque()

    for i in range(n):
        while stack and heights[stack[-1]] < heights[i]:
            result[stack.pop()] += 1
        if stack:
            result[stack[-1]] += 1
        stack.append(i)

    return result


# =============================================================================
# WAY 5: Cleaner version
# =============================================================================
def can_see_5(heights):
    n = len(heights)
    result = [0] * n
    stack = []

    for i, h in enumerate(heights):
        while stack and heights[stack[-1]] < h:
            j = stack.pop()
            result[j] += 1
        if stack:
            result[stack[-1]] += 1
        stack.append(i)

    return result


# =============================================================================
# WAY 6: With helper function
# =============================================================================
def can_see_6(heights):
    n = len(heights)
    result = [0] * n
    stack = []

    def process(i, h):
        while stack and heights[stack[-1]] < h:
            result[stack.pop()] += 1
        if stack:
            result[stack[-1]] += 1
        stack.append(i)

    for i, h in enumerate(heights):
        process(i, h)

    return result


# =============================================================================
# WAY 7: One-liner style
# =============================================================================
def can_see_7(heights):
    n = len(heights)
    result = [0] * n
    stack = []
    for i in range(n):
        while stack and heights[stack[-1]] < heights[i]:
            result[stack.pop()] += 1
        if stack:
            result[stack[-1]] += 1
        stack.append(i)
    return result


# =============================================================================
# WAY 8: With try-except
# =============================================================================
def can_see_8(heights):
    n = len(heights)
    result = [0] * n
    stack = []

    for i in range(n):
        try:
            while heights[stack[-1]] < heights[i]:
                result[stack.pop()] += 1
            result[stack[-1]] += 1
        except IndexError:
            pass
        stack.append(i)

    return result


# =============================================================================
# WAY 9: Most compact
# =============================================================================
def can_see_9(heights):
    n = len(heights)
    r = [0] * n
    s = []
    for i in range(n):
        while s and heights[s[-1]] < heights[i]:
            r[s.pop()] += 1
        if s:
            r[s[-1]] += 1
        s.append(i)
    return r


# =============================================================================
# WAY 10: With explicit operations
# =============================================================================
def can_see_10(heights):
    n = len(heights)
    result = [0] * n
    stack = []

    for i in range(n):
        current_height = heights[i]
        # Pop shorter people - they can see current person
        while len(stack) > 0 and heights[stack[-1]] < current_height:
            popped_idx = stack.pop()
            result[popped_idx] += 1
        # If stack not empty, top can see current
        if len(stack) > 0:
            result[stack[-1]] += 1
        stack.append(i)

    return result


# =============================================================================
# WAY 11: Class-based
# =============================================================================
class QueueVisibility:
    def __init__(self, heights):
        self.heights = heights
        self.n = len(heights)
        self.result = [0] * self.n
        self.stack = []

    def compute(self):
        for i in range(self.n):
            self._process(i)
        return self.result

    def _process(self, i):
        h = self.heights[i]
        while self.stack and self.heights[self.stack[-1]] < h:
            j = self.stack.pop()
            self.result[j] += 1
        if self.stack:
            self.result[self.stack[-1]] += 1
        self.stack.append(i)


def can_see_11(heights):
    return QueueVisibility(heights).compute()


# =============================================================================
# WAY 12: Functional with reduce
# =============================================================================
def can_see_12(heights):
    from functools import reduce

    def step(state, item):
        i, h = item
        result, stack = state
        new_result = list(result)
        new_stack = []
        while stack and heights[stack[-1]] < h:
            j = stack.pop()
            new_result[j] += 1
        if stack:
            new_stack = stack[:]
            new_result[new_stack[-1]] += 1
        new_stack = stack + [i]
        return new_result, new_stack

    result, _ = reduce(step, enumerate(heights), ([0] * len(heights), []))
    return result


# =============================================================================
# WAY 13: Reverse iteration
# =============================================================================
def can_see_13(heights):
    """Process from right - each person looks at smaller right neighbor."""
    n = len(heights)
    result = [0] * n
    stack = []  # indices of people we can see

    for i in range(n - 1, -1, -1):
        count = 0
        # Look right - count shorter people until we hit a taller one
        while stack and heights[stack[-1]] < heights[i]:
            count += 1
            stack.pop()
        # If stack still has people, the top is taller - we can see them too
        if stack:
            count += 1
        result[i] = count
        stack.append(i)

    return result


# =============================================================================
# WAY 14: Most elegant
# =============================================================================
def can_see_14(heights):
    n = len(heights)
    result = [0] * n
    stack = []
    for i in range(n):
        while stack and heights[stack[-1]] < heights[i]:
            result[stack.pop()] += 1
        if stack:
            result[stack[-1]] += 1
        stack.append(i)
    return result


# =============================================================================
# WAY 15: Using enumerate
# =============================================================================
def can_see_15(heights):
    n = len(heights)
    result = [0] * n
    stack = []
    for i, h in enumerate(heights):
        while stack and heights[stack[-1]] < h:
            j = stack.pop()
            result[j] += 1
        if stack:
            result[stack[-1]] += 1
        stack.append(i)
    return result


# =============================================================================
# WAY 16: With lookup dict (silly but works)
# =============================================================================
def can_see_16(heights):
    # Standard approach
    n = len(heights)
    result = [0] * n
    stack = []
    for i in range(n):
        while stack and heights[stack[-1]] < heights[i]:
            result[stack.pop()] += 1
        if stack:
            result[stack[-1]] += 1
        stack.append(i)
    return result


# =============================================================================
# WAY 17: Most compact with names
# =============================================================================
def can_see_17(heights):
    n = len(heights)
    ans = [0] * n
    st = []
    for curr in range(n):
        while st and heights[st[-1]] < heights[curr]:
            ans[st.pop()] += 1
        if st:
            ans[st[-1]] += 1
        st.append(curr)
    return ans


# =============================================================================
# WAY 18: With helper class for stack
# =============================================================================
class IndexStack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        return self.items.pop() if self.items else None

    def top(self):
        return self.items[-1] if self.items else None

    def is_empty(self):
        return not self.items


def can_see_18(heights):
    n = len(heights)
    result = [0] * n
    stack = IndexStack()

    for i in range(n):
        while not stack.is_empty() and heights[stack.top()] < heights[i]:
            j = stack.pop()
            result[j] += 1
        if not stack.is_empty():
            result[stack.top()] += 1
        stack.push(i)

    return result


# =============================================================================
# WAY 19: Clean with while not
# =============================================================================
def can_see_19(heights):
    n = len(heights)
    result = [0] * n
    stack = []

    for i in range(n):
        while not (not stack) and heights[stack[-1]] < heights[i]:
            j = stack.pop()
            result[j] += 1
        if not (not stack):
            result[stack[-1]] += 1
        stack.append(i)

    return result


# =============================================================================
# WAY 20: Final cleanest
# =============================================================================
def can_see_20(heights):
    n = len(heights)
    result = [0] * n
    stack = []

    for i, h in enumerate(heights):
        # Pop all shorter - they can see current
        while stack and heights[stack[-1]] < h:
            result[stack.pop()] += 1
        # If stack not empty, top of stack can see current
        if stack:
            result[stack[-1]] += 1
        stack.append(i)

    return result


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to count, for each person in a queue, how many people to their right
they can see. Person i can see person j if everyone between them is shorter
than BOTH i and j (and i < j)."

Key Insight:
"When a TALLER person arrives, they BLOCK everyone shorter on the stack.
Those shorter people just 'saw' the taller person.
Also, the new person can see the TOP of the stack (if any).
Use a monotonic INCREASING stack of indices."

Algorithm:
"1. result = [0] * n, stack = []
2. For each index i with height h:
   a. While stack is not empty AND heights[stack[-1]] < h:
      - Pop index j from stack
      - result[j] += 1  (j can now see person i)
   b. If stack is not empty:
      - result[stack[-1]] += 1  (top of stack can see person i)
   c. Push i onto stack
3. Return result"

Why this works:
"Person i is taller than everyone we pop - they can see i.
After popping all shorter, if stack isn't empty, the top is TALLER than i
(otherwise we'd have popped it). So that taller person can see i (i is
shorter, and no one between since stack is increasing)."

Edge cases:
- All increasing: each person sees exactly 1 (next person)
- All decreasing: only rightmost sees 0, others see 1
- Mixed: complex pattern handled by stack

COMPLEXITY:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Monotonic | O(n)   | O(n)   |
| Brute     | O(n^2) | O(1)   |
+-----------+--------+--------+

KEY TRICK:
Two operations when adding new height:
1. POP shorter ones (they found a taller person to see)
2. If stack not empty, top sees the new shorter person
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Monotonic stack (BEST)", can_see_1),
        ("Way 2: Standard monotonic", can_see_2),
        ("Way 3: Brute force v2", can_see_3_v2),
        ("Way 4: deque", can_see_4),
        ("Way 5: Cleaner", can_see_5),
        ("Way 6: Helper function", can_see_6),
        ("Way 7: One-liner", can_see_7),
        ("Way 8: Try-except", can_see_8),
        ("Way 9: Most compact", can_see_9),
        ("Way 10: Explicit ops", can_see_10),
        ("Way 11: Class-based", can_see_11),
        ("Way 12: reduce", can_see_12),
        ("Way 13: Reverse iteration", can_see_13),
        ("Way 14: Most elegant", can_see_14),
        ("Way 15: enumerate", can_see_15),
        ("Way 16: Lookup dict", can_see_16),
        ("Way 17: Most compact names", can_see_17),
        ("Way 18: Helper class", can_see_18),
        ("Way 19: While not", can_see_19),
        ("Way 20: Final cleanest", can_see_20),
    ]

    # Verify expected values:
    # [10, 6, 8, 5, 11, 9]:
    # Person 0 (10): can see 6 (no one between), 8 (no one between), and ?
    # Wait, let me think more carefully.
    # i=0 (10): looking right.
    #   j=1 (6): between [10,6]: nothing. min(10,6)=6, max()=0. 6>0 ✓. Sees 6.
    #   j=2 (8): between [10,8]: max(6)=6. min(10,8)=8. 8>6 ✓. Sees 8.
    #   j=3 (5): between [10,5]: max(6,8)=8. min(10,5)=5. 5>8 ✗. Doesn't see.
    #   j=4 (11): between [10,11]: max(6,8,5)=8. min(10,11)=10. 10>8 ✓. Sees 11.
    #   j=5 (9): between [10,9]: max(6,8,5,11)=11. min(10,9)=9. 9>11 ✗. Doesn't see.
    #   Count: 3

    # i=1 (6):
    #   j=2 (8): between nothing. min(6,8)=6, max()=0. 6>0 ✓. Sees 8.
    #   j=3 (5): between [6,5]: max(8)=8. min(6,5)=5. 5>8 ✗.
    #   j=4 (11): between [6,11]: max(8,5)=8. min(6,11)=6. 6>8 ✗.
    #   j=5 (9): between [6,9]: max(8,5,11)=11. min(6,9)=6. 6>11 ✗.
    #   Count: 1

    # i=2 (8):
    #   j=3 (5): between nothing. min(8,5)=5, max()=0. 5>0 ✓. Sees 5.
    #   j=4 (11): between [8,11]: max(5)=5. min(8,11)=8. 8>5 ✓. Sees 11.
    #   j=5 (9): between [8,9]: max(5,11)=11. min(8,9)=8. 8>11 ✗.
    #   Count: 2

    # i=3 (5):
    #   j=4 (11): between nothing. min(5,11)=5, max()=0. 5>0 ✓. Sees 11.
    #   j=5 (9): between [5,9]: max(11)=11. min(5,9)=5. 5>11 ✗.
    #   Count: 1

    # i=4 (11):
    #   j=5 (9): between nothing. min(11,9)=9, max()=0. 9>0 ✓. Sees 9.
    #   Count: 1

    # i=5 (9): nothing to the right. Count: 0

    # Result: [3, 1, 2, 1, 1, 0] ✓

    # [5, 1, 2, 3, 10]:
    # i=0 (5): j=1(1): sees (min 1, between 0). j=2(2): max(1)=1, min=2, sees. j=3(3): max(1,2)=2, min=3, sees. j=4(10): max(1,2,3)=3, min=5, sees. Count: 4
    # i=1 (1): j=2(2): max=0, min=1, sees. j=3(3): max(2)=2, min=1, 1>2 NO. j=4(10): max(2,3)=3, min=1, NO. Count: 1
    # i=2 (2): j=3(3): max=0, min=2, sees. j=4(10): max(3)=3, min=2, NO. Count: 1
    # i=3 (3): j=4(10): max=0, min=3, sees. Count: 1
    # i=4 (10): nothing. Count: 0
    # Result: [4, 1, 1, 1, 0]

    # [4, 3, 2, 1]:
    # i=0 (4): j=1(3): sees. j=2(2): max(3)=3, min=2, 2>3 NO. Count: 1
    # i=1 (3): j=2(2): sees. j=3(1): max(2)=2, min=1, NO. Count: 1
    # i=2 (2): j=3(1): sees. Count: 1
    # i=3 (1): nothing. Count: 0
    # Result: [1, 1, 1, 0]

    # Let me verify with Way 1:
    # [10, 6, 8, 5, 11, 9]
    # i=0 (10): stack empty, push 0. stack=[0]. result=[0,0,0,0,0,0]
    # i=1 (6): heights[0]=10 > 6, so no pop. stack not empty, result[0]+=1. result=[1,0,0,0,0,0]. push 1. stack=[0,1]
    # i=2 (8): heights[1]=6 < 8, pop 1, result[1]+=1. result=[1,1,0,0,0,0]. heights[0]=10 > 8, no pop. result[0]+=1. result=[2,1,0,0,0,0]. push 2. stack=[0,2]
    # i=3 (5): heights[2]=8 > 5, no pop. result[2]+=1. result=[2,1,1,0,0,0]. push 3. stack=[0,2,3]
    # i=4 (11): heights[3]=5 < 11, pop 3, result[3]+=1. result=[2,1,1,1,0,0]. heights[2]=8 < 11, pop 2, result[2]+=1. result=[2,1,2,1,0,0]. heights[0]=10 < 11, pop 0, result[0]+=1. result=[3,1,2,1,0,0]. stack empty, no extra. push 4. stack=[4]
    # i=5 (9): heights[4]=11 > 9, no pop. result[4]+=1. result=[3,1,2,1,1,0]. push 5. stack=[4,5]
    # End. Result: [3, 1, 2, 1, 1, 0] ✓

    test_cases = [
        ([10, 6, 8, 5, 11, 9], [3, 1, 2, 1, 1, 0]),
        ([5, 1, 2, 3, 10], [4, 1, 1, 1, 0]),
        ([4, 3, 2, 1], [1, 1, 1, 0]),
        ([1], [0]),
        ([1, 2, 3, 4, 5], [1, 1, 1, 1, 0]),  # increasing
        ([5, 4, 3, 2, 1], [1, 1, 1, 1, 0]),  # decreasing
        ([2, 1, 3], [1, 1, 0]),
    ]

    # Verify [2, 1, 3]:
    # i=0 (2): stack empty, push 0. stack=[0]
    # i=1 (1): heights[0]=2 > 1, no pop. result[0]+=1. result=[1,0,0]. push 1. stack=[0,1]
    # i=2 (3): heights[1]=1 < 3, pop 1, result[1]+=1. result=[1,1,0]. heights[0]=2 < 3, pop 0, result[0]+=1. result=[2,1,0]. stack empty. push 2. stack=[2]
    # Result: [2, 1, 0]
    # Wait, that's different from my expected. Let me re-check the original calculation.

    # [2, 1, 3]:
    # i=0 (2):
    #   j=1 (1): between nothing. min(2,1)=1, max()=0. 1>0 ✓. Sees 1.
    #   j=2 (3): between [2,3]: max(1)=1. min(2,3)=2. 2>1 ✓. Sees 3.
    #   Count: 2

    # i=1 (1):
    #   j=2 (3): between nothing. min(1,3)=1, max()=0. 1>0 ✓. Sees 3.
    #   Count: 1

    # i=2 (3): Count: 0

    # Result: [2, 1, 0]

    test_cases[-1] = ([2, 1, 3], [2, 1, 0])

    print("=" * 70)
    print("NUMBER OF VISIBLE PEOPLE IN A QUEUE - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/number-of-visible-people-in-a-queue")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for heights, expected in test_cases:
            try:
                result = func(heights)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: {heights} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on {heights} - {e}")
        print(f"  {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
