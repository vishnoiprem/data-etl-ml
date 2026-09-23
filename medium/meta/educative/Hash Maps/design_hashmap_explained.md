# Design HashMap - 20 Solutions with How to Think

## The Problem
Build a HashMap from scratch (no built-in libraries):
- `put(key, value)` - insert or update
- `get(key)` - return value or -1
- `remove(key)` - delete key

---

## How I Think (The Mental Process)

### Step 1: "What does a HashMap do?"
> "Stores key-value pairs with O(1) lookup. Uses a hash function to find the bucket."

### Step 2: "What's the trick?"
> "Array of buckets + hash function = fast lookup. Chaining handles collisions."

### Step 3: "Design choices?"
| Choice | Options |
|--------|---------|
| Bucket size | 1000 / prime (1009) |
| Collision handling | chaining (list) vs open addressing |
| Hash function | modulo or multiplication |
| Storage | list of pairs / linked list |

### Step 4: "How do real HashMaps work?"
```
1. Hash the key: bucket_index = hash(key) % size
2. Go to that bucket
3. If collision: chain (linked list of pairs)
4. Search chain for the key
```

### Step 5: "Optimizations?"
- Prime bucket size (better distribution)
- Load factor + resizing
- Better hash function (multiplication)

---

## The 20 Implementations

### Way 1: Basic with Bucket class
```python
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
```

### Way 2: Inline buckets (no separate class)
```python
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
```

### Way 3: With hash helper
Same logic, extracted `_hash` method.

### Way 4: Real Linked List Nodes
```python
class Node:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None

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
```

### Way 5-15: Variants
- Way 5: dict of tuples
- Way 6: larger size (10000)
- Way 7: prime size (1009)
- Way 8: try/except
- Way 9: `_find` helper method
- Way 10: compact style
- Way 11: Bucket2 class with linked list
- Way 12: lazy initialization
- Way 13: defaultdict
- Way 14: multiplication hash function
- Way 15: defaultdict alternative

### Way 16: With Load Factor + Resizing
```python
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
```

### Way 17-20: More variations
- Way 17: separate key/value arrays
- Way 18: dict per bucket
- Way 19: manual search with index
- Way 20: ultra-compact one-liner style

---

## Decision Tree

```
+------------------+------------------+----------+
| Storage          | Bucket           | Best For |
+------------------+------------------+----------+
| List of tuples   | List             | Simple   |
| List of lists    | Mutable lists    | Pythonic |
| Linked list      | Node objects     | Real impl|
| Dict per bucket  | Python dict      | Fast     |
+------------------+------------------+----------+
```

## Complexity

| Operation | Average | Worst |
|-----------|---------|-------|
| put | O(1) | O(n) |
| get | O(1) | O(n) |
| remove | O(1) | O(n) |

Worst case: all keys hash to same bucket.

## Key Concepts to Remember

1. **Hash function**: key % size
2. **Bucket array**: stores the chains
3. **Chaining**: handle collisions with lists
4. **Prime size**: better distribution
5. **Load factor**: when to resize

## Best Answer to Use

**Simple version (interview default):**
```python
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
```

**Impressive version (with linked list):**
Shows you know real HashMap internals.
