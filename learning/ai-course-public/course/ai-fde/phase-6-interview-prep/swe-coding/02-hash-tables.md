# SWE Coding Sub-Lesson 2 — Hash Tables (frequency counter, two-sum, group by)

> **Hash tables are the second most common SWE coding pattern.** 20-30% of LeetCode medium problems use hash tables. The FDE signal: a candidate who uses a hash table to go from O(n²) to O(n) is showing they understand the data structure choice. **This sub-lesson covers 3 sub-patterns: frequency counter, two-sum, group by.**

---

## Why hash tables are the FDE signal

The 3 things the interviewer is testing:

1. **Can you recognize when to use a hash table?** The 3 sub-patterns (frequency counter, two-sum, group by) cover 80% of hash table problems.
2. **Can you name the complexity?** "O(n) time, O(n) space" is the FDE answer. "It's fast" is a junior answer.
3. **Can you handle collisions?** Hash tables have collisions. The candidate who knows when to use a counter vs a defaultdict vs a regular dict is showing depth.

**The FDE pattern:** clarify → brute force → optimize → code → test. Same as arrays, but the optimization is usually a hash table.

---

## Sub-pattern 1: Frequency Counter

**The pattern:** count occurrences in O(n). Use a `dict` or `collections.Counter` or `collections.defaultdict`.

**When to use:** anagram check, find duplicates, find most frequent element, ransom note.

**The template:**

```python
from collections import Counter, defaultdict

def frequency_counter(arr: list) -> Counter:
    return Counter(arr)

def frequency_dict(arr: list) -> dict:
    freq = {}
    for item in arr:
        freq[item] = freq.get(item, 0) + 1
    return freq
```

**Sample problem 1: Valid Anagram**

> Given two strings, check if one is an anagram of the other.

```python
def is_anagram(s: str, t: str) -> bool:
    return Counter(s) == Counter(t)
```

**Time:** O(n). **Space:** O(n).

**Sample problem 2: Top K Frequent Elements**

> Given an array of integers, return the k most frequent elements.

```python
def top_k_frequent(arr: list[int], k: int) -> list[int]:
    freq = Counter(arr)
    # Use a bucket sort: index = frequency, value = list of elements
    bucket = [[] for _ in range(len(arr) + 1)]
    for num, count in freq.items():
        bucket[count].append(num)
    result = []
    for i in range(len(bucket) - 1, 0, -1):
        result.extend(bucket[i])
        if len(result) == k:
            return result
    return result
```

**Time:** O(n). **Space:** O(n).

**The 3 edge cases:** empty array, k > len(arr), all same elements.

---

## Sub-pattern 2: Two-Sum

**The pattern:** store seen values, check complement in O(n).

**When to use:** two-sum, three-sum, four-sum, subarray sum equals K.

**The template:**

```python
def two_sum_hash(arr: list[int], target: int) -> tuple[int, int]:
    seen = {}  # value -> index
    for i, num in enumerate(arr):
        complement = target - num
        if complement in seen:
            return (seen[complement], i)
        seen[num] = i
    return (-1, -1)
```

**Sample problem 1: Two Sum (unsorted)**

> Given an array of integers, return the indices of two numbers that add up to a target.

```python
def two_sum(arr: list[int], target: int) -> tuple[int, int]:
    seen = {}
    for i, num in enumerate(arr):
        complement = target - num
        if complement in seen:
            return (seen[complement], i)
        seen[num] = i
    return (-1, -1)
```

**Time:** O(n). **Space:** O(n).

**Sample problem 2: Subarray Sum Equals K**

> Given an array of integers, find the total number of continuous subarrays whose sum equals k.

```python
def subarray_sum(arr: list[int], k: int) -> int:
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

**The 3 edge cases:** empty array, no valid subarray, all zeros.

---

## Sub-pattern 3: Group By

**The pattern:** group items by key. Use a `defaultdict(list)`.

**When to use:** group anagrams, group by category, merge intervals by key.

**The template:**

```python
from collections import defaultdict

def group_by(items: list, key_fn) -> dict:
    groups = defaultdict(list)
    for item in items:
        groups[key_fn(item)].append(item)
    return dict(groups)
```

**Sample problem 1: Group Anagrams**

> Given an array of strings, group the anagrams together.

```python
def group_anagrams(strs: list[str]) -> list[list[str]]:
    groups = defaultdict(list)
    for s in strs:
        key = tuple(sorted(s))
        groups[key].append(s)
    return list(groups.values())
```

**Time:** O(n × k log k) where k is the average string length. **Space:** O(n × k).

**Sample problem 2: Group by Category (e.g., users by department)**

> Given a list of users, group them by department.

```python
def group_by_department(users: list[dict]) -> dict[str, list[dict]]:
    groups = defaultdict(list)
    for user in users:
        groups[user["department"]].append(user)
    return dict(groups)
```

**Time:** O(n). **Space:** O(n).

**The 3 edge cases:** empty list, single user, missing department field.

---

## Hash table vs sorted array: when to use which

| Scenario | Use hash table | Use sorted array |
|---|---|---|
| Lookup by key | O(1) | O(log n) |
| Insert/delete | O(1) | O(n) |
| Range query | O(n) | O(log n + k) |
| Ordered iteration | No | Yes |
| Memory | O(n) | O(n) |

**The FDE answer:** "If I need O(1) lookup, I use a hash table. If I need ordered iteration or range queries, I use a sorted array. The trade-off is memory vs speed."

---

## The 5 anti-patterns for hash tables

1. **Jumping to code without a plan.** "I'll just start coding" is a junior answer. The plan is the signal.
2. **Skipping the edge cases.** Empty input, single element, all duplicates, missing field. The edge cases are the signal.
3. **Using the wrong hash function.** "I'll hash a list" is wrong; lists aren't hashable. Use a tuple.
4. **Not handling collisions.** Hash tables have collisions. The candidate who knows when to use a counter vs a defaultdict vs a regular dict is showing depth.
5. **Not naming the complexity.** "O(n) time, O(n) space" is the FDE answer. "It's fast" is a junior answer.

---

## The 5 SWE coding etiquette rules for hash tables

1. **Clarify the problem first.** "Can the array be empty? Are the numbers positive? Should I handle duplicates?" The questions are the signal.
2. **State the brute force.** "The naive solution is O(n²). Can I do better?" The brute force is the floor.
3. **State the optimized solution.** "I can use a hash table for O(n)." The optimization is the signal.
4. **Walk through the code out loud.** "I iterate through the array. For each element, I check if the complement is in the hash table..." The walkthrough is the signal.
5. **Test with edge cases.** "If the array is empty, I return (-1, -1). If no two numbers add up, I return (-1, -1)." The edge cases are the signal.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "What's the time + space complexity?" | "O(n) time, O(n) space. The hash table is O(n) but each lookup is O(1) on average." |
| 2. "How would you test this?" | "3 cases: empty input, single element, all duplicates. The edge cases are the canary." |
| 3. "What if the input is a stream?" | "I'd use a hash table with a sliding window. The trade-off is memory vs accuracy." |

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../practical-coding/README.md` | The AI-assisted coding round (the new norm) |
| `../system-design/README.md` | The 9 patterns (hash tables underpin Pattern 1: read-heavy systems) |
| `../swe-coding/01-arrays.md` | The 2 pointers / sliding window / prefix sum patterns |

---

## The thesis

**Hash tables are the second most common SWE coding pattern.** The candidate who uses a hash table to go from O(n²) to O(n), names the complexity, and handles the edge cases — is showing they understand the data structure choice.

**The 3 sub-patterns (frequency counter, two-sum, group by) cover 80% of hash table problems.** The 2 sample problems per sub-pattern (6 total) are the muscle memory. Practice them out loud, time yourself at 25 minutes per problem, and rehearse with an AI assistant.

**General prep gets you past the resume screen. SWE coding prep gets you past the classic LeetCode round at Anthropic, OpenAI, Palantir, and AWS FDE.**