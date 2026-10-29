# Pascal's Triangle

## Problem
Generate the first `numRows` of Pascal's Triangle. Row `i` has `i+1`
elements. The first and last elements of each row are `1`; interior
elements are the sum of the two elements directly above from the
previous row.

## Approach: Iterative Construction

### Algorithm
For each row `i` from 0 to `numRows - 1`:
1. Initialize row with `i + 1` ones.
2. Fill interior entries:
   `row[j] = prev_row[j-1] + prev_row[j]` for `j = 1, ..., i-1`.

### Implementation
```python
triangle = []
for i in range(numRows):
    row = [1] * (i + 1)
    for j in range(1, i):
        row[j] = triangle[i - 1][j - 1] + triangle[i - 1][j]
    triangle.append(row)
```

## Walkthrough: `numRows = 5`

```
Row 0: [1]
Row 1: [1, 1]
Row 2: [1, 2, 1]                   (1+1 = 2)
Row 3: [1, 3, 3, 1]                (1+2=3, 2+1=3)
Row 4: [1, 4, 6, 4, 1]             (1+3=4, 3+3=6, 3+1=4)
```

## Complexity
- **Time:** `O(numRows²)` — total cells is `1+2+...+numRows` ≈ `numRows²/2`
- **Space:** `O(numRows²)` for the triangle + `O(numRows)` for current row

## Edge Cases
- `numRows = 0` → `[]`
- `numRows = 1` → `[[1]]`
- Large `numRows` → values can grow large but Python handles big ints natively
