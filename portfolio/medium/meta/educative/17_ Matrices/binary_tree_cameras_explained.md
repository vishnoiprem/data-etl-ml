# Binary Tree Cameras — 0.0001% Expert Guide

> **LeetCode 968** | **Difficulty:** Hard | **Avg Solve Time:** 40 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/binary-tree-cameras
> **Problem:** `minCameraCover(root)` — minimum cameras to monitor every node.

---

## 📋 WHAT THE QUESTION ASKS

Given a binary tree root, place the minimum number of cameras on nodes such that every node is monitored. A camera on a node covers the node, its parent, and its children.

### Constraints
- `1 <= number of nodes <= 1000`
- `Node.val == 0` (all values zero, structure matters)

### Examples
```
Tree: [0]                            -> 1
Tree: [0,0]                          -> 1   (camera on root)
Tree: [0,0,0]                        -> 1   (camera on root)
Tree: [0,0,null,0,0]                 -> 1   (camera on root.left)
Tree: [0,0,null,0,null,0]            -> 2   (camera on root.left and deepest)
Tree: [0,0,0,0,0,0,0]                -> 2   (cameras on level 1)
Tree: []                             -> 0
```

### Why This Is "Hard"
- Tree DP with 3 states.
- Greedy choice justification.
- Edge case: root needs camera after DFS.

---

## 🧠 HOW TO THINK — STEP BY STEP (Expert Framework)

### Step 1: Understand the Question (1 min)
> "Cover all tree nodes with cameras. Camera covers node + parent + children."

### Step 2: KEY INSIGHT — Greedy on Bottom-up States (5 min)
> "Bottom-up DFS. Three states per node:
> - 0 = NOT_COVERED (no camera, not covered by children's cameras).
> - 1 = HAS_CAMERA (camera installed here).
> - 2 = COVERED (covered by some child's camera, no camera here).
>
> For each node:
> - If any child is NOT_COVERED → must install camera here → return 1.
> - Else if any child HAS_CAMERA → this node is COVERED → return 2.
> - Else → NOT_COVERED → return 0.
>
> After DFS, if root is NOT_COVERED, install camera at root."

### Step 3: Why Greedy is Optimal (3 min)
> "Installing camera on a leaf's PARENT covers 3 nodes (parent + 2 children).
> Installing camera on a LEAF itself covers only 1 node.
> So always prefer placing cameras higher up the tree."

### Step 4: Algorithm (3 min)
```
1. Define dfs(node) returning 0/1/2.
2. For None, return 2 (covered by definition).
3. Recursively get left, right.
4. Apply rules:
   - if left == 0 or right == 0: count++, return 1.
   - elif left == 1 or right == 1: return 2.
   - else: return 0.
5. Call dfs(root). If returns 0: count++.
6. Return count.
```

### Step 5: Edge Cases (2 min)
- Empty tree: 0.
- Single node: 1.
- Deep chain: alternating cameras.
- Full tree: cameras at every other level.

### Step 6: Code It (3 min)

```python
def minCameraCover(root):
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
```

### Step 7: Verify (2 min)
For `[0,0,null,0,0]`:
```
       0
      /
     0
    / \
   0   0
```
DFS postorder:
- Leaf at depth 2: returns 0 (both children None→2, no camera child). Wait, actually returns 0 because both children are "covered" (2) but no child has camera. So leaf is NOT_COVERED.
- Depth 1 left: left=0 → install camera, return 1.
- Depth 1 right: returns 0.
- Root: left=1 → covered, return 2.
- Root returns 2, no extra camera needed. Count = 1. ✓

### Step 8: Discuss Trade-offs (3 min)
> "Two approaches:
> 1. **Greedy DFS:** O(N) time, O(H) space. **BEST**.
> 2. **Tree DP with 3 states:** O(N) time, O(N) space.
>
> Greedy is simpler and same complexity. I'll use greedy."

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT (Memorize This!)

```
"I need minimum cameras to monitor every node in a binary tree.
A camera covers itself, its parent, and its children."

KEY INSIGHT: Greedy bottom-up DFS with 3 states per node:
- 0 = NOT_COVERED (no camera, not covered).
- 1 = HAS_CAMERA (camera here).
- 2 = COVERED (covered by some child).

For each node:
- If any child is NOT_COVERED → MUST install camera → return 1.
- Else if any child HAS_CAMERA → this is COVERED → return 2.
- Else → NOT_COVERED → return 0.

After DFS, if root is NOT_COVERED, install camera at root.

ALGORITHM:
1. DFS postorder.
2. Apply state rules.
3. After processing root, if it's NOT_COVERED, count++.

COMPLEXITY: O(N) time, O(H) space for recursion.

EDGE CASES:
- Empty: 0.
- Single node: 1.
- Chain: alternating cameras.

THE TRICK:
- "Child NOT_COVERED" forces camera at parent.
- "Child HAS_CAMERA" makes parent covered.
- After DFS, root may need its own camera.

WHY GREEDY IS OPTIMAL:
- Camera at leaf's parent covers 3 nodes.
- Camera at leaf covers 1 node.
- Always install higher up.
"""
```

---

## 🔬 THE 20 SOLUTIONS — TECHNIQUE LADDER

### 🟢 TIER 1: Greedy DFS (BEST — Memorize!)

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 2 | Greedy state flags | O(N) | O(H) | **THE ANSWER** |
| 3 | Greedy inline | O(N) | O(H) | Variant |
| 5 | Class OOP | O(N) | O(H) | Reusable |
| 9 | String states | O(N) | O(H) | Educational |
| 13 | List state | O(N) | O(H) | Variant |
| 14 | Class State | O(N) | O(H) | Educational |
| 15 | Dict tracker | O(N) | O(H) | Variant |
| 17 | Greedy detailed | O(N) | O(H) | Educational |
| 20 | Final cleanest | O(N) | O(H) | **THE ONE TO MEMORIZE** |

### 🟡 TIER 2: Tree DP with 3-State Tuple

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 1 | Tree DP 3-state | O(N) | O(H) | **Alternative** |
| 7 | Tuple states | O(N) | O(H) | Variant |
| 8 | Named states | O(N) | O(H) | Educational |
| 16 | Tuple DP variant | O(N) | O(H) | Variant |
| 19 | Pure tuple DP | O(N) | O(H) | Educational |

### 🟠 TIER 3: Iterative / BFS

| Way | Technique | Time | Space | When to Use |
|-----|-----------|------|-------|-------------|
| 4 | Iterative postorder | O(N) | O(H) | No recursion |
| 6 | Memoized recursive | O(N) | O(N) | Educational |
| 10 | BFS leaves | O(N) | O(N) | BFS variant |
| 11 | Two-pass | O(N) | O(N) | Variant |
| 12 | Tree-to-array BFS | O(N) | O(N) | BFS variant |
| 18 | BFS parent map | O(N) | O(N) | BFS variant |

---

## 💎 THE 10-LINE SOLUTION (Memorize!)

```python
def minCameraCover(root):
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
```

**Time:** `O(N)`
**Space:** `O(H)` recursion depth (worst case O(N) for chain)

---

## 🤖 HOW A 0.0001% DATA/AI EXPERT THINKS

### Insight 1: Three States Capture Everything

> Each node is in one of three states:
> - 0: not covered (no camera, not by children).
> - 1: has camera.
> - 2: covered (by child).

**Connection to:**
- **State machine:** 3 discrete states.
- **Bottom-up:** Children → parent.

### Insight 2: Why "Not Covered" Forces Camera

> If a child is NOT_COVERED, the only way to cover it is to install
> a camera at the parent (since grandchildren don't reach it).

**Connection to:**
- **Locality:** Camera only covers 1 level.
- **Necessity:** Forced choice.

### Insight 3: Why Camera Higher is Better

> Installing camera at leaf's parent covers 3 nodes:
> - parent (where camera is).
> - leaf (left child).
> - sibling (right child, if exists).

> Installing camera at leaf covers only 1 node.

**Connection to:**
- **Coverage maximization:** Greedy choice.
- **Locality:** 1-level reach.

### Insight 4: Root Special Case

> After DFS, root may be NOT_COVERED (state 0).
> Root has no parent, so no one covers it from above.
> Must install camera at root.

**Connection to:**
- **Edge case:** Asymmetric root.
- **Final pass:** Always check root.

### Insight 5: Connection to House Robber III

> Both are tree DP problems with 3 states.
> House Robber: take/skip with money.
> Cameras: covered/has-cam/not-covered.

**Connection to:**
- **Tree DP family:** Same skeleton.
- **State design:** Reusable pattern.

### Insight 6: Real-World Applications

| Application | Use |
|-------------|-----|
| **Surveillance** | Minimum cameras to cover building |
| **Network monitoring** | Sensors covering all nodes |
| **Lighting** | Minimum lamps for full coverage |
| **Security** | Cameras in warehouses |
| **Robotics** | Coverage of all points |

**Surveillance** is canonical.

### Insight 7: Why Post-order

> State depends on children first.
> Post-order (DFS left, right, then root) is required.

**Connection to:**
- **Tree traversal:** Bottom-up.
- **State dependency:** Children first.

### Insight 8: None Returns "Covered"

> `None` node returns state 2 (covered).
> This is because the absence of a node is "already covered".
> It prevents installing unneeded cameras at leaves.

**Connection to:**
- **Sentinel:** None is convenient.
- **Base case:** Avoid over-counting.

### Insight 9: Both Children "Covered" → Not Covered Here

> If both children return 2 (covered, no camera), parent is NOT_COVERED.
> Because nothing covers the parent.

**Connection to:**
- **State logic:** Careful with combinations.
- **Greedy:** Don't install camera unnecessarily.

### Insight 10: BFS Variant Possible

> Process tree in reverse BFS order (deepest first).
> Install camera when a node has uncovered children.
> Final check for root.

**Connection to:**
- **Iterative:** No recursion.
- **Same logic:** Different order.

### Insight 11: Time Complexity is O(N)

> Each node visited once (DFS) or once (BFS).
> Constant work per node.
> Total: O(N).

**Connection to:**
- **Linear:** Single pass.
- **Optimal:** Can't do better.

### Insight 12: Why Not 4 States

> Some formulations use 4 states (including "parent has camera").
> But the 3-state formulation captures everything because
> parent's camera coverage is handled at parent level.

**Connection to:**
- **Minimal states:** 3 is enough.
- **Modeling:** Careful design.

### Insight 13: Comparison with Vertex Cover

> Vertex cover on trees: min edges to cover all vertices.
> Cameras: min vertices to cover all vertices with 1-hop range.

Different problem, similar DP structure.

**Connection to:**
- **Graph theory:** Related but different.
- **DP patterns:** Reusable.

### Insight 14: Why Greedy = Optimal

> Greedy installs camera at the highest possible node that
> forces installation. This is provably optimal because:
> - Camera at node covers max possible (3 nodes).
> - Delaying camera installation doesn't help.

**Connection to:**
- **Proof:** Greedy optimality.
- **Standard:** Tree DP greedy.

### Insight 15: Alternative: BFS from Leaves

> Process leaves first, install cameras at their parents.
> Continue up until all nodes covered.
> This is the "greedy BFS" approach (Ways 10, 12, 18).

**Connection to:**
- **Iterative:** BFS variant.
- **Same result:** Optimal.

---

## 🧪 TEST CASES

| Tree | Expected | Note |
|------|----------|------|
| `[0]` | 1 | Single node |
| `[0,0]` | 1 | Root camera |
| `[0,0,0]` | 1 | Root camera |
| `[0,0,null,0,0]` | 1 | LC example 1 |
| `[0,0,null,0,null,0]` | 2 | LC example 2 |
| `[0,0,0,0,0,0,0]` | 2 | Full tree 3 levels |
| `[]` | 0 | Empty |
| `[0,0,0,0,null,null,null,null]` | 2 | Skewed |

---

## 📊 COMPLEXITY SUMMARY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Greedy DFS** | **O(N)** | **O(H)** | **✅ BEST** |
| Tree DP 3-state | O(N) | O(H) | ✅ Alternative |
| BFS leaves | O(N) | O(N) | ✅ Iterative |
| Iterative postorder | O(N) | O(H) | ✅ No recursion |

N = nodes, H = height.

---

## 🔗 RELATED PROBLEMS

| Problem | Technique | Link |
|---------|-----------|------|
| House Robber III (LC 337) | Tree DP | https://leetcode.com/problems/house-robber-iii/ |
| Vertex Cover on Trees | Tree DP | Various |
| Minimum Vertex Cover | Graph DP | https://en.wikipedia.org/wiki/Vertex_cover |
| Tree Coloring | Tree DP | Various |
| Surveillance Cameras | Greedy | Various |

---

## 🎓 EXPERT TAKEAWAYS

1. **3 states per node:** NOT_COVERED, HAS_CAMERA, COVERED.
2. **Greedy is optimal** (camera at parent covers 3 nodes).
3. **Post-order DFS** required.
4. **None returns COVERED** (state 2).
5. **Root special case** — check after DFS.
6. **Surveillance** is canonical use case.
7. **Same skeleton** as House Robber III.
8. **O(N) time, O(H) space** — optimal.
9. **BFS variant** available for iterative.
10. **Not-covered child** forces camera at parent.

---

## 🚀 AI / DATA ENGINEERING CONNECTIONS

| Domain | Connection |
|--------|------------|
| **Surveillance** | Camera placement |
| **Network sensors** | Coverage optimization |
| **Lighting** | Minimum lamps |
| **Security** | Warehouse cameras |
| **Robotics** | Coverage planning |
| **IoT** | Sensor placement |
| **Telecom** | Cell tower placement |
| **Smart cities** | Traffic monitoring |
| **Agriculture** | Field sensors |
| **Disaster response** | Monitoring stations |

---

## ✅ FINAL CHECKLIST

- [x] Can explain the problem in 30 seconds
- [x] Can derive the 3-state greedy in 90 seconds
- [x] Can code the 10-line solution in 60 seconds
- [x] Know complexity: O(N) time, O(H) space
- [x] Know the 3 states (NOT_COVERED, HAS_CAMERA, COVERED)
- [x] Know why camera higher is better
- [x] Know root special case
- [x] Know None returns COVERED
- [x] Know BFS variant
- [x] Can list 5 real-world applications

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Time to solve in interview:** < 20 minutes.
**Lines of code to write:** 10.
**Insight:** "Bottom-up DFS, 3 states. Child NOT_COVERED forces camera. Child HAS_CAMERA makes parent covered. Root needs camera if NOT_COVERED."
