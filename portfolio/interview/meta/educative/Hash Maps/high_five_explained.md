# High Five - 10 Ways with How to Think

## The Problem
```
Given a list of [ID, score] pairs, compute the top 5 average score
for each student. Return result sorted by ID.

Top 5 average = sum of top 5 scores / 5 (integer division)

Example:
    items = [[1,91],[1,92],[2,93],[2,97],[1,60],
             [2,77],[1,65],[1,87],[1,100],[2,100],[2,98]]
    Output: [[1,87],[2,93]]
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
items = [[1, 91], [1, 92], [2, 93], [2, 97], [1, 60], [2, 77],
         [1, 65], [1, 87], [1, 100], [2, 100], [2, 98]]

Group by ID:
  ID 1: [91, 92, 60, 65, 87, 100]  -> top 5: [100, 92, 91, 87, 65] = 435/5 = 87
  ID 2: [93, 97, 77, 100, 98]      -> top 5: [100, 98, 97, 93, 77] = 465/5 = 93

Output: [[1, 87], [2, 93]]
```

### Step 2: The Steps
> "1. Group scores by ID using hashmap
> 2. For each ID, sort scores descending, take top 5
> 3. Calculate average (sum of top 5 / 5)
> 4. Sort result by ID"

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to group scores by student ID, then for each student take their top 5 scores and calculate the average."

**Approach:**
> "I'll use a hashmap (defaultdict) to group scores by ID. Then for each ID, I'll sort their scores in descending order, take the top 5, sum them, and divide by 5."

**Alternative (more efficient):**
> "If memory is a concern, I could use a min-heap of size 5 for each student - this way I never store more than 5 scores per student."

**Steps:**
> "1. Group scores by ID using hashmap
> 2. For each ID, sort scores descending and take top 5
> 3. Calculate average = sum(top 5) // 5
> 4. Sort result by ID and return"

---

## The 10 Implementations

### Way 1: defaultdict + sort (BEST - Memorize!)
```python
from collections import defaultdict

def highFive(items):
    scores = defaultdict(list)
    for item_id, score in items:
        scores[item_id].append(score)

    result = []
    for student_id in sorted(scores.keys()):
        top_five = sorted(scores[student_id], reverse=True)[:5]
        result.append([student_id, sum(top_five) // 5])

    return result
```

### Way 2: Manual Dictionary
Same logic, regular dict instead of defaultdict.

### Way 3: Using heapq (Efficient!)
```python
import heapq
from collections import defaultdict

def highFive(items):
    scores = defaultdict(list)
    for item_id, score in items:
        heapq.heappush(scores[item_id], score)
        # Keep only top 5 by popping smallest if we have more
        if len(scores[item_id]) > 5:
            heapq.heappop(scores[item_id])

    result = []
    for student_id in sorted(scores.keys()):
        top_five = scores[student_id]
        result.append([student_id, sum(top_five) // 5])

    return result
```

### Way 4: Dict + min-heap
Same as Way 3 with manual dict.

### Way 5: Counter-based
Uses regular dict with explicit checks.

### Way 6: List Comprehension
```python
return [[student_id, sum(sorted(s, reverse=True)[:5]) // 5]
        for student_id in sorted(scores.keys())]
```

### Way 7: Compact one-liner
```python
return [[k, sum(sorted(v, reverse=True)[:5]) // 5] for k in sorted(d)]
```

### Way 8-10: Variations
- Way 8: sorted and zip
- Way 9: Explicit top-5
- Way 10: Most compact with sorted output

---

## Decision Tree

```
+------------------+-------------+--------------+
| Scenario         | Best        | Why          |
+------------------+-------------+--------------+
| Cleanest         | defaultdict  | Readable     |
| Memory efficient | heapq        | O(k) space   |
| Pythonic         | List comp    | One line     |
+------------------+-------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Sort | O(n log n) | O(n) |
| Heap | O(n log k) | O(n) |

where n = total items, k = 5

---

## Walkthrough Example

```
items = [[1,91],[1,92],[2,93],[2,97],[1,60],
         [2,77],[1,65],[1,87],[1,100],[2,100],[2,98]]

Step 1: Group by ID
  scores = {1: [91,92,60,65,87,100], 2: [93,97,77,100,98]}

Step 2: For each ID, sort and take top 5
  ID 1: sorted desc = [100, 92, 91, 87, 65, 60]
        top 5 = [100, 92, 91, 87, 65]
        sum = 435, avg = 87
  
  ID 2: sorted desc = [100, 98, 97, 93, 77]
        top 5 = [100, 98, 97, 93, 77]
        sum = 465, avg = 93

Step 3: Sort result by ID
  [[1, 87], [2, 93]] ✓
```

## Best Answer to Memorize

```python
from collections import defaultdict

def highFive(items):
    scores = defaultdict(list)
    for item_id, score in items:
        scores[item_id].append(score)

    result = []
    for student_id in sorted(scores.keys()):
        top_five = sorted(scores[student_id], reverse=True)[:5]
        result.append([student_id, sum(top_five) // 5])

    return result
```

**11 lines. Clean. O(n log n) time.** 🚀

## Memory-Efficient Version (Heap)

```python
import heapq
from collections import defaultdict

def highFive(items):
    scores = defaultdict(list)
    for item_id, score in items:
        heapq.heappush(scores[item_id], score)
        if len(scores[item_id]) > 5:
            heapq.heappop(scores[item_id])

    result = []
    for student_id in sorted(scores.keys()):
        result.append([student_id, sum(scores[student_id]) // 5])

    return result
```

**Better when scores list is huge** - keeps only top 5 in memory.

## Test Cases

| items | Expected | Why |
|-------|----------|-----|
| Standard | [[1,87],[2,93]] | Mixed scores |
| All 90,80,70,60,50 | [[1,70]] | Avg of top 5 |
| Two students same | [[1,80],[2,80]] | Different IDs |

## When to Use Each

| Use Case | Best Approach |
|----------|---------------|
| Memory OK | defaultdict + sort (simplest) |
| Memory tight | heapq (constant per student) |
| Many scores | heapq (O(n log k)) |
