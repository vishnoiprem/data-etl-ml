# Subarray Sum Equals K - All 10 Methods Explained

## The Problem
```
Given nums and k, find total subarrays whose sum equals k.
nums = [1, 2, 3], k = 3 -> Output: 2 ([1,2] and [3])
```

---

## Method 1: Brute Force (Triple Nested Loop)

### How I Think
> "Let me check every possible subarray. A subarray is nums[i..j]. I'll use three loops: one for start, one for end, and the inner sum() to calculate the sum."

```python
def subarray_sum(nums, k):
    count = 0
    n = len(nums)
    for i in range(n):
        for j in range(i, n):
            if sum(nums[i:j+1]) == k:
                count += 1
    return count
```

### Walkthrough
```
nums = [1, 2, 3], k = 3

i=0:
  j=0: sum([1])=1 != 3
  j=1: sum([1,2])=3 == 3 ✓ count=1
  j=2: sum([1,2,3])=6 != 3

i=1:
  j=1: sum([2])=2 != 3
  j=2: sum([2,3])=5 != 3

i=2:
  j=2: sum([3])=3 == 3 ✓ count=2

Answer: 2
```

### Time: O(n^3) | Space: O(1)
### Problem: Recalculating sum() each time

---

## Method 2: Brute Force Without Resumming

### How I Think
> "Why am I calling sum() each time? As j grows, I just add ONE more number. Let me keep a running total."

```python
def subarray_sum(nums, k):
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

### Improvement: No more sum() call
### Time: O(n^2) | Space: O(1)

---

## Method 3: Prefix Sum Array

### How I Think
> "What if I precompute ALL prefix sums at once? Then any subarray sum is just two lookups."

**Key idea:**
```
nums    = [1, 2, 3, 4]
prefix  = [0, 1, 3, 6, 10]

Sum of nums[1..3] = prefix[4] - prefix[1] = 10 - 1 = 9
```

```python
def subarray_sum(nums, k):
    n = len(nums)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i+1] = prefix[i] + nums[i]
    
    count = 0
    for i in range(n):
        for j in range(i+1, n+1):
            if prefix[j] - prefix[i] == k:
                count += 1
    return count
```

### Time: O(n^2) | Space: O(n)

---

## Method 4: Hashmap on Prefix Sums (OPTIMAL!)

### How I Think
> "For each j, I only need: how many i exist where prefix[i] = prefix[j] - k? That's a perfect hashmap lookup!"

**The math:**
```
prefix[j] - prefix[i] = k
prefix[i] = prefix[j] - k
```

```python
def subarray_sum(nums, k):
    count = 0
    current = 0
    seen = {0: 1}
    
    for num in nums:
        current += num
        count += seen.get(current - k, 0)
        seen[current] = seen.get(current, 0) + 1
    
    return count
```

### Walkthrough
```
nums = [1, 2, 3], k = 3
seen = {0: 1}, current = 0, count = 0

num=1: current=1, need -2, seen[-2]=0, count=0
       seen = {0:1, 1:1}

num=2: current=3, need 0, seen[0]=1, count=1 ← found [1,2]!
       seen = {0:1, 1:1, 3:1}

num=3: current=6, need 3, seen[3]=1, count=2 ← found [1,2,3]!
       seen = {0:1, 1:1, 3:1, 6:1}

Answer: 2
```

### Why {0: 1} at start? Handles subarrays from index 0
### Time: O(n) | Space: O(n) ⭐ BEST!

---

## Method 5: Using defaultdict

### How I Think
> "Defaultdict saves me from writing .get(key, 0) everywhere."

```python
from collections import defaultdict

def subarray_sum(nums, k):
    count = 0
    current = 0
    seen = defaultdict(int)
    seen[0] = 1
    
    for num in nums:
        current += num
        count += seen[current - k]
        seen[current] += 1
    
    return count
```

### Time: O(n) | Space: O(n)

---

## Method 6: Using Counter

### How I Think
> "Counter is like defaultdict(int) with extra features."

```python
from collections import Counter

def subarray_sum(nums, k):
    count = 0
    current = 0
    seen = Counter([0])
    
    for num in nums:
        current += num
        count += seen[current - k]
        seen[current] += 1
    
    return count
```

### Time: O(n) | Space: O(n)

---

## Method 7: Sliding Window (Positive Numbers Only)

### How I Think
> "If all numbers are positive, sliding window works. Expand right, shrink left when too big."

```python
def subarray_sum(nums, k):
    count = 0
    current = 0
    left = 0
    
    for right in range(len(nums)):
        current += nums[right]
        while current > k and left <= right:
            current -= nums[left]
            left += 1
        if current == k:
            count += 1
    
    return count
```

### Why it doesn't work for negatives!

---

## Method 8: Using itertools.accumulate

### How I Think
> "Python has accumulate that does running sum for me."

```python
from itertools import accumulate

def subarray_sum(nums, k):
    count = 0
    seen = {0: 1}
    
    for prefix in accumulate(nums):
        count += seen.get(prefix - k, 0)
        seen[prefix] = seen.get(prefix, 0) + 1
    
    return count
```

### Time: O(n) | Space: O(n)

---

## Method 9: List Comprehension (Brute)

### How I Think
> "Can I do brute force in one line?"

```python
def subarray_sum(nums, k):
    n = len(nums)
    return sum(1 for i in range(n) 
                 for j in range(i+1, n+1)
                 if sum(nums[i:j]) == k)
```

### Time: O(n^3) - looks cool but slow

---

## Method 10: accumulate + Brute

### How I Think
> "Combine accumulate with brute force checking."

```python
from itertools import accumulate

def subarray_sum(nums, k):
    prefixes = list(accumulate(nums, initial=0))
    return sum(1 for i in range(len(prefixes))
                 for j in range(i+1, len(prefixes))
                 if prefixes[j] - prefixes[i] == k)
```

### Time: O(n^2)

---

## Summary Table

| Method | Time | Space | Key Insight |
|--------|------|-------|-------------|
| 1. Triple loop | O(n^3) | O(1) | Check all |
| 2. Running sum | O(n^2) | O(1) | Don't resumm |
| 3. Prefix array | O(n^2) | O(n) | Pre-compute |
| 4. Hashmap | O(n) | O(n) | ⭐ Best |
| 5. defaultdict | O(n) | O(n) | Cleaner |
| 6. Counter | O(n) | O(n) | Cleaner |
| 7. Sliding window | O(n) | O(1) | Positive only |
| 8. accumulate | O(n) | O(n) | Python helper |
| 9. Comprehension | O(n^3) | O(1) | One-liner |
| 10. accumulate+brute | O(n^2) | O(n) | Hybrid |

---

## The Thinking Journey

```
Method 1: "Let me check everything"           -> O(n^3)
Method 2: "Don't resumm, just keep adding"    -> O(n^2)
Method 3: "Pre-compute all prefix sums"       -> O(n^2)
Method 4: "Use hashmap for instant lookup"    -> O(n)  ← BEST!
Method 5: "Cleaner with defaultdict"
Method 6: "Cleaner with Counter"
Method 7: "Sliding window? Oh wait, negatives..."
Method 8: "Python's accumulate helper"
Method 9: "One-liner brute force"
Method 10: "Combine accumulate + brute"
```

## Universal Pattern

1. Find brute force (always works)
2. Look for **repeated work** (summing same numbers)
3. Pre-compute that work (prefix sums)
4. Look for **repeated searches** (finding if prefix exists)
5. Use **hashmap** for O(1) lookup

## Best Answer to Memorize

```python
from collections import defaultdict

def subarray_sum(nums, k):
    count = 0
    current = 0
    seen = defaultdict(int)
    seen[0] = 1
    
    for num in nums:
        current += num
        count += seen[current - k]
        seen[current] += 1
    
    return count
```

7 lines. O(n) time. Clean and interview-ready! 🚀
