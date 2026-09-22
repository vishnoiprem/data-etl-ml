# Contains Duplicate II - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/contains-duplicate-ii

## The Problem
```
Given an integer array nums and an integer k, return True if there exist
two distinct indices i and j such that nums[i] == nums[j] and |i - j| <= k.
Otherwise, return False.

Examples:
    nums=[1,2,3,1], k=3 -> True (nums[0]==nums[3], |0-3|=3<=3)
    nums=[1,0,1,1], k=1 -> True (nums[2]==nums[3], |2-3|=1<=1)
    nums=[1,2,3,1,2,3], k=2 -> False

Constraints:
- 1 <= nums.length <= 10^3
- -10^3 <= nums[i] <= 10^3
- 0 <= k <= 10^4
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
We need duplicate elements within distance k (inclusive).
For each element, we only care about its OCCURRENCES within the previous k indices.
```

### Step 2: The Trick
> "KEY INSIGHT: For each element, only the MOST RECENT previous occurrence matters.
> Why? Any earlier occurrence is FURTHER away. If the most recent is too far,
> all earlier ones are too far too.
>
> So: maintain a hash map value -> most recent index. When we see nums[i]=v:
> - If v is in map at index j, and i - j <= k: return True.
> - Otherwise, update map[v] = i."

### Step 3: Why it works
> "Distance is monotone: later index = larger distance. So if the closest previous
> occurrence is already too far, all earlier ones are too. Only need most recent."

### Step 4: Algorithm
> "1. last_index = {} (value -> most recent index).
> 2. For each (i, num) in enumerate(nums):
> 3.   If num in last_index and i - last_index[num] <= k: return True.
> 4.   last_index[num] = i.
> 5. Return False."

### Step 5: Alternative — sliding window set
> "Maintain a set of last k elements. Add new element, check if already in set.
> Remove element at index i-k to keep size <= k."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to check if any duplicate exists within k indices of each other."

**Key Insight:**
> "Only the most recent previous occurrence matters. Use a hash map from value
> to its most recent index. For each element, if it's been seen and the
> distance is <= k, return True."

**Algorithm:**
> "1. last_index = {}.
> 2. For each (i, num) in enumerate(nums):
> 3.   If num in last_index and i - last_index[num] <= k: return True.
> 4.   last_index[num] = i.
> 5. Return False."

**Why this works:**
> "We only need the most recent index because earlier indices are further away.
> If the most recent occurrence is too far, all earlier ones are too."

**Edge cases:**
- k=0: No two distinct indices can have distance 0, so always False.
- All same elements: True if n>=2 and k>=1.
- k >= n: Any duplicate works.
- Empty array: False.

**Complexity:**
- Time:  O(n) - single pass.
- Space: O(min(n, k)) - hash map size bounded by n entries.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Hash map of last seen index (BEST - Memorize!)
```python
def contains_nearby_duplicate_1(nums, k):
    seen = {}
    for i, num in enumerate(nums):
        if num in seen and i - seen[num] <= k:
            return True
        seen[num] = i
    return False
```

### Way 2: Verbose version
### Way 3: Sliding window with set
### Way 4: Brute force O(n*k)
### Way 5: enumerate hash map
### Way 6: dict.get for clean lookup
### Way 7: defaultdict
### Way 8: deque sliding window
### Way 9: List as sliding window
### Way 10: any() with generator (brute force)
### Way 11: Class-based
### Way 12: zip-based window
### Way 13: OrderedDict (LRU)
### Way 14: Set with k=0 check
### Way 15: Early exit on k=0
### Way 16: List sliding window
### Way 17: Track all indices per value
### Way 18: One-liner
### Way 19: Most concise
### Way 20: Final cleanest (the one to memorize)

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Most efficient     | Way 1    | O(n) hash map|
| Small k            | Way 3    | Set window   |
| Simplicity         | Way 4    | Brute force  |
| Teaching/clear     | Way 1    | Easy to read |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Hash map (Way 1) | O(n) | O(min(n, k)) | Best general |
| Sliding set (Way 3) | O(n) | O(min(n, k)) | Bounded by k |
| Brute force (Way 4) | O(n*k) | O(1) | Worst case only |
| All indices (Way 17) | O(n) | O(n) | Extra space |

---

## Walkthrough Example

```
nums = [1, 2, 3, 1], k = 3

Iteration:
  i=0, num=1: last_index={}. Add 1->0. last_index={1:0}.
  i=1, num=2: last_index={1:0}. 2 not in map. Add 2->1. last_index={1:0, 2:1}.
  i=2, num=3: 3 not in map. Add 3->2. last_index={1:0, 2:1, 3:2}.
  i=3, num=1: 1 in map at j=0. Check: 3 - 0 = 3 <= 3. Return True! ✓

Result: True (nums[0]==nums[3], distance 3).
```

```
nums = [1, 0, 1, 1], k = 1

Iteration:
  i=0, num=1: Add 1->0. last_index={1:0}.
  i=1, num=0: Add 0->1. last_index={1:0, 0:1}.
  i=2, num=1: 1 in map at j=0. Check: 2 - 0 = 2 > 1. Update 1->2. last_index={1:2, 0:1}.
  i=3, num=1: 1 in map at j=2. Check: 3 - 2 = 1 <= 1. Return True! ✓

Result: True (nums[2]==nums[3], distance 1).
```

```
nums = [1, 2, 3, 1, 2, 3], k = 2

Iteration:
  i=0, num=1: Add 1->0.
  i=1, num=2: Add 2->1.
  i=2, num=3: Add 3->2.
  i=3, num=1: 1 in map at 0. Check: 3-0=3 > 2. Update 1->3.
  i=4, num=2: 2 in map at 1. Check: 4-1=3 > 2. Update 2->4.
  i=5, num=3: 3 in map at 2. Check: 5-2=3 > 2. Update 3->5.
  End. Return False.

Result: False (no duplicates within k=2).
```

---

## Best Answer to Memorize

```python
def contains_nearby_duplicate(nums, k):
    last_index = {}
    for i, num in enumerate(nums):
        if num in last_index and i - last_index[num] <= k:
            return True
        last_index[num] = i
    return False
```

**~5 lines. O(n) time. O(min(n, k)) space. Interview-ready!**

---

## Key Insights

### Why only most recent index?
> "Distance is monotone with index. If the most recent occurrence is too far,
> all earlier ones are too. So storing only the most recent is sufficient."

### Why O(min(n, k)) space?
> "The hash map size is at most n (one entry per unique value). But practically
> bounded by k+1 entries if we cleared entries beyond k (sliding window set).
> So O(min(n, k))."

### Why not brute force O(n*k)?
> "Brute force checks up to k neighbors for each element. For k=10^4 and n=10^3,
> that's 10^7 operations - slow. Hash map is O(n) total."

### Sliding window set vs hash map?
> "Sliding window set: keep only the last k elements. Bounded by k entries.
> Hash map: keep ALL elements. Bounded by n entries.
> Both O(n) time. Choose based on whether k is small (set) or n is small (map)."

### What about k=0?
> "Distance must be >= 1 (distinct indices). With k=0, no distance qualifies.
> So always False unless... well, never True. Add early exit for clarity."

---

## Test Cases

| nums | k | Expected | Notes |
|------|---|----------|-------|
| [1,2,3,1] | 3 | True | \|0-3\|=3 |
| [1,0,1,1] | 1 | True | \|2-3\|=1 |
| [1,2,3,1,2,3] | 2 | False | min dist = 3 |
| [1] | 1 | False | single elem |
| [1,1] | 1 | True | distance 1 |
| [1,1] | 0 | False | k=0 |
| [1,2,1] | 0 | False | k=0 |
| [] | 5 | False | empty |
| [1,1,1,1] | 2 | True | consecutive |
| [1,2,3,4,5] | 10 | False | all distinct |
| [1,2,3,4,1] | 3 | False | \|0-4\|=4 > 3 |
| [1,2,3,1] | 4 | True | \|0-3\|=3 <= 4 |
| [-1,-1] | 1 | True | negative nums |
| [1,2,1,3,1] | 2 | True | \|0-2\|=2 |

---

## Common Pitfalls

1. **Storing all indices**: Just need the most recent, not all.
2. **Confusing < and <=**: Use `<=` for distance (k is inclusive).
3. **Forgetting k=0 edge case**: Always returns False.
4. **Off-by-one in distance**: `i - j <= k` (not `< k`).
5. **Not using enumerate**: Need both index and value.

---

## Why This Problem Matters

> "Tests:
> 1. Hash map for index tracking.
> 2. Sliding window concept.
> 3. Understanding of when 'most recent' suffices.
> 4. Foundation for: caching, LRU eviction, time-series analysis."

---

## Beyond This Problem: Related Patterns

### 1. Contains Duplicate (LC 217)
```python
# Just check if any duplicate exists (no distance constraint).
def contains_duplicate(nums):
    return len(nums) != len(set(nums))
```

### 2. Contains Duplicate III (LC 220)
```python
# Distance <= k AND value difference <= t.
# Use sorted buckets by value // (t+1).
```

### 3. LRU Cache (LC 146)
```python
# Maintain cache of last k items, evict oldest.
# Same sliding window concept.
```

### 4. Minimum Absolute Difference (LC 1200)
```python
# Sort and check adjacent. Different pattern.
```

---

## Connection to Sliding Window

This problem is a classic **sliding window** application:

```
Window = last k elements.
Invariant: window contains elements at indices [max(0, i-k), i].

For each new element:
  - Check if it's in the window (duplicate).
  - Add to window.
  - Slide: remove elements that fell out of window.
```

The hash map approach is the "index-tracking" version, while the set
approach is the "window-content" version. Both O(n).

---

## Quick Checklist

When given a similar problem:
- [ ] What's the distance metric? (|i-j| here)
- [ ] What counts as "near"? (within k here)
- [ ] Do we need value-only or value+index? (both here)
- [ ] Is brute force O(n*k) acceptable? (no, O(n) better)
- [ ] Edge case: k=0? (always False)

---

## Two Approaches Comparison

**Hash map of last index:**
- ✅ Simpler logic.
- ✅ O(n) time, O(min(n,k)) space.
- ❌ Stores all seen elements (up to n).

**Sliding window set:**
- ✅ Bounded by k+1 elements.
- ✅ Same O(n) time.
- ❌ Slightly more code (add + remove).

Both are valid. The hash map is more common in interviews.

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 219 - Contains Duplicate II](https://leetcode.com/problems/contains-duplicate-ii/)
