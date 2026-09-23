# Merge Sorted Array — 0.0001% Expert Guide

> **LeetCode 88** | **Difficulty:** Easy | **Avg Solve Time:** 15 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/merge-sorted-array
> **Problem:** Merge nums2 into nums1 in-place, sorted.

---

## 📋 WHAT THE QUESTION ASKS

Given two sorted integer arrays `nums1` and `nums2`, merge `nums2` into `nums1` so that the result is sorted. The first `m` elements of `nums1` are valid; the last `n` are zeros (placeholders). `nums2` has length `n`.

Must be **in-place** in `nums1`.

### Constraints
- `0 <= m, n <= 200`
- `1 <= m + n <= 200`
- `nums1.length == m + n`
- `nums2.length == n`
- Sorted in non-decreasing order.

### Examples
```
nums1=[1,2,3,0,0,0], m=3, nums2=[2,5,6], n=3  -> [1,2,2,3,5,6]
nums1=[1], m=1, nums2=[], n=0                  -> [1]
nums1=[0], m=0, nums2=[1], n=1                 -> [1]
nums1=[4,5,6,0,0,0], m=3, nums2=[1,2,3], n=3   -> [1,2,3,4,5,6]
```

### Why This Is "Easy"
- Classic three-pointer from end.
- O(m+n) time, O(1) space.
- Foundation for merge sort and K-way merge.

---

## 🧠 HOW TO THINK — STEP BY STEP

### Step 1: Understand the Problem
> "Merge nums2 into nums1's empty slots, in-place, sorted."

### Step 2: Key Insight — Merge from the Back
> "If we merge from the FRONT, we'd overwrite nums1's valid data.
> The END of nums1 has empty slots — perfect for placing the LARGEST elements first."

### Step 3: Three-Pointer Technique
> "p1 = m-1: walks nums1's valid region backward.
>  p2 = n-1: walks nums2 backward.
>  p = m+n-1: write position in nums1's full length."

### Step 4: Algorithm
```
1. p1, p2, p = m-1, n-1, m+n-1.
2. While p1 >= 0 and p2 >= 0:
     if nums1[p1] > nums2[p2]: nums1[p] = nums1[p1]; p1--.
     else: nums1[p] = nums2[p2]; p2--.
     p--.
3. Drain remaining nums2 to nums1[p..0].
4. (If p1 has remaining, they're already in place.)
```

### Step 5: Why Backward Merge Works
> "The end of nums1 has empty slots (zeros).
> We fill them with the largest remaining elements first.
> This never disturbs unprocessed data at the front of nums1."

### Step 6: Edge Cases
- nums2 empty: nums1 unchanged.
- m=0: just copy nums2.
- nums1 fully consumed (p1 < 0): copy remaining nums2.
- nums2 fully consumed (p2 < 0): nums1's remaining stays.

### Step 7: Code It
```python
def merge(nums1, m, nums2, n):
    p1, p2, p = m - 1, n - 1, m + n - 1
    while p1 >= 0 and p2 >= 0:
        if nums1[p1] > nums2[p2]:
            nums1[p] = nums1[p1]
            p1 -= 1
        else:
            nums1[p] = nums2[p2]
            p2 -= 1
        p -= 1
    nums1[:p2 + 1] = nums2[:p2 + 1]
    return nums1
```

### Step 8: Verify
For nums1=[1,2,3,0,0,0], m=3, nums2=[2,5,6]:
- p1=2 (val=3), p2=2 (val=6), p=5. 6>3, place 6. p2=1, p=4.
- p1=2 (val=3), p2=1 (val=5), p=4. 5>3, place 5. p2=0, p=3.
- p1=2 (val=3), p2=0 (val=2), p=3. 3>2, place 3. p1=1, p=2.
- p1=1 (val=2), p2=0 (val=2), p=2. 2=2, place 2. p2=-1, p=1.
- p2=-1, exit loop. nums1[:0] = nums2[:0] = []. ✓
- Result: [1,2,2,3,5,6]. ✓

### Step 9: Trade-offs
- 3-ptr from end: O(m+n) time, O(1) space. **BEST**.
- New array: O(m+n) time, O(m+n) space.
- Sort after append: O((m+n) log(m+n)) time.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT

```
"I need to merge nums2 into nums1 in-place."

KEY INSIGHT: Merge from the BACK. The end of nums1 has empty slots,
so we can place the LARGEST elements there without overwriting
unprocessed data.

ALGORITHM:
1. Three pointers: p1 (nums1 valid end), p2 (nums2 end), p (write).
2. While both have elements:
     Place max(nums1[p1], nums2[p2]) at nums1[p].
     Move pointers backward.
3. Copy remaining nums2 (if any) to nums1's front.

COMPLEXITY: O(m+n) time, O(1) space.

EDGE CASES:
- Empty nums2: no-op.
- Empty nums1 (m=0): just copy nums2.
- nums1 fully consumed: copy remaining nums2.

WHY BACKWARD:
- Front merge would overwrite nums1's data.
- Backward fills empty slots with largest values first.

WHY O(1) SPACE:
- Only constant extra variables.
- All merging happens in nums1.

RELATED:
- Merge Sort (uses this technique recursively)
- Merge K Sorted Lists (LC 23) — K-way generalization
- Sorted merge in linked lists
"""
```

---

## 💎 THE 8-LINE SOLUTION (Memorize!)

```python
def merge(nums1, m, nums2, n):
    p1, p2, p = m - 1, n - 1, m + n - 1
    while p1 >= 0 and p2 >= 0:
        if nums1[p1] > nums2[p2]:
            nums1[p] = nums1[p1]; p1 -= 1
        else:
            nums1[p] = nums2[p2]; p2 -= 1
        p -= 1
    nums1[:p2 + 1] = nums2[:p2 + 1]
    return nums1
```

**Time:** `O(m+n)` | **Space:** `O(1)`

---

## 🤖 KEY INSIGHTS

1. **Three pointers** — p1 (nums1), p2 (nums2), p (write).
2. **Merge from back** — fills empty slots without overwriting.
3. **O(m+n) single pass** — touch each element once.
4. **O(1) space** — in-place.
5. **Drain remaining** — only need to drain nums2 (nums1 stays in place).
6. **Stable in spirit** — preserves relative order from both arrays.
7. **Foundation of merge sort** — recursive split + merge.
8. **Generalizes to K-way** — use a min-heap of size K.
9. **`heapq.merge`** — Python's built-in streaming merge.
10. **Sort + append** — works but O(n log n).

---

## 🧪 TEST CASES

| nums1 | m | nums2 | n | Expected | Note |
|-------|---|-------|---|----------|------|
| `[1,2,3,0,0,0]` | 3 | `[2,5,6]` | 3 | `[1,2,2,3,5,6]` | Standard |
| `[1]` | 1 | `[]` | 0 | `[1]` | Empty nums2 |
| `[0]` | 0 | `[1]` | 1 | `[1]` | Empty nums1 |
| `[4,5,6,0,0,0]` | 3 | `[1,2,3]` | 3 | `[1,2,3,4,5,6]` | Reversed |
| `[1,2,3,0,0,0,0]` | 3 | `[4,5,6,7]` | 4 | `[1,2,3,4,5,6,7]` | Larger nums2 |
| `[2,0]` | 1 | `[1]` | 1 | `[1,2]` | Single merge |
| `[-1,0,0,3,3,3,0,0]` | 6 | `[1,2]` | 2 | `[-1,0,0,1,2,3,3,3]` | Negatives |

---

## 📊 COMPLEXITY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **3-ptr backward** | **O(m+n)** | **O(1)** | **✅ BEST** |
| New array | O(m+n) | O(m+n) | ❌ Extra space |
| Append + sort | O((m+n) log(m+n)) | O(1) | ❌ Slower |
| heapq.merge | O(m+n) | O(m+n) | ⚠️ Inefficient here |

---

## 🔗 RELATED

- Merge Sort
- Merge K Sorted Lists (LC 23) — K-way
- Kth Smallest in M Sorted Lists — K-way + heap
- Sorted merge in linked lists

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Insight:** "Three pointers from the end. Place largest at nums1[p] working backward. O(m+n) time, O(1) space."
