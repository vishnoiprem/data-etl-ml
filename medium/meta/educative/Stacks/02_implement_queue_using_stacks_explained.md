# Implement Queue Using Stacks - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/implement-queue-using-stacks

## The Problem
```
Implement a queue using ONLY stack operations (push to top, pop from top, peek, empty).

Implement MyQueue class:
- push(x): Add to back
- pop(): Remove from front, return value
- peek(): Return front value
- empty(): True if queue is empty

Follow-up: Can you do push/pop/peek in amortized O(1)?
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
Queue: 1 -> 2 -> 3 (1 enters first, leaves first)
Stack: 3, 2, 1 (1 enters last, leaves first)

The PROBLEM: Stack reverses order! When we push 1, 2, 3 onto a stack
and pop, we get 3, 2, 1 - opposite of queue behavior.
```

### Step 2: The Trick
> "Use TWO stacks!
> - in_stack: takes all pushes (reverses order naturally)
> - out_stack: when popped, transfer from in_stack (reverses AGAIN, restoring original order)
> - Only transfer when out_stack is EMPTY (lazy transfer)"

### Step 3: Why Two Stacks?
> "Pushing onto in_stack reverses order. Transferring to out_stack reverses AGAIN.
> Two reversals = original order! Perfect for FIFO."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to implement a queue (FIFO) using only stack operations (LIFO). The key insight is to use two stacks."

**Key Insight:**
> "Push operations go to in_stack. When I need to pop/peek, I transfer from in_stack to out_stack - this REVERSES the order TWICE, restoring FIFO behavior. The crucial trick is to only transfer when out_stack is empty (lazy transfer) - this gives amortized O(1) for all operations."

**Algorithm:**
> "1. push(x): append x to in_stack
> 2. pop(): if out_stack is empty, transfer all from in_stack to out_stack; then pop from out_stack
> 3. peek(): same as pop but return top instead of removing
> 4. empty(): both stacks must be empty"

**Why amortized O(1):**
> "Each element is pushed to in_stack once, transferred to out_stack once, and popped from out_stack once. Total: 3 ops per element over n operations = O(1) amortized per op. The worst case for a single pop is O(n), but it's amortized."

**Edge cases:**
- Empty queue: empty() returns True
- Many pushes, no pops: in_stack grows, no transfer needed
- Many pops after pushes: out_stack empties, triggers transfer

---

## The 20 Implementations (Simple to Complex)

### Way 1: Two Stacks Lazy Transfer (BEST - Memorize!)
```python
class MyQueue:
    def __init__(self):
        self.in_stack = []
        self.out_stack = []

    def push(self, x):
        self.in_stack.append(x)

    def pop(self):
        if not self.out_stack:
            while self.in_stack:
                out_stack.append(self.in_stack.pop())
        return self.out_stack.pop()

    def peek(self):
        if not self.out_stack:
            while self.in_stack:
                self.out_stack.append(self.in_stack.pop())
        return self.out_stack[-1]

    def empty(self):
        return not self.in_stack and not self.out_stack
```

### Way 2: With helper Stack class
### Way 3: Using deque as both stacks
### Way 4: Single stack RECURSIVE push (O(n) per push)
### Way 5: Single stack ITERATIVE push (O(n) per push)

### Way 6-10: Variations
- Way 6: With size tracking
- Way 7: With list comprehension
- Way 8: Move on push (always transfers - simpler but less efficient)
- Way 9: Reverse-list approach (O(n) per op)
- Way 10: One-liner style

### Way 11-15: Specialized
- Way 11: Try-except
- Way 12: Tuple-based (immutable)
- Way 13: Compact two-stack
- Way 14: With __repr__ for debugging
- Way 15: Insert at position 0 (O(n) per push)

### Way 16-20: More variations
- Way 16: Named methods
- Way 17: Helper transfer method
- Way 18: Inline transfer
- Way 19: Most compact (textbook)
- Way 20: Most elegant

---

## Decision Tree

```
+------------------+-------------+--------------+
| Scenario         | Best        | Why          |
+------------------+-------------+--------------+
| Most efficient   | Two-stack   | Amortized    |
| Simple           | Two-stack   | Standard     |
| Recursive        | Single stk  | Elegant      |
| Pure functional  | Tuple       | Immutable    |
+------------------+-------------+--------------+
```

## Complexity

| Operation | Average | Worst |
|-----------|---------|-------|
| push | O(1) | O(1) |
| pop | O(1) | O(n) |
| peek | O(1) | O(n) |
| empty | O(1) | O(1) |

**Space:** O(n) where n is queue size.

---

## Walkthrough Example

```
Operations: push(1), push(2), push(3), pop(), peek(), pop(), push(4), pop()

push(1):  in_stack=[1],         out_stack=[]
push(2):  in_stack=[1, 2],      out_stack=[]
push(3):  in_stack=[1, 2, 3],   out_stack=[]
pop():    out_stack empty, transfer:
          in_stack=[] -> out_stack=[3, 2, 1]
          return out_stack.pop() = 1
          out_stack=[3, 2]
peek():   out_stack not empty
          return out_stack[-1] = 2
          out_stack=[3, 2]
pop():    return out_stack.pop() = 2
          out_stack=[3]
push(4):  in_stack=[4],         out_stack=[3]
pop():    out_stack not empty
          return out_stack.pop() = 3
          out_stack=[]
pop():    out_stack empty, transfer:
          in_stack=[] -> out_stack=[4]
          return out_stack.pop() = 4
          out_stack=[]

Order of returns: 1, 2, 2, 3, 4 (FIFO ✓)
```

## Best Answer to Memorize

```python
class MyQueue:
    def __init__(self):
        self.in_stack = []
        self.out_stack = []

    def push(self, x):
        self.in_stack.append(x)

    def pop(self):
        self.peek()  # ensures transfer
        return self.out_stack.pop()

    def peek(self):
        if not self.out_stack:
            while self.in_stack:
                self.out_stack.append(self.in_stack.pop())
        return self.out_stack[-1]

    def empty(self):
        return not self.in_stack and not self.out_stack
```

**20 lines. Amortized O(1) for all ops. Interview-ready!**

## Key Insights

### Why Lazy Transfer?
> "If we transferred on every push, we'd do O(n) work per push.
> Lazy transfer means: each element gets transferred EXACTLY ONCE over its lifetime.
> Total work for n operations = O(n), so amortized O(1) per op."

### Why Two Stacks vs One?
> "One stack (recursive or iterative) makes push O(n).
> Two stacks with lazy transfer makes ALL operations amortized O(1)."

### Why "Peek() in Pop()" Trick?
> "We can DRY up the code by calling peek() in pop().
> peek() handles the transfer logic, then pop() just removes."

## Test Cases

```python
q = MyQueue()
q.push(1); q.push(2); q.push(3)
assert q.peek() == 1
assert q.pop() == 1
assert q.peek() == 2
assert q.pop() == 2
assert q.pop() == 3
assert q.empty() == True

# Mixed operations
q2 = MyQueue()
q2.push(10); q2.push(20); q2.peek()  # 10
q2.pop()  # 10
q2.push(30); q2.peek()  # 20
q2.pop(); q2.pop()  # 20, 30
assert q2.empty() == True
```

## Common Pitfalls

1. **Transferring too often**: Waste O(n) on every push
2. **Forgetting lazy check**: Transfer every time, defeating purpose
3. **Wrong order after transfer**: Forgetting reverse reverses TWICE
4. **Not handling empty**: Crashes on empty pop

## Why This Problem Matters

> "Classic 'implement data structure X using only Y' problem.
> Tests:
> 1. Understanding of LIFO vs FIFO
> 2. Amortized analysis
> 3. Lazy vs eager evaluation
> 4. Code organization (helper methods)
> 5. The insight of REVERSING TWICE"
