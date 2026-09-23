"""
FIND CENTER OF STAR GRAPH — LeetCode 1791
========================================
A star graph is a graph in which n−1 edges are incident to a SINGLE
central node and n−1 edges radiate to other nodes (a hub-and-spoke).

Given the edge list, find the centre. O(1) with NO graph construction:

The centre must appear in BOTH endpoints of the FIRST TWO edges —
any other arrangement contradicts the star property.

Proof sketch:
    In a star graph, every edge touches the centre.
    So among edges[0]=(a,b) and edges[1]=(c,d):
        {a,b} ∩ {c,d} must contain the centre.
    The intersection is either 1 element (→ centre) or 2 (impossible
    because two edges sharing two endpoints would be the same edge).
"""

from typing import List


def find_center(edges: List[List[int]]) -> int:
    # Set intersection: choose whichever endpoint appears in edge 1
    return (set(edges[0]) & set(edges[1])).pop()


# Even simpler — the centre has to be in edge 0 too, so:
def find_center_cheeky(edges: List[List[int]]) -> int:
    a, b = edges[0]
    if edges[1].count(a):
        return a
    return b


if __name__ == "__main__":
    print(find_center([[1,2],[2,3],[4,2]]))           # 2
    print(find_center([[1,2],[5,1],[1,3],[1,4]]))     # 1
