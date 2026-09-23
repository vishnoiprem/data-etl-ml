"""
Problem: Serialize and Deserialize Binary Tree (Hard)
LeetCode: https://leetcode.com/problems/serialize-and-deserialize-binary-tree/

How to Think:
1. Serialize: preorder DFS, encode None as a marker (e.g., '#').
2. Deserialize: preorder parse using an iterator; reconstruct left then right.
3. Preorder is preferred because the FIRST element is always the root — easy to anchor.

How to Remember:
- Pattern: "preorder string + index/iterator = rebuild tree."
- The trick is treating the string as a stream the iterator consumes once.
- Memo clue: serialize = write a recipe (root, then left recipe, then right recipe).

AI Use Cases:
- Model serialization for tree-based ML (XGBoost, LightGBM JSON formats).
- Saving/loading hierarchical configs (YAML/JSON parse trees).
- Distributed training: ship tree structure across nodes.
- Token-tree persistence in structured prediction.
"""

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
            node.left = build()
            node.right = build()
            return node

        return build()


if __name__ == "__main__":
    codec = Codec()
    root = TreeNode(1)
    root.left = TreeNode(2)
    root.right = TreeNode(3, TreeNode(4), TreeNode(5))
    s = codec.serialize(root)
    print(s)  # "1,2,#,#,3,4,#,#,5,#,#"
    rebuilt = codec.deserialize(s)
    print(codec.serialize(rebuilt) == s)  # True
