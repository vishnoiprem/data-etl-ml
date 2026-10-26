"""String to Integer (atoi) — parse with overflow clamping.

Time:  O(n)
Space: O(1)
"""


def solve_atoi(s):
    """Convert ``s`` to a 32-bit signed int, clamping on overflow.

    >>> solve_atoi("   -42")
    -42
    """
    INT_MIN, INT_MAX = -2**31, 2**31 - 1
    i, n = 0, len(s)
    # Skip leading whitespace.
    while i < n and s[i] == " ":
        i += 1
    # Optional sign.
    sign = 1
    if i < n and s[i] in ("+", "-"):
        sign = -1 if s[i] == "-" else 1
        i += 1
    # Parse digits.
    result = 0
    while i < n and s[i].isdigit():
        result = result * 10 + int(s[i])
        # Clamp early.
        if sign * result < INT_MIN:
            return INT_MIN
        if sign * result > INT_MAX:
            return INT_MAX
        i += 1
    return sign * result


if __name__ == "__main__":
    print(solve_atoi("   -42"))
