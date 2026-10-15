# Day 29 — Algorithms: Trees, BFS, DFS
**Module 21** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

A **binary tree** is a node with at most two children (`left`, `right`). The two ways to walk it:

- **BFS (breadth-first):** level by level. Use a **queue**.
- **DFS (depth-first):** path by path. Use a **stack** or **recursion**.

Three DFS orders: **pre-order** (root, left, right), **in-order** (left, root, right), **post-order** (left, right, root). Each has a use.

---

## 2. Technical concepts (20 min)

### When to use BFS vs DFS

| Problem | Use |
|---|---|
| Level order traversal | BFS |
| Shortest path in unweighted graph | BFS |
| Tree depth | DFS |
| Validate BST | DFS |
| Topological sort | DFS (or Kahn's BFS) |
| Cycle detection | DFS with 3-color |

### Recursion vs iterative
- **Recursion:** cleaner, but stack overflow on deep trees (>10k nodes).
- **Iterative with stack:** more code, but no stack overflow.
- **Iterative BFS with queue:** level order is naturally iterative.

### Three DFS orders

```python
def preorder(node):
    if not node: return
    visit(node); preorder(node.left); preorder(node.right)

def inorder(node):
    if not node: return
    inorder(node.left); visit(node); inorder(node.right)

def postorder(node):
    if not node: return
    postorder(node.left); postorder(node.right); visit(node)
```

- **In-order on BST** = sorted output.
- **Pre-order** = copy a tree, prefix serialization.
- **Post-order** = delete a tree, compute subtree size.

### Complexity
- All tree traversals: O(n) time, O(h) space (h = height).
- Balanced: h = log n. Skewed: h = n. Always think: "could the tree be a linked list?"

### Common pitfall
- Forgetting the **null check** at the start of recursion. Always `if not node: return`.

---

## 3. Coding (30 min)

Solve **3 problems**, ~10 min each.

### Problem 1: Binary Tree Level Order Traversal

```python
from collections import deque
from typing import Optional

class Node:
    def __init__(self, v: int, left=None, right=None):
        self.v = v; self.left = left; self.right = right

def level_order(root: Optional[Node]) -> list[list[int]]:
    if not root: return []
    out: list[list[int]] = []
    q = deque([root])
    while q:
        level = []
        for _ in range(len(q)):  # process one level at a time
            node = q.popleft()
            level.append(node.v)
            if node.left: q.append(node.left)
            if node.right: q.append(node.right)
        out.append(level)
    return out
```

- **Time:** O(n). **Space:** O(w) where w = max width.

### Problem 2: Validate BST

```python
def is_valid_bst(root: Optional[Node]) -> bool:
    def helper(node, lo, hi):
        if not node: return True
        if not (lo < node.v < hi): return False
        return helper(node.left, lo, node.v) and helper(node.right, node.v, hi)
    return helper(root, float("-inf"), float("inf"))
```

- **Time:** O(n). **Space:** O(h).
- **Key insight:** pass `lo, hi` as bounds; don't just compare to parent.

### Problem 3: Lowest Common Ancestor

Given the root of a BST and two target values `p` and `q`, find the value of the LCA (lowest common ancestor).

```python
def lca_bst(root: Optional[Node], p: int, q: int) -> Optional[int]:
    cur = root
    while cur:
        if p < cur.v and q < cur.v:
            cur = cur.left
        elif p > cur.v and q > cur.v:
            cur = cur.right
        else:
            return cur.v
    return None
```

- **Time:** O(h) iterative, O(h) recursive.
- **Note:** the LeetCode version takes `TreeNode` objects, not values. Same algorithm — compare by value via the nodes' `.val` field.
- **Variant (binary tree, not BST):** use parent pointers or store paths from root to each node, then compare.

---

## 4. Debugging & tests (20 min)

### Bug 1: validate_bst doesn't allow duplicates
**Fix:** be specific. `<` strict (no dupes) or `<=` (dupes on one side).

### Bug 2: level order skips null children
**Symptom:** missing leaves in the output.
**Fix:** `if node.left: q.append(node.left)` — only enqueue non-null. Don't add nulls.

### Bug 3: recursive depth blows stack
**Fix:** for skewed trees with depth > 10k, convert to iterative.

### Bug 4: LCA on non-BST returns wrong
**Fix:** use the **path comparison** approach. Walk root→p and root→q, then find last common.

### Tests
```python
def test_level_order():
    #        1
    #       / \
    #      2   3
    #     / \   \
    #    4   5   6
    root = Node(1, Node(2, Node(4), Node(5)), Node(3, None, Node(6)))
    assert level_order(root) == [[1], [2, 3], [4, 5, 6]]

def test_validate_bst():
    assert is_valid_bst(Node(2, Node(1), Node(3))) == True
    assert is_valid_bst(Node(5, Node(1), Node(4, Node(3), Node(6)))) == False
    assert is_valid_bst(None) == True

def test_lca_bst():
    #         6
    #        / \
    #       2   8
    #      / \ / \
    #     0  4 7  9
    #       / \
    #      3   5
    root = Node(6, Node(2, Node(0), Node(4, Node(3), Node(5))), Node(8, Node(7), Node(9)))
    assert lca_bst(root, 2, 8) == 6
    assert lca_bst(root, 0, 4) == 2
    assert lca_bst(root, 3, 5) == 4
```

---

## 5. Mock interview practice (20 min)

**Q1 — "Iterative BFS or recursive DFS — which is faster?"**
> BFS uses a heap-allocated `deque`; recursion uses the call stack. In practice, BFS is slightly faster per call (deque operations are O(1) amortized) but uses more memory (each queue entry is a heap object vs. a stack frame). For trees, iterative DFS with an explicit stack is often faster than recursive DFS.

**Q2 — "How do you handle a tree so deep it blows the stack?"**
> Convert to iterative with an explicit stack. Or use a chunked traversal (process 1000 nodes at a time).

**Q3 — "Serialize a binary tree. Then deserialize."**
> Pre-order traversal. Mark nulls explicitly. JSON array: `[1,2,null,null,3,4,null,null,5,null,null]`.

**Q4 — "Why is BST validation tricky?"**
> A common bug is checking only parent-child. The correct check is "all left subtree < node < all right subtree", which needs bound propagation.

**Q5 — "Find the kth smallest in a BST in O(h) time?"**
> Iterative in-order traversal, stop at k. O(h) because you stop early.

---

## 6. Success criteria check
- [ ] I can write BFS in 5 min.
- [ ] I can write recursive DFS in 3 min.
- [ ] I can name the 3 DFS orders.
- [ ] I can solve validate BST with bounds.

## 7. Grade yourself 0–10
| Area | Score |
|---|---|
| Correctness | /10 |
| Code quality | /10 |
| Debugging | /10 |
| Performance | /10 |
| Testing | /10 |
| Communication | /10 |
| **Total** | **/60** |

## 8. Coding assignment
**Maximum Depth of Binary Tree** — return the depth (max root-to-leaf path length). Empty tree = 0. Iterative BFS solution.

### Rubric (0–10)
- 0: doesn't compile
- 4: recursive O(n)
- 6: iterative BFS O(n)
- 8: O(n) without storing all levels
- 10: O(h) early-exit (if just need max, not the path)

### Solution
```python
def max_depth(root: Optional[Node]) -> int:
    if not root: return 0
    q = deque([(root, 1)])
    d = 0
    while q:
        node, depth = q.popleft()
        d = max(d, depth)
        if node.left: q.append((node.left, depth + 1))
        if node.right: q.append((node.right, depth + 1))
    return d
```

**Time: 90 min**
