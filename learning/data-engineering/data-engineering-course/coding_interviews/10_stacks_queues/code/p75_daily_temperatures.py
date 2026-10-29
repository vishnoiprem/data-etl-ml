"""Daily Temperatures — next-warmer-day distance for each day.

Time:  O(n) — monotonic stack
Space: O(n)
"""


def solve_daily_temperatures(temps):
    """Return days-until-warmer for each day (0 if none).

    >>> solve_daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73])
    [1, 1, 4, 2, 1, 1, 0, 0]
    """
    answer = [0] * len(temps)
    stack = []  # indices of days with decreasing temps
    for i, t in enumerate(temps):
        while stack and temps[stack[-1]] < t:
            prev = stack.pop()
            answer[prev] = i - prev
        stack.append(i)
    return answer


if __name__ == "__main__":
    print(solve_daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73]))
