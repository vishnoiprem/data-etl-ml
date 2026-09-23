# Path Sum III (Medium)

**LeetCode:** https://leetcode.com/problems/path-sum-iii/

## Problem
Given the `root` of a binary tree and an integer `targetSum`, return the number of **paths** that sum to `targetSum`. Paths can start and end at any nodes, must go **downward** (parent to child), and don't need to pass through the root.

## How to Think
1. Brute force is O(n²): for each node, DFS downward looking for `targetSum`.
2. **Optimization**: prefix-sum trick from "subarray sum equals k", extended to trees.
   - Keep a hash map from cumulative sum along the current root-to-node path → count.
   - At each node, the number of valid subpaths ending here is `map[currSum - targetSum]`.
3. **Backtracking is essential** — when leaving a subtree, decrement the count so siblings aren't polluted.

## How to Remember
- **Pattern**: "Prefix-sum on the DFS path + backtracking undo."
- `prefix[0] = 1` initializes the empty-path count.
- **Memory cue**: same idea as "subarray sum equals k", but the array is replaced by a rooted path through a tree, and we backtrack.

## Algorithm
```
count = 0
prefix = {0: 1}   # empty path

function dfs(node, currSum):
    if node is None:
        return
    currSum += node.val
    count += prefix.get(currSum - target, 0)
    prefix[currSum] += 1
    dfs(node.left,  currSum)
    dfs(node.right, currSum)
    prefix[currSum] -= 1    # backtrack on the way up
```

## Complexity
- **Time:** O(n) — each node visited once; hashmap ops are O(1) average.
- **Space:** O(h) for recursion + O(h) for the hashmap.

## Code (Python)
```python
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
        prefix[0] = 1

        def dfs(node, curr):
            if not node:
                return
            curr += node.val
            self.count += prefix[curr - targetSum]
            prefix[curr] += 1
            dfs(node.left,  curr)
            dfs(node.right, curr)
            prefix[curr] -= 1
        dfs(root, 0)
        return self.count
```

## AI Use Cases
- **Feature attribution along tree-structured models** — path integrals.
- **Credit assignment in hierarchical RL** — cumulative rewards along action paths.
- **Genomic / phylogenetic cumulative mutation scoring**.
- **Token path scoring in structured language models** (e.g., constrained decoding trees).
- **Graph neural networks on trees** — counting motifs satisfying a sum constraint.
