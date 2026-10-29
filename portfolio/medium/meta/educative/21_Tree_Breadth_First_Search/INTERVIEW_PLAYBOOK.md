# Tree BFS — Playbook, Memory Anchors, and Uses in AI

> This document is structured around your three questions:
> **Part 1 — How to think** (the algorithmic reasoning during an interview).
> **Part 2 — How to remember** (mnemonics and mental "hooks" so the patterns stick).
> **Part 3 — How to use these in AI** (real ML / DL / Agentic systems that solve the same way).

---

## PART 1 — How to think

### 1.1 The opening line (say this whenever a tree problem starts)

> "Trees are graphs without cycles. BFS gives me level-by-level access for free, which is more useful than any line count. If the problem says *by level*, *kth from root*, *minimum depth*, *shortest path from X to Y*, BFS is my default."

### 1.2 The 4-question classifier (always silent-first, then aloud)

| # | Question | Answer |
|---|----------|--------|
| Q1 | Does the problem mention **levels** explicitly? | Use level-by-level BFS (snapshot `len(q)` each loop). |
| Q2 | Do I want the **first** node satisfying a predicate? | Early-exit BFS (return the moment the goal-test is true). |
| Q3 | Do I need **left ↔ right** symmetry / comparison within a level? | Queue pairs `(L, R)` and compare them in lockstep. |
| Q4 | Is the graph **implicit** (defined by a transition, not stored)? | BFS over implicit graph — generate neighbours on the fly. |

Most tree-BFS problems are some combination of these four.

### 1.3 The universal template

```python
from collections import deque

def bfs(root):
    if not root: return []
    result, q = [], deque([root])
    while q:
        level = []
        for _ in range(len(q)):        # ← snapshot = level boundary
            node = q.popleft()
            level.append(node.val)     # ← replace with predicate / reduce
            if node.left:  q.append(node.left)
            if node.right: q.append(node.right)
        result.append(level)
    return result
```

**What changes between problems:** the line `level.append(...)`. It can become `level_sum +=`, `is_leaf`, `pair_check(node.left, node.right)`, etc. That's the only edit.

### 1.4 Decision matrix for the 10 problems

| File | Pattern | Why BFS |
|------|---------|---------|
| `01_introduction_to_tree_bfs.py` | Template | Level-by-level bucket. |
| `02_average_of_levels.py` | Level-bucket + reduce | Substitute `sum/length` for `append`. |
| `03_minimum_depth_binary_tree.py` | Early-exit BFS | First leaf = min depth by construction. |
| `04_symmetric_tree.py` | Pair-comparison BFS | Each level must be a palindrome. |
| `05_populating_next_right_pointers.py` | Level-linked BFS | Carry `prev` across siblings. |
| `06_zigzag_level_order.py` | Level-bucket + direction toggle | Flip left/right per level. |
| `07_connect_all_siblings.py` | Single linked-list BFS | `prev` chains without level reset. |
| `08_two_sum_bst.py` | BFS + lookup set | O(n) without leveraging BST. |
| `09_vertical_order_traversal.py` | BFS with coordinates | Sort by `(col, row, val)`. |
| `10_open_the_lock.py` | BFS over implicit graph | Generate neighbours on the fly. |

### 1.5 Interview script (3 timed phases)

1. **Classify (15 s):** "It's BFS because the problem asks for levels / minimum turns / nearest leaf."
2. **State the state (15 s):** "I'll keep `queue` for frontier and `visited` (when needed)." Skip `visited` only when the graph is a tree.
3. **Sketch (30 s):** "While the queue is not empty, snapshot its size, process that many nodes, enqueue their children."

### 1.6 Traps

| Trap | Symptom | Fix |
|------|---------|-----|
| Forgetting `len(q)` snapshot | Levels bleed into each other | Snapshot the queue size BEFORE the inner loop. |
| Using DFS for minimum depth | Returns `1 + min(0, depth)` for half-trees | Use BFS; the first leaf is the answer. |
| Reversing an *empty* list | Off-by-one on a single-child tree | Empty levels are still pushed to `result`; check both None-symmetry carefully. |
| Modifying a tree you're traversing | Corrupts later levels | Make a new `deque` per problem, don't rewire `parent` pointers mid-BFS unless the problem says so. |
| Trying to dedupe visited in an implicit graph | TLE / memory blow-up | Always `visited.add(...)` BEFORE pushing to the queue. |

---

## PART 2 — How to remember

### 2.1 The "shorthand" — say this one phrase during the interview

> **"Snapshot the queue, process that many, push children."**

It is the entire algorithm in 8 words. Anything else is a variation.

### 2.2 Mnemonic for the 5 shapes you must be able to draw cold

Memory hook — visualise each as a **kitchen utensil**:

| Pattern | Visual | Cue |
|---------|--------|-----|
| Level-bucket (avg/sum/etc) | Soup ladle scooping level by level | "**Ladle**" → `len(q)` snapshot. |
| Early-exit BFS (min depth) | First pancake off the griddle | "**Pancake**" → return at first leaf. |
| Pair-comparison (symmetric) | Two hands high-fiving | "**High-five**" → queue of `(L, R)` pairs. |
| Linked-list BFS (siblings / next) | Linking sausages | "**Sausage**" → carry `prev`. |
| Implicit-graph BFS (open the lock) | Whack-a-mole with new states | "**Whack-a-mole**" → generate neighbours, dedupe via `visited`. |

Draw these 5 utensil-words on a sticky note before you walk into the interview.

### 2.3 Two memorisation rhythms

**Rhythm A (15 min/day, 7 days):**
- Day 1: read §1.3 + file 01.
- Day 2–7: each morning, re-derive ONE file from scratch, no peeking.
- End of Day 7 you have 6 patterns cold (all but the linked-list family).
- Day 8: redo 07, 08, 09 together (they share the `prev` / coordinate trick).

**Rhythm B (if you only have an hour):**
- Memorise the universal template (§1.3) verbatim.
- Memorise the 5 utensil-words (§2.2).
- Re-derive 02, 03, 04 from those — three problems in an hour, full confidence.

### 2.4 The 30-second cold-recall drill

Without writing code, state out loud:
1. **Template skeleton.**
2. **Which shape applies** to the new problem.
3. **What changes inside `level.append(...)`** (or whatever the inner work is).

If you can do all three in under 30 seconds, you're ready to code.

---

## PART 3 — How to use these in AI

Tree BFS is far from "just an interview trick". It is the algorithmic backbone of *many* real AI systems. Below is a tour.

### 3.1 Decision Trees / Random Forests — classical ML

Each internal node is `if x[feature] ≤ threshold`, each leaf a class label. **Inference** is exactly tree-BFS:

```
# scikit-learn equivalent
def predict_one(tree, x):
    node = tree.root
    while node.is_leaf() is False:
        node = node.left if x[node.feature] <= node.threshold else node.right
    return node.value
```

This is **DFS** (down to a leaf) for a single example. For **batch prediction** or **per-level metric collection** (e.g. "how many leaves does path length ≤ k reach?"), use BFS over the tree.

### 3.2 Beam search & BFS in language models

Decoding in LLMs (e.g. a T5 captioner, an offline translation system) often uses **beam search**, which is **BFS on a tree of partial token sequences**:

- Each level = adding one token.
- Each node = a partial hypothesis + its score.
- You keep the top-`k` hypotheses per level (the beam).

The skeleton is literally the file-01 template, with a `heapq.nlargest` filter on the level bucket:

```python
def beam_search(model, start_token, beam_size=5, max_len=50):
    beams = [(0.0, [start_token])]
    for _ in range(max_len):
        all_next = []
        for score, seq in beams:
            logits = model.next_token_logits(seq)   # scores for next token
            for token, p in topk(logits, beam_size):
                all_next.append((score + log(p), seq + [token]))
        beams = sorted(all_next, reverse=True)[:beam_size]
    return beams[0]
```

### 3.3 AlphaZero / MCTS (game AI)

Monte-Carlo Tree Search uses **BFS-like expansion** of a search tree of game states. After a playout, the result is **propagated up the path** — exactly like the `connect_siblings` pattern (chaining through `prev`).

### 3.4 Knowledge-graph reasoning (retrieval / RAG)

A knowledge graph `entity → relation → entity` defines an implicit graph. Multi-hop QA (e.g. "Who founded the company that acquired X?") is **BFS over the implicit graph**, with `visited` controlling hop-count limits. This is the production-grade cousin of `open_the_lock`.

```python
def multi_hop_retrieve(start_entity, max_hops=3):
    frontier = [(start_entity, 0)]
    visited = {start_entity}
    while frontier:
        next_frontier, retrieved = [], []
        for entity, hop in frontier:
            for (rel, neighbour) in kg.neighbours(entity):
                if neighbour in visited: continue
                visited.add(neighbour)
                retrieved.append((entity, rel, neighbour))
                if hop + 1 < max_hops: next_frontier.append((neighbour, hop + 1))
        frontier = next_frontier
        yield retrieved
```

### 3.5 Token-tree attention in vision transformers

Hierarchical vision transformers (e.g. Swin Transformer, MViT) build a **pyramid of feature maps** by merging neighbouring tokens level by level. The merging operation is bottom-up BFS across a 2-D spatial graph. The result is a multi-scale feature "tree", which downstream heads use for detection or segmentation.

### 3.6 Pathfinding in robotics / motion planning

Rapidly-Exploring Random Trees (RRT) and A* on a grid are both BFS-like tree searches over a configuration space.

### 3.7 Reinforcement learning — eligibility traces

In TD(λ) or advantage actor-critic, the credit-assignment trace is a **tree of future rewards** indexed by step. The computation that backs through it is level-by-level — BFS with rewards as the payload.

---

## TL;DR — what to take away

1. **One template, five shapes**, four question-classifiers, ten files.
2. **Say "snapshot the queue"** to yourself whenever a tree problem starts; that phrase alone will carry you 80% of the way.
3. The same algorithms are running under the hood of:
   - scikit-learn's `DecisionTreeClassifier.predict`,
   - LLM beam search,
   - AlphaZero,
   - RAG multi-hop retrieval,
   - Vision-transformer token merging,
   - Robot motion planners.

If you can recognise these in the wild, you've already crossed from "interview prep" into "useful engineering judgement".
