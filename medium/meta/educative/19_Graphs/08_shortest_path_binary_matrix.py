"""
SHORTEST PATH IN BINARY MATRIX — LeetCode 1091
=============================================
Given an n × n binary grid, find the shortest CLEAR path from
top-left (0,0) to bottom-right (n-1,n-1). A clear path moves in
8 directions. Return -1 if no path exists.

This is a BFS problem because every move has equal cost (1).
The only twist vs. ordinary BFS is the 8-neighbour stencil.
"""

from collections import deque
from typing import List


def shortest_path_binary_matrix(grid: List[List[int]]) -> int:
    n = len(grid)
    if grid[0][0] or grid[n-1][n-1]:    # start or end blocked
        return -1
    if n == 1:                          # single cell, already at goal
        return 1

    dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    q = deque([(0, 0, 1)])              # (r, c, path length)
    grid[0][0] = 1                      # mark visited by flipping to 1

    while q:
        r, c, d = q.popleft()
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and grid[nr][nc] == 0:
                if nr == nc == n - 1:
                    return d + 1
                grid[nr][nc] = 1        # visited
                q.append((nr, nc, d + 1))
    return -1


if __name__ == "__main__":
    print(shortest_path_binary_matrix(
        [[0,1],[1,0]]))                                 # 2
    print(shortest_path_binary_matrix(
        [[0,0,0],[1,1,0],[1,1,0]]))                     # -1
    print(shortest_path_binary_matrix([[0]]))           # 1
