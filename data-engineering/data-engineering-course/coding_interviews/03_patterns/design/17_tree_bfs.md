# 17 — Tree BFS

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

Breadth-First Search visits a tree level by level using a queue.

## Template

```python
from collections import deque
queue = deque([root])
while queue:
    level = []
    for _ in range(len(queue)):
        node = queue.popleft()
        level.append(node.val)
        if node.left:  queue.append(node.left)
        if node.right: queue.append(node.right)
    result.append(level)
```

## Examples in this course

- 65 Level Order Traversal
- 67 Kth Smallest in BST
