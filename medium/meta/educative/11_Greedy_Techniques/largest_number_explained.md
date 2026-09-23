# Largest Number - 10 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/largest-number

## The Problem
```
Given a list of non-negative integers nums, rearrange them to form the largest
possible number. Return as a string.

Examples:
    [10, 2] -> "210"
    [3, 30, 34, 5, 9] -> "9534330"
    [0, 0] -> "0"

Constraints:
- 1 <= nums.length <= 100
- 0 <= nums[i] <= 10^3
```

## How I Think (The Mental Process)

### Step 1: Understand
```
Rearrange nums to form the largest concatenated number. Return as a string
because the result may overflow int.
```

### Step 2: The Trick
> "KEY INSIGHT: Custom comparator.
>
> For two numbers a, b: 'a' should come before 'b' in the result IF 'ab' > 'ba'
> (as concatenated strings).
>
> Equivalently: a + b > b + a means a comes first.
>
> In Python: use functools.cmp_to_key with a comparator that returns -1, 0, 1."

### Step 3: Why this works
> "Sorting by the pairwise-optimal comparator (a + b > b + a) yields a globally
> optimal sequence. Any inversion (a before b when 'ba' > 'ab') makes the result
> strictly smaller — by transposition argument."

### Step 4: Algorithm
> "1. Convert nums to strings.
> 2. Sort with comparator (a, b) -> -1 if a + b > b + a, +1 if a + b < b + a, 0 otherwise.
> 3. Concatenate.
> 4. If result starts with '0', return '0' (all zeros edge case)."

### Step 5: Edge cases
> "- All zeros: return '0' (not '000...0').
> - Single element: return its string form.
> - Mixed lengths: comparator handles any length."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to reorder nums to form the largest concatenated number, returned as a string."

**Key Insight:**
> "Sort strings such that 'a' comes before 'b' iff 'ab' > 'ba'. This pairwise-optimal comparator gives a globally optimal sort."

**Algorithm:**
> "1. Convert each num to string.
> 2. Sort with custom comparator using functools.cmp_to_key.
> 3. Concatenate.
> 4. Handle all-zeros edge case."

**Why this works:**
> "Any inversion in the sorted order would let us swap two adjacent numbers and strictly increase the result. So a fully sorted (by comparator) sequence is optimal."

**Edge cases:**
- All zeros: return '0'.
- Single element: trivial.

**Complexity:**
- Time:  O(n log n * k) where k is max string length.
- Space: O(n * k).

---

## The 10 Implementations (Simple to Complex)

### Way 1: cmp_to_key canonical (BEST - Memorize!)
```python
def largest_number(nums):
    from functools import cmp_to_key
    def compare(x, y):
        if x + y > y + x:
            return -1
        elif x + y < y + x:
            return 1
        return 0
    s = list(map(str, nums))
    s.sort(key=cmp_to_key(compare))
    result = ''.join(s)
    return '0' if result[0] == '0' else result
```

### Way 2: Sort by x*4 trick (BEST for short nums)
```python
def largest_number(nums):
    s = list(map(str, nums))
    s.sort(key=lambda x: x * 4, reverse=True)
    result = ''.join(s)
    return '0' if result[0] == '0' else result
```

### Way 3: Bubble sort with comparator
### Way 4: Selection sort with comparator
### Way 5: Insertion sort with comparator
### Way 6: Heap-based with custom key
### Way 7: Quicksort with comparator
### Way 8: Merge sort with comparator
### Way 9: Class-based
### Way 10: Final cleanest

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Standard           | Way 1    | cmp_to_key   |
| nums <= 999        | Way 2    | x*4 trick    |
| Verify optimality  | Way 7/8  | Custom sort  |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| cmp_to_key (Way 1) | O(n log n) | O(n) | Best |
| x*4 trick (Way 2) | O(n log n) | O(n) | For nums <= 999 |
| Bubble sort (Way 3) | O(n^2) | O(1) | Educational |
| Quicksort (Way 7) | O(n log n) avg | O(log n) | |
| Merge sort (Way 8) | O(n log n) | O(n) | Stable |

---

## Walkthrough Example

```
nums = [3, 30, 34, 5, 9]
Convert to strings: ['3', '30', '34', '5', '9']

Sort with comparator:
  Compare '3' vs '30': '330' vs '303' -> '330' bigger -> '3' first
  Compare '30' vs '34': '3034' vs '3430' -> '3430' bigger -> '34' first
  Compare '5' vs '34': '534' vs '345' -> '534' bigger -> '5' first
  Compare '9' vs '5': '95' vs '59' -> '95' bigger -> '9' first

Sorted: ['9', '5', '34', '3', '30']
Concatenate: "9534330"
```

---

## Best Answer to Memorize

```python
from functools import cmp_to_key

def largestNumber(nums):
    s = list(map(str, nums))
    s.sort(key=cmp_to_key(lambda a, b: -1 if a + b > b + a else (1 if a + b < b + a else 0)))
    return '0' if s[0] == '0' else ''.join(s)
```

**~5 lines. O(n log n) time. O(n) space. Interview-ready!**

---

## Key Insights

### Why custom comparator?
> "Standard numeric or lexicographic order doesn't give the right answer. We need pairwise-concatenation order."

### Why check leading zeros?
> "If all nums are 0, sorted result is '0...0'. We must return single '0'."

### What about Python's tuple-key trick (x*4)?
> "For nums[i] <= 10^3 (length <= 4), repeating each string 4 times makes standard lex sort behave like the comparator. But cmp_to_key is more general."

### What's the proof of optimality?
> "Transposition argument: any unsorted adjacent pair can be swapped to strictly increase the result. Hence sorted is best."

---

## Test Cases

| nums | Expected | Notes |
|------|----------|-------|
| [10, 2] | "210" | Standard |
| [3, 30, 34, 5, 9] | "9534330" | LeetCode |
| [0, 0] | "0" | All zeros |
| [121, 12] | "12121" | Same prefix |
| [9, 99, 999] | "999999" | Length cascade |
| [830, 8308] | "8308830" | Mid-prefix |

---

## Common Pitfalls

1. **All zeros**: Must return '0' (single zero), not '000...0'.
2. **Comparator sign**: -1 means a FIRST (a should come before b in result).
3. **String vs int sort**: Numbers must be compared as strings (with concatenation).
4. **Empty input**: Return '0' (or appropriate default).

---

## Why This Problem Matters

> "Tests:
> 1. Custom comparator design.
> 2. Edge case handling (leading zeros).
> 3. Foundation for: string comparison tricks, sort key transformations."

---

## Beyond This Problem: Related Patterns

### 1. Form Smallest Number
```python
# Same comparator with reversed direction.
```

### 2. Largest Number From At Most K Swaps
```python
# Bubble-sort-like greedy.
```

### 3. String Sorting with Custom Comparator
```python
# Generalizes to other ordering problems.
```

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 179 - Largest Number](https://leetcode.com/problems/largest-number/)