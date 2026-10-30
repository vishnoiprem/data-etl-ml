# Valid Parentheses - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/valid-parentheses

## The Problem
```
Given a string of parentheses, check if they form a valid sequence.

Conditions:
- Every opening bracket must be closed by the same type
- Brackets must be closed in correct order

Examples:
    "()" -> True
    "()[]{}" -> True
    "(]" -> False
    "([)]" -> False
    "{[]}" -> True
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
s = "()[]{}" -> True (all matched correctly)
s = "(]" -> False (mismatched type)
s = "([)]" -> False (wrong order)
s = "{[]}" -> True (nested correctly)
```

### Step 2: The Trick
> "Use a STACK:
> - Push opening brackets
> - When you see a closing bracket, check if it matches the top of the stack
> - At end, stack should be empty"

### Step 3: Why Stack?
> "LIFO behavior - the LAST opening bracket must be closed FIRST.
> Stack naturally handles this!"

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to verify that brackets are properly matched and ordered."

**Key Insight:**
> "This is a classic stack problem because the LAST opening bracket must be closed FIRST. The LIFO behavior of a stack perfectly matches this requirement."

**Algorithm:**
> "1. For each character:
>    - If it's an opening bracket, push it on the stack
>    - If it's a closing bracket, check if it matches the top of the stack
>    - If matches, pop. If not, return False.
> 2. At the end, the stack should be empty for valid input."

**Why this works:**
> "The stack keeps track of which opening brackets are waiting to be closed. The top of the stack is always the most recent unclosed bracket, which must match the next closing bracket we encounter."

**Edge cases:**
- Single bracket: invalid (no pair)
- All opening: invalid (stack not empty at end)
- All closing: invalid (stack underflow)
- Empty string: valid (stack is empty)

---

## The 20 Implementations (Simple to Complex)

### Way 1: Basic Stack (BEST - Memorize!)
```python
def isValid(s):
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}

    for char in s:
        if char in mapping:
            if stack and stack[-1] == mapping[char]:
                stack.pop()
            else:
                return False
        else:
            stack.append(char)

    return not stack
```

### Way 2: With closing set
```python
def isValid(s):
    stack = []
    closing = {')', '}', ']'}
    pairs = {')': '(', '}': '{', ']': '['}

    for char in s:
        if char in closing:
            if not stack or stack[-1] != pairs[char]:
                return False
            stack.pop()
        else:
            stack.append(char)

    return len(stack) == 0
```

### Way 3: Replace approach (clever!)
```python
def isValid(s):
    while '()' in s or '[]' in s or '{}' in s:
        s = s.replace('()', '').replace('[]', '').replace('{}', '')
    return len(s) == 0
```

### Way 4: List as stack with explicit checks
```python
def isValid(s):
    stack = []
    for char in s:
        if char in '({[':
            stack.append(char)
        elif char == ')' and (not stack or stack.pop() != '('):
            return False
        elif char == '}' and (not stack or stack.pop() != '{'):
            return False
        elif char == ']' and (not stack or stack.pop() != '['):
            return False
    return not stack
```

### Way 5-10: Variations
- Way 5: zip-based mapping
- Way 6: counter-based
- Way 7: one-liner with reduce
- Way 8: try/except
- Way 9: enumerate
- Way 10: most compact

### Way 11-15: More variations
- Way 11: early exit
- Way 12: Stack class
- Way 13: explicit checks
- Way 14: collections.deque
- Way 15: helper function

### Way 16-20: Specialized
- Way 16: generator-based
- Way 17: push expected closer (elegant!)
- Way 18: explicit closing set
- Way 19: most elegant push-expected
- Way 20: cleanest

---

## The Elegant Push-Expected Trick

```python
def isValid(s):
    pairs = {'(': ')', '{': '}', '[': ']'}
    stack = []

    for c in s:
        if c in pairs:
            stack.append(pairs[c])  # Push what we expect
        elif stack and stack[-1] == c:
            stack.pop()
        else:
            return False

    return not stack
```

**Why elegant:** Push the EXPECTED closer. When we see the matching closer, just compare directly. No reverse lookup needed!

---

## Decision Tree

```
+------------------+-------------+--------------+
| Scenario         | Best        | Why          |
+------------------+-------------+--------------+
| Cleanest         | HashMap     | Readable     |
| Elegant          | Push expect | No reverse   |
| Performance      | Stack       | O(n) time    |
| Most compact     | One-liner   | Concise      |
+------------------+-------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Stack | O(n) | O(n) |

---

## Walkthrough Example

```
s = "{[]}"

Process:
  '{': push -> [{]
  '[': push -> [{, []
  ']': top=[], match! pop -> [{]
  '}': top={, match! pop -> []

Result: stack empty, return True ✓
```

```
s = "([)]"

Process:
  '(': push -> [(]
  '[': push -> [(, []
  ')': top=[, not '(' -> False!

Result: return False ✓
```

## Best Answer to Memorize

```python
def isValid(s):
    stack = []
    pairs = {')': '(', '}': '{', ']': '['}

    for char in s:
        if char in pairs:
            if not stack or stack.pop() != pairs[char]:
                return False
        else:
            stack.append(char)

    return not stack
```

**11 lines. O(n) time. Clean. Interview-ready!** 🚀

## Even More Elegant

```python
def isValid(s):
    pairs = {'(': ')', '{': '}', '[': ']'}
    stack = []

    for c in s:
        if c in pairs:
            stack.append(pairs[c])
        elif stack and stack[-1] == c:
            stack.pop()
        else:
            return False

    return not stack
```

## Test Cases

| s | Expected | Why |
|---|----------|-----|
| () | True | Pair |
| ()[]{} | True | All pairs |
| (] | False | Wrong type |
| ([)] | False | Wrong order |
| {[]} | True | Nested |
| ( | False | No close |
| ) | False | No open |

## Key Insight

> "Stack's LIFO behavior matches the requirement that the LAST opening bracket must be closed FIRST. The top of the stack is always the most recent unclosed bracket."

The "push expected closer" trick is super elegant - it eliminates the need for reverse lookups!
