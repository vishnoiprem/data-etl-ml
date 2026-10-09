# Coding Interviews — Full Curriculum

A **fully working, runnable** Coding Interviews course covering **15 modules, 118 lessons, 28 videos**, with **103 working Python solutions and ~400+ unit tests**.

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
>
> Inspired by the coding interview prep used at top engineering organizations; every problem is implemented in clean Python with a unittest suite so you can run the entire track on your laptop.

## What's in this directory

```
coding_interviews/
├── README.md
├── 01_overview/                # 6 lessons (3 design, 3 code)
├── 02_complexity/              # 4 design lessons
├── 03_patterns/                # 8 design lessons
├── 04_arrays/                  # 12 problems
├── 05_hash_tables/             # 6 problems
├── 06_searching_sorting/       # 8 problems
├── 07_strings/                 # 9 problems
├── 08_graphs/                  # 9 problems
├── 09_trees/                   # 9 problems
├── 10_stacks_queues/           # 8 problems
├── 11_linked_lists/            # 6 problems
├── 12_heaps/                   # 5 problems
├── 13_recursion/               # 12 problems
├── 14_dp/                      # 10 problems
├── 15_mock_interviews/         # 6 mock interviews
└── exercise.md                 # 5 graded capstone problems
```

## How to use

Each module contains:
- `module_overview.md` — list of problems with links to the code files
- `code/` — one file per problem with a clean `solve_X(input) -> output` function
- `tests/` — `unittest.TestCase` files with 3-5 tests per problem

Run all the tests for this track:

```bash
cd data-engineering-course
python3 scripts/run_all_tests.py coding_interviews
```

Or run a single module's tests:

```bash
cd data-engineering-course
python3 -m unittest discover -s coding_interviews/04_arrays/tests -v
```

## Style conventions

- Function signature: `def solve_X(input) -> output`
- Docstring includes 1-line description + complexity
- Each file is self-contained (stdlib only) — no shared module beyond standard library
- Variable names are spelled out (`left`, `right`, `mid` — never `l`, `r`, `m`)
- Comments on non-obvious steps; alternatives noted when relevant

## Module counts

| Module | Problems (code) | Design only | Total lessons |
| --- | --- | --- | --- |
| 01 Overview | 3 | 3 | 6 |
| 02 Complexity | 0 | 4 | 4 |
| 03 Patterns | 0 | 8 | 8 |
| 04 Arrays | 12 | 0 | 12 |
| 05 Hash Tables | 6 | 0 | 6 |
| 06 Searching & Sorting | 8 | 0 | 8 |
| 07 Strings | 9 | 0 | 9 |
| 08 Graphs | 9 | 0 | 9 |
| 09 Trees | 9 | 0 | 9 |
| 10 Stacks & Queues | 8 | 0 | 8 |
| 11 Linked Lists | 6 | 0 | 6 |
| 12 Heaps | 5 | 0 | 5 |
| 13 Recursion & Backtracking | 12 | 0 | 12 |
| 14 Dynamic Programming | 10 | 0 | 10 |
| 15 Mock Interviews | 6 | 0 | 6 |
| **Totals** | **103** | **15** | **118** |
