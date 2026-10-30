# Serialize and Deserialize Binary Tree (Hard)

**LeetCode:** https://leetcode.com/problems/serialize-and-deserialize-binary-tree/

## Problem
Design an algorithm to **serialize** a binary tree to a string and **deserialize** that string back to the original tree structure. You may choose any format.

## How to Think
1. **Serialize** with preorder DFS. Encode `None` as a sentinel (e.g., `'#'`). The root is always first.
2. **Deserialize** by parsing the preorder string with an iterator (consumed once left-to-right). First token becomes the root; then recurse left, then right.
3. Why preorder? Because the **first** element anchors the subtree's root, making reconstruction trivial.

## How to Remember
- **Pattern**: "Preorder string + iterator/pointer = rebuild tree."
- The iterator is consumed once; recursion walks the stream in lockstep.
- **Memory cue**: serialize = write a recipe (root, then left recipe, then right recipe); deserialize = follow the recipe top-down.

## Algorithm
```
serialize(node):
    if node is None: return "#"
    return str(node.val) + "," + serialize(node.left) + "," + serialize(node.right)

deserialize(data):
    tokens = iterator over data.split(",")
    function build():
        v = next(tokens)
        if v == "#": return None
        node = TreeNode(int(v))
        node.left  = build()
        node.right = build()
        return node
    return build()
```

## Complexity
- **Time:** O(n) for both serialize and deserialize.
- **Space:** O(n) for the serialized string + O(h) recursion.

## Code (Python)
```python
from typing import Optional

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Codec:
    SEP = ','
    NIL = '#'

    def serialize(self, root: Optional[TreeNode]) -> str:
        def dfs(node):
            if not node:
                return self.NIL
            return f"{node.val}{self.SEP}{dfs(node.left)}{self.SEP}{dfs(node.right)}"
        return dfs(root)

    def deserialize(self, data: str) -> Optional[TreeNode]:
        tokens = iter(data.split(self.SEP))
        def build():
            v = next(tokens)
            if v == self.NIL:
                return None
            node = TreeNode(int(v))
            node.left  = build()
            node.right = build()
            return node
        return build()
```

## AI Use Cases
- **Model serialization for tree-based ML** — XGBoost / LightGBM JSON formats use preorder-style dumps.
- **Saving / loading hierarchical configs** — YAML / JSON parse trees.
- **Distributed training** — shipping tree structure across nodes / parameter servers.
- **Token-tree persistence** in structured prediction (parsers, grammars).
- **Compilation pipelines** — round-tripping ASTs between IRs.
