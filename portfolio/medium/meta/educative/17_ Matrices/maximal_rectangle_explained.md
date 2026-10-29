# Maximal Rectangle — 0.0001% Expert Guide

> **LeetCode 85** | **Difficulty:** Hard | **Avg Solve Time:** 40 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/maximal-rectangle
> **Problem:** `maximalRectangle(matrix)` — area of largest all-1s rectangle.

---

## 📋 WHAT THE QUESTION ASKS

Given a binary matrix of 0s and 1s, find the area of the largest rectangle containing only 1s.

### Constraints
- `1 <= rows, cols <= 200`
- `matrix[i][j]` is `'0'` or `'1'`

### Examples
```
matrix=[
  [1,0,1,0,0],
  [1,0,1,1,1],
  [1,1,1,1,1],
  [1,0,0,1,0]
] -> 6   (rows 1-3, cols 2-3)
matrix=[[0,1],[1,0]] -> 1
matrix=[[1]] -> 1
matrix=[[0]] -> 0
matrix=[[1,1,1,1]] -> 4
```

### Why This Is "Hard"
- 2D histogram conversion.
- Monotonic stack per row.
- O(R*C) time and space.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (2 min)
> "Find largest axis-aligned rectangle of all 1s. Return area."

### Step 2: KEY INSIGHT — Histogram Conversion (5 min)
> "For each row, compute heights[j] = # consecutive 1s above (including current).
>
> Largest rectangle in the resulting histogram = answer ending at this row.
>
> Largest Rectangle in Histogram uses monotonic stack: O(C) per row."

### Step 3: Why Monotonic Stack (3 min)
> "Process heights left to right with sentinel 0 at end.
> For each i, pop while stack top > heights[i]. Each pop computes area.
> h = popped height, w = i - left_smaller - 1.
> O(n) amortized: each index pushed and popped once."

### Step 4: Algorithm (3 min)
```
1. heights = [0] * (C + 1)  # +1 sentinel.
2. For each row r:
     For c: heights[c] = heights[c]+1 if matrix[r][c]==1 else 0.
     stack = []
     For i in 0..C:
       while stack and heights[stack[-1]] > heights[i]:
         h = heights[stack.pop()]
         w = i if not stack else i - stack[-1] - 1
         best = max(best, h*w)
       stack.append(i)
3. Return best.
```

### Step 5: Edge Cases (2 min)
- Empty matrix: 0.
- Single cell: 0 or 1.
- All 1s: R*C.
- All 0s: 0.
- Single row: max consecutive 1s.

### Step 6: Code It (3 min)

```python
def maximalRectangle(matrix):
    if not matrix or not matrix[0]:
        return 0
    R, C = len(matrix), len(matrix[0])
    heights = [0] * (C + 1)
    best = 0
    for r in range(R):
        for c in range(C):
            v = matrix[r][c]
            heights[c] = heights[c] + 1 if (v == "1" or v == 1) else 0
        stack = []
        for i in range(C + 1):
            while stack and heights[stack[-1]] > heights[i]:
                h = heights[stack.pop()]
                w = i if not stack else i - stack[-1] - 1
                best = max(best, h * w)
            stack.append(i)
    return best
```

### Step 7: Verify (2 min)
For `[[1,0,1,0,0],[1,0,1,1,1],[1,1,1,1,1],[1,0,0,1,0]]`:
- After row 0: heights=[1,0,1,0,0,0] -> max rect = 1.
- After row 1: heights=[2,0,2,1,1,0] -> bar 2:1 alone =1; height 1 spans (3..4) = 1*2=2.
- After row 2: heights=[3,1,3,2,2,0] -> height 2 spans (3..4) = 2*2=4; height 1 spans (1..4) = 1*4=4.
- After row 3: heights=[4,0,0,3,0,0] -> height 4 at col 0 = 4; height 3 at col 3 = 3.
- Best = max(1, 2, 4, 4, 6, ...). The 6 comes from height 2 in row 2 spanning (2..4) = 2*3 = 6. ✓

### Step 8: Discuss Trade-offs (3 min)
> "Three approaches:
> 1. **Histogram + monotonic stack:** O(R*C) time, O(C) space. **BEST**.
> 2. **2D DP height/left/right:** O(R*C) time, O(C) space. Alternative.
> 3. **Brute force:** O(R^2 * C^2). Too slow for n=200.
>
> I'll use histogram + stack."

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need to find the largest rectangle of 1s in a binary matrix.

KEY INSIGHT: Histogram conversion.
- For each row, compute heights[j] = number of consecutive 1s above (incl. row).
- The largest rectangle of 1s ending at this row = largest rectangle
  in this histogram.

ALGORITHM:
1. heights = [0] * (C+1) sentinel.
2. For each row r:
     For c: heights[c] += 1 if matrix[r][c]=='1' else 0.
     Run monotonic-stack largest rect in histogram.
3. Return max area.

LARGEST RECT IN HISTOGRAM (monotonic stack):
- stack holds indices with increasing heights.
- For each i (0..C with sentinel 0):
    while stack top > heights[i]:
      h = popped height
      w = i if stack empty else i - stack.top - 1
      best = max(best, h*w)
    push i.

COMPLEXITY: O(R*C) time, O(C) space.

EDGE CASES:
- Empty matrix: 0.
- All 1s: R*C.
- All 0s: 0.

ALTERNATE: height/left/right 2D DP — track for each column the
leftmost and rightmost boundary where height is preserved.

RELATED:
- Largest Rectangle in Histogram (LC 84).
- Maximal Square (LC 221).
- Trapping Rain Water (LC 42).
"
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Histogram + Monotonic Stack (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | Histogram + stack | O(R*C) | O(C) | **THE ANSWER** |
| 7 | Stack clean | O(R*C) | O(C) | Educational |
| 9 | Sentinel stack | O(R*C) | O(C) | Educational |
| 11 | Stack from scratch | O(R*C) | O(C) | Educational |
| 15 | Stack sentinel explicit | O(R*C) | O(C) | Educational |
| 20 | Final cleanest | O(R*C) | O(C) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: 2D DP (Height/Left/Right)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 2 | 2D DP h/l/r | O(R*C) | O(C) | Educational |
| 6 | DP variant | O(R*C) | O(C) | Variant |
| 16 | Width + stack | O(R*C) | O(C) | Variant |

### 🟠 TIER 3: Specialized

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 3 | LRH helper | O(R*C) | O(C) | Modular |
| 4 | Two-pointer | O(R*C²) | O(C) | Educational |
| 8 | Class OOP | O(R*C) | O(C) | Reusable |
| 10 | Numpy | O(R*C) | O(C) | Vectorized |
| 12 | Char convert | O(R*C) | O(C) | Cleanup |
| 13 | Deque | O(R*C) | O(C) | Variant |
| 14 | D&C | O(R*C) | O(C) | Educational |
| 17 | Pre-compute heights | O(R*C) | O(R*C) | Variant |

### 🔵 TIER 4: Brute Force

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 5 | Brute rows | O(R²*C) | O(C) | Reference |
| 18 | Pure brute O(R²*C²) | O(R²*C²) | O(1) | Tiny n |
| 19 | Prefix sum brute | O(R²*C²) | O(R*C) | Reference |

---

## 💎 THE 13-LINE SOLUTION (Memorize!)

```python
def maximalRectangle(matrix):
    if not matrix or not matrix[0]:
        return 0
    R, C = len(matrix), len(matrix[0])
    heights = [0] * (C + 1)
    best = 0
    for r in range(R):
        for c in range(C):
            v = matrix[r][c]
            heights[c] = heights[c] + 1 if (v == "1" or v == 1) else 0
        stack = []
        for i in range(C + 1):
            while stack and heights[stack[-1]] > heights[i]:
                h = heights[stack.pop()]
                w = i if not stack else i - stack[-1] - 1
                best = max(best, h * w)
            stack.append(i)
    return best
```

**Time:** `O(R*C)`
**Space:** `O(C)`

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: 2D to 1D Reduction

> Reduce 2D rectangle problem to 1D histogram problem (per row).

**Connection to:**
- **Problem reduction:** Cross-dimension.
- **Reusable algorithms:** LC 84 → LC 85.

### Insight 2: Sentinel Trick

> Append 0 sentinel to heights. Forces stack to empty at end.

Without sentinel, last bar's area wouldn't be computed correctly.

**Connection to:**
- **Boundary handling:** Sentinel.
- **Common trick:** Standard pattern.

### Insight 3: Monotonic Stack = O(n) Histogram

> Each index pushed and popped at most once. O(n) total.

Naive: O(n²). Stack: O(n).

**Connection to:**
- **Amortized analysis:** O(n).
- **Stack patterns:** Standard.

### Insight 4: Why Iterate Per Row

> Each row's histogram = answer for ALL rectangles ending at this row.

If we miss row r, we miss rectangles with bottom at r.

**Connection to:**
- **Iteration order:** Row-based.
- **Completeness:** All positions.

### Insight 5: Width Calculation Logic

> `w = i if stack empty else i - stack[-1] - 1`.
> 
> Popped bar extends from one past previous smaller (or 0) to one before current smaller.

**Connection to:**
- **Index arithmetic:** Standard.
- **Boundary:** Off-by-one care.

### Insight 6: Connection to Trapping Rain Water

> Both use monotonic stack on bar heights. Different width semantics.

LC 42: water trapped. LC 84/85: rect areas.

**Connection to:**
- **Problem family:** Bar-height problems.
- **Reusable technique:** Stack.

### Insight 7: Real-World Applications

| Application | Use |
|-------------|-----|
| **Image processing** | Largest connected region |
| **PCB design** | Largest 1s block |
| **Memory allocation** | Largest contiguous block |
| **Data mining** | Dense submatrix |
| **Bioinformatics** | Sequence patterns |
| **OCR** | Character segmentation |

**Image processing** is canonical.

### Insight 8: Why Square-Only DP Fails

> Square DP (LC 221) gives SQUARE max area, not rectangle.
> E.g., 2x6 rectangle = 12 but max square = 4.

Use histogram stack for general rectangles.

**Connection to:**
- **Square vs rectangle:** Different problems.
- **Common mistake:** Confusion.

### Insight 9: Height/Left/Right 2D DP

> For each column, track consecutive 1s height.
> Left/right = bounds where height preserved.
> Area = height * (right - left).

**Connection to:**
- **DP state design:** Multiple vars.
- **Alternative:** Same complexity.

### Insight 10: Empty Row Edge Case

> If a row is all 0s, heights all reset. Stack handles naturally.

**Connection to:**
- **Robustness:** Handles all cases.
- **Initialization:** Sentinel works.

### Insight 11: Why C+1 Length Heights

> heights[C] = 0 sentinel. Without it, last bar wouldn't be popped.

**Connection to:**
- **Edge case:** Final cleanup.
- **Common pattern:** Always add sentinel.

### Insight 12: Char vs Int Matrix

> LeetCode uses chars ('0'/'1'), Educative uses ints (0/1).
> Handle both: `v == "1" or v == 1`.

**Connection to:**
- **Input flexibility:** Both formats.
- **Defensive coding:** Multiple types.

### Insight 13: Connection to Histogram Problems

> LC 84 (Largest Rectangle in Histogram) is the subroutine.
> LC 85 applies it per row.

**Connection to:**
- **Subroutine:** Reusable code.
- **Layered approach:** Compose.

### Insight 14: When 2D DP Wins

> If asked for rectangle area per row, 2D DP saves stack.

Both O(R*C). Pick by familiarity.

**Connection to:**
- **Multiple approaches:** Same complexity.
- **Style choice:** Pick one.

### Insight 15: Total Time O(R*C)

> O(R) rows × O(C) per row = O(R*C) total.

Even though we process R rows with O(C) stack work each.

**Connection to:**
- **Big-O analysis:** Nested work.
- **Loop counting:** Standard.

### Insight 16: Connection to Submatrix Sum

> 2D prefix sum helps for rectangle sum queries (not area max).

Different problem. Prefix sum doesn't directly help here.

**Connection to:**
- **Different problems:** Sum vs max.
- **Subproblem choice:** Histogram.

---

## 🧪 TEST CASES

| `matrix` | Expected | Note |
|----------|----------|------|
| `[[1,0,1,0,0],[1,0,1,1,1],[1,1,1,1,1],[1,0,0,1,0]]` | 6 | Standard |
| `[[0,1],[1,0]]` | 1 | Diagonal |
| `[[1]]` | 1 | Single |
| `[[0]]` | 0 | Single 0 |
| `[[1,1,1,1]]` | 4 | Single row |
| `[[1,1],[1,1]]` | 4 | 2x2 |
| `[[1,0,1,0,1,0,1,1]]` | 2 | End block |
| All 1s matrix 3x3 | 9 | Whole matrix |
| All 0s matrix 3x3 | 0 | No 1s |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Histogram + stack** | **O(R*C)** | **O(C)** | **✅ BEST** |
| 2D DP h/l/r | O(R*C) | O(C) | ✅ Alternative |
| Square DP (LC 221) | O(R*C) | O(R*C) | ❌ Squares only |
| Brute | O(R²*C²) | O(1) | ❌ Too slow |

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| Largest Rect in Histogram (LC 84) | Monotonic stack | https://leetcode.com/problems/largest-rectangle-in-histogram/ |
| Maximal Square (LC 221) | 2D DP | https://leetcode.com/problems/maximal-square/ |
| Trapping Rain Water (LC 42) | Monotonic stack | https://leetcode.com/problems/trapping-rain-water/ |
| Container With Most Water (LC 11) | Two pointers | https://leetcode.com/problems/container-with-most-water/ |
| Maximal Rectangle (LC 85) | **This problem** | https://leetcode.com/problems/maximal-rectangle/ |

---

## 🎓 EXPERT TAKEAWAYS

1. **2D → 1D** via histogram conversion.
2. **Monotonic stack** gives O(C) per row.
3. **Sentinel** ensures cleanup.
4. **width = i - stack.top - 1** when popping.
5. **Image processing** is canonical use case.
6. **LC 84 is the subroutine.**
7. **Square DP** doesn't work (rectangles ≠ squares).
8. **Total O(R*C)** time and space.
9. **Char vs int matrix**: handle both.
10. **Same stack pattern** as LC 42 (rain water).

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Image processing** | Largest connected region |
| **PCB design** | Largest 1s block |
| **Memory allocation** | Largest contiguous block |
| **Data mining** | Dense submatrix |
| **Bioinformatics** | Sequence patterns |
| **OCR** | Character segmentation |
| **Computer vision** | Region detection |
| **GIS** | Largest land block |
| **Sparse matrices** | Density regions |
| **ML features** | Max-pool regions |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive the histogram conversion in 90 seconds
- [x] Can code the 13-line solution in 90 seconds
- [x] Know complexity: O(R*C) time, O(C) space
- [x] Know monotonic stack logic
- [x] Know sentinel purpose
- [x] Know width calculation: `i - stack.top - 1`
- [x] Know related problems (LC 84, 221, 42)
- [x] Know why square DP fails for rectangles
- [x] Can list 5 real-world applications

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 15 minutes.
**Lines of code to write:** 13.
**Insight:** "Histogram conversion + monotonic stack. Sentinel 0 at end. width = i - stack.top - 1 when popping."
