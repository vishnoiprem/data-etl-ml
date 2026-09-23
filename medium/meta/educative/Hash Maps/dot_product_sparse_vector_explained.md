# Dot Product of Two Sparse Vectors - 20 Ways with How to Think

## The Problem
```
Create a SparseVector class:
- Constructor: Initializes the object with the vector
- dotProduct(vec): Computes dot product with another sparse vector

A sparse vector contains mostly zeros. Store only non-zero entries.
```

## How I Think (The Mental Process)

### Step 1: What is a Sparse Vector?
> "A vector where MOST values are zero. Instead of storing all zeros, just store the non-zero positions."

```
Regular:  [0, 0, 0, 0, 5, 0, 0, 3, 0, 0]   (10 elements)
Sparse:   {4: 5, 7: 3}                     (2 entries only!)
```

### Step 2: What is Dot Product?
> "Multiply corresponding elements, sum them up."
```
[1, 2, 3] · [4, 5, 6] = 1*4 + 2*5 + 3*6 = 32
```

### Step 3: The Trick
> "Since most values are zero, skip them. Only multiply non-zero × non-zero."

### Step 4: Algorithm Options
| Approach | Time | Space | Best For |
|----------|------|-------|----------|
| Brute force | O(n) | O(n) | Dense vectors |
| HashMap | O(k) | O(k) | Many zeros |
| Two pointers | O(k1+k2) | O(k1+k2) | Both sparse |

(k = non-zero count, n = total length)

---

## What to Say Aloud in the Interview

**Opening:**
> "A sparse vector has mostly zeros. So instead of storing all n elements, I should store only the non-zero positions and values. That way, the constructor is O(n) but uses O(k) space where k is non-zero count."

**For HashMap approach:**
> "For dot product, I just iterate through one vector's non-zero entries and look them up in the other. This is O(k) which is much better than O(n) when the vector is truly sparse."

**For Two Pointers:**
> "Alternative: if both vectors are sparse, I can use two pointers over their sorted indices. This gives O(k1 + k2) without hashmap overhead."

**Edge cases to mention:**
> "What if both vectors are completely zero? Result is 0.
> What if they have no overlapping indices? Result is 0.
> What about negative numbers? My algorithm handles them naturally."

---

## The 20 Implementations

### Way 1: Basic HashMap (BEST - Memorize!)
```python
class SparseVector:
    def __init__(self, nums):
        self.data = {}
        for i, v in enumerate(nums):
            if v != 0:
                self.data[i] = v

    def dot_product(self, vec):
        result = 0
        for i, v in self.data.items():
            if i in vec.data:
                result += v * vec.data[i]
        return result
```

### Way 2: Dict Comprehension
```python
class SparseVector:
    def __init__(self, nums):
        self.data = {i: v for i, v in enumerate(nums) if v != 0}

    def dot_product(self, vec):
        return sum(self.data[i] * vec.data.get(i, 0) for i in self.data)
```

### Way 3: List of Tuples
```python
class SparseVector:
    def __init__(self, nums):
        self.data = [(i, v) for i, v in enumerate(nums) if v != 0]

    def dot_product(self, vec):
        vec_map = dict(vec.data)
        return sum(v * vec_map[i] for i, v in self.data if i in vec_map)
```

### Way 4: List of (index, value) pairs
```python
class SparseVector:
    def __init__(self, nums):
        self.pairs = [(i, nums[i]) for i in range(len(nums)) if nums[i] != 0]

    def dot_product(self, vec):
        vec_dict = dict(vec.pairs)
        return sum(v * vec_dict[i] for i, v in self.pairs if i in vec_dict)
```

### Way 5: Two Pointers (Optimal for Two Sparse)
```python
class SparseVector:
    def __init__(self, nums):
        self.pairs = [(i, v) for i, v in enumerate(nums) if v != 0]

    def dot_product(self, vec):
        i, j = 0, 0
        result = 0
        while i < len(self.pairs) and j < len(vec.pairs):
            if self.pairs[i][0] == vec.pairs[j][0]:
                result += self.pairs[i][1] * vec.pairs[j][1]
                i += 1
                j += 1
            elif self.pairs[i][0] < vec.pairs[j][0]:
                i += 1
            else:
                j += 1
        return result
```

### Way 6: Using Counter
```python
from collections import Counter

class SparseVector:
    def __init__(self, nums):
        self.data = Counter({i: v for i, v in enumerate(nums) if v != 0})

    def dot_product(self, vec):
        return sum(self.data[i] * vec.data[i] for i in self.data.keys() & vec.data.keys())
```

### Way 7: defaultdict
```python
from collections import defaultdict

class SparseVector:
    def __init__(self, nums):
        self.data = defaultdict(int, {i: v for i, v in enumerate(nums) if v != 0})

    def dot_product(self, vec):
        return sum(self.data[i] * vec.data.get(i, 0) for i in self.data)
```

### Way 8-10: Variants
- Way 8: One-line constructor
- Way 9: enumerate + filter
- Way 10: set intersection

### Way 11-15: Optimized versions
- Way 11: Compact with set
- Way 12: Generator
- Way 13: dict.get
- Way 14: Explicit loop
- Way 15: Two pointers (sorted)

### Way 16-20: Specialty versions
- Way 16: numpy
- Way 17: Most compact
- Way 18: Lambda
- Way 19: Two pointers unpack
- Way 20: Single line

---

## Decision Tree

```
+------------------+-------------+--------------+
| Vector           | Best        | Why          |
+------------------+-------------+--------------+
| Both sparse      | Two pointers| No hashmap   |
| One dense        | HashMap     | O(k) lookup  |
| Many dot products| HashMap     | Build once   |
+------------------+-------------+--------------+
```

## Complexity Comparison

| Approach | Time | Space | When |
|----------|------|-------|------|
| Brute | O(n) | O(n) | Always works |
| HashMap | O(k) | O(k) | Sparse vectors |
| Two pointers | O(k1+k2) | O(k1+k2) | Both sparse |

Where n = length, k = non-zero count.

## Walkthrough Example

```
nums1 = [1, 0, 0, 2, 3]  -> SparseVector1.data = {0: 1, 3: 2, 4: 3}
nums2 = [0, 3, 0, 4, 0]  -> SparseVector2.data = {1: 3, 3: 4}

dot_product:
  Iterate SparseVector1's data:
    i=0, v=1: 0 not in vec2.data -> skip
    i=3, v=2: 3 in vec2.data, vec2.data[3]=4 -> result += 2*4 = 8
    i=4, v=3: 4 not in vec2.data -> skip

Answer: 8 ✓
```

## Best Answer to Memorize

```python
class SparseVector:
    def __init__(self, nums):
        self.data = {i: v for i, v in enumerate(nums) if v != 0}

    def dot_product(self, vec):
        result = 0
        for i, v in self.data.items():
            if i in vec.data:
                result += v * vec.data[i]
        return result
```

**8 lines. Clean. O(k) time. Interview-ready!** 🚀

## What to Discuss With Interviewer

1. **Trade-off:** Space vs Time - we save space but pay for hashing
2. **When to use each:** HashMap for general case, Two Pointers when both are very sparse
3. **Optimization:** Iterate over smaller vector, lookup in larger
4. **Edge cases:** All zeros, no overlap, single non-zero element

## Test Cases

| nums1 | nums2 | Result | Why |
|-------|-------|--------|-----|
| [1,0,0,2,3] | [0,3,0,4,0] | 8 | 2*4=8 |
| [0,0,0] | [1,2,3] | 0 | No overlap |
| [1,2,3] | [4,5,6] | 32 | All overlap |
| [0,1,0,1] | [1,0,1,0] | 0 | No same position |
| [5,0,0,0,5] | [5,0,0,0,5] | 50 | 5*5+5*5=50 |
