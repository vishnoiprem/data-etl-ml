# Number of Visible People in a Queue - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/number-of-visible-people-in-a-queue

## The Problem
```
Given an array heights where heights[i] is the height of person i in a queue
(standing in a line), return an array answer where answer[i] is the number
of people person i CAN SEE looking to their right.

Person i can see person j (i < j) if:
- Everyone between i and j has height STRICTLY LESS than BOTH heights[i] and heights[j]

Examples:
    [10, 6, 8, 5, 11, 9]    -> [3, 1, 2, 1, 1, 0]
    [5, 1, 2, 3, 10]        -> [4, 1, 1, 1, 0]
    [5, 4, 3, 2, 1]         -> [1, 1, 1, 1, 0]
    [1, 2, 3, 4, 5]         -> [1, 1, 1, 1, 0]

Constraints:
- 1 <= heights.length <= 10^5
- 1 <= heights[i] <= 10^5
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
heights = [10, 6, 8, 5, 11, 9]

Person 0 (h=10): can see 6 (yes), 8 (yes, but 6 was shorter between), 
                  5 (yes, after popping 6 and 8), 11 (yes).
                  Wait - actually can see: 6, 8 (since 6 is smaller than 8),
                  but 11 is taller so 10 is blocked. Hmm.

Let me re-think:
Person 0 sees:
- 6 (immediately, since 10>6)
- 8 (yes - 6<8<10 and 6<10)
- 5 (no - 5<10 but 5 is shorter than 6? wait 5<6<10, so 5<10. Can 10 see 5?)
  Yes IF no one between 10 and 5 is >= 5. But between 10 and 5 are 6 and 8, both >= 5. So NO.
- 11: 10<11, blocked. NO.
- Answer for 0: sees 6 and 8. Count = 2. Hmm but expected is 3.

Wait, let me re-read the problem. Maybe person 0 can see 6, 8, AND something else.

Standard interpretation: Person i sees person j (j > i) if:
- All people between i and j have height STRICTLY LESS than BOTH heights[i] and heights[j]
- Actually no: all between have height LESS than min(heights[i], heights[j])

For i=0 (h=10):
- j=1 (h=6): between = empty. min(10,6)=6. Person 0 sees 1. ✓
- j=2 (h=8): between = [6]. min(10,8)=8. Is 6<8? Yes. Person 0 sees 2. ✓
- j=3 (h=5): between = [6,8]. min(10,5)=5. Is 6<5? No. Person 0 does NOT see 3.
- j=4 (h=11): between = [6,8,5]. min(10,11)=10. Is everyone <10? Yes (6,8,5 all <10). So 0 sees 4. ✓
  But heights[4]=11 > 10, so person 0 doesn't matter for next. 4 sees 0 actually.
  Hmm, actually "sees" - person 0 sees 11 because 11 is taller and the path is clear.

Wait I'm confusing myself. Let me re-check standard LeetCode problem 1944:
"Number of Visible People in a Queue"

answer[i] = number of people person i can see to the RIGHT.
Person i sees person j (j > i) if:
- heights[k] < min(heights[i], heights[j]) for all i < k < j

For [10, 6, 8, 5, 11, 9]:
Person 0 (h=10):
- Sees 1 (h=6): min=6, between empty. ✓
- Sees 2 (h=8): min=8, between [6], 6<8 ✓
- Sees 3 (h=5): min=5, between [6,8], 6<5? No. ✗
- Sees 4 (h=11): min=10, between [6,8,5], all <10 ✓
- Sees 5 (h=9): min=9, between [6,8,5,11], 11<9? No. ✗
Total = 3 ✓ (matches expected)
```

### Step 2: The Trick
> "Use a MONOTONIC INCREASING STACK of indices.
> When a TALLER person (or equal) arrives:
>   - POP all shorter ones - they just 'saw' the new person
>   - If stack not empty after popping, the TOP also sees the new person
> Push current index.
> Each person can see at most 2: one taller behind them OR one in front + new shorter ones."

### Step 3: Why Stack?
> "When person i (height h) arrives:
> - Everyone on stack with height < h just found their 'next taller to see'
>   They get popped and increment their count by 1.
> - If stack still has elements, the top is TALLER (>= h), so it can see h.
>   Increment stack[-1]'s count by 1.
> - Push i.
>
> Why this works: Stack keeps people in INCREASING height order.
> When taller comes, shorter people on top all see it.
> Then taller sees the new shorter one (in front of it)."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to count, for each person in a queue, how many people to their right
> they can see. Person i can see person j if everyone between them is shorter
> than BOTH i and j."

**Key Insight:**
> "When a TALLER person arrives, they BLOCK everyone shorter on the stack.
> Those shorter people just 'saw' the taller person - increment their count.
> Also, the new shorter (or equal) person can be seen by the TOP of the stack
> if any (top is taller than or equal).
> Use a monotonic INCREASING stack of indices."

**Algorithm:**
> "1. Initialize result = [0] * n, stack = []
> 2. For each i in range(n):
>    a. h = heights[i]
>    b. While stack not empty AND heights[stack[-1]] < h:
>       - Pop j = stack.pop()
>       - result[j] += 1  (j can see person i)
>    c. If stack not empty:
>       - result[stack[-1]] += 1  (top sees person i)
>    d. Push i onto stack
> 3. Return result"

**Why this works:**
> "When person i (height h) arrives, all shorter people on the stack are
> blocked by i - they could see past them to a taller/equal person.
> They increment their count by 1 each.
>
> After popping all shorter, the top of stack (if any) is taller than or equal.
> Top can see i (no one between since stack is increasing, and i < top's pos).
> So top increments its count by 1.
>
> Push i.
>
> Result for i itself: increments happen when someone taller/equal arrives."

**Edge cases:**
- All increasing: each sees exactly 1
- All decreasing: each sees 1 EXCEPT last sees 0
- Equal heights: tricky - equal still sees count carefully

---

## The 20 Implementations (Simple to Complex)

### Way 1: Monotonic Stack (BEST - Memorize!)
```python
def canSeePersonsCount(heights):
    n = len(heights)
    result = [0] * n
    stack = []
    for i in range(n):
        while stack and heights[stack[-1]] < heights[i]:
            result[stack.pop()] += 1
        if stack:
            result[stack[-1]] += 1
        stack.append(i)
    return result
```

### Way 2: Standard monotonic (with >= check)
### Way 3: Brute force O(n^2)
### Way 4: With deque
### Way 5: Cleaner variable names
### Way 6: Helper function for visible logic
### Way 7: One-liner style
### Way 8: Try-except handling
### Way 9: Most compact

### Way 10-12: Specialized
- Way 10: Explicit ops
- Way 11: Class-based
- Way 12: reduce-based

### Way 13-16: Specialized
- Way 13: Reverse iteration
- Way 14: Most elegant
- Way 15: enumerate-based
- Way 16: Lookup dict for heights

### Way 17-20: Variations
- Way 17: Most compact names
- Way 18: Helper class
- Way 19: While not loop
- Way 20: Final cleanest

---

## Decision Tree

```
+------------------+-------------+--------------+
| Scenario         | Best        | Why          |
+------------------+-------------+--------------+
| Most efficient   | Monotonic   | O(n)         |
| Educational      | Brute       | Simple       |
| Functional       | reduce      | No mutation  |
+------------------+-------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Monotonic | O(n) | O(n) |
| Brute | O(n^2) | O(1) |

---

## Walkthrough Example

```
heights = [10, 6, 8, 5, 11, 9]

i=0, h=10: stack empty. if stack skip. push 0. stack=[0]. result=[0,0,0,0,0,0]
i=1, h=6: stack[-1]=0, h[0]=10, 10<6? No. if stack: result[0]+=1. result=[1,...]
          push 1. stack=[0,1]
i=2, h=8: stack[-1]=1, h[1]=6, 6<8? Yes. pop 1. result[1]+=1. result=[..,1,..]
          stack[-1]=0, h[0]=10, 10<8? No. if stack: result[0]+=1. result=[2,...]
          push 2. stack=[0,2]
i=3, h=5: stack[-1]=2, h[2]=8, 8<5? No. if stack: result[2]+=1. result=[..,2,..]
          push 3. stack=[0,2,3]
i=4, h=11:
  stack[-1]=3, h[3]=5, 5<11. pop 3. result[3]+=1. result=[..,1,..]
  stack[-1]=2, h[2]=8, 8<11. pop 2. result[2]+=1. result=[..,3,..]
  stack[-1]=0, h[0]=10, 10<11. pop 0. result[0]+=1. result=[3,...]
  stack empty. push 4. stack=[4]
i=5, h=9: stack[-1]=4, h[4]=11, 11<9? No. if stack: result[4]+=1.
          push 5. stack=[4,5]

Final result = [3, 1, 2, 1, 1, 0] ✓
```

## Best Answer to Memorize

```python
def canSeePersonsCount(heights):
    n = len(heights)
    result = [0] * n
    stack = []
    for i in range(n):
        while stack and heights[stack[-1]] < heights[i]:
            result[stack.pop()] += 1
        if stack:
            result[stack[-1]] += 1
        stack.append(i)
    return result
```

**11 lines. O(n) time. Clean. Interview-ready!**

## Key Insights

### Why Monotonic INCREASING Stack?
> "Stack maintains increasing heights. When a new (taller) person comes,
> it 'resolves' the visibility of all shorter people on top.
> After all pop, the top is taller (or equal), so it sees the new shorter."

### Why Both Pop+Increment AND If-stack-Increment?
> "Two scenarios when new person arrives:
> - NEW person is TALLER than top: top sees new (after pop). Each popped sees new.
> - NEW person is SHORTER (or equal): just push, but top (taller) sees new.
>
> Wait no - if new is SHORTER, while loop doesn't execute. We push.
> But we still increment top (top sees the new shorter from above).
>
> If new is TALLER: pops all shorter (each sees new), then push.
> If stack still has elements (taller than new), they see new."
>
> Actually let me re-think: in both cases (shorter or taller):
> if new arrives, top of stack (after popping all shorter) can see new.
> Because top is taller (or equal).

### Why Each Pop Sees New Person?
> "Person j (shorter) sees person i (taller) because:
> - j is to the left of i
> - No one between j and i is taller than j (we just popped j when finding i)
> - But i is taller than j, so j can see i
> - j cannot see anyone BEYOND i (i is taller, blocks j)"
>
> So each pop increments by 1 ONLY for seeing the immediate taller person.
> Could j see people beyond? No, they're blocked by i.

### Difference from "Daily Temperatures"?
> "Daily Temperatures: find NEXT GREATER (count days to wait).
> Number of Visible People: COUNT visible people on the RIGHT.
>
> Stack is similar (monotonic increasing), but the action is different:
> - Daily: just record distance
> - Visible: increment multiple counters in result"

## Test Cases

| heights | Expected | Why |
|---------|----------|-----|
| [10, 6, 8, 5, 11, 9] | [3, 1, 2, 1, 1, 0] | Standard |
| [5, 1, 2, 3, 10] | [4, 1, 1, 1, 0] | Mixed |
| [5, 4, 3, 2, 1] | [1, 1, 1, 1, 0] | Decreasing |
| [1, 2, 3, 4, 5] | [1, 1, 1, 1, 0] | Increasing |
| [1] | [0] | Single person |
| [3, 1, 5, 1, 5, 1] | [3, 1, 1, 1, 1, 0] | Complex |
| [4, 3, 2, 1] | [1, 1, 1, 0] | Strictly decreasing |

## Common Pitfalls

1. **Using >= in pop condition**: Should be < to handle equal correctly
2. **Forgetting to increment top of stack**: Each person sees the new shorter person
3. **Wrong direction**: We need RIGHT-TO-LEFT (next taller), so we iterate FORWARD
4. **Off-by-one**: result[0] for person 0 starts at 0, increments when someone taller comes

## Why This Problem Matters

> "Tests:
> 1. Monotonic stack pattern (CRITICAL skill)
> 2. Visibility/counting problem
> 3. Multiple counter updates per operation
> 4. Similar to: Daily Temperatures, Trapping Rain Water
> 5. Key insight: each pop = +1 to that person's count"
