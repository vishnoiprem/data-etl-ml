# Subarray Product Less Than K — 10 Solutions + Interview Thinking

## Problem
Given positive integers `nums` and integer `k`, count subarrays whose
product is strictly less than `k`.

Reference: LeetCode #713 / Educative Grokking — "Subarray Product
Less Than K".

---

## Interview Talking Points

Lead with the **sliding window invariant**: "Since all positive,
shrinking only decreases product. Track running product."

---

## 10-Step Thinking Process

### 1. Understand
"Count subarrays with product < k. All nums are positive."

### 2. Key Insight
Sliding window with running product. Shrink from left while product
>= k. After shrinking, all sub-windows ending at right (with smaller
lefts) are also valid.

### 3. Pattern Recognition
- Sliding window with product constraint
- All positive → monotonicity preserved

### 4. Edge Cases
- k <= 1 → 0 (no positive product is < 1).
- All ones → n*(n+1)/2.
- Single element >= k → 0.

### 5. Tricky Detail — Integer Division

Since all nums are positive integers, product can be divided exactly
by `nums[left]`.

### 6. Algorithm
```
if k <= 1: return 0
product = 1; left = 0; result = 0
for right in range(n):
    product *= nums[right]
    while product >= k:
        product //= nums[left]
        left += 1
    result += right - left + 1
return result
```

### 7. Why It Works
After shrinking, [left..right] has product < k. All sub-windows
ending at right with starts in [left..right] are also valid (smaller
products). There are right - left + 1 such.

### 8. Complexity
- **Time**: O(n).
- **Space**: O(1).

### 9. Code Structure
1. Edge case k <= 1.
2. Init product, left, result.
3. Iterate right; shrink; add count.

### 10. Mental Trace
`nums=[10,5,2,6]`, `k=100`:
- right=0 (10): product=10. result=1.
- right=1 (5): product=50. result=3.
- right=2 (2): product=100>=100. Shrink: product=10, left=1. result=5.
- right=3 (6): product=60. result=8.
- Final = 8. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time    | Space | Notes |
|----|---------------------------------------|---------|-------|-------|
| 1  | Sliding window (BEST)                 | O(n)    | O(1)  | canonical |
| 2  | Cleaner version                       | O(n)    | O(1)  | same |
| 3  | Brute force                           | O(n²)   | O(1)  | educational |
| 4  | log prefix + bisect                   | O(n log n) | O(n) | alternative |
| 5  | Float product                         | O(n)    | O(1)  | same |
| 6  | numpy fallback                        | O(n)    | O(1)  | vectorized |
| 7  | Recursive                             | O(n)    | O(n)  | educational |
| 8  | math.prod of window                   | O(n²)   | O(n)  | slow |
| 9  | Same as V1 with shrink counter        | O(n)    | O(1)  | alt |
| 10 | Same as V1, minimal                   | O(n)    | O(1)  | cleanest |

---

## Recommended Interview Answer

**Solution 1** — clean, optimal:

```python
def num_subarray_product_less_than_k(nums, k):
    if k <= 1:
        return 0
    product = 1
    left = 0
    result = 0
    for right in range(len(nums)):
        product *= nums[right]
        while product >= k:
            product //= nums[left]
            left += 1
        result += right - left + 1
    return result
```

---

## Common Pitfalls

1. **Handling k <= 1** — must return 0 explicitly.
2. **Integer overflow** in other languages; Python is fine.
3. **Forgetting to divide** on shrink — `product //= nums[left]`.
4. **Off-by-one in count** — `right - left + 1` after shrinking.
5. **Negative numbers** — would break the algorithm.

---

## Talking Points — Interview Cheat Sheet

If asked "what if nums[i] can be zero?":
> "Adding zero makes product 0 which is < k. The window expands.
>  Shrinking resets product. The algorithm still works since 0 > 0
>  doesn't trigger shrink."

If asked "what about negatives?":
> "Breaks the algorithm because multiplying a negative flips the
>  sign. Need a different approach (track even/odd negative count)."

If asked "could we use log?":
> "Yes. Take log of each, sum to get log(product). Then sliding window
>  with log sum < log(k). O(n log n) with binary search, but precision
>  is an issue with floating-point."

If asked "could we use prefix products?":
> "Yes. prefix[i] = product of nums[0..i-1]. For each right, find
>  smallest left with prefix[right+1] / prefix[left] < k. Binary
>  search since prefix is increasing (positive integers)."

---

## Related Problems

- **Minimum Size Subarray Sum** (LC #209) — additive version.
- **Count Subarrays With Score Less Than K** (LC #2302) — sum × len.
- **Subarray Product Less Than K** — this problem.

---

## Variants

- **<= k instead of <**: change `>=` to `>`.
- **Negative numbers**: track sign and use a different approach.
- **Min length with product < k**: track min.
- **Max product subarray** (LC #152): different — track max with sign.
