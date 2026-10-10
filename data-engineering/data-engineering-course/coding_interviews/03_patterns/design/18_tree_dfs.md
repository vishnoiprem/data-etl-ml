# 18 — Tree DFS

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>

Depth-First Search visits a tree by going as deep as possible before backtracking. Three flavors: preorder, inorder, postorder.

## When to use

- Preorder (root → left → right): copy a tree, serialize
- Inorder (left → root → right): BST → sorted output
- Postorder (left → right → root): delete a tree, compute subtree metrics

## Examples in this course

- 64 Validate BST
- 69 Construct Tree from Preorder and Inorder
- 70 Serialize and Deserialize
- 71 Binary Tree Max Path Sum
