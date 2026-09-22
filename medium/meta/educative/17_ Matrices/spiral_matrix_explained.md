# Spiral Matrix — 0.0001% Expert Guide

> **LeetCode 54** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/spiral-matrix
> **Problem:** `spiralOrder(matrix)` — return matrix elements in spiral order

---

## 📋 WHAT THE QUESTION ASKS

Given an `m×n` matrix, return all elements in **spiral order** starting from the top-left:
- Go right along the top row
- Go down along the right column
- Go left along the bottom row
- Go up along the left column
- Repeat with the inner sub-matrix

### Constraints
- `1 <= m, n <= 10`
- `-100 <= matrix[i][j] <= 100`

### Example

```
Input: [[1,2,3],
        [4,5,6],
        [7,8,9]]

Spiral: 1→2→3→6→9→8→7→4→5
Output: [1, 2, 3, 6, 9, 8, 7, 4, 5]
```

### Why This Is "Medium"
- The boundary shrinking logic has subtle off-by-one traps.
- Must handle rectangular matrices (m ≠ n).
- The "inner layer" concept requires careful thought.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Visit elements in a spiral: right across top, down the right, left across bottom, up the left. Then repeat for the inner sub-matrix."

### Step 2: Identify the Algorithm (3 min)
> "Maintain four boundaries: top, bottom, left, right. Shrink them as we traverse."

### Step 3: Algorithm (5 min)
```
top = 0, bottom = m-1, left = 0, right = n-1
while top <= bottom and left <= right:
    1. Traverse top row: (top, left) to (top, right). top += 1.
    2. Traverse right col: (top, right) to (bottom, right). right -= 1.
    3. If top <= bottom: traverse bottom row (right, left). bottom -= 1.
    4. If left <= right: traverse left col (bottom, top). left += 1.
```

### Step 4: Critical Detail (2 min)
> "Steps 3 and 4 need a guard: `if top <= bottom` and `if left <= right`. Without these, we'd duplicate cells in single-row or single-column cases."

### Step 5: Edge Cases (2 min)
- 1x1: just return `[[1]]`.
- 1xN or Nx1: just iterate in order.
- Square matrix: simpler logic.

### Step 6: Code It (5 min)

```python
def spiralOrder(matrix):
    if not matrix:
        return []
    result = []
    top, bottom = 0, len(matrix) - 1
    left, right = 0, len(matrix[0]) - 1
    while top <= bottom and left <= right:
        # 1. Left → Right
        for j in range(left, right + 1):
            result.append(matrix[top][j])
        top += 1
        # 2. Top → Bottom
        for i in range(top, bottom + 1):
            result.append(matrix[i][right])
        right -= 1
        # 3. Right → Left
        if top <= bottom:
            for j in range(right, left - 1, -1):
                result.append(matrix[bottom][j])
            bottom -= 1
        # 4. Bottom → Top
        if left <= right:
            for i in range(bottom, top - 1, -1):
                result.append(matrix[i][left])
            left += 1
    return result
```

### Step 7: Verify with Example (2 min)
For 3x3:
- top=0, bottom=2, left=0, right=2.
- Step 1: 1,2,3. top=1.
- Step 2: 6,9. right=1.
- Step 3: 8,7. bottom=1.
- Step 4: 4. left=1.
- top=1, bottom=1, left=1, right=1. Continue.
- Step 1: 5. top=2.
- Step 2: (none, top > bottom). right=0.
- Step 3: top > bottom, skip. bottom=0.
- Step 4: left > right, skip. left=2.
- top > bottom, exit. Result: [1,2,3,6,9,8,7,4,5]. ✓

### Step 8: Discuss Trade-offs (3 min)
> "Three approaches:
> 1. **Boundary shrinking:** O(mn) time, O(1) space. **Best.**
> 2. **Direction vectors:** O(mn) time, O(mn) space (visited set).
> 3. **Pop and rotate:** O(mn²) time, O(mn) space (worst case).

> I'll use boundary shrinking."

### Step 9: Generalize to Spiral Matrix II (5 min)
> "The reverse problem: given n, generate an n×n matrix filled in spiral order with 1 to n²."

Same boundary logic, but write instead of read.

### Step 10: Final Clean Code (5 min)
Memorize the 25-line solution.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to return matrix elements in spiral order.

KEY INSIGHT: Maintain four boundaries (top, bottom, left, right) and
shrink them after each traversal direction.

ALGORITHM:
1. top = 0, bottom = m-1, left = 0, right = n-1.
2. While top <= bottom and left <= right:
   a. Traverse top row left → right. top += 1.
   b. Traverse right col top → bottom. right -= 1.
   c. If top <= bottom: traverse bottom row right → left. bottom -= 1.
   d. If left <= right: traverse left col bottom → top. left += 1.

CRITICAL: Steps c and d need guards to avoid duplicate visits in
single-row or single-column cases.

COMPLEXITY: O(mn) time, O(1) extra space."
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Boundary Shrinking (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | Boundary shrinking (BEST) | O(mn) | O(1) | **THE ANSWER** |
| 2 | Verbose | O(mn) | O(1) | Educational |
| 7 | Layer-by-layer | O(mn) | O(1) | Variant |
| 9 | While loop | O(mn) | O(1) | Variant |
| 10 | Compact boundaries | O(mn) | O(1) | Variant |
| 14 | Most concise | O(mn) | O(1) | One-liner |
| 16 | With bounds tracking | O(mn) | O(1) | Educational |
| 18 | Explicit shrinking | O(mn) | O(1) | Educational |
| 20 | Final cleanest | O(mn) | O(1) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: Direction Vectors

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 3 | Direction + visited set | O(mn) | O(mn) | Educational |
| 4 | Direction + bounds check | O(mn) | O(1) | Variant |
| 8 | BFS with deque | O(mn) | O(mn) | Educational |
| 15 | Direction + while loop | O(mn) | O(1) | Variant |

### 🟣 TIER 3: Specialized Approaches

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 5 | Recursive | O(mn) | O(mn) recursion | Functional |
| 6 | Pop + rotate | O(mn²) | O(mn) | Educational only |
| 11 | Zip rotate | O(mn) | O(mn) | Pythonic |
| 12 | Itertools chain | O(mn) | O(mn) | Pythonic |
| 13 | Generator | O(mn) | O(mn) | Pythonic |
| 17 | Class-based | O(mn) | O(1) | Reusable |
| 19 | Numpy | O(mn) | O(mn) | Fast in practice |

---

## 💎 THE 25-LINE SOLUTION (Memorize!)

```python
def spiralOrder(matrix):
    if not matrix:
        return []
    result = []
    top, bottom = 0, len(matrix) - 1
    left, right = 0, len(matrix[0]) - 1
    while top <= bottom and left <= right:
        # 1. Left → Right
        for j in range(left, right + 1):
            result.append(matrix[top][j])
        top += 1
        # 2. Top → Bottom
        for i in range(top, bottom + 1):
            result.append(matrix[i][right])
        right -= 1
        # 3. Right → Left
        if top <= bottom:
            for j in range(right, left - 1, -1):
                result.append(matrix[bottom][j])
            bottom -= 1
        # 4. Bottom → Top
        if left <= right:
            for i in range(bottom, top - 1, -1):
                result.append(matrix[i][left])
            left += 1
    return result
```

**Time:** `O(m * n)`
**Space:** `O(1)` (excluding output)

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Boundary Shrinking = Recursive Sub-problems

> Each iteration peels off one layer of the matrix and recurses on the inner sub-matrix.

The recursion is implicit: after step 4, the new boundaries define a smaller matrix.

**Connection to:**
- **Matrix operations:** Block matrix decomposition.
- **Sparse matrices:** Border row/column handling.
- **Convolution:** Edge handling (zero-pad, reflect, etc.).

### Insight 2: The Critical Guards

> Steps 3 and 4 need `if top <= bottom` and `if left <= right` checks.

Without these, in single-row or single-column cases (e.g., 1×n or 3×1), we'd visit cells twice.

**Connection to:**
- **Off-by-one errors:** The #1 bug in matrix problems.
- **Edge handling:** Critical in image processing.
- **Boundary conditions:** Always test single row/col cases.

### Insight 3: Why Direction Vectors Use O(mn) Space

> Direction vectors need a visited set to avoid revisiting cells.

Boundary shrinking avoids this by tracking the boundaries directly. **Implicit > explicit** when possible.

**Connection to:**
- **Memory-efficient algorithms:** Use problem structure.
- **Streaming:** Don't store what you can recompute.
- **BFS/DFS:** Visited set is often necessary; sometimes not.

### Insight 4: Connection to Image Processing

> Spiral traversal is a **space-filling curve** — Hilbert, Moore, Peano curves.

These curves preserve locality: nearby cells in 2D are nearby in 1D.

**Connection to:**
- **JPEG 2000:** Uses space-filling curves for better locality.
- **Hilbert curves:** Used in databases for spatial indexing.
- **Cache locality:** Spiral traversal has good locality.

### Insight 5: The "Layer" Concept

> A matrix has `ceil(min(m, n) / 2)` spiral layers.

Each layer is a rectangle. The outermost layer has 4 sides; inner layers may be degenerate.

**Connection to:**
- **Convolution layers:** Same structure in neural networks.
- **Image pyramids:** Multi-resolution layers.
- **Tensors:** Slicing along dimensions.

### Insight 6: Spiral Matrix II is the Inverse

> Spiral Matrix II generates a matrix in spiral order. Same logic, but **write** instead of **read**.

The state of each cell `(i, j)` in spiral order can be computed:
- cell number `k` (1-indexed) at position `(r, c)` after `k-1` writes.

**Connection to:**
- **Inverse problems:** Read vs write traversal.
- **Generative models:** Same algorithm, different direction.
- **Database transactions:** Insert vs select.

### Insight 7: Why Test Single Row/Col

Single row `[[1,2,3,4,5]]`:
- Step 1: 1,2,3,4,5. top=1.
- Step 2: (top > bottom). right=4.
- Step 3: (top > bottom), skip. bottom=-1.
- Step 4: (left > right), skip. left=5.
- Exit. Result: [1,2,3,4,5]. ✓

Without the guards, we'd visit 5 again in step 3.

**Connection to:**
- **Property-based testing:** Test degenerate cases.
- **QuickCheck:** Generate random matrices including edge cases.

### Insight 8: Connection to BFS

> Direction-based spiral is essentially BFS with a direction queue.

You can use a deque of directions: `[right, down, left, up]` and rotate.

**Connection to:**
- **BFS variants:** Wall-following, spiral, zigzag.
- **Pac-Man AI:** Same direction rotation.
- **Robotics:** Path planning patterns.

### Insight 9: Why This Problem Is Common

This problem tests:
1. **Boundary handling** — off-by-one mastery.
2. **Loop structure** — while loops with multiple conditions.
3. **Direction control** — state machine.
4. **Edge cases** — single row/col.

It's the "Hello World" of medium-difficulty matrix problems.

**Connection to:**
- **Teaching:** Used in algorithm courses.
- **Interview prep:** Universal medium-difficulty problem.
- **System design:** Boundary handling in distributed systems.

### Insight 10: Real-World Applications

| Application | Use |
|-------------|-----|
| **Image processing** | Spiral scanning for MRI, CT scans |
| **Data visualization** | Spiral plots (e.g., galaxy maps) |
| **Memory layout** | Spiral arrangement on tape/disk |
| **Antenna design** | Spiral antennas for RF |
| **DNA sequencing** | Cyclic patterns |
| **Crypto** | Some block ciphers use spiral |

**MRI scans use spiral trajectories** for faster imaging — k-space is filled in a spiral pattern!

---

## 🧪 TEST CASES

| Matrix | Expected | Note |
|--------|----------|------|
| `[[1,2,3],[4,5,6],[7,8,9]]` | `[1,2,3,6,9,8,7,4,5]` | Standard 3x3 |
| `[[1,2,3,4],[5,6,7,8],[9,10,11,12]]` | `[1,2,3,4,8,12,11,10,9,5,6,7]` | 3x4 |
| `[[1]]` | `[1]` | 1x1 |
| `[[1,2,3,4,5]]` | `[1,2,3,4,5]` | 1x5 |
| `[[1],[2],[3],[4]]` | `[1,2,3,4]` | 4x1 |
| `[[1,2],[3,4]]` | `[1,2,4,3]` | 2x2 |
| `[[1,2],[3,4],[5,6]]` | `[1,2,4,6,5,3]` | 3x2 |
| `[[1,2,3],[4,5,6]]` | `[1,2,3,6,5,4]` | 2x3 |
| `[[2,5],[8,4],[0,-1]]` | `[2,5,4,-1,0,8]` | With negatives |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Boundary shrinking** | **O(mn)** | **O(1)** | **✅ BEST** |
| Direction vectors | O(mn) | O(mn) | ✅ Educational |
| Pop + rotate | O(mn²) | O(mn) | ❌ Slow |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Spiral Matrix II (LC 59) | Inverse spiral (generate) | https://leetcode.com/problems/spiral-matrix-ii/ |
| Spiral Matrix III (LC 885) | Spiral on a grid | https://leetcode.com/problems/spiral-matrix-iii/ |
| Diagonal Traverse (LC 498) | Diagonal traversal | https://leetcode.com/problems/diagonal-traverse/ |
| Rotate Image (LC 48) | Matrix rotation | https://leetcode.com/problems/rotate-image/ |
| Spiral Matrix (LC 54) | **This problem** | https://leetcode.com/problems/spiral-matrix/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **Boundary shrinking** is the cleanest approach. Track `top, bottom, left, right`.
2. **Always guard steps 3 and 4** with `if top <= bottom` and `if left <= right`.
3. **Single row/col cases** are the most common bug source. Always test.
4. **The matrix has `ceil(min(m,n)/2)` layers** — each iteration peels off one layer.
5. **Direction vectors** are intuitive but use O(mn) space for visited set.
6. **The "pop and rotate" approach is O(mn²)** — avoid it.
7. **Boundary shrinking is the inverse** of spiral generation (Spiral Matrix II).
8. **Spiral is a space-filling curve** — same family as Hilbert, Moore curves.
9. **MRI uses spiral k-space trajectories** for faster imaging.
10. **Always test:** 1x1, 1xN, Nx1, single-row middle case.

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **MRI / CT scans** | Spiral k-space trajectories |
| **Space-filling curves** | Hilbert, Moore, Peano curves |
| **JPEG 2000** | Uses space-filling curves for locality |
| **Spatial databases** | Hilbert curves for indexing |
| **Image processing** | Edge handling, convolution |
| **Cache locality** | Spiral traversal has good locality |
| **Pac-Man AI** | Direction rotation |
| **Robotics** | Wall-following, path planning |
| **Block ciphers** | Some use spiral-like patterns |
| **Antenna design** | Spiral antennas |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive boundary shrinking in 60 seconds
- [x] Can code the 25-line solution in 90 seconds
- [x] Know the complexity: O(mn) time, O(1) space
- [x] Know the critical guards for steps 3 and 4
- [x] Can compare boundary shrinking vs direction vectors
- [x] Know the number of layers is `ceil(min(m,n)/2)`
- [x] Know the MRI / space-filling curve connection
- [x] Can list 5 real-world applications
- [x] Can generalize to Spiral Matrix II

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 10 minutes.
**Lines of code to write:** 25.
**Insight:** "Track top/bottom/left/right boundaries. Shrink after each direction. Guard steps 3-4 to avoid double-visits."
