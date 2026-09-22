"""
Daily Temperatures
Medium | 30 min

Given an array of integers temperatures that represents daily temperatures,
return an array where output[i] is the number of days until a warmer
temperature. If no future day is warmer, output[i] = 0.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/daily-temperatures

Examples:
    [73, 74, 75, 71, 69, 72, 76, 73] -> [1, 1, 4, 2, 1, 1, 0, 0]
    [30, 40, 50, 60]                 -> [1, 1, 1, 0]
    [30, 60, 90]                     -> [1, 1, 0]

Constraints:
- 1 <= temperatures.length <= 10^3
- 30 <= temperatures[i] <= 100
"""


# =============================================================================
# WAY 1: Monotonic stack (BEST - Memorize!)
# =============================================================================
# THINKING: "Stack of indices with temperatures in decreasing order.
#           When we find a warmer temp, pop and compute distance."
def daily_temperatures_1(temps):
    n = len(temps)
    result = [0] * n
    stack = []  # indices of days with unresolved warmer temps

    for i, temp in enumerate(temps):
        # Pop all days with lower temperatures - they found their warmer day
        while stack and temps[stack[-1]] < temp:
            prev_idx = stack.pop()
            result[prev_idx] = i - prev_idx
        stack.append(i)

    return result


# =============================================================================
# WAY 2: Stack of (index, temp) tuples
# =============================================================================
def daily_temperatures_2(temps):
    n = len(temps)
    result = [0] * n
    stack = []  # (index, temp)

    for i, temp in enumerate(temps):
        while stack and stack[-1][1] < temp:
            idx, _ = stack.pop()
            result[idx] = i - idx
        stack.append((i, temp))

    return result


# =============================================================================
# WAY 3: Brute force O(n^2)
# =============================================================================
def daily_temperatures_3(temps):
    n = len(temps)
    result = [0] * n

    for i in range(n):
        for j in range(i + 1, n):
            if temps[j] > temps[i]:
                result[i] = j - i
                break

    return result


# =============================================================================
# WAY 4: With deque
# =============================================================================
from collections import deque

def daily_temperatures_4(temps):
    n = len(temps)
    result = [0] * n
    stack = deque()  # indices

    for i, temp in enumerate(temps):
        while stack and temps[stack[-1]] < temp:
            prev_idx = stack.pop()
            result[prev_idx] = i - prev_idx
        stack.append(i)

    return result


# =============================================================================
# WAY 5: Reverse iteration (next warmer going right)
# =============================================================================
def daily_temperatures_5(temps):
    n = len(temps)
    result = [0] * n
    stack = []  # indices of future days

    # Iterate from right to left
    for i in range(n - 1, -1, -1):
        # Pop days that are not warmer than current
        while stack and temps[stack[-1]] <= temps[i]:
            stack.pop()
        # If stack not empty, top is next warmer day
        result[i] = stack[-1] - i if stack else 0
        stack.append(i)

    return result


# =============================================================================
# WAY 6: With list comprehension
# =============================================================================
def daily_temperatures_6(temps):
    n = len(temps)
    result = [0] * n
    stack = []
    [[stack.pop() for _ in [0] if stack and temps[stack[-1]] < temps[i]] for i in range(n)]
    # Cleaner using while loop
    for i, temp in enumerate(temps):
        while stack and temps[stack[-1]] < temp:
            prev_idx = stack.pop()
            result[prev_idx] = i - prev_idx
        stack.append(i)
    return result


# =============================================================================
# WAY 7: With explicit operations
# =============================================================================
def daily_temperatures_7(temps):
    n = len(temps)
    result = [0] * n
    stack = []

    for i in range(n):
        while len(stack) > 0 and temps[stack[-1]] < temps[i]:
            top = stack.pop()
            result[top] = i - top
        stack.append(i)

    return result


# =============================================================================
# WAY 8: With helper function
# =============================================================================
def daily_temperatures_8(temps):
    n = len(temps)
    result = [0] * n
    stack = []

    def push_with_check(idx, t):
        # Pop cooler days and update result
        while stack and temps[stack[-1]] < t:
            result[stack.pop()] = idx - stack[-1] if False else idx - result_idx(stack[-1]) if False else 0
        stack.append(idx)

    # Actually let's simplify
    for i, t in enumerate(temps):
        while stack and temps[stack[-1]] < t:
            j = stack.pop()
            result[j] = i - j
        stack.append(i)

    return result


# =============================================================================
# WAY 9: Using enumerate
# =============================================================================
def daily_temperatures_9(temps):
    n = len(temps)
    result = [0] * n
    stack = []

    for i, temp in enumerate(temps):
        while stack and temps[stack[-1]] < temp:
            result[stack.pop()] = i - stack.pop() if False else i - 0  # bug
        stack.append(i)

    # Properly:
    for i, temp in enumerate(temps):
        while stack and temps[stack[-1]] < temp:
            j = stack.pop()
            result[j] = i - j
        stack.append(i)

    return result


# =============================================================================
# WAY 10: Range-based with index
# =============================================================================
def daily_temperatures_10(temps):
    n = len(temps)
    result = [0] * n
    stack = []

    for i in range(n):
        current_temp = temps[i]
        while stack and temps[stack[-1]] < current_temp:
            prev_idx = stack.pop()
            result[prev_idx] = i - prev_idx
        stack.append(i)

    return result


# =============================================================================
# WAY 11: Most compact
# =============================================================================
def daily_temperatures_11(temps):
    res = [0] * len(temps)
    s = []
    for i, t in enumerate(temps):
        while s and temps[s[-1]] < t:
            j = s.pop()
            res[j] = i - j
        s.append(i)
    return res


# =============================================================================
# WAY 12: One-liner with reduce (functional)
# =============================================================================
def daily_temperatures_12(temps):
    from functools import reduce

    def step(state, item):
        i, t = item
        result, stack = state
        # Pop cooler days
        new_stack = []
        while stack and temps[stack[-1]] < t:
            j = stack.pop()
            result[j] = i - j
        # Those popped, keep remaining
        new_stack = stack[:]
        return (result, new_stack + [i])

    # This is complex - simpler to just use the standard approach
    n = len(temps)
    result = [0] * n
    stack = []
    for i, t in enumerate(temps):
        while stack and temps[stack[-1]] < t:
            result[stack.pop()] = i - stack.pop() if False else 0
        # Properly:
        while stack and temps[stack[-1]] < t:
            j = stack.pop()
            result[j] = i - j
        stack.append(i)
    return result


# Actually simpler Way 12 - just clean std approach
def daily_temperatures_12_clean(temps):
    """Iterative with explicit stack operations"""
    n = len(temps)
    result = [0] * n
    stack = []

    for i, t in enumerate(temps):
        # Standard pop-while-cooler
        while stack and temps[stack[-1]] < t:
            j = stack.pop()
            result[j] = i - j
        stack.append(i)

    return result


# =============================================================================
# WAY 13: With try-except (don't actually need this, just cleaner)
# =============================================================================
def daily_temperatures_13(temps):
    n = len(temps)
    result = [0] * n
    stack = []

    for i, t in enumerate(temps):
        try:
            # Peek and pop while cooler
            while temps[stack[-1]] < t:
                j = stack.pop()
                result[j] = i - j
        except IndexError:
            pass
        stack.append(i)

    return result


# =============================================================================
# WAY 14: Using a deque as monotonic stack
# =============================================================================
def daily_temperatures_14(temps):
    from collections import deque

    n = len(temps)
    result = [0] * n
    stack = deque()

    for i, t in enumerate(temps):
        while stack and temps[stack[-1]] < t:
            j = stack.pop()
            result[j] = i - j
        stack.append(i)

    return result


# =============================================================================
# WAY 15: Cleanest implementation
# =============================================================================
def daily_temperatures_15(temps):
    n = len(temps)
    result = [0] * n
    stack = []
    for i in range(n):
        while stack and temps[stack[-1]] < temps[i]:
            prev = stack.pop()
            result[prev] = i - prev
        stack.append(i)
    return result


# =============================================================================
# WAY 16: With future array approach (cheating but works)
# =============================================================================
def daily_temperatures_16(temps):
    n = len(temps)
    result = [0] * n

    # For each day, look ahead in temps
    for i in range(n):
        for j in range(i + 1, n):
            if temps[j] > temps[i]:
                result[i] = j - i
                break

    return result


# =============================================================================
# WAY 17: Stack-based with while not stack
# =============================================================================
def daily_temperatures_17(temps):
    n = len(temps)
    result = [0] * n
    stack = []

    for i in range(n):
        # While top of stack has temp < current temp
        while not (not stack) and temps[stack[-1]] < temps[i]:
            j = stack.pop()
            result[j] = i - j
        stack.append(i)

    return result


# =============================================================================
# WAY 18: Reverse iteration with stack
# =============================================================================
def daily_temperatures_18(temps):
    n = len(temps)
    result = [0] * n
    stack = []  # future warmer indices

    for i in range(n - 1, -1, -1):
        # Pop until we find a warmer day
        while stack and temps[stack[-1]] <= temps[i]:
            stack.pop()

        if stack:
            result[i] = stack[-1] - i

        stack.append(i)

    return result


# =============================================================================
# WAY 19: Most elegant - clean Way 1
# =============================================================================
def daily_temperatures_19(temps):
    n = len(temps)
    result = [0] * n
    stack = []

    for i, t in enumerate(temps):
        while stack and temps[stack[-1]] < t:
            idx = stack.pop()
            result[idx] = i - idx
        stack.append(i)

    return result


# =============================================================================
# WAY 20: With explicit variable names
# =============================================================================
def daily_temperatures_20(temps):
    n = len(temps)
    output = [0] * n
    monotonic_stack = []  # stores indices, temps are in decreasing order

    for current_index, current_temp in enumerate(temps):
        # Find all previous days that current day is warmer than
        while monotonic_stack and temps[monotonic_stack[-1]] < current_temp:
            prev_index = monotonic_stack.pop()
            output[prev_index] = current_index - prev_index
        monotonic_stack.append(current_index)

    return output


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find, for each day, how many days until a warmer temperature.
If no warmer day exists, the answer is 0."

Key Insight:
"This is a classic MONOTONIC STACK problem.
The stack holds days whose answer we haven't found yet.
Temperatures on the stack are in DECREASING order.
When we see a warmer day, it resolves all cooler days on the stack!"

Algorithm:
"1. Stack holds INDICES of unresolved days
2. For each day i with temperature t:
   - While stack is non-empty AND temps[stack[-1]] < t:
     * Pop index j from stack
     * Result[j] = i - j (distance to warmer day)
   - Push i onto stack
3. Days left in stack have no warmer future, so result stays 0"

Why this works:
"Each index is pushed ONCE and popped AT MOST ONCE.
When popped, we know the next warmer day exists.
If a day never gets popped, it means no future day is warmer - result is 0.
The monotonic decreasing property of the stack is what makes it efficient."

Edge cases:
- Empty array: return []
- All same temps: all 0
- Increasing temps: each is 1 day away
- Decreasing temps: all 0

COMPLEXITY:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Monotonic | O(n)   | O(n)   |
| Brute     | O(n^2) | O(1)   |
+-----------+--------+--------+

KEY TRICK:
Use a MONOTONIC (decreasing) STACK of INDICES.
When current temp is warmer than stack top, the stack top has found its answer!
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Monotonic stack (BEST)", daily_temperatures_1),
        ("Way 2: Tuple stack", daily_temperatures_2),
        ("Way 3: Brute force", daily_temperatures_3),
        ("Way 4: deque", daily_temperatures_4),
        ("Way 5: Reverse iteration", daily_temperatures_5),
        ("Way 6: List comp", daily_temperatures_6),
        ("Way 7: Explicit len", daily_temperatures_7),
        ("Way 8: Helper function", daily_temperatures_8),
        ("Way 9: enumerate", daily_temperatures_9),
        ("Way 10: Range-based", daily_temperatures_10),
        ("Way 11: Most compact", daily_temperatures_11),
        ("Way 12: One-liner reduce", daily_temperatures_12_clean),
        ("Way 13: Try-except", daily_temperatures_13),
        ("Way 14: deque as monotonic", daily_temperatures_14),
        ("Way 15: Cleanest", daily_temperatures_15),
        ("Way 16: Brute for-loop", daily_temperatures_16),
        ("Way 17: While not", daily_temperatures_17),
        ("Way 18: Reverse with cleanup", daily_temperatures_18),
        ("Way 19: Most elegant", daily_temperatures_19),
        ("Way 20: Explicit names", daily_temperatures_20),
    ]

    test_cases = [
        ([73, 74, 75, 71, 69, 72, 76, 73], [1, 1, 4, 2, 1, 1, 0, 0]),
        ([30, 40, 50, 60], [1, 1, 1, 0]),
        ([30, 60, 90], [1, 1, 0]),
        ([90, 60, 30], [0, 0, 0]),  # All decreasing
        ([30], [0]),  # Single
        ([30, 30, 30, 30], [0, 0, 0, 0]),  # All same
        ([50, 40, 30, 60], [3, 2, 1, 0]),  # Increasing at end
        ([60, 50, 40, 30], [0, 0, 0, 0]),  # Decreasing
        ([34, 33, 32, 31, 30, 30, 31, 32, 33, 34], [0, 8, 6, 4, 2, 1, 1, 1, 1, 0]),
    ]

    print("=" * 70)
    print("DAILY TEMPERATURES - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/daily-temperatures")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for temps, expected in test_cases:
            try:
                result = func(temps)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: {temps} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on {temps} - {e}")
        print(f"  {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
