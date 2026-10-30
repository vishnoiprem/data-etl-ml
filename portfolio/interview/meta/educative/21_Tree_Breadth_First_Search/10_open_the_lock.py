"""
OPEN THE LOCK — LeetCode 752
============================
A lock has 4 wheels, each with digits 0-9. From a starting string
`"0000"`, each turn you can spin any one wheel up or down by 1.
A set of `deadends` are forbidden states. The target is given.
Return the minimum number of turns to reach target, or -1 if impossible.

This is BFS over an IMPLICIT graph.
    • Vertices = 10^4 = 10000 four-digit strings.
    • Edges    = "spin one wheel by ±1" (8 neighbours per vertex).
We don't BUILD the graph — we generate neighbours on the fly.

Pattern: any time the problem describes transformations on a state
("spin one wheel", "flip one bit", "change one character"), think
"BFS over the implicit graph of states".
"""

from collections import deque
from typing import List


def open_lock(deadends: List[str], target: str) -> int:
    start = "0000"
    if start in deadends or target in deadends:
        return -1 if target in deadends else 0

    dead = set(deadends)
    visited = {start}
    q = deque([(start, 0)])
    while q:
        state, turns = q.popleft()
        if state == target:
            return turns
        for i in range(4):
            for d in (-1, 1):
                digit = int(state[i])
                new_digit = (digit + d) % 10         # wrap 9 → 0 and 0 → 9
                new_state = state[:i] + str(new_digit) + state[i+1:]
                if new_state not in visited and new_state not in dead:
                    visited.add(new_state)
                    q.append((new_state, turns + 1))
    return -1


# ---- Bidirectional BFS (faster for huge state spaces) ----
def open_lock_bidirectional(deadends: List[str], target: str) -> int:
    start = "0000"
    dead = set(deadends)
    if start == target:
        return 0 if start not in dead else -1
    if start in dead or target in dead:
        return -1

    def neighbours(s: str):
        for i in range(4):
            for d in (-1, 1):
                nd = (int(s[i]) + d) % 10
                yield s[:i] + str(nd) + s[i+1:]

    # `dist[s]` = number of turns to reach s from `start`.
    # We maintain it for both ends and sum on meeting.
    dist_start, dist_target = {start: 0}, {target: 0}
    front, back = {start}, {target}
    while front and back:
        if front & back:                          # met: sum the two distances
            s = next(iter(front & back))
            return dist_start[s] + dist_target[s]
        # Expand the smaller frontier
        if len(front) > len(back):
            front, back = back, dist_start, dist_target
            dist_start, dist_target = dist_target, dist_start
        nxt = {}
        for s in front:
            for ns in neighbours(s):
                if ns in dead or ns in dist_start:
                    continue
                nxt[ns] = dist_start[s] + 1       # parent pointer + dist
        dist_start.update(nxt)
        front = set(nxt.keys())
    return -1


if __name__ == "__main__":
    print(open_lock(["0201","0101","0102","1212","2002"], "0202"))    # 6
    print(open_lock_bidirectional(["8888"], "0009"))                 # 1
