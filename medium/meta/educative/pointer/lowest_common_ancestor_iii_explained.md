# Lowest Common Ancestor of a Binary Tree III — 0.0001% Expert Guide

> **LeetCode 1650** | **Difficulty:** Medium | **Avg Solve Time:** 30 min
> **Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/lowest-common-ancestor-of-a-binary-tree-iii
> **Problem:** `lowestCommonAncestor(p, q)` — LCA with parent pointers.

---

## 📋 WHAT THE QUESTION ASKS

Given two nodes `p` and `q` in a binary tree with **parent pointers** (no root reference), return their **lowest common ancestor** (LCA).

Each node has access to its parent via `node.parent`. Root is not given.

### Constraints
- `-10^4 <= Node.data <= 10^4`
- `2 <= number of nodes <= 500`
- All `Node.data` unique.
- `p != q`
- Both `p` and `q` present in tree.

### Examples
```
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
LCA(3, 8) = 3   (3 is ancestor of 8)
```

### Why This Is "Medium"
- Parent pointers enable upward walking.
- O(h) time, O(1) space (best approach).
- Two-pointer meeting technique.

---

## 🧠 HOW TO THINK — STEP BY STEP

### Step 1: Understand the Problem
> "Find LCA of two nodes with parent pointers. No root given."

### Step 2: Key Insight — Walk Up
> "With parent pointers, we can walk from any node up to root.
> LCA = first shared ancestor when walking up."

### Step 3: Two Approaches
**a) HashSet:** Walk p up, mark ancestors. Walk q up; first match = LCA. O(h) time, O(h) space.

**b) Two-pointer meeting (BEST):** Like linked-list cycle.
- `a = p, b = q`.
- While `a != b`:
  - `a = a.parent if a else q`.
  - `b = b.parent if b else p`.
- They meet at LCA after at most 2*(h+1) steps.

### Step 4: Why Meeting-Point Works
> "Imagine two linked lists:
> List 1: p → root → q.
> List 2: q → root → p.
> They intersect at LCA. Two-pointer meeting finds intersection."

### Step 5: Algorithm
```
1. a, b = p, q.
2. While a != b:
     a = a.parent if a else q.
     b = b.parent if b else p.
3. Return a (= b at this point).
```

### Step 6: Edge Cases
- p is ancestor of q: they meet at p.
- q is ancestor of p: they meet at q.
- They meet at LCA = sibling case.

### Step 7: Code It
```python
def lowestCommonAncestor(p, q):
    a, b = p, q
    while a is not b:
        a = a.parent if a else q
        b = b.parent if b else p
    return a
```

### Step 8: Verify
For LCA(5, 4) where 5 is ancestor of 4:
- a=5, b=4. Diff. a=5.parent=3. b=4.parent=2.
- a=3, b=2. Diff. a=3.parent=None → a=q=4. b=2.parent=5.
- a=4, b=5. Diff. a=4.parent=2. b=5.parent=3.
- a=2, b=3. Diff. a=2.parent=5. b=3.parent=None → b=5.
- a=5, b=5. Meet! Return 5. ✓

### Trade-offs
- Meeting-point: O(h) time, O(1) space. **BEST**.
- HashSet: O(h) time, O(h) space.
- Depth equalization: O(h) time, O(1) space.

---

## 🎯 THE GOLDEN INTERVIEW SCRIPT

```
"I need to find LCA with parent pointers, no root."

KEY INSIGHT: Walk upward. The first shared ancestor is LCA.
Two-pointer meeting: when one pointer hits None, jump to other's start.

ALGORITHM:
1. a, b = p, q.
2. While a != b:
     a = a.parent if a else q.
     b = b.parent if b else p.
3. Return a.

COMPLEXITY: O(h) time, O(1) space.

EDGE CASES:
- p is ancestor of q: meet at p.
- q is ancestor of p: meet at q.

WHY MEETING-POINT WORKS:
- Treat as two linked lists: p→root→q and q→root→p.
- They intersect at LCA.
- Same as "intersection of two linked lists".

THE TRICK:
- "When a hits None, redirect to q's start."
- Equalizes path lengths implicitly.

ALTERNATE: HashSet of p's ancestors, then check q's path.
Or: depth equalization, then walk together.

RELATED:
- LCA in regular binary tree (LC 236) — recursion.
- LCA in BST (LC 235) — BST property.
- Intersection of two linked lists (LC 160) — same technique.
"""
```

---

## 💎 THE 5-LINE SOLUTION (Memorize!)

```python
def lowestCommonAncestor(p, q):
    a, b = p, q
    while a is not b:
        a = a.parent if a else q
        b = b.parent if b else p
    return a
```

**Time:** `O(h)` | **Space:** `O(1)`

---

## 🤖 KEY INSIGHTS

1. **Parent pointers** = walk upward.
2. **Meeting-point technique** = elegant O(1) space.
3. **Linked-list cycle** analogy works here.
4. **O(h) is** O(n) worst case (skewed tree).
5. **HashSet** is simpler but O(h) space.
6. **Depth equalization** is alternative O(1) space.
7. **No root needed** — just parent pointers.
8. **Same as intersection** of two linked lists.
9. **p or q** might be the LCA itself.
10. **Constraints small** (n ≤ 500), all approaches work.

---

## 🧪 TEST CASES

| `p` | `q` | Expected | Note |
|-----|-----|----------|------|
| `5` | `1` | `3` | Different subtrees |
| `5` | `4` | `5` | p is ancestor |
| `7` | `4` | `2` | Same subtree |
| `6` | `4` | `5` | Different paths |
| `0` | `8` | `1` | Same parent |
| `3` | `8` | `3` | Root LCA |
| `7` | `6` | `5` | Cross paths |

---

## 📊 COMPLEXITY

| Approach | Time | Space | Verdict |
|----------|------|-------|---------|
| **Meeting-point** | **O(h)** | **O(1)** | **✅ BEST** |
| HashSet | O(h) | O(h) | ✅ Simple |
| Depth equalize | O(h) | O(1) | ✅ Alternative |
| Find root + recursive | O(n) | O(h) | ❌ Slower |

---

## 🔗 RELATED

- LCA Binary Tree (LC 236) — recursion, no parent
- LCA BST (LC 235) — BST property
- Intersection Two Linked Lists (LC 160) — same technique
- Path to node problems

---

**Status:** ✅ Mastered at 0.0001% expert level.
**Insight:** "Two pointers p, q. When one hits None, jump to other's start. They meet at LCA after at most 2*(h+1) steps."