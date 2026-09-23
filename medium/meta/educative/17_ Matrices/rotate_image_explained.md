# Rotate Image — 0.0001% Expert Guide

> **LeetCode 48** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/rotate-image
> **Problem:** `rotate(matrix)` — rotate an n×n matrix 90° clockwise in place

---

## 📋 WHAT THE QUESTION ASKS

Given an `n×n` 2D matrix representing an image, rotate it by **90 degrees clockwise**, in place.

### Constraints
- `n == matrix.length == matrix[i].length`
- `1 <= n <= 200`
- `-1000 <= matrix[i][j] <= 1000`

### Example

```
Input: [[1,2,3],
        [4,5,6],
        [7,8,9]]

Output: [[7,4,1],
         [8,5,2],
         [9,6,3]]
```

### Why This Is "Medium"
- Requires understanding of matrix transposition.
- In-place rotation is trickier than using extra space.
- The "transpose + reverse" trick is elegant but not obvious.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Rotate an n×n matrix 90° clockwise, in place."

### Step 2: Identify the Algorithm (3 min)
> "Three approaches:
> 1. **Transpose + reverse:** transpose the matrix, then reverse each row. O(1) extra space.
> 2. **Rotate layer by layer:** swap 4 cells at a time for each ring. O(1) extra space.
> 3. **New matrix:** build a new rotated matrix. O(n²) extra space.

> Best: Transpose + reverse. Cleanest."

### Step 3: Why Transpose + Reverse Works (3 min)
> "Rotating 90° clockwise = transpose + reverse each row.
> - Transpose: swap (r, c) with (c, r).
> - Reverse: flip each row.
> 
> This works because rotating clockwise moves the top row to the right column."

### Step 4: Layer-by-Layer Alternative (3 min)
> "For each ring (outer, inner, etc.):
> - For each cell in the top row of the ring, swap with 3 other cells (right, bottom, left).
> - 4-way swap pattern.

> More complex but useful when you can't transpose."

### Step 5: Edge Cases (2 min)
- 1x1: unchanged.
- 2x2: just transpose and reverse.

### Step 6: Code It — Transpose + Reverse (5 min)

```python
def rotate(matrix):
    n = len(matrix)
    # Transpose
    for r in range(n):
        for c in range(r + 1, n):
            matrix[r][c], matrix[c][r] = matrix[c][r], matrix[r][c]
    # Reverse each row
    for r in range(n):
        matrix[r].reverse()
```

### Step 7: Code It — Layer by Layer (5 min)

```python
def rotate(matrix):
    n = len(matrix)
    for layer in range(n // 2):
        first, last = layer, n - 1 - layer
        for i in range(first, last):
            offset = i - first
            top = matrix[first][i]
            # left → top
            matrix[first][i] = matrix[last - offset][first]
            # bottom → left
            matrix[last - offset][first] = matrix[last][last - offset]
            # right → bottom
            matrix[last][last - offset] = matrix[i][last]
            # top → right
            matrix[i][last] = top
```

### Step 8: Verify with Example (2 min)
For 3x3 `[[1,2,3],[4,5,6],[7,8,9]]`:
- Transpose: `[[1,4,7],[2,5,8],[3,6,9]]`.
- Reverse each row: `[[7,4,1],[8,5,2],[9,6,3]]`. ✓

### Step 9: Discuss Trade-offs (5 min)
> "Three approaches:
> 1. **Transpose + reverse:** O(n²) time, O(1) space. **Cleanest.**
> 2. **Layer-by-layer:** O(n²) time, O(1) space. More complex.
> 3. **New matrix:** O(n²) time, O(n²) space. Easy but uses memory.

> I'll use transpose + reverse."

### Step 10: Final Clean Code (5 min)
Memorize the 8-line solution.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to rotate an n×n matrix 90° clockwise, in place.

KEY INSIGHT: 90° clockwise rotation = TRANSPOSE + REVERSE EACH ROW.
- Transpose: swap (r, c) with (c, r).
- Reverse: flip each row.

ALGORITHM:
1. For r in range(n):
   For c in range(r+1, n):
       swap matrix[r][c] and matrix[c][r]
2. For r in range(n):
       reverse matrix[r]

COMPLEXITY: O(n²) time, O(1) extra space.

ALTERNATIVE: Layer-by-layer rotation. For each ring, do a 4-way swap.

EDGE CASES: 1x1 unchanged. 2x2 just transpose."
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Transpose + Reverse (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | Transpose + reverse (BEST) | O(n²) | O(1) | **THE ANSWER** |
| 2 | Verbose | O(n²) | O(1) | Educational |
| 8 | One-liner | O(n²) | O(1) | Pythonic |
| 10 | Transpose + zip reverse | O(n²) | O(1) | Pythonic |
| 12 | Most concise | O(n²) | O(1) | One-liner |
| 19 | One-liner | O(n²) | O(1) | Variant |
| 20 | Final cleanest | O(n²) | O(1) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: Layer-by-Layer

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 3 | Layer-by-layer 4-swap | O(n²) | O(1) | Educational |
| 4 | With offset | O(n²) | O(1) | Variant |
| 11 | Ring traversal | O(n²) | O(1) | Variant |

### 🟣 TIER 3: Extra Space

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 5 | New matrix | O(n²) | O(n²) | Easy |
| 6 | Numpy rot90 | O(n²) | O(n²) | Fast in practice |
| 7 | Numpy transpose | O(n²) | O(n²) | Variant |
| 9 | Functional zip | O(n²) | O(n²) | Functional |
| 13 | Itertools | O(n²) | O(n²) | Functional |
| 17 | With helpers | O(n²) | O(n²) | Readable |
| 18 | Numpy k=1 | O(n²) | O(n²) | Variant |

### ⚪ TIER 4: Specialized

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 14 | Recursive | O(n²) | O(log n) | Educational |
| 15 | Class OOP | O(n²) | O(1) | Reusable |
| 16 | Generator | O(n²) | O(1) | Pythonic |

---

## 💎 THE 8-LINE SOLUTION (Memorize!)

```python
def rotate(matrix):
    n = len(matrix)
    # Transpose
    for r in range(n):
        for c in range(r + 1, n):
            matrix[r][c], matrix[c][r] = matrix[c][r], matrix[r][c]
    # Reverse each row
    for r in range(n):
        matrix[r].reverse()
```

**Time:** `O(n²)`
**Space:** `O(1)` (in-place)

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Transpose is the Foundation

> A matrix transpose swaps row index with column index: `(r, c) → (c, r)`.

This is the **most fundamental matrix operation**. Rotate 90° is built on it.

**Connection to:**
- **Linear algebra:** Transpose matrix Aᵀ.
- **Symmetric matrices:** S = Aᵀ = A.
- **Strassen's algorithm:** Uses transpose for fast multiplication.

### Insight 2: Why Transpose + Reverse = Rotate 90° CW

> Take a cell `(r, c)`. After transpose: `(c, r)`. After row reverse: `(c, n-1-r)`.

So `(r, c) → (c, n-1-r)`. This is exactly 90° CW rotation.

**Connection to:**
- **Coordinate transforms:** Rotation matrices.
- **Computer graphics:** 2D/3D rotations.
- **Physics:** Frame transformations.

### Insight 3: Layer-by-Layer Approach

> An n×n matrix has `n // 2` "rings" (layers). Each ring is a square border.

For each ring, swap 4 cells in a cycle. Move 4 elements in 4 swaps = 0 extra space.

**Connection to:**
- **Cache-oblivious algorithms:** Block decomposition.
- **Sparse matrices:** Block matrix operations.
- **Convolutional networks:** Same structure.

### Insight 4: Rotation Matrix in Linear Algebra

> The 2D rotation matrix is `[[cos θ, -sin θ], [sin θ, cos θ]]`.

For θ = 90°: `[[0, -1], [1, 0]]`. Applying this to each cell gives the rotation.

But in-place rotation needs **discrete swaps**, not matrix multiplication.

**Connection to:**
- **Computer graphics:** OpenGL, DirectX use rotation matrices.
- **Robotics:** Forward kinematics.
- **Quantum computing:** Qubit rotations.

### Insight 5: Why In-Place is Hard

> A naive rotation creates a new matrix. In-place requires careful tracking.

The transpose is in-place (one swap per pair). Reverse is in-place. Together, O(1) extra space.

**Connection to:**
- **In-place algorithms:** Always consider the data structure.
- **Memory constraints:** Embedded systems.
- **Streaming:** When you can't buffer.

### Insight 6: Generalization to k×90° Rotations

> 90° CW = transpose + reverse.
> 180° = reverse rows + reverse columns (or just reverse all).
> 270° CW = reverse + transpose.
> 90° CCW = reverse + transpose (CW) = transpose + reverse (CCW).

**Connection to:**
- **Group theory:** Rotations form a cyclic group of order 4.
- **Crystallography:** 90° rotations are symmetry operations.
- **Image processing:** All rotations needed.

### Insight 7: Connection to Image Processing

> Image rotation in OpenCV/PIL uses similar tricks.

But for non-square images, you need to crop or pad, since 90° rotates change dimensions.

**Connection to:**
- **EXIF orientation:** Images stored with rotation metadata.
- **TensorFlow image ops:** `tf.image.rot90`.
- **Photo apps:** Rotate buttons.

### Insight 8: Real-World Applications

| Application | Use |
|-------------|-----|
| **Image processing** | Rotate photos |
| **Computer graphics** | 2D game rotations |
| **Display drivers** | Screen orientation |
| **Printers** | Page rotation |
| **Robotics** | Coordinate frame transforms |
| **Crystallography** | Molecular structure |
| **Game development** | Sprite rotation |
| **Map rendering** | Tile rotation |

**Smartphone rotation** uses similar logic. The OS rotates the framebuffer.

### Insight 9: Connection to Bit Manipulation

> Both transpose and reverse are O(1) extra space. Both work on the data structure itself.

**Connection to:**
- **Game of Life:** Bit encoding.
- **Set Matrix Zeroes:** First row/col markers.
- **In-place string reversal:** Two-pointer.

### Insight 10: Why This Is Interview Favorite

This problem tests:
1. **Matrix operations** — transpose, reverse.
2. **In-place algorithms** — O(1) extra space.
3. **Spatial reasoning** — visualize the rotation.
4. **Multiple solutions** — transpose+reverse vs layer-by-layer.

**Connection to:**
- **Teaching:** Used in algorithms courses.
- **Interview prep:** Universal medium-difficulty problem.
- **Spatial reasoning:** Important in robotics, graphics.

---

## 🧪 TEST CASES

| Matrix | Expected | Note |
|--------|----------|------|
| `[[1,2,3],[4,5,6],[7,8,9]]` | `[[7,4,1],[8,5,2],[9,6,3]]` | Standard 3x3 |
| `[[1,2],[3,4]]` | `[[3,1],[4,2]]` | 2x2 |
| `[[1]]` | `[[1]]` | 1x1 |
| `[[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]]` | 4x4 rotated | Standard |
| 5x5 | rotated 5x5 | General |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Transpose + reverse** | **O(n²)** | **O(1)** | **✅ BEST** |
| Layer-by-layer | O(n²) | O(1) | ✅ Alternative |
| New matrix | O(n²) | O(n²) | ✅ Easy |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Spiral Matrix (LC 54) | Boundary shrinking | https://leetcode.com/problems/spiral-matrix/ |
| Set Matrix Zeroes (LC 73) | First row/col markers | https://leetcode.com/problems/set-matrix-zeroes/ |
| Transpose Matrix (LC 867) | Swap indices | https://leetcode.com/problems/transpose-matrix/ |
| Rotate Image (LC 48) | **This problem** | https://leetcode.com/problems/rotate-image/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **90° CW = transpose + reverse each row.** Memorize this.
2. **Transpose swaps (r, c) with (c, r).** Only iterate `c > r` to avoid double-swap.
3. **Layer-by-layer** is an alternative — 4-way swap for each ring.
4. **O(1) extra space** is achievable — don't allocate a new matrix.
5. **Generalizes to k×90°** — group of order 4.
6. **Rotation matrix** in linear algebra is `[[0,-1],[1,0]]` for 90° CW.
7. **Image rotation in OpenCV/PIL** uses similar tricks.
8. **Connection to robotics, graphics, crystallography.**
9. **Test cases:** 1x1, 2x2, 3x3, 4x4.
10. **The transpose + reverse is THE interview answer.**

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Image processing** | Rotate photos, EXIF orientation |
| **Computer graphics** | 2D game rotations |
| **Linear algebra** | Rotation matrices, transpose |
| **Robotics** | Coordinate frame transforms |
| **Crystallography** | Molecular symmetry |
| **Display drivers** | Screen orientation |
| **Game development** | Sprite rotation |
| **Map rendering** | Tile rotation |
| **Quantum computing** | Qubit rotations |
| **Convolutional networks** | Filter rotations |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive transpose + reverse in 60 seconds
- [x] Can code the 8-line solution in 90 seconds
- [x] Know the complexity: O(n²) time, O(1) space
- [x] Know the layer-by-layer alternative
- [x] Know the rotation matrix in linear algebra
- [x] Know how to generalize to k×90° rotations
- [x] Can list 5 real-world applications
- [x] Can explain why in-place is non-trivial
- [x] Can compare with the 3 main approaches

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 8 minutes.
**Lines of code to write:** 8 (transpose + reverse).
**Insight:** "90° CW rotation = transpose + reverse each row. In-place, O(1) extra space."