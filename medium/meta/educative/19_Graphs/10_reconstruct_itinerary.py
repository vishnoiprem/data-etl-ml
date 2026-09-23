"""
RECONSTRUCT ITINERARY — LeetCode 332
====================================
Given a list of airline tickets [from, to], reconstruct the itinerary
in order. Start at "JFK". Use every ticket exactly once. If multiple
valid itineraries exist, return the LEXICOGRAPHICALLY SMALLEST one.

This is the EULERIAN PATH problem in disguise:
    "Trace every edge exactly once, starting from a specific node."

Algorithm: Hierholzer's algorithm in REVERSE.
    Why reverse? In the lexicographic-smallest-first variant we
    always want to use the smallest lexical neighbour LAST (so it
    remains on our path when we backtrack). Recursing onto the
    smallest first and then appending gives us that ordering for free.

Pattern: any time a problem says "use every edge / vertex exactly
once in a connected graph", your first thought should be Hierholzer or
Hierholzer-with-reverse (the smallest-first variant).
"""

from collections import defaultdict
from typing import List


def find_itinerary(tickets: List[List[str]]) -> List[str]:
    graph = defaultdict(list)             # multiset per node
    for u, v in tickets:
        graph[u].append(v)

    # Sort each adjacency list in REVERSE so we can pop() smallest first.
    for u in graph:
        graph[u].sort(reverse=True)

    route = []

    def dfs(u: str):
        while graph[u]:
            dfs(graph[u].pop())           # consume the smallest ticket
        route.append(u)                   # post-order: append on the way up

    dfs("JFK")
    return route[::-1]                    # reverse the post-order


if __name__ == "__main__":
    t = [["MUC","LHR"],["JFK","MUC"],["SFO","SJC"],["LHR","SFO"]]
    print(find_itinerary(t))
    # ["JFK","MUC","LHR","SFO","SJC"]
