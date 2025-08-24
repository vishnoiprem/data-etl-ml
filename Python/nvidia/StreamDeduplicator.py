from collections import deque
import time

class StreamDeduplicator:
    def __init__(self, window_minutes=10):
        self.window_sec = window_minutes * 60  # 10 minutes = 600 seconds
        self.seen = {}  # {event_id: last_seen_timestamp}
        self.queue = deque()  # [(event_id, timestamp)]

    def process_event(self, event_id):
        now = time.time()

        # Step 1: Evict expired events (older than window)
        while self.queue and now - self.queue[0][1] > self.window_sec:
            old_id, old_ts = self.queue.popleft()
            if self.seen.get(old_id) == old_ts:
                del self.seen[old_id]

        # Step 2: Check if this event is a duplicate in the current window
        if event_id in self.seen:
            # It was seen recently → suppress
            print(f"[SUPPRESSED] Event '{event_id}' at {now:.0f} (already seen)")
            return False

        # Step 3: Emit the event
        self.seen[event_id] = now
        self.queue.append((event_id, now))
        print(f"[EMITTED] Event '{event_id}' at {now:.0f}")
        return True


# ——————————————————————
# ✅ Example Usage
# ——————————————————————

# Simulate incoming events over time
dedup = StreamDeduplicator(window_minutes=10)

events = [
    ("A", 0),   # Now + 0 sec
    ("B", 10),  # +10 sec
    ("A", 500), # +500 sec → ~8 min 20 sec → still within 10-min window
    ("A", 650), # +650 sec → ~10 min 50 sec → outside window!
    ("C", 700), # +700 sec → ~11 min 40 sec → OK
    ("B", 1200), # +1200 sec → ~20 min → B was seen at 10 sec → expired
]

print("Starting stream...\n")
for event_id, delay in events:
    time.sleep(delay)  # Simulate time passing
    dedup.process_event(event_id)