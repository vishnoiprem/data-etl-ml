# Build Binary Tree from Preorder and Inorder Traversal (Medium)

**LeetCode:** https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/

## Problem
Given two integer arrays `preorder` and `inorder` where they are traversals of the same binary tree, reconstruct and return the tree. Values are unique.

## How to Think
1. **Preorder's first element is the root.**
2. Locate the root in `inorder`. Everything **left** of it is the left subtree's inorder; everything **right** is the right subtree's inorder.
3. The **count** of nodes on each side tells you how to slice the preorder array too (sizes must match).
4. Recurse on each side. Use a hash map for O(1) inorder lookup → O(n) overall.

## How to Remember
- **Pattern**: "Root = `preorder[head]`; partition `inorder` via the root's index; sizes of `inorder` halves = sizes of `preorder` halves."
- **Memory cue**: inorder = "who's left of whom", preorder = "who's first".
- The preorder index advances globally; the inorder range shrinks left or right.

## Algorithm
```
idx = {value: i for i, value in enumerate(inorder)}
pre_i = 0

function build(in_left, in_right):
    if in_left > in_right:
        return None
    root_val = preorder[pre_i]
    pre_i += 1
    node = TreeNode(root_val)
    mid = idx[root_val]                # split point in inorder
    node.left  = build(in_left, mid - 1)
    node.right = build(mid + 1, in_right)
    return node

return build(0, len(inorder) - 1)
```

## Complexity
- **Time:** O(n) — thanks to the hashmap, each node is processed once.
- **Space:** O(n) for the hashmap + O(h) recursion.

## Code (Python)
```python
from typing import Optional, List

class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Solution:
    def buildTree(self, preorder: List[int], inorder: List[int]) -> Optional[TreeNode]:
        idx = {v: i for i, v in enumerate(inorder)}
        self.pre_i = 0

        def build(lo, hi):
            if lo > hi:
                return None
            root_val = preorder[self.pre_i]
            self.pre_i += 1
            node = TreeNode(root_val)
            mid = idx[root_val]
            node.left  = build(lo, mid - 1)
            node.right = build(mid + 1, hi)
            return node

        return build(0, len(inorder) - 1)
```

## AI Use Cases
- **Reconstructing ASTs** from linearized code (preorder + inorder line numbers).
- **Compiler / interpreter parse-tree recovery** from bytecode.
- **Reconstructing phylogenetic trees** from character matrices.
- **Document hierarchy reconstruction** in OCR / PDF extraction pipelines.
- **Inverse problem**: tree → features then back to tree for explainability.
