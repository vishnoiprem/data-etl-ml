# Custom Sort String - 10 Ways with How to Think

## The Problem
```
Given order and s, return any permutation of s where:
- Characters follow the relative order in `order`
- If x appears before y in order, x must appear before y in result
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
order = "cba", s = "abcd"

Output: any string where c comes before b, b comes before a
d (not in order) can go anywhere

Valid: "cbad", "cbda", "cdba", etc.
```

### Step 2: The Trick
> "Two-pass approach:
> 1. Output characters in the ORDER they appear in `order`
> 2. Then output the characters NOT in `order`"

### Step 3: Walkthrough
```
order = "cba", s = "abcd"

Step 1: Count chars in s: {a:1, b:1, c:1, d:1}

Step 2: For each char in order, output it (count times):
  'c': in s -> output "c"
  'b': in s -> output "cb"
  'a': in s -> output "cba"

Step 3: Output remaining chars:
  'd' -> output "cbad"

Result: "cbad" ✓
```

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to reorder s so that characters follow the order in 'order' string. Any characters in s that aren't in 'order' can go anywhere - typically at the end."

**Approach:**
> "I'll use a two-pass approach. First, I'll count occurrences of each char in s using a hashmap. Then I'll iterate through 'order' and add each character (as many times as it appears in s) to the result. Finally, I'll add any remaining chars that weren't in 'order'."

**Why this works:**
> "Since I'm iterating through 'order' first, characters in the result appear in the correct relative order. The remaining chars at the end can be in any order."

**Alternative:**
> "I could also use Python's sorted() with a custom key that maps each char to its position in 'order'. This is more elegant but less obvious."

**Edge cases:**
- What if a char in 'order' doesn't appear in s? Skip it (count is 0).
- What if all chars in s are in 'order'? Just output in order.
- What if no chars in 'order' appear in s? Return s as-is.

---

## The 10 Implementations

### Way 1: Counter + Loop (BEST - Memorize!)
```python
from collections import Counter

def custom_sort_string(order, s):
    count = Counter(s)
    result = []

    # First: chars that appear in order (in the right sequence)
    for char in order:
        if char in count:
            result.append(char * count[char])
            del count[char]

    # Then: remaining chars (not in order)
    for char in count:
        result.append(char * count[char])

    return "".join(result)
```

### Way 2: Dict + Loop
Same as Way 1 but using regular dict instead of Counter.

### Way 3: defaultdict
Uses `defaultdict(int)` and a `seen` set.

### Way 4: One-Liner
```python
def custom_sort_string(order, s):
    c = Counter(s)
    return "".join(ch * c.pop(ch, 0) for ch in order) + "".join(ch * cnt for ch, cnt in c.items())
```

### Way 5: Custom Sort Key (Elegant!)
```python
def custom_sort_string(order, s):
    order_map = {c: i for i, c in enumerate(order)}
    return "".join(sorted(s, key=lambda c: order_map.get(c, ord(c))))
```

### Way 6: List-based Counting
Uses array of 26 for letter counts (faster than dict).

### Way 7-10: More variations
- Way 7: Compact Counter
- Way 8: String builder list
- Way 9: In-place modification
- Way 10: Functional with reduce

---

## Decision Tree

```
+------------------+-------------+--------------+
| Scenario         | Best        | Why          |
+------------------+-------------+--------------+
| Quick & clean    | Counter     | Readable     |
| Elegant          | Sort key    | One line     |
| Performance      | Array count | O(1) lookup  |
+------------------+-------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Counter | O(n) | O(1) - only 26 chars |
| Sort key | O(n log n) | O(n) |
| Array count | O(n) | O(1) |

where n = len(s)

---

## Walkthrough Example

```
order = "cba", s = "abcd"

Pass 1: Count s -> {a:1, b:1, c:1, d:1}

Pass 2: Iterate order:
  c -> count[c]=1 -> "c", remove c
  b -> count[b]=1 -> "cb", remove b
  a -> count[a]=1 -> "cba", remove a

Pass 3: Remaining count: {d:1}
  d -> "cbad"

Result: "cbad" ✓
```

## Best Answer to Memorize

```python
from collections import Counter

def customSortString(order, s):
    count = Counter(s)
    result = []

    for char in order:
        if char in count:
            result.append(char * count[char])
            del count[char]

    for char in count:
        result.append(char * count[char])

    return "".join(result)
```

**11 lines. O(n) time. Clean. Interview-ready!** 🚀

## Test Cases

| order | s | Valid Outputs |
|-------|---|---------------|
| "cba" | "abcd" | "cbad", "cbda", "cdba" |
| "xyz" | "xyz" | "xyz" |
| "abc" | "cba" | "abc" |
| "kqep" | "pekeq" | "kqeep", "kqeee", etc. |

## Key Insight

> "Two-pass approach: First output chars in the ORDER they appear in `order`, then output the rest. This guarantees the relative order constraint."

The trick is that **iterating through `order` itself ensures the correct relative ordering** - we don't need to sort or compare!
