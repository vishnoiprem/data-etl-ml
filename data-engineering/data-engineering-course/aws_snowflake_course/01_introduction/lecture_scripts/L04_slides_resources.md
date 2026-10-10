---
l_id: L04
title: All course slides & resources
duration: "5:00"
prereqs: ["L03"]
downloads: []
---

# L04 — All Course Slides & Resources

> **Author:** Prem Vishnoi <pvishnoi@avilx.com>
> **Section:** 1 — Introduction
> **Duration:** ~5:00

## Prereqs

L01–L03. This is the last orientation lecture before we get to
the free trial in L05.

## Lecture

This lecture is the single reference for every downloadable
artifact in the course. I'll group them by folder and tell you
when in the course you'll use each one.

### Repo layout at a glance

```text
aws_snowflake_course/
├── 01_introduction/      ← you are here (L01–L04)
├── 02_getting_started/   ← free trial, UI, warehouses (L05–L14)
├── 03_snowflake_architecture/  (L15–L23)
├── 04_loading_data/      (L24–L32)
├── 05_copy_options/      (L33–L40)
├── …                      (sections 06–20, future content)
├── assignments/          ← 4 graded assignments
├── code/                 ← 19 working SQL demos + 5 Python test suites
├── diagrams/             ← 6 architecture diagrams (Mermaid)
├── downloads/            ← slide decks, cheat sheets, sample CSVs
├── quizzes/              ← 19 section quizzes
├── scripts/              ← helper shell / Python scripts
├── CHANGELOG.md
├── DIRECTORY.md
├── README.md
├── SYLLABUS.md
└── requirements.txt
```

### Downloads

The `downloads/` folder contains slide decks, cheat sheets, and
sample CSV/JSON files you'll need for the labs. Each lecture's
front-matter lists which download it references. The three you'll
use most often:

- **`snowflake_cheat_sheet.pdf`** — single-page reference for
  account objects, warehouse sizing, `COPY INTO` syntax, and
  Snowpipe limits. Print it.
- **`sample_data.zip`** — small CSVs and JSON files used in the
  loading-data labs (sections 4–5).
- **`slides_*.pdf`** — slide decks per section, if you prefer
  slides to scripts.

### Code demos

The `code/` folder has 19 working SQL demos. The pattern is one
SQL file per section, named like `s04_loading_data.sql`. Each
file is **executable end-to-end** in your Snowflake account — it
creates the demo database, the demo warehouse, runs the load,
and prints summary results. We will not use Python in this course;
the focus is SQL.

### Assignments

Four assignments in `assignments/`:

1. **`01_warehouses.md`** — design and create warehouses for
   three different workloads.
2. **`02_loading.md`** — load a CSV + JSON file into Snowflake
   using the `COPY INTO` command.
3. **`03_performance.md`** — diagnose a slow query using the
   query profile and warehouse history.
4. **`04_sharing.md`** — set up a share with a reader account
   and consume it from a second account.

Each assignment has a starter file, an autograder (where
possible), and a rubric. Assignments are **optional** but they
are the closest thing to a real-world Snowflake interview
exercise.

### Diagrams

Six Mermaid diagrams in `diagrams/`:

1. `01_three_layer_architecture.mmd` — storage / compute /
   cloud services.
2. `02_data_sharing.mmd` — provider / consumer account flow.
3. `03_zero_copy_clone.mmd` — clone vs copy trade-offs.
4. `04_snowpipe.mmd` — auto-ingest + cloud notifications.
5. `05_stream_task.mmd` — CDC pattern with streams + tasks.
6. `06_cortex_ai.mmd` — Cortex AI / ML surface area.

Mermaid is plain text, so you can edit them in any editor; they
render in GitHub, VS Code (with the Mermaid extension), and
Obsidian.

### The scripts folder

The `scripts/` folder has helper scripts:

- **`bootstrap_free_trial.sh`** — automate the initial SQL you
  run after signing up (create admin user, create demo database,
  set default warehouse).
- **`reset_demo.sql`** — drop and recreate all demo objects in
  one statement. Use it between labs.

### How the resources fit together

- **Lectures teach concepts.** Each lecture is the *why*.
- **Downloads give you data + references.** Each lab needs them.
- **Code demos show you the *how*** — the SQL patterns you'll
  actually type.
- **Assignments force you to build without a script.** This is
  where real learning happens.
- **Diagrams** give you the mental model.
- **Quizzes** tell you whether you actually understood.

## Hands-on

```bash
# Skim the repo structure
ls /Users/vishnoiprem/PycharmProjects/data-etl-ml/data-engineering/data-engineering-course/aws_snowflake_course/
```

## Quiz prep

For this lecture, focus on the **resource-locator** questions:

- Where do the SQL demos live? (`code/`)
- Where do the assignments live? (`assignments/`)
- Where do the Mermaid diagrams live? (`diagrams/`)

## What's next

Next up is **L05 — Sign up for free trial**, the first lecture in
Section 2. From here on out every lecture has a real hands-on lab.
