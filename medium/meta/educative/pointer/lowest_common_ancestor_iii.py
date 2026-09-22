"""
Lowest Common Ancestor of a Binary Tree III
Medium | 30 min

Given two nodes p and q in a binary tree with parent pointers (but no
root reference), return their lowest common ancestor (LCA).

Note: each node has access to its parent via node.parent.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/lowest-common-ancestor-of-a-binary-tree-iii

Examples:
    Tree:
            3
           / \
          5   1
         / \ / \
        6  2 0  8
          / \
         7   4

    LCA(5, 1) = 3
    LCA(5, 4) = 5
    LCA(7, 4) = 2

Constraints:
- -10^4 <= Node.data <= 10^4
- 2 <= number of nodes <= 500
- All Node.data are unique.
- p != q
- Both p and q are present in the tree.

KEY INSIGHT:
With parent pointers, we can walk UP from p and q. The LCA is the first
shared ancestor. Two-pointer technique:
- Walk p up, track visited.
- Walk q up; first visited node is LCA.

Or "meeting point" technique (like linked-list cycle):
- a_ptr, b_ptr start at p, q.
- When a_ptr reaches null, jump to q. When b_ptr reaches null, jump to p.
- They meet at LCA after 2*(depth) steps.

Time:  O(h) — h = tree height.
Space: O(1) — meeting-point technique (or O(h) for visited set).
"""


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT LCA WITH PARENT POINTERS:

1. UNDERSTAND THE PROBLEM:
   "Two nodes p, q with parent pointers. Find their LCA. No root given."

2. KEY OBSERVATION:
   "With parent pointers, we can walk UP from any node.
   The LCA is the first node that's an ancestor of both."

3. TWO APPROACHES:
   a) **HashSet**: Walk p up, add all ancestors to set. Walk q up;
      first node in set = LCA. O(h) time, O(h) space.
   b) **Two-pointer meeting (BEST)**: Like linked-list cycle detection.
      - a=p, b=q.
      - Walk both up. When a hits null, redirect to q.
      - When b hits null, redirect to p.
      - They meet at LCA after at most 2*(h_diff) + (h) steps.

4. WHY MEETING-POINT WORKS:
   - Treat the upward paths as two "linked lists".
   - Concatenate them: p→root + q→root.
   - Intersection at LCA, found by meeting.
   - Same as "intersection of two linked lists".

5. EDGE CASES:
   - p is ancestor of q (or vice versa): they meet at the ancestor.
   - p and q are siblings: LCA is parent.
   - p == q (not allowed by constraints).

6. COMPLEXITY:
   +----------+--------+--------+
   | Approach | Time   | Space  |
   +----------+--------+--------+
   | Hash     | O(h)   | O(h)   |
   | Meeting  | O(h)   | O(1)   |
   +----------+--------+--------+

7. WHY MEETING > HASH:
   - O(1) space vs O(h).
   - Same time complexity.
   - More elegant.
"""


# =============================================================================
# WAY 1: Two-pointer meeting (BEST - Memorize!)
# =============================================================================
def lowest_common_ancestor_1(p, q):
    """
    Two-pointer meeting technique.
    Like linked-list cycle: when one pointer hits None, jump to other.
    They meet at LCA.
    """
    a, b = p, q
    # Walk until they meet.
    while a is not b:
        a = a.parent if a else q
        b = b.parent if b else p
    return a


# =============================================================================
# WAY 2: HashSet of p's ancestors
# =============================================================================
def lowest_common_ancestor_2(p, q):
    """Walk p up, record ancestors. Walk q up; first match = LCA."""
    ancestors = set()
    node = p
    while node:
        ancestors.add(node)
        node = node.parent
    node = q
    while node:
        if node in ancestors:
            return node
        node = node.parent
    return None  # Should never reach here per constraints.


# =============================================================================
# WAY 3: Depth equalization, then walk together
# =============================================================================
def lowest_common_ancestor_3(p, q):
    """
    Walk both up to compute depths.
    Bring deeper one up until depths match.
    Then walk both up together until they meet.
    """
    def depth(node):
        d = 0
        while node:
            d += 1
            node = node.parent
        return d

    dp, dq = depth(p), depth(q)
    # Bring deeper one up.
    while dp > dq:
        p = p.parent
        dp -= 1
    while dq > dp:
        q = q.parent
        dq -= 1
    # Walk together.
    while p is not q:
        p = p.parent
        q = q.parent
    return p


# =============================================================================
# WAY 4: Two-pointer meeting (same as Way 1, explicit counter)
# =============================================================================
def lowest_common_ancestor_4(p, q):
    """
    Same as Way 1 but with explicit iteration limit
    to make the algorithm's bound visible.
    """
    a, b = p, q
    # At most 2*(h+1) iterations: one full walk plus second walk.
    for _ in range(2 * 501):  # 2*(max nodes = 500)
        if a is b:
            return a
        a = a.parent if a else q
        b = b.parent if b else p
    return a  # Should reach here only if a is b.


# =============================================================================
# WAY 5: Use visited flag with None sentinel
# =============================================================================
def lowest_common_ancestor_5(p, q):
    """Use None as terminator sentinel."""
    a, b = p, q
    while True:
        if a is None:
            a = q
        if b is None:
            b = p
        if a is b:
            return a
        a = a.parent
        b = b.parent


# =============================================================================
# WAY 6: Find path lists, then last common
# =============================================================================
def lowest_common_ancestor_6(p, q):
    """Get full paths up to root, find last common."""
    path_p = []
    node = p
    while node:
        path_p.append(node)
        node = node.parent
    path_q = []
    node = q
    while node:
        path_q.append(node)
        node = node.parent
    # Find last common from root.
    i = len(path_p) - 1
    j = len(path_q) - 1
    while i >= 0 and j >= 0 and path_p[i] is path_q[j]:
        i -= 1
        j -= 1
    return path_p[i + 1]


# =============================================================================
# WAY 7: Class OOP
# =============================================================================
class LCASolver:
    def __init__(self, p, q):
        self.p = p
        self.q = q

    def solve(self):
        a, b = self.p, self.q
        while a is not b:
            a = a.parent if a else self.q
            b = b.parent if b else self.p
        return a


def lowest_common_ancestor_7(p, q):
    return LCASolver(p, q).solve()


# =============================================================================
# WAY 8: Find root first, then standard LCA
# =============================================================================
def lowest_common_ancestor_8(p, q):
    """Walk up from p to find root, then use root-based LCA."""
    # Find root.
    root = p
    while root.parent:
        root = root.parent

    # Now use standard LCA with root and parent pointers.
    # (Recursive helper for clarity.)
    def lca(root, p, q):
        if not root or root is p or root is q:
            return root
        left = lca(root.left, p, q)
        right = lca(root.right, p, q)
        if left and right:
            return root
        return left or right

    return lca(root, p, q)


# =============================================================================
# WAY 9: Iterative with counter (max iterations = 2*h)
# =============================================================================
def lowest_common_ancestor_9(p, q):
    """Iterative meeting with explicit max iterations."""
    a, b = p, q
    # After at most 2*(h+1) steps, they MUST meet.
    for _ in range(10000):  # generous upper bound
        if a is b:
            return a
        a = a.parent if a else q
        b = b.parent if b else p
    return None


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def lowest_common_ancestor_10(p, q):
    """
    THE ONE TO MEMORIZE.

    Two-pointer meeting technique.
    Like linked-list cycle: when one pointer hits None, jump to other.
    They meet at LCA.

    Time:  O(h).
    Space: O(1).
    """
    a, b = p, q
    while a is not b:
        a = a.parent if a else q
        b = b.parent if b else p
    return a


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    # Define EduTreeNode inline since we don't import it.
    class EduTreeNode:
        def __init__(self, data):
            self.data = data
            self.left = None
            self.right = None
            self.parent = None

        def __repr__(self):
            return f"Node({self.data})"

    # Build test tree:
    #         3
    #        / \
    #       5   1
    #      / \ / \
    #     6  2 0  8
    #       / \
    #      7   4
    n3 = EduTreeNode(3)
    n5 = EduTreeNode(5)
    n1 = EduTreeNode(1)
    n6 = EduTreeNode(6)
    n2 = EduTreeNode(2)
    n0 = EduTreeNode(0)
    n8 = EduTreeNode(8)
    n7 = EduTreeNode(7)
    n4 = EduTreeNode(4)

    # Set children.
    n3.left, n3.right = n5, n1
    n5.left, n5.right = n6, n2
    n1.left, n1.right = n0, n8
    n2.left, n2.right = n7, n4

    # Set parents.
    n5.parent = n3
    n1.parent = n3
    n6.parent = n5
    n2.parent = n5
    n0.parent = n1
    n8.parent = n1
    n7.parent = n2
    n4.parent = n2

    implementations = [
        ("Way 1: Two-pointer meeting (BEST)", lowest_common_ancestor_1),
        ("Way 2: HashSet of ancestors", lowest_common_ancestor_2),
        ("Way 3: Depth equalization", lowest_common_ancestor_3),
        ("Way 4: Iterative with seen", lowest_common_ancestor_4),
        ("Way 5: None sentinel", lowest_common_ancestor_5),
        ("Way 6: Path lists", lowest_common_ancestor_6),
        ("Way 7: Class OOP", lowest_common_ancestor_7),
        ("Way 8: Find root first", lowest_common_ancestor_8),
        ("Way 9: Max iterations", lowest_common_ancestor_9),
        ("Way 10: Final cleanest", lowest_common_ancestor_10),
    ]

    test_cases = [
        # (p, q, expected_data)
        (n5, n1, 3),
        (n5, n4, 5),
        (n7, n4, 2),
        (n6, n4, 5),
        (n0, n8, 1),
        (n7, n8, 3),
        (n3, n8, 3),  # p is ancestor of q
        (n7, n6, 5),
    ]

    print("=" * 70)
    print("LOWEST COMMON ANCESTOR III - 10 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/lowest-common-ancestor-of-a-binary-tree-iii")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for p, q, expected_data in test_cases:
            try:
                result = func(p, q)
                if result is None or result.data != expected_data:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: p={p.data}, q={q.data}, expected={expected_data}, got={result}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: p={p.data}, q={q.data}, ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)