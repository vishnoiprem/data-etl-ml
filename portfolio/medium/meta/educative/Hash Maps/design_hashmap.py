"""
Design HashMap - Easy | 15 min

Design a HashMap that supports:
- Constructor: Initialize empty map
- Put(key, value): Insert or update
- Get(key): Return value or -1
- Remove(key): Delete key

Constraints:
- 0 <= key, value <= 10^6
- At most 10^4 calls to put, get, remove
- Cannot use built-in hash table libraries

Example:
    put(1, 1)
    put(2, 2)
    get(1)      -> 1
    get(3)      -> -1
    put(2, 1)
    get(2)      -> 1
    remove(2)
    get(2)      -> -1
"""

from bucket import Bucket


# =============================================================================
# WAY 1: Basic with Bucket class (Chaining)
# =============================================================================
# THINKING: "HashMap = array of buckets. Each bucket handles collisions via list."
def hashmap_1():
    class DesignHashMap:
        def __init__(self):
            self.size = 1000
            self.buckets = [Bucket() for _ in range(self.size)]

        def _hash(self, key):
            return key % self.size

        def put(self, key, value):
            self.buckets[self._hash(key)].update(key, value)

        def get(self, key):
            i, v = self.buckets[self._hash(key)].get(key)
            return v if i != -1 else -1

        def remove(self, key):
            self.buckets[self._hash(key)].remove(key)
    return DesignHashMap


# =============================================================================
# WAY 2: Inline buckets (no separate class)
# =============================================================================
# THINKING: "Don't need separate class - just use list of lists."
def hashmap_2():
    class DesignHashMap:
        def __init__(self):
            self.size = 1000
            self.data = [[] for _ in range(self.size)]

        def put(self, key, value):
            bucket = self.data[key % self.size]
            for i, (k, v) in enumerate(bucket):
                if k == key:
                    bucket[i] = (key, value)
                    return
            bucket.append((key, value))

        def get(self, key):
            for k, v in self.data[key % self.size]:
                if k == key:
                    return v
            return -1

        def remove(self, key):
            bucket = self.data[key % self.size]
            for i, (k, v) in enumerate(bucket):
                if k == key:
                    bucket.pop(i)
                    return
    return DesignHashMap


# =============================================================================
# WAY 3: Using dict of lists (Python style)
# =============================================================================
# THINKING: "Use Python dict as outer structure, but for hashing logic."
def hashmap_3():
    class DesignHashMap:
        def __init__(self):
            self.size = 1000
            self.data = [[] for _ in range(self.size)]

        def _hash(self, key):
            return key % self.size

        def put(self, key, value):
            bucket = self.data[self._hash(key)]
            for pair in bucket:
                if pair[0] == key:
                    pair[1] = value
                    return
            bucket.append([key, value])

        def get(self, key):
            for pair in self.data[self._hash(key)]:
                if pair[0] == key:
                    return pair[1]
            return -1

        def remove(self, key):
            bucket = self.data[self._hash(key)]
            for i, pair in enumerate(bucket):
                if pair[0] == key:
                    del bucket[i]
                    return
    return DesignHashMap


# =============================================================================
# WAY 4: Using Linked List Nodes (Real HashMap)
# =============================================================================
# THINKING: "Real HashMaps use linked lists inside buckets, not Python lists."
class Node:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None


def hashmap_4():
    class DesignHashMap:
        def __init__(self):
            self.size = 1000
            self.buckets = [None] * self.size

        def put(self, key, value):
            idx = key % self.size
            if not self.buckets[idx]:
                self.buckets[idx] = Node(key, value)
            else:
                curr = self.buckets[idx]
                while curr:
                    if curr.key == key:
                        curr.value = value
                        return
                    if not curr.next:
                        break
                    curr = curr.next
                curr.next = Node(key, value)

        def get(self, key):
            curr = self.buckets[key % self.size]
            while curr:
                if curr.key == key:
                    return curr.value
                curr = curr.next
            return -1

        def remove(self, key):
            idx = key % self.size
            curr = self.buckets[idx]
            if not curr:
                return
            if curr.key == key:
                self.buckets[idx] = curr.next
            else:
                while curr.next:
                    if curr.next.key == key:
                        curr.next = curr.next.next
                        return
                    curr = curr.next
    return DesignHashMap


# =============================================================================
# WAY 5: Using Dictionary of tuples (compact)
# =============================================================================
def hashmap_5():
    class DesignHashMap:
        def __init__(self):
            self.data = {}

        def put(self, key, value):
            self.data[key] = value

        def get(self, key):
            return self.data.get(key, -1)

        def remove(self, key):
            if key in self.data:
                del self.data[key]
    return DesignHashMap
# NOTE: This uses dict - violates the "no built-in" rule, but works


# =============================================================================
# WAY 6: Larger bucket size (fewer collisions)
# =============================================================================
def hashmap_6():
    class DesignHashMap:
        def __init__(self):
            self.size = 10000
            self.data = [[] for _ in range(self.size)]

        def put(self, key, value):
            bucket = self.data[key % self.size]
            for i, (k, v) in enumerate(bucket):
                if k == key:
                    bucket[i] = (key, value)
                    return
            bucket.append((key, value))

        def get(self, key):
            for k, v in self.data[key % self.size]:
                if k == key:
                    return v
            return -1

        def remove(self, key):
            bucket = self.data[key % self.size]
            for i, (k, v) in enumerate(bucket):
                if k == key:
                    bucket.pop(i)
                    return
    return DesignHashMap


# =============================================================================
# WAY 7: Prime size (better distribution)
# =============================================================================
def hashmap_7():
    class DesignHashMap:
        def __init__(self):
            self.size = 1009  # prime number
            self.data = [[] for _ in range(self.size)]

        def put(self, key, value):
            bucket = self.data[key % self.size]
            for i, (k, v) in enumerate(bucket):
                if k == key:
                    bucket[i] = (key, value)
                    return
            bucket.append((key, value))

        def get(self, key):
            for k, v in self.data[key % self.size]:
                if k == key:
                    return v
            return -1

        def remove(self, key):
            bucket = self.data[key % self.size]
            for i, (k, v) in enumerate(bucket):
                if k == key:
                    bucket.pop(i)
                    return
    return DesignHashMap


# =============================================================================
# WAY 8: Dict of dicts (Pythonic but violates rule)
# =============================================================================
def hashmap_8():
    class DesignHashMap:
        def __init__(self):
            self.data = {}

        def put(self, key, value):
            self.data[key] = value

        def get(self, key):
            try:
                return self.data[key]
            except KeyError:
                return -1

        def remove(self, key):
            self.data.pop(key, None)
    return DesignHashMap


# =============================================================================
# WAY 9: With hash function helper
# =============================================================================
def hashmap_9():
    class DesignHashMap:
        def __init__(self):
            self.size = 1000
            self.buckets = [None] * self.size

        def _hash(self, key):
            return key % self.size

        def _find(self, key, idx):
            """Find node with key in bucket at idx."""
            curr = self.buckets[idx]
            prev = None
            while curr:
                if curr.key == key:
                    return curr, prev
                prev = curr
                curr = curr.next
            return None, prev

        def put(self, key, value):
            idx = self._hash(key)
            node, _ = self._find(key, idx)
            if node:
                node.value = value
            else:
                self.buckets[idx] = Node(key, value)

        def get(self, key):
            node, _ = self._find(key, self._hash(key))
            return node.value if node else -1

        def remove(self, key):
            idx = self._hash(key)
            node, prev = self._find(key, idx)
            if node:
                if prev:
                    prev.next = node.next
                else:
                    self.buckets[idx] = node.next
    return DesignHashMap


# =============================================================================
# WAY 10: Compact one-liner style
# =============================================================================
def hashmap_10():
    class DesignHashMap:
        def __init__(self):
            self.s = 1000
            self.d = [[] for _ in range(self.s)]

        def put(self, k, v):
            b = self.d[k % self.s]
            for i, p in enumerate(b):
                if p[0] == k:
                    b[i] = (k, v)
                    return
            b.append((k, v))

        def get(self, k):
            for p in self.d[k % self.s]:
                if p[0] == k:
                    return p[1]
            return -1

        def remove(self, k):
            b = self.d[k % self.s]
            for i, p in enumerate(b):
                if p[0] == k:
                    del b[i]
                    return
    return DesignHashMap


# =============================================================================
# WAY 11-15: More variations
# =============================================================================

# WAY 11: With separate Bucket class (different style)
class Bucket2:
    def __init__(self):
        self.head = None

    def add(self, key, value):
        if not self.head:
            self.head = Node(key, value)
            return
        curr = self.head
        while curr.next:
            if curr.key == key:
                curr.value = value
                return
            curr = curr.next
        if curr.key == key:
            curr.value = value
        else:
            curr.next = Node(key, value)

    def find(self, key):
        prev = None
        curr = self.head
        while curr:
            if curr.key == key:
                return curr, prev
            prev = curr
            curr = curr.next
        return None, None

    def delete(self, key):
        node, prev = self.find(key)
        if node:
            if prev:
                prev.next = node.next
            else:
                self.head = node.next


def hashmap_11():
    class DesignHashMap:
        def __init__(self):
            self.size = 1000
            self.buckets = [Bucket2() for _ in range(self.size)]

        def put(self, key, value):
            self.buckets[key % self.size].add(key, value)

        def get(self, key):
            node, _ = self.buckets[key % self.size].find(key)
            return node.value if node else -1

        def remove(self, key):
            self.buckets[key % self.size].delete(key)
    return DesignHashMap


# WAY 12: Using array of None initially
def hashmap_12():
    class DesignHashMap:
        def __init__(self):
            self.s = 1000
            self.a = [None] * self.s

        def put(self, k, v):
            i = k % self.s
            if self.a[i] is None:
                self.a[i] = []
            for j, p in enumerate(self.a[i]):
                if p[0] == k:
                    self.a[i][j] = (k, v)
                    return
            self.a[i].append((k, v))

        def get(self, k):
            if self.a[k % self.s] is None:
                return -1
            for p in self.a[k % self.s]:
                if p[0] == k:
                    return p[1]
            return -1

        def remove(self, k):
            if self.a[k % self.s] is None:
                return
            self.a[k % self.s] = [p for p in self.a[k % self.s] if p[0] != k]
    return DesignHashMap


# WAY 13: Compact with setdefault
def hashmap_13():
    class DesignHashMap:
        def __init__(self):
            self.s = 1000
            self.d = {}

        def put(self, k, v):
            self.d[k] = v

        def get(self, k):
            return self.d.get(k, -1)

        def remove(self, k):
            self.d.pop(k, None)
    return DesignHashMap


# WAY 14: With custom hash (multiplication method)
def hashmap_14():
    class DesignHashMap:
        def __init__(self):
            self.s = 1000
            self.d = [[] for _ in range(self.s)]

        def _hash(self, key):
            # Multiplication method (better distribution)
            A = 0.6180339887
            return int(self.s * ((key * A) % 1))

        def put(self, k, v):
            b = self.d[self._hash(k)]
            for i, p in enumerate(b):
                if p[0] == k:
                    b[i] = (k, v)
                    return
            b.append((k, v))

        def get(self, k):
            for p in self.d[self._hash(k)]:
                if p[0] == k:
                    return p[1]
            return -1

        def remove(self, k):
            b = self.d[self._hash(k)]
            for i, p in enumerate(b):
                if p[0] == k:
                    del b[i]
                    return
    return DesignHashMap


# WAY 15: Using collections.defaultdict (violates rule but works)
def hashmap_15():
    from collections import defaultdict
    class DesignHashMap:
        def __init__(self):
            self.d = defaultdict(lambda: -1)

        def put(self, k, v):
            self.d[k] = v

        def get(self, k):
            return self.d[k]

        def remove(self, k):
            if k in self.d:
                del self.d[k]
    return DesignHashMap


# WAY 16-20: Edge cases and variations

# WAY 16: With load factor and resizing
def hashmap_16():
    class DesignHashMap:
        def __init__(self):
            self.size = 16
            self.count = 0
            self.buckets = [[] for _ in range(self.size)]

        def _resize(self):
            old_buckets = self.buckets
            self.size *= 2
            self.buckets = [[] for _ in range(self.size)]
            self.count = 0
            for bucket in old_buckets:
                for k, v in bucket:
                    self.put(k, v)

        def put(self, k, v):
            if self.count / self.size > 0.75:
                self._resize()
            bucket = self.buckets[k % self.size]
            for i, p in enumerate(bucket):
                if p[0] == k:
                    bucket[i] = (k, v)
                    return
            bucket.append((k, v))
            self.count += 1

        def get(self, k):
            for p in self.buckets[k % self.size]:
                if p[0] == k:
                    return p[1]
            return -1

        def remove(self, k):
            bucket = self.buckets[k % self.size]
            for i, p in enumerate(bucket):
                if p[0] == k:
                    del bucket[i]
                    self.count -= 1
                    return
    return DesignHashMap


# WAY 17: Using arrays of arrays
def hashmap_17():
    class DesignHashMap:
        def __init__(self):
            self.s = 1000
            self.keys = [[] for _ in range(self.s)]
            self.vals = [[] for _ in range(self.s)]

        def put(self, k, v):
            i = k % self.s
            if k in self.keys[i]:
                idx = self.keys[i].index(k)
                self.vals[i][idx] = v
            else:
                self.keys[i].append(k)
                self.vals[i].append(v)

        def get(self, k):
            i = k % self.s
            if k in self.keys[i]:
                return self.vals[i][self.keys[i].index(k)]
            return -1

        def remove(self, k):
            i = k % self.s
            if k in self.keys[i]:
                idx = self.keys[i].index(k)
                del self.keys[i][idx]
                del self.vals[i][idx]
    return DesignHashMap


# WAY 18: Using tuple storage
def hashmap_18():
    class DesignHashMap:
        def __init__(self):
            self.s = 1000
            self.d = [{} for _ in range(self.s)]

        def put(self, k, v):
            self.d[k % self.s][k] = v

        def get(self, k):
            return self.d[k % self.s].get(k, -1)

        def remove(self, k):
            self.d[k % self.s].pop(k, None)
    return DesignHashMap


# WAY 19: Using sets
def hashmap_19():
    class DesignHashMap:
        def __init__(self):
            self.s = 1000
            self.keys = [[] for _ in range(self.s)]
            self.vals = [[] for _ in range(self.s)]

        def put(self, k, v):
            i = k % self.s
            for j in range(len(self.keys[i])):
                if self.keys[i][j] == k:
                    self.vals[i][j] = v
                    return
            self.keys[i].append(k)
            self.vals[i].append(v)

        def get(self, k):
            i = k % self.s
            for j in range(len(self.keys[i])):
                if self.keys[i][j] == k:
                    return self.vals[i][j]
            return -1

        def remove(self, k):
            i = k % self.s
            for j in range(len(self.keys[i])):
                if self.keys[i][j] == k:
                    del self.keys[i][j]
                    del self.vals[i][j]
                    return
    return DesignHashMap


# WAY 20: Most compact one-liner style
def hashmap_20():
    class DesignHashMap:
        def __init__(self):
            self.d = [None] * 1000

        def put(self, k, v):
            i, b = k % 1000, self.d[i] if self.d[k % 1000] else (self.d.__setitem__(k % 1000, []), self.d[k % 1000])[1]
            for j, p in enumerate(b):
                if p[0] == k: b[j] = (k, v); return
            b.append((k, v))

        def get(self, k):
            b = self.d[k % 1000]
            return next((v for p, v in b if p == k), -1) if b else -1

        def remove(self, k):
            b = self.d[k % 1000]
            if b: self.d[k % 1000] = [p for p in b if p[0] != k]
    return DesignHashMap


# =============================================================================
# HOW I THINK - THE COMPLETE FRAMEWORK
# =============================================================================

HOW_TO_THINK = """
THE THINKING PROCESS FOR THIS PROBLEM:

Step 1: "What does a HashMap do?"
        -> Stores key-value pairs with O(1) lookup
        -> Uses hash function to find bucket

Step 2: "What's the trick?"
        -> Array of buckets + hash function = fast lookup
        -> Chaining handles collisions (multiple keys in one bucket)

Step 3: "What are the design choices?"
        a) Bucket size: 1000 or prime (1009)
        b) Collision handling: chaining (list) vs open addressing
        c) Hash function: simple modulo or multiplication
        d) Storage per bucket: list of pairs or linked list

Step 4: "How do real HashMaps work?"
        -> Hash the key -> bucket index -> search bucket
        -> If collision: chain (linked list) or probe (open addressing)

Step 5: "Optimizations?"
        -> Prime bucket size (better distribution)
        -> Load factor + resizing (when too many collisions)
        -> Better hash function (multiplication method)

DECISION TREE:
+------------------+------------------+----------+
| Storage          | Bucket           | Best     |
+------------------+------------------+----------+
| List of tuples   | List             | Simple   |
| List of lists    | Mutable lists    | Pythonic |
| Linked list      | Node objects     | Real     |
| Dict per bucket  | Python dict      | Fast     |
+------------------+------------------+----------+
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Bucket class", hashmap_1()),
        ("Way 2: Inline buckets", hashmap_2()),
        ("Way 3: Hash helper", hashmap_3()),
        ("Way 4: Linked list nodes", hashmap_4()),
        ("Way 5: Dict of tuples", hashmap_5()),
        ("Way 6: Larger size", hashmap_6()),
        ("Way 7: Prime size", hashmap_7()),
        ("Way 8: Try/except dict", hashmap_8()),
        ("Way 9: _find helper", hashmap_9()),
        ("Way 10: Compact", hashmap_10()),
        ("Way 11: Bucket2 class", hashmap_11()),
        ("Way 12: Lazy init", hashmap_12()),
        ("Way 13: defaultdict", hashmap_13()),
        ("Way 14: Multiplication hash", hashmap_14()),
        ("Way 15: defaultdict2", hashmap_15()),
        ("Way 16: With resizing", hashmap_16()),
        ("Way 17: Separate key/val", hashmap_17()),
        ("Way 18: Dict per bucket", hashmap_18()),
        ("Way 19: Manual search", hashmap_19()),
        ("Way 20: One-liner", hashmap_20()),
    ]

    print("=" * 70)
    print("DESIGN HASHMAP - ALL 20 IMPLEMENTATIONS")
    print("=" * 70)

    for name, HashMapClass in implementations:
        h = HashMapClass()
        h.put(1, 1)
        h.put(2, 2)
        g1 = h.get(1)
        g3 = h.get(3)
        h.put(2, 1)
        g2 = h.get(2)
        h.remove(2)
        g2_after = h.get(2)

        passed = (g1 == 1 and g3 == -1 and g2 == 1 and g2_after == -1)
        status = "✓" if passed else "✗"
        print(f"{status} {name}: get(1)={g1}, get(3)={g3}, get(2)={g2}, get(2)_after_remove={g2_after}")

    print("\n" + "=" * 70)
    print(HOW_TO_THINK)
    print("=" * 70)
