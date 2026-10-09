"""Longest Common Prefix — longest shared prefix of a list of strings.

Time:  O(n · k) where n is len(strs) and k is the prefix length
Space: O(1)
"""


def solve_longest_common_prefix(strs):
    """Return the longest common prefix string.

    >>> solve_longest_common_prefix(["flower", "flow", "flight"])
    'fl'
    """
    if not strs:
        return ""
    # Use the first string as the candidate prefix; shrink it as needed.
    prefix = strs[0]
    for s in strs[1:]:
        while not s.startswith(prefix):
            prefix = prefix[:-1]
            if not prefix:
                return ""
    return prefix


if __name__ == "__main__":
    print(solve_longest_common_prefix(["flower", "flow", "flight"]))
