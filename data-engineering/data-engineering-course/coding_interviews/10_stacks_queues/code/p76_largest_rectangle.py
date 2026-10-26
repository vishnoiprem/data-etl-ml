"""Largest Rectangle in Histogram.

Time:  O(n) — single pass with a monotonic stack
Space: O(n)
"""


def solve_largest_rectangle(heights):
    """Return the area of the largest rectangle in the histogram.

    >>> solve_largest_rectangle([2, 1, 5, 6, 2, 3])
    10
    """
    # Sentinel heights of 0 flush the stack at the end.
    stack = []  # indices
    best = 0
    for i, h in enumerate(heights + [0]):
        while stack and heights[stack[-1]] > h:
            height = heights[stack.pop()]
            # Width is the current index minus the new stack top, minus 1.
            width = i if not stack else i - stack[-1] - 1
            best = max(best, height * width)
        stack.append(i)
    return best


if __name__ == "__main__":
    print(solve_largest_rectangle([2, 1, 5, 6, 2, 3]))
