"""Meeting Rooms II — minimum number of conference rooms required.

Time:  O(n log n) — sort starts + min-heap on end times
Space: O(n)
"""

import heapq


def solve_meeting_rooms(intervals):
    """Return the minimum number of rooms needed to hold all meetings.

    >>> solve_meeting_rooms([[0,30],[5,10],[15,20]])
    2
    """
    if not intervals:
        return 0
    intervals = sorted(intervals, key=lambda iv: iv[0])
    heap = []  # end times
    for start, end in intervals:
        # Reuse a room whose meeting has ended.
        if heap and heap[0] <= start:
            heapq.heappop(heap)
        heapq.heappush(heap, end)
    return len(heap)


if __name__ == "__main__":
    print(solve_meeting_rooms([[0, 30], [5, 10], [15, 20]]))
