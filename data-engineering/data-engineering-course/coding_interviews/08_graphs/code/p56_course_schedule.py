"""Course Schedule — can you finish all courses given prerequisites?

Time:  O(V + E) — topological sort via Kahn's algorithm
Space: O(V + E) — adjacency list + in-degree map
"""

from collections import defaultdict, deque


def solve_course_schedule(num_courses, prerequisites):
    """Return True if all courses can be finished.

    >>> solve_course_schedule(2, [[1, 0]])
    True
    >>> solve_course_schedule(2, [[1, 0], [0, 1]])
    False
    """
    graph = defaultdict(list)
    in_degree = [0] * num_courses
    for dest, src in prerequisites:
        graph[src].append(dest)
        in_degree[dest] += 1
    queue = deque([c for c in range(num_courses) if in_degree[c] == 0])
    taken = 0
    while queue:
        course = queue.popleft()
        taken += 1
        for nxt in graph[course]:
            in_degree[nxt] -= 1
            if in_degree[nxt] == 0:
                queue.append(nxt)
    return taken == num_courses


if __name__ == "__main__":
    print(solve_course_schedule(2, [[1, 0]]))
    print(solve_course_schedule(2, [[1, 0], [0, 1]]))
