# L79 — Python Basics – 1: PyCharm, Print Function, Variables, Format, User Input

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 14 — Python Basics Appendix
> **Duration target:** 9:11

## Prereqs

- L78 watched (it's 56 seconds).
- A computer running Windows 10/11, macOS 11+, or Ubuntu 20.04+. Anything
  from the last five years is plenty.
- About 3 GB of free disk space for PyCharm.
- **No prior Python or programming experience required.**

## Key terms

- **IDE (Integrated Development Environment):** a single application that
  helps you write, run, and debug code. Think of it as Microsoft Word for
  programs. PyCharm is an IDE for Python.
- **Project folder:** a directory on your disk where PyCharm keeps your
  code. Every PyCharm project is a folder. The folder holds your `.py`
  files, your virtual environment, and your settings.
- **Script (`.py` file):** a plain text file that contains Python code,
  saved with the extension `.py`. When you "run" the file, Python reads
  the file from top to bottom and does what each line says.
- **`print()`:** a built-in Python function that displays text on the
  screen. It's the first function every beginner learns because the output
  is visible immediately.
- **Variable:** a name attached to a value. Think of it as a sticky-note
  with a name on it — you can read the note or rewrite it. Example:
  `name = "Alice"`. Here `name` is the variable; `"Alice"` is the value.
- **String (`str`):** a piece of text inside quotes. Either single quotes
  `'hello'` or double quotes `"hello"` work — they are the same thing.
- **f-string:** a way to embed the value of a variable inside a string.
  Example: `f"Hello, {name}"` becomes `Hello, Alice` when `name = "Alice"`.
- **`input()`:** a built-in function that pauses the program and waits for
  the user to type something and press Enter. Whatever the user types
  comes back to the program as a string.

## Lecture

### 0:00 — Welcome and what this lecture covers

This lecture has one goal: take you from "I've never opened an IDE" to
"my first working Python script that asks the user a question and prints
a personalized answer." By the end you will have used `print`,
`variables`, f-strings, and `input`. That's it. Four ideas. Nine minutes.

### 0:30 — Step 1: install Python 3.11+

Before we install PyCharm we need Python itself. PyCharm is a **code
editor**, not a language runtime. The Python interpreter is what actually
runs the code.

- **Windows:** download the official installer from
  <https://www.python.org/downloads/windows/>. Run it. **Tick the
  "Add Python to PATH" checkbox at the bottom of the first screen —
  this is the most important step.** Click "Install Now".
- **macOS:** download the universal installer from
  <https://www.python.org/downloads/macos/>. Open the `.pkg` file and
  follow the prompts. (Apple's system Python is too old for this course.)
- **Ubuntu:** Python 3.11 is in 23.04+ repos. If you have an older
  Ubuntu, install via the deadsnakes PPA, or use `pyenv` (recommended).

Verify the install by opening a terminal and running:

```bash
python3 --version
# expected: Python 3.11.x or 3.12.x
```

If you see `3.11` or higher you're good. If you see `2.7` something is
wrong — check the "Add to PATH" step on Windows.

### 1:30 — Step 2: install PyCharm Community Edition

PyCharm comes in two flavors: **Professional** (paid) and **Community
Edition** (free, open source). For this course we use the free one.
Everything in the course runs on Community Edition.

- Download from <https://www.jetbrains.com/pycharm/download/>.
- Pick the **Community** tab, not Professional.
- Run the installer with the default options.

When PyCharm opens for the first time it will ask you to accept the
license, pick a UI theme (Light or Dark — your call), and possibly
install some plugins. The defaults are fine. You do not need any
plugin for this course.

### 2:30 — Step 3: create your first project

A **project** in PyCharm is a folder on your disk. PyCharm will create
the folder, drop a virtual environment into it, and open the project
window.

1. Click **"New Project"** on the welcome screen.
2. For "Location" type a path you can find later, e.g.
   `~/projects/python_basics` (macOS/Linux) or
   `C:\projects\python_basics` (Windows).
3. PyCharm defaults to a "Pure Python" project type. Leave that.
4. **Important:** under "Python interpreter" choose
   "New environment using Virtualenv" with the Python 3.11+ base
   interpreter. This creates an isolated environment so the libraries
   you install in this project do not pollute your system Python.
5. Click **Create**. PyCharm creates the folder and opens the project
   window.

You will see a project tree on the left with the project folder at the
top. Right now the folder only has a hidden `.venv` directory — the
virtual environment.

```
python_basics/
└── .venv/                ← virtual environment (Python 3.11+)
```

### 3:30 — Step 4: create your first Python file

In the project tree, right-click the **project folder** (the outer
`python_basics` folder, not the inner `.venv`). Choose
**New → Python File**. Name it `hello.py`. PyCharm creates the file
and opens it in the editor.

Type this into the file:

```python
print("Hello, world!")
```

Now run it. Three ways, all equivalent:

- Press the **green triangle Run button** in the top-right corner.
- Press **Shift + F10** (Windows/Linux) or **Ctrl + Shift + R** (macOS).
- Right-click the file in the tree and choose **Run 'hello'**.

A panel opens at the bottom of the screen called the **Run console**.
You should see:

```
Hello, world!
```

Congratulations — you just ran your first Python script. Stop and
celebrate for a second. You typed code, the computer did what you said,
and you saw the output. This is the entire loop you will repeat for
the rest of the course.

### 4:30 — Step 5: what `print` actually does

`print` is a **function**. A function is a named block of work. The
word `print` is the name. The parentheses hold the **arguments** —
the things you want the function to act on. In our case the argument
is the string `"Hello, world!"`.

Strings are always wrapped in matching quotes — single `'...'` or
double `"..."`. The quotes are not part of the string. They are
**delimiters** — they tell Python "the text starts here and ends here."

Try changing the line and re-running:

```python
print("Hello, Prem")
print(42)
print(3.14)
```

You can mix text and numbers — `print` will happily print anything
you put inside the parentheses, one argument per call.

### 5:00 — Step 6: variables

A variable is a name that points to a value. You create one with
`=`. The name goes on the left; the value goes on the right.

```python
name = "Alice"
age = 30
city = "London"
```

This reads as: "Store the string `Alice` under the name `name`.
Store the number `30` under the name `age`. Store the string
`London` under the name `city`."

Now use the variables:

```python
print(name)
print(age)
print(city)
```

Output:

```
Alice
30
London
```

A few rules for variable names in Python:

- Lowercase letters, digits, and underscores only.
- Cannot start with a digit (`1name` is illegal).
- Case-sensitive — `Name` and `name` are different variables.
- Avoid Python's reserved words like `print`, `for`, `if` — these
  have special meaning. (PyCharm highlights them in a different
  color to remind you.)

The convention for multi-word names is **snake_case**: lowercase
letters joined by underscores, like `first_name` or
`total_s3_buckets`.

You can reassign a variable at any time:

```python
score = 10
print(score)        # 10
score = 20
print(score)        # 20
```

This is why they're called *variables* — the value they point to
can change.

### 6:30 — Step 7: f-strings (formatted string literals)

So far we've printed variables one at a time. Most real programs
print sentences that mix text and values, like
"Hello Alice, you are 30 years old." That's where f-strings come in.

An f-string is a string that starts with the letter `f` and contains
expressions in `{ }` curly braces. Python evaluates the expression
inside the braces and inserts the result.

```python
name = "Alice"
age = 30
print(f"Hello {name}, you are {age} years old.")
```

Output:

```
Hello Alice, you are 30 years old.
```

Anything inside the braces is a real Python expression. You can do
math, call functions, even do conditional logic in there.

```python
a = 5
b = 3
print(f"{a} + {b} = {a + b}")
print(f"Next year Alice will be {age + 1}")
```

Output:

```
5 + 3 = 8
Next year Alice will be 31
```

f-strings are the standard way to format strings in modern Python.
You'll see them everywhere in this course — every Lambda log line,
every error message, every S3 key. Get comfortable with them now.

### 7:30 — Step 8: `input()` — talking to the user

So far our scripts run and exit. They don't interact with the person
running them. `input()` changes that. It pauses the program, shows
an optional prompt, waits for the user to type something and press
Enter, and then **returns** whatever the user typed as a string.

```python
name = input("What is your name? ")
print(f"Hello, {name}!")
```

Run it. The Run console shows:

```
What is your name? _
```

The cursor blinks. You type something, press Enter, and the program
prints the greeting.

Important: `input()` **always returns a string**, even if the user
types a number. So:

```python
age = input("How old are you? ")
print(type(age))
```

…prints `<class 'str'>` — even if you typed `30`. We'll convert
strings to numbers in the next lecture. For now just remember:
`input()` returns a string, full stop.

### 8:00 — Step 9: putting it all together

Let's combine everything in one script. Create a new file
`greeter.py` in the same project:

```python
# greeter.py
# A small program that asks the user's name, age, and city,
# then prints a friendly summary.

name = input("What is your name? ")
age = input("How old are you? ")
city = input("Which city do you live in? ")

print(f"Hello {name}!")
print(f"You are {age} years old and live in {city}.")
print(f"Nice to meet you, {name} from {city}.")
```

Run it. Type your answers. Read the output. That's a working Python
program — the kind of program that prints a receipt, shows a Lambda
log line, or displays an error message to a user.

### 8:45 — Recap and what's next

In this lecture you:

- Installed Python 3.11+ and PyCharm Community Edition.
- Created your first PyCharm project with a virtual environment.
- Wrote and ran your first Python script (`hello.py`).
- Used `print()` to display text.
- Stored values in variables (`name`, `age`, `city`).
- Embedded variables in strings using f-strings.
- Read keyboard input using `input()`.

In L80 we extend this foundation with the four basic data types
(`int`, `float`, `str`, `bool`), two kinds of loops (`for` and
`while`), and a brand-new data structure called a **dictionary**.
None of that is harder than what you did in this lecture — it just
gives you more words to use.

## Hands-on

The only hands-on for this lecture is the install + first-script loop.
Concrete steps:

1. Install Python 3.11+. Open a terminal. Run `python3 --version`.
2. Install PyCharm Community Edition.
3. Create a new project at `~/projects/python_basics` (or the
   Windows equivalent).
4. Inside the project, create `hello.py` with `print("Hello, world!")`.
   Run it. Confirm the output.
5. Edit `hello.py` to print three lines: your name, your city, and
   your favorite color, each on its own line.
6. Create `greeter.py` with the code from the lecture. Run it. Type
   your answers. Confirm the output.
7. **Stretch:** create `mad_libs.py` that asks the user for a noun,
   a verb, an adjective, and a name, then prints a single silly
   sentence using all four. Example output:
   `Sir Reginald, the fluffy dragon, danced on a Tuesday.`

## Quiz prep

The quiz for this section (L78–L81) will ask you about:

- What `print()` does and how to use it.
- What a variable is and how to assign one.
- How to write an f-string.
- What `input()` returns (always a string).
- The difference between `int`, `float`, `str`, `bool`.
- What a `for` loop does and how to write one.
- What a dictionary is and how to read a value by key.
- What a list is and how to append to one.
- How to define a function with a parameter and a `return` value.

The 10 quiz questions are in `../../quizzes/section_14.md`.

## Further reading

- **Official Python tutorial, section 3** <https://docs.python.org/3/tutorial/introduction.html>
  — the official "An Informal Introduction to Python" pages. Same
  material as L79, in the language of the Python team.
- **PyCharm quickstart** <https://www.jetbrains.com/help/pycharm/quick-start-guide.html>
  — the official JetBrains guide if you want to learn more IDE
  features (debugger, version control integration) later.
- **L80 (next lecture):** `L80_python_basics_2.md` — data types, loops,
  dictionaries.
- **Section README:** `../README.md`.
