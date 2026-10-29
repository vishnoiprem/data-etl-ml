"""Mock 114 — L5 Google phone screen: longest substring with at most 2 distinct chars."""


def solve_longest_two_distinct(s):
    """Return the length of the longest substring with at most 2 distinct chars.

    Time:  O(n) — sliding window
    Space: O(1) — only a tiny dict of size <= 2.
    """
    if not s:
        return 0
    counts = {}
    left = 0
    best = 0
    for right, ch in enumerate(s):
        counts[ch] = counts.get(ch, 0) + 1
        # Shrink until the window has at most 2 distinct chars again.
        while len(counts) > 2:
            counts[s[left]] -= 1
            if counts[s[left]] == 0:
                del counts[s[left]]
            left += 1
        best = max(best, right - left + 1)
    return best


if __name__ == "__main__":
    print(solve_longest_two_distinct("eceba"))  # 3
    print(solve_longest_two_distinct("ccaabbb"))  # 5
