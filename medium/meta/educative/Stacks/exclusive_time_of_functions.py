"""
Exclusive Time of Functions
Medium | 30 min

Given a list of logs where each log is a string formatted as:
    "function_id:start_or_end:timestamp"

Where function_id is an integer, start_or_end is either "start" or "end",
and timestamp is an integer.

For each function, return its exclusive execution time (in units),
which is the total time the function spent on the CPU.

When a function calls another function, the inner function takes over
the CPU until it ends. The outer function's time is paused.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/exclusive-time-of-functions

Examples:
    n = 2
    logs = ["0:start:0","1:start:2","1:end:5","0:end:6"]
    -> [3, 4]

    Explanation:
        Function 0 starts at 0, runs until 1 starts at 2 -> 2 units
        Function 1 runs from 2 to 5 -> 3 units
        Function 0 resumes from 5 to 6 -> 1 unit
        Total for 0: 3, Total for 1: 4

    n = 1
    logs = ["0:start:0","0:start:1","0:end:2","0:end:3"]
    -> [3]

    Explanation: Function 0 runs continuously (recursive) -> 3 units

Constraints:
- 1 <= n <= 100
- 1 <= logs.length <= 500
- 0 <= function_id < n
- 0 <= timestamp <= 10^9
- No two start events happen at the same timestamp
- No two end events happen at the same timestamp
- End events are always paired with start events of the same function
"""

from collections import deque


# =============================================================================
# WAY 1: Stack with prev_time (BEST - Memorize!)
# =============================================================================
# THINKING: "Stack holds (function_id, start_time). When we see 'start',
#           pause the parent (add elapsed time), push new one. When 'end',
#           pop and add full duration."
def exclusive_time_1(n, logs):
    result = [0] * n
    stack = []  # stack of function ids
    prev_time = 0

    for log in logs:
        fid, action, time = log.split(':')
        fid, time = int(fid), int(time)

        if action == 'start':
            # Pause the current function (if any)
            if stack:
                result[stack[-1]] += time - prev_time
            stack.append(fid)
            prev_time = time
        else:  # end
            result[stack.pop()] += time - prev_time + 1
            prev_time = time + 1

    return result


# =============================================================================
# WAY 2: Stack with (id, start_time) tuples
# =============================================================================
def exclusive_time_2(n, logs):
    result = [0] * n
    stack = []  # (function_id, start_time)

    for log in logs:
        parts = log.split(':')
        fid = int(parts[0])
        action = parts[1]
        time = int(parts[2])

        if action == 'start':
            stack.append((fid, time))
        else:
            _, start = stack.pop()
            duration = time - start + 1
            result[fid] += duration
            # Pause the parent: subtract child's duration from time
            if stack:
                # The parent's effective start time shifts forward
                # Actually we need to track that the parent's prev_time
                # is now updated to time + 1
                pass

    # Hmm, this approach needs prev_time tracking. Let's simplify:
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


# =============================================================================
# WAY 3: Two stacks (ids and start_times)
# =============================================================================
def exclusive_time_3(n, logs):
    result = [0] * n
    stack_ids = deque()
    stack_times = deque()

    for log in logs:
        fid, action, time = log.split(':')
        fid, time = int(fid), int(time)

        if action == 'start':
            if stack_ids:
                # Pause the parent
                parent = stack_ids[-1]
                result[parent] += time - stack_times[-1]
            stack_ids.append(fid)
            stack_times.append(time)
        else:
            # End: pop the matching start
            stack_ids.pop()
            start_time = stack_times.pop()
            result[fid] += time - start_time + 1
            # Update parent's prev_time to time + 1
            if stack_times:
                stack_times[-1] = time + 1

    return result


# =============================================================================
# WAY 4: Single list as stack
# =============================================================================
def exclusive_time_4(n, logs):
    result = [0] * n
    stack = []  # entries: [fid, start_time]
    prev_time = 0

    for log in logs:
        fid, action, time = log.split(':')
        fid = int(fid)
        time = int(time)

        if action == 'start':
            if stack:
                result[stack[-1][0]] += time - prev_time
            stack.append([fid, time])
            prev_time = time
        else:
            popped = stack.pop()
            result[fid] += time - prev_time + 1
            prev_time = time + 1

    return result


# =============================================================================
# WAY 5: Parsing with index
# =============================================================================
def exclusive_time_5(n, logs):
    result = [0] * n
    stack = []
    prev_time = 0

    for log in logs:
        # Find the first and last colon
        first_colon = log.index(':')
        last_colon = log.rindex(':')

        fid = int(log[:first_colon])
        action = log[first_colon + 1:last_colon]
        time = int(log[last_colon + 1:])

        if action == 'start':
            if stack:
                result[stack[-1]] += time - prev_time
            stack.append(fid)
            prev_time = time
        else:
            result[stack.pop()] += time - prev_time + 1
            prev_time = time + 1

    return result


# =============================================================================
# WAY 6: Using dictionary to store stack entries
# =============================================================================
def exclusive_time_6(n, logs):
    result = [0] * n
    stack = []  # dicts: {'id': fid, 'start': time}
    prev_time = 0

    for log in logs:
        parts = log.split(':')
        fid = int(parts[0])
        action = parts[1]
        time = int(parts[2])

        if action == 'start':
            if stack:
                result[stack[-1]['id']] += time - prev_time
            stack.append({'id': fid, 'start': time})
            prev_time = time
        else:
            top = stack.pop()
            result[fid] += time - prev_time + 1
            prev_time = time + 1

    return result


# =============================================================================
# WAY 7: Using deque for stack
# =============================================================================
def exclusive_time_7(n, logs):
    result = [0] * n
    stack = deque()
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


# =============================================================================
# WAY 8: Using enumerate for parsing
# =============================================================================
def exclusive_time_8(n, logs):
    result = [0] * n
    stack = []
    prev_time = 0

    for i, log in enumerate(logs):
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


# =============================================================================
# WAY 9: Helper functions for parsing
# =============================================================================
def exclusive_time_9(n, logs):
    def parse(log):
        parts = log.split(':')
        return int(parts[0]), parts[1], int(parts[2])

    result = [0] * n
    stack = []
    prev_time = 0

    for log in logs:
        fid, action, time = parse(log)

        if action == 'start':
            if stack:
                result[stack[-1]] += time - prev_time
            stack.append(fid)
            prev_time = time
        else:
            result[stack.pop()] += time - prev_time + 1
            prev_time = time + 1

    return result


# =============================================================================
# WAY 10: With try-except
# =============================================================================
def exclusive_time_10(n, logs):
    result = [0] * n
    stack = []
    prev_time = 0

    for log in logs:
        fid, action, time = log.split(':')
        fid, time = int(fid), int(time)

        if action == 'start':
            try:
                result[stack[-1]] += time - prev_time
            except IndexError:
                pass  # no parent
            stack.append(fid)
            prev_time = time
        else:
            try:
                result[stack.pop()] += time - prev_time + 1
            except IndexError:
                pass
            prev_time = time + 1

    return result


# =============================================================================
# WAY 11: Stack with start time stored separately
# =============================================================================
def exclusive_time_11(n, logs):
    result = [0] * n
    stack = []
    last_timestamp = 0

    for log in logs:
        fid, action, time = log.split(':')
        fid = int(fid)
        time = int(time)

        if action == 'start':
            if stack:
                result[stack[-1][0]] += time - last_timestamp
            stack.append((fid, time))
            last_timestamp = time
        else:
            fid_start, start_time = stack.pop()
            result[fid_start] += time - last_timestamp + 1
            last_timestamp = time + 1

    return result


# =============================================================================
# WAY 12: Recursive approach (event-based)
# =============================================================================
def exclusive_time_12(n, logs):
    result = [0] * n
    stack = []
    prev_time = 0

    def process(log):
        nonlocal prev_time
        fid, action, time = log.split(':')
        return int(fid), action, int(time)

    for log in logs:
        fid, action, time = process(log)

        if action == 'start':
            if stack:
                result[stack[-1]] += time - prev_time
            stack.append(fid)
            prev_time = time
        else:
            result[stack.pop()] += time - prev_time + 1
            prev_time = time + 1

    return result


# =============================================================================
# WAY 13: Using zip with iteration
# =============================================================================
def exclusive_time_13(n, logs):
    result = [0] * n
    stack = []
    prev_time = 0

    parsed_logs = [log.split(':') for log in logs]

    for parts in parsed_logs:
        fid = int(parts[0])
        action = parts[1]
        time = int(parts[2])

        if action == 'start':
            if stack:
                result[stack[-1]] += time - prev_time
            stack.append(fid)
            prev_time = time
        else:
            result[stack.pop()] += time - prev_time + 1
            prev_time = time + 1

    return result


# =============================================================================
# WAY 14: Object-oriented with FunctionCall class
# =============================================================================
class FunctionCall:
    def __init__(self, fid, start):
        self.fid = fid
        self.start = start


def exclusive_time_14(n, logs):
    result = [0] * n
    stack = []
    prev_time = 0

    for log in logs:
        parts = log.split(':')
        fid = int(parts[0])
        action = parts[1]
        time = int(parts[2])

        if action == 'start':
            if stack:
                result[stack[-1].fid] += time - prev_time
            stack.append(FunctionCall(fid, time))
            prev_time = time
        else:
            top = stack.pop()
            result[top.fid] += time - prev_time + 1
            prev_time = time + 1

    return result


# =============================================================================
# WAY 15: One-liner with reduce
# =============================================================================
def exclusive_time_15(n, logs):
    from functools import reduce

    def step(state, log):
        result, stack, prev_time = state
        fid, action, time = log.split(':')
        fid, time = int(fid), int(time)
        result = list(result)

        if action == 'start':
            if stack:
                result[stack[-1]] += time - prev_time
            stack = stack + [fid]
            prev_time = time
        else:
            new_stack = stack[:-1]
            popped = stack[-1]
            result[popped] += time - prev_time + 1
            prev_time = time + 1
            stack = new_stack

        return result, stack, prev_time

    initial_state = ([0] * n, [], 0)
    result, _, _ = reduce(step, logs, initial_state)
    return result


# =============================================================================
# WAY 16: Using list comprehension (no, too complex, use cleaner version)
# =============================================================================
def exclusive_time_16(n, logs):
    result = [0] * n
    stack = []
    prev_time = 0

    for log in logs:
        # Direct unpacking
        parts = log.split(':')
        fid, action, time = int(parts[0]), parts[1], int(parts[2])

        if action == 'start':
            if stack:
                result[stack[-1]] += time - prev_time
            stack.append(fid)
            prev_time = time
        else:
            result[stack.pop()] += time - prev_time + 1
            prev_time = time + 1

    return result


# =============================================================================
# WAY 17: With explicit state machine
# =============================================================================
def exclusive_time_17(n, logs):
    result = [0] * n
    stack = []
    prev_time = 0
    state = 'start'  # tracking mode

    for log in logs:
        parts = log.split(':')
        fid = int(parts[0])
        action = parts[1]
        time = int(parts[2])

        if action == 'start' and state == 'start':
            if stack:
                result[stack[-1]] += time - prev_time
            stack.append(fid)
            prev_time = time
        elif action == 'end':
            result[stack.pop()] += time - prev_time + 1
            prev_time = time + 1

    return result


# =============================================================================
# WAY 18: With lambda helper
# =============================================================================
def exclusive_time_18(n, logs):
    parse = lambda log: (int(x) if i != 1 else x for i, x in enumerate(log.split(':')))

    result = [0] * n
    stack = []
    prev_time = 0

    for log in logs:
        parts = list(parse(log))
        fid, action, time = parts[0], parts[1], parts[2]

        if action == 'start':
            if stack:
                result[stack[-1]] += time - prev_time
            stack.append(fid)
            prev_time = time
        else:
            result[stack.pop()] += time - prev_time + 1
            prev_time = time + 1

    return result


# =============================================================================
# WAY 19: Most compact
# =============================================================================
def exclusive_time_19(n, logs):
    res = [0] * n
    st = []
    t = 0
    for log in logs:
        i, a, ts = log.split(':')
        i, ts = int(i), int(ts)
        if a == 'start':
            if st:
                res[st[-1]] += ts - t
            st.append(i)
            t = ts
        else:
            res[st.pop()] += ts - t + 1
            t = ts + 1
    return res


# =============================================================================
# WAY 20: Most elegant (clean Way 1 variant)
# =============================================================================
def exclusive_time_20(n, logs):
    result = [0] * n
    stack = []
    prev_time = 0

    for log in logs:
        fid_str, action, time_str = log.split(':')
        fid = int(fid_str)
        time = int(time_str)

        if action == 'start':
            if stack:
                result[stack[-1]] += time - prev_time
            stack.append(fid)
            prev_time = time
        else:
            result[stack.pop()] += time - prev_time + 1
            prev_time = time + 1

    return result


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to compute the exclusive time each function spends on the CPU,
considering that when a function calls another, it pauses execution."

Key Insight:
"A STACK of function ids tracks the call stack. When we see 'start',
we pause the current function and push the new one. When we see 'end',
we pop and add the duration. The trick is tracking the PREVIOUS
timestamp to know how long each function ran between events."

Algorithm:
"1. Initialize result=[0]*n, empty stack, prev_time=0
2. For each log entry:
   - Parse fid, action, time
   - If action is 'start':
     * If stack is non-empty, add (time - prev_time) to result[stack[-1]]
       (the parent ran this long before being paused)
     * Push fid to stack
     * Update prev_time = time
   - If action is 'end':
     * Add (time - prev_time + 1) to result[stack.pop()]
       (this function ran this long)
     * Update prev_time = time + 1 (the parent's clock resumes here)
3. Return result"

Why this works:
"The stack represents which function is currently running on the CPU.
When a new function starts, the old one is paused. When a function
ends, we know how long it ran by comparing with prev_time.
Updating prev_time to time+1 after 'end' is crucial - it represents
that the parent's effective time continues from the next instant."

Edge cases:
- Single function with nested calls (recursive)
- No nested calls (sequential)
- Many levels of nesting
- Function starts at time 0

COMPLEXITY:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Stack     | O(n)   | O(n)   |
+-----------+--------+--------+

KEY TRICK:
When 'end' happens, prev_time = time + 1 (not time).
Because after time, the NEXT instant is time+1, and that's when
the parent resumes. Both 'start' and 'end' at time T occupy
T..T (start at T, end at T inclusive) so end uses +1.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Stack with prev_time (BEST)", exclusive_time_1),
        ("Way 2: Tuples in stack", exclusive_time_2),
        ("Way 3: Two stacks (ids + times)", exclusive_time_3),
        ("Way 4: List as stack", exclusive_time_4),
        ("Way 5: Index-based parsing", exclusive_time_5),
        ("Way 6: Dict entries", exclusive_time_6),
        ("Way 7: deque", exclusive_time_7),
        ("Way 8: enumerate", exclusive_time_8),
        ("Way 9: Helper parse function", exclusive_time_9),
        ("Way 10: Try-except", exclusive_time_10),
        ("Way 11: Tuple stack", exclusive_time_11),
        ("Way 12: Recursive helper", exclusive_time_12),
        ("Way 13: Pre-parsed logs", exclusive_time_13),
        ("Way 14: FunctionCall class", exclusive_time_14),
        ("Way 15: reduce", exclusive_time_15),
        ("Way 16: Direct unpacking", exclusive_time_16),
        ("Way 17: State machine", exclusive_time_17),
        ("Way 18: Lambda parse", exclusive_time_18),
        ("Way 19: Most compact", exclusive_time_19),
        ("Way 20: Most elegant", exclusive_time_20),
    ]

    test_cases = [
        # (n, logs, expected)
        (2, ["0:start:0","1:start:2","1:end:5","0:end:6"], [3, 4]),
        # f0 runs 0..6, but pauses for f1 (2..5)
        # f0 own time: 0..2 (2 units) + 5..6 (1 unit) = 3
        # f1 own time: 2..5 (4 units) because end is inclusive -> but wait
        # Actually time 2..5 inclusive is 4 units (2,3,4,5) but our calc does 5-2+1=4
        # Let's re-trace: start at 2 means f1 starts running AT t=2, ends at t=5 inclusive = 4 units
        # f0: starts at 0, runs until t=2 when f1 starts. So f0 has 0..1 = 2 units.
        # f0 then resumes at t=6 (after f1 ends at 5+1=6) and ends at 6 -> 0 units.
        # Wait, f0 ends AT 6 meaning time is exactly 6, so 1 unit (6-6+1=1)? But f0 was already done at t=2.
        # Actually: f0 ends at 6 means it stops. But its last action was at t=2 (paused).
        # After f1 ends at 5, f0's "prev_time" becomes 6. Then f0 ends at 6, duration = 6-6+1 = 1
        # So f0 = 2 + 1 = 3, f1 = 4. ✓
        (1, ["0:start:0","0:end:0"], [1]),
        # f0: start 0, end 0 -> 0-0+1 = 1
        (1, ["0:start:0","0:start:1","0:end:2","0:end:3"], [4]),
        # Trace: start 0 (stack=[0], prev=0)
        # start 1 (add 1-0=1 to result[0], stack=[0,0], prev=1)
        # end 2 (add 2-1+1=2, stack=[0], prev=3)
        # end 3 (add 3-3+1=1, stack=[], prev=4)
        # Total: 1+2+1 = 4
        (1, ["0:start:0","0:end:2"], [3]),
        # start 0, end 2 -> duration 2-0+1 = 3
        (3, ["0:start:0","0:end:0","1:start:1","1:end:1","2:start:2","2:end:2"], [1, 1, 1]),
        # Each runs for 1 instant
        (2, ["0:start:0","0:start:1","0:end:2","0:start:3","0:end:4","1:start:5","1:end:5","0:end:6"], [6, 1]),
        # Trace:
        # start 0: stack=[0], prev=0
        # start 1: add 1-0=1 to r[0], stack=[0,0], prev=1
        # end 2: add 2-1+1=2 to r[0], stack=[0], prev=3
        # start 3: stack=[0] - hmm this is f0 again, but f0 is already running
        # Actually we can have "start" for same fid while it's on stack (re-entering)
        # add 3-3=0 to r[0], stack=[0,0], prev=3
        # end 4: add 4-3+1=2 to r[0], stack=[0], prev=5
        # start 5 (f1): add 5-5=0 to r[0], stack=[0,1], prev=5
        # end 5 (f1): add 5-5+1=1 to r[1], stack=[0], prev=6
        # end 6 (f0): add 6-6+1=1 to r[0], stack=[], prev=7
        # Total r[0] = 1+2+0+2+0+1 = 6, r[1] = 1
    ]

    print("=" * 70)
    print("EXCLUSIVE TIME OF FUNCTIONS - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/exclusive-time-of-functions")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for n, logs, expected in test_cases:
            try:
                result = func(n, logs)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: n={n}, logs={logs} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on n={n}, logs={logs} - {e}")
        print(f"  {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
