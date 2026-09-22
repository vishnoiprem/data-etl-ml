# Subarray Sum Equals K - How to Think

## The Problem
```
Given an array of integers nums and integer k, count subarrays that sum to k.

Examples:
    nums = [1, 1, 1], k = 2     -> 2
    nums = [1, 2, 3], k = 3     -> 2 ([1,2] and [3])
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
nums = [1, 1, 1], k = 2
Subarrays and their sums:
  [1]   = 1
  [1,1] = 2 ✓
  [1,1,1] = 3
  [1]   = 1
  [1,1] = 2 ✓
  [1]   = 1

Answer: 2 ✓
```

### Step 2: The Trick
> "Subarray sum from i to j = prefix[j+1] - prefix[i].
> If this equals k, then prefix[i] = prefix[j+1] - k.
> So for each j, count how many i have prefix[i] = prefix[j+1] - k."

### Step 3: Use HashMap!
> "Maintain running prefix sum. For each position, check how many
> previous prefixes equal (current - k). Use HashMap to count."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to count subarrays whose sum equals k. The standard approach is to use prefix sums with a hashmap."

**Key Insight:**
> "A subarray from index i to j has sum = prefix[j+1] - prefix[i].
> If this equals k, then prefix[i] = prefix[j+1] - k.
> So for each prefix[j+1], I need to count occurrences of prefix[j+1] - k among previous prefixes."

**Algorithm:**
> "1. Maintain a hashmap from prefix_sum -> count
> 2. Start with {0: 1} (empty prefix)
> 3. For each num:
>    - Update cumulative sum
>    - Add to count: hashmap[sum - k] (how many previous prefixes match)
>    - Increment hashmap[sum]
> 4. Return count"

**Why this works:**
> "Each time we add hashmap[sum - k] to our answer, we're counting
> subarrays that END at the current index with sum k."

**Edge cases:**
- Empty array: returns 0
- All zeros with k=0: count subarrays (combinations)
- Negative numbers: must use hashmap, NOT sliding window
- k=0: count subarrays with sum 0

---

## The Approaches (Simple to Complex)

### Way 1-2: Brute Force (O(n²) and O(n³))
```python
# O(n^3) - resumming each subarray
def subarray_sum_brute(nums, k):
    count = 0
    n = len(nums)
    for i in range(n):
        for j in range(i, n):
            if sum(nums[i:j+1]) == k:
                count += 1
    return count

# O(n^2) - running sum
def subarray_sum_running(nums, k):
    count = 0
    n = len(nums)
    for i in range(n):
        current = 0
        for j in range(i, n):
            current += nums[j]
            if current == k:
                count += 1
    return count
```

### Way 3-5: Prefix Sum with HashMap (BEST - O(n))
```python
from collections import defaultdict

def subarray_sum_hashmap(nums, k):
    count = 0
    prefix = 0
    prefix_count = defaultdict(int)
    prefix_count[0] = 1  # empty prefix

    for num in nums:
        prefix += num
        # Count subarrays ending here with sum k
        count += prefix_count[prefix - k]
        prefix_count[prefix] += 1

    return count
```

### Way 6: With Counter
```python
from collections import Counter

def subarray_sum_counter(nums, k):
    count = 0
    prefix = 0
    prefix_count = Counter([0])

    for num in nums:
        prefix += num
        count += prefix_count[prefix - k]
        prefix_count[prefix] += 1

    return count
```

### Way 7: With dict instead of defaultdict
### Way 8: With get() method
### Way 9: One-liner style
### Way 10: With set (only for unique prefix detection)

---

## Decision Tree

```
+----------------------+-----------+--------------+
| Scenario             | Best      | Why          |
+----------------------+-----------+--------------+
| Any integers         | Hashmap   | O(n)         |
| All positive only    | Sliding w | Simple       |
| Just check exists    | Hashmap   | O(n)         |
| Force brute          | Nested    | Educational  |
+----------------------+-----------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Brute | O(n²) | O(1) |
| Prefix + hashmap | O(n) | O(n) |

---

## Walkthrough Example

```
nums = [1, 1, 1], k = 2

Init: hashmap = {0: 1}, prefix = 0, count = 0

i=0, num=1:
  prefix = 1
  count += hashmap[1-2] = hashmap[-1] = 0  -> count=0
  hashmap[1] = 1  -> {0:1, 1:1}

i=1, num=1:
  prefix = 2
  count += hashmap[2-2] = hashmap[0] = 1  -> count=1 ✓ (subarray [1,1])
  hashmap[2] = 1  -> {0:1, 1:1, 2:1}

i=2, num=1:
  prefix = 3
  count += hashmap[3-2] = hashmap[1] = 1  -> count=2 ✓ (subarray [1,1])
  hashmap[3] = 1  -> {0:1, 1:1, 2:1, 3:1}

Final: count = 2 ✓
```

## Best Answer to Memorize

```python
from collections import defaultdict

def subarraySum(nums, k):
    count = 0
    prefix = 0
    prefix_count = defaultdict(int)
    prefix_count[0] = 1  # empty prefix

    for num in nums:
        prefix += num
        count += prefix_count[prefix - k]
        prefix_count[prefix] += 1

    return count
```

**9 lines. O(n) time. Handles negative numbers. Interview-ready!**

## Key Insight

> "Subarray sum from i to j = prefix[j+1] - prefix[i].
> Setting this equal to k: prefix[i] = prefix[j+1] - k.
> The hashmap counts how many 'i' values satisfy this for each 'j'."

The `prefix_count[0] = 1` initialization is critical - it counts subarrays that
start from index 0 (the empty prefix).

## Test Cases

| nums | k | Expected |
|------|---|----------|
| [1,1,1] | 2 | 2 |
| [1,2,3] | 3 | 2 |
| [1,-1,1,-1] | 0 | 4 |
| [0,0,0,0] | 0 | 10 |
| [] | 5 | 0 |
| [1] | 1 | 1 |

## Why NOT Sliding Window?

> "Sliding window works only when ALL numbers are positive (or all negative).
> With mixed signs, the constraint 'sum >= k' isn't monotonic.
> Hashmap is the universal solution for any sign pattern."
