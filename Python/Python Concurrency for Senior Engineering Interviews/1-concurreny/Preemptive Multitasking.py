
# 1. Preemptive Multitasking (threading)
import threading
import time

def task(name):
    for i in range(3):
        print(f"[{name}] Working step {i}")
        # simulate CPU work with a blocking sleep
        time.sleep(0.1)

# Create two threads
t1 = threading.Thread(target=task, args=("Thread-1",))
t2 = threading.Thread(target=task, args=("Thread-2",))

# The OS preemptively schedules and switches between t1 and t2
t1.start()
t2.start()

t1.join()
t2.join()