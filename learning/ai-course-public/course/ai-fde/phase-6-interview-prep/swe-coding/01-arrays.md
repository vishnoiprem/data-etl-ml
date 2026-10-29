# SWE Coding Sub-Lesson 1 — Arrays (2 pointers, sliding window, prefix sum)

> **Arrays are the most common SWE coding pattern.** 30-40% of LeetCode medium problems are array problems. The FDE signal: a candidate who recognizes the pattern in the first 2 minutes, names the time + space complexity, and writes clean code with edge cases — is showing they can debug a codebase in production. **This sub-lesson covers 3 sub-patterns: 2 pointers, sliding window, prefix sum.**

---

## Why arrays are the FDE signal

The 3 things the interviewer is testing:

1. **Can you recognize the pattern?** The 3 sub-patterns (2 pointers, sliding window, prefix sum) cover 80% of array problems.
2. **Can you name the complexity?** "O(n) time, O(1) space" is the FDE answer. "It's fast" is a junior answer.
3. **Can you handle the edge cases?** Empty input, single element, all duplicates, negative numbers. The edge cases are the signal.

**The FDE pattern:** clarify → brute force → optimize → code → test. Same as the take-home, compressed to 25 minutes.

---

## Sub-pattern 1: 2 Pointers

**The pattern:** left + right pointers, move toward each other (or away from each other). O(n) time, O(1) space.

**When to use:** sorted array, palindrome check, pair sum, container with most water.

**The template:**

```python
def two_pointers(arr: list[int]) -> int:
    left, right = 0, len(arr) - 1
    result = 0
    while left < right:
        # Process arr[left] and arr[right]
        if condition:
            result = max(result, ...)
            left += 1
        else:
            right -= 1
    return result
```

**Sample problem 1: Two Sum (sorted array)**

> Given a sorted array of integers, find two numbers that add up to a target.

```python
def two_sum_sorted(arr: list[int], target: int) -> tuple[int, int]:
    left, right = 0, len(arr) - 1
    while left < right:
        total = arr[left] + arr[right]
        if total == target:
            return (left, right)
        elif total < target:
            left += 1
        else:
            right -= 1
    return (-1, -1)
```

**Time:** O(n). **Space:** O(1).

**Sample problem 2: Container With Most Water**

> Given an array of heights, find two lines that together with the x-axis form a container that holds the most water.

```python
def max_area(heights: list[int]) -> int:
    left, right = 0, len(heights) - 1
    max_water = 0
    while left < right:
        width = right - left
        height = min(heights[left], heights[right])
        max_water = max(max_water, width * height)
        if heights[left] < heights[right]:
            left += 1
        else:
            right -= 1
    return max_water
```

**Time:** O(n). **Space:** O(1).

**The 3 edge cases:** empty array, single element, all same heights.

---

## Sub-pattern 2: Sliding Window

**The pattern:** maintain a window of size k, slide it. O(n) time, O(1) space (or O(k) for the window contents).

**When to use:** contiguous subarray, fixed-size window, variable-size window with constraint.

**The template (fixed-size window):**

```python
def sliding_window_fixed(arr: list[int], k: int) -> int:
    window_sum = sum(arr[:k])
    result = window_sum
    for i in range(k, len(arr)):
        window_sum += arr[i] - arr[i - k]
        result = max(result, window_sum)
    return result
```

**The template (variable-size window):**

```python
def sliding_window_variable(arr: list[int], target: int) -> int:
    left = 0
    window_sum = 0
    result = float('inf')
    for right in range(len(arr)):
        window_sum += arr[right]
        while window_sum >= target:
            result = min(result, right - left + 1)
            window_sum -= arr[left]
            left += 1
    return result
```

**Sample problem 1: Maximum Sum Subarray of Size K**

> Given an array of integers, find the maximum sum of any contiguous subarray of size k.

```python
def max_sum_subarray_k(arr: list[int], k: int) -> int:
    if len(arr) < k:
        return 0
    window_sum = sum(arr[:k])
    max_sum = window_sum
    for i in range(k, len(arr)):
        window_sum += arr[i] - arr[i - k]
        max_sum = max(max_sum, window_sum)
    return max_sum
```

**Time:** O(n). **Space:** O(1).

**Sample problem 2: Longest Substring Without Repeating Characters**

> Given a string, find the length of the longest substring without repeating characters.

```python
def longest_substring(s: str) -> int:
    char_index = {}
    left = 0
    max_len = 0
    for right, char in enumerate(s):
        if char in char_index and char_index[char] >= left:
            left = char_index[char] + 1
        char_index[char] = right
        max_len = max(max_len, right - left + 1)
    return max_len
```

**Time:** O(n). **Space:** O(min(n, alphabet_size)).

**The 3 edge cases:** empty string, all same characters, all unique characters.

---

## Sub-pattern 3: Prefix Sum

**The pattern:** precompute cumulative sum, answer range queries in O(1). O(n) preprocessing, O(1) per query.

**When to use:** range sum queries, subarray sum equals K, product of array except self.

**The template:**

```python
def prefix_sum(arr: list[int]) -> list[int]:
    """Compute prefix sum array. prefix[i] = sum(arr[0:i])."""
    prefix = [0] * (len(arr) + 1)
    for i in range(len(arr)):
        prefix[i + 1] = prefix[i] + arr[i]
    return prefix

def range_sum(prefix: list[int], left: int, right: int) -> int:
    """Sum of arr[left:right+1] using prefix sum."""
    return prefix[right + 1] - prefix[left]
```

**Sample problem 1: Subarray Sum Equals K**

> Given an array of integers, find the total number of continuous subarrays whose sum equals k.

```python
def subarray_sum_equals_k(arr: list[int], k: int) -> int:
    count = 0
    prefix_sum = 0
    prefix_count = {0: 1}
    for num in arr:
        prefix_sum += num
        if prefix_sum - k in prefix_count:
            count += prefix_count[prefix_sum - k]
        prefix_count[prefix_sum] = prefix_count.get(prefix_sum, 0) + 1
    return count
```

**Time:** O(n). **Space:** O(n).

**Sample problem 2: Product of Array Except Self**

> Given an array of integers, return an array where each element is the product of all elements except itself. Don't use division.

```python
def product_except_self(arr: list[int]) -> list[int]:
    n = len(arr)
    result = [1] * n
    # Left products
    left_product = 1
    for i in range(n):
        result[i] = left_product
        left_product *= arr[i]
    # Right products
    right_product = 1
    for i in range(n - 1, -1, -1):
        result[i] *= right_product
        right_product *= arr[i]
    return result
```

**Time:** O(n). **Space:** O(1) (excluding output array).

**The 3 edge cases:** empty array, single element, contains zero.

---

## The 5 anti-patterns for arrays

1. **Jumping to code without a plan.** "I'll just start coding" is a junior answer. The plan is the signal.
2. **Skipping the edge cases.** Empty input, single element, all duplicates, negative numbers. The edge cases are the signal.
3. **Using the wrong data structure.** "I'll use a list when I need a hash table" is O(n) instead of O(1). The data structure is the signal.
4. **Not testing the code.** Walk through 1-2 examples out loud. The test is the signal.
5. **Not naming the complexity.** "O(n) time, O(1) space" is the FDE answer. "It's fast" is a junior answer.

---

## The 5 SWE coding etiquette rules for arrays

1. **Clarify the problem first.** "Can the array be empty? Are the numbers positive? Should I handle duplicates?" The questions are the signal.
2. **State the brute force.** "The naive solution is O(n²). Can I do better?" The brute force is the floor.
3. **State the optimized solution.** "I can use 2 pointers for O(n)." The optimization is the signal.
4. **Walk through the code out loud.** "I start with i=0, j=n-1. While i < j, I swap arr[i] and arr[j]..." The walkthrough is the signal.
5. **Test with edge cases.** "If the array is empty, I return []. If the array has 1 element, I return [arr[0]]." The edge cases are the signal.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "What's the time + space complexity?" | "O(n) time, O(1) space. The hash table is O(n) but the answer is O(1) because we only store the seen values." |
| 2. "How would you test this?" | "3 cases: empty input, single element, all duplicates. The edge cases are the canary." |
| 3. "How would you scale this to 1B records?" | "External sort + map-reduce. Or a streaming algorithm with O(1) memory. The trade-off is accuracy vs memory." |

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../practical-coding/README.md` | The AI-assisted coding round (the new norm) |
| `../system-design/README.md` | The 9 patterns (arrays underpin read-heavy systems) |
| `../behavioral/README.md` | The STAR format (for the wrap-up) |

---

## The thesis

**Arrays are the most common SWE coding pattern.** The candidate who recognizes the pattern in the first 2 minutes, names the time + space complexity, and writes clean code with edge cases — is showing they can debug a codebase in production.

**The 3 sub-patterns (2 pointers, sliding window, prefix sum) cover 80% of array problems.** The 2 sample problems per sub-pattern (6 total) are the muscle memory. Practice them out loud, time yourself at 25 minutes per problem, and rehearse with an AI assistant.

**General prep gets you past the resume screen. SWE coding prep gets you past the classic LeetCode round at Anthropic, OpenAI, Palantir, and AWS FDE.**