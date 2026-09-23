# Count Number of Nice Subarrays — 10 Solutions + Interview Thinking

## Problem
Given an array of positive integers `nums` and an integer `k`, return
the number of contiguous subarrays containing **exactly `k` odd
numbers**. A "nice" subarray is one with exactly `k` odds.

Reference: LeetCode #1248 / Educative Grokking — "Number of Nice
Subarrays".

---

## Interview Talking Points

Lead with the **"exactly K = atMost(K) − atMost(K−1)"** reframing.
Then mention the sliding window that supports `atMost`.

---

## 10-Step Thinking Process

### 1. Understand
"Count subarrays containing exactly k odd numbers."

### 2. Key Insight
Exactly k = atMost(k) − atMost(k−1). The `atMost(k)` count is itself
a classic sliding window: count subarrays with at most k odds.

### 3. Pattern Recognition
- Sliding window with odd-count constraint
- Inclusion–exclusion: exactly = atMost − atMost(less)

### 4. Edge Cases
- k > total_odds → 0.
- All even nums → 0 (assuming k ≥ 1).
- k == 0 → count all subarrays with no odds.
- All odds → number of length-k windows = n − k + 1.

### 5. Tricky Detail — Why `atMost(k) − atMost(k−1)` Works

A subarray has exactly k odds iff it has ≤ k odds AND it does NOT
have ≤ k−1 odds. So `atMost(k)` overcounts windows with 0, 1, …,
k−1 odds. Subtracting `atMost(k−1)` removes those with 0..k−1, leaving
just exactly k.

### 6. Algorithm
```
def at_most(k):
    left = 0; odd = 0; result = 0
    for right in range(n):
        if nums[right] % 2 == 1: odd += 1
        while odd > k:
            if nums[left] % 2 == 1: odd -= 1
            left += 1
        result += right - left + 1
    return result
return at_most(k) - at_most(k - 1)
```

### 7. Why It Works
After shrinking, [left..right] has ≤ k odds. Every sub-window ending at
`right` whose start is in [left..right] is also valid (shrinking
left removes at most one odd from a window that already has ≤ k).
There are `right − left + 1` such starts.

### 8. Complexity
- **Time**: O(n). Each element enters and leaves the window at most once.
- **Space**: O(1).

### 9. Code Structure
1. Inner helper `at_most(k)`.
2. Slide `right`; track odd count.
3. Shrink while odd > k; accumulate count.
4. Return `at_most(k) - at_most(k-1)`.

### 10. Mental Trace
`nums=[1,1,2,1,1]`, `k=1`:

`at_most(1)`:
- right=0 (1): odd=1. result += 1. total=1.
- right=1 (1): odd=2. shrink: nums[0]=1 odd → odd=1, left=1. result += 1. total=2.
- right=2 (2): odd=1. result += 2. total=4.
- right=3 (1): odd=2. shrink: nums[1]=1 odd → odd=1, left=2. result += 2. total=6.
- right=4 (1): odd=2. shrink: nums[2]=2 even, left=3. shrink: nums[3]=1 odd → odd=1, left=4. result += 1. total=7.

`at_most(0)`:
- right=0 (1): odd=1. shrink: nums[0]=1 odd → odd=0, left=1. result += 0. total=0.
- right=1 (1): odd=1. shrink: nums[1]=1 odd → odd=0, left=2. result += 0. total=0.
- right=2 (2): odd=0. result += 1. total=1.
- right=3 (1): odd=1. shrink: nums[2]=2 even, left=3. shrink: nums[3]=1 odd → odd=0, left=4. result += 0. total=1.
- right=4 (1): odd=1. shrink: nums[4]=1 odd → odd=0, left=5. result += 0. total=1.

`exactly(1) = 7 − 1 = 6`. ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time    | Space | Notes |
|----|---------------------------------------|---------|-------|-------|
| 1  | `at_most` helper (BEST)               | O(n)    | O(1)  | canonical |
| 2  | `at_most` with k_val guard            | O(n)    | O(1)  | safe for k=0 |
| 3  | Brute force                           | O(n²)   | O(1)  | educational |
| 4  | Prefix sum + hashmap                  | O(n)    | O(n)  | alternative |
| 5  | defaultdict + prefix                  | O(n)    | O(n)  | cleaner hash |
| 6  | numpy fallback                        | O(n)    | O(1)  | calls V1 |
| 7  | Same as V1 (manual bit math)          | O(n)    | O(1)  | same |
| 8  | Same as V1 (alt code)                 | O(n)    | O(1)  | alt |
| 9  | itertools.accumulate                  | O(n)    | O(n)  | pythonic |
| 10 | Most concise                          | O(n)    | O(1)  | cleanest |

---

## Recommended Interview Answer

**Solution 1** — clean, optimal:

```python
def number_of_nice_subarrays(nums, k):
    def at_most(k_val):
        if k_val < 0:
            return 0
        left = 0
        odd = 0
        result = 0
        for right in range(len(nums)):
            if nums[right] % 2 == 1:
                odd += 1
            while odd > k_val:
                if nums[left] % 2 == 1:
                    odd -= 1
                left += 1
            result += right - left + 1
        return result

    return at_most(k) - at_most(k - 1)
```

---

## Common Pitfalls

1. **Not handling k=0** — `at_most(-1)` needs an early return.
2. **Off-by-one in the inner count** — must be `right - left + 1` AFTER shrinking.
3. **Confusing the k for at_most** — the inner function uses `k_val`, the outer passes both `k` and `k-1`.
4. **Subarray vs subsequence** — only contiguous subarrays count.
5. **Not verifying edge cases** — empty array, all evens, single odd.

---

## Talking Points — Interview Cheat Sheet

If asked "why atMost(k) − atMost(k-1)?":
> "Exactly k is the difference of two atMost counts. A subarray with
>  exactly k odds contributes to atMost(k) but not to atMost(k-1)."

If asked "can you do this without subtraction?":
> "Yes — count valid middle ranges. For each pair of consecutive
>  odd indices i and j with exactly k odds between them, the number
>  of valid lefts times valid rights gives the count."

If asked "what if k > total odds?":
> "Return 0 immediately."

If asked "is this O(n) or O(n²)?":
> "O(n). Each element is added to the window once and removed once."

If asked "can you do this with prefix sums?":
> "Yes. Build prefix of odd counts. Then for each index, look up how
>  many earlier indices have count = current - k. O(n) with hashmap."

---

## Related Problems

- **Binary Subarrays With Sum** (LC #930) — same pattern, "treat 1 as odd, 0 as even".
- **Subarrays with K Different Integers** (LC #992) — different element count.
- **Count Subarrays With Score Less Than K** (LC #2302) — different metric.

---

## Variants

- **At most k odds**: just `at_most(k)` directly.
- **Min length subarray with exactly k odds**: track min length while counting.
- **Max length subarray with exactly k odds**: track max length.
- **Number of subarrays with sum-of-evens == k**: same technique with even counts.
