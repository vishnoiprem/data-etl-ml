# Exclusive Time of Functions - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/exclusive-time-of-functions

## The Problem
```
Given n functions and a list of logs in the format "id:start_or_end:timestamp",
return the EXCLUSIVE execution time of each function.

When function A calls function B:
- A pauses execution
- B takes over the CPU
- B's time is counted only for B
- A's time is counted only when it's actually running

Examples:
    n = 2
    logs = ["0:start:0","1:start:2","1:end:5","0:end:6"]
    -> [3, 4]

    Explanation:
        0 runs 0..2 (2 units), then 1 runs 2..5 (4 units), then 0 runs 5..6 (1 unit)
        Total for 0: 2 + 1 = 3
        Total for 1: 4
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
logs = ["0:start:0","1:start:2","1:end:5","0:end:6"]

Timeline:
  t=0: 0 starts
  t=2: 0 pauses, 1 starts
  t=5: 1 ends, 0 resumes
  t=6: 0 ends

Function 0 actual run time: [0..2) + [5..6) = 2 + 1 = 3 units
Function 1 actual run time: [2..5] = 4 units (inclusive)
```

### Step 2: The Trick
> "Use a STACK to track the call hierarchy.
> - On 'start': pause parent (add elapsed time), push new function
> - On 'end': pop function, add its duration
> - The KEY: prev_time tracks when the last event happened"

### Step 3: Why Stack?
> "LIFO matches the function call stack!
> When function A calls B, B is on top.
> When B ends, control returns to A.
> Stack naturally handles this nesting."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to compute the exclusive CPU time each function spent, accounting for the fact that when a function calls another, it pauses."

**Key Insight:**
> "The trick is to track 'prev_time' - the timestamp of the last event. When I see a 'start', the parent function ran from prev_time to current_time. When I see an 'end', the function ran from prev_time to current_time+1 (inclusive end)."

**Algorithm:**
> "1. Initialize result=[0]*n, empty stack, prev_time=0
> 2. For each log entry:
>    - Parse fid, action, time
>    - If 'start':
>      * If stack non-empty: add (time - prev_time) to result[stack[-1]] (parent ran this long)
>      * Push fid, prev_time = time
>    - If 'end':
>      * Add (time - prev_time + 1) to result[stack.pop()]
>      * prev_time = time + 1 (parent's clock resumes here)
> 3. Return result"

**Why this works:**
> "The stack represents which function is currently on the CPU. When a new function starts, the old one pauses - we record how long it ran. When a function ends, we record how long IT ran. The +1 in 'end' accounts for inclusive timestamps."

**Edge cases:**
- Recursive: same function calls itself (multiple instances in stack)
- Sequential: no nested calls
- Single function: just one log pair
- Deep nesting: many levels on stack

---

## The 20 Implementations (Simple to Complex)

### Way 1: Stack with prev_time (BEST - Memorize!)
```python
def exclusiveTime(n, logs):
    result = [0] * n
    stack = []
    prev_time = 0

    for log in logs:
        fid, action, time = log.split(':')
        fid, time = int(fid), int(time)

        if action == 'start':
            if stack:
                result[stack[-1]] += time - prev_time
            stack.append(fid)
            prev_time = time
        else:  # end
            result[stack.pop()] += time - prev_time + 1
            prev_time = time + 1

    return result
```

### Way 2: Stack with (id, start) tuples
```python
def exclusiveTime(n, logs):
    result = [0] * n
    stack = []
    prev_time = 0

    for log in logs:
        fid, action, time = log.split(':')
        fid, time = int(fid), int(time)

        if action == 'start':
            if stack:
                result[stack[-1][0]] += time - prev_time
            stack.append((fid, time))
            prev_time = time
        else:
            popped_id, _ = stack.pop()
            result[popped_id] += time - prev_time + 1
            prev_time = time + 1

    return result
```

### Way 3: Two parallel stacks
```python
from collections import deque

def exclusiveTime(n, logs):
    result = [0] * n
    stack_ids = deque()
    stack_times = deque()

    for log in logs:
        fid, action, time = log.split(':')
        fid, time = int(fid), int(time)

        if action == 'start':
            if stack_ids:
                result[stack_ids[-1]] += time - stack_times[-1]
            stack_ids.append(fid)
            stack_times.append(time)
        else:
            stack_ids.pop()
            start_time = stack_times.pop()
            result[fid] += time - start_time + 1
            if stack_times:
                stack_times[-1] = time + 1

    return result
```

### Way 4-10: Other variants
- Way 4: List of [id, start_time] sublists
- Way 5: Index-based parsing (avoids split)
- Way 6: Dict entries per stack frame
- Way 7: deque for stack
- Way 8: enumerate for iteration
- Way 9: Helper parse function
- Way 10: try-except for empty stack

### Way 11-15: Functional and class-based
- Way 11: Tuple stack
- Way 12: Recursive helper
- Way 13: Pre-parsed logs
- Way 14: FunctionCall class
- Way 15: reduce-based

### Way 16-20: Compact variants
- Way 16: Direct unpacking
- Way 17: State machine
- Way 18: Lambda parse
- Way 19: Most compact
- Way 20: Most elegant

---

## Decision Tree

```
+------------------+-------------+--------------+
| Scenario         | Best        | Why          |
+------------------+-------------+--------------+
| Cleanest         | Stack+prev  | Standard     |
| Most compact     | Way 19      | Fewest lines |
| OOP              | FunctionCall| Self-doc     |
+------------------+-------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Stack + prev_time | O(L) | O(n) |

where L = number of logs, n = number of functions.

---

## Walkthrough Example

```
n = 2, logs = ["0:start:0","1:start:2","1:end:5","0:end:6"]

Init: result=[0,0], stack=[], prev_time=0

"0:start:0":
  stack empty, no pause
  push 0, stack=[0], prev_time=0
  result=[0,0]

"1:start:2":
  stack non-empty, pause parent
  add 2-0=2 to result[0]=2
  push 1, stack=[0,1], prev_time=2
  result=[2,0]

"1:end:5":
  pop 1, add 5-2+1=4 to result[1]=4
  prev_time=6
  stack=[0]
  result=[2,4]

"0:end:6":
  pop 0, add 6-6+1=1 to result[0]=3
  prev_time=7
  stack=[]
  result=[3,4] ✓
```

```
Recursive example:
n = 1, logs = ["0:start:0","0:start:1","0:end:2","0:end:3"]

Init: result=[0], stack=[], prev=0

"0:start:0":
  stack empty, push 0, prev=0

"0:start:1":
  pause parent (add 1-0=1 to r[0]=1)
  push 0, stack=[0,0], prev=1

"0:end:2":
  pop, add 2-1+1=2 to r[0]=3
  prev=3, stack=[0]

"0:end:3":
  pop, add 3-3+1=1 to r[0]=4
  prev=4, stack=[]

Final: result=[4]
```

## Best Answer to Memorize

```python
def exclusiveTime(n, logs):
    result = [0] * n
    stack = []
    prev_time = 0

    for log in logs:
        fid, action, time = log.split(':')
        fid, time = int(fid), int(time)

        if action == 'start':
            if stack:
                result[stack[-1]] += time - prev_time
            stack.append(fid)
            prev_time = time
        else:
            result[stack.pop()] += time - prev_time + 1
            prev_time = time + 1

    return result
```

**15 lines. O(L) time. Clean. Interview-ready!**

## Key Insights

### Why +1 on End?
> "Timestamps are INCLUSIVE. If a function ends at time 5, it ran at t=5 too.
> So duration from prev_time to time T inclusive = T - prev_time + 1."

### Why prev_time = time + 1 After End?
> "After a function ends at time T, the next instant is T+1.
> The parent resumes at T+1, so prev_time becomes T+1 for the next event."

### Why We Track parent on 'start'?
> "When a new function starts at time T, the previous function was running
> from prev_time to T. We add (T - prev_time) to its result."

## Test Cases

| n | logs | Expected | Why |
|---|------|----------|-----|
| 2 | ["0:start:0","1:start:2","1:end:5","0:end:6"] | [3, 4] | Nested |
| 1 | ["0:start:0","0:end:0"] | [1] | Single |
| 1 | ["0:start:0","0:start:1","0:end:2","0:end:3"] | [4] | Recursive |
| 1 | ["0:start:0","0:end:2"] | [3] | Long |
| 3 | sequential calls | [1,1,1] | Sequential |

## Common Pitfalls

1. **Forgetting +1 on end**: Each function loses 1 unit
2. **Not updating prev_time after end**: Parent's elapsed time is wrong
3. **Not handling empty stack on start**: Crashes on first call
4. **Confusing 'start' with 'begin'**: The log says "start"

## Why Not Hashmap?

> "We need ORDERED access to the most recent function.
> Hashmap is unordered. Stack is perfect for LIFO access.
> The fundamental data structure here IS a stack."

The "exclusive" time computation requires knowing the order of function calls,
which is naturally represented by a stack.
