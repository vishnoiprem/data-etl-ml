# Basic Calculator II - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/basic-calculator-ii

## The Problem
```
Evaluate a mathematical expression string s containing:
- Non-negative integers
- Operators: '+', '-', '*', '/'
- Spaces (ignored)

Operations follow standard precedence (* and / before + and -).
Integer division truncates TOWARD ZERO.

Return the result.

Examples:
    "3+2*2"        -> 7
    " 3/2 "        -> 1
    " 3+5 / 2 "    -> 5
    "0-2147483647" -> -2147483647
    "14/3*2"       -> 8        (left to right: 14/3=4, 4*2=8)
    "100/3/2"      -> 16       (100/3=33, 33/2=16)

Constraints:
- 1 <= s.length <= 3 * 10^5
- s has digits, operators, spaces
- Expression is always valid
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
We need to evaluate "3+2*2" correctly:
- Naive (left to right): (3+2)*2 = 10. WRONG.
- Correct (precedence):  3+(2*2) = 7. ✓

Key constraints:
1. Standard math precedence
2. Integer division TRUNCATES TOWARD ZERO
   (Python's // already does this for positives, but:
    -7 // 2 = -4 in Python (rounds down). Need to round TOWARD ZERO.
    -7 / 2 truncated toward zero = -3.)
```

### Step 2: The Trick
> "Use a STACK with DEFERRED addition!
>
> When we encounter each operator:
> - '+': push the current number (positive) onto stack
> - '-': push NEGATIVE of current number onto stack
> - '*': POP top, compute top * num, PUSH result
> - '/': POP top, compute top // num (with truncation), PUSH result
>
> At the end, SUM the stack."

### Step 3: Why This Works
> "Operators with HIGHER precedence (* and /) are resolved IMMEDIATELY.
> Operators with LOWER precedence (+ and -) are DEFERRED.
>
> After the entire expression:
> - Stack contains all '+' terms (positive)
> - Stack contains all '-' terms (negative)
> - Stack contains the result of * and / chains
> Sum = correct answer with precedence built in."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to evaluate a math expression with +, -, *, /. * and / have higher
> precedence than + and -. Integer division truncates toward zero."

**Key Insight:**
> "Use a STACK with DEFERRED addition!
> - '+': push current number
> - '-': push -current number
> - '*': pop and push (top * num)
> - '/': pop and push (top // num) with truncation
>
> Sum the stack at the end. * and / are resolved immediately because
> they have higher precedence - their left operand is always on top of
> the stack."

**Algorithm:**
> "1. Initialize empty stack, num = 0, sign = '+'
> 2. For each char in s:
>    - If digit: build num (num = num * 10 + int(c))
>    - If operator OR end of string:
>      * If sign == '+': push num to stack
>      * If sign == '-': push -num to stack
>      * If sign == '*': pop, push (top * num)
>      * If sign == '/': pop, push (top // num) (with truncation)
>      * sign = current char, num = 0
> 3. Don't forget to process the LAST number (no operator after it!)
> 4. Return sum(stack)"

**Why this works:**
> "* and / bind tighter than + and -, so we resolve them immediately.
> When we see * or /, the LEFT operand is whatever's on the stack.
> We pop, compute, push back.
> For + and -, we just push with sign - they have lower precedence,
> so other ops come first. Sum at end gives correct answer."

**Truncation toward zero:**
> "Python's // rounds DOWN for negatives: -7 // 2 = -4. But problem says
> truncate TOWARD ZERO, so -7/2 should be -3.
> Fix: if top < 0: -(abs(top) // num)"

**Edge cases:**
- Single number: just push and sum
- All multiplications: stack stays small (just intermediate results)
- Division by negative: careful with truncation
- Leading/trailing spaces: ignore
- Large numbers: stack values can be large, sum them carefully

---

## The 20 Implementations (Simple to Complex)

### Way 1: Stack with deferred addition (BEST - Memorize!)
```python
def calculate(s):
    stack = []
    num = 0
    sign = '+'

    for char in s:
        if char.isdigit():
            num = num * 10 + int(char)
        elif char in '+-*/':
            if sign == '+': stack.append(num)
            elif sign == '-': stack.append(-num)
            elif sign == '*': stack.append(stack.pop() * num)
            else:  # /
                top = stack.pop()
                stack.append(top // num if top >= 0 else -((-top) // num))
            sign = char
            num = 0

    # Process the last number (no operator triggers it)
    if sign == '+': stack.append(num)
    elif sign == '-': stack.append(-num)
    elif sign == '*': stack.append(stack.pop() * num)
    else:
        top = stack.pop()
        stack.append(top // num if top >= 0 else -((-top) // num))

    return sum(stack)
```

### Way 2: Same with explicit index tracking
- Skip leading spaces using index `i == len(s) - 1` for end.

### Way 3: Pre-replace spaces
- `s = s.replace(' ', '')` then process normally.

### Way 4: Two passes - tokenize first, then process * and / first
- First pass: extract numbers and operators.
- Second pass: resolve * and / into single values.
- Final pass: evaluate + and - left to right.

### Way 5: No stack - track 'last' and 'result'
- `result += last` then `last = num` (or -num) on + or -.
- `last = last * num` or `last = last / num` on * or /.
- Final: `return result + last`

### Way 6: Regex-based tokenization
- `tokens = re.findall(r'\d+|[+\-*/]', s)`
- Process tokens with stack.

### Way 7: Recursive descent parser
- `parse_number()` reads digits
- `parse_term()` handles * and / chain
- `parse_expr()` handles + and - chain

### Way 8: While loop with explicit index
- Same as Way 1 but with while loop and index variable.

### Way 9: Helper function for op application
```python
def apply_op(stack, op, num):
    if op == '+': stack.append(num)
    elif op == '-': stack.append(-num)
    elif op == '*': stack.append(stack.pop() * num)
    elif op == '/':
        top = stack.pop()
        stack.append(top // num if top >= 0 else -((-top) // num))
```

### Way 10: With deque
- Same as Way 1, using `collections.deque()` (no real benefit).

### Way 11: Most elegant no-stack
- Track `last` and `result` - no actual stack needed.

### Way 12: Class-based
- `Calculator` class with state and methods.

### Way 13: Using math.trunc
- `math.trunc(top / num)` handles truncation toward zero.

### Way 14: Compact one pass with `i == len(s) - 1` end check

### Way 15: Helper function for truncation
```python
def truncate_div(a, b):
    if a < 0: return -((-a) // b)
    return a // b
```

### Way 16: Conditional processing with explicit space handler
- `elif c == ' ': continue` to skip spaces.

### Way 17: Op function map
- Lambda functions for each operation.

### Way 18: Most compact (inline)
- Compressed one-liners for op processing.

### Way 19: Two-pass with explicit num tracking
- Read number, check for * or /, handle accordingly.

### Way 20: Final cleanest
- Same as Way 1, polished variable names.

---

## Decision Tree

```
+------------------+--------------+--------------+
| Scenario         | Best         | Why          |
+------------------+--------------+--------------+
| Standard         | Way 1        | Clean stack  |
| No stack         | Way 5 / 11   | Track last   |
| Educational      | Way 7        | Recursive    |
| Functional       | Way 7        | No mutation  |
+------------------+--------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Stack (Way 1) | O(n) | O(n) |
| No stack (Way 5, 11) | O(n) | O(1) |
| Recursive (Way 7) | O(n) | O(d) |

---

## Walkthrough Example

```
s = "3+2*2"

i=0, '3': digit. num=3. stack=[]
i=1, '+': operator.
  sign='+', push 3. stack=[3]
  sign='+', num=0
i=2, '2': digit. num=2.
i=3, '*': operator.
  sign='+', push 2. stack=[3, 2]
  sign='*', num=0
i=4, '2': digit. num=2.
End of string. Process last:
  sign='*', pop 2, push 2*2=4. stack=[3, 4]
Return sum(stack) = 7 ✓

s = "14/3*2"

i=0, '1': num=1
i=1, '4': num=14
i=2, '/': operator.
  sign='+', push 14. stack=[14]
  sign='/', num=0
i=3, '3': num=3
i=4, '*': operator.
  sign='/', pop 14, push 14//3=4. stack=[4]
  sign='*', num=0
i=5, '2': num=2
End. Process last:
  sign='*', pop 4, push 4*2=8. stack=[8]
Return 8 ✓

s = "0-2147483647"

i=0, '0': num=0
i=1, '-': operator.
  sign='+', push 0. stack=[0]
  sign='-', num=0
i=2..12, digits: num=2147483647
End. Process last:
  sign='-', push -2147483647. stack=[0, -2147483647]
Return 0 + (-2147483647) = -2147483647 ✓
```

## Best Answer to Memorize

```python
def calculate(s):
    stack = []
    num = 0
    sign = '+'

    for c in s:
        if c.isdigit():
            num = num * 10 + int(c)
        elif c in '+-*/':
            if sign == '+': stack.append(num)
            elif sign == '-': stack.append(-num)
            elif sign == '*': stack.append(stack.pop() * num)
            else:
                top = stack.pop()
                stack.append(top // num if top >= 0 else -((-top) // num))
            sign = c
            num = 0

    # Last number
    if sign == '+': stack.append(num)
    elif sign == '-': stack.append(-num)
    elif sign == '*': stack.append(stack.pop() * num)
    else:
        top = stack.pop()
        stack.append(top // num if top >= 0 else -((-top) // num))

    return sum(stack)
```

**Clean. Interview-ready!**

---

## Key Insights

### Why deferred addition?
> "* and / are resolved immediately because their left operand is on
> the stack. + and - push with sign because they have lower precedence -
> we don't know the full effect until everything's processed."

### Why "stack.pop() * num" for '*'?
> "When we see '*', the previous number (or result of * /) is on top
> of the stack. We pop it, multiply by current num, push back. This
> correctly handles '2*3*4' as we keep multiplying."

### Why truncate toward zero for division?
> "Python's // floors: -7 // 2 = -4. Problem wants -3.
> If top < 0: -(abs(top) // num) gives correct truncation."

### Why process last number outside loop?
> "The loop processes on each OPERATOR. The last number has no
> operator after it. We need explicit code to handle it."

### Why not eval()?
> "eval() is unsafe (security risk), banned in interviews."

---

## Test Cases

| s | Expected | Why |
|---|----------|-----|
| "3+2*2" | 7 | Standard |
| " 3/2 " | 1 | Space + truncation |
| " 3+5 / 2 " | 5 | Mixed |
| "0-2147483647" | -2147483647 | Min int |
| "1+1+1+1+1" | 5 | All + |
| "14/3*2" | 8 | Div then mul |
| "14-3/2" | 13 | Sub then div |
| "0+0" | 0 | Zeros |
| "1-1-1-1-1" | -3 | Multiple subs |
| "1*2*3*4*5" | 120 | All * |
| "100/3/2" | 16 | Chained div |
| "1+2*3-4" | 3 | Mixed precedence |
| "2*3+4/2" | 8 | Standard |

## Common Pitfalls

1. **Forgetting the last number**: Loop only processes on operator.
   Need explicit handling after loop.
2. **Wrong truncation for negatives**: `//` floors, not truncates toward zero.
3. **Spaces not handled**: Either skip them or strip them first.
4. **Multi-digit numbers**: Use `num = num * 10 + int(c)` to build.
5. **Sign of popped value**: When dividing negative by positive, careful!

## Why This Problem Matters

> "Tests:
> 1. Stack with deferred operations (CRITICAL pattern)
> 2. Operator precedence handling WITHOUT a parser
> 3. Multi-digit number parsing from string
> 4. Integer truncation toward zero (NOT floor division)
> 5. Edge cases: spaces, large numbers, last number
> 6. Pattern similar to: parser problems, expression evaluation"
