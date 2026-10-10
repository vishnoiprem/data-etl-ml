# Section 14 — Python Basics Appendix (L78–L81, ~32 min)

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Format:** 4 lectures, ~32 minutes total. Deeper-dive Python tutorial aimed
> at absolute beginners with no prior coding experience.
> **Position:** APPENDIX — placed at the end of the course per the Udemy layout.

---

## Who this section is for

This section is **optional for experienced developers** but **required reading
for anyone who has never written Python before**.

If any of the following describe you, work through L78–L81 before continuing
on to the Lambda-heavy sections (or revisit them now if you've already
finished the course):

- You have never run a Python script.
- The words "variable", "loop", "function" and "data type" sound new.
- You installed PyCharm but don't know how to create a new file or press Run.
- You're afraid the words "dictionary" and "list" will show up and you'll be
  lost.

If you already write Python in your day job — skip this section entirely.
You've already seen everything in it.

## What you'll learn

By the end of this section you will be able to:

| Lecture | Skill you'll have |
|---|---|
| L78 (0:56) | A clear map of the section and a confidence check before you start |
| L79 (9:11) | Install PyCharm Community Edition, create your first `hello.py`, use `print()`, define variables, format strings with f-strings, accept `input()` from the keyboard |
| L80 (13:03) | Tell the difference between `int`, `str`, `float`, and `bool`; ask an object's type with `type()`; repeat work with `for` and `while` loops; build and read Python dictionaries |
| L81 (8:58) | Store many items in a list; use list methods (`append`, `pop`, `sort`); define your own function with parameters and a `return` value |

## Lecture map

| L# | Title | Duration | File |
|---|---|---|---|
| L78 | Python Basics — Section Overview | 0:56 | `lecture_scripts/L78_section_overview.md` |
| L79 | Python Basics – 1 : PyCharm, Print Function, Variables, Format, User Input | 9:11 | `lecture_scripts/L79_python_basics_1.md` |
| L80 | Python Basics – 2 : Data Types Intro, For Loops and Data Type – Dictionary | 13:03 | `lecture_scripts/L80_python_basics_2.md` |
| L81 | Python Basics – 3 : Data Type – List and Functions | 8:58 | `lecture_scripts/L81_python_basics_3.md` |

## How to read this section

1. Watch L78 first (under 1 minute). It is the section overview.
2. L79–L81 are step-by-step tutorials. Each one starts with a complete
   **Setup** section (installing software, creating a folder, opening a
   file). Do exactly what the Setup section says before you read any further.
3. Every code block in every lecture is a complete, runnable script.
   Copy-paste it into a new file in PyCharm, press Shift+F10 (or the green
   triangle Run button), and confirm the output matches.
4. Type the code yourself for the first few examples. After you've seen the
   pattern you can switch to copy-paste. **Typing the code yourself is the
   fastest way to memorize the syntax.**
5. After L81, take the section quiz: `quizzes/section_14.md`. 10 questions,
   hidden answers. A score of 8/10 is the readiness bar.

## What's in this folder

```
14_python_basics_appx/
├── README.md                       ← you are here
├── lecture_scripts/
│   ├── L78_section_overview.md
│   ├── L79_python_basics_1.md
│   ├── L80_python_basics_2.md
│   └── L81_python_basics_3.md
├── code/                           ← runnable scripts referenced in lectures
└── assignments/                    ← optional graded practice
```

## Relationship to Section 3 (Python Refresher)

Section 3 (L09–L10, 23 min) is a **refresher** — it assumes you already know
how to install Python and write a simple script. It briefly recaps the
constructs you'll need to read the Lambda code later in the course.

Section 14 is the **appendix** — it's a from-scratch tutorial assuming you've
never seen Python before. It is more detailed, more hands-on, and more
gentle in pacing.

**If you took the course and felt lost during the boto3 lectures, jump to
this section and start at L79.**

## What's next

- Beginners: after L81, take `quizzes/section_14.md`. If you score 8/10 or
  better, return to Section 4 (L11) and start the Lambda-with-boto3 work.
- Experienced devs: skip this section and move to the downloadable resources
  in Section 16.

## License & attribution

Authored by **Prem Vishnoi <prem.vishnoi@example.com>** based on the
published Udemy curriculum. Code samples are MIT-licensed.
See `../../LICENSE` for the full text.
