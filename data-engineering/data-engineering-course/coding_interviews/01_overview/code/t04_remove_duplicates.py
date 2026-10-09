"""Remove duplicate characters from a string, preserving first occurrence.

Time:  O(n) — single pass with a set
Space: O(n) — output + set
"""


def solve_remove_duplicates(s):
    """Return a new string with each character appearing at most once.

    >>> solve_remove_duplicates("programming")
    'progamin'
    """
    seen = set()
    out_chars = []
    for ch in s:
        if ch in seen:
            continue
        seen.add(ch)
        out_chars.append(ch)
    return "".join(out_chars)


if __name__ == "__main__":
    sample = "programming"
    print(f"input:  {sample!r}")
    print(f"output: {solve_remove_duplicates(sample)!r}")
