"""Mock 117 — Senior/Staff mixed: LFU Cache (Hard) with O(1) ops.

Approach: per-frequency doubly-linked lists; a counter of min frequency.
"""

from collections import defaultdict


class _Node:
    __slots__ = ("key", "val", "freq", "prev", "next")

    def __init__(self, key, val):
        self.key = key
        self.val = val
        self.freq = 1
        self.prev = None
        self.next = None


class _DLL:
    """Doubly linked list of nodes; head and tail are sentinels."""

    def __init__(self):
        self.head = _Node(0, 0)
        self.tail = _Node(0, 0)
        self.head.next = self.tail
        self.tail.prev = self.head

    def add_after_head(self, node):
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def remove(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def remove_last(self):
        # Returns the real node just before the tail sentinel.
        if self.head.next is self.tail:
            return None
        node = self.tail.prev
        self.remove(node)
        return node

    def empty(self):
        return self.head.next is self.tail


class LFUCache:
    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self.nodes = {}                    # key -> _Node
        self.freq_lists = defaultdict(_DLL)  # freq -> DLL
        self.min_freq = 1

    def _bump_freq(self, node):
        old_freq = node.freq
        self.freq_lists[old_freq].remove(node)
        if self.freq_lists[old_freq].empty() and old_freq == self.min_freq:
            self.min_freq += 1
        node.freq += 1
        self.freq_lists[node.freq].add_after_head(node)

    def get(self, key):
        if key not in self.nodes:
            return -1
        node = self.nodes[key]
        self._bump_freq(node)
        return node.val

    def put(self, key, value):
        if self.capacity == 0:
            return
        if key in self.nodes:
            node = self.nodes[key]
            node.val = value
            self._bump_freq(node)
            return
        if len(self.nodes) >= self.capacity:
            victim = self.freq_lists[self.min_freq].remove_last()
            if victim is not None:
                del self.nodes[victim.key]
        node = _Node(key, value)
        self.nodes[key] = node
        self.freq_lists[1].add_after_head(node)
        self.min_freq = 1


if __name__ == "__main__":
    cache = LFUCache(2)
    cache.put(1, 1)
    cache.put(2, 2)
    print(cache.get(1))    # 1, freq of 1 is now 2
    cache.put(3, 3)        # evicts key 2 (min_freq=1, LRU)
    print(cache.get(2))    # -1
    print(cache.get(3))    # 3
    print(cache.get(1))    # 1
