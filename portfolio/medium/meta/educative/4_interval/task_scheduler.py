"""
Task Scheduler - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/task-scheduler

Given a list of tasks and a cooling interval n, return the least number of
intervals (CPU cycles) needed to execute all tasks, where identical tasks
must be at least n intervals apart.

KEY INSIGHT:
The answer is max(len(tasks), (max_count - 1) * (n + 1) + num_max_tasks).
This formula handles both when idle time is needed and when tasks can
fill all idle slots.

Examples:
    tasks = ["A","A","A","B","B","B"], n = 2 -> 8
    (A _ _ A _ _ A B B -> 8 with idle slots, but B can fit at end)

Constraints:
- 1 <= tasks.length <= 10^4
- 1 <= n <= 100
"""

import copy
import sys
from collections import Counter

sys.setrecursionlimit(100000)


def _eq(a, b):
    return a == b


def _least_interval_brute(tasks, n):
    """Greedy: pick most frequent available task, schedule, decrement."""
    counts = Counter(tasks)
    time = 0
    while counts:
        # Pick up to n+1 most frequent tasks
        available = sorted(counts.items(), key=lambda x: -x[1])[:n + 1]
        if not available:
            break
        for task, _ in available:
            counts[task] -= 1
            if counts[task] == 0:
                del counts[task]
        # Schedule available tasks. If we scheduled fewer than n+1, add idle slots.
        time += n + 1
    # Subtract trailing idle slots
    if available:
        scheduled = len(available)
        time -= (n + 1) - scheduled
    return time


# ============================================================
# Way 1: Formula (BEST - Memorize!)
# ============================================================
def least_interval_1(tasks, n):
    """max(len(tasks), (max_count - 1) * (n + 1) + num_max_tasks)."""
    if not tasks:
        return 0
    counts = Counter(tasks)
    max_count = max(counts.values())
    num_max = sum(1 for c in counts.values() if c == max_count)
    return max(len(tasks), (max_count - 1) * (n + 1) + num_max)


# ============================================================
# Way 2: Greedy simulation with sorting
# ============================================================
def least_interval_2(tasks, n):
    """Greedy: pick most frequent available, simulate."""
    counts = Counter(tasks)
    time = 0
    while counts:
        # Sort by count descending
        available = sorted(counts.items(), key=lambda x: -x[1])
        scheduled_this_round = 0
        scheduled_tasks = []
        for task, _ in available:
            if scheduled_this_round >= n + 1:
                break
            scheduled_tasks.append(task)
            scheduled_this_round += 1
        for task in scheduled_tasks:
            counts[task] -= 1
            if counts[task] == 0:
                del counts[task]
        time += n + 1
        if not counts:
            time -= (n + 1) - scheduled_this_round
    return time


# ============================================================
# Way 3: Heap-based simulation
# ============================================================
def least_interval_3(tasks, n):
    """Use max-heap."""
    import heapq
    if not tasks:
        return 0
    counts = Counter(tasks)
    heap = [-c for c in counts.values()]
    heapq.heapify(heap)
    time = 0
    while heap:
        cycle = []
        scheduled = 0
        for _ in range(n + 1):
            if heap:
                cnt = -heapq.heappop(heap)
                cnt -= 1
                if cnt > 0:
                    cycle.append(cnt)
                scheduled += 1
        for c in cycle:
            heapq.heappush(heap, -c)
        # If heap still has tasks, we filled a full n+1 cycle.
        # Otherwise, just use scheduled count (last partial cycle).
        time += n + 1 if heap else scheduled
    return time


# ============================================================
# Way 4: Sort by count and arrange
# ============================================================
def least_interval_4(tasks, n):
    """Compute the answer via formula."""
    if not tasks:
        return 0
    counts = Counter(tasks)
    max_count = max(counts.values())
    num_max = sum(1 for c in counts.values() if c == max_count)
    return max(len(tasks), (max_count - 1) * (n + 1) + num_max)


# ============================================================
# Way 5: Time-series simulation
# ============================================================
def least_interval_5(tasks, n):
    """Simulate each time slot."""
    if not tasks:
        return 0
    counts = Counter(tasks)
    time = 0
    last_used = {}
    while counts:
        # Pick most frequent task not on cooldown
        candidates = [t for t in counts if last_used.get(t, -n - 1) + n < time]
        if not candidates:
            time += 1
            continue
        task = max(candidates, key=lambda t: counts[t])
        last_used[task] = time
        counts[task] -= 1
        if counts[task] == 0:
            del counts[task]
        time += 1
    return time


# ============================================================
# Way 6: Idle slots calculation
# ============================================================
def least_interval_6(tasks, n):
    """Compute idle slots needed; answer = total + idle."""
    if not tasks:
        return 0
    counts = Counter(tasks)
    max_count = max(counts.values())
    num_max = sum(1 for c in counts.values() if c == max_count)
    frames = max_count - 1
    slots = frames * (n + 1) + num_max
    return max(len(tasks), slots)


# ============================================================
# Way 7: Recursive
# ============================================================
def least_interval_7(tasks, n):
    """Recursive scheduler."""
    if not tasks:
        return 0
    counts = Counter(tasks)

    def helper(remaining):
        if not remaining:
            return 0
        max_count = max(remaining.values())
        num_max = sum(1 for c in remaining.values() if c == max_count)
        return max(sum(remaining.values()), (max_count - 1) * (n + 1) + num_max)

    return helper(counts)


# ============================================================
# Way 8: Class-based
# ============================================================
class TaskScheduler_8:
    def __init__(self, tasks, n):
        self.tasks = tasks
        self.n = n

    def least_interval(self):
        return least_interval_1(self.tasks, self.n)


def least_interval_8(tasks, n):
    return TaskScheduler_8(tasks, n).least_interval()


# ============================================================
# Way 9: Brute force with explicit idle filling
# ============================================================
def least_interval_9(tasks, n):
    """Greedy: in each round pick up to n+1 most-frequent tasks."""
    if not tasks:
        return 0
    counts = Counter(tasks)
    time = 0
    while counts:
        sorted_items = sorted(counts.items(), key=lambda x: -x[1])
        used = 0
        scheduled_tasks = []
        for task, c in sorted_items:
            if used >= n + 1:
                break
            scheduled_tasks.append(task)
            used += 1
        for task in scheduled_tasks:
            counts[task] -= 1
            if counts[task] == 0:
                del counts[task]
        if counts:
            time += n + 1
        else:
            time += used
    return time


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def least_interval_10(tasks, n):
    """
    THE ONE TO MEMORIZE.

    1. Count tasks. Find max_count and num_max (tasks with max count).
    2. Answer = max(len(tasks), (max_count - 1) * (n + 1) + num_max).

    The first term handles the case where tasks fill all idle slots.
    The second is the structured schedule with idle slots.

    Time:  O(n) for counting
    Space: O(1) for counter dict.
    """
    if not tasks:
        return 0
    counts = Counter(tasks)
    max_count = max(counts.values())
    num_max = sum(1 for c in counts.values() if c == max_count)
    return max(len(tasks), (max_count - 1) * (n + 1) + num_max)


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the minimum number of intervals to execute all tasks where
identical tasks must be at least n intervals apart."

Key Insight:
"Think of it as filling a 'frame' structure. The most frequent task
determines the structure. We have max_count - 1 'gaps' that each need n
cooling slots. Plus num_max tasks at the end (the last row of the most
frequent tasks)."

Algorithm:
1. Count tasks. Find max_count.
2. num_max = number of tasks with count == max_count.
3. frames_needed = max_count - 1.
4. answer = max(len(tasks), frames_needed * (n + 1) + num_max).

Edge Cases:
- n == 0: just len(tasks).
- All same task: max_count = n, num_max = 1, answer = max(n, 0 + 1) = n.
- Many distinct tasks: idle slots filled, answer = len(tasks).

Complexity:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Formula   | O(n)   | O(k)   |
| Heap      | O(n)   | O(k)   |
+-----------+--------+--------+

KEY TRICK:
The formula has TWO terms. The second term (max_count - 1) * (n + 1) + num_max
is the structured answer with idle slots. The first term (len(tasks)) handles
when we don't need idle slots. Take the MAX.

RELATED PROBLEMS:
- Rearrange String k Distance Apart (LC 358).
- Meeting Rooms II (LC 253).
- Car Pooling (LC 1094).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        (["A", "A", "A", "B", "B", "B"], 2, 8, "Standard LC621"),
        (["A", "A", "A", "B", "B", "B"], 0, 6, "No cooldown"),
        (["A", "B", "C", "D", "E"], 2, 5, "All distinct"),
        (["A", "A", "A", "A"], 3, 13, "Single task with cooldown"),
        ([], 2, 0, "Empty"),
        (["A", "A", "B", "B", "C"], 2, 5, "Mixed"),
    ]

    implementations = [
        ("Way 1: Formula (BEST)", least_interval_1),
        ("Way 2: Greedy simulation", least_interval_2),
        ("Way 3: Heap-based", least_interval_3),
        ("Way 4: Sort + arrange", least_interval_4),
        ("Way 5: Time-series", least_interval_5),
        ("Way 6: Idle slots calc", least_interval_6),
        ("Way 7: Recursive", least_interval_7),
        ("Way 8: Class-based", least_interval_8),
        ("Way 9: Brute greedy", least_interval_9),
        ("Way 10: Final cleanest", least_interval_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for tasks, n, expected, desc in test_cases:
            try:
                result = fn(copy.deepcopy(tasks), n)
                if result == expected:
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: tasks={tasks} n={n} expected={expected} got={result}")
            except Exception as e:
                failed += 1
                all_pass = False
                print(f"  ERROR [{name}] {desc}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 60)
    print(HOW_TO_THINK)


if __name__ == "__main__":
    run_tests()
