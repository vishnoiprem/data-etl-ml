"""
Dot Product of Two Sparse Vectors
Medium | 30 min

Create a SparseVector class that:
- Constructor: Initializes the object with the vector
- dotProduct(vec): Computes dot product with another sparse vector

A sparse vector contains mostly zeros. We should store only non-zero entries.

Constraints:
- n == nums1.length == nums2.length
- 1 <= n <= 10^3
- 0 <= nums1[i], nums2[i] <= 100

Example:
    v1 = SparseVector([1, 0, 0, 2, 3])
    v2 = SparseVector([0, 3, 0, 4, 0])
    v1.dotProduct(v2) = 1*0 + 0*3 + 0*0 + 2*4 + 3*0 = 8
"""

from collections import Counter, defaultdict
from itertools import zip_longest
import numpy as np


# =============================================================================
# WAY 1: Basic HashMap
# =============================================================================
# THINKING: "Store non-zero values in a dict. Dot product = iterate over
# smaller dict, look up in larger."
class SparseVector1:
    def __init__(self, nums):
        self.data = {}
        for i, v in enumerate(nums):
            if v != 0:
                self.data[i] = v

    def dot_product(self, vec):
        result = 0
        for i, v in self.data.items():
            if i in vec.data:
                result += v * vec.data[i]
        return result


# =============================================================================
# WAY 2: Using dict comprehension
# =============================================================================
class SparseVector2:
    def __init__(self, nums):
        self.data = {i: v for i, v in enumerate(nums) if v != 0}

    def dot_product(self, vec):
        return sum(self.data[i] * vec.data.get(i, 0) for i in self.data)


# =============================================================================
# WAY 3: List of tuples
# =============================================================================
class SparseVector3:
    def __init__(self, nums):
        self.data = [(i, v) for i, v in enumerate(nums) if v != 0]

    def dot_product(self, vec):
        vec_map = dict(vec.data)
        result = 0
        for i, v in self.data:
            if i in vec_map:
                result += v * vec_map[i]
        return result


# =============================================================================
# WAY 4: List of (index, value) pairs
# =============================================================================
class SparseVector4:
    def __init__(self, nums):
        self.pairs = [(i, nums[i]) for i in range(len(nums)) if nums[i] != 0]

    def dot_product(self, vec):
        vec_dict = dict(vec.pairs)
        return sum(v * vec_dict[i] for i, v in self.pairs if i in vec_dict)


# =============================================================================
# WAY 5: Two Pointers (Optimal for Two Sparse Vectors!)
# =============================================================================
# THINKING: "If both vectors are sparse, two pointers over sorted indices is faster."
class SparseVector5:
    def __init__(self, nums):
        self.pairs = [(i, v) for i, v in enumerate(nums) if v != 0]

    def dot_product(self, vec):
        i, j = 0, 0
        result = 0
        while i < len(self.pairs) and j < len(vec.pairs):
            if self.pairs[i][0] == vec.pairs[j][0]:
                result += self.pairs[i][1] * vec.pairs[j][1]
                i += 1
                j += 1
            elif self.pairs[i][0] < vec.pairs[j][0]:
                i += 1
            else:
                j += 1
        return result


# =============================================================================
# WAY 6: Using Counter
# =============================================================================
class SparseVector6:
    def __init__(self, nums):
        self.data = Counter({i: v for i, v in enumerate(nums) if v != 0})

    def dot_product(self, vec):
        return sum(self.data[i] * vec.data[i] for i in self.data.keys() & vec.data.keys())


# =============================================================================
# WAY 7: defaultdict
# =============================================================================
class SparseVector7:
    def __init__(self, nums):
        self.data = defaultdict(int, {i: v for i, v in enumerate(nums) if v != 0})

    def dot_product(self, vec):
        result = 0
        for i in self.data:
            result += self.data[i] * vec.data.get(i, 0)
        return result


# =============================================================================
# WAY 8: One-Liner Constructor
# =============================================================================
class SparseVector8:
    def __init__(self, nums):
        self.data = {i: v for i, v in enumerate(nums) if v}

    def dot_product(self, vec):
        return sum(a * vec.data[i] for i, a in self.data.items() if i in vec.data)


# =============================================================================
# WAY 9: Using enumerate and filter
# =============================================================================
class SparseVector9:
    def __init__(self, nums):
        self.data = dict(filter(lambda x: x[1] != 0, enumerate(nums)))

    def dot_product(self, vec):
        return sum(v * vec.data.get(k, 0) for k, v in self.data.items())


# =============================================================================
# WAY 10: With set intersection
# =============================================================================
class SparseVector10:
    def __init__(self, nums):
        self.data = {i: nums[i] for i in range(len(nums)) if nums[i] != 0}

    def dot_product(self, vec):
        common = set(self.data.keys()) & set(vec.data.keys())
        return sum(self.data[k] * vec.data[k] for k in common)


# =============================================================================
# WAY 11: Compact with zip and set
# =============================================================================
class SparseVector11:
    def __init__(self, nums):
        self.data = {i: v for i, v in enumerate(nums) if v != 0}

    def dot_product(self, vec):
        return sum(self.data[k] * vec.data[k] for k in self.data.keys() & vec.data.keys())


# =============================================================================
# WAY 12: Generator with yield
# =============================================================================
class SparseVector12:
    def __init__(self, nums):
        self.data = {i: nums[i] for i in range(len(nums)) if nums[i] != 0}

    def dot_product(self, vec):
        return sum(self.data[i] * vec.data[i] for i in self.data if i in vec.data)


# =============================================================================
# WAY 13: Using dict.get and sum
# =============================================================================
class SparseVector13:
    def __init__(self, nums):
        self.data = {i: v for i, v in enumerate(nums) if v}

    def dot_product(self, vec):
        return sum(v * vec.data.get(i, 0) for i, v in self.data.items())


# =============================================================================
# WAY 14: Loop-based with explicit check
# =============================================================================
class SparseVector14:
    def __init__(self, nums):
        self.data = {}
        for i, v in enumerate(nums):
            if v:
                self.data[i] = v

    def dot_product(self, vec):
        result = 0
        for i in self.data:
            if i in vec.data:
                result += self.data[i] * vec.data[i]
        return result


# =============================================================================
# WAY 15: Two pointers optimized (sorted dict)
# =============================================================================
class SparseVector15:
    def __init__(self, nums):
        self.pairs = sorted([(i, v) for i, v in enumerate(nums) if v != 0])

    def dot_product(self, vec):
        i, j, result = 0, 0, 0
        while i < len(self.pairs) and j < len(vec.pairs):
            if self.pairs[i][0] == vec.pairs[j][0]:
                result += self.pairs[i][1] * vec.pairs[j][1]
                i += 1
                j += 1
            elif self.pairs[i][0] < vec.pairs[j][0]:
                i += 1
            else:
                j += 1
        return result


# =============================================================================
# WAY 16: Using numpy
# =============================================================================
class SparseVector16:
    def __init__(self, nums):
        self.data = {i: v for i, v in enumerate(nums) if v}

    def dot_product(self, vec):
        max_idx = max(max(self.data.keys(), default=0), max(vec.data.keys(), default=0)) + 1
        a = np.array([self.data.get(i, 0) for i in range(max_idx)])
        b = np.array([vec.data.get(i, 0) for i in range(max_idx)])
        return int(a @ b)


# =============================================================================
# WAY 17: Most compact (Pythonic)
# =============================================================================
class SparseVector17:
    def __init__(self, nums):
        self.data = {i: x for i, x in enumerate(nums) if x}

    def dot_product(self, vec):
        return sum(a * vec.data[i] for i, a in self.data.items() if i in vec.data)


# =============================================================================
# WAY 18: With lambda
# =============================================================================
class SparseVector18:
    def __init__(self, nums):
        self.data = dict(filter(lambda kv: kv[1] != 0, enumerate(nums)))

    def dot_product(self, vec):
        return sum(map(lambda kv: kv[1] * vec.data.get(kv[0], 0), self.data.items()))


# =============================================================================
# WAY 19: Two pointers with explicit unpacking
# =============================================================================
class SparseVector19:
    def __init__(self, nums):
        self.pairs = [(i, v) for i, v in enumerate(nums) if v != 0]

    def dot_product(self, vec):
        result = 0
        i = j = 0
        while i < len(self.pairs) and j < len(vec.pairs):
            a_idx, a_val = self.pairs[i]
            b_idx, b_val = vec.pairs[j]
            if a_idx == b_idx:
                result += a_val * b_val
                i += 1
                j += 1
            elif a_idx < b_idx:
                i += 1
            else:
                j += 1
        return result


# =============================================================================
# WAY 20: Single-line constructor
# =============================================================================
class SparseVector20:
    def __init__(self, nums):
        self.d = dict((i, v) for i, v in enumerate(nums) if v)

    def dot_product(self, vec):
        return sum(v * vec.d.get(i, 0) for i, v in self.d.items())


# =============================================================================
# HOW I THINK - SAYING ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"A sparse vector has mostly zeros. So instead of storing all n elements,
I should store only the non-zero positions and values. That way, the
constructor is O(n) but uses O(k) space where k is non-zero count."

Approach 1 (HashMap):
"For dot product, I just iterate through one vector's non-zero entries
and look them up in the other. This is O(k) which is much better than O(n)
when the vector is truly sparse."

Approach 2 (Two Pointers):
"Alternative: if both vectors are sparse, I can use two pointers over their
sorted indices. This gives O(k1 + k2) without hashmap overhead."

Edge cases to mention:
"What if both vectors are completely zero? Result is 0.
What if they have no overlapping indices? Result is 0.
What about negative numbers? My algorithm handles them naturally."

DECISION TREE:
+------------------+-------------+--------------+
| Vector           | Best        | Why          |
+------------------+-------------+--------------+
| Both sparse      | Two pointers| No hashmap   |
| One dense        | HashMap     | O(k) lookup  |
| Many dot products| HashMap     | Build once   |
+------------------+-------------+--------------+

COMPLEXITY:
+-----------+--------+----------+
| Approach  | Time   | Space    |
+-----------+--------+----------+
| Brute     | O(n)   | O(n)     |
| HashMap   | O(k)   | O(k)     |
| 2 ptrs    | O(k1+k2)| O(k1+k2)|
+-----------+--------+----------+
where n = length, k = non-zero count
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Basic HashMap", SparseVector1),
        ("Way 2: Dict comp", SparseVector2),
        ("Way 3: List of tuples", SparseVector3),
        ("Way 4: List pairs", SparseVector4),
        ("Way 5: Two pointers", SparseVector5),
        ("Way 6: Counter", SparseVector6),
        ("Way 7: defaultdict", SparseVector7),
        ("Way 8: One-liner", SparseVector8),
        ("Way 9: Filter", SparseVector9),
        ("Way 10: Set intersection", SparseVector10),
        ("Way 11: Compact set", SparseVector11),
        ("Way 12: Generator", SparseVector12),
        ("Way 13: dict.get", SparseVector13),
        ("Way 14: Loop explicit", SparseVector14),
        ("Way 15: Two ptr sorted", SparseVector15),
        ("Way 16: numpy", SparseVector16),
        ("Way 17: Most compact", SparseVector17),
        ("Way 18: Lambda", SparseVector18),
        ("Way 19: 2 ptr unpack", SparseVector19),
        ("Way 20: Single line", SparseVector20),
    ]

    test_cases = [
        ([1, 0, 0, 2, 3], [0, 3, 0, 4, 0], 8),
        ([0, 0, 0], [1, 2, 3], 0),
        ([1, 2, 3], [4, 5, 6], 32),
        ([0, 1, 0, 1], [1, 0, 1, 0], 0),
        ([5, 0, 0, 0, 5], [5, 0, 0, 0, 5], 50),
    ]

    print("=" * 70)
    print("DOT PRODUCT OF TWO SPARSE VECTORS - ALL 20 IMPLEMENTATIONS")
    print("=" * 70)

    all_pass = True
    for name, SV in implementations:
        all_test_pass = True
        for nums1, nums2, expected in test_cases:
            try:
                v1 = SV(nums1)
                v2 = SV(nums2)
                result = v1.dot_product(v2)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  ✗ {name}: {nums1} · {nums2} = {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  ✗ {name}: ERROR - {e}")
        status = "✓ PASS" if all_test_pass else "✗ FAIL"
        print(f"{status} - {name}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS! 🎉")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
