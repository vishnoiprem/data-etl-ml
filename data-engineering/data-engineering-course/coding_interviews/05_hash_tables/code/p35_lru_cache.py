"""LRU Cache — get/put in O(1) using an OrderedDict.

Time:  O(1) per get/put
Space: O(capacity)
"""

from collections import OrderedDict


class LRUCache:
    """A least-recently-used cache backed by an OrderedDict."""

    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self.store = OrderedDict()

    def get(self, key):
        """Return the value or -1; marks the key as recently used."""
        if key not in self.store:
            return -1
        # move_to_end makes this the most-recently-used entry.
        self.store.move_to_end(key)
        return self.store[key]

    def put(self, key, value):
        """Insert or update ``key``; evict the LRU entry if over capacity."""
        if key in self.store:
            self.store.move_to_end(key)
        self.store[key] = value
        if len(self.store) > self.capacity:
            self.store.popitem(last=False)


def solve_lru_cache(operations):
    """Run a list of operations and return the outputs.

    Operations are tuples: ("LRUCache", capacity), ("put", k, v), ("get", k).
    Returns a list of get-result integers (in order). The constructor
    returns nothing.
    """
    results = []
    cache = None
    for op in operations:
        if op[0] == "LRUCache":
            cache = LRUCache(op[1])
        elif op[0] == "get":
            results.append(cache.get(op[1]))
        elif op[0] == "put":
            cache.put(op[1], op[2])
    return results


if __name__ == "__main__":
    ops = [
        ("LRUCache", 2),
        ("put", 1, 1),
        ("put", 2, 2),
        ("get", 1),     # 1
        ("put", 3, 3),  # evicts key 2
        ("get", 2),     # -1
    ]
    print(solve_lru_cache(ops))
