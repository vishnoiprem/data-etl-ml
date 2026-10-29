# Remove nth Node from End of List — 10 Solutions + Interview Thinking

## Problem
Remove the n-th node from the end of a singly linked list in a single pass.

Reference: LeetCode #19 / Educative Grokking — "Remove nth Node from End of List".

---

## Interview Thinking (10 Steps)

### 1. Understand
"Given a singly linked list, remove its n-th node from the end and return the head."

### 2. Key Insight
**Two-pointer with a gap of n.** Advance `fast` by n steps, then move both pointers until `fast` reaches the end. `slow` is now at the node just before the target.

### 3. Pattern Recognition
Fast/slow with gap = n. Classic single-pass trick.

### 4. Edge Cases
- n == size → remove head → return head.next
- size == 1, n == 1 → return None
- n == 1 → remove tail

### 5. Tricky Detail
**Use a dummy head.** `dummy = ListNode(0, head)`. Initialize both pointers to `dummy`. Without the dummy, removing the head requires special-casing.

### 6. Algorithm
```
dummy = ListNode(0, head)
fast = slow = dummy
for _ in range(n): fast = fast.next
while fast.next:
    fast = fast.next
    slow = slow.next
slow.next = slow.next.next
return dummy.next
```

### 7. Why It Works
After advancing `fast` by n, the gap is n. When `fast.next` is None (i.e., `fast` is at the last node), `slow` is exactly n behind — at the (n+1)-th from end, which is the node BEFORE the target.

### 8. Complexity
- Time: O(size) — single pass.
- Space: O(1).

### 9. Code Structure
```python
def removeNth(head, n):
    dummy = ListNode(0, head)
    fast = slow = dummy
    for _ in range(n):
        fast = fast.next
    while fast.next:
        fast = fast.next
        slow = slow.next
    slow.next = slow.next.next
    return dummy.next
```

### 10. Mental Trace
`[1,2,3,4,5]`, n=2:
- dummy -> 1 -> 2 -> 3 -> 4 -> 5
- Advance fast by 2 → fast at 2.
- Loop: fast=3,slow=1 → fast=4,slow=2 → fast=5,slow=3. Exit.
- slow at 3; slow.next = 4; set slow.next = 5.
- Result: 1 -> 2 -> 3 -> 5 ✓

---

## 10 Solutions Summary

| #  | Approach                              | Time  | Space |
|----|---------------------------------------|-------|-------|
| 1  | Two-pointer with dummy (BEST)         | O(N)  | O(1)  |
| 2  | Two-pointer without dummy             | O(N)  | O(1)  |
| 3  | Two-pass (count then remove)          | O(N)  | O(1)  |
| 4  | Stack-based                           | O(N)  | O(N)  |
| 5  | Recursive with counter                | O(N)  | O(N)  |
| 6  | List of nodes                         | O(N)  | O(N)  |
| 7  | Two-pointer (head init, no dummy)     | O(N)  | O(1)  |
| 8  | Two-pass with sentinel                | O(N)  | O(1)  |
| 9  | Dict mapping index -> node            | O(N)  | O(N)  |
| 10 | Functional rebuild                    | O(N)  | O(N)  |

---

## Recommended Interview Answer
**Solution 1** — clean, optimal, single pass:

```python
def removeNth(head, n):
    dummy = ListNode(0, head)
    fast = slow = dummy
    for _ in range(n):
        fast = fast.next
    while fast.next:
        fast = fast.next
        slow = slow.next
    slow.next = slow.next.next
    return dummy.next
```

---

## Common Pitfalls
1. **Forgetting the dummy** — special-casing head removal is messy.
2. **Off-by-one in the gap** — the gap should be n, not n+1; `slow` lands on the node BEFORE the target.
3. **Setting `slow.next = None` instead of `slow.next.next`** — must skip the target, not nuke the rest.
4. **Not handling n == size** — works naturally with dummy but can break without.
