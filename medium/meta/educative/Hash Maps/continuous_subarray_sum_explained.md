# Continuous Subarray Sum - 10 Ways with How to Think

## The Problem
```
Given nums and k, return True if there's a subarray of length >= 2
whose sum is a multiple of k.

Examples:
    [23, 2, 4, 6, 7], k=6 -> True
        Subarray [2, 4] has sum 6 (multiple of 6)

    [23, 2, 6, 4, 7], k=13 -> False
        No subarray with sum divisible by 13
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
nums = [23, 2, 4, 6, 7], k = 6

Find subarray (length >= 2) where sum is multiple of 6:
- [2, 4] = 6 ✓ (6 = 1*6)
- [4, 6] = 10
- [6, 7] = 13
- [2, 4, 6] = 12 ✓ (12 = 2*6)

Answer: True
```

### Step 2: The Key Insight
> "Same as Subarray Sum Equals K! But instead of finding sum = k, find sum % k == 0.
>
> Math: if prefix[i] % k == prefix[j] % k, then sum(nums[i+1..j]) is multiple of k"

### Step 3: Walkthrough
```
nums = [23, 2, 4, 6, 7], k = 6
prefix = [0, 23, 25, 29, 35, 42]
prefix % k = [0, 5, 1, 5, 5, 0]

When we see 5 at index 1, store it.
At index 3, prefix % k = 5 again!
Subarray from index 2 to 3 = [2, 4], sum = 6 ✓
```

### Step 4: Algorithm
```
1. Compute prefix sum and prefix % k
2. Use hashmap: remainder -> first index where seen
3. If same remainder seen twice AND indices are far enough apart, return True
4. Special case: prefix[i] % k == 0 (subarray from start)
```

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to find a subarray of length >= 2 whose sum is divisible by k."

**Key Insight:**
> "Same as Subarray Sum K! The math: If prefix[i] % k == prefix[j] % k, then sum(nums[i+1..j]) is divisible by k. So I need to find two prefix sums with the same remainder where the distance between them is >= 2 (to ensure subarray length >= 2)."

**Algorithm:**
> "1. Use hashmap: remainder -> first index where seen
> 2. For each element, compute prefix sum and prefix % k
> 3. If I've seen this remainder before, check if distance >= 2
> 4. If yes, return True"

**Special case:**
> "If prefix sum itself is divisible by k, the subarray from index 0 to current has length >= 1. I need to check length >= 2 specifically."

**Why this works:**
> "Two prefix sums with same remainder means their difference is divisible by k. That difference is exactly the sum of the elements between them."

---

## The 10 Implementations

### Way 1: HashMap of Remainders (BEST - Memorize!)
```python
def checkSubarraySum(nums, k):
    remainder_index = {0: -1}
    prefix_sum = 0

    for i, num in enumerate(nums):
        prefix_sum += num
        remainder = prefix_sum % k

        if remainder in remainder_index:
            if i - remainder_index[remainder] >= 2:
                return True
        else:
            remainder_index[remainder] = i

    return False
```

### Way 2: Using defaultdict
Same logic but with defaultdict.

### Way 3: Brute Force
```python
def checkSubarraySum(nums, k):
    n = len(nums)
    for i in range(n):
        for j in range(i+1, n):
            if sum(nums[i:j+1]) % k == 0:
                return True
    return False
```

### Way 4: Optimized Brute Force
Uses running sum instead of sum().

### Way 5-9: Variations
- Way 5: enumerate + dict
- Way 6: Most compact
- Way 7: List of indices
- Way 8: Counter-based
- Way 9: Proper length check

### Way 10: Functional style (complex, illustrative)

---

## Decision Tree

```
+------------------+-------------+--------------+
| Scenario         | Best        | Why          |
+------------------+-------------+--------------+
| Optimal          | HashMap     | O(n) time    |
| Memory tight     | Brute force | O(1) space   |
| Clean code       | Way 1       | Readable     |
+------------------+-------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| HashMap | O(n) | O(n) |
| Brute Force | O(n²) | O(1) |

---

## Walkthrough Example

```
nums = [23, 2, 4, 6, 7], k = 6

i=0, num=23: prefix=23, rem=5
  Not in map -> {0:-1, 5:0}

i=1, num=2: prefix=25, rem=1
  Not in map -> {0:-1, 5:0, 1:1}

i=2, num=4: prefix=29, rem=5
  In map at index 0!
  i - 0 = 2 >= 2 ✓
  Return True!

Subarray nums[1..2] = [2, 4], sum = 6 ✓
```

## Best Answer to Memorize

```python
def checkSubarraySum(nums, k):
    remainder_index = {0: -1}
    prefix_sum = 0

    for i, num in enumerate(nums):
        prefix_sum += num
        remainder = prefix_sum % k

        if remainder in remainder_index:
            if i - remainder_index[remainder] >= 2:
                return True
        else:
            remainder_index[remainder] = i

    return False
```

**13 lines. O(n) time. Clean.** 🚀

## Why `>= 2` Check?

> "The subarray must have length >= 2. If remainder_index[remainder] was seen at index i and we see it again at index j, the subarray has length j - i. We need this >= 2."

```
remainder_index = {0: -1}  # Initial setup
```

This special entry ensures that if any prefix sum itself is divisible by k, we can find a subarray starting from index 0 of length >= 2.

## Test Cases

| nums | k | Expected | Why |
|------|---|----------|-----|
| [23,2,4,6,7] | 6 | True | [2,4]=6 |
| [23,2,6,4,7] | 13 | False | No match |
| [5,0,0,0] | 5 | True | [5,0]=5 |
| [0,0] | 1 | True | [0,0]=0 |
| [1,1] | 2 | True | [1,1]=2 |
| [1,2,3] | 5 | False | No subarray sum=5 or 10 |

## Comparison with Subarray Sum Equals K

This problem is similar but with key differences:
| Aspect | Subarray Sum K | Continuous Subarray Sum |
|--------|----------------|-------------------------|
| Goal | sum == K | sum % K == 0 |
| Length | any | >= 2 |
| Hashmap value | count | first index |
| Special case | {0: 1} | {0: -1} |
