"""Restore IP Addresses — every way to insert 3 dots.

Time:  O(3^4) — bounded combinatorics
Space: O(4) — recursion stack
"""


def solve_restore_ip_addresses(s):
    """Return every valid IP address we can form from s.

    >>> sorted(solve_restore_ip_addresses("25525511135"))
    ['255.255.11.135', '255.255.111.35']
    """
    out = []

    def backtrack(start, parts):
        if len(parts) == 4:
            if start == len(s):
                out.append(".".join(parts))
            return
        # Each part is 1-3 digits.
        for end in range(start, min(start + 3, len(s))):
            segment = s[start:end + 1]
            # Leading zero not allowed for multi-digit segments.
            if len(segment) > 1 and segment[0] == "0":
                break
            if int(segment) > 255:
                break
            parts.append(segment)
            backtrack(end + 1, parts)
            parts.pop()

    backtrack(0, [])
    return out


if __name__ == "__main__":
    print(solve_restore_ip_addresses("25525511135"))
