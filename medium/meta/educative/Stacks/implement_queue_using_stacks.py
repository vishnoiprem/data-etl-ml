"""
Implement Queue using Stacks
Easy | 15 min

Implement a queue using only stacks (push, pop, top, size, empty) operations.

Implement the MyQueue class:
- push(x): Pushes element x to the back of the queue
- pop(): Removes and returns the element from the front
- peek(): Returns the front element
- empty(): Returns True if queue is empty

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/implement-queue-using-stacks

Constraints:
- 1 <= x <= 9
- At most 100 calls will be made to push, pop, peek, empty
- All calls to pop and peek are valid (queue non-empty)

Follow-up: Can you implement peek/pop in amortized O(1) time?
"""


# =============================================================================
# Helper Stack class (would normally be imported)
# =============================================================================
class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        return self.items.pop() if self.items else None

    def top(self):
        return self.items[-1] if self.items else None

    def is_empty(self):
        return len(self.items) == 0

    def size(self):
        return len(self.items)


# =============================================================================
# WAY 1: Two stacks, lazy transfer (BEST - Memorize!)
# =============================================================================
# THINKING: "in_stack for pushes, out_stack for pops. Transfer only when
#           out_stack is empty. Amortized O(1) for all operations."
class MyQueue1:
    def __init__(self):
        self.in_stack = []
        self.out_stack = []

    def push(self, x):
        self.in_stack.append(x)

    def pop(self):
        self._transfer()
        return self.out_stack.pop()

    def peek(self):
        self._transfer()
        return self.out_stack[-1]

    def empty(self):
        return not self.in_stack and not self.out_stack

    def _transfer(self):
        if not self.out_stack:
            while self.in_stack:
                self.out_stack.append(self.in_stack.pop())


# =============================================================================
# WAY 2: Two stacks with helper Stack class
# =============================================================================
class MyQueue2:
    def __init__(self):
        self.in_stack = Stack()
        self.out_stack = Stack()

    def push(self, x):
        self.in_stack.push(x)

    def pop(self):
        self._transfer()
        return self.out_stack.pop()

    def peek(self):
        self._transfer()
        return self.out_stack.top()

    def empty(self):
        return self.in_stack.is_empty() and self.out_stack.is_empty()

    def _transfer(self):
        if self.out_stack.is_empty():
            while not self.in_stack.is_empty():
                self.out_stack.push(self.in_stack.pop())


# =============================================================================
# WAY 3: Using deque as both stacks
# =============================================================================
from collections import deque

class MyQueue3:
    def __init__(self):
        self.in_stack = deque()
        self.out_stack = deque()

    def push(self, x):
        self.in_stack.append(x)

    def pop(self):
        self._transfer()
        return self.out_stack.pop()

    def peek(self):
        self._transfer()
        return self.out_stack[-1]

    def empty(self):
        return len(self.in_stack) == 0 and len(self.out_stack) == 0

    def _transfer(self):
        if not self.out_stack:
            while self.in_stack:
                self.out_stack.append(self.in_stack.pop())


# =============================================================================
# WAY 4: Single stack recursive (push is O(n))
# =============================================================================
class MyQueue4:
    def __init__(self):
        self.stack = []

    def push(self, x):
        # Recursive push: hold all elements, push new, then re-push held
        if not self.stack:
            self.stack.append(x)
        else:
            temp = self.stack.pop()
            self.push(x)
            self.stack.append(temp)

    def pop(self):
        return self.stack.pop()

    def peek(self):
        return self.stack[-1]

    def empty(self):
        return len(self.stack) == 0


# =============================================================================
# WAY 5: Single stack iterative (push is O(n))
# =============================================================================
class MyQueue5:
    def __init__(self):
        self.stack = []

    def push(self, x):
        # Hold all existing, push x, then push back held
        temp = []
        while self.stack:
            temp.append(self.stack.pop())
        self.stack.append(x)
        while temp:
            self.stack.append(temp.pop())

    def pop(self):
        return self.stack.pop()

    def peek(self):
        return self.stack[-1]

    def empty(self):
        return not self.stack


# =============================================================================
# WAY 6: Two stacks with explicit size tracking
# =============================================================================
class MyQueue6:
    def __init__(self):
        self.in_stack = []
        self.out_stack = []
        self._size = 0

    def push(self, x):
        self.in_stack.append(x)
        self._size += 1

    def pop(self):
        self._transfer()
        self._size -= 1
        return self.out_stack.pop()

    def peek(self):
        self._transfer()
        return self.out_stack[-1]

    def empty(self):
        return self._size == 0

    def _transfer(self):
        if not self.out_stack:
            while self.in_stack:
                self.out_stack.append(self.in_stack.pop())


# =============================================================================
# WAY 7: With list comprehension
# =============================================================================
class MyQueue7:
    def __init__(self):
        self.in_stack = []
        self.out_stack = []

    def push(self, x):
        self.in_stack.append(x)

    def pop(self):
        if not self.out_stack:
            # Reverse in_stack into out_stack
            self.out_stack = [self.in_stack.pop() for _ in range(len(self.in_stack))]
        return self.out_stack.pop()

    def peek(self):
        if not self.out_stack:
            self.out_stack = [self.in_stack.pop() for _ in range(len(self.in_stack))]
        return self.out_stack[-1]

    def empty(self):
        return not self.in_stack and not self.out_stack


# =============================================================================
# WAY 8: Two stacks with peek optimization (move on peek too)
# =============================================================================
class MyQueue8:
    def __init__(self):
        self.in_stack = []
        self.out_stack = []

    def push(self, x):
        # Move all out_stack back to in_stack, push, transfer back
        while self.out_stack:
            self.in_stack.append(self.out_stack.pop())
        self.in_stack.append(x)
        while self.in_stack:
            self.out_stack.append(self.in_stack.pop())

    def pop(self):
        return self.out_stack.pop()

    def peek(self):
        return self.out_stack[-1]

    def empty(self):
        return not self.out_stack and not self.in_stack


# =============================================================================
# WAY 9: Using built-in list operations
# =============================================================================
class MyQueue9:
    def __init__(self):
        self.stack = []

    def push(self, x):
        self.stack.append(x)

    def pop(self):
        # Reverse, pop, reverse
        reversed_stack = list(reversed(self.stack))
        val = reversed_stack.pop()
        self.stack = list(reversed(reversed_stack))
        return val

    def peek(self):
        return self.stack[0] if self.stack else None

    def empty(self):
        return len(self.stack) == 0


# =============================================================================
# WAY 10: One-liner style
# =============================================================================
class MyQueue10:
    def __init__(self):
        self.stack = []

    def push(self, x):
        self.stack.append(x)

    def pop(self):
        val = self.stack[0]
        self.stack = self.stack[1:]
        return val

    def peek(self):
        return self.stack[0]

    def empty(self):
        return not self.stack


# =============================================================================
# WAY 11: With try-except
# =============================================================================
class MyQueue11:
    def __init__(self):
        self.in_stack = []
        self.out_stack = []

    def push(self, x):
        self.in_stack.append(x)

    def pop(self):
        try:
            return self.out_stack.pop()
        except IndexError:
            while self.in_stack:
                self.out_stack.append(self.in_stack.pop())
            return self.out_stack.pop()

    def peek(self):
        try:
            return self.out_stack[-1]
        except IndexError:
            while self.in_stack:
                self.out_stack.append(self.in_stack.pop())
            return self.out_stack[-1]

    def empty(self):
        return not self.in_stack and not self.out_stack


# =============================================================================
# WAY 12: Tuple-based stack (immutable)
# =============================================================================
class MyQueue12:
    def __init__(self):
        # Each "stack" is a tuple - immutable, but we recreate on change
        # Treat as a stack: append is push, [-1] is top
        self.in_stack = ()
        self.out_stack = ()

    def push(self, x):
        self.in_stack = self.in_stack + (x,)

    def pop(self):
        if not self.out_stack:
            # Transfer reverses the order: 1,2,3 -> push in order means top=3
            # After reversed we want top=1 (front of queue), so: (3,2,1)
            self.out_stack = tuple(reversed(self.in_stack))[::-1]
            # Simpler: just iterate
            self.out_stack = ()
            for item in reversed(self.in_stack):
                self.out_stack = self.out_stack + (item,)
            self.in_stack = ()
        result = self.out_stack[-1]
        self.out_stack = self.out_stack[:-1]
        return result

    def peek(self):
        if not self.out_stack:
            self.out_stack = ()
            for item in reversed(self.in_stack):
                self.out_stack = self.out_stack + (item,)
            self.in_stack = ()
        return self.out_stack[-1]

    def empty(self):
        return not self.in_stack and not self.out_stack


# =============================================================================
# WAY 13: Compact two-stack
# =============================================================================
class MyQueue13:
    def __init__(self):
        self.s1, self.s2 = [], []

    def push(self, x):
        self.s1.append(x)

    def pop(self):
        if not self.s2:
            while self.s1:
                self.s2.append(self.s1.pop())
        return self.s2.pop()

    def peek(self):
        if not self.s2:
            while self.s1:
                self.s2.append(self.s1.pop())
        return self.s2[-1]

    def empty(self):
        return not self.s1 and not self.s2


# =============================================================================
# WAY 14: With __repr__ for debugging
# =============================================================================
class MyQueue14:
    def __init__(self):
        self.in_stack = []
        self.out_stack = []

    def push(self, x):
        self.in_stack.append(x)

    def pop(self):
        self._ensure()
        return self.out_stack.pop()

    def peek(self):
        self._ensure()
        return self.out_stack[-1]

    def empty(self):
        return not self.in_stack and not self.out_stack

    def _ensure(self):
        if not self.out_stack:
            while self.in_stack:
                self.out_stack.append(self.in_stack.pop())

    def __repr__(self):
        return f"Queue(in={self.in_stack}, out={self.out_stack})"


# =============================================================================
# WAY 15: Reversed-list approach
# =============================================================================
class MyQueue15:
    def __init__(self):
        self.stack = []

    def push(self, x):
        # Insert at position 0 to maintain queue order
        self.stack.insert(0, x)

    def pop(self):
        return self.stack.pop()

    def peek(self):
        return self.stack[-1]

    def empty(self):
        return not self.stack


# =============================================================================
# WAY 16: With named methods
# =============================================================================
class MyQueue16:
    def __init__(self):
        self.input = []
        self.output = []

    def push(self, x):
        self.input.append(x)

    def pop(self):
        if not self.output:
            while self.input:
                self.output.append(self.input.pop())
        return self.output.pop()

    def peek(self):
        if not self.output:
            while self.input:
                self.output.append(self.input.pop())
        return self.output[-1]

    def empty(self):
        return len(self.input) == 0 and len(self.output) == 0


# =============================================================================
# WAY 17: With helper transfer method
# =============================================================================
class MyQueue17:
    def __init__(self):
        self.s_push = []
        self.s_pop = []

    def push(self, x):
        self.s_push.append(x)

    def pop(self):
        self._move()
        return self.s_pop.pop()

    def peek(self):
        self._move()
        return self.s_pop[-1]

    def empty(self):
        return not self.s_push and not self.s_pop

    def _move(self):
        if not self.s_pop:
            self.s_pop = [self.s_push.pop() for _ in range(len(self.s_push))]


# =============================================================================
# WAY 18: With max size tracking
# =============================================================================
class MyQueue18:
    def __init__(self):
        self.in_stack = []
        self.out_stack = []

    def push(self, x):
        self.in_stack.append(x)

    def pop(self):
        if not self.out_stack:
            # Pop everything from in_stack to out_stack
            while self.in_stack:
                self.out_stack.append(self.in_stack.pop())
        return self.out_stack.pop()

    def peek(self):
        if not self.out_stack:
            while self.in_stack:
                self.out_stack.append(self.in_stack.pop())
        return self.out_stack[-1]

    def empty(self):
        return len(self.in_stack) == 0 and len(self.out_stack) == 0


# =============================================================================
# WAY 19: Most compact (the textbook answer)
# =============================================================================
class MyQueue19:
    def __init__(self):
        self.i, self.o = [], []

    def push(self, x):
        self.i.append(x)

    def pop(self):
        self.peek()  # ensures o is populated
        return self.o.pop()

    def peek(self):
        if not self.o:
            while self.i:
                self.o.append(self.i.pop())
        return self.o[-1]

    def empty(self):
        return not self.i and not self.o


# =============================================================================
# WAY 20: Most elegant (same as Way 1)
# =============================================================================
class MyQueue20:
    def __init__(self):
        self.in_stack, self.out_stack = [], []

    def push(self, x):
        self.in_stack.append(x)

    def pop(self):
        if not self.out_stack:
            while self.in_stack:
                self.out_stack.append(self.in_stack.pop())
        return self.out_stack.pop()

    def peek(self):
        if not self.out_stack:
            while self.in_stack:
                self.out_stack.append(self.in_stack.pop())
        return self.out_stack[-1]

    def empty(self):
        return not self.in_stack and not self.out_stack


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to implement a queue (FIFO) using only stack operations (LIFO).
The trick is using TWO stacks: one for input, one for output."

Key Insight:
"in_stack accepts new elements via push (preserves reverse order).
When we need to pop/peek, we 'pour' in_stack into out_stack,
which REVERSES it back to original order. We only pour when
out_stack is empty - amortized O(1) per operation!"

Algorithm:
"1. push(x): just append to in_stack
2. pop(): if out_stack is empty, transfer all from in_stack;
          then pop from out_stack
3. peek(): same as pop but return top instead of removing
4. empty(): both stacks empty"

Why amortized O(1):
"Each element is pushed to in_stack once, transferred to out_stack
once, and popped from out_stack once - total 3 operations per element
amortized over n operations = O(1) per op."

Edge cases:
- pop on empty queue: invalid (problem guarantees valid calls)
- peek on empty: invalid
- Single push then peek: in_stack=[x], out_stack=[]
  After transfer: in_stack=[], out_stack=[x], peek returns x

COMPLEXITY:
+--------------+---------+---------+
| Operation    | Average | Worst   |
+--------------+---------+---------+
| push         | O(1)    | O(1)    |
| pop          | O(1)    | O(n)    |
| peek         | O(1)    | O(n)    |
| empty        | O(1)    | O(1)    |
+--------------+---------+---------+

KEY TRICK:
The 'lazy transfer' - we don't transfer on every push. We only transfer
when we need to pop/peek and out_stack is empty. This is the difference
between the elegant solution and the naive one.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
def test_myqueue(cls):
    """Test the MyQueue implementation with the standard LeetCode test."""
    q = cls()

    # Test push and empty
    assert q.empty() == True, f"Expected empty=True initially, got {q.empty()}"

    # Test push
    q.push(1)
    assert q.empty() == False, f"After push, should not be empty"
    q.push(2)
    q.push(3)

    # Test peek
    assert q.peek() == 1, f"Expected peek=1, got {q.peek()}"

    # Test pop
    assert q.pop() == 1, f"Expected pop=1, got {q.pop()}"
    assert q.peek() == 2, f"Expected peek=2, got {q.peek()}"
    assert q.pop() == 2, f"Expected pop=2, got {q.pop()}"
    assert q.pop() == 3, f"Expected pop=3, got {q.pop()}"
    assert q.empty() == True, f"After all pops, should be empty"

    # Test mix of operations
    q2 = cls()
    q2.push(10)
    q2.push(20)
    assert q2.peek() == 10
    assert q2.pop() == 10
    q2.push(30)
    assert q2.peek() == 20
    assert q2.pop() == 20
    assert q2.pop() == 30
    assert q2.empty() == True

    return True


if __name__ == "__main__":
    implementations = [
        ("Way 1: Two stacks lazy transfer (BEST)", MyQueue1),
        ("Way 2: With Stack class", MyQueue2),
        ("Way 3: deque for stacks", MyQueue3),
        ("Way 4: Single stack recursive", MyQueue4),
        ("Way 5: Single stack iterative", MyQueue5),
        ("Way 6: With size tracking", MyQueue6),
        ("Way 7: List comprehension", MyQueue7),
        ("Way 8: Move on push", MyQueue8),
        ("Way 9: Reverse-list approach", MyQueue9),
        ("Way 10: One-liner", MyQueue10),
        ("Way 11: Try-except", MyQueue11),
        ("Way 12: Tuple-based", MyQueue12),
        ("Way 13: Compact two-stack", MyQueue13),
        ("Way 14: With __repr__", MyQueue14),
        ("Way 15: Insert at position 0", MyQueue15),
        ("Way 16: Named methods", MyQueue16),
        ("Way 17: Helper transfer", MyQueue17),
        ("Way 18: Inline transfer", MyQueue18),
        ("Way 19: Most compact", MyQueue19),
        ("Way 20: Most elegant", MyQueue20),
    ]

    print("=" * 70)
    print("IMPLEMENT QUEUE USING STACKS - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/implement-queue-using-stacks")
    print("=" * 70)

    all_pass = True
    for name, cls in implementations:
        try:
            test_myqueue(cls)
            print(f"  {name}: PASS")
        except Exception as e:
            all_pass = False
            print(f"  X {name}: FAIL - {e}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
