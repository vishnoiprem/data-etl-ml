"""
Split Linked List in Parts - 10 Ways
https://www.educative.io/courses/grokking-coding-interview-in-python/split-linked-list-in-parts

Given the head of a singly linked list and an integer k, split the list into
k consecutive parts. The sizes of parts differ by at most 1; earlier parts
are larger.

KEY INSIGHT:
Find length n. Each part has size = n // k or n // k + 1 (the first
(n % k) parts have +1). Walk and split accordingly.

Examples:
    1->2->3, k=5  =>  [[1],[2],[3],[],[]]

Constraints:
- 0 <= number of nodes <= 1000
- 1 <= k <= 50
"""

import copy
import sys

sys.setrecursionlimit(100000)


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def list_from_array(arr):
    if not arr:
        return None
    head = ListNode(arr[0])
    cur = head
    for v in arr[1:]:
        cur.next = ListNode(v)
        cur = cur.next
    return head


def list_to_array(head):
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


def list_to_nested_array(heads):
    return [list_to_array(h) if h else [] for h in heads]


def nested_equal(a, b):
    if len(a) != len(b):
        return False
    return all(a[i] == b[i] for i in range(len(a)))


# ============================================================
# Way 1: Count + walk + split (BEST - Memorize!)
# ============================================================
def split_list_to_parts_1(head, k):
    """Count length; first (n%k) parts have size+1; split."""
    # Count length
    n = 0
    cur = head
    while cur:
        n += 1
        cur = cur.next
    base_size = n // k
    extra = n % k
    out = []
    cur = head
    for i in range(k):
        part_size = base_size + (1 if i < extra else 0)
        if part_size == 0:
            out.append(None)
            continue
        # Walk part_size nodes from cur; the part_size-th is the last
        part_head = cur
        for _ in range(part_size - 1):
            cur = cur.next
        nxt = cur.next
        cur.next = None
        out.append(part_head)
        cur = nxt
    return out


# ============================================================
# Way 2: Walk with running part index
# ============================================================
def split_list_to_parts_2(head, k):
    """Walk and increment part index based on target sizes."""
    n = 0
    cur = head
    while cur:
        n += 1
        cur = cur.next
    base_size = n // k
    extra = n % k
    out = []
    cur = head
    for i in range(k):
        if not cur:
            out.append(None)
            continue
        part_head = cur
        target_size = base_size + (1 if i < extra else 0)
        for _ in range(target_size - 1):
            cur = cur.next
        nxt = cur.next
        cur.next = None
        out.append(part_head)
        cur = nxt
    return out


# ============================================================
# Way 3: Build into array; split
# ============================================================
def split_list_to_parts_3(head, k):
    """Collect values; split into k parts by computed sizes."""
    vals = []
    cur = head
    while cur:
        vals.append(cur.val)
        cur = cur.next
    n = len(vals)
    base_size = n // k
    extra = n % k
    out = []
    i = 0
    for j in range(k):
        size = base_size + (1 if j < extra else 0)
        out.append(list_from_array(vals[i:i + size]))
        i += size
    return out


# ============================================================
# Way 4: Recursive
# ============================================================
def split_list_to_parts_4(head, k):
    """Recursive split."""
    n = 0
    cur = head
    while cur:
        n += 1
        cur = cur.next
    base_size = n // k
    extra = n % k
    out = [None] * k
    cur = head
    for i in range(k):
        if not cur:
            break
        size = base_size + (1 if i < extra else 0)
        out[i] = cur
        for _ in range(size - 1):
            cur = cur.next
        nxt = cur.next if cur else None
        if cur:
            cur.next = None
        cur = nxt
    return out


# ============================================================
# Way 5: Class-based wrapper
# ============================================================
class ListSplitter_5:
    def __init__(self, head, k):
        self.head = head
        self.k = k

    def split(self):
        return split_list_to_parts_1(self.head, self.k)


def split_list_to_parts_5(head, k):
    return ListSplitter_5(head, k).split()


# ============================================================
# Way 6: Use helper to extract part of size N
# ============================================================
def split_list_to_parts_6(head, k):
    """Helper to extract first n nodes."""
    def take(node, n):
        if not node or n == 0:
            return None, node
        head = node
        for _ in range(n - 1):
            node = node.next
        nxt = node.next
        node.next = None
        return head, nxt

    total = 0
    cur = head
    while cur:
        total += 1
        cur = cur.next
    base_size = total // k
    extra = total % k
    out = []
    for i in range(k):
        size = base_size + (1 if i < extra else 0)
        part, head = take(head, size)
        out.append(part)
    return out


# ============================================================
# Way 7: Hash map by index
# ============================================================
def split_list_to_parts_7(head, k):
    """Use index map to slice."""
    nodes = []
    cur = head
    while cur:
        nodes.append(cur)
        cur = cur.next
    n = len(nodes)
    base_size = n // k
    extra = n % k
    out = []
    i = 0
    for j in range(k):
        size = base_size + (1 if j < extra else 0)
        if size == 0:
            out.append(None)
        else:
            # nodes[i..i+size-1]
            nodes[i + size - 1].next = None
            out.append(nodes[i])
            i += size
    return out


# ============================================================
# Way 8: Generator-based
# ============================================================
def split_list_to_parts_8(head, k):
    """Walk with generator; split."""
    n = 0
    cur = head
    while cur:
        n += 1
        cur = cur.next
    base_size = n // k
    extra = n % k
    out = []
    cur = head
    for i in range(k):
        size = base_size + (1 if i < extra else 0)
        if not cur or size == 0:
            out.append(None)
            continue
        part_head = cur
        for _ in range(size - 1):
            cur = cur.next
        nxt = cur.next
        cur.next = None
        out.append(part_head)
        cur = nxt
    return out


# ============================================================
# Way 9: Two-pointer (walk and split)
# ============================================================
def split_list_to_parts_9(head, k):
    """Use two pointers to track boundary."""
    n = 0
    cur = head
    while cur:
        n += 1
        cur = cur.next
    base_size = n // k
    extra = n % k
    out = []
    cur = head
    for i in range(k):
        if not cur:
            out.append(None)
            continue
        size = base_size + (1 if i < extra else 0)
        part_head = cur
        # Use second pointer to walk to last of part
        walker = cur
        for _ in range(size - 1):
            walker = walker.next
        nxt = walker.next
        walker.next = None
        out.append(part_head)
        cur = nxt
    return out


# ============================================================
# Way 10: Final cleanest (THE ONE TO MEMORIZE)
# ============================================================
def split_list_to_parts_10(head, k):
    """
    THE ONE TO MEMORIZE.

    1. Count total length n.
    2. base_size = n // k; extra = n % k.
    3. For i in range(k):
       a. size = base_size + (1 if i < extra else 0).
       b. If head is None or size is 0, append None.
       c. Else walk size-1 steps from head; the current node's next becomes
          None (cuts the part); the next becomes the new head.

    Time:  O(n + k)
    Space: O(k) for output.
    """
    n = 0
    cur = head
    while cur:
        n += 1
        cur = cur.next
    base_size = n // k
    extra = n % k
    out = []
    cur = head
    for i in range(k):
        size = base_size + (1 if i < extra else 0)
        if not cur or size == 0:
            out.append(None)
            continue
        part_head = cur
        for _ in range(size - 1):
            cur = cur.next
        nxt = cur.next
        cur.next = None
        out.append(part_head)
        cur = nxt
    return out


# ============================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# ============================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to split a linked list into k consecutive parts where the part
sizes differ by at most 1 and earlier parts are larger."

Key Insight:
"Count total length n. base_size = n // k, extra = n % k. The first
`extra` parts have size (base_size + 1); the remaining parts have
size base_size. Walk through and cut each part."

Algorithm:
1. Count length n.
2. base_size = n // k; extra = n % k.
3. cur = head.
4. For i in range(k):
   a. size = base_size + (1 if i < extra else 0).
   b. If not cur or size == 0: append None.
   c. Else walk size-1 steps from cur; cur.next becomes None (cut); nxt = cur.next;
      out.append(part_head); cur = nxt.

Edge Cases:
- Empty list: all parts are None.
- k == 1: whole list as one part.
- k > n: first n parts are single-node, rest are None.
- n is multiple of k: all parts equal.

KEY TRICK:
The "+1" for the first `extra` parts makes earlier parts larger, which
matches the requirement.

RELATED PROBLEMS:
- Rotate List (LC 61).
- Reverse Linked List II (LC 92).
- Odd Even Linked List (LC 328).
"""


# ============================================================
# TEST CASES
# ============================================================
def run_tests():
    test_cases = [
        ([1, 2, 3], 5, [[1], [2], [3], [], []], "Standard LC725"),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 3, [[1, 2, 3, 4], [5, 6, 7], [8, 9, 10]], "10 nodes 3 parts"),
        ([1, 2, 3, 4], 2, [[1, 2], [3, 4]], "Equal split"),
        ([], 3, [[], [], []], "Empty"),
        ([1, 2, 3], 1, [[1, 2, 3]], "k=1"),
        ([1, 2, 3], 3, [[1], [2], [3]], "k=n"),
    ]

    implementations = [
        ("Way 1: Count + split (BEST)", split_list_to_parts_1),
        ("Way 2: Walk + part idx", split_list_to_parts_2),
        ("Way 3: Array split", split_list_to_parts_3),
        ("Way 4: Recursive", split_list_to_parts_4),
        ("Way 5: Class-based", split_list_to_parts_5),
        ("Way 6: Take helper", split_list_to_parts_6),
        ("Way 7: Hash map", split_list_to_parts_7),
        ("Way 8: Generator", split_list_to_parts_8),
        ("Way 9: Two-pointer", split_list_to_parts_9),
        ("Way 10: Final cleanest", split_list_to_parts_10),
    ]

    all_pass = True
    for name, fn in implementations:
        passed = 0
        failed = 0
        for inp, k, expected, desc in test_cases:
            try:
                head = list_from_array(copy.deepcopy(inp))
                result = fn(head, k)
                got = list_to_nested_array(result)
                if nested_equal(got, expected):
                    passed += 1
                else:
                    failed += 1
                    all_pass = False
                    print(f"  FAIL [{name}] {desc}: input={inp} k={k} expected={expected} got={got}")
            except Exception as e:
                failed += 1
                all_pass = False
                print(f"  ERROR [{name}] {desc}: {e}")
        status = "PASS" if failed == 0 else f"FAIL ({failed} failures)"
        print(f"{name}: {status} ({passed}/{passed + failed})")

    print("\n" + "=" * 60)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 60)
    print(HOW_TO_THINK)


if __name__ == "__main__":
    run_tests()