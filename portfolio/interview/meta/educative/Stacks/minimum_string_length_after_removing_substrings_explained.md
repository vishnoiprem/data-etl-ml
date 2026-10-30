# Minimum String Length After Removing Substrings - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-string-length-after-removing-substrings

## The Problem
```
Given a string s with uppercase letters.
You can repeatedly remove "AB" or "CD" substrings.
After each removal, the string joins and may form new patterns.
Return the length of the shortest possible resulting string.

Examples:
    "ABFCACDB"      -> 2
    "ACBBD"         -> 5
    "ABAB"          -> 0
    "CABD"          -> 0  (CA + AB pops + CD pops)

Constraints:
- 1 <= s.length <= 100
- s consists only of uppercase English letters
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
s = "ABFCACDB"

Step 1: Remove "AB" at start -> "FCACDB"
Step 2: Remove "CD" at end -> "FCAB"
Step 3: Remove "AB" at end -> "FC"

Result length: 2

s = "ABAB"
Step 1: Remove "AB" -> ""
Step 2: Empty string

Result: 0

s = "CABD"
Step 1: Remove "AB" in middle -> "CD"
Step 2: Remove "CD" -> ""

Result: 0
```

### Step 2: The Trick
> "Use a STACK:
> - Push each char
> - When new char + stack[-1] is 'AB' or 'CD', POP (they cancel)
> - The remaining stack is the answer"

### Step 3: Why Stack?
> "When 'AB' is removed, the char before 'A' and char after 'B' become
> adjacent. The stack tracks the LAST unresolved char. When new char cancels
> with top, it's like the chars between got removed - new cancellations
> become possible!"

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to repeatedly remove 'AB' and 'CD' patterns until no more can be removed, then return the final length."

**Key Insight:**
> "This is a stack problem! Push each char. When a new char forms 'AB' or 'CD' with the top of the stack, pop them - this simulates the removal. The remaining stack length is the answer."

**Algorithm:**
> "1. Initialize empty stack
> 2. For each character in s:
>    - If stack is non-empty AND (stack[-1] + char) is in {'AB', 'CD'}:
>      * Pop the stack (the pattern is removed)
>    - Else:
>      * Push char onto stack
> 3. Return len(stack)"

**Why this works:**
> "When 'AB' is removed from position i..i+1, the chars before and after become adjacent. The stack tracks the LAST unresolved char at each position. When new char cancels with top, it naturally allows cascading cancellations."

**Edge cases:**
- Empty string: length 0
- No removable patterns: length unchanged
- All removable: length 0
- Single char: length 1

---

## The 20 Implementations (Simple to Complex)

### Way 1: Stack (BEST - Memorize!)
```python
def minLength(s):
    stack = []
    for char in s:
        if stack and stack[-1] + char in ("AB", "CD"):
            stack.pop()
        else:
            stack.append(char)
    return len(stack)
```

### Way 2: Replace Approach
```python
def minLength(s):
    while "AB" in s or "CD" in s:
        s = s.replace("AB", "").replace("CD", "")
    return len(s)
```

### Way 3: Two stacks (track removals)
### Way 4: deque-based
### Way 5: Explicit if-else (no string concat)
### Way 6: With set check
### Way 7: One-liner style
### Way 8: With reduce

### Way 9-12: Variations
- Way 9: List comprehension
- Way 10: Iterative mutation
- Way 11: Lookup table (lookup = {"A": "B", "C": "D"})
- Way 12: Recursive helper

### Way 13-16: Specialized
- Way 13: Try-except
- Way 14: Regex with re.sub
- Way 15: Most compact
- Way 16: Explicit pattern check (cleaner)

### Way 17-20: More variations
- Way 17: With enumerate
- Way 18: Most elegant (uses set)
- Way 19: String builder approach
- Way 20: Char class check

---

## Decision Tree

```
+------------------+-------------+--------------+
| Scenario         | Best        | Why          |
+------------------+-------------+--------------+
| Most efficient   | Stack       | O(n) single  |
| Most concise     | Way 15      | Fewest lines |
| Functional       | reduce      | No mutation  |
| Easy to read     | Stack       | Standard     |
+------------------+-------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Stack | O(n) | O(n) |
| Replace | O(n²) | O(n) |
| Regex | O(n²) | O(n) |

---

## Walkthrough Example

```
s = "ABFCACDB"

i=0, 'A': stack empty, push. stack=[A]
i=1, 'B': top='A', 'AB' matches! pop. stack=[]
i=2, 'F': push. stack=[F]
i=3, 'C': top='F', no match. push. stack=[F,C]
i=4, 'A': top='C', no match. push. stack=[F,C,A]
i=5, 'C': top='A', no match. push. stack=[F,C,A,C]
i=6, 'D': top='C', 'CD' matches! pop. stack=[F,C,A]
i=7, 'B': top='A', 'AB' matches! pop. stack=[F,C]

Final stack length: 2 ✓
```

```
s = "CABD"

i=0, 'C': [C]
i=1, 'A': top='C', 'CA' no. push. [C,A]
i=2, 'B': top='A', 'AB' matches! pop. [C]
i=3, 'D': top='C', 'CD' matches! pop. []

Final: 0 ✓
```

## Best Answer to Memorize

```python
def minLength(s):
    stack = []
    for char in s:
        if stack and stack[-1] + char in ("AB", "CD"):
            stack.pop()
        else:
            stack.append(char)
    return len(stack)
```

**8 lines. O(n) time. Clean. Interview-ready!**

## Key Insights

### Why "+ char" Creates the Pattern?
> "stack[-1] is the LAST char in the stack (a string).
> When we add the new char, we get a 2-char string.
> 'in' operator checks if it's in the tuple ('AB', 'CD')."

### Why NOT "Counter" Approach?
> "Counting chars alone is WRONG!
> Example: 'BA' has counter A=1, B=1, so min=1, predicts length 0.
> But 'BA' isn't a removable pattern! Only 'AB' is.
> We need ORDER information, which stack provides."

### Why Replace is O(n²)?
> "Each replace creates a new string O(n).
> We may need O(n) replacements.
> Total: O(n²).
> Stack does it in O(n) because we only iterate once."

## Test Cases

| s | Expected | Why |
|---|----------|-----|
| ABFCACDB | 2 | Multiple cascading removals |
| ACBBD | 5 | No patterns |
| ABAB | 0 | Fully removable |
| CDCD | 0 | Fully removable |
| ABC | 1 | AB pops, leaves C |
| CABD | 0 | AB then CD pops |
| AAAA | 4 | No AB patterns |
| (empty) | 0 | Empty input |
| AB | 0 | Single removal |
| BACAB | 3 | Complex ordering |

## Common Pitfalls

1. **Using counter instead of stack**: Wrong for non-adjacent chars
2. **Forgetting 'CD'**: Both patterns matter
3. **Using `==` instead of `in`**: Only matches "AB", not "CD"
4. **Replacing greedily**: Replace approach can miss cascading removals

## Why This Problem Matters

> "Tests:
> 1. Stack pattern recognition (CRUCIAL)
> 2. Cascading operations handling
> 3. Pattern matching with state
> 4. Why greedy replace is suboptimal
> 5. Pattern similar to: valid parentheses, remove duplicates, decode string"
