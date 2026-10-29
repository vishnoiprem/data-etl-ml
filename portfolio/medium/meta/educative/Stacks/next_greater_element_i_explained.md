# Next Greater Element I - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/next-greater-element-i

## The Problem
```
Given two arrays:
- nums1: subset of nums2 (unique elements)
- nums2: larger array

For each nums1[i], find the FIRST element to the RIGHT of nums1[i]'s
position in nums2 that is STRICTLY GREATER.

If no such element, return -1.

Examples:
    nums1 = [4,1,2], nums2 = [1,3,4,2]   -> [-1, 3, -1]
    nums1 = [2,4],   nums2 = [1,2,3,4]   -> [3, -1]

Constraints:
- 1 <= nums1.length <= nums2.length <= 1000
- 0 <= nums1[i], nums2[i] <= 10^4
- All integers in nums1 and nums2 are unique
- All integers of nums1 also appear in nums2
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
nums1 = [4, 1, 2], nums2 = [1, 3, 4, 2]

For 4 (at nums2[2]): look right of index 2 -> [2]. No greater. → -1
For 1 (at nums2[0]): look right of index 0 -> [3, 4, 2]. First greater: 3. → 3
For 2 (at nums2[3]): look right of index 3 -> []. No element. → -1

Result: [-1, 3, -1] ✓
```

### Step 2: The Trick
> "Use a MONOTONIC DECREASING STACK on nums2!
> - For each v in nums2:
>   - While stack top < v:
>     * POP and record next_greater[popped] = v
>   - Push v onto stack
> - Elements left in stack have no next greater (-1)
> - Then lookup each num in nums1 from the next_greater map"

### Step 3: Why Decreasing Stack?
> "Stack maintains elements WAITING for their next greater.
> They're in DECREASING order so that each new element v is greater
> than everything below it in the stack.
> When v arrives, it's the next greater for all smaller elements above.
> Pop them, record v as their answer, then push v to wait for its own."

---

## What to Say Aloud in the Interview

**Opening:**
> "I have two arrays. nums1 is a subset of nums2. For each element in
> nums1, I need to find the next greater element to its right in nums2."

**Key Insight:**
> "Use a MONOTONIC DECREASING STACK on nums2!
> - For each v in nums2:
>   - While stack non-empty AND stack top < v:
>     * next_greater[stack.pop()] = v
>   - Push v onto stack
> - At the end, lookup each num in nums1 from the map."

**Algorithm:**
> "1. Initialize empty stack and ng dict
> 2. For each v in nums2:
>    - While stack and stack[-1] < v:
>      * ng[stack.pop()] = v
>    - stack.append(v)
> 3. Return [ng.get(num, -1) for num in nums1]"

**Why this works:**
> "The stack maintains elements in DECREASING order that haven't
> found their next greater yet. When v arrives, it's greater than
> stack top (and everything below), so it's the answer for those.
> We pop them, record the answer, then push v to wait for its own
> next greater."

**Edge cases:**
- All decreasing in nums2: nothing pops, all -1
- All increasing in nums2: each element's next greater is the next one
- nums1 has elements not in nums2: not possible (nums1 subset of nums2)
- Single element nums2: that element gets -1

**Complexity:**
- Time: O(n + m) where n = len(nums1), m = len(nums2)
- Space: O(m) for the map and stack

---

## The 20 Implementations (Simple to Complex)

### Way 1: Stack on values + dict (BEST - Memorize!)
```python
def nextGreaterElement(nums1, nums2):
    ng = {}
    stack = []
    for v in nums2:
        while stack and stack[-1] < v:
            ng[stack.pop()] = v
        stack.append(v)
    return [ng.get(num, -1) for num in nums1]
```

### Way 2: Same with index-based stack
```python
stack = []  # indices
for i, num in enumerate(nums2):
    while stack and nums2[stack[-1]] < num:
        ng[nums2[stack.pop()]] = num
    stack.append(i)
```

### Way 3: Brute force O(n*m)
```python
for num in nums1:
    idx = nums2.index(num)
    # Look right
```

### Way 4: Pre-compute next_idx array
- For each position, find next index with greater value.

### Way 5: With deque

### Way 6-7: Functional variants

### Way 8: Most concise (same as Way 1)

### Way 9: Reverse iteration
- Iterate nums2 from end. Stack is strictly increasing.

### Way 10: Position dict

### Way 11: Class-based
```python
class NextGreaterFinder:
    def __init__(self, nums2):
        self.next_greater = {}
        self._build(nums2)
    def find(self, num):
        return self.next_greater.get(num, -1)
```

### Way 12-20: Various optimizations and styles
- Two-pass, enumerate, list comp + map, defaultdict, etc.

---

## Decision Tree

```
+------------------+----------+--------------+
| Scenario         | Best     | Why          |
+------------------+----------+--------------+
| Standard         | Way 1    | Clean stack  |
| Educational      | Way 3    | Simple brute |
| Reusable         | Way 11   | Class-based  |
+------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Stack (Way 1) | O(n+m) | O(m) |
| Brute (Way 3) | O(n*m) | O(1) |
| Reverse (Way 9) | O(n+m) | O(m) |

---

## Walkthrough Example

```
nums2 = [1, 3, 4, 2]
nums1 = [4, 1, 2]

Process nums2:
- 1: stack empty, push. stack=[1]
- 3: 3 > 1, pop 1, ng[1]=3. push 3. stack=[3]
- 4: 4 > 3, pop 3, ng[3]=4. push 4. stack=[4]
- 2: 2 < 4, no pop. push 2. stack=[4, 2]

ng map: {1: 3, 3: 4}
stack leftover: [4, 2] - no next greater

For each in nums1:
- 4: not in ng, return -1
- 1: in ng, return 3
- 2: not in ng, return -1

Result: [-1, 3, -1] ✓
```

## Best Answer to Memorize

```python
def nextGreaterElement(nums1, nums2):
    ng = {}
    stack = []
    for v in nums2:
        while stack and stack[-1] < v:
            ng[stack.pop()] = v
        stack.append(v)
    return [ng.get(num, -1) for num in nums1]
```

**8 lines. O(n+m) time. Clean. Interview-ready!**

---

## Key Insights

### Why decreasing stack?
> "Elements in stack are in DECREASING order (top is smallest).
> When a larger v arrives, it's the answer for everything smaller on
> the stack. Pop them. v goes on stack to wait for its own answer."

### Why "stack top < v" not "<="?
> "Strict inequality. Equal values are NOT 'greater'."

### Why not just brute force?
> "Brute force is O(n*m). For nums2 with 10^5 elements, this is too slow.
> Stack approach is O(n+m)."

### Why use a dict, not just the array?
> "We need to look up by VALUE (not position) when answering for nums1.
> Dict provides O(1) value-based lookup."

---

## Test Cases

| nums1 | nums2 | Result | Why |
|-------|-------|--------|-----|
| [4,1,2] | [1,3,4,2] | [-1,3,-1] | Standard |
| [2,4] | [1,2,3,4] | [3,-1] | Increasing nums2 |
| [1] | [1] | [-1] | Single, no next |
| [1] | [1,2] | [2] | Single, has next |
| [2] | [2,1] | [-1] | Decreasing |
| [3,2,1] | [1,2,3] | [-1,3,2] | Increasing |
| [1,2,3] | [3,2,1] | [-1,-1,-1] | Decreasing |

## Common Pitfalls

1. **Wrong inequality**: Use "<" not "<=" (strict greater required).
2. **Order of operations**: Pop BEFORE pushing the current value.
3. **Looking up wrong direction**: Must look RIGHT in nums2, not left.
4. **Forgetting -1 default**: Use dict.get(key, -1).
5. **Using index instead of value**: When popping, the value IS the key.

## Why This Problem Matters

> "Tests:
> 1. Monotonic stack pattern (CRITICAL - foundation for harder problems)
> 2. Pre-computation for efficient lookup
> 3. Strict inequality handling
> 4. Pattern similar to: Next Greater Element II, Daily Temperatures,
>    Largest Rectangle in Histogram, Stock Span
> 5. The MOST IMPORTANT template for stack-based problems!"
