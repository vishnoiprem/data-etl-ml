# Remove Element — 0.0001% Expert Guide

> **LeetCode 27** | **Difficulty:** Easy | **Avg Solve Time:** 15 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/remove-element
> **Problem:** `removeElement(nums, val)` — remove all occurrences of val in-place.

---

## 📋 WHAT THE QUESTION ASKS

Given an integer array `nums` and an integer `val`, remove **all occurrences** of `val` in `nums` **in-place**. The order of elements may be changed. Return the number of elements in `nums` which are **not equal to val**.

### Constraints
- `0 <= nums.length <= 100`
- `0 <= nums[i] <= 50`
- `0 <= val <= 100`

### Examples
```
nums=[3,2,2,3], val=3               -> 2, nums=[2,2,_,_]
nums=[0,1,2,2,3,0,4,2], val=2        -> 5, nums=[0,1,3,0,4,_,_,_]
nums=[], val=1                        -> 0, nums=[]
nums=[1], val=1                       -> 0, nums=[]
nums=[2,2,2], val=2                   -> 0, nums=[_,_,_]
nums=[1,2,3,4], val=5                 -> 4, nums=[1,2,3,4]
```

### Why This Is "Easy"
- Classic two-pointer pattern (read-write).
- O(n) time, O(1) space.
- Foundation for array filtering problems.

---

## 🧠 HOW TO THINK — STEP BY STEP

### Step 1: Understand the Problem
> "Remove all occurrences of val. Return count of remaining elements.
> Order may change. Don't care about positions beyond returned count."

### Step 2: Key Insight — Don't Delete, Overwrite
> "We don't need to actually DELETE elements — just overwrite 'kept' elements
> to the front. Elements beyond returned index can be anything."

### Step 3: Two-Pointer Pattern (Read-Write)
> "Walk through nums with one pointer (read).
> Use another pointer (write) to track where the next 'kept' element goes.
> When nums[i] != val: copy to nums[j], advance j."

### Step 4: Algorithm
```
1. j = 0 (write pointer).
2. For i in 0..len(nums)-1:
     if nums[i] != val:
         nums[j] = nums[i]
         j += 1.
3. Return j.
```

### Step 5: Why This Works
> "All non-val elements are moved forward in their original relative order.
> val elements are skipped. Beyond j, the array is 'garbage' but allowed."

### Step 6: Edge Cases
- Empty array: return 0.
- All elements equal val: return 0.
- No element equals val: return len(nums).
- Single element: trivial.

### Step 7: Code It
```python
def removeElement(nums, val):
    j = 0
    for i in range(len(nums)):
        if nums[i] != val:
            nums[j] = nums[i]
            j += 1
    return j
```

### Step 8: Verify
For nums=[3,2,2,3], val=3:
- i=0, nums[0]=3==val: skip.
- i=1, nums[1]=2!=val: nums[0]=2, j=1.
- i=2, nums[2]=2!=val: nums[1]=2, j=2.
- i=3, nums[3]=3==val: skip.
- Return j=2, nums=[2,2,2,3]. ✓

### Step 9: Trade-offs
- Two-pointer (read-write): O(n) time, O(1) space. **BEST**.
- Two-pointer swap with end: O(n) time, O(1) space, doesn't preserve order.
- New array: O(n) time, O(n) space.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT

```
"I need to remove all occurrences of val in-place and return new length."

KEY INSIGHT: Don't actually delete — overwrite. Read-write two pointers.
i reads each element. j tracks position to write 'kept' element.
Skip elements equal to val, copy others forward.

ALGORITHM:
1. j = 0.
2. For i in 0..n-1:
     if nums[i] != val:
         nums[j] = nums[i]
         j += 1.
3. Return j.

COMPLEXITY: O(n) time, O(1) space.

EDGE CASES:
- Empty: return 0.
- All val: return 0.
- None val: return n.

WHY IN-PLACE:
- We only need first j elements to be valid.
- Beyond j, the array contents don't matter.

ALTERNATE: Two-pointer from both ends (swap-with-end). Doesn't preserve order
but works when order doesn't matter.

RELATED:
- Remove Duplicates (LC 26) — same two-pointer pattern.
- Move Zeroes (LC 283) — keep zeros at end.
- Filter arrays in-place.
"""
```

---

## 💎 THE 5-LINE SOLUTION (Memorize!)

```python
def removeElement(nums, val):
    j = 0
    for i in range(len(nums)):
        if nums[i] != val:
            nums[j] = nums[i]
            j += 1
    return j
```

**Time:** `O(n)` | **Space:** `O(1)`

---

## 🤖 KEY INSIGHTS

1. **Don't delete, overwrite** — elements beyond new length are ignored.
2. **Read-write two pointers** — i reads, j writes.
3. **Skip val elements**, copy others.
4. **Preserves relative order** of kept elements (stable filter).
5. **O(n) single pass** — touch each element once.
6. **O(1) extra space** — in-place.
7. **Counter counts** — returned length, not array size.
8. **Order doesn't have to match** — only kept-element order stable.
9. **`list.remove()` works** but is O(n) per call = O(n²) total.
10. **`pop(index)` similar** — O(n) per pop.

---

## 🧪 TEST CASES

| `nums` | `val` | `k` | Note |
|--------|-------|-----|------|
| `[3,2,2,3]` | `3` | `2` | Standard |
| `[0,1,2,2,3,0,4,2]` | `2` | `5` | Multiple vals |
| `[]` | `1` | `0` | Empty |
| `[1]` | `1` | `0` | Single match |
| `[1]` | `2` | `1` | Single non-match |
| `[2,2,2]` | `2` | `0` | All val |
| `[1,2,3,4]` | `5` | `4` | No match |
| `[1,1,1,1]` | `1` | `0` | All match |
| `[4,5]` | `4` | `1` | First match |
| `[3,3]` | `5` | `2` | All kept |

---

## 📊 COMPLEXITY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Two-pointer (read-write)** | **O(n)** | **O(1)** | **✅ BEST** |
| Two-pointer swap with end | O(n) | O(1) | ✅ Alternative |
| List comprehension | O(n) | O(n) | ⚠️ Extra space |
| `list.remove()` in loop | O(n²) | O(1) | ❌ Slow |
| New array copy | O(n) | O(n) | ❌ Extra space |

---

## 🔗 RELATED

- Remove Duplicates (LC 26)
- Move Zeroes (LC 283)
- Array filtering in-place
- Two-pointer read-write pattern

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Insight:** "Read-write two pointers. Skip val, copy others forward. Return j as new count. O(n) time, O(1) space."
