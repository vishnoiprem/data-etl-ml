"""
Merge K Sorted Lists
Hard | 45 min

You are given an array of k linked lists, each sorted in ascending order.
Merge all the linked lists into one sorted linked list and return it.

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/merge-k-sorted-lists

Examples:
    lists=[[1,4,5],[1,3,4],[2,6]] -> [1,1,2,3,4,4,5,6]
    lists=[] -> []
    lists=[[]] -> []

Constraints:
- 0 <= k <= 10^4
- 0 <= lists[i].length <= 500
- -10^4 <= lists[i][j] <= 10^4
- lists[i] is sorted in ascending order.
- Total nodes across all lists <= 10^4.

KEY INSIGHT:
Min-heap (priority queue) of k heads.
Pop smallest, append to result, push next from same list.

Time:  O(N log k) — N = total nodes.
Space: O(k) — heap + output.
"""


# =============================================================================
# HOW TO THINK
# =============================================================================
HOW_TO_THINK = """
HOW TO THINK ABOUT MERGE K SORTED LISTS:

1. UNDERSTAND THE PROBLEM:
   "Merge k sorted linked lists into one sorted list."

2. KEY OBSERVATION:
   "At any time, the NEXT smallest element is among the heads of the
   k lists. We pick it, append to result, advance that list, repeat."

3. WHY MIN-HEAP:
   "A min-heap of size k gives us the smallest head in O(log k).
   Total O(N log k) where N is total nodes.
   Naive pairwise merge would be O(k * N) or O(k² * avg_len)."

4. ALGORITHM:
   "1. Initialize min-heap with head of each non-empty list.
    2. Pop smallest, append to result.
    3. If popped node has next, push next to heap.
    4. Repeat until heap empty."

5. EDGE CASES:
   - Empty lists array: return None.
   - Lists with empty entries: skip empties when initializing heap.
   - Single list: return that list.

6. COMPLEXITY:
   +----------+--------+--------+
   | Approach | Time   | Space  |
   +----------+--------+--------+
   | Min-heap | O(N log k) | O(k) |
   | Pairwise | O(kN)    | O(1)  |
   | Divide-conq| O(N log k) | O(log k) |
   +----------+--------+--------+

7. WHY HEAP > PAIRWISE:
   "Pairwise merge (merge 2, then merge result with 3rd, ...) is O(kN).
   Heap gives O(N log k) which is much better for large k."
"""


# =============================================================================
# Node definition
# =============================================================================
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


# =============================================================================
# Helper: build list from array
# =============================================================================
def build_list(arr):
    """Build linked list from array. Returns head or None."""
    if not arr:
        return None
    head = ListNode(arr[0])
    cur = head
    for v in arr[1:]:
        cur.next = ListNode(v)
        cur = cur.next
    return head


def list_to_array(head):
    """Convert linked list to array."""
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


# =============================================================================
# WAY 1: Min-heap (BEST - Memorize!)
# =============================================================================
def merge_k_lists_1(lists):
    """
    Use min-heap of size at most k.
    Each entry: (node.val, idx, node) — idx for tie-breaking.
    """
    import heapq
    heap = []
    for i, head in enumerate(lists):
        if head:
            heapq.heappush(heap, (head.val, i, head))
    dummy = ListNode(0)
    cur = dummy
    while heap:
        val, i, node = heapq.heappop(heap)
        cur.next = node
        cur = cur.next
        if node.next:
            heapq.heappush(heap, (node.next.val, i, node.next))
    return dummy.next


# =============================================================================
# WAY 2: heapq with wrapper class (no idx needed)
# =============================================================================
class HeapNode:
    def __init__(self, node):
        self.node = node

    def __lt__(self, other):
        return self.node.val < other.node.val


def merge_k_lists_2(lists):
    """Use a wrapper class to compare nodes by val."""
    import heapq
    heap = []
    for head in lists:
        if head:
            heapq.heappush(heap, HeapNode(head))
    dummy = ListNode(0)
    cur = dummy
    while heap:
        wrapper = heapq.heappop(heap)
        cur.next = wrapper.node
        cur = cur.next
        if wrapper.node.next:
            heapq.heappush(heap, HeapNode(wrapper.node.next))
    return dummy.next


# =============================================================================
# WAY 3: Divide and conquer (merge pairs recursively)
# =============================================================================
def merge_k_lists_3(lists):
    """Pairwise merge using divide and conquer. O(N log k)."""

    def merge_two(a, b):
        dummy = ListNode(0)
        cur = dummy
        while a and b:
            if a.val <= b.val:
                cur.next = a
                a = a.next
            else:
                cur.next = b
                b = b.next
            cur = cur.next
        cur.next = a if a else b
        return dummy.next

    if not lists:
        return None
    if len(lists) == 1:
        return lists[0]

    def helper(l):
        if len(l) <= 1:
            return l[0] if l else None
        mid = len(l) // 2
        left = helper(l[:mid])
        right = helper(l[mid:])
        return merge_two(left, right)

    return helper(lists)


# =============================================================================
# WAY 4: Sequential pairwise merge (pairwise reduce)
# =============================================================================
def merge_k_lists_4(lists):
    """Reduce: merge two at a time. O(kN) but simple."""

    def merge_two(a, b):
        dummy = ListNode(0)
        cur = dummy
        while a and b:
            if a.val <= b.val:
                cur.next = a
                a = a.next
            else:
                cur.next = b
                b = b.next
            cur = cur.next
        cur.next = a if a else b
        return dummy.next

    if not lists:
        return None
    result = lists[0]
    for i in range(1, len(lists)):
        result = merge_two(result, lists[i])
    return result


# =============================================================================
# WAY 5: Sort all values, build list
# =============================================================================
def merge_k_lists_5(lists):
    """Collect all values, sort, rebuild list. O(N log N)."""
    vals = []
    for head in lists:
        while head:
            vals.append(head.val)
            head = head.next
    vals.sort()
    return build_list(vals)


# =============================================================================
# WAY 6: heapq.merge on lazy iterators
# =============================================================================
def merge_k_lists_6(lists):
    """Use heapq.merge with iterators. Then build list."""

    def iter_list(head):
        node = head
        while node:
            yield node.val
            node = node.next

    import heapq
    merged_vals = list(heapq.merge(*[iter_list(h) for h in lists if h]))
    return build_list(merged_vals)


# =============================================================================
# WAY 7: Brute - merge smallest pair repeatedly
# =============================================================================
def merge_k_lists_7(lists):
    """Find smallest pair, merge, repeat. Educational, slow."""

    def merge_two(a, b):
        dummy = ListNode(0)
        cur = dummy
        while a and b:
            if a.val <= b.val:
                cur.next = a
                a = a.next
            else:
                cur.next = b
                b = b.next
            cur = cur.next
        cur.next = a if a else b
        return dummy.next

    active = [h for h in lists if h]
    while len(active) > 1:
        # Find two smallest first nodes (by val).
        min_val = float("inf")
        min_idx = -1
        for i, h in enumerate(active):
            if h.val < min_val:
                min_val = h.val
                min_idx = i
        # Swap with last and merge with neighbor.
        active[min_idx], active[-1] = active[-1], active[min_idx]
        merged = merge_two(active[-2], active[-1])
        active = active[:-2] + ([merged] if merged else [])
    return active[0] if active else None


# =============================================================================
# WAY 8: Class OOP
# =============================================================================
class KListMerger:
    def __init__(self, lists):
        self.lists = lists

    def merge(self):
        import heapq
        heap = []
        for i, head in enumerate(self.lists):
            if head:
                heapq.heappush(heap, (head.val, i, head))
        dummy = ListNode(0)
        cur = dummy
        while heap:
            val, i, node = heapq.heappop(heap)
            cur.next = node
            cur = cur.next
            if node.next:
                heapq.heappush(heap, (node.next.val, i, node.next))
        return dummy.next


def merge_k_lists_8(lists):
    return KListMerger(lists).merge()


# =============================================================================
# WAY 9: heapq with global counter for tie-breaking
# =============================================================================
def merge_k_lists_9(lists):
    """Use heapq with unique counter for tie-breaking."""
    import heapq
    counter = 0  # tiebreaker
    heap = []
    for i, head in enumerate(lists):
        if head:
            heapq.heappush(heap, (head.val, counter, head))
            counter += 1
    dummy = ListNode(0)
    cur = dummy
    while heap:
        val, _, node = heapq.heappop(heap)
        cur.next = node
        cur = cur.next
        if node.next:
            heapq.heappush(heap, (node.next.val, counter, node.next))
            counter += 1
    return dummy.next


# =============================================================================
# WAY 10: Final cleanest (THE ONE TO MEMORIZE)
# =============================================================================
def merge_k_lists_10(lists):
    """
    THE ONE TO MEMORIZE.

    Min-heap of size k. Each entry: (node.val, idx, node).
    Pop smallest, advance list, push next.

    Time:  O(N log k), Space: O(k).
    """
    import heapq
    heap = []
    for i, head in enumerate(lists):
        if head:
            heapq.heappush(heap, (head.val, i, head))
    dummy = ListNode(0)
    cur = dummy
    while heap:
        val, i, node = heapq.heappop(heap)
        cur.next = node
        cur = cur.next
        if node.next:
            heapq.heappush(heap, (node.next.val, i, node.next))
    return dummy.next


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Min-heap (BEST)", merge_k_lists_1),
        ("Way 2: Wrapper class", merge_k_lists_2),
        ("Way 3: Divide and conquer", merge_k_lists_3),
        ("Way 4: Sequential merge", merge_k_lists_4),
        ("Way 5: Sort all values", merge_k_lists_5),
        ("Way 6: heapq.merge iterators", merge_k_lists_6),
        ("Way 7: Brute pair min", merge_k_lists_7),
        ("Way 8: Class OOP", merge_k_lists_8),
        ("Way 9: Counter tiebreak", merge_k_lists_9),
        ("Way 10: Final cleanest", merge_k_lists_10),
    ]

    test_cases = [
        # (lists_as_arrays, expected_array)
        ([[1, 4, 5], [1, 3, 4], [2, 6]], [1, 1, 2, 3, 4, 4, 5, 6]),
        ([], []),
        ([[]], []),
        ([[1, 2, 3]], [1, 2, 3]),
        ([[1], [2], [3]], [1, 2, 3]),
        ([[-1, 0, 1], [-2, 0, 2]], [-2, -1, 0, 0, 1, 2]),
        ([[1, 5, 9], [2, 6, 10], [3, 7, 11]], [1, 2, 3, 5, 6, 7, 9, 10, 11]),
    ]

    print("=" * 70)
    print("MERGE K SORTED LISTS - 10 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/merge-k-sorted-lists")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for lists_arr, expected in test_cases:
            try:
                # Build linked lists.
                lists = [build_list(arr) for arr in lists_arr]
                result = func(lists)
                if list_to_array(result) != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: expected={expected}, got={list_to_array(result)}")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR - {e}")
        print(f"  OK {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 10 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
