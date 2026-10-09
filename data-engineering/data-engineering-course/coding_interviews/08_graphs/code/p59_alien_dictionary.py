"""Alien Dictionary — derive character ordering from a sorted alien dictionary.

Time:  O(N · L + U²) where N is the number of words, L the avg length, U unique chars
Space: O(U + E) — graph and in-degree
"""

from collections import defaultdict, deque


def solve_alien_dictionary(words):
    """Return a possible alphabet ordering, or "" if inconsistent.

    >>> solve_alien_dictionary(["wrt","wrf","er","ett","rftt"])
    'wertf'
    """
    # Initialize graph: every distinct character starts with no outgoing edges.
    graph = defaultdict(set)
    in_degree = {c: 0 for w in words for c in w}
    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i + 1]
        # Edge case: w1 starts with w2 but is longer — invalid.
        if len(w1) > len(w2) and w1.startswith(w2):
            return ""
        # First differing character defines an edge.
        for c1, c2 in zip(w1, w2):
            if c1 != c2:
                if c2 not in graph[c1]:
                    graph[c1].add(c2)
                    in_degree[c2] += 1
                break
    # Kahn's algorithm.
    queue = deque([c for c, d in in_degree.items() if d == 0])
    out = []
    while queue:
        c = queue.popleft()
        out.append(c)
        for nxt in graph[c]:
            in_degree[nxt] -= 1
            if in_degree[nxt] == 0:
                queue.append(nxt)
    if len(out) != len(in_degree):
        return ""  # cycle
    return "".join(out)


if __name__ == "__main__":
    print(solve_alien_dictionary(["wrt", "wrf", "er", "ett", "rftt"]))
