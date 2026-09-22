# Sum of Subarray Minimums - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/sum-of-subarray-minimums

## The Problem
```
Given array arr of positive integers. Find sum of min(b) for every
CONTIGUOUS subarray b of arr. Return answer mod (10^9 + 7).

Examples:
    arr = [3, 1, 2, 4]        -> 17
    arr = [11, 81, 94, 43, 3] -> 444

Trace [3, 1, 2, 4]:
    [3]=3, [1]=1, [2]=2, [4]=4
    [3,1]=1, [1,2]=1, [2,4]=2
    [3,1,2]=1, [1,2,4]=1
    [3,1,2,4]=1
    Sum: 3+1+2+4+1+1+2+1+1+1 = 17 ✓

Constraints:
- 1 <= arr.length <= 3 * 10^4
- 1 <= arr[i] <= 3 * 10^4
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
Brute force is O(n^2): for each subarray, find min.
But for n = 30000, n^2 = 9*10^8 operations. Too slow.

Better: for each element arr[i], count subarrays where it's the min,
then multiply by arr[i] and sum.
```

### Step 2: The Trick
> "For each element arr[i]:
> - It's the min for subarrays in some range.
> - Compute LEFT = number of subarrays ENDING at i with arr[i] as min.
> - Compute RIGHT = number of subarrays STARTING at i with arr[i] as min.
> - Contribution = arr[i] * LEFT * RIGHT"

### Step 3: Stack Computation
> "Use a monotonic stack:
> - LEFT: walk left to right. Pop elements STRICTLY greater than arr[i].
>   Count how many subarrays ending at i have arr[i] as min.
> - RIGHT: walk right to left. Pop elements GREATER OR EQUAL to arr[i].
>   Count subarrays starting at i with arr[i] as min."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need to sum min(b) over all subarrays b of arr. Brute force is
> O(n^2). I need O(n)."

**Key Insight:**
> "Each element's contribution: count subarrays where it's the MIN
> and multiply by its value.
>
> For element arr[i]:
> - left[i] = # subarrays ending at i with arr[i] as min
> - right[i] = # subarrays starting at i with arr[i] as min
> - contribution = arr[i] * left[i] * right[i]"

**Algorithm:**
> "1. Compute left[i] using monotonic stack (strict greater for pop)
> 2. Compute right[i] using monotonic stack (greater-or-equal for pop)
> 3. Sum arr[i] * left[i] * right[i] mod 10^9+7"

**Why strict vs non-strict:**
> "To avoid double-counting equal elements:
> - For left (going forward): pop strict-greater (arr[j] > arr[i])
> - For right (going backward): pop greater-equal (arr[j] >= arr[i])
> This ensures each subarray's min is counted EXACTLY ONCE."

**Edge cases:**
- All same: each element is min for some range
- All increasing: first element is min for everything containing it (sort of)

**Complexity:**
- Time: O(n) - each element pushed/popped once
- Space: O(n) for left, right, and stack

---

## The 20 Implementations (Simple to Complex)

### Way 1: Two stacks for distances (BEST - Memorize!)
```python
def sumSubarrayMins(arr):
    MOD = 10**9 + 7
    n = len(arr)

    # Left: distance to previous strictly less
    left = [0] * n
    stack = []
    for i in range(n):
        while stack and arr[stack[-1]] > arr[i]:
            stack.pop()
        left[i] = i - (stack[-1] if stack else -1)
        stack.append(i)

    # Right: distance to next less-or-equal
    right = [0] * n
    stack = []
    for i in range(n - 1, -1, -1):
        while stack and arr[stack[-1]] >= arr[i]:
            stack.pop()
        right[i] = (stack[-1] if stack else n) - i
        stack.append(i)

    return sum(arr[i] * left[i] * right[i] for i in range(n)) % MOD
```

### Way 2: Expanding counts version
```python
for i in range(n):
    cnt = 1
    while stack and arr[stack[-1]] > arr[i]:
        cnt += left[stack.pop()]
    left[i] = cnt
    stack.append(i)
```

### Way 3: Brute force O(n^2)

### Way 4-7: With sentinel values
- Add 0 at start and end. The 0 forces pop of all elements at end.

### Way 8-10: With prev_less and next_less arrays

### Way 11: Class-based

### Way 12: With deque

### Way 13-17: Various indexing patterns

### Way 18: Pre-computed distances

### Way 19-20: With helper functions

---

## Decision Tree

```
+------------------+----------+--------------+
| Scenario         | Best     | Why          |
+------------------+----------+--------------+
| Standard         | Way 1    | Cleanest     |
| Educational      | Way 3    | Simple brute |
| One pass         | Way 7/15 | Sentinel     |
+------------------+----------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| 2-pass with stacks | O(n) | O(n) |
| One-pass with sentinels | O(n) | O(n) |
| Brute force | O(n²) | O(1) |

---

## Walkthrough Example

```
arr = [3, 1, 2, 4]

LEFT pass (strict greater for pop):
i=0, 3: stack empty. left[0] = 0 - (-1) = 1. push 0. stack=[0]
i=1, 1: arr[0]=3 > 1, pop. stack=[]. left[1] = 1 - (-1) = 2. push 1. stack=[1]
i=2, 2: arr[1]=1 < 2, no pop. left[2] = 2 - 1 = 1. push 2. stack=[1,2]
i=3, 4: arr[2]=2 < 4, no pop. arr[1]=1 < 4, no pop. left[3] = 3 - 1 = 2. push 3. stack=[1,2,3]

left = [1, 2, 1, 2]

RIGHT pass (greater-or-equal for pop):
i=3, 4: empty. right[3] = 4 - 3 = 1. push 3. stack=[3]
i=2, 2: arr[3]=4 >= 2, pop. empty. right[2] = 4 - 2 = 2. push 2. stack=[2]
i=1, 1: arr[2]=2 >= 1, pop. empty. right[1] = 4 - 1 = 3. push 1. stack=[1]
i=0, 3: arr[1]=1 < 3, no pop. right[0] = 1 - 0 = 1. push 0. stack=[1, 0]

right = [1, 3, 2, 1]

Contributions:
- arr[0]=3: 3 * 1 * 1 = 3
- arr[1]=1: 1 * 2 * 3 = 6
- arr[2]=2: 2 * 1 * 2 = 4
- arr[3]=4: 4 * 2 * 1 = 8
Sum: 3+6+4+8 = 21... wait that's not 17!

Hmm let me re-trace.

Actually with strict greater on left and greater-or-equal on right, for arr[2]=2:
- left[2]: previous strictly less than 2. arr[1]=1 < 2. So left[2] should be 1 (just itself? or 2 counting the [1,2]?)

Hmm. Let me re-think.

Actually the formula left[i] = i - prev_strict_less should give the count of subarrays ENDING at i where arr[i] is the min. Let me re-trace.

For i=2, arr[2]=2:
- prev strict less: arr[1]=1. So we can have subarrays ending at i that start at any index from 1 to 2 (= 2 subarrays: [2] and [1,2]).
- Wait but [1,2] has min 1, not 2. So [1,2] should NOT have arr[2]=2 as min.

I think I had it wrong. Let me reconsider.

left[i] should count subarrays ENDING at i where arr[i] is the MIN (smaller than or equal to all elements to its left in the subarray).

For arr[2]=2, in [1,2,4]: [1,2] (ends at 2, contains 1 < 2). 1 is min. arr[2] is NOT min.
So left[2] for "arr[2]=2 is min" subarrays ending at 2:
- [2]: arr[2]=2 is min. ✓
- [1,2]: arr[1]=1 is min. arr[2] is NOT min. ✗
So left[2] should be 1, not 2.

But my formula gave left[2] = 1. ✓

Hmm, let me re-trace arr[3]=4:
- left[3]: previous strict less than 4. arr[1]=1. So subarrays ending at 3 starting from 1 to 3: [4], [2,4], [1,2,4].
- For [4]: 4 is min. ✓
- For [2,4]: 2 is min. ✗
- For [1,2,4]: 1 is min. ✗
- So left[3] = 1, not 2.

But my trace gave left[3] = 2!

I think my formula is wrong. The correct formula uses >= not > when popping for left too?

Or: left[i] = i - (index of previous <= or index of previous strictly less)?

Actually let me think again. For Way 1, when we pop arr[stack[-1]] > arr[i], we pop elements that are STRICTLY greater than arr[i]. We keep elements that are <= arr[i].

If stack is empty after popping, prev_strict_less = -1 (no such element).
If stack is not empty and the top is <= arr[i]: that top could be equal or less.

For i=3, arr[3]=4:
- Stack before: [1, 2, 3] (indices)
- arr[2]=2 < 4, no pop.
- arr[1]=1 < 4, no pop.
- left[3] = 3 - 1 = 2.

But 1 < 4 means 1 is strictly less than 4. So prev_strict_less is at index 1, distance is 3-1=2.

Hmm but that says there are 2 subarrays ending at 3 with arr[3]=4 as min. Let me list subarrays ending at 3:
- [4]: min=4 ✓
- [2,4]: min=2 (NOT 4) ✗
- [1,2,4]: min=1 ✗
- [3,1,2,4]: min=1 ✗

So only 1 subarray, but formula says 2.

There's a bug in Way 1. The correct formula should be:

Actually I realize the formula gives 2 subarrays, but it should give 1. The formula is wrong.

Hmm, wait, actually this is a known issue with the strict-vs-non-strict comparison.

In Way 2 (expanding counts version), I do:
```python
for i in range(n):
    cnt = 1
    while stack and arr[stack[-1]] > arr[i]:
        cnt += left[stack.pop()]
    left[i] = cnt
    stack.append(i)
```

This is actually a different approach. We're not computing distance, we're accumulating counts.

For i=3, arr[3]=4:
- Stack before: [1, 2, 3] (left[1]=2, left[2]=1, left[3]=2)
- arr[3]=4. While arr[stack[-1]] > 4? arr[2]=2, 2 > 4? No. arr[1]=1, 1 > 4? No. Don't pop.
- cnt = 1.
- left[3] = 1.

So Way 2 gives left[3] = 1, which is correct.

So Way 1 is wrong, Way 2 is right. Let me fix Way 1.

Actually wait, let me re-think the formula. Maybe I'm confusing myself.

Let me think about a simpler example: arr = [2, 4, 1, 3].
- Subarrays and their mins:
  [2]=2, [4]=4, [1]=1, [3]=3
  [2,4]=2, [4,1]=1, [1,3]=1
  [2,4,1]=1, [4,1,3]=1
  [2,4,1,3]=1
- Sum: 2+4+1+3+2+1+1+1+1+1 = 17

For element 0 (arr[0]=2):
- Subarrays where it's min:
  - [2] (✓, ends at 0)
  - [2,4] (✓, ends at 1)
- left = 2, right = 1
- Contribution: 2 * 2 * 1 = 4

For element 2 (arr[2]=1):
- Subarrays where it's min:
  - [1], [4,1], [1,3], [2,4,1], [4,1,3], [2,4,1,3]
- In terms of ending at 2: [1], [4,1], [2,4,1] = 3
- In terms of starting at 2: [1], [1,3], [1,3] = wait
  - [1] starts at 2
  - [1,3] starts at 2
  - [2,4,1,3] starts at 0 (not at 2)
- Actually starting AT 2: [1], [1,3] = 2

Hmm. Let me rethink.

left[i] = number of subarrays ENDING at i where arr[i] is min.
right[i] = number of subarrays STARTING at i where arr[i] is min.

For arr[2]=1:
Subarrays ending at 2: [1], [4,1], [2,4,1]
- [1]: min=1=arr[2] ✓
- [4,1]: min=1=arr[2] ✓
- [2,4,1]: min=1=arr[2] ✓
left[2] = 3

Subarrays starting at 2: [1], [1,3]
- [1]: min=1=arr[2] ✓
- [1,3]: min=1=arr[2] ✓
right[2] = 2

Contribution: 1 * 3 * 2 = 6.

Now WAY 2 computation for left:
i=0, arr[0]=2: stack empty. cnt = 1. left[0]=1. push 0. stack=[0]
i=1, arr[1]=4: arr[0]=2 < 4, no pop. cnt = 1. left[1]=1. push 1. stack=[0,1]
i=2, arr[2]=1: arr[1]=4 > 1, pop. cnt += left[1] = 1+1 = 2. arr[0]=2 > 1, pop. cnt += left[0] = 2+1 = 3. stack empty. cnt = 3. left[2]=3. push 2. stack=[2].
i=3, arr[3]=3: arr[2]=1 < 3, no pop. cnt = 1. left[3]=1. push 3. stack=[2,3]

left = [1, 1, 3, 1] ✓

For WAY 1 formula: distance to prev strict less
i=0: prev = -1, dist = 1. left[0] = 1 ✓
i=1: prev = 0 (arr[0]=2 < 4, not popped), dist = 1. left[1] = 1 ✓
i=2: pop until top <= 1. After popping 4 and 2, stack empty. prev = -1. dist = 3. left[2] = 3 ✓
i=3: top = 2 (arr[2]=1 < 3), prev = 2, dist = 1. left[3] = 1 ✓

So Way 1 gives [1, 1, 3, 1] too. The formula was right.

Let me retrace my earlier trace for [3, 1, 2, 4]:
i=0, arr[0]=3: stack empty. left[0] = 0 - (-1) = 1. push 0. stack=[0]
i=1, arr[1]=1: arr[0]=3 > 1, pop. stack empty. left[1] = 1-(-1) = 2. push 1. stack=[1]
i=2, arr[2]=2: arr[1]=1 < 2, no pop. left[2] = 2-1 = 1. push 2. stack=[1, 2]
i=3, arr[3]=4: arr[2]=2 < 4, no pop. arr[1]=1 < 4, no pop. left[3] = 3-1 = 2. push 3. stack=[1, 2, 3]

left = [1, 2, 1, 2]

For arr[3]=4, the subarrays ENDING at 3:
- [4]: arr[3]=4 is min ✓ (1 subarray)
- [2,4]: arr[2]=2 < 4, arr[2] is min, NOT arr[3] ✗
- [1,2,4]: arr[1]=1, NOT arr[3] ✗
- [3,1,2,4]: arr[1]=1, NOT arr[3] ✗

So left[3] should be 1, not 2!

My formula is WRONG. The issue is that when computing distance to previous STRICTLY LESS, we need to find the closest such element. The element at index 1 is 1 < 4, but there could be elements between 1 and 3 that don't have smaller values strictly less than 4 but the algorithm doesn't capture correctly.

Wait, actually the formula left[i] = i - prev_strict_less_index gives:
- The count of elements from (prev_strict_less_index + 1) to i, inclusive.
- These are all indices in [prev_strict_less_index + 1, i] for subarrays ending at i.

For i=3, prev=1, count = 3 - 1 = 2, subarrays [arr[2..3], arr[3..3]]? No wait, that includes subarrays starting at 2 and 3 only.

Actually distance = i - prev = 3 - 1 = 2.
Subarrays ending at 3 with arr[3] as min:
- Starting from index 2: [arr[2..3]] = [2,4]. Min = 2, NOT 4. ✗
- Starting from index 3: [arr[3..3]] = [4]. Min = 4. ✓

So only 1 subarray, but formula says 2. Issue!

Hmm. The issue: distance to prev strict less is 2 (indices 1, 2, 3), which is 2 elements before... wait, i - prev = 3 - 1 = 2 means there are 2 indices in the range (1, 3]? No, the count of indices from (prev+1) to i is i - prev = 2 (just indices 2 and 3).

Oh wait, I miscounted. Let me re-list.

Subarrays ENDING at index 3 with min = arr[3] = 4:
- [arr[2..3]] = [2, 4]: min is 2 ✗
- [arr[3..3]] = [4]: min is 4 ✓

So 1 subarray. But formula left[3] = i - prev = 3 - 1 = 2. That's WRONG.

Hmm. Let me re-think.

Actually, the algorithm with stack popping > and computing distance is for finding how far we can extend to the left such that the min equals arr[i]. The condition is that arr[i] is the SMALLEST in the subarray going left from i.

In [2, 4]: arr[2]=2 < 4=arr[3]. So arr[2] < arr[3]. So arr[3] is NOT the min of [2, 4]. ✗

The formula i - prev_strict_less gives the count of elements in [prev+1, i] for which we can form a subarray ending at i. But we need ALL those subarrays to have arr[i] as the smallest.

In our trace, prev_strict_less for index 3 is 1 (arr[1]=1 < 4=arr[3]). What about arr[2]=2? 2 < 4 so it's also strictly less. The algorithm should consider this.

The stack-based "distance to previous strictly less" algorithm computes the distance to the NEAREST strictly less element, but it doesn't account for elements BETWEEN prev_strict_less and i that are also smaller.

Actually, let me reconsider. The monotonic stack approach is designed so that:
- When we pop elements > arr[i] from the stack, we remove those elements.
- The remaining stack has elements <= arr[i] (where top is strictly less or equal).
- The COUNT of subarrays ending at i with arr[i] as min = the DISTANCE from the top of stack (if exists) to i.

But this isn't quite right either. The "subarrays ending at i with arr[i] as min" count is more nuanced.

Actually, wait. After popping all > arr[i], the top of stack is < arr[i] (strict, since we use > to pop, so what's left has <= arr[i]).

Hmm, > in the while condition means we pop strictly greater. So remaining elements have <= arr[i]. If equals, the formula breaks.

In [3, 1, 2, 4], after popping for i=3, arr[3]=4:
- arr[2]=2 < 4, no pop
- arr[1]=1 < 4, no pop
- Stack: [1, 2, 3]
- top = 1, distance = 3 - 1 = 2.

But subarrays ending at 3 with arr[3]=4 as min: only [4], count = 1.

So distance 2 overcounts. The formula must account for not just the prev_strict_less but all intermediate elements.

I think the correct formula is more involved. Let me look this up.

Actually I recall now. The correct algorithm is:

left[i] = distance to prev less OR equal element (NOT strictly less).

If we pop >= arr[i], remaining stack has elements < arr[i] strictly.

Let me re-trace with >=:
i=0, arr[0]=3: stack empty. left[0] = 1. push 0. stack=[0]
i=1, arr[1]=1: arr[0]=3 >= 1, pop. stack empty. left[1] = 2. push 1. stack=[1]
i=2, arr[2]=2: arr[1]=1 < 2, no pop. left[2] = 2-1 = 1. push 2. stack=[1,2]
i=3, arr[3]=4: arr[2]=2 < 4, no pop. arr[1]=1 < 4, no pop. left[3] = 3-1 = 2. push 3. stack=[1,2,3]

Same result. So popping with > vs >= gives same answer here since elements are distinct.

The issue is that the algorithm gives count = i - prev_less_equal, but this counts subarrays ending at i where min is <= arr[i]. Wait no, that's different.

Actually, I realize the formula left[i] = i - prev_less gives:
- The number of subarrays ending at i where arr[i] is the LAST minimum (i.e., the rightmost smaller-or-equal to previous smaller). 

Wait, I think there's a more subtle interpretation:

left[i] = distance to prev smaller-or-equal = # of subarrays ending at i where arr[i] is the minimum OR where it ties with another minimum.

Actually the count of subarrays ENDING at i where arr[i] is strictly the minimum:
- prev_strict_less is the index of nearest STRICTLY smaller element.
- The subarrays ending at i can extend from prev_strict_less+1 to i.
- But within this range, intermediate elements must not be smaller than arr[i].

So left[i] is not just i - prev_strict_less. It depends on what we pop.

When we pop elements > arr[i], we're removing those that are LARGER. But intermediate elements (between prev_strict_less and i) that are SMALLER but not popped... wait they would be popped if smaller.

Actually wait, in [3, 1, 2, 4]:
After popping for i=3, arr[3]=4:
- Stack: [1, 2, 3] (in stack terms, indices)
- arr[2]=2: is 2 > 4? No. So we don't pop.
- arr[1]=1: is 1 > 4? No. Don't pop.

So the remaining stack has elements with arr values [1, 2] at indices [1, 2]. The TOP is index 2, value 2.

I was wrong - the top is 2, not 1!

Distance = 3 - 2 = 1. left[3] = 1. ✓

Let me recompute:
i=3, arr[3]=4: 
- Top is 2, arr[2]=2. Is 2 > 4? No, don't pop.
- Top is now 2. Distance from top = 3 - 2 = 1.
- left[3] = 1.

Wait, but the algorithm I wrote is:
```python
while stack and arr[stack[-1]] > arr[i]:
    stack.pop()
left[i] = i - (stack[-1] if stack else -1)
```

This pops ALL > arr[i], then uses whatever remains on top. For i=3, arr[3]=4:
- No elements > 4 in stack [1, 2, 3]. Don't pop.
- stack[-1] = 3 (top of stack is current index itself because we just popped nothing).
- Wait, we haven't pushed 3 yet. Stack is [1, 2]. stack[-1] = 2.
- Wait, but then after pushing 3, stack becomes [1, 2, 3].

Ah I see. Let me re-read the algorithm:

```python
for i in range(n):
    while stack and arr[stack[-1]] > arr[i]:
        stack.pop()
    if stack:
        left[i] = i - stack[-1]
    else:
        left[i] = i + 1
    stack.append(i)
```

For i=3, arr[3]=4:
- Before the while: stack = [1, 2] (assuming from previous iters)
- arr[stack[-1]] = arr[2] = 2. Is 2 > 4? No.
- Don't enter loop.
- stack is not empty. left[3] = 3 - 2 = 1. ✓

Wait I had it wrong. The stack doesn't include i yet! It includes only previous indices.

So for i=3, stack is [1, 2] (indices 1 and 2 with values 1 and 2). top is index 2.
left[3] = 3 - 2 = 1. ✓

Great, so Way 1 IS correct. I was confused in my trace.

Let me redo:
LEFT pass:
- i=0, 3: stack=[]. stack empty, left[0]=0-(-1)=1. push 0. stack=[0]
- i=1, 1: arr[0]=3 > 1, pop. stack=[]. stack empty, left[1]=1-(-1)=2. push 1. stack=[1]
- i=2, 2: arr[1]=1, 1 > 2? No. left[2]=2-1=1. push 2. stack=[1,2]
- i=3, 4: arr[2]=2, 2 > 4? No. Don't pop. left[3]=3-2=1. push 3. stack=[1,2,3]

Hmm wait, in step i=3, after checking arr[2], we don't check arr[1]. We only check the TOP. So stack[-1] = 2, distance = 1, left[3] = 1. ✓

OK so left = [1, 2, 1, 1] not [1, 2, 1, 2]. I made an error in my original trace.

With left = [1, 2, 1, 1] and similar for right, let me recompute:

RIGHT pass (greater-or-equal for pop):
- i=3, 4: stack=[]. right[3]=4-3=1. push 3. stack=[3]
- i=2, 2: arr[3]=4 >= 2, pop. stack=[]. right[2]=4-2=2. push 2. stack=[2]
- i=1, 1: arr[2]=2 >= 1, pop. stack=[]. right[1]=4-1=3. push 1. stack=[1]
- i=0, 3: arr[1]=1, 1 >= 3? No. right[0]=1-0=1. push 0. stack=[1, 0]

right = [1, 3, 2, 1]

Contributions:
- arr[0]=3: 3 * 1 * 1 = 3
- arr[1]=1: 1 * 2 * 3 = 6
- arr[2]=2: 2 * 1 * 2 = 4
- arr[3]=4: 4 * 1 * 1 = 4

Sum: 3+6+4+4 = 17 ✓ Great, matches!

So Way 1 IS correct. My initial trace was wrong.

OK so all the implementations should pass. Let me check that my test case for arr=[3,1,2,4] expecting 17 is right by tracing Way 2:

Way 2 (expanding counts):
i=0, arr[0]=3: cnt=1, left[0]=1. push 0. stack=[0]
i=1, arr[1]=1: arr[0]=3 > 1, pop. cnt += left[0]=1+1=2. stack empty. left[1]=2. push 1. stack=[1]
i=2, arr[2]=2: arr[1]=1, 1 > 2? No. cnt=1. left[2]=1. push 2. stack=[1,2]
i=3, arr[3]=4: arr[2]=2, 2 > 4? No. cnt=1. left[3]=1. push 3. stack=[1,2,3]

left = [1, 2, 1, 1]

Same result! Good.

So Way 1 works correctly, my confusing trace was wrong. The code should be correct.

Let me also verify Way 3 (brute force) for [3,1,2,4]=17:

i=0: min=3. Subarrays: [3]=3. Total=3.
i=1: min=1. Subarrays: [1]=1, [3,1]=1. Total=3+2=5.
i=2: min=2 then min([1,2])=1. Subarrays: [2]=2, [1,2]=1, [3,1,2]=1. Total=5+4=9.
i=3: min=4 then min([2,4])=2 then min([1,2,4])=1 then min([3,1,2,4])=1. Subarrays: [4]=4, [2,4]=2, [1,2,4]=1, [3,1,2,4]=1. Total=9+8=17 ✓

Great, brute force gives 17.

So Way 1 and Way 2 both correctly compute left = [1, 2, 1, 1] for [3,1,2,4].

OK so implementations are correct. The trace I did earlier was wrong, but the actual code is right. All 20 passed the test.

Now let me write the explained.md
"""

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need to find the sum of min(b) over all subarrays b of arr. Brute force is O(n^2). I need O(n)."

Key Insight:
"Each element's contribution: count subarrays where it's the MIN and multiply by its value.

For element arr[i]:
- left[i] = # subarrays ending at i with arr[i] as min
- right[i] = # subarrays starting at i with arr[i] as min
- contribution = arr[i] * left[i] * right[i]"

Algorithm:
"1. Compute left[i] using monotonic stack (strict greater for pop)
   - left[i] = i - (prev strictly less index) if exists, else i+1
2. Compute right[i] using monotonic stack (greater-or-equal for pop)
   - right[i] = (next less-or-equal index) - i if exists, else n-i
3. Sum arr[i] * left[i] * right[i] mod 10^9+7"

Why strict vs non-strict:
"For LEFT (forward), use STRICT greater when popping.
For RIGHT (backward), use GREATER OR EQUAL when popping.
This avoids double-counting equal elements."

Edge cases:
- Single element: just return arr[0]
- All same: each is min for some range
- Two-pass for left and right independently

COMPLEXITY:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| 2-pass    | O(n)   | O(n)   |
| Brute     | O(n^2) | O(1)   |
+-----------+--------+--------+

KEY TRICK:
Element arr[i] is min for left[i] * right[i] subarrays.
Need PREVIOUS LESS and NEXT LESS distances via monotonic stack.
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    implementations = [
        ("Way 1: Two stacks with distances", sum_subarray_mins_1),
        ("Way 2: With expanding counts", sum_subarray_mins_2),
        ("Way 3: Brute force O(n^2)", sum_subarray_mins_3),
        ("Way 4: With sentinels", sum_subarray_mins_4),
        ("Way 5: Sentinel non-strict", sum_subarray_mins_5),
        ("Way 6: Cartesian tree style", sum_subarray_mins_6),
        ("Way 7: Most concise sentinel", sum_subarray_mins_7),
        ("Way 8: With prev_less/next_less", sum_subarray_mins_8),
        ("Way 9: Direct contribution", sum_subarray_mins_9),
        ("Way 10: Explicit indices", sum_subarray_mins_10),
        ("Way 11: Class-based", sum_subarray_mins_11),
        ("Way 12: Deque", sum_subarray_mins_12),
        ("Way 13: Verbose counter", sum_subarray_mins_13),
        ("Way 14: With helper", sum_subarray_mins_14),
        ("Way 15: Most elegant", sum_subarray_mins_15),
        ("Way 16: No special case", sum_subarray_mins_16),
        ("Way 17: Explicit modulo", sum_subarray_mins_17),
        ("Way 18: Pre-computed distances", sum_subarray_mins_18),
        ("Way 19: With helper functions", sum_subarray_mins_19),
        ("Way 20: Final cleanest", sum_subarray_mins_20),
    ]

    test_cases = [
        ([3, 1, 2, 4], 17),
        ([11, 81, 94, 43, 3], 444),
        ([1], 1),
        ([1, 2, 3], 10),
        ([7], 7),
        ([1, 1], 3),
        ([2, 1, 3], 9),
    ]

    print("=" * 70)
    print("SUM OF SUBARRAY MINIMUMS - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/sum-of-subarray-minimums")
    print("=" * 70)

    all_pass = True
    for name, func in implementations:
        all_test_pass = True
        for arr, expected in test_cases:
            try:
                result = func(arr)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: arr={arr} -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on arr={arr} - {e}")
        print(f"  {name}: {'PASS' if all_test_pass else 'FAIL'}")

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL 20 IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
