#! number: 02
#! title: DAG Anatomy & Scheduling
#! module: Module 1 · Composer Fundamentals & Model
#! lecture: Lecture 1.3

- The anatomy of a `DAG` object — every parameter and what it actually controls
- Distinguish the **logical date**, the **data interval** and the **execution date**
- Internalise the half-open interval convention `[start, end)` and the off-by-one it prevents
- Understand `schedule`, `catchup`, `start_date` and `max_active_runs` and their interactions
- Build a schedule simulator you can run, so `catchup` stops being a mystery
