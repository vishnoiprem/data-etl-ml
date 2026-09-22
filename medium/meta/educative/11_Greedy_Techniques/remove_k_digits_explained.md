# Remove K Digits - 20 Ways

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/remove-k-digits

## The Problem
```
Given string num representing a non-negative integer and int k,
remove exactly k digits to form the smallest possible number.

Examples:
    num="1432219", k=3 -> "1219"
    num="10200", k=1 -> "200"
    num="10", k=2 -> "0"

Constraints:
- 1 <= k <= num.length <= 10^5
- num consists only of digits.
```

## How I Think (The Mental Process)

### Step 1: Understand
```
We have a numeric string and need to remove exactly k digits. We want the
smallest possible result (in numeric value).
```

### Step 2: The Trick
> "KEY INSIGHT: Monotonic stack (greedy).
>
> Process each digit from left to right. Maintain a stack of 'kept' digits.
> Before pushing the current digit, while the stack top is GREATER than the
> current digit AND we still have removals (k > 0), pop the stack top.
>
> Popping a bigger digit in favor of a smaller one (later in the number)
> always makes the result smaller."

### Step 3: Why this works
> "Consider digits at positions i and i+1 where num[i] > num[i+1]. Swapping
> them makes the number smaller lexicographically (and numerically, for same
> length). Each pop corresponds to one such swap, hence one removal.
>
> After processing all digits, if k > 0, the remaining digits are in
> non-decreasing order, so we pop from the END (rightmost = largest)."

### Step 4: Algorithm
> "1. Initialize empty stack.
> 2. For each digit:
>    - While k > 0 and stack and stack[-1] > digit:
>      stack.pop(); k -= 1
>    - stack.append(digit)
> 3. If k > 0: stack = stack[:-k]
> 4. result = ''.join(stack).lstrip('0')
> 5. Return result or '0' if empty."

### Step 5: Edge cases
> "- Leading zeros: Strip them; return '0' if all zeros.
> - k == len(num): Return '0'.
> - k == 0: Return num unchanged.
> - Single digit: Remove it, return '0'."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to remove k digits to form the smallest possible number. This is a classic monotonic stack greedy."

**Key Insight:**
> "Whenever the next digit is smaller than the stack top, the top should be removed (if k > 0). This swaps a larger digit for a smaller one in an earlier position."

**Algorithm:**
> "1. Build a stack greedily. Before each push, pop larger digits from the top, consuming k.
> 2. After processing, if k remains, drop from the end (rightmost).
> 3. Strip leading zeros."

**Why this works:**
> "Each pop corresponds to making the number smaller by replacing a big digit with a smaller one. After processing, k removals are guaranteed."

**Edge cases:**
- All digits removed: return '0'.
- Leading zeros: strip them.
- k == 0: return num.

**Complexity:**
- Time:  O(n). Each digit pushed/popped at most once.
- Space: O(n) for the stack.

---

## The 20 Implementations (Simple to Complex)

### Way 1: Monotonic stack (BEST - Memorize!)
```python
def removeKdigits(num, k):
    stack = []
    for digit in num:
        while k > 0 and stack and stack[-1] > digit:
            stack.pop()
            k -= 1
        stack.append(digit)
    stack = stack[:-k] if k else stack
    result = ''.join(stack).lstrip('0')
    return result if result else '0'
```

### Way 2: Stack with explicit counter
### Way 3: List as stack
### Way 4: Two-pointer / index-based stack
### Way 5: Class-based
### Way 6: Recursive with memo
### Way 7: numpy vectorized
### Way 8: lru_cache decorator
### Way 9: Brute force (combinations)
### Way 10: Helper for smallest
### Way 11: deque-based
### Way 12: enumerate-based
### Way 13: Generator
### Way 14: Reduce
### Way 15: Tabulation style with trim
### Way 16: Stateful
### Way 17: Greedy with for-else
### Way 18: With pop counter
### Way 19: Heap conceptual
### Way 20: Final cleanest

---

## Decision Tree

```
+--------------------+----------+--------------+
| Scenario           | Best     | Why          |
+--------------------+----------+--------------+
| Standard           | Way 1    | O(n) O(n)    |
| Conceptually clear | Way 10   | Recursive    |
| Verify correctness | Way 9    | Brute force  |
+--------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Monotonic stack (Way 1) | O(n) | O(n) | Best |
| Brute force (Way 9) | O(C(n,k) * n) | O(n) | Exponential |
| Recursive (Way 10) | O(n^2) worst | O(n) | Stack depth |

---

## Walkthrough Example

```
num = "1432219", k = 3

Step 1: digit='1', stack=[], push '1'.        stack=['1']
Step 2: digit='4', top='1' < '4', push '4'.    stack=['1','4']
Step 3: digit='3', top='4' > '3', pop. k=2.   stack=['1']
        push '3'.                              stack=['1','3']
Step 4: digit='2', top='3' > '2', pop. k=1.    stack=['1']
        push '2'.                              stack=['1','2']
Step 5: digit='2', top='2' == '2', push.       stack=['1','2','2']
Step 6: digit='1', top='2' > '1', pop. k=0.    stack=['1','2']
        push '1'.                              stack=['1','2','1']
Step 7: digit='9', top='1' < '9', push.        stack=['1','2','1','9']

k=0, no trim. result = '1219'.
```

---

## Best Answer to Memorize

```python
def removeKdigits(num, k):
    stack = []
    for digit in num:
        while k and stack and stack[-1] > digit:
            stack.pop()
            k -= 1
        stack.append(digit)
    final = stack[:-k] if k else stack
    result = ''.join(final).lstrip('0')
    return result or '0'
```

**~10 lines. O(n) time. O(n) space. Interview-ready!**

---

## Key Insights

### Why monotonic stack?
> "The stack stays non-decreasing. Each pop removes a 'big before small' inversion, which is the local optimal choice for making the number smaller."

### Why pop at most k times total?
> "Each pop consumes one of the k removals. We never pop more than k times."

### Why strip leading zeros at the end?
> "Removing early digits can leave leading zeros. They must be stripped, and if the result is empty, return '0'."

### Why is brute force exponential?
> "C(n,k) ways to choose which digits to keep. For n=10^5, this is intractable. The greedy approach is provably optimal."

---

## Test Cases

| num | k | Expected | Notes |
|-----|---|---------|-------|
| 1432219 | 3 | 1219 | Standard |
| 10200 | 1 | 200 | With zeros |
| 10 | 2 | 0 | Remove all |
| 112 | 1 | 11 | Same digits |
| 9 | 1 | 0 | Single |
| 1234567890 | 9 | 0 | Remove all but one |
| 1234 | 0 | 1234 | k=0 |
| 1234 | 4 | 0 | k=n |

---

## Common Pitfalls

1. **Leading zeros**: Always strip them at the end; return '0' if all zeros.
2. **Trim from end**: If k > 0 after processing, the stack is non-decreasing, so remove from end.
3. **Stack growth**: Each digit is pushed once, popped at most once. O(n) total operations.
4. **Empty result**: After strip, if result is '', return '0'.

---

## Why This Problem Matters

> "Tests:
> 1. Monotonic stack greedy.
> 2. Recognizing the 'remove bigger-before-smaller' pattern.
> 3. Foundation for: largest number, smallest subsequence, etc."

---

## Beyond This Problem: Related Patterns

### 1. Largest Number (LC 179)
```python
# Reverse problem: arrange digits to form the largest number.
```

### 2. Smallest Subsequence of Distinct Characters (LC 1081)
```python
# Monotonic stack with distinctness constraint.
```

### 3. Remove Duplicate Letters (LC 316)
```python
# Monotonic stack with last-occurrence tracking.
```

---

## Sources

- [Educative - Grokking the Coding Interview Patterns](https://www.educative.io/courses/grokking-coding-interview-in-python/)
- [LeetCode 402 - Remove K Digits](https://leetcode.com/problems/remove-k-digits/)