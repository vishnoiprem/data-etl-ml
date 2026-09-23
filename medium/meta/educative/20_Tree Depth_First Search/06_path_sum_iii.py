"""
Problem: Path Sum III (Medium)
LeetCode: https://leetcode.com/problems/path-sum-iii/

How to Think:
1. Paths can start and end at any nodes, going downward.
2. For each node as starting point, DFS downward counting paths that sum to target.
3. To avoid O(n^2), use prefix-sum + backtracking on cumulative sums.

How to Remember:
- Pattern: "Prefix-sum on DFS path + backtrack on undo."
- Keep a map from cumulative sum -> count. At each node, increment ans by map[curr_sum - target].
- Memo clue: it's the same trick as 'subarray sum equals k', but on a tree.

AI Use Cases:
- Feature attribution along tree-structured models (path integrals).
- Credit assignment in hierarchical RL.
- Genomic/phylogenetic cumulative mutation scoring.
- Token path scoring in structured language models.
"""

from typing import Optional
from collections import defaultdict


class TreeNode:
    def __init__(self, val: int = 0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def pathSum(self, root: Optional[TreeNode], targetSum: int) -> int:
        self.count = 0
        prefix = defaultdict(int)
        prefix[0] = 1  # empty path

        def dfs(node, curr):
            if not node:
                return
            curr += node.val
            self.count += prefix[curr - targetSum]
            prefix[curr] += 1
            dfs(node.left, curr)
            dfs(node.right, curr)
            prefix[curr] -= 1  # backtrack

        dfs(root, 0)
        return self.count


if __name__ == "__main__":
    #      10
    #     /  \
    #    5   -3
    #   / \    \
    #  3   2    11
    # / \   \
    #3  -2   1
    root = TreeNode(10)
    root.left = TreeNode(5, TreeNode(3, TreeNode(3), TreeNode(-2)),
                         TreeNode(2, None, TreeNode(1)))
    root.right = TreeNode(-3, None, TreeNode(11))
    print(Solution().pathSum(root, 8))  # 3
