"""Implement Queue using Stacks — amortized O(1) per op.

Time:  O(1) amortized per operation
Space: O(n)
"""


class QueueFromStacks:
    """Two-stack queue: ``in_stack`` accepts pushes; ``out_stack`` serves pops."""

    def __init__(self):
        self.in_stack = []
        self.out_stack = []

    def push(self, val):
        self.in_stack.append(val)

    def pop(self):
        self._shift()
        return self.out_stack.pop()

    def peek(self):
        self._shift()
        return self.out_stack[-1]

    def empty(self):
        return not self.in_stack and not self.out_stack

    def _shift(self):
        # Move everything from in_stack to out_stack only when out_stack is empty;
        # this keeps each element moved at most once amortized.
        if not self.out_stack:
            while self.in_stack:
                self.out_stack.append(self.in_stack.pop())


def solve_queue_ops(operations):
    """Drive the queue with a list of ops; return outputs of pop/peek/empty in order."""
    out = []
    q = None
    for op in operations:
        if op[0] == "Queue":
            q = QueueFromStacks()
        elif op[0] == "push":
            q.push(op[1])
        elif op[0] == "pop":
            out.append(q.pop())
        elif op[0] == "peek":
            out.append(q.peek())
        elif op[0] == "empty":
            out.append(q.empty())
    return out


if __name__ == "__main__":
    ops = [
        ("Queue",),
        ("push", 1),
        ("push", 2),
        ("peek",),
        ("pop",),
        ("empty",),
    ]
    print(solve_queue_ops(ops))  # [1, 1, False]
