# Parsing A Boolean Expression - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/parsing-a-boolean-expression

## The Problem
```
A boolean expression is one of:
- 't' (true)
- 'f' (false)
- '!(expr)'             (NOT, 1 operand)
- '&(expr1,expr2,...)'  (AND, 1+ operands)
- '|(expr1,expr2,...)'  (OR, 1+ operands)

Return the result of evaluating the expression.

Examples:
    "!(f)"           -> True
    "|(f,t)"         -> True
    "&(t,f)"         -> False
    "|(&(t,f,t),!(t))" -> False
    "!(&(t,t))"      -> False
    "&(|(t,!(t)),t)" -> True

Constraints:
- 1 <= expression.length <= 20000
- All inputs are valid expressions
"""

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
expression = "&(|(t,!(t)),t)"

Innermost first:  !(t) = False
Then:            |(t, False) = True
Then:            &(True, t) = True

expression = "!(&(t,t,f))"
Innermost first: &(t,t,f) = False
Then:            !(False) = True
```

### Step 2: The Trick
> "Use a STACK to keep track of operators and operands in order.
> When we see ')', the top of the stack has all the operands and
> the operator for the just-completed sub-expression.
> Evaluate it and push the result ('t' or 'f') back."

### Step 3: Why Stack?
> "Each ')' closes a complete subexpression. The operands and operator
> were all pushed sequentially. We pop them, evaluate, and push the result.
> This naturally handles nested expressions!"

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to parse and evaluate a boolean expression that uses '!', '&', '|'
> operators with potentially multiple operands in fully parenthesized form."

**Key Insight:**
> "This is a SHUNTING problem. Use a STACK:
> - Push each character except '(' and ','
> - When we see ')', the stack has operands and operator ready
> - Pop operands until '(', then pop the operator, evaluate, push result
> - Final stack top is the answer"

**Algorithm:**
> "1. Initialize empty stack
> 2. For each char in expression:
>    - If char == ')':
>      * Pop operands (truth values) until we hit '('
>      * Pop '('
>      * Pop the operator (!, &, |)
>      * Evaluate: ! = NOT single, & = AND of all, | = OR of all
>      * Push result as 't' or 'f'
>    - Else if char != ',': push to stack
> 3. Return top == 't'"

**Why this works:**
> "Each ')' marks the end of a complete subexpression. Everything from
> the operator down to '(' is the operand list and operator. We evaluate
> it and replace with the result. Stack handles arbitrary nesting."

**Edge cases:**
- Single value: 't' or 'f' returns it directly
- NOT: exactly 1 operand
- AND/OR: 1 or more operands (can be 1!)
- Deep nesting: stack grows then shrinks naturally

---

## The 20 Implementations (Simple to Complex)

### Way 1: Stack (BEST - Memorize!)
```python
def parseBoolExpr(expression):
    stack = []
    for char in expression:
        if char == ')':
            operands = []
            while stack and stack[-1] != '(':
                operands.append(stack.pop() == 't')
            stack.pop()  # '('
            op = stack.pop()
            if op == '!':
                result = not operands[0]
            elif op == '&':
                result = all(operands)
            else:  # '|'
                result = any(operands)
            stack.append('t' if result else 'f')
        elif char != ',':
            stack.append(char)
    return stack[-1] == 't'
```

### Way 2: With explicit operator functions
### Way 3: Push results immediately (no string roundtrip)
### Way 4: With deque
### Way 5: Recursive descent parser
### Way 6: Recursive with helper
### Way 7: Stack with operator lookup dictionary
### Way 8: String replacement (innermost first)
### Way 9: Regex-based replacement
### Way 10: Dictionary-based operators

### Way 11-15: Variations
- Way 11: Direct boolean stack (push Python bools)
- Way 12: Two-pass with index iteration
- Way 13: Most concise
- Way 14: Class-based parser
- Way 15: Explicit dispatch with short-circuit

### Way 16-20: Specialized
- Way 16: Compact stack
- Way 17: Recursive with operator functions
- Way 18: Short-circuit evaluation
- Way 19: With pop helper
- Way 20: Final cleanest (Way 1 minimal)

---

## Decision Tree

```
+------------------+-------------+--------------+
| Scenario         | Best        | Why          |
+------------------+-------------+--------------+
| Most efficient   | Stack       | O(n) single  |
| Most concise     | Way 13/20   | Fewest lines |
| Functional       | Recursive   | Math-style   |
| Easy to debug    | Recursive   | Clear logic  |
+------------------+-------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Stack | O(n) | O(n) |
| Recursive | O(n) | O(d) depth |
| Regex (replace) | O(n²) | O(n) |
| String replace (innermost) | O(n²) | O(n) |

Where `n` is length of expression and `d` is maximum nesting depth.

---

## Walkthrough Example

```
expression = "&(|(t,!(t)),t)"

i=0, '&': stack=[&]
i=1, '(': stack=[&,(]
i=2, '|': stack=[&,(,|]
i=3, '(': stack=[&,(,|,(]
i=4, 't': stack=[&,(,|,(,t]
i=5, ',': skip
i=6, '!': stack=[&,(,|,(,!,]
i=7, '(': stack=[&,(,|,(,!,(]
i=8, 't': stack=[&,(,|,(,!,(,t]
i=9, ')': 
  operands: pop 't' -> operands=[True]
  pop '('
  op = '!'
  not True = False
  push 'f'. stack=[&,(,|,(,f]
i=10, ',': skip
i=11, 't': stack=[&,(,|,(,f,t]
i=12, ')':
  operands: pop 't', 'f' -> operands=[True, False]
  pop '('
  op = '|'
  any([True, False]) = True
  push 't'. stack=[&,(,t]
i=13, ')':
  operands: pop 't' -> operands=[True]
  pop '('
  op = '&'
  all([True]) = True
  push 't'. stack=[&,t]
i=14, ')':
  operands: pop 't', 't' -> operands=[True, True]
  pop '('
  op = '&'
  all([True, True]) = True
  push 't'. stack=[t]

Result: True ✓
```

## Best Answer to Memorize

```python
def parseBoolExpr(expression):
    stack = []
    for char in expression:
        if char == ')':
            operands = []
            while stack and stack[-1] != '(':
                operands.append(stack.pop() == 't')
            stack.pop()  # '('
            op = stack.pop()
            if op == '!':
                result = not operands[0]
            elif op == '&':
                result = all(operands)
            else:
                result = any(operands)
            stack.append('t' if result else 'f')
        elif char != ',':
            stack.append(char)
    return stack[-1] == 't'
```

**13 lines. O(n) time. Clean. Interview-ready!**

## Key Insights

### Why "all(operands)" for AND?
> "When we AND multiple booleans, the result is True only if ALL are True.
> Python's `all()` gives us this for free."

### Why Convert to Bool?
> "We push 't'/'f' as characters, but `all()` and `any()` need actual booleans.
> So convert with `stack.pop() == 't'`."

### Why NOT Inside-Out Regex?
> "Regex/inner-replace is O(n²) - each replacement creates new strings.
> Stack approach is O(n) single pass."

### Why Push '(' to Stack?
> "'(' marks where operands start. When we see ')', we know to pop operands
> until we hit '('. Cleaner than other tracking mechanisms."

## Test Cases

| expression | Expected | Why |
|------------|----------|-----|
| "!(f)" | True | NOT false |
| "\|(f,t)" | True | OR has true |
| "&(t,f)" | False | AND has false |
| "\|(&(t,f,t),!(t))" | False | (F\|F)=F |
| "!(&(t,t))" | False | NOT true |
| "&(\|(t,!(t)),t)" | True | (T)&T=T |
| "t" | True | Just true |
| "f" | False | Just false |
| "!(t)" | False | NOT true |
| "&(t,t,t)" | True | AND all true |
| "\|(f,f,f)" | False | OR all false |
| "&(t,f,t)" | False | AND has false |
| "!(t,t,f)" | INVALID | ! takes 1 arg |
| "!(&(t,t,f))" | True | !(F)=T |

## Common Pitfalls

1. **Not converting 't'/'f' to bool**: `all(['f', 't'])` is True (all truthy strings!)
2. **Filtering `(` from stack**: Required for the algorithm to work
3. **Off-by-one in pop**: Pop `(` first then op, not op first
4. **Order of operands**: Doesn't matter for `&`/`|`, but matters for `!` position
5. **Empty expression**: Should return False (or handle explicitly)

## Why This Problem Matters

> "Tests:
> 1. Stack-based expression parsing (CRUCIAL skill)
> 2. Operator dispatch with multi-operand
> 3. Nested expression handling
> 4. String vs boolean conversion
> 5. Edge cases: NOT has 1 operand, AND/OR can have 1+
> 6. Pattern similar to: Decode String, Basic Calculator, Expression parsing"
