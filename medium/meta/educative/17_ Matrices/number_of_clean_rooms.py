"""
Number of Spaces Cleaning Robot Cleaned
Medium | 30 min

A cleaning robot starts at the top-left corner of the room, facing right.
It moves straight until it either reaches the edge of the room or
encounters an object (1 = obstacle, 0 = empty). When this happens, it
turns 90 degrees clockwise and continues moving.

The robot cleans the starting space and every space it visits.

If it visits a space again while facing the same direction, return
the number of unique spaces it has cleaned.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/number-of-spaces-cleaning-robot-cleaned

Constraints:
- 1 <= m, n <= 100
- room[i][j] is 0 (empty) or 1 (obstacle)

Examples:
    room = [[1,1,1,1,1,0,1,1],
            [1,1,1,1,1,0,1,1],
            [1,0,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1]] -> 33

Key Insight:
- The robot's (position, direction) state is finite (4*m*n states).
- It must eventually repeat a (position, direction) state.
- Once repeated, the robot is in a cycle, so it would visit no new spaces.
- Return the count of unique spaces cleaned BEFORE the first repeat.

Time:  O(m*n) — visits each (position, direction) at most once.
Space: O(m*n) — for visited set.
"""


# =============================================================================
# WAY 1: Simulate with visited set (BEST - Memorize!)
# =============================================================================
def number_of_clean_rooms_1(room):
    """
    Simulate the robot's movement. Track (position, direction) visited.
    When a state repeats, the robot is in a cycle - stop.
    Return count of unique (position only) cleaned spaces.

    When blocked, keep turning 90 degrees clockwise until can move.
    """
    if not room or not room[0]:
        return 0
    m, n = len(room), len(room[0])

    # Direction: 0=right, 1=down, 2=left, 3=up
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    r, c = 0, 0
    direction = 0  # Start facing right

    visited_states = set()
    cleaned = set()

    while (r, c, direction) not in visited_states:
        visited_states.add((r, c, direction))
        cleaned.add((r, c))

        # Keep turning until we can move
        for _ in range(4):
            dr, dc = directions[direction]
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and room[nr][nc] == 0:
                r, c = nr, nc
                break
            direction = (direction + 1) % 4
        else:
            # All 4 directions blocked - robot stuck
            break

    return len(cleaned)


# =============================================================================
# WAY 2: Verbose version with explicit state tracking
# =============================================================================
def number_of_clean_rooms_2(room):
    """More explicit version."""
    if not room or not room[0]:
        return 0
    m, n = len(room), len(room[0])

    RIGHT, DOWN, LEFT, UP = 0, 1, 2, 3
    deltas = {
        RIGHT: (0, 1),
        DOWN: (1, 0),
        LEFT: (0, -1),
        UP: (-1, 0),
    }

    r, c = 0, 0
    direction = RIGHT

    seen_states = set()
    cleaned = set()

    while True:
        state = (r, c, direction)
        if state in seen_states:
            break
        seen_states.add(state)
        cleaned.add((r, c))

        # Keep turning clockwise until we can move
        for _ in range(4):
            dr, dc = deltas[direction]
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and room[nr][nc] == 0:
                r, c = nr, nc
                break
            direction = (direction + 1) % 4
        else:
            break  # All 4 directions blocked

    return len(cleaned)


# =============================================================================
# WAY 3: Using while loop with break on state repeat
# =============================================================================
def number_of_clean_rooms_3(room):
    """Same as Way 1 with slightly different control flow."""
    if not room or not room[0]:
        return 0
    m, n = len(room), len(room[0])

    deltas = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    r, c, d = 0, 0, 0
    visited = {(0, 0, 0)}
    cleaned = {(0, 0)}

    while True:
        # Keep turning until can move
        moved = False
        for _ in range(4):
            dr, dc = deltas[d]
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and room[nr][nc] == 0:
                r, c = nr, nc
                moved = True
                break
            d = (d + 1) % 4
        if not moved:
            break
        if (r, c, d) in visited:
            break
        visited.add((r, c, d))
        cleaned.add((r, c))

    return len(cleaned)


# =============================================================================
# WAY 4: Use a 4D visited array (more efficient than set)
# =============================================================================
def number_of_clean_rooms_4(room):
    """Use 4D array for visited (more memory efficient for dense grids)."""
    if not room or not room[0]:
        return 0
    m, n = len(room), len(room[0])

    visited = [[[False] * 4 for _ in range(n)] for _ in range(m)]
    cleaned = [[False] * n for _ in range(m)]

    deltas = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    r, c, d = 0, 0, 0
    count = 0

    while not visited[r][c][d]:
        visited[r][c][d] = True
        if not cleaned[r][c]:
            cleaned[r][c] = True
            count += 1

        # Keep turning until can move
        moved = False
        for _ in range(4):
            dr, dc = deltas[d]
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and room[nr][nc] == 0:
                r, c = nr, nc
                moved = True
                break
            d = (d + 1) % 4
        if not moved:
            break

    return count


# =============================================================================
# WAY 5: Use bitmask to encode state
# =============================================================================
def number_of_clean_rooms_5(room):
    """Encode state as a single integer (r * 4 * n + c * 4 + d)."""
    if not room or not room[0]:
        return 0
    m, n = len(room), len(room[0])

    deltas = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    r, c, d = 0, 0, 0
    visited = set()
    cleaned = set()

    def state_id(r, c, d):
        return r * 4 * n + c * 4 + d

    while state_id(r, c, d) not in visited:
        visited.add(state_id(r, c, d))
        cleaned.add((r, c))

        moved = False
        for _ in range(4):
            dr, dc = deltas[d]
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and room[nr][nc] == 0:
                r, c = nr, nc
                moved = True
                break
            d = (d + 1) % 4
        if not moved:
            break

    return len(cleaned)


# =============================================================================
# WAY 6: Iterative with helper function
# =============================================================================
def number_of_clean_rooms_6(room):
    """Use helper functions for clarity."""
    if not room or not room[0]:
        return 0
    m, n = len(room), len(room[0])

    def is_blocked(r, c):
        return not (0 <= r < m and 0 <= c < n) or room[r][c] == 1

    deltas = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    r, c, d = 0, 0, 0
    visited = set()
    cleaned = set()

    while (r, c, d) not in visited:
        visited.add((r, c, d))
        cleaned.add((r, c))

        moved = False
        for _ in range(4):
            dr, dc = deltas[d]
            if not is_blocked(r + dr, c + dc):
                r, c = r + dr, c + dc
                moved = True
                break
            d = (d + 1) % 4
        if not moved:
            break

    return len(cleaned)


# =============================================================================
# WAY 7: Simulation with step counter
# =============================================================================
def number_of_clean_rooms_7(room):
    """Add step counter for safety bound (max 4*m*n steps)."""
    if not room or not room[0]:
        return 0
    m, n = len(room), len(room[0])

    deltas = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    r, c, d = 0, 0, 0
    visited = set()
    cleaned = set()
    max_steps = 4 * m * n  # Safety bound

    for _ in range(max_steps):
        if (r, c, d) in visited:
            break
        visited.add((r, c, d))
        cleaned.add((r, c))

        moved = False
        for _ in range(4):
            dr, dc = deltas[d]
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and room[nr][nc] == 0:
                r, c = nr, nc
                moved = True
                break
            d = (d + 1) % 4
        if not moved:
            break

    return len(cleaned)


# =============================================================================
# WAY 8: Class-based simulation
# =============================================================================
class CleaningRobot:
    def __init__(self, room):
        self.room = room
        self.m = len(room)
        self.n = len(room[0]) if room else 0
        self.deltas = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    def is_blocked(self, r, c):
        return not (0 <= r < self.m and 0 <= c < self.n) or self.room[r][c] == 1

    def simulate(self):
        r, c, d = 0, 0, 0
        visited = set()
        cleaned = set()

        while (r, c, d) not in visited:
            visited.add((r, c, d))
            cleaned.add((r, c))

            moved = False
            for _ in range(4):
                dr, dc = self.deltas[d]
                if not self.is_blocked(r + dr, c + dc):
                    r, c = r + dr, c + dc
                    moved = True
                    break
                d = (d + 1) % 4
            if not moved:
                break

        return len(cleaned)


def number_of_clean_rooms_8(room):
    """Class-based simulation."""
    if not room or not room[0]:
        return 0
    return CleaningRobot(room).simulate()


# =============================================================================
# WAY 9: Recursive simulation
# =============================================================================
def number_of_clean_rooms_9(room):
    """Recursive simulation."""
    if not room or not room[0]:
        return 0
    m, n = len(room), len(room[0])

    deltas = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    visited = set()
    cleaned = set()

    def step(r, c, d):
        if (r, c, d) in visited:
            return
        visited.add((r, c, d))
        cleaned.add((r, c))

        for _ in range(4):
            dr, dc = deltas[d]
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and room[nr][nc] == 0:
                step(nr, nc, d)
                return
            d = (d + 1) % 4

    step(0, 0, 0)
    return len(cleaned)


# =============================================================================
# WAY 10: Simulation with separate 'state visited' and 'space visited'
# =============================================================================
def number_of_clean_rooms_10(room):
    """Two separate sets: state visited and space visited."""
    if not room or not room[0]:
        return 0
    m, n = len(room), len(room[0])

    deltas = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    r, c, d = 0, 0, 0
    state_visited = {(0, 0, 0)}
    space_visited = {(0, 0)}

    while True:
        moved = False
        for _ in range(4):
            dr, dc = deltas[d]
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and room[nr][nc] == 0:
                r, c = nr, nc
                moved = True
                break
            d = (d + 1) % 4
        if not moved:
            break

        if (r, c, d) in state_visited:
            break
        state_visited.add((r, c, d))
        space_visited.add((r, c))

    return len(space_visited)


# =============================================================================
# WAY 11: Simulation tracking path
# =============================================================================
def number_of_clean_rooms_11(room):
    """Track full path and use sets for unique cleaned spaces."""
    if not room or not room[0]:
        return 0
    m, n = len(room), len(room[0])

    deltas = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    r, c, d = 0, 0, 0
    state_visited = set()
    path = [(0, 0)]

    while (r, c, d) not in state_visited:
        state_visited.add((r, c, d))

        moved = False
        for _ in range(4):
            dr, dc = deltas[d]
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and room[nr][nc] == 0:
                r, c = nr, nc
                moved = True
                break
            d = (d + 1) % 4
        if not moved:
            break
        path.append((r, c))

    return len(set(path))


# =============================================================================
# WAY 12: Use dict for visited states
# =============================================================================
def number_of_clean_rooms_12(room):
    """Use dict instead of set for visited."""
    if not room or not room[0]:
        return 0
    m, n = len(room), len(room[0])

    deltas = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    r, c, d = 0, 0, 0
    visited = {}
    cleaned = {}

    while True:
        key = (r, c, d)
        if visited.get(key):
            break
        visited[key] = True
        cleaned[(r, c)] = True

        moved = False
        for _ in range(4):
            dr, dc = deltas[d]
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and room[nr][nc] == 0:
                r, c = nr, nc
                moved = True
                break
            d = (d + 1) % 4
        if not moved:
            break

    return len(cleaned)


# =============================================================================
# WAY 13: Use frozen set for state
# =============================================================================
def number_of_clean_rooms_13(room):
    """Use frozenset as state for hashing."""
    if not room or not room[0]:
        return 0
    m, n = len(room), len(room[0])

    deltas = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    r, c, d = 0, 0, 0
    visited = set()
    cleaned = set()

    while True:
        state = (r, c, d)
        if state in visited:
            break
        visited.add(state)
        cleaned.add((r, c))

        moved = False
        for _ in range(4):
            dr, dc = deltas[d]
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and room[nr][nc] == 0:
                r, c = nr, nc
                moved = True
                break
            d = (d + 1) % 4
        if not moved:
            break

    return len(cleaned)


# =============================================================================
# WAY 14: Compact simulation
# =============================================================================
def number_of_clean_rooms_14(room):
    """Compact simulation."""
    if not room or not room[0]:
        return 0
    m, n = len(room), len(room[0])
    DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    r = c = d = 0
    states = {(0, 0, 0)}
    cleaned = {(0, 0)}

    while True:
        moved = False
        for _ in range(4):
            dr, dc = DIRS[d]
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and room[nr][nc] == 0:
                r, c = nr, nc
                moved = True
                break
            d = (d + 1) % 4
        if not moved:
            break

        if (r, c, d) in states:
            break
        states.add((r, c, d))
        cleaned.add((r, c))

    return len(cleaned)


# =============================================================================
# WAY 15: One-line-ish simulation
# =============================================================================
def number_of_clean_rooms_15(room):
    """Tightly compressed."""
    if not room or not room[0]:
        return 0
    m, n = len(room), len(room[0])
    ds = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    r, c, d = 0, 0, 0
    vis, cln = {(0, 0, 0)}, {(0, 0)}

    def ok(nr, nc):
        return 0 <= nr < m and 0 <= nc < n and not room[nr][nc]

    while True:
        moved = False
        for _ in range(4):
            dr, dc = ds[d]
            if ok(r + dr, c + dc):
                r, c = r + dr, c + dc
                moved = True
                break
            d = (d + 1) % 4
        if not moved:
            break
        if (r, c, d) in vis:
            break
        vis.add((r, c, d))
        cln.add((r, c))

    return len(cln)


# =============================================================================
# WAY 16: NumPy version
# =============================================================================
def number_of_clean_rooms_16(room):
    """Use numpy for grid operations."""
    try:
        import numpy as np
        if not room or not room[0]:
            return 0
        m, n = len(room), len(room[0])
        grid = np.array(room)

        deltas = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        r, c, d = 0, 0, 0
        visited = set()
        cleaned = set()

        while (r, c, d) not in visited:
            visited.add((r, c, d))
            cleaned.add((r, c))

            moved = False
            for _ in range(4):
                dr, dc = deltas[d]
                nr, nc = r + dr, c + dc
                if 0 <= nr < m and 0 <= nc < n and grid[nr][nc] == 0:
                    r, c = nr, nc
                    moved = True
                    break
                d = (d + 1) % 4
            if not moved:
                break

        return len(cleaned)
    except ImportError:
        return number_of_clean_rooms_1(room)


# =============================================================================
# WAY 17: Functional with helper
# =============================================================================
def number_of_clean_rooms_17(room):
    """Functional style."""
    if not room or not room[0]:
        return 0
    m, n = len(room), len(room[0])

    def turn(d):
        return (d + 1) % 4

    def can_move(r, c, d):
        dr, dc = [(0, 1), (1, 0), (0, -1), (-1, 0)][d]
        return 0 <= r + dr < m and 0 <= c + dc < n and room[r + dr][c + dc] == 0

    deltas = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    r, c, d = 0, 0, 0
    visited = set()
    cleaned = set()

    while (r, c, d) not in visited:
        visited.add((r, c, d))
        cleaned.add((r, c))

        moved = False
        for _ in range(4):
            if can_move(r, c, d):
                dr, dc = deltas[d]
                r, c = r + dr, c + dc
                moved = True
                break
            d = turn(d)
        if not moved:
            break

    return len(cleaned)


# =============================================================================
# WAY 18: With explicit helper for blocked check
# =============================================================================
def number_of_clean_rooms_18(room):
    """Extract blocked check into function."""
    if not room or not room[0]:
        return 0
    m, n = len(room), len(room[0])

    def blocked(r, c):
        return r < 0 or r >= m or c < 0 or c >= n or room[r][c] == 1

    deltas = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    r, c, d = 0, 0, 0
    visited = set()
    cleaned = set()

    while (r, c, d) not in visited:
        visited.add((r, c, d))
        cleaned.add((r, c))

        moved = False
        for _ in range(4):
            dr, dc = deltas[d]
            if not blocked(r + dr, c + dc):
                r, c = r + dr, c + dc
                moved = True
                break
            d = (d + 1) % 4
        if not moved:
            break

    return len(cleaned)


# =============================================================================
# WAY 19: Using generator
# =============================================================================
def number_of_clean_rooms_19(room):
    """Generate states with a generator."""
    if not room or not room[0]:
        return 0
    m, n = len(room), len(room[0])

    deltas = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    r, c, d = 0, 0, 0
    visited = set()
    cleaned = set()

    def state_iter():
        nonlocal r, c, d
        while True:
            yield (r, c, d)
            moved = False
            for _ in range(4):
                dr, dc = deltas[d]
                if 0 <= r + dr < m and 0 <= c + dc < n and room[r + dr][c + dc] == 0:
                    r, c = r + dr, c + dc
                    moved = True
                    break
                d = (d + 1) % 4
            if not moved:
                return

    for state in state_iter():
        if state in visited:
            break
        visited.add(state)
        cleaned.add((state[0], state[1]))

    return len(cleaned)


# =============================================================================
# WAY 20: Final cleanest (the one to memorize)
# =============================================================================
def number_of_clean_rooms_20(room):
    """
    Clean final version.
    Simulate robot movement. Robot state = (row, col, direction).
    Track visited states. When state repeats, robot is in a cycle.
    Return count of unique cells cleaned.

    The robot only stops when:
    1. A (row, col, direction) state is repeated (entered cycle), OR
    2. Robot is stuck (all 4 directions blocked from current cell).
    """
    if not room or not room[0]:
        return 0
    m, n = len(room), len(room[0])
    deltas = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    r, c, d = 0, 0, 0
    visited = set()
    cleaned = set()

    while (r, c, d) not in visited:
        visited.add((r, c, d))
        cleaned.add((r, c))

        # Keep turning clockwise until we can move
        moved = False
        for _ in range(4):
            dr, dc = deltas[d]
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and room[nr][nc] == 0:
                r, c = nr, nc
                moved = True
                break
            d = (d + 1) % 4
        if not moved:
            break

    return len(cleaned)


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to simulate a robot moving through a grid. The robot:
- Starts at top-left, facing right.
- Moves straight until blocked (edge or obstacle).
- Turns 90 degrees clockwise on block.
- Returns the number of unique cells cleaned before entering a cycle."

Key Insight:
"Robot state = (row, col, direction). There are at most 4*m*n states.
The robot MUST eventually repeat a state (pigeonhole).
Once a state repeats, robot is in a cycle - no new cells will be visited.
So: simulate until state repeats, count unique cells."

Algorithm:
"1. State = (r, c, d) where d in {0, 1, 2, 3} for right/down/left/up.
2. Track visited states and cleaned cells (sets).
3. While state not in visited:
   a. Mark state as visited, mark (r, c) as cleaned.
   b. Try to move forward; if blocked, turn right (clockwise).
   c. If still blocked after turn, robot is stuck.
4. Return count of cleaned cells."

Why state = (position + direction):
"Robot at (r, c) facing right can later be at (r, c) facing up - this is
a DIFFERENT state with different future behavior. So state includes direction."

Edge cases:
- All cells accessible: robot visits them all.
- Robot stuck immediately: returns 1 (only starting cell).
- 1x1 grid: returns 1.
- Empty grid: returns 0.

Complexity:
- Time: O(m*n) - at most 4*m*n states.
- Space: O(m*n) - sets for tracking.

KEY TRICK:
The robot CLEANS even if it later revisits a space (just with a different
direction). The cycle is detected by (position, direction) repeating,
not just position.

WHY THE ROBOT MUST CYCLE:
- 4 directions × m*n positions = 4*m*n possible states.
- Each step is deterministic given the state.
- After at most 4*m*n steps, a state must repeat.
- Once repeated, the robot will repeat the same sequence forever.

ALTERNATIVE: BFS/DFS
You could model this as a graph: nodes are states (r, c, d),
edges are transitions. BFS from (0,0,0) gives the same result.

RELATIONSHIP TO OTHER PROBLEMS:
- Robot Room (LC 489): Same simulation, different rules.
- Walking Robot Simulation (LC 874): Obstacles but no turning.
- Ant on a boundary: Different geometry.

INTERVIEW TIPS:
1. Always clarify: "What does 'visiting again' mean?" (Same cell, same direction)
2. Mention the cycle detection: "Robot will cycle within 4*m*n steps."
3. Show edge case handling: stuck robot, single cell, etc.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Simulate + visited set (BEST)", number_of_clean_rooms_1),
        ("Way 2: Verbose state tracking", number_of_clean_rooms_2),
        ("Way 3: While with break", number_of_clean_rooms_3),
        ("Way 4: 4D visited array", number_of_clean_rooms_4),
        ("Way 5: Bitmask state encoding", number_of_clean_rooms_5),
        ("Way 6: Helper functions", number_of_clean_rooms_6),
        ("Way 7: With step counter", number_of_clean_rooms_7),
        ("Way 8: Class-based", number_of_clean_rooms_8),
        ("Way 9: Recursive", number_of_clean_rooms_9),
        ("Way 10: Separate state/space sets", number_of_clean_rooms_10),
        ("Way 11: Track full path", number_of_clean_rooms_11),
        ("Way 12: Dict for visited", number_of_clean_rooms_12),
        ("Way 13: Use tuple as state", number_of_clean_rooms_13),
        ("Way 14: Compact", number_of_clean_rooms_14),
        ("Way 15: Tightly compressed", number_of_clean_rooms_15),
        ("Way 16: NumPy", number_of_clean_rooms_16),
        ("Way 17: Functional style", number_of_clean_rooms_17),
        ("Way 18: Helper for blocked check", number_of_clean_rooms_18),
        ("Way 19: Generator-based", number_of_clean_rooms_19),
        ("Way 20: Final cleanest", number_of_clean_rooms_20),
    ]

    test_cases = [
        # Educative quiz example
        (
            [[0, 0, 0],
             [0, 1, 0],
             [0, 0, 0]],
            8
        ),
        # Simple 2x2 empty: 4 cells visited in cycle
        ([[0, 0], [0, 0]], 4),
        # Single cell empty
        ([[0]], 1),
        # 2x2 with corner obstacle: visits 2 cells (cycles between (0,0) and (0,1))
        # (0,0)->(0,1)->turn down, blocked, turn left, back to (0,0)->turn up, blocked,
        # turn right, back to (0,1). Cycle.
        ([[0, 0], [0, 1]], 2),
        # 3x3 empty: visits outer ring (8 cells)
        ([[0, 0, 0], [0, 0, 0], [0, 0, 0]], 8),
        # L-shape obstacle (wall on right column): 6 cells
        ([[0, 0, 1], [0, 0, 1], [0, 0, 1]], 6),
        # Empty grid (treat as 0)
        ([], 0),
        # 4x4 empty: visits outer ring + 1 inner row/col
        # Trace: (0,0)->(0,1)->(0,2)->(0,3)->(1,3)->(2,3)->(3,3)->(3,2)->(3,1)->(3,0)->(2,0)->(1,0)->(0,0). Cycle.
        # Cleaned: 12 cells (perimeter).
        ([[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]], 12),
        # Single row: 2 cells
        ([[0, 0]], 2),
    ]

    print("=" * 70)
    print("NUMBER OF SPACES CLEANING ROBOT CLEANED - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/number-of-spaces-cleaning-robot-cleaned")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for room, expected in test_cases:
            try:
                import copy
                room_copy = copy.deepcopy(room)
                result = func(room_copy)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: room={room} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on room={room} - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)