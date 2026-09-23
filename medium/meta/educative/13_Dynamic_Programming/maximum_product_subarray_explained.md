# Maximum Product Subarray — 10 Solutions

## Problem
Given an integer array `nums`, find a contiguous subarray with the
largest product and return that product.

Constraints:
- `1 ≤ nums.length ≤ 10³`
- `-10 ≤ nums[i] ≤ 10`
- Product fits in 32-bit int

## Why it's tricky
For max-sum subarray (Kadane), multiplying by a positive number grows
the sum; multiplying by a negative number is bad. For products, a
negative number **flips** the sign — a "minimum" product can become
the "maximum" after multiplying by another negative.

## Solution Summary

| #  | Approach                                | Time     | Space |
|----|-----------------------------------------|----------|-------|
| 1  | Track min/max so far (canonical)        | O(n)     | O(1)  |
| 2  | DP with max_prod/min_prod arrays        | O(n)     | O(n)  |
| 3  | Brute force (all subarrays)             | O(n²)    | O(1)  |
| 4  | Prefix products + forward/backward scan | O(n)     | O(1)  |
| 5  | O(n) with constant variables only       | O(n)     | O(1)  |
| 6  | Split on zeros + segment analysis       | O(n)     | O(1)  |
| 7  | Memoized recursion (top-down)           | O(n)     | O(n)  |
| 8  | Kadane-style for products                | O(n)     | O(1)  |
| 9  | Forward+backward scanning                | O(n)     | O(1)  |
| 10 | Prefix-product ratio enumeration         | O(n²)    | O(n)  |

---

## Solution 1 (canonical, memorize this!)

```python
def max_product(nums):
    if not nums:
        return 0
    max_so_far = min_so_far = result = nums[0]
    for num in nums[1:]:
        if num < 0:
            max_so_far, min_so_far = min_so_far, max_so_far
        max_so_far = max(num, max_so_far * num)
        min_so_far = min(num, min_so_far * num)
        result = max(result, max_so_far)
    return result
```

### Why we track BOTH max and min
A negative `min_so_far` becomes the `max_so_far` when multiplied by
another negative number. Without tracking the min, we'd miss these
flips.

### Walkthrough: `[2, 3, -2, 4]`
- i=0: max=min=result=2
- i=1 (num=3): max=max(3, 2*3)=6, min=min(3, 2*3)=3, result=6
- i=2 (num=-2): swap → max=3, min=6; max=max(-2, 3*-2)=max(-2,-6)=-2;
  min=min(-2, 6*-2)=min(-2,-12)=-12; result stays 6
- i=3 (num=4): max=max(4, -2*4)=4, min=min(4, -12*4)=-48; result=max(6,4)=6 ✓

---

## Solution 4 — Prefix-Product with Forward+Backward Scans

The optimal subarray either:
- Starts at index 0 (forward scan finds it)
- Ends at index n-1 (backward scan finds it)

Reset product to 1 at every zero. Track max running product.
This works because the optimal subarray cannot contain a zero (since
zero kills the product, and we can always do better by truncating
to a non-zero region).

```python
def max_from(arr):
    best, cur = -inf, 1
    for x in arr:
        cur *= x
        if cur > best: best = cur
        if cur == 0: cur = 1
    return best

return max(max_from(nums), max_from(nums[::-1]))
```

---

## Solution 6 — Split on Zeros

For each zero-free segment:
- If even number of negatives → whole segment product is the answer.
- If odd → answer is max(product-after-dropping-first-negative,
  product-after-dropping-last-negative).

---

## Solution 10 — Brute Force via Prefix Ratios

`product(nums[i:j]) = prefix[j] / prefix[i]`. Enumerate all (i, j)
pairs to find the maximum ratio. `O(n²)` — for educational purposes.

---

## Complexity Comparison

| Aspect              | Best (V1, V5, V8, V9) | Brute (V3, V10) |
|---------------------|----------------------|----------------|
| Time                | O(n)                 | O(n²)          |
| Space               | O(1) extra           | O(n) extra     |
| Handles negatives?  | Yes                  | Yes            |
| Handles zeros?      | Yes                  | Yes            |
| Interview-friendly? | ★★★★★                | ★★             |

**Recommended interview answer:** Solution 1 (canonical min/max).

---

## Edge Cases (all 10 solutions handle)

- Empty array → 0
- Single element → that element
- All zeros → 0
- Mix of positives and negatives → flip-aware logic
- Zeros splitting the array → handled by reset / split
