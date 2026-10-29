# Logger Rate Limiter - 20 Ways with How to Think

**Reference:** https://www.educative.io/courses/grokking-coding-interview-in-python/logger-rate-limiter

## The Problem
```
Design a logger system that receives a stream of messages with timestamps.
Each unique message should be printed AT MOST once every 10 seconds.

All messages come in chronological order.

Implement:
    Logger() - constructor
    shouldPrintMessage(timestamp, message) -> bool

Return True if the message should be printed at this timestamp
(i.e., not printed in the last 10 seconds).

Examples:
    Logger logger = Logger()
    logger.shouldPrintMessage(1, "foo")     -> True   (first time)
    logger.shouldPrintMessage(2, "bar")     -> True   (new msg)
    logger.shouldPrintMessage(3, "foo")     -> False  (foo at 1, only 2s)
    logger.shouldPrintMessage(8, "bar")     -> False  (bar at 2, only 6s)
    logger.shouldPrintMessage(10, "foo")    -> False  (foo at 1, only 9s)
    logger.shouldPrintMessage(11, "foo")    -> True   (foo at 1, exactly 10s)

Constraints:
- 0 <= timestamp <= 10^9
- At most 10^4 calls to shouldPrintMessage
- Messages are unique within stream (or not - we handle both)
```

## How I Think (The Mental Process)

### Step 1: Understand the Problem
```
Each UNIQUE message has a 10-second rate limit.
- First time we see a message: always print.
- Same message within 10s: suppress.
- Same message after 10s: print again.

Simple: we just need to remember WHEN each message was last printed.
```

### Step 2: The Trick
> "Use a HASH MAP: message -> last_print_time!
> - On shouldPrintMessage(ts, msg):
>   - If msg NOT in map OR (ts - last_time) >= 10:
>     * Print (return True), update map[msg] = ts
>   - Else: don't print (return False)"

### Step 3: Why Hash Map?
> "Each message is INDEPENDENT - they don't interfere.
> The hash map gives O(1) lookup. We just need to track the last
> print time per message. No actual stack or queue needed."

---

## What to Say Aloud in the Interview

**Opening:**
> "I need a Logger class that decides whether each message should be
> printed based on a 10-second rate limit. Each unique message is
> independent."

**Key Insight:**
> "Use a HASH MAP: message -> last_print_time!
> - If message not in map: print, store current timestamp.
> - If in map and (current - last) >= 10: print, update timestamp.
> - Otherwise: don't print."

**Algorithm:**
> "1. Init self.msg_log = {}
> 2. shouldPrintMessage(timestamp, message):
>    - last = self.msg_log.get(message, -10)
>    - if timestamp - last >= 10:
>      * self.msg_log[message] = timestamp
>      * return True
>    - return False"

**Why get(..., -10):**
> "Default of -10 means FIRST message automatically passes the check:
> current_ts - (-10) = current_ts + 10, which is always >= 10."

**Why this works:**
> "The hash map tracks when each message was last printed.
> If 10+ seconds have passed since last print, print it again.
> Otherwise, suppress it. Different messages don't interfere."

**Edge cases:**
- First time message: passes (default -10 used)
- Same message at exact 10s: passes (>= 10 not > 10)
- Different messages at same time: independent tracking

**Complexity:**
- Time: O(1) per call (hash map lookup)
- Space: O(n) where n is number of unique messages

---

## The 20 Implementations (Simple to Complex)

### Way 1: Hash map class (BEST - Memorize!)
```python
class Logger:
    def __init__(self):
        self.msg_log = {}
    
    def shouldPrintMessage(self, timestamp, message):
        if message not in self.msg_log:
            self.msg_log[message] = timestamp
            return True
        if timestamp - self.msg_log[message] >= 10:
            self.msg_log[message] = timestamp
            return True
        return False
```

### Way 2: defaultdict (with default factory)
```python
from collections import defaultdict
class Logger:
    def __init__(self):
        self.msg_log = defaultdict(lambda: -10)
    
    def shouldPrintMessage(self, timestamp, message):
        if timestamp - self.msg_log[message] >= 10:
            self.msg_log[message] = timestamp
            return True
        return False
```

### Way 3: get(message, -11) variant

### Way 4: Closure (functional)
```python
def make_logger():
    state = {'log': {}}
    def should_print(ts, msg):
        if state['log'].get(msg, -11) + 10 <= ts:
            state['log'][msg] = ts
            return True
        return False
    return should_print
```

### Way 5-20: Various class implementations
- Different default values (-10, -11, -99, -inf)
- Different comparison styles (>= 10 vs last + 10 <= ts)
- Helper methods, __slots__ optimization, etc.

---

## Decision Tree

```
+------------------+------------+--------------+
| Scenario         | Best       | Why          |
+------------------+------------+--------------+
| Class-based      | Way 1      | Direct dict  |
| Functional       | Way 4      | Closure      |
+------------------+------------+--------------+
```

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Hash map | O(1) | O(n) |

---

## Walkthrough Example

```
Calls: (1, "foo"), (2, "bar"), (3, "foo"), (8, "bar"), (10, "foo"), (11, "foo")

State:
msg_log = {}

(1, "foo"):
- "foo" not in log.
- log["foo"] = 1
- return True

(2, "bar"):
- "bar" not in log.
- log["bar"] = 2
- return True

(3, "foo"):
- "foo" in log (last = 1).
- 3 - 1 = 2 < 10. Don't print.
- return False

(8, "bar"):
- "bar" in log (last = 2).
- 8 - 2 = 6 < 10. Don't print.
- return False

(10, "foo"):
- "foo" in log (last = 1).
- 10 - 1 = 9 < 10. Don't print.
- return False

(11, "foo"):
- "foo" in log (last = 1).
- 11 - 1 = 10 >= 10. Print.
- log["foo"] = 11
- return True
```

## Best Answer to Memorize

```python
class Logger:
    def __init__(self):
        self.msg_log = {}
    
    def shouldPrintMessage(self, timestamp, message):
        if timestamp - self.msg_log.get(message, -10) >= 10:
            self.msg_log[message] = timestamp
            return True
        return False
```

**7 lines. O(1) per call. Clean. Interview-ready!**

---

## Key Insights

### Why hash map, not stack?
> "Each message is independent - we don't need ordering. Hash map gives
> O(1) lookup. A stack wouldn't help here."

### Why get(message, -10)?
> "-10 ensures first message always passes (ts - (-10) >= 10 always).
> Other small defaults work too: -11, -99, etc."

### Why ">= 10" not "> 10"?
> "If message last printed at ts=1, and now it's ts=11, that's exactly
> 10 seconds elapsed. Should print again."

### Can we have hash collisions/cleanup?
> "In an infinite stream, log grows unbounded. For this problem,
> we don't clean up - it's bounded by 10^4 calls."

---

## Test Cases

| ts | msg | Expected | Why |
|----|-----|----------|-----|
| 1 | foo | True | First time |
| 2 | bar | True | Different msg |
| 3 | foo | False | Within 10s of foo (1) |
| 8 | bar | False | Within 10s of bar (2) |
| 10 | foo | False | 9s since foo (1) |
| 11 | foo | True | Exactly 10s |
| 12 | bar | True | Exactly 10s |

## Common Pitfalls

1. **Wrong default**: Using 0 instead of -10 means first call always fails!
2. **Wrong comparison**: >= 10 vs > 10 changes behavior at boundary.
3. **Not updating timestamp**: Must update when printing.
4. **Forget to handle missing key**: Use .get() with default.

## Why This Problem Matters

> "Tests:
> 1. Hash map design (CRITICAL)
> 2. Time-based decision (timestamp arithmetic)
> 3. Default value to handle missing keys
> 4. Pattern similar to: cache with TTL, sliding window with rate limit
> 5. Real-world: log deduplication, message throttling"
