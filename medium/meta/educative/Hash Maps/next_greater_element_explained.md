# Next Greater Element I - 10 Ways with How to Think

## The Problem
```
Given nums1 (subset of nums2), find the next greater element for each
nums1 element in nums2.

If no greater element exists, return -1.

Examples:
    nums1 = [4,1,2], nums2 = [1,3,4,2] -> [-1, 3, -1]
    nums1 = [2,4], nums2 = [1,2,3,4] -> [3, -1]
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
nums1 = [4, 1, 2]
nums2 = [1, 3, 4, 2]

For 4 in nums2: next greater is -1 (no greater to the right)
For 1 in nums2: next greater is 3
For 2 in nums2: next greater is -1

Output for nums1 = [4, 1, 2] -> [-1, 3, -1]
```

### Step 2: The Trick
> "Two-step approach:
> 1. Precompute next greater for ALL elements in nums2
> 2. Lookup answers for nums1 elements"

### Step 3: How to Find Next Greater
> "Use a **monotonic decreasing stack**:
> - Stack keeps elements waiting for their greater neighbor
> - When we see a bigger element, pop smaller ones and set their answer"

---

## What to Say Aloud in the Interview

**Opening:**
> "For each element in nums1, I need to find the next greater element to its right in nums2."

**Key Insight:**
> "Two-step approach:
> 1. Precompute the next greater element for ALL elements in nums2
> 2. Then look up the answers for nums1 elements in O(1)"

**Algorithm:**
> "I'll use a monotonic stack:
> - Stack keeps elements waiting for their greater neighbor (in decreasing order)
> - When I see a bigger element, I pop smaller ones - they found their next greater
> - Any remaining elements in the stack have no greater neighbor"

**Walkthrough:**
> "For nums2 = [1, 3, 4, 2]:
> - 1: stack=[], push 1 -> stack=[1]
> - 3: 1 < 3, pop 1, ng[1]=3, push 3 -> stack=[3]
> - 4: 3 < 4, pop 3, ng[3]=4, push 4 -> stack=[4]
> - 2: 4 > 2, just push -> stack=[4, 2]
> - Remaining: ng[4]=-1, ng[2]=-1"

---

## The 10 Implementations

### Way 1: Stack + HashMap (BEST - Memorize!)
```python
def nextGreaterElement(nums1, nums2):
    next_greater = {}
    stack = []

    for num in nums2:
        # Pop smaller elements - they found their next greater
        while stack and stack[-1] < num:
            smaller = stack.pop()
            next_greater[smaller] = num
        stack.append(num)

    # Remaining in stack have no greater
    for num in stack:
        next_greater[num] = -1

    return [next_greater[x] for x in nums1]
```

### Way 2: Using enumerate
Stores indices in stack instead of values.

### Way 3: Brute Force
```python
def nextGreaterElement(nums1, nums2):
    result = []
    for num in nums1:
        found = -1
        idx = nums2.index(num)
        for j in range(idx + 1, len(nums2)):
            if nums2[j] > num:
                found = nums2[j]
                break
        result.append(found)
    return result
```

### Way 4-10: Variations
- Way 4: Dict comprehension
- Way 5: defaultdict with default
- Way 6: Most compact with .get()
- Way 7: Explicit loop
- Way 8: Index lookup
- Way 9: Pre-compute
- Way 10: One-liner with map

---

## Decision Tree

```
+------------------+-------------+--------------+
| Scenario         | Best        | Why          |
+------------------+-------------+--------------+
| Optimal          | Stack       | O(n+m) time  |
| Simple           | Brute force | O(n*m)       |
| Most compact     | defaultdict | No .get()    |
+------------------+-------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Stack | O(n+m) | O(m) |
| Brute | O(n*m) | O(1) |

---

## Walkthrough Example

```
nums2 = [1, 3, 4, 2]

Process each element:
  num=1: stack empty, push -> [1]
  num=3: 1<3, pop 1, ng[1]=3, push -> [3]
  num=4: 3<4, pop 3, ng[3]=4, push -> [4]
  num=2: 4>2, push -> [4, 2]

After loop:
  Remaining [4, 2] -> ng[4]=-1, ng[2]=-1

ng = {1: 3, 3: 4, 4: -1, 2: -1}

For nums1 = [4, 1, 2]:
  4 -> ng[4] = -1
  1 -> ng[1] = 3
  2 -> ng[2] = -1

Result: [-1, 3, -1] ✓
```

## Best Answer to Memorize

```python
def nextGreaterElement(nums1, nums2):
    next_greater = {}
    stack = []

    for num in nums2:
        while stack and stack[-1] < num:
            next_greater[stack.pop()] = num
        stack.append(num)

    for num in stack:
        next_greater[num] = -1

    return [next_greater[x] for x in nums1]
```

**12 lines. O(n+m) time. Clean.** 🚀

## Even More Compact

```python
def nextGreaterElement(nums1, nums2):
    stack = []
    ng = {}
    for n in nums2:
        while stack and stack[-1] < n:
            ng[stack.pop()] = n
        stack.append(n)
    return [ng.get(x, -1) for x in nums1]
```

**5 lines! Uses `.get(x, -1)` for default value.**

## Why Monotonic Stack Works

```
Stack maintains decreasing order.
When a bigger element comes, it "serves" all smaller elements waiting.

Example: nums2 = [2, 1, 3]
- 2: push -> [2]
- 1: 2 > 1, just push -> [2, 1]
- 3: 1 < 3, pop 1, ng[1]=3
       2 < 3, pop 2, ng[2]=3
       push 3 -> [3]
```

The stack tells us: each popped element's next greater is the current number.

## Test Cases

| nums1 | nums2 | Expected | Why |
|-------|-------|----------|-----|
| [4,1,2] | [1,3,4,2] | [-1,3,-1] | 4 has nothing, 1->3, 2->nothing |
| [2,4] | [1,2,3,4] | [3,-1] | 2->3, 4 has nothing |
| [1] | [1,2,3] | [2] | 1->2 |
| [3,2,1] | [1,2,3] | [-1,3,-1] | 3 has nothing, 2->3, 1->2 |

## Key Insight

> "Precompute answers for ALL elements in nums2 using a monotonic stack. Then lookup is O(1) per nums1 element."

The monotonic stack is the key data structure - it efficiently finds next greater in O(n) total.
