# Apache Airflow Track — Course Curricula (Verbatim Outlines)

**Source attribution:** Course outlines from Data Vidhya (https://datavidhya.com/)
by **Darshil Parmar (Founder, Data Vidhya)**.

Reproduced in `data-enginnering-cloudvala/course-curricula/` as study-path
references. Outlines are verbatim; no editorial wrapping added.

This file aggregates the Airflow courses:

1. Airflow Fundamentals Course (21 lessons)
2. Intermediate Airflow Course (24 lessons)

**Combined: 45 lessons across 6 modules.**

---

## 1. Airflow Fundamentals Course

**Tagline:** Learn workflow orchestration from the ground up — Airflow
architecture, local setup, DAG authoring, tasks, operators, dependencies, and
sensors.
**Coverage:** 4 modules • 21 lessons
**Prerequisites:** Python Fundamentals

### Module 1: Introduction — 4 lessons

1. What is a Data Pipeline? — *Video*
2. Pipelines & Orchestration — *Article*
3. Introduction to Apache Airflow — *Video*
4. Quiz: Introduction — *Article*

### Module 2: Architecture & Concepts — 4 lessons

1. Airflow Architecture — *Article*
2. Reasons to Choose and Not Choose Airflow — *Video*
3. When to Choose Airflow — and When NOT to — *Article*
4. Quiz: Architecture & Concepts — *Article*

### Module 3: Environment Setup — 6 lessons

1. Docker Theory — *Video*
2. Docker Hands-On — *Video*
3. Docker Image Building — *Video*
4. Airflow Installation — *Video*
5. Install Airflow with Docker — *Video*
6. Quiz: Environment Setup — *Article*

### Module 4: DAGs, Tasks & Operators — 7 lessons

1. Airflow UI Basics — *Video*
2. Airflow UI — *Article*
3. Writing Your First Airflow DAG — *Video*
4. Writing Your First Real DAG: A Data Pipeline from Scratch — *Article*
5. Tasks vs Operators — *Video*
6. Tasks vs Operators — Understanding the Difference — *Article*
7. Quiz: DAGs, Tasks & Operators — *(no format tag given)*

---

## 2. Intermediate Airflow Course

**Tagline:** Control complex workflows with scheduling semantics, backfills,
XComs, TaskFlow, branching, dynamic tasks, templating, sensors, and
API-triggered DAGs.
**Coverage:** 2 modules • 24 lessons
**Prerequisites:** Airflow Fundamentals

### Module 1: Scheduling & Execution — 8 lessons

1. Scheduling in Airflow — Part 1 — *Video*
2. Scheduling in Airflow — Part 2 — *Video*
3. In-Depth Scheduling: Cron Expressions, Timetables, Presets — *Article*
4. Incremental Data Loading with Execution Dates — *Video*
5. Understanding Airflow Execution Dates — *Video*
6. Backfilling to Fill the Gaps — *Video*
7. Atomicity and Idempotency — *Video*
8. Quiz: Scheduling & Execution — *Article*

### Module 2: Intermediate Airflow — 16 lessons

1. Operators and Templating — Part 1 — *Video*
2. Operators and Templating — Part 2 — *Video*
3. Branching, Fan-In & Fan-Out — *Video*
4. Branching in Airflow — *Video*
5. Branching: BranchPythonOperator and Conditional Workflows — *Article*
6. XCom — Sharing Data Between Tasks — *Video*
7. XCom — Passing Data Between Tasks — *Article*
8. TaskFlow API — *Video*
9. TaskFlow API: Writing Clean DAGs with @task Decorators — *Article*
10. Polling in Airflow — Part 1: Sensors — *Video*
11. Polling in Airflow — Part 2: Modes and Deadlocks — *Video*
12. Deferrable Operators and the Triggerer — *Article*
13. Executing Workflows Using REST API — *Video*
14. Trigger Airflow Using REST API — *Article*
15. Airflow CLI Essentials: Testing, Debugging, Managing DAGs — *Article*
16. Quiz: Intermediate Airflow — *(no format tag given)*
