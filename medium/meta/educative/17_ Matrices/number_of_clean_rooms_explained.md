# Number of Spaces Cleaning Robot Cleaned - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/number-of-spaces-cleaning-robot-cleaned

## The Problem
```
Given a 0-indexed 2D binary matrix `room`:
- 0 = empty space
- 1 = space with object (obstacle)
- top-left corner (0, 0) is always empty.

A cleaning robot:
- Starts at (0, 0), facing right.
- Moves straight until blocked (edge of room or obstacle).
- On blocked, turns 90 degrees clockwise.
- KEEPS turning until it can move.
- Cleans every space it visits (including start).
- Continues indefinitely.
- When it visits a space again while facing the SAME direction, return
  the number of unique spaces cleaned.

Examples:
    room = [[0,0,0],[0,1,0],[0,0,0]] -> 8

Constraints:
- 1 <= m, n <= 300
- room[r][c] is 0 or 1
- room[0][0] == 0
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
We have a deterministic robot. The robot's behavior depends ONLY on
its current state (position + direction). Since there are only 4*m*n
possible states, the robot MUST eventually enter a cycle.

When it visits (r, c, d) that was visited before, it will repeat the
exact same sequence forever - no new cells will be cleaned.

So the problem is: simulate until cycle, count unique cells.
```

### Step 2: The Trick
> "KEY INSIGHT: The robot's state is (row, col, direction). The state
> space is finite (4*m*n). The robot MUST eventually repeat a state.
> Once it does, it's stuck in a cycle forever.
>
> Algorithm:
> 1. Track visited (row, col, direction) states.
> 2. Track unique cleaned (row, col) cells.
> 3. Simulate until a state repeats.
> 4. Return count of cleaned cells."

### Step 3: Movement rules
> "On each step, try to move in current direction.
> - If blocked (out of bounds OR obstacle), turn 90° clockwise.
> - KEEP TURNING clockwise until we find a valid move.
> - If all 4 directions blocked, robot is stuck.
>
> Why keep turning? Because the robot 'turns 90 degrees clockwise
> and continues moving' - this implies it tries the new direction.
> If still blocked, it would naturally keep turning."

### Step 4: Why state includes direction
> "Two visits to the same cell are considered 'visiting again' only
> if facing the SAME direction. The robot at (r, c) facing right has
> different future behavior than at (r, c) facing up.
>
> So state = (row, col, direction) — NOT just (row, col)."

### Step 5: Why the robot must cycle
> "Pigeonhole principle: 4*m*n possible states. Each step is
> deterministic given the state. After at most 4*m*n steps, a state
> must repeat. After repeat, the sequence repeats forever."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to simulate a robot moving through a grid. The robot:
> - Starts at (0, 0), facing right.
> - Moves straight until blocked.
> - Turns clockwise (90°) on block.
> - Returns the number of unique cells cleaned before entering a cycle."

**Key Insight:**
> "The robot's state is (row, col, direction). State space is 4*m*n,
> so the robot MUST eventually repeat a state. Once repeated, it cycles
> forever — no new cells cleaned. So simulate until state repeats."

**Algorithm:**
> "1. Initialize state = (0, 0, right), visited = {}, cleaned = {}.
> 2. While current state not in visited:
>    a. Mark state visited, mark current cell cleaned.
>    b. Try to move forward; if blocked, turn clockwise.
>    c. Keep turning until can move.
>    d. If all 4 directions blocked, robot is stuck — stop.
> 3. Return |cleaned|."

**Why include direction in state:**
> "Two visits to the same cell are 'visiting again' only if facing
> the same direction. The robot at (r, c) facing right behaves
> differently than at (r, c) facing up."

**Edge cases:**
- 1x1 grid: visits only (0,0), cycles back. Returns 1.
- All empty 2x2: visits all 4 cells in a cycle. Returns 4.
- Robot stuck at start (impossible if (0,0) is empty and grid >= 2x2).
- Empty grid: returns 0.

**Complexity:**
- Time: O(m*n) — at most 4*m*n states visited.
- Space: O(m*n) — visited states and cleaned cells.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Simulate with visited set (BEST - Memorize!)
```python
def number_of_clean_rooms_1(room):
    if not room or not room[0]:
        return 0
    m, n = len(room), len(room[0])
    deltas = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # right, down, left, up

    r, c, d = 0, 0, 0
    visited = set()
    cleaned = set()

    while (r, c, d) not in visited:
        visited.add((r, c, d))
        cleaned.add((r, c))

        # Keep turning clockwise until we can move
        for _ in range(4):
            dr, dc = deltas[d]
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and room[nr][nc] == 0:
                r, c = nr, nc
                break
            d = (d + 1) % 4
        else:
            break  # All 4 directions blocked

    return len(cleaned)
```

### Way 2: Verbose state tracking

### Way 3: While loop with break

### Way 4: 4D visited array

### Way 5: Bitmask state encoding

### Way 6: Helper functions

### Way 7: With step counter safety bound

### Way 8: Class-based simulation

### Way 9: Recursive simulation

### Way 10: Separate state/space sets

### Way 11: Track full path

### Way 12: Use dict for visited

### Way 13: Use tuple as state

### Way 14: Compact simulation

### Way 15: Tightly compressed

### Way 16: NumPy-based

### Way 17: Functional style

### Way 18: Helper for blocked check

### Way 19: Generator-based

### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Most efficient     | Way 1    | O(m*n)       |
| Educational        | Way 4    | 4D array     |
| Avoid recursion    | Way 1    | Iterative    |
| Compact code       | Way 15   | One-liner    |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Way 1 (BEST) | O(m*n) | O(m*n) | Standard |
| Way 4 (4D array) | O(m*n) | O(m*n) | No hashing overhead |
| Way 7 (step limit) | O(m*n) | O(m*n) | Safety bound |

All approaches have the same complexity since the algorithm is fundamentally
deterministic simulation.

---

## Walkthrough Example

```
room = [[0, 0, 0],
        [0, 1, 0],
        [0, 0, 0]]

Start at (0,0) facing right.
Step 1: Move right to (0,1). State (0,1,0).
Step 2: Move right to (0,2). State (0,2,0).
Step 3: Right blocked (edge). Turn down. Move to (1,2). State (1,2,1).
Step 4: Move down to (2,2). State (2,2,1).
Step 5: Down blocked (edge). Turn left. Move to (2,1). State (2,1,2).
Step 6: Move left to (2,0). State (2,0,2).
Step 7: Left blocked (edge). Turn up. Move to (1,0). State (1,0,3).
Step 8: Move up to (0,0). State (0,0,3).
Step 9: Up blocked (edge). Turn right. Move to (0,1). State (0,1,0).
        ALREADY VISITED! Stop.

Cleaned cells: (0,0), (0,1), (0,2), (1,2), (2,2), (2,1), (2,0), (1,0)
Count: 8 ✓
```

---

## Best Answer to Memorize

```python
def number_of_clean_rooms(room):
    if not room or not room[0]:
        return 0
    m, n = len(room), len(room[0])
    deltas = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # R, D, L, U

    r, c, d = 0, 0, 0
    visited = set()
    cleaned = set()

    while (r, c, d) not in visited:
        visited.add((r, c, d))
        cleaned.add((r, c))

        # Keep turning clockwise until can move
        for _ in range(4):
            dr, dc = deltas[d]
            nr, nc = r + dr, c + dc
            if 0 <= nr < m and 0 <= nc < n and room[nr][nc] == 0:
                r, c = nr, nc
                break
            d = (d + 1) % 4
        else:
            break

    return len(cleaned)
```

**~17 lines. O(m*n) time. O(m*n) space. Interview-ready!**

---

## Key Insights

### Why state includes direction?
> "Two visits to the same cell are 'visiting again' ONLY IF the robot
> is facing the same direction. So state = (row, col, direction)."

### Why does the robot cycle?
> "Pigeonhole: at most 4*m*n states. After at most that many steps,
> a state repeats. Once repeated, the deterministic behavior repeats."

### Why keep turning on block?
> "The robot 'turns 90° clockwise and continues moving'. If still
> blocked, by the same logic it would keep turning clockwise."

### Why return len(cleaned)?
> "The robot cleans each cell it visits. We want unique cells,
> so we use a set. The cycle starts at the FIRST repeated state,
> meaning the robot had cleaned all reachable cells."

---

## Test Cases

| room | Expected | Notes |
|------|----------|-------|
| [[0,0,0],[0,1,0],[0,0,0]] | 8 | Educative example |
| [[0,0],[0,0]] | 4 | All 4 cells in cycle |
| [[0]] | 1 | Single cell |
| [[0,0],[0,1]] | 2 | Cycles between 2 cells |
| [[0,0,0],[0,0,0],[0,0,0]] | 8 | Perimeter |
| [[0,0,1],[0,0,1],[0,0,1]] | 6 | Right column blocked |
| [] | 0 | Empty grid |

---

## Common Pitfalls

1. **Single-turn logic**: When blocked, the robot may need to turn MULTIPLE times (not just once). Use a loop or "keep turning until can move".
2. **State = position only**: Must include direction. Two visits to same cell from different directions don't count as "visiting again".
3. **Forgetting to mark visited BEFORE checking**: Add state to visited, THEN check next state.
4. **Edge case: stuck robot**: If all 4 directions blocked from current cell, robot stops.
5. **Cycle detection timing**: Stop when state would be repeated, but DON'T add the repeated state to cleaned (it wasn't cleaned again).

---

## Why This Problem Matters

> "Tests:
> 1. Cycle detection in deterministic systems.
> 2. State space modeling.
> 3. Simulation with multiple stopping conditions.
> 4. Foundation for: robot simulation, game state, automata."

---

## Beyond This Problem: Related Patterns

### 1. Robot Room (LC 489)
```python
# Robot with sensors, can call API.
# Similar cycle detection.
```

### 2. Walking Robot Simulation (LC 874)
```python
# Robot moves with commands, but obstacles as set.
# No turning here, just movement.
```

### 3. Out of Boundary Paths (LC 576)
```python
# Different: probabilistic (ball moves in random direction).
```

### 4. Number of Distinct Islands (LC 694)
```python
# Cycle detection isn't the focus, but state tracking is.
```

---

## Connection to Cycle Detection Problems

This problem uses "Pigeonhole + Determinism" pattern:

```
1. Define a state space (here: 4*m*n states).
2. Each step is deterministic given the state.
3. State space is finite.
4. Therefore, system MUST cycle.
5. Find when it cycles; answer is what happened BEFORE cycle.
```

This applies to:
- Floyd's cycle detection (linked lists).
- Game of life termination.
- Cellular automata.
- Many deterministic simulations.

---

## Quick Checklist

When given a similar problem:
- [ ] What's the state? (position + direction + other)
- [ ] What's the state space size? (m * n * 4 here)
- [ ] Is the system deterministic? (yes here)
- [ ] What causes termination? (state repeat, stuck, target reached)
- [ ] Do I need multiple turns? (yes here)

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- Pattern: Cycle Detection in Deterministic Systems
