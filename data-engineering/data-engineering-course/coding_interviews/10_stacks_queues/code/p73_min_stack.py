"""Min Stack — push/pop/getMin all O(1).

Time:  O(1) amortized per op
Space: O(n)
"""


class MinStack:
    """A stack that supports push, pop, top, and getMin in O(1)."""

    def __init__(self):
        self.stack = []      # (val, current_min) tuples

    def push(self, val):
        cur_min = val if not self.stack else min(val, self.stack[-1][1])
        self.stack.append((val, cur_min))

    def pop(self):
        self.stack.pop()

    def top(self):
        return self.stack[-1][0]

    def get_min(self):
        return self.stack[-1][1]


def solve_min_stack(operations):
    """Run a list of ops; return outputs of "top" / "getMin" in order.

    Operations: ("MinStack",), ("push", v), ("pop",), ("top",), ("getMin",)
    """
    out = []
    stack = None
    for op in operations:
        if op[0] == "MinStack":
            stack = MinStack()
        elif op[0] == "push":
            stack.push(op[1])
        elif op[0] == "pop":
            stack.pop()
        elif op[0] == "top":
            out.append(stack.top())
        elif op[0] == "getMin":
            out.append(stack.get_min())
    return out


if __name__ == "__main__":
    ops = [
        ("MinStack",),
        ("push", -2),
        ("push", 0),
        ("push", -3),
        ("getMin",),
        ("pop",),
        ("top",),
        ("getMin",),
    ]
    print(solve_min_stack(ops))  # [-3, 0, -2]
