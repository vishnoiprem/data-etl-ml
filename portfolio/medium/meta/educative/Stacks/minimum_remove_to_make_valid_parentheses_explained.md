# Minimum Remove to Make Valid Parentheses - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/minimum-remove-to-make-valid-parentheses

## The Problem
```
Given a string s with '(', ')', and lowercase letters, remove the MINIMUM number
of parentheses so that the resulting string is valid.

Conditions:
- After removal, the string must be valid parens
- Removal must be MINIMAL
- Order of remaining characters is preserved

Examples:
    "lee(t(c)o)de)" -> "lee(t(c)o)de"
    "a)b(c)d"       -> "ab(c)d"
    "))(("          -> ""
    "(a(b(c)d)"     -> "a(b(c)d)"  or "(a(bc)d)"
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
s = "lee(t(c)o)de)"
     lee(t(c)o)de)   <- extra ')' at end must go
     Result: lee(t(c)o)de

s = "))(("
     4 parens, all unmatched
     Result: ""

s = "(a(b(c)d)"
     '(' opens, 'a', '(' opens, 'b', '(' opens, 'c', ')' closes inner, 'd', no ')' for the outer '('
     Unmatched: the LAST '('
     Result: "a(b(c)d)" or "(a(bc)d)"
```

### Step 2: The Trick
> "Use a STACK of INDICES:
> - Push index of '(' as we see it
> - On ')', pop if stack has '(' (matched), else mark ')' for removal
> - At end, leftover '(' indices in stack are unmatched - mark them too
> - Build string from original, skipping marked indices"

### Step 3: Why Stack?
> "LIFO - ')' MUST match the most recent unclosed '('. Stack handles this naturally.
> We store INDICES (not chars) so we know exactly which positions to remove."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to remove the minimum number of parentheses to make the string valid, keeping the order of all other characters."

**Key Insight:**
> "There are only TWO types of 'bad' parentheses:
> 1. ')' that have no matching '(' before them (extra closing)
> 2. '(' that have no matching ')' after them (extra opening)
> I find both in one pass with a stack of indices!"

**Algorithm:**
> "1. Iterate through s, tracking unmatched '(' indices in a stack
> 2. For each ')':
>    - If stack is non-empty, pop (this ')' matches the most recent '(')
>    - Else, this ')' is unmatched - mark it for removal
> 3. After iteration, any indices left in stack are unmatched '(' - mark them
> 4. Build result by skipping marked indices"

**Why stack works:**
> "When I see a ')', it MUST close the MOST RECENTLY opened unclosed '('.
> That's LIFO - perfect match for a stack!"

**Edge cases:**
- All closing brackets: '))((' -> ''
- All opening brackets: '(((' -> ''
- Already valid: '(abc)' -> unchanged
- No parentheses: 'abc' -> unchanged
- Multiple unmatched in different positions

---

## The 20 Implementations (Simple to Complex)

### Way 1: Stack of Indices (BEST - Memorize!)
```python
def minRemoveToMakeValid(s):
    stack = []
    to_remove = set()

    for i, char in enumerate(s):
        if char == '(':
            stack.append(i)
        elif char == ')':
            if stack:
                stack.pop()
            else:
                to_remove.add(i)

    to_remove.update(stack)
    return "".join(c for i, c in enumerate(s) if i not in to_remove)
```

### Way 2: Two-Pass Counter (O(1) auxiliary logic per pass)
```python
def minRemoveToMakeValid(s):
    # Pass 1: remove invalid ')'
    sb = []
    balance = 0
    for c in s:
        if c == ')':
            if balance == 0:
                continue
            balance -= 1
        elif c == '(':
            balance += 1
        sb.append(c)

    # Pass 2: remove extra '(' from right
    result = []
    to_remove = balance
    for c in reversed(sb):
        if c == '(' and to_remove > 0:
            to_remove -= 1
            continue
        result.append(c)
    return "".join(reversed(result))
```

### Way 3: Stack of Characters
```python
def minRemoveToMakeValid(s):
    stack = []
    for c in s:
        if c == ')':
            # Count balance in current stack
            o = stack.count('(')
            cl = stack.count(')')
            if o > cl:
                stack.append(c)
        else:
            stack.append(c)
    # Drop excess '(' from right
    o = stack.count('(')
    cl = stack.count(')')
    extras = o - cl
    result = []
    for c in reversed(stack):
        if c == '(' and extras > 0:
            extras -= 1
            continue
        result.append(c)
    return "".join(reversed(result))
```

### Way 4: With Helper Functions (cleaner separation)
```python
def remove_invalid_closing(string):
    sb = []
    count = 0
    for c in string:
        if c == ')':
            if count == 0:
                continue
            count -= 1
        if c == '(':
            count += 1
        sb.append(c)
    return "".join(sb)


def remove_invalid_opening(string):
    sb = []
    count = 0
    for c in reversed(string):
        if c == '(':
            if count == 0:
                continue
            count -= 1
        if c == ')':
            count += 1
        sb.append(c)
    return "".join(reversed(sb))


def minRemoveToMakeValid(s):
    return remove_invalid_opening(remove_invalid_closing(s))
```

### Way 5: Same as Way 1 (cleaner naming)
### Way 6: List mutable marks
### Way 7: deque + indices
### Way 8: Recursive
### Way 9: Replace approach

### Way 10: Counter only
```python
def minRemoveToMakeValid(s):
    # Pass 1
    chars = list(s)
    open_count = 0
    for i, c in enumerate(chars):
        if c == '(':
            open_count += 1
        elif c == ')':
            if open_count > 0:
                open_count -= 1
            else:
                chars[i] = ''

    # Pass 2 (reverse)
    s_clean = "".join(chars)
    chars2 = list(s_clean)
    close_count = 0
    for i in range(len(chars2) - 1, -1, -1):
        c = chars2[i]
        if c == ')':
            close_count += 1
        elif c == '(':
            if close_count > 0:
                close_count -= 1
            else:
                chars2[i] = ''
    return "".join(chars2)
```

### Way 11: List comprehension
### Way 12: Explicit counts
### Way 13: Boolean array
```python
def minRemoveToMakeValid(s):
    n = len(s)
    keep = [True] * n
    stack = []

    for i, c in enumerate(s):
        if c == '(':
            stack.append(i)
        elif c == ')':
            if stack:
                stack.pop()
            else:
                keep[i] = False

    for i in stack:
        keep[i] = False

    return "".join(c for i, c in enumerate(s) if keep[i])
```

### Way 14: Try-except
### Way 15: Functional reduce
### Way 16: String builder
### Way 17: Generator-based
### Way 18: Compact one-liner style
### Way 19: Dict tracking
### Way 20: Most elegant (cleanest variant of Way 1)

---

## Decision Tree

```
+------------------+-------------+--------------+
| Scenario         | Best        | Why          |
+------------------+-------------+--------------+
| Cleanest         | Stack idx   | Standard sol |
| No index track   | Two pass    | Counter-only |
| Most efficient   | Stack idx   | O(n) single  |
+------------------+-------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Stack of indices | O(n) | O(n) |
| Two-pass counter | O(n) | O(n) |
| Recursive | O(n²) | O(n²) |

---

## Walkthrough Example

```
s = "lee(t(c)o)de)"

Process with Way 1 (stack of indices):
  i=0  l: letter        stack=[]    remove={}
  i=1  e: letter        stack=[]    remove={}
  i=2  e: letter        stack=[]    remove={}
  i=3  (: open          stack=[3]   remove={}
  i=4  t: letter        stack=[3]   remove={}
  i=5  (: open          stack=[3,5] remove={}
  i=6  c: letter        stack=[3,5] remove={}
  i=7  ): close         stack=[3]   remove={}     (matched)
  i=8  o: letter        stack=[3]   remove={}
  i=9  ): close         stack=[]    remove={}     (matched)
  i=10 d: letter        stack=[]    remove={}
  i=11 e: letter        stack=[]    remove={}
  i=12 ): close         stack=[]    remove={12}   (UNMATCHED!)

After loop:
  stack is empty, so no '(' to remove
  remove = {12}

Final result:
  "lee(t(c)o)de" (skipping index 12) ✓
```

```
s = "a)b(c)d"

Process:
  i=0  a: letter        stack=[]    remove={}
  i=1  ): close         stack=[]    remove={1}   (UNMATCHED)
  i=2  b: letter        stack=[]    remove={1}
  i=3  (: open          stack=[3]   remove={1}
  i=4  c: letter        stack=[3]   remove={1}
  i=5  ): close         stack=[]    remove={1}   (matched)
  i=6  d: letter        stack=[]    remove={1}

After loop:
  remove = {1}

Final result:
  "ab(c)d" ✓
```

## Best Answer to Memorize

```python
def minRemoveToMakeValid(s):
    stack = []
    to_remove = set()

    for i, char in enumerate(s):
        if char == '(':
            stack.append(i)
        elif char == ')':
            if stack:
                stack.pop()
            else:
                to_remove.add(i)

    to_remove.update(stack)
    return "".join(c for i, c in enumerate(s) if i not in to_remove)
```

**14 lines. O(n) time. O(n) space. Single pass + cleanup. Interview-ready!**

## Alternative: Two-Pass Counter (no explicit stack)

```python
def minRemoveToMakeValid(s):
    # First pass: remove invalid ')'
    sb = []
    balance = 0
    for c in s:
        if c == ')':
            if balance == 0:
                continue  # skip unmatched ')'
            balance -= 1
        elif c == '(':
            balance += 1
        sb.append(c)

    # Second pass: remove extra '(' from right
    result = []
    to_remove = balance
    for c in reversed(sb):
        if c == '(' and to_remove > 0:
            to_remove -= 1
            continue
        result.append(c)
    return "".join(reversed(result))
```

## Test Cases

| Input | Expected | Why |
|-------|----------|-----|
| lee(t(c)o)de) | lee(t(c)o)de | One trailing ')' removed |
| a)b(c)d | ab(c)d | Unmatched ')' removed |
| ))(( | '' | All unmatched, drop all |
| (a(b(c)d) | a(b(c)d) or (a(bc)d) | One '(' unmatched |
| abc | abc | No parens |
| ( | '' | Single unmatched '(' |
| ) | '' | Single unmatched ')' |
| (() | () | One ')' for matching? Actually one extra '(' |

## Key Insight

> "Stack's LIFO behavior matches the matching requirement: the most recent '(' must be closed first. By tracking indices, we know exactly which characters to drop while keeping everything else in original order."

The two-pass counter version achieves the same result without an explicit stack - just count '(' and ')'. Brilliant trick!
