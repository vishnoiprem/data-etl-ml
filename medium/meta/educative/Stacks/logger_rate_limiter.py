"""
Logger Rate Limiter
Easy | 15 min

Design a logger system that receives a stream of messages with timestamps.
Each message should be printed if it has not been printed in the last 10
seconds. All messages will come in chronological order.

Implement the Logger class:
    Logger() initializes the logger
    shouldPrintMessage(timestamp, message):
        Returns True if message should be printed, False otherwise.

If message was already printed and last print time was within last 10
seconds, return False. Otherwise return True.

Examples:
    Logger logger = Logger()
    logger.shouldPrintMessage(1, "foo")     // True
    logger.shouldPrintMessage(2, "bar")     // True
    logger.shouldPrintMessage(3, "foo")     // False (already printed < 10s ago)
    logger.shouldPrintMessage(8, "bar")     // False
    logger.shouldPrintMessage(10, "foo")    // False
    logger.shouldPrintMessage(11, "foo")    // True (>= 10s since last)

Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/logger-rate-limiter

Constraints:
- 0 <= timestamp <= 10^9
- "hello" <= message <= "world" (length up to 20)
- At most 10^4 calls to shouldPrintMessage
- Messages are unique (or not? we handle both cases by using last print time)
"""


# =============================================================================
# WAY 1: Hash map of message -> last_print_time (BEST - Memorize!)
# =============================================================================
class Logger1:
    def __init__(self):
        self.msg_log = {}  # message -> last timestamp when printed

    def shouldPrintMessage(self, timestamp, message):
        if message not in self.msg_log:
            self.msg_log[message] = timestamp
            return True
        if timestamp - self.msg_log[message] >= 10:
            self.msg_log[message] = timestamp
            return True
        return False


# Functional version
def logger_rate_limiter_1(timestamps_messages):
    """Functional: process list of (timestamp, message)."""
    msg_log = {}
    results = []
    for ts, msg in timestamps_messages:
        if msg not in msg_log or ts - msg_log[msg] >= 10:
            results.append(True)
            msg_log[msg] = ts
        else:
            results.append(False)
    return results


# =============================================================================
# WAY 2: defaultdict
# =============================================================================
class Logger2:
    def __init__(self):
        from collections import defaultdict
        self.msg_log = defaultdict(lambda: -10)

    def shouldPrintMessage(self, timestamp, message):
        if timestamp - self.msg_log[message] >= 10:
            self.msg_log[message] = timestamp
            return True
        return False


# =============================================================================
# WAY 3: With set of recent messages
# =============================================================================
class Logger3:
    def __init__(self):
        self.msg_log = {}  # message -> last print time

    def shouldPrintMessage(self, timestamp, message):
        # Always update if returning True
        old_time = self.msg_log.get(message, -11)
        if timestamp - old_time >= 10:
            self.msg_log[message] = timestamp
            return True
        return False


# =============================================================================
# WAY 4: Functional with dict operations
# =============================================================================
def make_logger_4():
    state = {'log': {}}
    def should_print(timestamp, message):
        log = state['log']
        last = log.get(message, -11)
        if timestamp - last >= 10:
            log[message] = timestamp
            return True
        return False
    return should_print


# =============================================================================
# WAY 5: Class with timing tracking
# =============================================================================
class Logger5:
    def __init__(self):
        self.last_printed = {}

    def shouldPrintMessage(self, timestamp, message):
        if message not in self.last_printed:
            self.last_printed[message] = timestamp
            return True
        elapsed = timestamp - self.last_printed[message]
        if elapsed >= 10:
            self.last_printed[message] = timestamp
            return True
        return False


# =============================================================================
# WAY 6: Try/except KeyError
# =============================================================================
class Logger6:
    def __init__(self):
        self.log = {}

    def shouldPrintMessage(self, timestamp, message):
        try:
            last = self.log[message]
            if timestamp - last < 10:
                return False
        except KeyError:
            pass
        self.log[message] = timestamp
        return True


# =============================================================================
# WAY 7: Lambda-based
# =============================================================================
def make_logger_7():
    log = {}
    def should_print(ts, msg):
        if log.get(msg, -11) + 10 <= ts:
            log[msg] = ts
            return True
        return False
    return should_print


# =============================================================================
# WAY 8: Simple with get default -99
# =============================================================================
class Logger8:
    def __init__(self):
        self.log = {}

    def shouldPrintMessage(self, timestamp, message):
        if self.log.get(message, -99) + 10 <= timestamp:
            self.log[message] = timestamp
            return True
        return False


# =============================================================================
# WAY 9: With explicit reset
# =============================================================================
class Logger9:
    def __init__(self):
        self.last_time = {}

    def shouldPrintMessage(self, timestamp, message):
        prev_time = self.last_time.get(message)
        if prev_time is None or timestamp - prev_time >= 10:
            self.last_time[message] = timestamp
            return True
        return False


# =============================================================================
# WAY 10: With __slots__ optimization
# =============================================================================
class Logger10:
    __slots__ = ('msg_log',)

    def __init__(self):
        self.msg_log = {}

    def shouldPrintMessage(self, timestamp, message):
        last = self.msg_log.get(message, -11)
        if timestamp - last >= 10:
            self.msg_log[message] = timestamp
            return True
        return False


# =============================================================================
# WAY 11: Using setrecursionlimit - not relevant, skip to other variants
# Way 11: Most concise
# =============================================================================
class Logger11:
    def __init__(self):
        self.seen = {}

    def shouldPrintMessage(self, timestamp, message):
        if self.seen.get(message, -10) + 10 <= timestamp:
            self.seen[message] = timestamp
            return True
        return False


# =============================================================================
# WAY 12: As a single function
# =============================================================================
def logger_rate_limiter_12(init_log=None):
    """Factory function returning a closure."""
    log = init_log if init_log is not None else {}
    def should_print(timestamp, message):
        last = log.get(message, -10)
        if timestamp - last >= 10:
            log[message] = timestamp
            return True
        return False
    return should_print


# =============================================================================
# WAY 13: Two state dict (current + next_clear)
# =============================================================================
class Logger13:
    def __init__(self):
        self.log = {}

    def shouldPrintMessage(self, timestamp, message):
        last = self.log.get(message)
        if last is None or timestamp - last >= 10:
            self.log[message] = timestamp
            return True
        return False


# =============================================================================
# WAY 14: With helper method
# =============================================================================
class Logger14:
    def __init__(self):
        self.log = {}

    def _can_print(self, message, timestamp):
        return message not in self.log or timestamp - self.log[message] >= 10

    def shouldPrintMessage(self, timestamp, message):
        if self._can_print(message, timestamp):
            self.log[message] = timestamp
            return True
        return False


# =============================================================================
# WAY 15: Using negative infinity default
# =============================================================================
class Logger15:
    def __init__(self):
        self.log = {}

    def shouldPrintMessage(self, timestamp, message):
        import math
        last = self.log.get(message, -math.inf)
        if timestamp - last >= 10:
            self.log[message] = timestamp
            return True
        return False


# =============================================================================
# WAY 16: With separate update and check
# =============================================================================
class Logger16:
    def __init__(self):
        self.log = {}

    def shouldPrintMessage(self, timestamp, message):
        last_time = self.log.get(message, -10)
        eligible = timestamp - last_time >= 10
        if eligible:
            self.log[message] = timestamp
        return eligible


# =============================================================================
# WAY 17: Using OrderedDict (for FIFO if needed)
# =============================================================================
class Logger17:
    def __init__(self):
        self.log = {}

    def shouldPrintMessage(self, timestamp, message):
        last = self.log.get(message, -11)
        if last + 10 <= timestamp:
            self.log[message] = timestamp
            return True
        return False


# =============================================================================
# WAY 18: Most minimal
# =============================================================================
class Logger18:
    def __init__(self):
        self.d = {}

    def shouldPrintMessage(self, t, m):
        if self.d.get(m, -10) + 10 <= t:
            self.d[m] = t
            return True
        return False


# =============================================================================
# WAY 19: With docstring and explicit timing
# =============================================================================
class Logger19:
    """Logger that limits message printing to once per 10 seconds."""
    RATE_LIMIT = 10

    def __init__(self):
        self.last_time = {}

    def shouldPrintMessage(self, timestamp, message):
        last = self.last_time.get(message)
        should_print = last is None or timestamp - last >= self.RATE_LIMIT
        if should_print:
            self.last_time[message] = timestamp
        return should_print


# =============================================================================
# WAY 20: Final cleanest
# =============================================================================
class Logger20:
    def __init__(self):
        self.last_print = {}

    def shouldPrintMessage(self, timestamp, message):
        if timestamp - self.last_print.get(message, -10) >= 10:
            self.last_print[message] = timestamp
            return True
        return False


# =============================================================================
# HOW I THINK - SAY ALOUD IN INTERVIEW
# =============================================================================

HOW_TO_THINK = """
WHAT TO SAY ALOUD IN THE INTERVIEW:

Opening:
"I need a Logger class that decides whether each message should be
printed based on a 10-second rate limit."

Key Insight:
"Use a HASH MAP of message -> last_print_time!
- If message not in map: print, store current timestamp.
- If in map and current - last >= 10: print, update timestamp.
- Otherwise: don't print."

Algorithm:
"1. Initialize self.msg_log = {}
2. shouldPrintMessage(timestamp, message):
   - last_time = self.msg_log.get(message, -10)
   - if timestamp - last_time >= 10:
     * self.msg_log[message] = timestamp
     * return True
   - return False"

Why get(..., -10):
"Default of -10 means FIRST message always passes the check
(current_ts - (-10) = current_ts + 10 >= 10)."

Why this works:
"The hash map tracks when each message was last printed.
If 10+ seconds have passed since last print, print it again.
Otherwise, suppress it."

Edge cases:
- First time message: passes (default -10)
- Same message at exact 10s: passes (>= 10)
- Message at exact same timestamp: fails (< 10)
- Different message at same time: independent tracking

COMPLEXITY:
+-----------+--------+--------+
| Approach  | Time   | Space  |
+-----------+--------+--------+
| Hash map  | O(1)   | O(n)   |
+-----------+--------+--------+
"""


# =============================================================================
# TEST ALL IMPLEMENTATIONS
# =============================================================================
if __name__ == "__main__":
    logger_classes = [
        ("Way 1: Hash map class", Logger1),
        ("Way 2: defaultdict", Logger2),
        ("Way 3: Get with default", Logger3),
        ("Way 5: Class with timing", Logger5),
        ("Way 6: Try/except", Logger6),
        ("Way 8: Get with -99", Logger8),
        ("Way 9: Explicit None", Logger9),
        ("Way 10: __slots__", Logger10),
        ("Way 11: Most concise", Logger11),
        ("Way 13: Two state dict", Logger13),
        ("Way 14: Helper method", Logger14),
        ("Way 15: Negative inf default", Logger15),
        ("Way 16: Separate update", Logger16),
        ("Way 17: OrderedDict-like", Logger17),
        ("Way 18: Most minimal", Logger18),
        ("Way 19: With docstring", Logger19),
        ("Way 20: Final cleanest", Logger20),
    ]

    test_cases = [
        # (timestamp, message, expected)
        (1, "foo", True),
        (2, "bar", True),
        (3, "foo", False),  # foo at ts 1, only 2s ago
        (8, "bar", False),  # bar at ts 2, only 6s ago
        (10, "foo", False),  # foo at ts 1, 9s ago. < 10
        (11, "foo", True),  # foo at ts 1, 10s ago. >= 10
        (12, "bar", True),  # bar at ts 2, 10s ago. >= 10
    ]

    print("=" * 70)
    print("LOGGER RATE LIMITER - ALL 20 IMPLEMENTATIONS")
    print("Reference: https://www.educative.io/courses/grokking-coding-interview-in-python/logger-rate-limiter")
    print("=" * 70)

    all_pass = True
    for name, cls in logger_classes:
        logger = cls()
        all_test_pass = True
        for ts, msg, expected in test_cases:
            try:
                result = logger.shouldPrintMessage(ts, msg)
                if result != expected:
                    all_test_pass = False
                    all_pass = False
                    print(f"  X {name}: ts={ts}, msg='{msg}' -> {result} (expected {expected})")
            except Exception as e:
                all_test_pass = False
                all_pass = False
                print(f"  X {name}: ERROR on ts={ts}, msg='{msg}' - {e}")
        print(f"  {name}: {'PASS' if all_test_pass else 'FAIL'}")

    # Test functional versions
    print()
    functional_ways = [
        ("Way 1 (functional)", logger_rate_limiter_1),
    ]

    print("=" * 70)
    print("LOGGER RATE LIMITER - FUNCTIONAL")
    print("=" * 70)
    for name, fn in functional_ways:
        try:
            results = fn([(ts, msg) for ts, msg, _ in test_cases])
            expected_list = [expected for _, _, expected in test_cases]
            if results == expected_list:
                print(f"  {name}: PASS")
            else:
                print(f"  X {name}: results={results} expected={expected_list}")
                all_pass = False
        except Exception as e:
            print(f"  X {name}: ERROR - {e}")
            all_pass = False

    # Test closure versions
    print()
    closure_ways = [
        ("Way 4: Closure", make_logger_4),
        ("Way 7: Lambda", make_logger_7),
        ("Way 12: Factory", logger_rate_limiter_12),
    ]

    print("=" * 70)
    print("LOGGER RATE LIMITER - CLOSURES")
    print("=" * 70)
    for name, fn in closure_ways:
        should_print = fn()
        try:
            results = []
            for ts, msg, _ in test_cases:
                results.append(should_print(ts, msg))
            expected_list = [expected for _, _, expected in test_cases]
            if results == expected_list:
                print(f"  {name}: PASS")
            else:
                print(f"  X {name}: results={results} expected={expected_list}")
                all_pass = False
        except Exception as e:
            print(f"  X {name}: ERROR - {e}")
            all_pass = False

    print("\n" + "=" * 70)
    if all_pass:
        print("ALL IMPLEMENTATIONS PASS!")
    else:
        print("Some implementations need fixing")
    print("=" * 70)
    print(HOW_TO_THINK)
