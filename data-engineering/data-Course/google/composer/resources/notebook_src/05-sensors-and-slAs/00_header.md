#! number: 05
#! title: Sensors & SLAs
#! module: Module 2 · Reliability & Operations
#! lecture: Lecture 2.1–2.3

- Understand what a sensor really is: a **task that waits**, and the two ways it can wait
- Compare `mode="poke"` and `mode="reschedule"` by their worker-slot economics
- Learn the difference between `timeout`, `execution_timeout`, `retries` and an **SLA**
- Measure an SLA against the **data interval end**, not wall-clock now
- Build an `sla_miss_callback` and an SLA compliance tracker
