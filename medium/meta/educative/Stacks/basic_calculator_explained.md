# Basic Calculator - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/basic-calculator

## The Problem
```
Evaluate an arithmetic expression containing +, -, (, ), and integers.

Constraints:
- '+' is always binary (between two numbers)
- '-' can be unary (e.g., "-2+1" -> -1)
- All expressions are valid
- Result fits in 32-bit integer

Examples:
    "1+1"               -> 2
    " 2-1 + 2 "         -> 3
    "(1+(4+5+2)-3)+(6+8)" -> 23
    "-2+1"              -> -1
    "-(1+2)"            -> -3
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
s = "1+1"
  Just add: 1 + 1 = 2

s = "(1+(4+5+2)-3)+(6+8)"
  Inner: (1+(4+5+2)-3) = 1 + 11 - 3 = 9
  Then: 9 + 14 = 23

s = "-2+1"
  Unary minus! Start at -2, add 1 = -1

s = "-(1+2)"
  -(3) = -3
```

### Step 2: The Trick
> "Use a STACK of SIGNS:
> - Each '(' pushes a sign onto stack
> - When we see '-' AFTER a '(', the sign within is NEGATIVE
> - Actually we push the EFFECTIVE sign multiplier:
>   - '(' after '+' or start: push +1
>   - '(' after '-': push -1 * current_sign
> - Then '+'/'-' picks the effective sign from top of stack"

### Step 3: Why Stack?
> "Each '(' opens a context where the parent '-' sign flips the inside.
> We track running 'sign multiplier' on a stack. Nested '(' = nested flipping."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to evaluate an arithmetic expression with +, -, parentheses, and possibly unary minus."

**Key Insight:**
> "The crucial insight: when we see '(', the parent's sign context applies to everything inside. If parent is '-', the inside is flipped. I track this with a stack of sign multipliers."

**Algorithm:**
> "1. Initialize result=0, sign=+1, num=0, stack=[+1]
> 2. For each character:
>    - Digit: build num (multi-digit numbers)
>    - '+': result += sign * num; num=0; sign = stack[-1]
>    - '-': result += sign * num; num=0; sign = -stack[-1]
>    - '(': push current sign onto stack
>    - ')': pop the stack
> 3. At end, add remaining: result += sign * num"

**Why this works:**
> "The sign stack encodes the sign multiplier at each paren depth.
> '-' inherits the parent's sign BUT flips it: sign = -parent_sign.
> '+' just inherits: sign = parent_sign."

**Edge cases:**
- Single number: "42" -> 42
- Unary minus: "-5+3" -> -2
- Nested parentheses: "(1+(2+3))" -> 6
- Spaces: ignore them
- Multi-digit: "12+34" -> 46

---

## The 20 Implementations (Simple to Complex)

### Way 1: Sign Stack (BEST - Memorize!)
```python
def calculate(s):
    stack = [1]
    sign = 1
    result = 0
    num = 0

    for char in s:
        if char.isdigit():
            num = num * 10 + int(char)
        elif char == '+':
            result += sign * num
            num = 0
            sign = stack[-1]
        elif char == '-':
            result += sign * num
            num = 0
            sign = -stack[-1]
        elif char == '(':
            stack.append(sign)
        elif char == ')':
            stack.pop()

    return result + sign * num
```

### Way 2: With explicit reset
```python
def calculate(s):
    stack = [1]
    sign = 1
    result = 0
    num = 0

    for char in s:
        if char.isdigit():
            num = num * 10 + int(char)
        elif char in '+-':
            result += sign * num
            num = 0
            sign = stack[-1] * (1 if char == '+' else -1)
        elif char == '(':
            stack.append(sign)
        elif char == ')':
            stack.pop()

    return result + sign * num
```

### Way 3: Push expected result approach
```python
def calculate(s):
    stack = []
    num = 0
    sign = 1
    result = 0

    for char in s:
        if char.isdigit():
            num = num * 10 + int(char)
        elif char == '+':
            result += sign * num
            num = 0
            sign = 1
        elif char == '-':
            result += sign * num
            num = 0
            sign = -1
        elif char == '(':
            stack.append(result)
            stack.append(sign)
            result = 0
            sign = 1
        elif char == ')':
            result += sign * num
            num = 0
            prev_sign = stack.pop()
            prev_result = stack.pop()
            result = prev_result + prev_sign * result
        elif char == ' ':
            continue

    return result + sign * num
```

### Way 4: Two-stack (numbers and ops)
### Way 5: Recursive descent parser
### Way 6: Recursive with index
### Way 7: Using op module
### Way 8: Using deque
### Way 9: Functional with reduce
### Way 10: Using tokenizer

### Way 11: Iterative with lookback
### Way 12: Stack of contexts
### Way 13: Using AST construction
### Way 14: Polish notation
### Way 15: Shunting-yard algorithm

### Way 16: Direct interpretation
### Way 17: Most compact
### Way 18: With operator module
### Way 19: Most elegant sign-stack
### Way 20: Cleanest

---

## Decision Tree

```
+------------------+-------------+--------------+
| Scenario         | Best        | Why          |
+------------------+-------------+--------------+
| Cleanest         | Sign stack  | Readable     |
| No unary         | Eval inside | Standard     |
| Compact          | Push result | Minimal code |
+------------------+-------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Sign stack | O(n) | O(n) |
| Push result | O(n) | O(n) |
| Recursive | O(n) | O(n) |

---

## Walkthrough Example

```
s = "(1+(4+5+2)-3)+(6+8)"

Process:
  '(':  stack=[1,1]
  '1':  num=1
  '+':  result+=1*1=1, sign=stack[-1]=1, num=0
  '(':  stack=[1,1,1]
  '4':  num=4
  '+':  result+=1*4=5, sign=1, num=0
  '5':  num=5
  '+':  result+=1*5=10, sign=1, num=0
  '2':  num=2
  ')':  stack=[1,1]
  '-':  result+=1*2=12, sign=-stack[-1]=-1, num=0
  '3':  num=3
  ')':  stack=[1]
  '+':  result+=-1*3=9, sign=stack[-1]=1, num=0
  '(':  stack=[1,1]
  '6':  num=6
  '+':  result+=1*6=9+6=15, sign=1, num=0
  '8':  num=8
  ')':  stack=[1]
  end:  result=15, sign=1, num=8

Final: 15 + 1*8 = 23 ✓
```

```
s = "-2+1"

Process:
  '-':  sign = -stack[-1] = -1, num=0
  '2':  num=2
  '+':  result += -1*2 = -2, sign = stack[-1] = 1, num=0
  '1':  num=1
  end:  result = -2, sign = 1, num = 1

Final: -2 + 1*1 = -1 ✓
```

## Best Answer to Memorize

```python
def calculate(s):
    stack = [1]
    sign = 1
    result = 0
    num = 0

    for char in s:
        if char.isdigit():
            num = num * 10 + int(char)
        elif char == '+':
            result += sign * num
            num = 0
            sign = stack[-1]
        elif char == '-':
            result += sign * num
            num = 0
            sign = -stack[-1]
        elif char == '(':
            stack.append(sign)
        elif char == ')':
            stack.pop()

    return result + sign * num
```

**17 lines. O(n) time. Handles unary minus. Interview-ready!**

## Key Insight

> "The sign stack tracks the sign multiplier at each paren depth.
> '-' inverts the parent's sign: sign = -parent_sign.
> '+' inherits parent's sign: sign = parent_sign.
> When we encounter a number, we add sign * num to result immediately... wait, we accumulate num first and add on the next operator (or at end)."

The trick is:
- Each '(' pushes CURRENT sign onto stack
- After '(', the inside flips if preceded by '-'

## Test Cases

| Input | Expected | Why |
|-------|----------|-----|
| "1+1" | 2 | Simple add |
| "2-1+2" | 3 | Subtract then add |
| "(1+(4+5+2)-3)+(6+8)" | 23 | Nested |
| "-2+1" | -1 | Unary minus |
| "-(1+2)" | -3 | Unary on parens |
| "0" | 0 | Single zero |
| "1" | 1 | Single digit |

## Why "Sign Stack" is the Best

> "It handles unary minus naturally because '-' inside a paren group flips the parent's sign. Each new context just multiplies. The stack tracks context multipliers efficiently."

The cleanest alternative: push (result_so_far, current_sign) at each '(' so closing a paren can compute the inner result and combine with outer. This requires two values per stack entry vs one, but the logic is sometimes clearer.

Both are valid - the sign stack approach uses less memory (one value per paren level vs two).
