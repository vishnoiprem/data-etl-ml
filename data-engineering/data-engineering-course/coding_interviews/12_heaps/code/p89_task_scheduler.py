"""Task Scheduler — minimum intervals to run all tasks with cooling.

Time:  O(n) where n is the number of unique tasks
Space: O(n)
"""

from collections import Counter
import heapq


def solve_task_scheduler(tasks, cooldown):
    """Return the minimum number of intervals to run all tasks.

    >>> solve_task_scheduler(["A","A","A","B","B","B"], 2)
    8
    """
    counts = Counter(tasks)
    # Max-heap of remaining counts.
    heap = [-c for c in counts.values()]
    heapq.heapify(heap)
    time = 0
    queue = []  # (time_when_available, -remaining_count)
    while heap or queue:
        time += 1
        if heap:
            count = heapq.heappop(heap) + 1  # negate back
            if count != 0:
                queue.append((time + cooldown, count))
        if queue and queue[0][0] == time:
            heapq.heappush(heap, queue.pop(0)[1])
    return time


if __name__ == "__main__":
    print(solve_task_scheduler(["A", "A", "A", "B", "B", "B"], 2))
