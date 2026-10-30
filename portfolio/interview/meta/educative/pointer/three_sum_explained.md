# 3Sum — 0.0001% Expert Guide

> **LeetCode 15** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/3sum
> **Problem:** `threeSum(nums)` — find all unique triplets summing to zero.

---

## 📋 WHAT THE QUESTION ASKS

Given an integer array `nums`, return all the triplets `[nums[i], nums[j], nums[k]]` such that `i != j`, `i != k`, and `j != k`, and `nums[i] + nums[j] + nums[k] == 0`.

The solution set **must not contain duplicate triplets**.

### Constraints
- `3 <= nums.length <= 3000`
- `-10^5 <= nums[i] <= 10^5`

### Examples
```
[-1,0,1,2,-1,-4]   -> [[-1,-1,2],[-1,0,1]]
[0,1,1]            -> []
[0,0,0]            -> [[0,0,0]]
```

### Why This Is "Medium"
- Sort + two-pointer trick.
- Duplicate avoidance is the tricky part.
- O(n²) time, O(1) extra space (best).

---

## 🧠 HOW TO THINK — STEP BY STEP

### Step 1: Understand the Problem
> "Find all unique triplets summing to 0. No duplicates in output."

### Step 2: Key Insight — Sort + Fix One Element
> "If we SORT nums, we can:
> - Fix element i.
> - Find pairs (j, k) with j < k where nums[j] + nums[k] == -nums[i].
> - This is the classic 2-sum problem on the remaining sorted subarray."

### Step 3: Two-Pointer for 2-Sum
> "For each i:
> - left = i+1, right = n-1.
> - While left < right:
>     sum = nums[i] + nums[left] + nums[right].
>     If sum == 0: record, advance left/right past duplicates.
>     If sum < 0: left++.
>     If sum > 0: right--."

### Step 4: Algorithm
```
1. Sort nums.
2. result = [].
3. For i in 0..n-3:
     Skip duplicate i (if nums[i] == nums[i-1], continue).
     left, right = i+1, n-1.
     While left < right:
       sum = nums[i] + nums[left] + nums[right].
       If sum == 0: result.append([nums[i], nums[left], nums[right]]);
                    Skip duplicate left and right; left++; right--.
       Elif sum < 0: left++.
       Else: right--.
4. Return result.
```

### Step 5: Why Sort + Two Pointer = Best
> "Sort enables two-pointer 2-sum (O(n) per i).
> Total O(n²) time. Duplicates are easy to skip in sorted array.
> No extra hash table needed."

### Step 6: Edge Cases
- All same number (e.g., [0,0,0]): one triplet [0,0,0].
- No valid triplet: empty result.
- Many duplicates: careful skipping.

### Step 7: Code It
```python
def threeSum(nums):
    nums.sort()
    n = len(nums)
    result = []
    for i in range(n - 2):
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        left, right = i + 1, n - 1
        while left < right:
            s = nums[i] + nums[left] + nums[right]
            if s == 0:
                result.append([nums[i], nums[left], nums[right]])
                while left < right and nums[left] == nums[left + 1]:
                    left += 1
                while left < right and nums[right] == nums[right - 1]:
                    right -= 1
                left += 1
                right -= 1
            elif s < 0:
                left += 1
            else:
                right -= 1
    return result
```

### Step 8: Verify
For [-1,0,1,2,-1,-4]:
- Sort: [-4,-1,-1,0,1,2].
- i=0 (val=-4): no two-sum pair.
- i=1 (val=-1): find pair summing to 1.
  - left=2(-1), right=5(2). sum=0! Add [-1,-1,2]. left=3, right=4.
  - left=3(0), right=4(1). sum=0! Add [-1,0,1]. left=4, right=3. Done.
- i=2 (val=-1): skip (duplicate).
- i=3 (val=0): no two-sum pair.
- Result: [[-1,-1,2], [-1,0,1]]. ✓

### Step 9: Trade-offs
- Sort + two-pointer: O(n²) time, O(1) extra. **BEST**.
- Hash set per i: O(n²) time, O(n) extra.
- Brute force: O(n³) time.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT

```
"I need to find all unique triplets summing to 0."

KEY INSIGHT: Sort + fix one element + two-pointer 2-sum on the rest.
Sorting enables two-pointer for the remaining pair (O(n) per i).
Total O(n²) time.

ALGORITHM:
1. Sort nums.
2. For i in 0..n-3:
     Skip if nums[i] == nums[i-1] (avoid duplicate triplets).
     Two-pointer find pairs summing to -nums[i] in nums[i+1..n-1].
     After adding triplet, skip duplicate left/right.
3. Return result.

COMPLEXITY: O(n²) time, O(1) extra space.

EDGE CASES:
- All same: one triplet.
- No triplet: empty.
- Many duplicates: skip carefully.

WHY SORT:
- Two-pointer works only on sorted.
- Easy to skip duplicates.
- 2-sum reduces to linear scan.

WHY SKIP DUPLICATES:
- After adding triplet, advance left past all equal nums[left].
- Similarly for right.

VARIANT: 4Sum (LC 18) — recursive k-sum pattern.

RELATED:
- 2Sum (LC 1)
- 3Sum Closest (LC 16)
- 4Sum (LC 18)
- k-Sum family
"""
```

---

## 💎 THE 12-LINE SOLUTION (Memorize!)

```python
def threeSum(nums):
    nums.sort()
    n = len(nums)
    result = []
    for i in range(n - 2):
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        left, right = i + 1, n - 1
        while left < right:
            s = nums[i] + nums[left] + nums[right]
            if s == 0:
                result.append([nums[i], nums[left], nums[right]])
                while left < right and nums[left] == nums[left + 1]:
                    left += 1
                while left < right and nums[right] == nums[right - 1]:
                    right -= 1
                left += 1
                right -= 1
            elif s < 0:
                left += 1
            else:
                right -= 1
    return result
```

**Time:** `O(n²)` | **Space:** `O(1)` extra

---

## 🤖 KEY INSIGHTS

1. **Sort first** — enables two-pointer 2-sum.
2. **Fix i, two-pointer rest** — reduces to 2-sum.
3. **Skip duplicate i** — `nums[i] == nums[i-1]`.
4. **Skip duplicate left/right after match** — avoid duplicate triplets.
5. **O(n²) total** — n iterations × O(n) two-pointer.
6. **O(1) extra** — sorting in-place, no hash table.
7. **Hash variant** — possible but uses O(n) extra.
8. **Brute O(n³)** — possible but slow.
9. **Output** is list of triplets, not indices.
10. **k-Sum generalization** — recursive fix-i + solve (k-1)-sum.

---

## 🧪 TEST CASES

| Input | Expected | Note |
|-------|----------|------|
| `[-1,0,1,2,-1,-4]` | `[[-1,-1,2],[-1,0,1]]` | Classic |
| `[0,1,1]` | `[]` | No triplet |
| `[0,0,0]` | `[[0,0,0]]` | All same |
| `[-2,0,1,1,2]` | `[[-2,0,2],[-2,1,1]]` | Multiple |
| `[]` | `[]` | Empty |
| `[1,2,3]` | `[]` | All positive |
| `[-1,-2,-3]` | `[]` | All negative |
| `[-1,0,1,0]` | `[[-1,0,1]]` | Duplicate zero |
| `[1,-1,-1,0]` | `[[-1,0,1]]` | Mixed |
| `[0,0,0,0]` | `[[0,0,0]]` | Many duplicates |

---

## 📊 COMPLEXITY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Sort + two-pointer** | **O(n²)** | **O(1)** extra | **✅ BEST** |
| Hash set per i | O(n²) | O(n) | ✅ Alternative |
| Brute triple loop | O(n³) | O(1) | ❌ Slow |

---

## 🔗 RELATED

- 2Sum (LC 1)
- 3Sum Closest (LC 16)
- 4Sum (LC 18)
- k-Sum family
- Two-pointer problems

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Insight:** "Sort, fix i, two-pointer for 2-sum. Skip duplicates at i, left, right. O(n²) time, O(1) extra space."
