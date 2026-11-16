# Setup Local Environment using VS Code

> **Curriculum item 1.** This is the environment setup for every module that
> follows. If you can get through this chapter on **both** Windows and Mac,
> everything downstream has a working terminal, a working Python, and a
> working `gcloud`.
>
> **Scope note:** this chapter is about your **local** machine. The
> *remote* setup — pointing VS Code at a running Dataproc cluster — is a
> different skill and is covered in
> [07 Big Data Processing using Google Dataproc](07 Big Data Processing using Google Dataproc.md).

---

## What you are building

By the end of this chapter you will have:

- [ ] VS Code installed, with the extensions this course actually needs
- [ ] A Python environment your editor and your terminal both agree on
- [ ] `gcloud` installed, authenticated, and working **inside** the VS Code
      integrated terminal
- [ ] This repository open as a workspace, with the right folders visible
- [ ] A runnable check that proves all of the above

The last item matters most. Every subsequent module assumes a working
environment. We verify it explicitly rather than discovering a broken
Python at 2am in chapter 7.

---

## 1. Install VS Code

Download from the official site and install with your platform's defaults.

- macOS — <https://code.visualstudio.com/download>
- Windows — <https://code.visualstudio.com/download>

macOS: open the `.zip`, drag `Visual Studio Code.app` into `Applications`.
Windows: run the installer and accept the defaults — in particular, make sure
**"Add to PATH"** is checked so `code` is available from the terminal.

Open it once. The welcome screen is the right place for the next step.

---

## 2. Install the extensions

Open the Extensions view (`Ctrl+Shift+X` on Windows, `Cmd+Shift+X` on macOS)
and install:

| Extension | Publisher | Why this course needs it |
|---|---|---|
| **Python** | Microsoft | The interpreter, the debugger, the test runner |
| **Pylance** | Microsoft | Fast type-checking and autocomplete for the notebooks and apps |
| **Jupyter** | Microsoft | Opens the `.ipynb` notebooks in this repo |
| **Cloud Code** | Google | Editor support for `gcloud` — flags a bad flag before you run it |
| **GitLens** | GitKraken | Shows who last changed a line; useful when reading the reference repo |

You do **not** need the Python Environments extension — modern VS Code handles
virtual environments natively once you pick one.

> **Reading the .ipynb notebooks?** These are stored as JSON, which is
> unreadable as raw text. The Jupyter extension renders them properly, with
> runnable cells and a kernel selector in the top right.

---

## 3. Get the repository

Clone the course repository and open it **as a folder**, not as a loose file.

```shell
git clone YOUR_REPO_URL data-engineering-on-gcp
cd data-engineering-on-gcp
```

Then in VS Code: **File → Open Folder…** and select the `data-engineering-on-gcp`
directory.

**Open the folder, not a file inside it.** This is the single most common
setup mistake, and it is the reason the extensions, the terminal, the
Python interpreter, and the file explorer all behave. When you open a single
`.md` or `.ipynb` file, VS Code runs in "single file" mode — no workspace,
no integrated terminal rooted at the repo, and the Jupyter extension will not
find the sibling notebooks.

---

## 4. Set up Python

This course's code uses **Python 3.9+**. Check what you have:

```shell
python3 --version
```

> **On Windows the command is usually `python`, not `python3`.** The
> Python.org installer registers `python` and `py`. If `python3` is not
> found on Windows, use `py -3 --version` instead, and substitute `py -3`
> for `python3` in every command below.

### 4.1 Create a virtual environment

A virtual environment keeps this course's dependencies out of your system
Python, so you can delete it at any time without breaking anything else on
your machine.

**macOS / Linux:**
```shell
python3 -m venv .venv
```

**Windows (PowerShell):**
```powershell
py -3 -m venv .venv
```

### 4.2 Activate it — the part that differs

This is where Windows and macOS genuinely diverge, and it is the step that
most often fails silently.

**macOS / Linux (zsh or bash):**
```shell
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt / cmd.exe):**
```cmd
.venv\Scripts\activate.bat
```

Your prompt changes to show `(.venv)` at the front when it works:

```text
(.venv) data-engineering-on-gcp %
```

> **Windows: "running scripts is disabled on this system".**
> PowerShell blocks `Activate.ps1` by default, and the error is about
> *execution policy*, not about Python. Fix it for your user:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```
> Then activate again. `-Scope CurrentUser` means you are not changing the
> machine-wide policy and you do not need Administrator.
>
> **Windows: "cannot be loaded because running scripts is disabled"** — same
> fix. **macOS: "command not found: activate"** — you are probably in `zsh`
> and the file is `activate` with no extension; use `source .venv/bin/activate`
> exactly.

### 4.3 Install the dependencies

```shell
python -m pip install --upgrade pip
pip install google-cloud-storage google-cloud-bigquery google-cloud-secret-manager google-cloud-sql-connector pyspark apache-airflow jupyter nbformat nbclient pandas
```

`pandas` and `jupyter` are needed for the notebooks. The `google-cloud-*`
clients are needed for the Secret Manager, BigQuery, and Cloud SQL chapters.

### 4.4 Verify

```shell
python -c "import pandas, google.cloud.bigquery, google.cloud.secretmanager; print('deps OK')"
```

---

## 5. Install and configure the Google Cloud CLI

```shell
gcloud --version
```

**macOS:** use the [Google Cloud SDK installer](https://cloud.google.com/sdk/docs/install),
then add the SDK's `bin` directory to your shell profile:

```shell
echo 'export PATH="$PATH:$(gcloud info --format='value(installation_path)')/bin"' >> ~/.zshrc
source ~/.zshrc
```

**Windows:** install via the same [Google Cloud SDK installer](https://cloud.google.com/sdk/docs/install).
It adds itself to your `PATH` automatically. Restart the terminal afterwards
— a running terminal keeps the old `PATH`.

### 5.1 Authenticate

```shell
gcloud init
```

This opens a browser. Sign in with the Google account that owns your GCP
project, pick the project, and choose a region.

For the Python libraries specifically you also need application default
credentials:

```shell
gcloud auth application-default login
```

> **Why both?** `gcloud init` configures the **CLI**. The
> `application-default` login configures the **client libraries**, which
> read a separate credential file. A notebook using `google.cloud.bigquery`
> fails with `DefaultCredentialsError` until you run the second command.
> This trips up nearly everyone once.

### 5.2 Confirm the CLI can reach your project

```shell
gcloud config list
gcloud projects list
```

You should see your project ID in the output.

---

## 6. Use the integrated terminal

**Terminal → New Terminal** (`Ctrl+\`` on Windows, `Ctrl+\`` on macOS).

This is the terminal you will use for the whole course. The critical thing:
**it must be a login shell that sources your profile.**

```shell
echo $SHELL          # macOS — expect /bin/zsh or /bin/bash
$Env:ComSpec         # Windows — expect the cmd path
```

On **macOS**, the integrated terminal defaults to `zsh -i`, which sources
`.zshrc` — so your `gcloud` PATH line works automatically.

On **Windows**, the integrated terminal defaults to PowerShell, which reads
your `PATH` from the system environment. If you installed the SDK *before*
opening VS Code, `gcloud` will not be found. Two fixes:

1. Restart VS Code entirely (not just the terminal) so it picks up the new
   `PATH`.
2. Or set the terminal profile explicitly: **Terminal → Select Default
   Profile → Command Prompt**, or configure `terminal.integrated.defaultProfile.windows`.

### 6.1 Verify gcloud works inside VS Code

```shell
gcloud config list
```

If this fails inside VS Code but works in your system terminal, it is a
`PATH` problem, not an installation problem. Move on to §9, which has the
diagnostic.

---

## 7. Point VS Code at the right Python

VS Code picks an interpreter per workspace. The integrated terminal and the
editor must agree, or you get "works in terminal, red squiggle in editor"
confusion.

**macOS / Linux:**
1. `Cmd+Shift+P` → **Python: Select Interpreter**
2. Choose `./.venv/bin/python`

**Windows:**
1. `Ctrl+Shift+P` → **Python: Select Interpreter**
2. Choose `.\.venv\Scripts\python.exe`

**Or, faster and identical across both platforms:** `Cmd+Shift+P` /
`Ctrl+Shift+P` → **Python: Create Environment** → **Venv** → select the
interpreter → **OK**. VS Code creates the venv, activates it in the
terminal, and selects it as the workspace interpreter in one step. This is
the recommended path.

### 7.1 A workspace settings file

With the folder open, create `.vscode/settings.json` in the repository root:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.analysis.extraPaths": ["${workspaceFolder}"],
  "files.insertFinalNewline": true,
  "files.trimTrailingWhitespace": true,
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": ["project/tests"],
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  },
  "jupyter.jupyterServerType": "local"
}
```

> **Windows note:** the interpreter path in the file above is the macOS
> layout. On Windows change it to:
> ```json
> "python.defaultInterpreterPath": "${workspaceFolder}\\.venv\\Scripts\\python.exe"
> ```
> To avoid maintaining two files, use the platform-agnostic form instead:
> ```json
> "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python"
> ```
> VS Code resolves this correctly on Windows too — it normalises the
> separators.

**What each setting buys you:**

| Setting | Why it matters here |
|---|---|
| `python.defaultInterpreterPath` | The editor and the terminal use one Python |
| `python.analysis.extraPaths` | Lets `from pipeline_logic import ...` resolve in the apps without `sys.path` hacks |
| `python.testing.pytestEnabled` | The Test Explorer finds and runs the suite |
| `jupyter.jupyterServerType: local` | Notebooks run in your venv, not a global kernel |

---

## 8. Add tasks so the common commands are one keystroke

`.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run: sample data generator",
      "type": "shell",
      "command": "python resources/sample_data.py --output-dir ./sample_data",
      "options": { "cwd": "${workspaceFolder}" },
      "group": "build",
      "problemMatcher": []
    },
    {
      "label": "Run: local pipeline",
      "type": "shell",
      "command": "python project/local_runner.py --run",
      "options": { "cwd": "${workspaceFolder}" },
      "problemMatcher": []
    },
    {
      "label": "Test: pytest",
      "type": "shell",
      "command": "python -m pytest project/tests/ -q",
      "options": { "cwd": "${workspaceFolder}" },
      "group": { "kind": "test", "isDefault": true },
      "problemMatcher": []
    },
    {
      "label": "Lint: course audit",
      "type": "shell",
      "command": "python resources/audit_course.py",
      "options": { "cwd": "${workspaceFolder}" },
      "problemMatcher": []
    },
    {
      "label": "Check: environment",
      "type": "shell",
      "command": "python tools/check_environment.py",
      "options": { "cwd": "${workspaceFolder}" },
      "problemMatcher": []
    }
  ]
}
```

Run them via **Terminal → Run Task…** or `Ctrl+Shift+B` for the default
(build) task.

---

## 9. The verification script

Run this once. It checks every assumption this chapter made, and tells you
which one failed.

```python
# tools/check_environment.py
import os
import shutil
import subprocess
import sys

failures = []
notes = []


def check(name, fn):
    try:
        result = fn()
    except Exception as exc:  # noqa: BLE001 - report and continue
        failures.append(f"{name}: {type(exc).__name__}: {exc}")
        return
    if result is True:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}: {result}")
        failures.append(f"{name}: {result}")


def python_version():
    v = sys.version_info
    if v < (3, 9):
        return f"Python {v.major}.{v.minor} is too old; need 3.9+"
    return True


def in_venv():
    if hasattr(sys, "real_prefix") or sys.base_prefix != sys.prefix:
        return True
    return "not in a virtualenv — activate .venv first"


def deps_installed():
    missing = []
    for mod in ("pandas", "google.cloud.bigquery", "google.cloud.secretmanager"):
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    return True if not missing else f"missing: {', '.join(missing)}"


def gcloud_present():
    path = shutil.which("gcloud")
    return True if path else "gcloud not on PATH in this terminal"


def gcloud_authed():
    if not shutil.which("gcloud"):
        return "gcloud not installed"
    proc = subprocess.run(
        ["gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return f"gcloud auth list failed: {proc.stderr.strip()}"
    accounts = proc.stdout.strip()
    return True if accounts else "no active gcloud account — run `gcloud init`"


def project_set():
    if not shutil.which("gcloud"):
        return "gcloud not installed"
    proc = subprocess.run(
        ["gcloud", "config", "get-value", "project"],
        capture_output=True, text=True,
    )
    val = proc.stdout.strip()
    if proc.returncode != 0 or not val or val == "(unset)":
        return "no default project — run `gcloud config set project YOUR_PROJECT_ID`"
    return True


def repo_layout():
    expected = ["apps", "data", "notebooks", "scripts"]
    missing = [d for d in expected if not os.path.isdir(d)]
    return True if not missing else f"missing folders: {', '.join(missing)}"


def sample_data_present():
    if not os.path.isdir("sample_data"):
        return "sample_data/ not generated — run `python resources/sample_data.py --output-dir ./sample_data`"
    return True


print("Environment check\n")
check("Python >= 3.9", python_version)
check("Virtualenv active", in_venv)
check("Dependencies installed", deps_installed)
check("gcloud on PATH", gcloud_present)
check("gcloud authenticated", gcloud_authed)
check("Default project set", project_set)
check("Repository layout", repo_layout)
check("Sample data generated", sample_data_present)

print()
if failures:
    print(f"{len(failures)} check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)

print("All checks passed. You are ready for chapter 2.")
```

```shell
python tools/check_environment.py
```

> **Note:** the script lives at `tools/check_environment.py` in this
> course's directory. Run it from the course root so the relative paths
> (`apps/`, `data/`, `notebooks/`, `scripts/`) resolve. The `sample_data`
> check points at the parent directory, where the refactored course's
> `resources/sample_data.py` lives.

---

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `gcloud: command not found` in VS Code only | The terminal has a stale `PATH` | Restart VS Code entirely, then `Terminal → New Terminal` |
| `gcloud: command not found` everywhere | SDK not installed or not on `PATH` | Reinstall; on macOS add the SDK `bin` to `.zshrc` as in §5 |
| `python3: command not found` (Windows) | Windows registers `python` / `py` | Use `py -3` everywhere |
| `running scripts is disabled` (Windows) | PowerShell execution policy | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `command not found: activate` (macOS) | Wrong filename or wrong shell | `source .venv/bin/activate` |
| Terminal works, editor shows import errors | Editor is on a different interpreter | `Python: Select Interpreter` → the venv |
| `DefaultCredentialsError` in a notebook | Library credentials missing | `gcloud auth application-default login` |
| `ModuleNotFoundError: pandas` after activating | Wrong venv, or deps not installed | Re-run `pip install` **after** activating; check `which python` |
| `tests pass in terminal, fail in Test Explorer | Wrong interpreter for the test runner | Select the venv interpreter, then reload the window |
| Notebook kernel is the wrong Python | Jupyter picked a global kernel | `jupyter.jupyterServerType: local` in settings, then restart kernel |

### The one diagnostic that settles most of it

Run this in the **VS Code integrated terminal**:

```shell
which python        # macOS/Linux
where.exe python    # Windows
```

The path must point inside your project:

```text
.../data-engineering-on-gcp/.venv/bin/python          # macOS/Linux
.../data-engineering-on-gcp\.venv\Scripts\python.exe   # Windows
```

If it points anywhere else — `/usr/bin/python`, `/usr/local/bin/python`,
`AppData\...` — the environment is not the one you think it is, and every
downstream symptom follows from that.

---

## 11. What "done" looks like

You are done with this chapter when:

1. `gcloud config list` shows your project ID, **inside** the VS Code
   terminal.
2. `python -c "import pandas"` succeeds.
3. `python tools/check_environment.py` prints
   `All checks passed. You are ready for chapter 2.`
4. You have opened a `.ipynb` from `notebooks/` and run a cell.

Now proceed to
[02 Setting up Data Lake using GCS](02 Setting up Data Lake using GCS.md).
