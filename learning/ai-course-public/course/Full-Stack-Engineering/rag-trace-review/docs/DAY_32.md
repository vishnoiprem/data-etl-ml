# Day 32 — Mock Coding Interview
**Module 21** | Total: 90 min (10 + 20 + 30 + 20 + 20)

---

## 1. Simple explanation (10 min)

Today is a **full 45-minute mock coding interview**, compressed to 30 min coding + 20 min discussion.

The interviewer says: "Solve a real problem end-to-end. Talk through your thinking. I'll ask follow-ups."

Two problems: one **Medium** (LRU Cache) and one **Hard** (Word Ladder II — a stretch goal). The first is graded; the second is bonus.

---

## 2. Technical concepts (20 min)

### The 60-min rhythm
- 0–2 min: restate the problem
- 2–5 min: ask clarifying questions
- 5–8 min: state brute force + complexity
- 8–12 min: describe optimal approach
- 12–32 min: code (clean, runnable)
- 32–37 min: trace through an example
- 37–45 min: test edge cases

### Communication template
> "I'm going to start with a brute-force approach. The state is... the recurrence is... the complexity is O(n²). I can optimize to O(n) by..."

### The "I'm stuck" escape hatch
- Stop coding. Say: "Let me think out loud."
- Draw the input.
- Try n=0, n=1, n=2, n=3.
- Look for a pattern.
- Suggest a simpler sub-problem.

### The "I made a mistake" recovery
- Say it: "I think there's a bug here."
- Trace: "When input is X, I do A, B, C. Expected D, got E."
- Don't pretend. Recoveries are scored positively.

---

## 3. Coding (30 min)

### Problem 1: LRU Cache (Medium) — graded

Design a data structure that follows the constraints of a **Least Recently Used (LRU) cache**. Implement the `LRUCache` class:

- `LRUCache(int capacity)` — initialize with positive capacity.
- `int get(int key)` — return value if key exists, else -1. Marks as recently used.
- `void put(int key, int value)` — insert/update. If over capacity, evict the **least recently used** key.

Both operations must be **O(1)**.

#### Solution
```python
class Node:
    __slots__ = ("k", "v", "prev", "next")
    def __init__(self, k, v):
        self.k = k; self.v = v; self.prev = None; self.next = None

class LRUCache:
    def __init__(self, capacity: int):
        self.cap = capacity
        self.cache: dict[int, Node] = {}
        # Sentinel head and tail — never evicted, never store data.
        self.head = Node(0, 0)
        self.tail = Node(0, 0)
        self.head.next = self.tail
        self.tail.prev = self.head

    def _remove(self, n: Node) -> None:
        n.prev.next = n.next
        n.next.prev = n.prev

    def _add(self, n: Node) -> None:
        n.prev = self.head
        n.next = self.head.next
        self.head.next.prev = n
        self.head.next = n

    def get(self, key: int) -> int:
        if key not in self.cache: return -1
        n = self.cache[key]
        self._remove(n); self._add(n)
        return n.v

    def put(self, key: int, value: int) -> None:
        if key in self.cache:
            self._remove(self.cache[key])
        n = Node(key, value)
        self._add(n)
        self.cache[key] = n
        if len(self.cache) > self.cap:
            # Evict the LRU: the node just before tail
            lru = self.tail.prev
            self._remove(lru)
            del self.cache[lru.k]
```

#### Walkthrough (when `cap=2`)
- `put(1,1)`: cache = {1:1}, list = [(head), 1, (tail)].
- `put(2,2)`: cache = {1:1, 2:2}, list = [(head), 1, 2, (tail)].
- `get(1)`: returns 1, list = [(head), 2, 1, (tail)] — `1` moves to the front (most-recently used).
- `put(3,3)`: evicts `2` (the LRU, now at `tail.prev`), cache = {1:1, 3:3}.
- `get(2)`: returns -1.

#### Why this works
- Hash map → O(1) lookup.
- Doubly-linked list → O(1) insertion/removal, and we always know the LRU (`tail.prev`).
- The list maintains usage order: **most-recent at `head.next`** (touching head), **least-recent at `tail.prev`** (touching tail). `_add` inserts after head; `_remove` unlinks a node.

#### Alternative (Python idiomatic)
```python
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.cap = capacity
        self.d = OrderedDict()
    def get(self, key: int) -> int:
        if key not in self.d: return -1
        self.d.move_to_end(key)
        return self.d[key]
    def put(self, key: int, value: int) -> None:
        if key in self.d:
            self.d.move_to_end(key)
        self.d[key] = value
        if len(self.d) > self.cap:
            self.d.popitem(last=False)  # LRU
```

### Problem 2: Word Ladder (Hard) — bonus, optional

Given `beginWord`, `endWord`, and a `wordList`, return the **length of the shortest transformation sequence** from `begin` to `end` such that:
- Only one letter can be changed at a time.
- Each transformed word must be in `wordList`.

```python
from collections import deque

def ladder_length(begin: str, end: str, word_list: list[str]) -> int:
    word_set = set(word_list)
    if end not in word_set: return 0
    q = deque([(begin, 1)])
    visited = {begin}
    L = len(begin)
    while q:
        word, depth = q.popleft()
        if word == end: return depth
        for i in range(L):
            for c in "abcdefghijklmnopqrstuvwxyz":
                nw = word[:i] + c + word[i+1:]
                if nw in word_set and nw not in visited:
                    visited.add(nw)
                    q.append((nw, depth + 1))
    return 0
```

- **Time:** O(L · 26 · B), where L is the word length and B is the BFS frontier (≤ N). **Space:** O(N) for the visited set + queue.
- **Sample:** `begin="hit", end="cog", list=["hot","dot","dog","lot","log","cog"]` → `5` (hit→hot→dot→dog→cog).

---

## 4. Debugging & tests (20 min)

### Bug 1: LRU eviction removes the wrong key
**Symptom:** after `get(1)`, putting 3 evicts 1 instead of 2.
**Fix:** `_remove` then `_add` in `get`. The recently-accessed node goes back to the front.

### Bug 2: sentinels get evicted
**Symptom:** cache breaks after a few ops.
**Fix:** `head` and `tail` are sentinels, never in `cache`. Only evict `tail.prev` after checking `len > cap`.

### Bug 3: word ladder revisits nodes
**Symptom:** infinite loop.
**Fix:** `visited` set; only add when pushing to queue.

### Bug 4: end not in word list
**Symptom:** returns 0 incorrectly.
**Fix:** explicit check at the top: `if end not in word_set: return 0`.

### Tests
```python
def test_lru():
    c = LRUCache(2)
    c.put(1, 1); c.put(2, 2)
    assert c.get(1) == 1
    c.put(3, 3)  # evicts 2
    assert c.get(2) == -1
    c.put(4, 4)  # evicts 1
    assert c.get(1) == -1
    assert c.get(3) == 3
    assert c.get(4) == 4

def test_ladder():
    assert ladder_length("hit", "cog", ["hot","dot","dog","lot","log","cog"]) == 5
    assert ladder_length("hit", "cog", ["hot","dot","dog","lot","log"]) == 0
    assert ladder_length("a", "c", ["a","b","c"]) == 2
```

---

## 5. Mock interview practice (20 min)

This is the full 45-min mock. **Time yourself.**

**Q1 — "Walk me through the LRU Cache approach."**
> Hash map for O(1) lookup; doubly-linked list for O(1) removal. Sentinels head/tail so we don't have null checks on the boundary.

**Q2 — "Why doubly-linked, not singly?"**
> To remove a node, we need to update its prev's next pointer. Singly-linked requires traversing from head, O(n).

**Q3 — "What's the space complexity?"**
> O(capacity) for the cache and the list. Each node is O(1) extra (just two pointers + key + value).

**Q4 — "How do you make it thread-safe?"**
> Add a lock around the list operations. Read-mostly workloads: use a striped lock per bucket.

**Q5 — "Could you implement it with O(1) memory for the LRU pointer?"**
> No. We need to know the LRU, and the LRU is the only thing that changes order. Either we store the order (list, O(n) total) or we use a structure that can answer "what's the LRU?" in O(1) (heap with timestamps, but then update is O(log n)).

**Q6 — "What's Word Ladder's complexity?"**
> O(L · 26 · B) time where B is the BFS frontier size (≤ N), O(N) space. L = word length, N = word list size. BFS guarantees shortest path.

**Q7 — "How would you return ALL shortest paths in Word Ladder?"**
> BFS to find min depth, then DFS with backtracking from end to begin, only using edges that are at min depth. Or BFS building a parent graph, then DFS from end.

---

## 6. Success criteria check
- [ ] I can solve LRU Cache in 20 min.
- [ ] I can explain why doubly-linked is needed.
- [ ] I can name 2 optimizations for Word Ladder.
- [ ] I can describe the 5-step DP framework from memory.

## 7. Grade yourself 0–10
| Area | Score |
|---|---|
| Correctness | /10 |
| Code quality | /10 |
| Debugging | /10 |
| Performance | /10 |
| Testing | /10 |
| Communication | /10 |
| **Total** | **/60** |

## 8. Coding assignment
**LFU Cache** — like LRU, but evict the **least frequently used**. Tiebreak: oldest among least frequent.

### Rubric (0–10)
- 0: doesn't compile
- 4: O(1) get, O(n) put
- 6: O(1) put with hash + freq map
- 8: handles tiebreak correctly
- 10: amortized O(1) with doubly-linked lists per freq

### Solution (sketch)
```python
class LFUCache:
    def __init__(self, capacity):
        self.cap = capacity
        self.cache = {}        # key -> (value, freq)
        self.freq = {}         # freq -> OrderedDict[key -> value]
        self.min_freq = 0
    def get(self, key):
        if key not in self.cache: return -1
        v, f = self.cache[key]
        self._bump(key, f)
        return v
    def put(self, key, value):
        if self.cap == 0: return
        if key in self.cache:
            self.cache[key] = (value, self.cache[key][1])
            self._bump(key, self.cache[key][1])
            return
        if len(self.cache) >= self.cap:
            evict = next(iter(self.freq[self.min_freq]))
            del self.cache[evict]
            del self.freq[self.min_freq][evict]
        self.cache[key] = (value, 1)
        self.freq.setdefault(1, OrderedDict())[key] = value
        self.min_freq = 1
    def _bump(self, key, f):
        del self.freq[f][key]
        if not self.freq[f]:
            del self.freq[f]
            if self.min_freq == f: self.min_freq += 1
        self.freq.setdefault(f + 1, OrderedDict())[key] = self.cache[key][0]
        v, _ = self.cache[key]
        self.cache[key] = (v, f + 1)
```

**Time: 90 min**

---

## Course done

You now have:
- **Days 1–21:** full-stack + testing + debugging
- **Days 22–26:** system design + AI domain
- **Days 27–32:** algorithms + coding interview

For full Meta/Google prep, see `docs/META_GOOGLE_REALITY_CHECK.md` and `docs/ALGORITHMS_PRIMER.md`.
