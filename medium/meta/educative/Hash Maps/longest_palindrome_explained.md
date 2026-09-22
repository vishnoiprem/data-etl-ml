# Longest Palindrome - 10 Ways with How to Think

## The Problem
```
Given a string of letters, return the length of the longest palindrome
that can be formed.

Letters are case-sensitive ("Aa" is NOT a palindrome).

Examples:
    "abccccdd" -> 7
    "a" -> 1
    "bb" -> 2
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
s = "abccccdd"

Longest palindrome that can be formed:
"dccaccd" -> length 7
(uses all: d-c-c-a-c-c-d)

Wait, "abccccdd" has: a=1, b=1, c=4, d=2
We can use even counts fully (c=4, d=2) + one odd count (a or b) for middle
= 4 + 2 + 1 = 7
```

### Step 2: The Trick
> "For a palindrome:
> - All even-count characters can be fully used
> - One odd-count character can be used (for the middle)
> - Other odd-count characters contribute (count - 1)"

### Step 3: Walkthrough
```
s = "abccccdd"
Counts: {a:1, b:1, c:4, d:2}

Even counts (use all): c=4, d=2 -> 6
Odd counts: a=1, b=1
  - Take one for middle: 1
  - Total: 6 + 1 = 7
```

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to find the longest palindrome that can be formed from the letters in the string."

**Key Insight:**
> "For a palindrome:
> - All even-count characters can be fully used
> - One odd-count character can be placed in the middle
> - Other odd-count characters contribute (count - 1)"

**Algorithm:**
> "1. Count occurrences of each character (case-sensitive!)
> 2. For each count, use the even part
> 3. If any odd count exists, add 1 for the middle"

**Why this works:**
> "A palindrome reads the same forwards and backwards, so characters on the left must mirror characters on the right. Even counts pair perfectly. One odd count can sit in the middle."

**Edge cases:**
- Empty string: 0
- Single character: 1
- All same characters: length of string
- Case sensitivity: "A" and "a" are different!

---

## The 10 Implementations

### Way 1: Counter + math (BEST - Memorize!)
```python
from collections import Counter

def longestPalindrome(s):
    counts = Counter(s)
    length = 0
    odd_found = False

    for count in counts.values():
        if count % 2 == 0:
            length += count
        else:
            length += count - 1
            odd_found = True

    return length + (1 if odd_found else 0)
```

### Way 2: Manual dict
Same logic, regular dict instead of Counter.

### Way 3: Set approach (Elegant!)
```python
def longestPalindrome(s):
    chars = set()
    length = 0

    for char in s:
        if char in chars:
            chars.remove(char)
            length += 2
        else:
            chars.add(char)

    return length + (1 if chars else 0)
```

### Way 4: defaultdict
Same as Way 1 with defaultdict.

### Way 5: Bit manipulation style
Uses `count // 2 * 2` to get even part.

### Way 6: Using Counter.most_common
Tracks if odd has been used for middle.

### Way 7: One-liner
```python
def longestPalindrome(s):
    counts = Counter(s)
    return sum(count // 2 * 2 for count in counts.values()) + (1 if any(c % 2 for c in counts.values()) else 0)
```

### Way 8: Most compact
```python
def longestPalindrome(s):
    c = Counter(s)
    return sum(v - v % 2 for v in c.values()) + any(v % 2 for v in c.values())
```

### Way 9: Array-based (faster)
Uses array of 52 for case-sensitive letter counts.

### Way 10: Single pass set
Uses set to track unpaired characters.

---

## Decision Tree

```
+------------------+-------------+--------------+
| Scenario         | Best        | Why          |
+------------------+-------------+--------------+
| Cleanest code    | Counter     | Readable     |
| Elegant          | Set         | One pass     |
| Performance      | Array       | O(1) lookup  |
+------------------+-------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Counter | O(n) | O(1) |
| Set | O(n) | O(1) |
| Array | O(n) | O(1) |

---

## Walkthrough Example

```
s = "abccccdd"

Counts: {a:1, b:1, c:4, d:2}

Using Way 1:
  a: count=1, odd -> length += 0, odd_found=True
  b: count=1, odd -> length += 0, odd_found=True (already)
  c: count=4, even -> length += 4 (length=4)
  d: count=2, even -> length += 2 (length=6)

Final: 6 + 1 = 7 ✓
```

## Best Answer to Memorize

```python
from collections import Counter

def longestPalindrome(s):
    counts = Counter(s)
    length = 0
    odd_found = False

    for count in counts.values():
        if count % 2 == 0:
            length += count
        else:
            length += count - 1
            odd_found = True

    return length + (1 if odd_found else 0)
```

**11 lines. O(n) time. Clean. Interview-ready!** 🚀

## Elegant Set Version

```python
def longestPalindrome(s):
    chars = set()
    length = 0

    for char in s:
        if char in chars:
            chars.remove(char)
            length += 2
        else:
            chars.add(char)

    return length + (1 if chars else 0)
```

## Test Cases

| s | Expected | Why |
|---|----------|-----|
| abccccdd | 7 | 4+2+1 |
| a | 1 | Single char |
| bb | 2 | Two same |
| AaBb | 4 | 4 different chars |
| abc | 1 | Only middle |
| aabbcc | 6 | All pairs |

## Key Insight

> "Use even counts fully. Add 1 if any odd count exists (for the middle). Case-sensitive: 'A' and 'a' are different characters!"

## Case Sensitivity Matters!

The problem explicitly says "Letters are case-sensitive. Hence, combinations such as 'Aa' are not considered palindromes."

This means:
- "Aa" -> can't form palindrome of length > 1 from these two chars together
- Each is treated separately
- "Aaaa" -> length 4 (A is one char, aaaa pairs)
