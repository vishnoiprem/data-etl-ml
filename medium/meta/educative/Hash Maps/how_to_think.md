# How to Think Beyond Brute Force

The **most important skill** for coding interviews. Here's a framework you can apply to ANY problem.

## The Mindset Shift

| Brute Force Thinking | Smart Thinking |
|---------------------|----------------|
| Try every combination | **What info do I actually need?** |
| Check all possibilities | **Can I avoid work I already did?** |
| Re-compute everything | **Can I remember results?** |

## 5 Patterns to Think About

### Pattern 1: "Did I Already Compute This?"
**Trigger words:** "subarray sum", "count paths", "number of ways"

**Ask yourself:** Am I doing the same calculation many times?

```
nums = [1, 2, 3]
Sum from index 0 to 2 = 6
Sum from index 1 to 2 = 5  <- don't recalculate, save prefix sums!
```

**Tool:** Hashmap / array to store past results.

### Pattern 2: "Can I Trade Space for Time?"
**Trigger:** Brute force is too slow but the answer is obvious.

```
Brute: O(n^2) check every pair
Smart: O(n) using hashmap lookup  <- pays memory to save time
```

### Pattern 3: "Can I Shrink the Problem?"
**Trigger:** Big problem feels similar to smaller problem.

```
3Sum = fix one number + solve 2Sum
4Sum = fix two numbers + solve 2Sum
```

**Ask:** "If I lock in part of the answer, does the rest become easier?"

### Pattern 4: "Can I Sort?"
**Trigger:** You don't care about original order, OR you need to find pairs.

```
Without sort: any pair? O(n^2)
With sort: two pointers! O(n)
```

**Sort enables:** two pointers, binary search, merging, deduplication.

### Pattern 5: "Can I Go From One End?"
**Trigger:** Need to find something at the END, or compare ends.

```
Two pointers:
- Left and right meet in middle (palindrome, two sum)
- Fast and slow (cycle detection, nth from end)
```

## Decision Flowchart

```
Start
  v
"Try every combination"
  v
Can I SORT first? --YES--> Two pointers? Hashmap?
  v NO                          |
                          Works? -> DONE
                            v NO
                      Try another pattern
```

## Real Examples

### Example: Subarray Sum K
**Brute force:** Check every subarray = O(n^2)
**Smart thought:** "I keep adding up numbers. What if I just remember the running sum?"
- -> Prefix sum + hashmap -> O(n) ✓

### Example: Two Sum
**Brute force:** Check every pair = O(n^2)
**Smart thought:** "I need to find if target - num exists. What if I remember numbers I've seen?"
- -> Hashmap -> O(n) ✓

### Example: 3Sum
**Brute force:** Check every triplet = O(n^3)
**Smart thought:** "If I fix one number, it becomes 2Sum!"
- -> Sort + two pointers -> O(n^2) ✓

### Example: Nth from End
**Brute force:** Count length, then walk again = 2 passes
**Smart thought:** "What if I start one pointer n steps ahead?"
- -> Two pointers, 1 pass ✓

## Practice Questions to Ask Yourself

When you see a problem, literally ask:

1. **"Can I sort?"** -> enables two pointers, binary search
2. **"Am I repeating work?"** -> hashmap, DP
3. **"Does part of it look like a smaller version?"** -> recursion
4. **"Is the answer at the ends?"** -> two pointers
5. **"Can I build up to the answer?"** -> prefix sums, running totals

## How to Practice This Thinking

1. **Solve the brute force first** - get the right answer
2. **Ask:** "What did I do over and over?"
3. **Ask:** "What info would have made this faster?"
4. **Build that structure** (hashmap, sorted array, etc.)

The more problems you do this with, the faster you'll recognize patterns!
