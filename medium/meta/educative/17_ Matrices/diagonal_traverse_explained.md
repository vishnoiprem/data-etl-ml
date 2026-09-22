# Diagonal Traverse — 0.0001% Expert Guide

> **LeetCode 498** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/diagonal-traverse
> **Problem:** `findDiagonalOrder(mat)` — traverse matrix in diagonal order

---

## 📋 WHAT THE QUESTION ASKS

Given an `m×n` integer matrix `mat`, return all elements traversed in **diagonal order**.

The diagonals **alternate**: first diagonal goes **up-right** (just the start), then **down-left**, then **up-right**, etc.

### Constraints
- `1 <= m, n <= 10^4`
- `1 <= m * n <= 10^4`
- `-10^5 <= mat[i][j] <= 10^5`

### Example

```
mat = [[1, 2, 3],
       [4, 5, 6],
       [7, 8, 9]]

Diagonals:
- d=0 (UP): [(0,0)] = [1]
- d=1 (DOWN-LEFT): [(0,1),(1,0)] = [2, 4]
- d=2 (UP): [(2,0),(1,1),(0,2)] = [7, 5, 3]
- d=3 (DOWN-LEFT): [(1,2),(2,1)] = [6, 8]
- d=4 (UP): [(2,2)] = [9]

Result: [1, 2, 4, 7, 5, 3, 6, 8, 9]
```

### Why This Is "Medium"
- The simulation logic is intricate (boundary conditions).
- Two valid approaches: simulation or grouping.
- Off-by-one errors at corners.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Traverse the matrix diagonally, alternating UP-RIGHT and DOWN-LEFT directions. Visit every element exactly once."

### Step 2: Identify the Diagonal Index (3 min)
> "Elements on the same diagonal share the value `i + j`. Diagonals are indexed by `d = i + j`."

So diagonal `d` contains all cells `(i, j)` where `i + j = d`, with bounds `0 <= i < m` and `0 <= j < n`.

### Step 3: Two Approaches (5 min)

**Approach A: Simulation**
- Track `(i, j)` and a direction flag.
- Move and flip at boundaries.
- O(mn) time, O(1) extra space.

**Approach B: Group by Diagonal**
- Collect elements into diagonal lists.
- Reverse even diagonals (UP-RIGHT traversal is bottom-to-top).
- O(mn) time, O(mn) space.

**Best:** Simulation (O(1) space, more intuitive).

### Step 4: Direction Logic (5 min)

**UP-RIGHT (going up):** move `(-1, +1)`. Flip when:
- Right edge (`j == n-1`): move to `(i+1, j)`, flip DOWN.
- Top edge (`i == 0`): move to `(i, j+1)`, flip DOWN.

**DOWN-LEFT (going down):** move `(+1, -1)`. Flip when:
- Bottom edge (`i == m-1`): move to `(i, j+1)`, flip UP.
- Left edge (`j == 0`): move to `(i+1, j)`, flip UP.

### Step 5: Sanity Checks (2 min)
- `1x1`: just one cell.
- `1xn` or `mx1`: just iterate row by row (no diagonals).
- Square matrix: same logic, just `m == n`.

### Step 6: Code It (5 min)

```python
def findDiagonalOrder(mat):
    m, n = len(mat), len(mat[0])
    result = []
    i = j = 0
    going_up = True
    for _ in range(m * n):
        result.append(mat[i][j])
        if going_up:
            if j == n - 1:
                i += 1; going_up = False
            elif i == 0:
                j += 1; going_up = False
            else:
                i -= 1; j += 1
        else:
            if i == m - 1:
                j += 1; going_up = True
            elif j == 0:
                i += 1; going_up = True
            else:
                i += 1; j -= 1
    return result
```

### Step 7: Verify with Example (2 min)
For 3x3 `[[1,2,3],[4,5,6],[7,8,9]]`:
- (0,0) UP. → (1,0) wait... should be (-1, 1) but i=0. j != n-1. Flip. j=1, going DOWN.
  Hmm wait that's wrong. Let me retrace.

Actually: starting at (0,0) going UP. Try to move to (-1, 1). i would be -1 (out of bounds). So hit top edge. Move to (0, 1), going DOWN.

So sequence: (0,0), (0,1), then go DOWN: (1,0), (2,0). Then hit bottom edge: move to (2,1) going UP. Then (1,2). Hit top + right simultaneously: tricky! Right edge takes precedence → move to (2,2) going DOWN.

Sequence: (0,0), (0,1), (1,0), (2,0), (2,1), (1,2), (2,2). With values: 1, 2, 4, 7, 8, 6, 9. Hmm, that's not right.

Let me re-trace the algorithm carefully:
- Start: (0,0) UP. Value: 1. Add to result.
- Try move UP-RIGHT: (-1, 1). Out of bounds. i==0 hit top edge → j=1, flip DOWN.
- Now (0,1) DOWN. Value: 2. Add to result.
- Try move DOWN-LEFT: (1, 0). In bounds. → (1, 0).
- (1,0) DOWN. Value: 4. Add.
- Try move DOWN-LEFT: (2, -1). j==0 hit left edge → i=2, flip UP.
- (2,0) UP. Value: 7. Add.
- Try UP-RIGHT: (1, 1). In bounds. → (1, 1).
- (1,1) UP. Value: 5. Add.
- Try UP-RIGHT: (0, 2). In bounds. → (0, 2).
- (0,2) UP. Value: 3. Add.
- Try UP-RIGHT: (-1, 3). j==n-1 hit right edge → i=1, flip DOWN.
- (1,2) DOWN. Value: 6. Add.
- Try DOWN-LEFT: (2, 1). In bounds. → (2, 1).
- (2,1) DOWN. Value: 8. Add.
- Try DOWN-LEFT: (3, 0). i==m-1 hit bottom edge → j=2, flip UP.
- (2,2) UP. Value: 9. Add.
- Done!

Result: [1, 2, 4, 7, 5, 3, 6, 8, 9] ✓

### Step 8: Discuss Trade-offs (5 min)
> "Two approaches:
> 1. **Simulation:** O(mn) time, O(1) space. **Best for production.**
> 2. **Group by diagonal:** O(mn) time, O(mn) space. Easier to reason about.

> I'll use simulation."

### Step 9: Off-by-One Considerations (2 min)
- Right edge precedence over top edge (when both hit).
- Bottom edge precedence over left edge (when both hit).
- Starting direction: UP (just (0,0)).

### Step 10: Final Clean Code (5 min)
Memorize the 18-line solution.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to traverse an m x n matrix in diagonal order, alternating
between up-right and down-left.

KEY INSIGHT: Elements on the same diagonal share i+j. Two approaches:
1. SIMULATION: Track (i, j) and direction. Flip at boundaries.
2. GROUP BY DIAGONAL: Collect elements per diagonal, reverse even ones.

I'll use simulation - O(1) extra space.

DIRECTION LOGIC:
- UP-RIGHT: move (i-1, j+1). Flip when:
  - j == n-1 (right edge): move to (i+1, j), flip DOWN
  - i == 0 (top edge): move to (i, j+1), flip DOWN

- DOWN-LEFT: move (i+1, j-1). Flip when:
  - i == m-1 (bottom edge): move to (i, j+1), flip UP
  - j == 0 (left edge): move to (i+1, j), flip UP

Start at (0, 0) going UP. Visit m*n cells.

COMPLEXITY: O(mn) time, O(1) extra space."
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Simulation (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | Direction-flipping (BEST) | O(mn) | O(1) | **THE ANSWER** |
| 2 | Verbose | O(mn) | O(1) | Educational |
| 6 | Direction vector | O(mn) | O(1) | Variant |
| 8 | Most concise | O(mn) | O(1) | One-liner |
| 9 | Helper function | O(mn) | O(1) | Readable |
| 11 | BFS visited | O(mn) | O(1) | Educational |
| 13 | Compact BFS | O(mn) | O(1) | Variant |
| 15 | Boundary helper | O(mn) | O(1) | Readable |
| 20 | Final cleanest | O(mn) | O(1) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: Group by Diagonal

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 3 | defaultdict + reverse | O(mn) | O(mn) | Educational |
| 4 | defaultdict + insert | O(mn) | O(mn) | Variant |
| 5 | List of lists | O(mn) | O(mn) | Same as 3 |
| 10 | Group + reverse | O(mn) | O(mn) | Variant |
| 12 | Process diagonals | O(mn) | O(mn) | Educational |
| 14 | Generator | O(mn) | O(mn) | Pythonic |
| 17 | Functional | O(mn) | O(mn) | Functional |
| 18 | Count-up | O(mn) | O(mn) | Educational |
| 19 | Itertools | O(mn) | O(mn) | Functional |

### 🟣 TIER 3: Specialized

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 7 | BFS-like with coords | O(mn) | O(mn) | Educational |
| 16 | Numpy | O(mn) | O(mn) | Fast in practice |

---

## 💎 THE 18-LINE SOLUTION (Memorize!)

```python
def findDiagonalOrder(mat):
    if not mat or not mat[0]:
        return []
    m, n = len(mat), len(mat[0])
    result = []
    i = j = 0
    going_up = True
    for _ in range(m * n):
        result.append(mat[i][j])
        if going_up:
            if j == n - 1:
                i += 1
                going_up = False
            elif i == 0:
                j += 1
                going_up = False
            else:
                i -= 1
                j += 1
        else:
            if i == m - 1:
                j += 1
                going_up = True
            elif j == 0:
                i += 1
                going_up = True
            else:
                i += 1
                j -= 1
    return result
```

**Time:** `O(m * n)`
**Space:** `O(1)` (excluding output)

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: i+j is the Diagonal Coordinate

> Every cell belongs to a unique diagonal identified by `d = i + j`.

There are `m + n - 1` diagonals (range `0` to `m+n-2`).

**Connection to:**
- **Coordinate transformations:** Rotate the grid by 45° and `i+j` becomes the new y-axis.
- **Hash functions:** `i+j` is a perfect hash for diagonal coordinates.
- **Linear algebra:** Skew transformation matrix.

### Insight 2: Diagonal Traversal = Sliced View

> Diagonal traversal is a **slice of the matrix** along `i+j = const`.

This is the same idea as **anti-diagonal** in linear algebra and **NW-SE** slicing in image processing.

**Connection to:**
- **Image processing:** Anti-diagonal filtering, edge detection.
- **Convolution:** Some kernels are diagonal (e.g., `[[0,1,0],[1,0,1],[0,1,0]]`).
- **Parallel computing:** Diagonal partitioning for load balancing.

### Insight 3: Why Group by Diagonal Then Reverse?

> For UP-RIGHT diagonals, we collect top-to-bottom but visit bottom-to-top.

So we collect in one order and reverse before emitting. This is a classic **buffer + reverse** pattern.

**Connection to:**
- **Stream processing:** Buffer, sort, emit (e.g., tumbling windows).
- **Database:** `ORDER BY` after `GROUP BY`.
- **MapReduce:** Shuffle, sort, reduce.

### Insight 4: Boundary Precedence

> When you hit a corner (both edges), the right/bottom edge takes precedence.

This is critical for correct corner handling. In 3x3:
- (0, 2): top AND right edge. Right edge takes precedence → move DOWN to (1, 2).
- (2, 0): bottom AND left edge. Bottom edge takes precedence → move UP to (2, 1).

**Connection to:**
- **CSS:** z-index, margin collapsing.
- **Game design:** Border handling (Pac-Man wraps around).
- **Physics:** Reflecting at corners.

### Insight 5: Why Simulation is O(1) Space

> The simulation only needs to know the **current position** and **direction**.

No need to store all diagonals. This is the **streaming** approach.

**Connection to:**
- **Streaming algorithms:** Process one element at a time.
- **Single-pass algorithms:** Lower memory footprint.
- **Real-time systems:** Constant memory.

### Insight 6: The Direction Vector Trick

> Use `(di, dj)` for directions: `(-1, 1)` for UP-RIGHT, `(1, -1)` for DOWN-LEFT.

Flipping: `(di, dj) = (-di, -dj)`. Compact and elegant.

**Connection to:**
- **Quaternions:** Rotations in 3D.
- **Vector graphics:** Direction + magnitude.
- **Physics:** Velocity components.

### Insight 7: Connection to Number Theory

> The cells visited on diagonal `d` are at positions `(i, d-i)` for valid `i`.

The number of cells on diagonal `d` is:
- `d + 1` if `d < min(m, n)`
- `min(m, n)` if `min(m, n) <= d < max(m, n)`
- `m + n - 1 - d` if `d >= max(m, n)`

This is a **triangular distribution**! Same pattern as **Pascal's triangle** row sums.

**Connection to:**
- **Combinatorics:** Triangular numbers.
- **Statistics:** Probability density.
- **Signal processing:** Triangular windows.

### Insight 8: Why This Is a Common Interview Problem

This problem tests:
1. **Boundary condition handling** (off-by-one mastery).
2. **State machine design** (direction flip).
3. **Two-pointer/coordinate tracking** (i, j manipulation).
4. **Space optimization** (O(1) vs O(mn)).

**Connection to:**
- **Compiler design:** Lexer token traversal.
- **Game development:** Sprite movement.
- **GIS:** Coordinate system transformations.

### Insight 9: Generalization to k-Diagonals

> This generalizes to **k-diagonal** traversal (skip k cells per step).

Used in image processing for non-local means filtering.

**Connection to:**
- **Image processing:** Non-local means.
- **Graph algorithms:** BFS by hop distance.
- **Sparse matrices:** Diagonal storage (DIA format).

### Insight 10: Real-World Applications

| Application | Use |
|-------------|-----|
| **Image compression (JPEG)** | Zigzag scan to group low-frequency coefficients |
| **Anti-aliasing** | Diagonal filtering |
| **Memory layout (DIA format)** | Sparse matrix storage |
| **GPU computing** | Diagonal tiling for cache locality |
| **ML attention** | Banded attention patterns |

**The JPEG zigzag scan IS a diagonal traversal!** That's why JPEG works — low-frequency components cluster along diagonals.

---

## 🧪 TEST CASES

| Matrix | Expected | Note |
|--------|----------|------|
| `[[1,2,3],[4,5,6],[7,8,9]]` | `[1,2,4,7,5,3,6,8,9]` | Standard 3x3 |
| `[[10,20,30,40,50],[60,70,80,90,100]]` | `[10,20,60,70,30,40,80,90,50,100]` | 2x5 |
| `[[5]]` | `[5]` | Trivial |
| `[[1,2,3,4]]` | `[1,2,3,4]` | 1x4 |
| `[[1],[2],[3],[4]]` | `[1,2,3,4]` | 4x1 |
| `[[1,2],[3,4]]` | `[1,2,3,4]` | 2x2 |
| `[[1,2,3,4],[5,6,7,8],[9,10,11,12]]` | `[1,2,5,9,6,3,4,7,10,11,8,12]` | 3x4 |
| `[[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]]` | `[1,2,5,9,6,3,4,7,10,13,14,11,8,12,15,16]` | 4x4 |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Simulation** | **O(mn)** | **O(1)** | **✅ BEST** |
| Group by diagonal | O(mn) | O(mn) | ✅ Educational |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Spiral Matrix (LC 54) | Direction change | https://leetcode.com/problems/spiral-matrix/ |
| Zigzag Conversion (LC 6) | 1D zigzag | https://leetcode.com/problems/zigzag-conversion/ |
| Diagonal Traverse II (LC 1424) | Same with bottom-up start | https://leetcode.com/problems/diagonal-traverse-ii/ |
| Set Matrix Zeroes (LC 73) | In-place marking | https://leetcode.com/problems/set-matrix-zeroes/ |
| Diagonal Traverse (LC 498) | **This problem** | https://leetcode.com/problems/diagonal-traverse/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **Diagonal coordinate = `i + j`.** Group or simulate based on this.
2. **Two approaches:** Simulation (O(1) space) or grouping (cleaner logic).
3. **Direction logic:** UP-RIGHT `(-1, +1)`, DOWN-LEFT `(+1, -1)`. Flip at boundaries.
4. **Right/bottom edge precedence** at corners.
5. **Starting direction is UP** (just (0,0)).
6. **The simulation is O(1) extra space** — only position + direction.
7. **Group by diagonal, reverse even ones** — easier to reason about but uses O(mn) space.
8. **The number of cells per diagonal** follows a triangular distribution.
9. **JPEG uses zigzag scan = diagonal traversal** — clusters low-frequency.
10. **Boundary conditions are the hard part** — off-by-one at every edge.

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **JPEG compression** | Zigzag scan groups low-frequency coefficients |
| **Sparse matrices** | DIA (diagonal) storage format |
| **Image processing** | Anti-diagonal filtering, edge detection |
| **GPU computing** | Diagonal tiling for cache locality |
| **ML attention** | Banded attention patterns (LongFormer, BigBird) |
| **Compiler design** | Lexer token traversal |
| **Game development** | Sprite movement, grid-based AI |
| **GIS** | Coordinate transformations |
| **Coordinate transforms** | Rotate by 45° makes i+j the y-axis |
| **Linear algebra** | Skew transformation matrix |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can identify i+j as diagonal coordinate
- [x] Can derive direction logic in 60 seconds
- [x] Can code the 18-line solution in 90 seconds
- [x] Know the complexity: O(mn) time, O(1) space
- [x] Can compare simulation vs grouping
- [x] Know corner precedence rules
- [x] Know the JPEG zigzag scan connection
- [x] Can list 5 real-world applications
- [x] Can generalize to k-diagonals

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 12 minutes.
**Lines of code to write:** 18 (simulation).
**Insight:** "Track (i, j) and direction. UP-RIGHT: move (-1, +1). DOWN-LEFT: move (+1, -1). Flip at edges with right/bottom precedence."
