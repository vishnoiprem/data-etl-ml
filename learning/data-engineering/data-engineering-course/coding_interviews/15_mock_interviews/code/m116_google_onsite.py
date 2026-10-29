"""Mock 116 — L6 Google onsite: random pick with weight, O(log n) per pick."""

import bisect
import random


class WeightedRandom:
    """Pick indices with probability proportional to weight."""

    def __init__(self, weights):
        self.prefix = []
        running = 0
        for w in weights:
            if w < 0:
                raise ValueError("weights must be non-negative")
            running += w
            self.prefix.append(running)
        self.total = running
        if self.total <= 0:
            raise ValueError("at least one weight must be positive")

    def pick(self):
        # Pick a random point in [1, total] and find the smallest prefix >= it.
        target = random.randint(1, self.total)
        return bisect.bisect_left(self.prefix, target)


if __name__ == "__main__":
    picker = WeightedRandom([1, 3])
    counts = [0, 0]
    for _ in range(10000):
        counts[picker.pick()] += 1
    print(counts)  # ~ [2500, 7500]
