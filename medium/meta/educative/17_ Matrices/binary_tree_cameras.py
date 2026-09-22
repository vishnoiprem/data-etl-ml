"""
Binary Tree Cameras
Hard | 40 min

Given root of binary tree, find minimum cameras to monitor every node.
Each camera monitors itself, parent, and immediate children.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/binary-tree-cameras

Examples:
    Tree: [0,0,null,0,0]
            0
           /
          0
         / \
        0   0
    -> 1  (camera at root's left child)

    Tree: [0,0,null,0,null,0]
            0
           /
          0
         /
        0
         \
          0
    -> 2

Constraints:
- 1 <= nodes <= 1000
- Node.val == 0

KEY INSIGHT:
Tree DP with 3 states per node:
- state_0: NOT_MONITORED (root NOT covered, no camera here)
- state_1: MONITORED (root covered by child, no camera here)
- state_2: HAS_CAMERA (camera on this node)

Recurrence:
- s0 = min(l1, l2) + min(r1, r2)  (children must be covered)
- s1 = min over child states where at least one child has camera
- s2 = 1 + min(l0,l1,l2) + min(r0,r1,r2)  (camera here, children any covered)

Base: None returns (0, 0, INF) — empty, 0 cameras, covered, but no camera needed.

Final answer: min(s1, s2) for root.
"""


# =============================================================================
# TreeNode definition
# =============================================================================
class TreeNode:
    def __init__(self, data=0, left=None, right=None):
        self.data = data
        self.left = left
        self.right = right

    def __repr__(self):
        return f"TreeNode({self.data})"


def build_tree(arr):
    """Build tree from level-order array (None for missing)."""
    if not arr:
        return None
    nodes = [None if v is None else TreeNode(v) for v in arr]
    kids = nodes[1:]
    i = 0
    for parent in nodes:
        if parent is not None:
            if i < len(kids):
                parent.left = kids[i]
                i += 1
            if i < len(kids):
                parent.right = kids[i]
                i += 1
    return nodes[0]


# =============================================================================
# WAY 1: Tree DP with 3 states (BEST - Memorize!)
# =============================================================================
def min_camera_1(root):
    """State DP. Returns min cameras covering entire tree."""
    INF = float("inf")

    def dfs(node):
        if node is None:
            return (0, 0, INF)  # 0 cams, covered, no need camera
        l0, l1, l2 = dfs(node.left)
        r0, r1, r2 = dfs(node.right)
        # s0: not covered. Children must be covered.
        s0 = min(l1, l2) + min(r1, r2)
        # s1: covered (by child). At least one child has camera.
        s1 = INF
        for ls in [l0, l1, l2]:
            for rs in [r0, r1, r2]:
                if ls == l2 or rs == r2:
                    s1 = min(s1, ls + rs)
        # s2: has camera. Children in any covered state.
        s2 = 1 + min(l0, l1, l2) + min(r0, r1, r2)
        return (s0, s1, s2)

    s0, s1, s2 = dfs(root)
    return min(s1, s2)


# =============================================================================
# WAY 2: Greedy with state flags
# =============================================================================
def min_camera_2(root):
    """
    Greedy DFS. 3 states:
    - 0: not covered
    - 1: has camera
    - 2: covered (no camera)
    Cameras installed only when needed.
    """
    self_cameras = [0]

    def dfs(node):
        if node is None:
            return 2  # covered
        left = dfs(node.left)
        right = dfs(node.right)
        if left == 0 or right == 0:
            # At least one child not covered -> install camera here.
            self_cameras[0] += 1
            return 1
        if left == 1 or right == 1:
            # At least one child has camera -> this is covered.
            return 2
        # Both children are covered (state 2) but no camera.
        return 0

    if dfs(root) == 0:
        self_cameras[0] += 1  # root needs camera
    return self_cameras[0]


# =============================================================================
# WAY 3: DFS returning int (greedy + count)
# =============================================================================
def min_camera_3(root):
    """Same as Way 2 but inline count."""
    count = 0

    def dfs(node):
        nonlocal count
        if node is None:
            return 2
        left = dfs(node.left)
        right = dfs(node.right)
        if left == 0 or right == 0:
            count += 1
            return 1
        if left == 1 or right == 1:
            return 2
        return 0

    if dfs(root) == 0:
        count += 1
    return count


# =============================================================================
# WAY 4: Iterative postorder with explicit stack
# =============================================================================
def min_camera_4(root):
    """Iterative postorder using stack."""
    if root is None:
        return 0
    # State per node: 0=unknown, 1=camera, 2=covered, 3=not_covered
    stack = [(root, False)]
    state = {}
    count = 0
    while stack:
        node, visited = stack.pop()
        if visited:
            left = state.get(node.left, 2)  # default covered for None
            right = state.get(node.right, 2)
            if left == 0 or right == 0:
                state[node] = 1
                count += 1
            elif left == 1 or right == 1:
                state[node] = 2
            else:
                state[node] = 0
        else:
            stack.append((node, True))
            if node.right:
                stack.append((node.right, False))
            if node.left:
                stack.append((node.left, False))
    # Check root
    if state[root] == 0:
        count += 1
    return count


# =============================================================================
# WAY 5: Class OOP
# =============================================================================
class CameraSolver:
    def __init__(self, root):
        self.root = root
        self.cameras = 0

    def solve(self):
        if self.dfs(self.root) == 0:
            self.cameras += 1
        return self.cameras

    def dfs(self, node):
        if node is None:
            return 2
        left = self.dfs(node.left)
        right = self.dfs(node.right)
        if left == 0 or right == 0:
            self.cameras += 1
            return 1
        if left == 1 or right == 1:
            return 2
        return 0


def min_camera_5(root):
    return CameraSolver(root).solve()


# =============================================================================
# WAY 6: Memoized recursive
# =============================================================================
def min_camera_6(root):
    """Memoize state at each node."""
    memo = {}

    def dfs(node):
        if node in memo:
            return memo[node]
        if node is None:
            return 2
        left = dfs(node.left)
        right = dfs(node.right)
        if left == 0 or right == 0:
            memo[node] = 1
        elif left == 1 or right == 1:
            memo[node] = 2
        else:
            memo[node] = 0
        return memo[node]

    def count_cameras(node):
        if node is None:
            return 0
        left_count = count_cameras(node.left)
        right_count = count_cameras(node.right)
        s = dfs(node)
        return left_count + right_count + (1 if s == 1 else 0)

    # Top-level: also need to handle if root is uncovered.
    total = count_cameras(root)
    if dfs(root) == 0:
        total += 1
    return total


# =============================================================================
# WAY 7: Bottom-up with tuple states (3 values)
# =============================================================================
def min_camera_7(root):
    """Same as Way 1 with explicit tuple unpacking."""
    INF = float("inf")

    def dfs(node):
        if node is None:
            return [0, 0, INF]
        left = dfs(node.left)
        right = dfs(node.right)
        # s0
        s0 = min(left[1], left[2]) + min(right[1], right[2])
        # s1
        s1 = INF
        for ls in left:
            for rs in right:
                if ls == left[2] or rs == right[2]:
                    s1 = min(s1, ls + rs)
        # s2
        s2 = 1 + min(left) + min(right)
        return [s0, s1, s2]

    states = dfs(root)
    return min(states[1], states[2])


# =============================================================================
# WAY 8: Tree DP with named states (enum-like)
# =============================================================================
def min_camera_8(root):
    """Use named state values for clarity."""
    NOT_COVERED, COVERED, HAS_CAMERA = 0, 1, 2
    INF = float("inf")

    def dfs(node):
        if node is None:
            return (0, 0, INF)  # 0 cams, covered, no camera
        l0, l1, l2 = dfs(node.left)
        r0, r1, r2 = dfs(node.right)
        # Node not covered: children must be covered (state 1 or 2)
        s0 = min(l1, l2) + min(r1, r2)
        # Node covered: at least one child has camera (state 2)
        s1 = INF
        for ls in (l0, l1, l2):
            for rs in (r0, r1, r2):
                if ls == l2 or rs == r2:
                    s1 = min(s1, ls + rs)
        # Node has camera: children can be in any covered state
        s2 = 1 + min(l0, l1, l2) + min(r0, r1, r2)
        return (s0, s1, s2)

    s = dfs(root)
    return min(s[1], s[2])


# =============================================================================
# WAY 9: Greedy with explicit None handling
# =============================================================================
def min_camera_9(root):
    """Same as Way 2 but explicit."""
    count = 0

    def dfs(node):
        nonlocal count
        if node is None:
            return "covered"
        left = dfs(node.left)
        right = dfs(node.right)
        if left == "not_covered" or right == "not_covered":
            count += 1
            return "has_camera"
        if left == "has_camera" or right == "has_camera":
            return "covered"
        return "not_covered"

    if dfs(root) == "not_covered":
        count += 1
    return count


# =============================================================================
# WAY 10: BFS layer-by-layer with backtracking
# =============================================================================
def min_camera_10(root):
    """Greedy BFS: process in reverse BFS order, installing cameras at
    parents of uncovered nodes."""
    if root is None:
        return 0
    from collections import deque
    parent = {root: None}
    queue = deque([root])
    bfs_order = []
    while queue:
        node = queue.popleft()
        bfs_order.append(node)
        for child in (node.left, node.right):
            if child:
                parent[child] = node
                queue.append(child)
    covered = set()
    cameras = 0
    # Process in reverse BFS order (deepest first).
    for node in reversed(bfs_order):
        if node in covered:
            continue
        # If this node has any uncovered child, install camera on THIS node
        # (not the parent). This is greedy: cover as many as possible.
        needs_camera = False
        for child in (node.left, node.right):
            if child is not None and child not in covered:
                needs_camera = True
                break
        if needs_camera:
            cameras += 1
            covered.add(node)
            if node.left:
                covered.add(node.left)
            if node.right:
                covered.add(node.right)
            if parent[node]:
                covered.add(parent[node])
    return cameras


# =============================================================================
# WAY 11: Iterative with two-pass
# =============================================================================
def min_camera_11(root):
    """Two-pass: first compute states bottom-up, then count cameras."""
    states = {}  # node -> 0/1/2
    count = [0]

    def postorder(node):
        if node is None:
            return
        postorder(node.left)
        postorder(node.right)
        left = states.get(node.left, 2)
        right = states.get(node.right, 2)
        if left == 0 or right == 0:
            states[node] = 1
            count[0] += 1
        elif left == 1 or right == 1:
            states[node] = 2
        else:
            states[node] = 0

    postorder(root)
    if states.get(root, 2) == 0:
        count[0] += 1
    return count[0]


# =============================================================================
# WAY 12: Use tree-to-list, then DP
# =============================================================================
def min_camera_12(root):
    """Greedy: process in reverse BFS order, install camera on any node
    with uncovered child."""
    if root is None:
        return 0
    from collections import deque
    parent = {root: None}
    queue = deque([root])
    nodes = []
    while queue:
        node = queue.popleft()
        nodes.append(node)
        for child in (node.left, node.right):
            if child:
                parent[child] = node
                queue.append(child)
    n = len(nodes)
    covered = [False] * n
    idx = {node: i for i, node in enumerate(nodes)}
    count = 0
    for node in reversed(nodes):
        i = idx[node]
        # If this node has any uncovered child, install camera here.
        needs = False
        if node.left and not covered[idx[node.left]]:
            needs = True
        if node.right and not covered[idx[node.right]]:
            needs = True
        if needs:
            count += 1
            covered[i] = True
            if node.left:
                covered[idx[node.left]] = True
            if node.right:
                covered[idx[node.right]] = True
            if parent[node]:
                covered[idx[parent[node]]] = True
    return count


# =============================================================================
# WAY 13: Recursive with explicit state names
# =============================================================================
def min_camera_13(root):
    """Recursive with named state return."""
    result = [0]  # camera count

    def dfs(node):
        if node is None:
            return 2  # "covered" by definition
        left = dfs(node.left)
        right = dfs(node.right)
        if left == 0 or right == 0:
            result[0] += 1
            return 1
        if left == 1 or right == 1:
            return 2
        return 0

    if dfs(root) == 0:
        result[0] += 1
    return result[0]


# =============================================================================
# WAY 14: Greedy DFS with single int return
# =============================================================================
def min_camera_14(root):
    """Same as Way 13, using class attribute."""

    class State:
        cameras = 0

        @staticmethod
        def dfs(node):
            if node is None:
                return 2
            left = State.dfs(node.left)
            right = State.dfs(node.right)
            if left == 0 or right == 0:
                State.cameras += 1
                return 1
            if left == 1 or right == 1:
                return 2
            return 0

    if State.dfs(root) == 0:
        State.cameras += 1
    return State.cameras


# =============================================================================
# WAY 15: With tracker class
# =============================================================================
def min_camera_15(root):
    """Track camera count in a dict."""
    state = {"cameras": 0}

    def dfs(node):
        if node is None:
            return 2
        left = dfs(node.left)
        right = dfs(node.right)
        if left == 0 or right == 0:
            state["cameras"] += 1
            return 1
        if left == 1 or right == 1:
            return 2
        return 0

    if dfs(root) == 0:
        state["cameras"] += 1
    return state["cameras"]


# =============================================================================
# WAY 16: DFS with explicit None sentinel
# =============================================================================
def min_camera_16(root):
    """Use sentinel node representation."""
    INF = float("inf")

    def dfs(node):
        if node is None:
            return (0, 0, INF)
        l = dfs(node.left)
        r = dfs(node.right)
        # state_0: not covered. Children covered.
        s0 = min(l[1], l[2]) + min(r[1], r[2])
        # state_1: covered. At least one child has camera.
        s1 = min(
            l[2] + r[1],
            l[2] + r[2],
            l[1] + r[2],
            l[2] + min(r[0], r[1]),
            min(l[0], l[1]) + r[2],
        )
        # state_2: has camera. Children covered.
        s2 = 1 + min(l) + min(r)
        return (s0, s1, s2)

    if root is None:
        return 0
    s = dfs(root)
    return min(s[1], s[2])


# =============================================================================
# WAY 17: Greedy DFS - explicit condition checks
# =============================================================================
def min_camera_17(root):
    """Greedy with detailed comments."""
    count = [0]

    def dfs(node):
        if node is None:
            return 2  # 0=not_covered, 1=has_camera, 2=covered
        left = dfs(node.left)
        right = dfs(node.right)
        # If any child is not_covered, we MUST have a camera here.
        if left == 0 or right == 0:
            count[0] += 1
            return 1
        # Else if any child has camera, this is covered.
        if left == 1 or right == 1:
            return 2
        # Else, this is not covered (no camera, not by children).
        return 0

    if dfs(root) == 0:
        count[0] += 1
    return count[0]


# =============================================================================
# WAY 18: Iterative BFS using parent map
# =============================================================================
def min_camera_18(root):
    """Build parent map, then greedy in reverse BFS order."""
    if root is None:
        return 0
    from collections import deque
    parent = {root: None}
    queue = deque([root])
    nodes = []
    while queue:
        node = queue.popleft()
        nodes.append(node)
        if node.left:
            parent[node.left] = node
            queue.append(node.left)
        if node.right:
            parent[node.right] = node
            queue.append(node.right)
    covered = set()
    count = 0
    for node in reversed(nodes):
        if node in covered:
            continue
        # If any child not covered, install camera here.
        needs = False
        if node.left and node.left not in covered:
            needs = True
        if node.right and node.right not in covered:
            needs = True
        if needs:
            count += 1
            covered.add(node)
            if node.left:
                covered.add(node.left)
            if node.right:
                covered.add(node.right)
            if parent[node]:
                covered.add(parent[node])
    return count


# =============================================================================
# WAY 19: Pure tuple DP (different state interpretation)
# =============================================================================
def min_camera_19(root):
    """Same as Way 1 with different variable names."""
    INF = float("inf")

    def dfs(node):
        if node is None:
            return [0, 0, INF]
        left = dfs(node.left)
        right = dfs(node.right)
        # NOT_MONITORED
        not_mon = min(left[1], left[2]) + min(right[1], right[2])
        # MONITORED (by child)
        mon = INF
        for i in range(3):
            for j in range(3):
                if i == 2 or j == 2:  # at least one child has camera
                    mon = min(mon, left[i] + right[j])
        # HAS_CAMERA
        has_cam = 1 + min(left) + min(right)
        return [not_mon, mon, has_cam]

    s = dfs(root)
    return min(s[1], s[2])


# =============================================================================
# WAY 20: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def min_camera_20(root):
    """
    THE ONE TO MEMORIZE.

    Greedy DFS. Three states per node:
    0 = NOT_COVERED (no camera, not covered by children's cameras).
    1 = HAS_CAMERA (camera installed here).
    2 = COVERED (covered by some child's camera).

    For each node:
    - If any child is NOT_COVERED (0), install camera here -> return 1.
    - Else if any child has CAMERA (1), this is covered -> return 2.
    - Else, return 0 (not covered, no camera, no child coverage).

    After processing root, if root is NOT_COVERED, install camera.

    Time:  O(N).
    Space: O(H) recursion depth.
    """
    count = 0

    def dfs(node):
        nonlocal count
        if node is None:
            return 2  # null is "covered" by definition
        left = dfs(node.left)
        right = dfs(node.right)
        if left == 0 or right == 0:
            count += 1
            return 1  # install camera
        if left == 1 or right == 1:
            return 2  # covered by child
        return 0  # not covered

    if dfs(root) == 0:
        count += 1  # root needs camera
    return count


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"Place minimum cameras on tree nodes such that every node is monitored.
A camera covers itself, its parent, and its children."

Key Insight (Greedy):
"Bottom-up DFS with 3 states per node:
- 0 = NOT_COVERED (no camera, not covered).
- 1 = HAS_CAMERA (camera on this node).
- 2 = COVERED (covered by some child).

For each node:
- If any child is NOT_COVERED -> MUST install camera here -> state 1.
- Else if any child HAS_CAMERA -> this is COVERED -> state 2.
- Else -> NOT_COVERED -> state 0.

After DFS, if root is NOT_COVERED, install camera on root."

Algorithm:
1. DFS postorder.
2. Apply state rules.
3. If root ends up NOT_COVERED, count++.

Why Greedy Works:
- Installing camera on a leaf's parent covers 3 nodes (parent + 2 children).
- Better than installing camera on the leaf itself (1 node covered).

Edge Cases:
- Empty tree: 0.
- Single node: 1.
- All leaves: install cameras on their parents.

Complexity:
+----------+--------+--------+
| Approach | Time   | Space  |
+----------+--------+--------+
| Greedy   | O(N)   | O(H)   |
| State DP | O(N)   | O(H)   |
+----------+--------+--------+
N = nodes, H = height.

THE TRICK:
- "Not covered child" forces camera at parent.
- "Child has camera" makes parent covered.
- After processing, root may need camera too.

RELATED:
- House Robber III (LC 337): tree DP.
- Tree coloring problems.
- Vertex cover on trees.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Tree DP 3-state (BEST)", min_camera_1),
        ("Way 2: Greedy state flags", min_camera_2),
        ("Way 3: Greedy inline", min_camera_3),
        ("Way 4: Iterative postorder", min_camera_4),
        ("Way 5: Class OOP", min_camera_5),
        ("Way 6: Memoized", min_camera_6),
        ("Way 7: Tuple states", min_camera_7),
        ("Way 8: Named states", min_camera_8),
        ("Way 9: Greedy strings", min_camera_9),
        ("Way 10: BFS leaves", min_camera_10),
        ("Way 11: Two-pass", min_camera_11),
        ("Way 12: Tree-to-array", min_camera_12),
        ("Way 13: Recursive count", min_camera_13),
        ("Way 14: Class State", min_camera_14),
        ("Way 15: Tracker dict", min_camera_15),
        ("Way 16: Tuple DP variant", min_camera_16),
        ("Way 17: Greedy detailed", min_camera_17),
        ("Way 18: BFS parent map", min_camera_18),
        ("Way 19: Pure tuple DP", min_camera_19),
        ("Way 20: Final cleanest", min_camera_20),
    ]

    test_cases = [
        # (tree_array, expected)
        ([0], 1),  # Single node
        ([0, 0], 1),  # Root + left
        ([0, 0, 0], 1),  # Root + L + R
        ([0, 0, None, 0, 0], 1),  # LC example 1
        ([0, 0, None, 0, None, 0], 2),  # LC example 2
        ([0, 0, 0, 0, 0, 0, 0], 2),  # Full tree 3 levels
        ([], 0),  # Empty
    ]

    print("=" * 70)
    print("BINARY TREE CAMERAS - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/binary-tree-cameras")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for arr, expected in test_cases:
            try:
                tree = build_tree(arr)
                result = func(tree)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: arr={arr}, expected={expected}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: arr={arr}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
