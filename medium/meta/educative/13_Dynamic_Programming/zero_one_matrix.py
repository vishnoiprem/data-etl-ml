from collections import deque


def update_matrix(mat):
    """
    For each cell in a binary matrix, return its distance to the nearest 0.
    Multi-source BFS starting from all 0s.
    """
    if not mat or not mat[0]:
        return mat

    m, n = len(mat), len(mat[0])
    dist = [[-1] * n for _ in range(m)]
    queue = deque()

    # Initialize: all 0-cells are sources, distance 0
    for i in range(m):
        for j in range(n):
            if mat[i][j] == 0:
                dist[i][j] = 0
                queue.append((i, j))

    # Multi-source BFS
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    while queue:
        i, j = queue.popleft()
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if (0 <= ni < m and 0 <= nj < n and dist[ni][nj] == -1):
                dist[ni][nj] = dist[i][j] + 1
                queue.append((ni, nj))

    return dist


if __name__ == "__main__":
    # Test cases
    m1 = [
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ]
    expected1 = [
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ]
    print(update_matrix(m1) == expected1)

    m2 = [
        [0, 0, 0],
        [0, 1, 0],
        [1, 1, 1],
    ]
    expected2 = [
        [0, 0, 0],
        [0, 1, 0],
        [1, 2, 1],
    ]
    print(update_matrix(m2) == expected2)

    m3 = [[0]]
    print(update_matrix(m3) == [[0]])
