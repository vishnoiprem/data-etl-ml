# Unique Number of Occurrences - 10 Ways with How to Think

## The Problem
```
Given an array, return True if each value has a unique number of occurrences.

Examples:
    [1, 2, 2, 1, 1, 3] -> True
        Counts: {1:3, 2:2, 3:1} - all unique counts

    [1, 2, 2, 1, 1, 3, 3] -> False
        Counts: {1:3, 2:2, 3:2} - '2' count appears twice

    [1, 1, 2, 2] -> False
        Counts: {1:2, 2:2} - both have count 2
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
nums = [1, 2, 2, 1, 1, 3]

Count occurrences:
  1 appears 3 times
  2 appears 2 times
  3 appears 1 time

Are all counts unique? {1, 2, 3} -> YES, all different!
Return: True
```

### Step 2: The Steps
> "1. Count occurrences of each number (hashmap)
> 2. Check if all counts are unique (compare count list vs count set)"

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to check if all elements in the array have unique counts of occurrences."

**Approach:**
> "I'll use a hashmap to count occurrences of each number. Then I'll check if all those counts are unique by comparing the length of the counts list to the length of the counts set."

**Why this works:**
> "If there are duplicates among the counts, then len(set) will be smaller than len(list). If all counts are unique, they'll be equal."

**Alternative:**
> "I could also sort the counts and check if any two adjacent counts are equal. Or I could use a set while building to detect duplicates early."

**Edge cases:**
- Single element: trivially unique
- All same numbers: only one count, unique
- Two elements with same count: False

---

## The 10 Implementations

### Way 1: Counter + set comparison (BEST - Memorize!)
```python
from collections import Counter

def uniqueOccurrences(nums):
    counts = Counter(nums)
    occurrences = list(counts.values())
    return len(occurrences) == len(set(occurrences))
```

### Way 2: Manual dict + set with early return
```python
def uniqueOccurrences(nums):
    counts = {}
    for num in nums:
        counts[num] = counts.get(num, 0) + 1

    seen = set()
    for count in counts.values():
        if count in seen:
            return False
        seen.add(count)
    return True
```

### Way 3: Using defaultdict
```python
from collections import defaultdict

def uniqueOccurrences(nums):
    counts = defaultdict(int)
    for num in nums:
        counts[num] += 1

    return len(set(counts.values())) == len(counts.values())
```

### Way 4: One-liner
```python
def uniqueOccurrences(nums):
    counts = Counter(nums)
    return len(set(counts.values())) == len(counts)
```

### Way 5: Using dict comprehension
```python
def uniqueOccurrences(nums):
    counts = {num: nums.count(num) for num in set(nums)}
    return len(set(counts.values())) == len(counts)
```

### Way 6: Sort and check adjacent
```python
def uniqueOccurrences(nums):
    counts = {}
    for num in nums:
        counts[num] = counts.get(num, 0) + 1

    sorted_counts = sorted(counts.values())
    for i in range(1, len(sorted_counts)):
        if sorted_counts[i] == sorted_counts[i-1]:
            return False
    return True
```

### Way 7: Most compact
```python
def uniqueOccurrences(nums):
    c = Counter(nums)
    return len(set(c.values())) == len(c)
```

### Way 8-10: Variations
- Way 8: List comprehension
- Way 9: Explicit comparison
- Way 10: Functional with reduce

---

## Decision Tree

```
+------------------+-------------+--------------+
| Scenario         | Best        | Why          |
+------------------+-------------+--------------+
| Cleanest         | Counter+set | Readable     |
| Early exit       | Dict+set    | O(n) fast    |
| No Counter       | defaultdict | No import    |
+------------------+-------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Counter | O(n) | O(n) |
| Sort | O(n log n) | O(n) |

---

## Walkthrough Example

```
nums = [1, 2, 2, 1, 1, 3]

Step 1: Count occurrences
  Counter: {1: 3, 2: 2, 3: 1}
  Values: [3, 2, 1]

Step 2: Check uniqueness
  set([3, 2, 1]) = {1, 2, 3}, length = 3
  len(list) = 3, len(set) = 3
  3 == 3 -> True ✓
```

```
nums = [1, 2, 2, 1, 1, 3, 3]

Step 1: Count occurrences
  Counter: {1: 3, 2: 2, 3: 2}
  Values: [3, 2, 2]

Step 2: Check uniqueness
  set([3, 2, 2]) = {2, 3}, length = 2
  len(list) = 3, len(set) = 2
  3 != 2 -> False ✓
```

## Best Answer to Memorize

```python
from collections import Counter

def uniqueOccurrences(nums):
    counts = Counter(nums)
    occurrences = list(counts.values())
    return len(occurrences) == len(set(occurrences))
```

**5 lines. O(n) time. Clean. Interview-ready!** 🚀

## Even Shorter:

```python
from collections import Counter

def uniqueOccurrences(nums):
    return len(set(Counter(nums).values())) == len(Counter(nums))
```

**2 lines. Same logic. Works!** 🚀

## Test Cases

| nums | Expected | Why |
|------|----------|-----|
| [1,2,2,1,1,3] | True | All counts unique (1,2,3) |
| [1,2,2,1,1,3,3] | False | '2' count appears twice |
| [1,1,2,2] | False | Both have count 2 |
| [-3,0,1,-3,1,1,1,-3,10,0] | True | Counts: 3,2,4,1 - all unique |
| [1] | True | Single element |
| [1,2] | True | Different counts (1 and 1) |
| [1,1,2] | True | Counts 2 and 1 |

## Key Insight

> "Use a hashmap to count occurrences, then check if all counts are unique. The trick: `len(set(counts)) == len(counts)` - duplicates make the set smaller!"
