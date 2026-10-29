# Daily Temperatures - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/daily-temperatures

## The Problem
```
Given an array of daily temperatures, return an array where output[i] is the
number of days until a warmer temperature. If no future day is warmer,
output[i] = 0.

Examples:
    [73, 74, 75, 71, 69, 72, 76, 73] -> [1, 1, 4, 2, 1, 1, 0, 0]
    [30, 40, 50, 60]                 -> [1, 1, 1, 0]
    [30, 60, 90]                     -> [1, 1, 0]

Constraints:
- 1 <= temperatures.length <= 10^3
- 30 <= temperatures[i] <= 100
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
temps = [73, 74, 75, 71, 69, 72, 76, 73]

Day 0 (73): next warmer? Day 1 (74) → 1 day
Day 1 (74): next warmer? Day 2 (75) → 1 day
Day 2 (75): next warmer? Day 6 (76) → 4 days (75<76 at days 3-5 nope, day 6 yes)
Day 3 (71): next warmer? Day 5 (72) → 2 days
Day 4 (69): next warmer? Day 5 (72) → 1 day
Day 5 (72): next warmer? Day 6 (76) → 1 day
Day 6 (76): next warmer? NONE → 0
Day 7 (73): next warmer? NONE → 0

Result: [1, 1, 4, 2, 1, 1, 0, 0] ✓
```

### Step 2: The Trick
> "MONOTONIC STACK of INDICES:
> - Stack keeps days whose answer we still need
> - Temperatures in stack are in DECREASING order
> - When we see a NEW day, pop all cooler days from stack - they found their warmer day!"

### Step 3: Why Monotonic Stack?
> "Each day 'waits' for a warmer day. When a warmer day arrives, it answers
> ALL previously-waiting cooler days at once. Stack gives us LIFO access to
> the most recent unsettled days."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to find, for each day, the next day with a warmer temperature.
> This is a classic 'next greater element' problem, perfect for a monotonic stack."

**Key Insight:**
> "I'll maintain a stack of INDICES where temps have been DECREASING.
> When I encounter a new day with temp t:
> - It might be the 'next warmer' for some previously seen cooler days
> - I pop those cooler days from the stack and set their answer = current_index - their_index
> - Then I push current_index onto stack"

**Algorithm:**
> "1. result = [0] * n, stack = []
> 2. For each index i with temp t:
>    - While stack is non-empty AND temps[stack[-1]] < t:
>      * Pop index j from stack
>      * result[j] = i - j  (j found its warmer day at i)
>    - Push i onto stack
> 3. Days still in stack have no warmer future - result stays 0
> 4. Return result"

**Why this works:**
> "When we see temp t, EVERY index in the stack has a temp <= t.
> Those with temps < t just found their warmer day (it's day i).
> We pop them and record the distance. The remaining ones (temps = t or > t) still wait."

**Edge cases:**
- Decreasing sequence: all 0 (nothing in stack gets popped)
- Increasing sequence: each day found its answer next day
- All same: all 0 (no temperature is strictly warmer)
- Single day: 0

---

## The 20 Implementations (Simple to Complex)

### Way 1: Monotonic Stack (BEST - Memorize!)
```python
def dailyTemperatures(temps):
    n = len(temps)
    result = [0] * n
    stack = []  # indices in decreasing temp order

    for i, temp in enumerate(temps):
        while stack and temps[stack[-1]] < temp:
            prev_idx = stack.pop()
            result[prev_idx] = i - prev_idx
        stack.append(i)

    return result
```

### Way 2: Stack of (index, temp) tuples
### Way 3: Brute force O(n^2)
### Way 4: deque as stack
### Way 5: Reverse iteration
### Way 6-10: Variations

### Way 11-15: Specialized
- Way 11: Most compact
- Way 12: reduce-based
- Way 13: Try-except for stack
- Way 14: deque as monotonic
- Way 15: Cleanest

### Way 16-20: More variations
- Way 16: Pure brute O(n^2)
- Way 17: While not
- Way 18: Reverse with cleanup
- Way 19: Most elegant
- Way 20: Explicit variable names

---

## Decision Tree

```
+------------------+-------------+--------------+
| Scenario         | Best        | Why          |
+------------------+-------------+--------------+
| Most efficient   | Monotonic   | O(n)         |
| Educational      | Brute       | Simple       |
| Functional       | reduce      | No mutation  |
| Reverse          | Iter right   | Different    |
+------------------+-------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Monotonic stack | O(n) | O(n) |
| Brute | O(n^2) | O(1) |
| Reverse iteration | O(n) | O(n) |

---

## Walkthrough Example

```
temps = [73, 74, 75, 71, 69, 72, 76, 73]

i=0, 73: stack empty, push 0. stack=[0]
i=1, 74: 73<74, pop 0, result[0]=1-0=1. push 1. stack=[1]
i=2, 75: 74<75, pop 1, result[1]=2-1=1. push 2. stack=[2]
i=3, 71: 75<71? No. push 3. stack=[2,3]
i=4, 69: 71<69? No. push 4. stack=[2,3,4]
i=5, 72:
  69<72, pop 4, result[4]=5-4=1
  71<72, pop 3, result[3]=5-3=2
  75<72? No. push 5. stack=[2,5]
i=6, 76:
  72<76, pop 5, result[5]=6-5=1
  75<76, pop 2, result[2]=6-2=4
  push 6. stack=[6]
i=7, 73: 76<73? No. push 7. stack=[6,7]

End. stack=[6,7] (still unresolved but at end)

Result: [1, 1, 4, 2, 1, 1, 0, 0] ✓
```

## Best Answer to Memorize

```python
def dailyTemperatures(temps):
    n = len(temps)
    result = [0] * n
    stack = []

    for i, temp in enumerate(temps):
        while stack and temps[stack[-1]] < temp:
            prev_idx = stack.pop()
            result[prev_idx] = i - prev_idx
        stack.append(i)

    return result
```

**11 lines. O(n) time. Clean. Interview-ready!**

## Key Insights

### Why Monotonic DECREASING Stack?
> "We want to find the NEXT GREATER for each element.
> A decreasing stack means the top is the SMALLEST unprocessed.
> When we see a bigger value, it can 'resolve' the smaller values above it."

### Why Use INDICES not Temperatures?
> "We need to compute DISTANCE = i - prev_idx.
> Storing indices lets us directly look up temps and compute distance."
> "Plus, after the loop, indices left in stack just stay 0 (default)."

### Why Strict Less Than (not <=)?
> "If temps[stack[-1]] == temp, the previous day is NOT warmer.
> We only pop on strictly less than. Equal temperatures stay 'unresolved'."

## Test Cases

| temps | Expected | Why |
|-------|----------|-----|
| [73, 74, 75, 71, 69, 72, 76, 73] | [1, 1, 4, 2, 1, 1, 0, 0] | Standard example |
| [30, 40, 50, 60] | [1, 1, 1, 0] | Increasing |
| [90, 60, 30] | [0, 0, 0] | Decreasing |
| [30, 30, 30, 30] | [0, 0, 0, 0] | All same (no strictly warmer) |
| [50, 40, 30, 60] | [3, 2, 1, 0] | Mostly dec, then jump |
| [34, 33, 32, 31, 30, 30, 31, 32, 33, 34] | [0, 8, 6, 4, 2, 1, 1, 1, 1, 0] | Stepped |

## Common Pitfalls

1. **Using <= instead of <**: Equal temps get resolved as 'warmer' incorrectly
2. **Storing temps not indices**: Can't compute distance
3. **Forgetting to check stack**: IndexError on empty stack
4. **Not initializing result**: Default 0s matter for unresolved days

## Why This Problem Matters

> "Tests:
> 1. Monotonic stack pattern (CRUCIAL - many problems use this)
> 2. 'Next greater element' family of problems
> 3. O(n) optimization insight
> 4. Edge cases (equal temps, no warmer)
> 5. Linear scan with stack-based backtracking"
