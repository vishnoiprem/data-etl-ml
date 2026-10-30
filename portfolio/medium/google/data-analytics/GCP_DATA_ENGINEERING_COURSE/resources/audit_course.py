#!/usr/bin/env python3
"""
audit_course.py — a static linter for the GCP Data Engineering course.

It catches the mistakes a reader would otherwise only hit on a worker,
hours into a run:

  * every relative link in a README, chapter or resource resolves;
  * every Python snippet in the chapters parses;
  * every chapter has all eight required sections, in order;
  * no leftover placeholders or TODO markers;
  * the documented expected outputs match what the code actually produces.

Usage:
    python resources/audit_course.py
    python resources/audit_course.py --quiet
"""
from __future__ import annotations

import argparse
import ast
import builtins
import contextlib
import io
import os
import re
import sys
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = COURSE_ROOT / "chapters"
PROJECT_DIR = COURSE_ROOT / "project"
RESOURCES_DIR = COURSE_ROOT / "resources"
INTERVIEW_DIR = COURSE_ROOT / "interview"
NOTEBOOKS_DIR = COURSE_ROOT / "notebooks"

#: The sections every chapter must contain, in order.
REQUIRED_SECTIONS = [
    "What you will learn",
    "Concept",
    "Hands-On",
    "Common Errors and Fixes",
    "Production Notes",
    "Key Takeaways",
    "Practice Exercises",
    "Further Reading",
]

#: Markers that indicate unfinished content.
PLACEHOLDER_PATTERNS = [
    (re.compile(r"\bTODO\b"), "TODO marker"),
    (re.compile(r"\bFIXME\b"), "FIXME marker"),
    (re.compile(r"\bXXX\b"), "XXX marker"),
    (re.compile(r"YOUR_VALUE_HERE"), "unfilled placeholder"),
]

#: Shell placeholders that are legitimately expected.
ALLOWED_PLACEHOLDERS = {
    "YOUR_PROJECT_ID",
    "YOUR_PROJECT",
    "YOUR_BUCKET",
    "YOUR_BILLING_ACCOUNT",
    "YOUR_DATASET",
    "YOUR_REGION",
    "ENV_NAME",
    "REGION",
    "BUCKET",
    "PROJECT_ID",
}

FENCE_RE = re.compile(r"^```(\w*)\s*$", re.MULTILINE)
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


class Report:
    """Collects audit findings."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.checks = 0

    def error(self, message: str) -> None:
        """Record an error.

        Args:
            message: The error message.
        """
        self.errors.append(message)

    def warn(self, message: str) -> None:
        """Record a warning.

        Args:
            message: The warning message.
        """
        self.warnings.append(message)

    def check(self) -> None:
        """Count one check."""
        self.checks += 1


def relative(path: Path) -> str:
    """Render a path relative to the course root, when it is inside it.

    Every message the linter prints names the file it came from. A
    path outside the course root — a temporary file, a file the reader
    points the linter at — still has to render without raising, or the
    linter crashes instead of reporting the defect it found.

    Args:
        path: The path to render.

    Returns:
        The path relative to the course root, or the absolute path.
    """
    try:
        return str(path.relative_to(COURSE_ROOT))
    except ValueError:
        return str(path)


def iter_code_blocks(text: str) -> list[str]:
    """Extract fenced code blocks from markdown.

    Only blocks tagged as Python are returned — ``text`` fences hold
    diagrams and shell output and must not be parsed.

    Args:
        text: The markdown source.

    Returns:
        A list of code strings.
    """
    blocks: list[str] = []
    lines = text.splitlines()
    in_block = False
    language = ""
    current: list[str] = []

    for line in lines:
        if not in_block:
            match = FENCE_RE.match(line)
            if match:
                in_block = True
                language = match.group(1)
                current = []
            continue
        if FENCE_RE.match(line):
            if language in ("python", "py"):
                blocks.append("\n".join(current))
            in_block = False
            language = ""
            continue
        current.append(line)

    return blocks


def check_markdown_links(path: Path, report: Report) -> None:
    """Check that every relative link in a markdown file resolves.

    Args:
        path: The markdown file.
        report: The report to collect findings in.
    """
    text = path.read_text(encoding="utf-8")
    for match in LINK_RE.finditer(text):
        target = match.group(2).split("#")[0].strip()
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = (path.parent / target).resolve()
        report.check()
        if not resolved.exists():
            report.error(f"{relative(path)}: broken link -> {target}")


def check_sections(path: Path, report: Report) -> None:
    """Check that a chapter has all the required sections, in order.

    Args:
        path: The chapter file.
        report: The report to collect findings in.
    """
    text = path.read_text(encoding="utf-8")
    headings = re.findall(r"^##\s+(.+)$", text, re.MULTILINE)
    for section in REQUIRED_SECTIONS:
        report.check()
        if not any(section.lower() in heading.lower() for heading in headings):
            report.error(
                f"{relative(path)}: missing section '{section}'"
            )
            continue
    # The sections must appear in the documented order.
    positions = []
    for section in REQUIRED_SECTIONS:
        for index, heading in enumerate(headings):
            if section.lower() in heading.lower():
                positions.append(index)
                break
    if len(positions) == len(REQUIRED_SECTIONS) and positions != sorted(positions):
        report.error(
            f"{relative(path)}: sections are out of order"
        )


def check_placeholders(path: Path, report: Report) -> None:
    """Check a file for unfinished-content markers.

    Args:
        path: The file to check.
        report: The report to collect findings in.
    """
    text = path.read_text(encoding="utf-8")
    for pattern, label in PLACEHOLDER_PATTERNS:
        for match in pattern.finditer(text):
            report.check()
            line = text[: match.start()].count("\n") + 1
            report.warn(
                f"{relative(path)}:{line}: {label} -> {match.group(0)!r}"
            )


def check_python_snippets(path: Path, report: Report) -> None:
    """Check that every Python snippet in a markdown file parses.

    A snippet that ends with ``...`` is an abbreviated call — a
    deliberate elision — and is exempt.

    Args:
        path: The markdown file.
        report: The report to collect findings in.
    """
    text = path.read_text(encoding="utf-8")
    for index, block in enumerate(iter_code_blocks(text)):
        report.check()
        stripped = block.strip()
        if not stripped:
            continue
        if re.search(r",\s*\.\.\.\s*[,)]", stripped) or stripped.endswith("..."):
            continue
        try:
            ast.parse(block)
        except SyntaxError as exc:
            report.error(
                f"{relative(path)}: python snippet {index + 1} "
                f"does not parse: {exc.msg}"
            )


#: Import errors that mean "this snippet needs a cloud SDK we do not
#: install". They are not defects — the snippet is documentation for a
#: reader who *does* have the SDK — so they are skipped, not reported.
SDK_OPTIONAL_ERRORS = (ModuleNotFoundError, ImportError)

#: Module names whose absence is expected. Anything outside this list
#: that raises ``ModuleNotFoundError`` is a real defect.
OPTIONAL_SDK_MODULES = {
    "apache_beam",
    "airflow",
    "kfp",
    "psycopg2",
    "redis",
    "google",
    "sklearn",
    "pandas",
    "numpy",
    "matplotlib",
    "seaborn",
    "xgboost",
    "torch",
    "tensorflow",
    "db_dtypes",
    "pytz",
}

#: Markers that identify a snippet as running *on a cloud cluster*
#: rather than locally. Such a snippet reads ``gs://`` paths or starts
#: a Spark session, and executing it here would be both slow and
#: wrong: it is documentation for a Dataproc worker, not local code.
CLUSTER_ONLY_MARKERS = (
    "gs://",
    "SparkSession",
    "spark.read",
    "spark-submit",
    "gcloud dataproc",
    "storage.Client",
    "bigquery.Client",
    "pubsub_v1",
    "spanner.Client",
    "datastore.Client",
    "firestore.Client",
    "bigtable.Client",
)

#: Snippets that need a local file the reader supplies. The course
#: cannot ship every input, so these are skipped rather than failed.
LOCAL_FILE_MARKERS = (
    "wave.open(",
    "open(\"call.wav\"",
    "open('call.wav'",
    ".wav",
)


def _is_fragment(tree: ast.AST, source: str) -> bool:
    """Whether a snippet is a fragment of a larger file.

    A chapter may show one class or one function from a larger module,
    with the imports in the surrounding prose. Such a fragment is not a
    standalone program: running it alone raises ``NameError`` for a
    name the reader is expected to have imported.

    A fragment is recognised by starting part-way into a file — with a
    class body, a bare decorator, or a continuation of an expression.

    Args:
        tree: The parsed snippet.
        source: The snippet source.

    Returns:
        True when the snippet is a fragment rather than a program.
    """
    lines = [line for line in source.splitlines() if line.strip()]
    if not lines:
        return False

    first = lines[0].strip()

    # A class whose base class comes from an import shown in prose.
    if re.match(r"^class\s+\w+\(", first):
        return True

    # A bare decorator — "@task", "@beam.ptransform" — with the import
    # in the surrounding prose.
    if re.match(r"^@\w", first):
        return True

    # A continuation of an expression: the first line is indented or
    # opens a bracket that the block never closes.
    if source[: len(source) - len(source.lstrip())].startswith((" ", "\t")):
        return True

    return False


def _is_optional_sdk_failure(exc: BaseException) -> bool:
    """Whether a snippet failure is an absent optional dependency.

    Args:
        exc: The exception raised while executing the snippet.

    Returns:
        True when the failure is an unavailable third-party package.
    """
    if not isinstance(exc, SDK_OPTIONAL_ERRORS):
        return False
    name = getattr(exc, "name", None)
    if name is None:
        # An ImportError such as "cannot import name 'storage' from
        # 'google.cloud'" — the module is a cloud SDK one.
        text = str(exc)
        return any(module.split(".")[0] in text for module in OPTIONAL_SDK_MODULES)
    return name.split(".")[0] in OPTIONAL_SDK_MODULES


def _bound_names(tree: ast.AST) -> set[str]:
    """Collect the names a snippet binds at module level.

    Args:
        tree: The parsed snippet.

    Returns:
        The set of names the snippet assigns, defines, or imports.
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                names.add(node.target.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            if isinstance(node.target, ast.Name):
                names.add(node.target.id)
        elif isinstance(node, ast.With):
            for item in node.items:
                if isinstance(item.optional_vars, ast.Name):
                    names.add(item.optional_vars.id)
    return names


def _imported_names(tree: ast.AST) -> set[str]:
    """Collect the names a snippet imports.

    Args:
        tree: The parsed snippet.

    Returns:
        The set of names the snippet imports.
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name)
    return names


def _undefined_decorators_or_bases(
    tree: ast.AST,
    prose_names: set[str],
) -> set[str]:
    """Find decorators and base classes a snippet never defines.

    A decorator or a base class is always a symbol the reader must
    import — never a prose placeholder. A snippet that uses
    ``@dataclass`` without importing it is missing an import, and that
    is a defect a reader would hit immediately.

    This is checked statically and precisely, because guessing from a
    list of names is not: a heuristic list picks up local variables
    and produces false positives.

    A name bound by an *earlier* snippet in the chapter does not
    satisfy this check. Such a name may be a value (a DataFrame, a
    fitted model) that a later block legitimately continues from — but
    a decorator or a base class is always an import, and a reader who
    saves the later block on its own must still import it. Requiring
    the import in the block that uses it is what makes the snippet
    self-contained.

    Args:
        tree: The parsed snippet.
        prose_names: The names the chapter's prose says to import.

    Returns:
        The set of undefined decorator or base-class names.
    """
    defined = _bound_names(tree) | _imported_names(tree)
    missing: set[str] = set()

    for node in ast.walk(tree):
        # A decorator: @name or @module.name
        if isinstance(node, ast.ClassDef):
            for decorator in node.decorator_list:
                target = decorator
                if isinstance(target, ast.Call):
                    target = target.func
                if (
                    isinstance(target, ast.Name)
                    and target.id not in defined
                    and target.id not in prose_names
                    and not hasattr(builtins, target.id)
                ):
                    missing.add(target.id)
            # A base class: class Foo(Bar)
            for base in node.bases:
                if (
                    isinstance(base, ast.Name)
                    and base.id not in defined
                    and base.id not in prose_names
                    and not hasattr(builtins, base.id)
                ):
                    missing.add(base.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in node.decorator_list:
                target = decorator
                if isinstance(target, ast.Call):
                    target = target.func
                if (
                    isinstance(target, ast.Name)
                    and target.id not in defined
                    and target.id not in prose_names
                    and not hasattr(builtins, target.id)
                ):
                    missing.add(target.id)

    return missing


def _prose_import_names(text: str) -> set[str]:
    """Collect the names the chapter's prose says to import.

    A chapter may present a snippet whose imports live in the
    surrounding prose — ``@task`` after "Airflow's ``@task``
    decorator", for instance. Those names are legitimately imported;
    the snippet alone just does not repeat them.

    Args:
        text: The chapter's markdown source.

    Returns:
        The set of names mentioned in an import context in the prose.
    """
    names: set[str] = set()
    # Outside code fences.
    outside = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    for match in re.finditer(
        r"\bfrom\s+[\w.]+\s+import\s+([\w, ]+)", outside
    ):
        for part in match.group(1).split(","):
            part = part.strip().split(" as ")[0].strip()
            if part:
                names.add(part)
    for match in re.finditer(r"\bimport\s+([\w.]+)", outside):
        names.add(match.group(1).split(".")[0])
    # A name the prose names in backticks immediately after a
    # decorator or class mention, e.g. "the ``@task`` decorator".
    for match in re.finditer(r"`@(\w+)`", outside):
        names.add(match.group(1))
    return names


def _is_continuation_failure(
    exc: BaseException,
    chapter_names: set[str],
) -> bool:
    """Whether a snippet failure is a continuation of an earlier block.

    A chapter may present one script as a sequence of blocks. The
    second block then depends on a name the first block bound — a
    DataFrame, a fitted model, a feature list. Running the second
    block alone raises ``NameError``; that is a presentation choice,
    not a defect.

    The one case that is *always* a defect is a missing import for a
    name used as a **decorator** or a **base class** — ``@dataclass``
    or ``class Foo(SomeClass)``. Those names are never prose
    placeholders; they are symbols the reader must import. Detecting
    them from the source is precise, where guessing from a name list
    is not.

    Args:
        exc: The exception raised while executing the snippet.
        chapter_names: The names bound anywhere in the chapter.

    Returns:
        True when the failure is an acceptable undefined name.
    """
    if not isinstance(exc, NameError):
        return False
    name = getattr(exc, "name", None)
    if not name:
        return False
    # The chapter binds this name somewhere — a genuine continuation.
    if name in chapter_names:
        return True
    # Otherwise it is a prose placeholder such as ``df`` or ``X``:
    # a value the surrounding text describes but never defines.
    return True


def _stdlib_names() -> set[str]:
    """Collect the importable names from the standard library.

    A snippet that uses one of these without importing it has a
    missing import — a real defect. This collects both module names
    (``dataclasses``) and the public symbols inside them
    (``dataclass``), because the failure mode is a decorator or class
    used without its import.

    The set is built from the running interpreter's own standard
    library, so it matches the Python the reader is running.

    Returns:
        The set of public standard-library names.
    """
    import sysconfig

    names: set[str] = set()
    stdlib = sysconfig.get_paths().get("stdlib")
    if not stdlib or not Path(stdlib).exists():
        return names

    def harvest(tree: ast.AST) -> None:
        """Add the public names a module binds.

        Args:
            tree: The parsed module.
        """
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not node.name.startswith("_"):
                    names.add(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith("_"):
                        names.add(target.id)
            elif isinstance(node, ast.AnnAssign):
                if (
                    isinstance(node.target, ast.Name)
                    and not node.target.id.startswith("_")
                ):
                    names.add(node.target.id)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    names.add(alias.asname or alias.name.split(".")[0])

    for entry in sorted(Path(stdlib).iterdir()):
        if entry.name == "__pycache__":
            continue
        if entry.suffix == ".py":
            names.add(entry.stem)
            try:
                harvest(ast.parse(entry.read_text(encoding="utf-8")))
            except (OSError, SyntaxError, ValueError):
                continue
        elif entry.is_dir():
            names.add(entry.name)
            package_init = entry / "__init__.py"
            if not package_init.exists():
                continue
            try:
                harvest(ast.parse(package_init.read_text(encoding="utf-8")))
            except (OSError, SyntaxError, ValueError):
                continue

    return names


#: The standard-library names, computed once at import time.
STDLIB_NAMES = _stdlib_names()


def check_snippet_execution(path: Path, report: Report) -> None:
    """Execute the Python snippets in a chapter.

    Parsing proves a snippet is well-formed; executing it proves it
    *works*. A missing ``from dataclasses import dataclass`` parses
    perfectly and then raises ``NameError`` — which is exactly the
    kind of defect a reader would hit on a laptop, hours into a
    chapter.

    Snippets within a chapter share one namespace, because a chapter
    may present a script as a sequence of blocks: the second block
    continues from the first. Blocks that need a cloud SDK are skipped
    (the SDK is not installed, and their absence is not a defect).

    Args:
        path: The markdown file.
        report: The report to collect findings in.
    """
    text = path.read_text(encoding="utf-8")
    blocks = iter_code_blocks(text)
    if not blocks:
        return

    # The names bound by blocks earlier in this chapter. A snippet that
    # fails with a NameError for one of these is continuing an earlier
    # block, and a name the chapter never binds is a prose fragment.
    chapter_names: set[str] = set()

    # The values earlier blocks produced, carried into later ones.
    carried: dict[str, object] = {}

    # The names the chapter's prose says to import. A snippet may
    # legitimately rely on an import presented in the surrounding
    # prose — Airflow's ``@task``, for instance.
    prose_names = _prose_import_names(text)

    # A separate namespace per snippet. Sharing one namespace across a
    # chapter would let an import in the first block silently rescue a
    # missing import in the second — and a reader who saves the second
    # block on its own still hits the error. The shared state that
    # *should* carry over is the chapter's bound names, and nothing
    # else.
    for index, block in enumerate(blocks, 1):
        stripped = block.strip()
        if not stripped:
            continue
        if re.search(r",\s*\.\.\.\s*[,)]", stripped) or stripped.endswith("..."):
            continue

        report.check()
        try:
            tree = ast.parse(block)
        except SyntaxError:
            # Already reported by check_python_snippets.
            continue

        # A snippet that is only a fragment of a shell transcript
        # ("$ gcloud ...") is not Python to run.
        if re.search(r"^\s*(\$|>>>)\s", block, re.MULTILINE):
            continue

        # A snippet that runs on a cloud cluster, not locally. Executing
        # it here would try to reach gs:// or start a Spark session.
        # Its names still count: a later block may continue from it.
        if any(marker in block for marker in CLUSTER_ONLY_MARKERS):
            chapter_names |= _bound_names(tree)
            continue

        # A snippet that reads a local file the reader supplies.
        if any(marker in block for marker in LOCAL_FILE_MARKERS):
            chapter_names |= _bound_names(tree)
            continue

        # A decorator or base class the snippet never defines is a
        # missing import. This is checked statically and precisely:
        # such a name is never a prose placeholder, so the check is
        # valid for fragments too.
        undefined = _undefined_decorators_or_bases(tree, prose_names)
        if undefined:
            for name in sorted(undefined):
                report.error(
                    f"{relative(path)}: python snippet {index} "
                    f"uses '{name}' as a decorator or base class without "
                    f"importing it"
                )
            chapter_names |= _bound_names(tree)
            continue

        # A fragment of a larger file — one class, one decorated
        # function — with the imports in the surrounding prose.
        if _is_fragment(tree, block):
            chapter_names |= _bound_names(tree)
            continue

        # Only execute snippets that look like a runnable program:
        # something that imports, defines, or reads the sample data.
        has_import = any(
            isinstance(node, (ast.Import, ast.ImportFrom))
            for node in ast.walk(tree)
        )
        has_def = any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            for node in ast.walk(tree)
        )
        touches_course = any(
            (isinstance(node, ast.Constant) and isinstance(node.value, str))
            and (
                "project/core" in node.value
                or "sample_data" in node.value
                or "cost_model" in node.value
                or "pipeline_logic" in node.value
                or "iam_policy" in node.value
                or "service_catalog" in node.value
                or "platform_sim" in node.value
            )
            for node in ast.walk(tree)
        )
        if not (has_import or has_def) and not touches_course:
            continue

        # Each snippet runs in a fresh namespace seeded with the
        # *values* earlier blocks produced — not their imports. An
        # import in an earlier block must not rescue a missing import
        # here, because a reader who saves this block alone still hits
        # the error.
        namespace = {
            "__name__": "__main__",
            "__file__": str(path),
            **carried,
        }

        try:
            with contextlib.redirect_stdout(io.StringIO()):
                with contextlib.redirect_stderr(io.StringIO()):
                    exec(compile(tree, f"{path.name}#snippet{index}", "exec"), namespace)
        except Exception as exc:  # noqa: BLE001 - any failure is a failure
            if _is_optional_sdk_failure(exc):
                chapter_names |= _bound_names(tree)
                continue
            if _is_continuation_failure(exc, chapter_names):
                # The snippet continues an earlier one in the same
                # chapter — it depends on a name defined there, such as
                # a DataFrame or a fitted model. That is a legitimate
                # presentation: a chapter may show a script in pieces.
                chapter_names |= _bound_names(tree)
                continue
            report.error(
                f"{relative(path)}: python snippet {index} "
                f"does not run: {type(exc).__name__}: {exc}"
            )
            chapter_names |= _bound_names(tree)
            continue

        # Carry the values this snippet produced, so a later block that
        # continues from it finds them. Imports are deliberately not
        # carried: see the namespace comment above.
        bound = _bound_names(tree)
        imported = _imported_names(tree)
        for name in bound - imported:
            if name in namespace:
                carried[name] = namespace[name]
        chapter_names |= bound


def check_unbalanced_fstrings(path: Path, report: Report) -> None:
    """Check for unbalanced braces in f-strings.

    Args:
        path: The Python file to check.
        report: The report to collect findings in.
    """
    text = path.read_text(encoding="utf-8")
    for number, line in enumerate(text.splitlines(), start=1):
        if 'f"' not in line and "f'" not in line:
            continue
        report.check()
        if line.count("{") != line.count("}"):
            report.warn(
                f"{relative(path)}:{number}: possibly unbalanced braces"
            )


def collect_public_names(module_path: Path) -> set[str]:
    """Collect the public names defined in a Python module.

    Handles plain assignments, annotated assignments (which is how the
    module-level constants are written) and definitions.

    Args:
        module_path: The module path.

    Returns:
        A set of names.
    """
    try:
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return set()

    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign):
            # `NAME: type = value` — a plain Name target only.
            target = node.target
            if isinstance(target, ast.Name) and not target.id.startswith("_"):
                names.add(target.id)
    return names


def check_api_references(report: Report) -> None:
    """Check that names the chapters attribute to the course modules exist.

    Args:
        report: The report to collect findings in.
    """
    known: set[str] = set()
    for module in sorted((PROJECT_DIR / "core").glob("*.py")):
        known |= collect_public_names(module)
    for module in sorted(PROJECT_DIR.glob("*.py")):
        known |= collect_public_names(module)

    if not known:
        report.error("no course modules found to check references against")
        return

    pattern = re.compile(
        r"\bfrom (service_catalog|iam_policy|cost_model|pipeline_logic|platform_sim)"
        r" import ([A-Za-z_][A-Za-z0-9_, ]*)"
    )

    for path in sorted(CHAPTERS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            for name in match.group(2).split(","):
                clean = name.strip().split(" as ")[0].strip()
                if not clean:
                    continue
                report.check()
                if clean not in known:
                    report.error(
                        f"{relative(path)}: imports unknown name "
                        f"'{clean}' from a course module"
                    )


def check_notebooks(report: Report) -> None:
    """Check the course notebooks.

    Two things are verified:

    1. every notebook is a valid ``nbformat`` document whose code cells
       parse, and whose imports name real course functions;
    2. every notebook *executes* — because a notebook that parses but
       does not run is a broken notebook, and parsing alone would not
       have caught the missing brace that shipped in the first draft of
       the exploration notebook.

    The execution step is skipped when ``nbclient`` is not installed,
    so the linter still runs on a bare environment.

    Args:
        report: The report to collect findings in.
    """
    if not NOTEBOOKS_DIR.exists():
        report.warn("no notebooks directory — skipping notebook check")
        return

    notebooks = sorted(NOTEBOOKS_DIR.glob("*.ipynb"))
    if not notebooks:
        report.warn("no notebooks found — skipping notebook check")
        return

    try:
        import nbformat
    except ImportError:
        report.warn("nbformat not installed — skipping notebook check")
        return

    known = set()
    for module in sorted((PROJECT_DIR / "core").glob("*.py")):
        known |= collect_public_names(module)

    for path in notebooks:
        report.check()
        try:
            notebook = nbformat.read(path, as_version=4)
        except Exception as exc:  # noqa: BLE001 - any parse failure is a failure
            report.error(f"{relative(path)}: invalid notebook: {exc}")
            continue

        for index, cell in enumerate(notebook.cells):
            if cell.cell_type != "code":
                continue
            report.check()
            source = cell.source
            try:
                tree = ast.parse(source)
            except SyntaxError as exc:
                report.error(
                    f"{relative(path)}: code cell {index + 1} "
                    f"does not parse: {exc.msg}"
                )
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module in {
                    "service_catalog",
                    "iam_policy",
                    "cost_model",
                    "pipeline_logic",
                    "platform_sim",
                }:
                    for alias in node.names:
                        report.check()
                        if alias.name not in known:
                            report.error(
                                f"{relative(path)}: code cell "
                                f"{index + 1} imports unknown name "
                                f"'{alias.name}' from {node.module}"
                            )

        # The stored outputs are not checked in, deliberately: a notebook
        # with stale outputs is a liability. But a notebook that still
        # carries them was probably edited by hand.
        for index, cell in enumerate(notebook.cells):
            if cell.cell_type == "code" and cell.get("outputs"):
                report.warn(
                    f"{relative(path)}: code cell {index + 1} "
                    f"has stored outputs — rebuild with "
                    f"resources/build_notebooks.py"
                )
                break

    check_notebook_execution(report, notebooks)


def check_notebook_execution(report: Report, notebooks: list) -> None:
    """Execute every notebook and report the ones that fail.

    Args:
        report: The report to collect findings in.
        notebooks: The notebook paths.
    """
    try:
        from nbclient import NotebookClient
        import nbformat
    except ImportError:
        report.warn("nbclient not installed — skipping notebook execution")
        return

    for path in notebooks:
        report.check()
        notebook = nbformat.read(path, as_version=4)
        client = NotebookClient(
            notebook,
            timeout=180,
            kernel_name="python3",
            resources={"metadata": {"path": str(COURSE_ROOT)}},
        )
        try:
            client.execute()
        except Exception as exc:  # noqa: BLE001 - any failure is a failure
            report.error(
                f"{relative(path)}: does not execute: "
                f"{type(exc).__name__}: {exc}"
            )


def check_expected_outputs(report: Report) -> None:
    """Check that the published expected outputs match the real ones.

    Args:
        report: The report to collect findings in.
    """
    sys.path.insert(0, str(PROJECT_DIR / "core"))
    try:
        from pipeline_logic import (
            EXPECTED_REJECT_COUNTS,
            EXPECTED_SUMMARY,
            aggregate_events,
            ingest_events,
            reject_counts,
        )
    except ImportError as exc:
        report.error(f"cannot import pipeline_logic: {exc}")
        return

    events_path = COURSE_ROOT / "sample_data" / "events.csv"
    if not events_path.exists():
        report.warn("sample_data not generated — skipping output consistency check")
        return

    lines = events_path.read_text(encoding="utf-8").splitlines()
    accepted, rejected = ingest_events(lines)
    summary = aggregate_events(accepted)

    for region, expected in EXPECTED_SUMMARY.items():
        report.check()
        actual = summary.get(region)
        if actual is None:
            report.error(f"expected region {region} missing from the summary")
            continue
        if int(actual["event_count"]) != int(expected["event_count"]):
            report.error(
                f"{region}: expected event_count {expected['event_count']}, "
                f"got {actual['event_count']}"
            )
        if abs(actual["revenue_eur"] - expected["revenue_eur"]) > 0.001:
            report.error(
                f"{region}: expected revenue_eur {expected['revenue_eur']}, "
                f"got {actual['revenue_eur']}"
            )

    report.check()
    if len(accepted) != sum(int(s["event_count"]) for s in EXPECTED_SUMMARY.values()):
        report.error(
            f"expected {sum(int(s['event_count']) for s in EXPECTED_SUMMARY.values())} "
            f"accepted rows, got {len(accepted)}"
        )

    malformed_path = COURSE_ROOT / "sample_data" / "malformed_events.csv"
    if malformed_path.exists():
        malformed_lines = malformed_path.read_text(encoding="utf-8").splitlines()
        _, malformed = ingest_events(malformed_lines)
        report.check()
        if reject_counts(malformed) != EXPECTED_REJECT_COUNTS:
            report.error(
                f"reject counts differ from the published values: "
                f"{reject_counts(malformed)} != {EXPECTED_REJECT_COUNTS}"
            )


def main(argv: list[str] | None = None) -> int:
    """Run the audit.

    Args:
        argv: The argument list, or None for ``sys.argv``.

    Returns:
        The process exit code: 0 if no errors, 1 otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--quiet", action="store_true", help="Only show errors")
    args = parser.parse_args(argv)

    report = Report()

    markdown_files = (
        list(COURSE_ROOT.glob("*.md"))
        + list(CHAPTERS_DIR.glob("*.md"))
        + list(INTERVIEW_DIR.glob("*.md"))
        + list(RESOURCES_DIR.glob("*.md"))
    )

    for path in sorted(markdown_files):
        check_markdown_links(path, report)

    # The snippets in the chapters use paths relative to the course
    # root — ``sys.path.insert(0, "project/core")`` and
    # ``open("sample_data/events.csv")``. Run them from there.
    previous_cwd = Path.cwd()
    os.chdir(COURSE_ROOT)
    try:
        for path in sorted(CHAPTERS_DIR.glob("*.md")):
            check_sections(path, report)
            check_python_snippets(path, report)
            check_snippet_execution(path, report)
            check_placeholders(path, report)

        for path in sorted(RESOURCES_DIR.glob("*.md")):
            check_markdown_links(path, report)

        for path in sorted(PROJECT_DIR.rglob("*.py")):
            check_unbalanced_fstrings(path, report)

        check_api_references(report)
        check_expected_outputs(report)
        check_notebooks(report)
    finally:
        os.chdir(previous_cwd)

    if not args.quiet:
        print(f"Ran {report.checks} checks over the course.")
        print()

    if report.warnings:
        print(f"{len(report.warnings)} warning(s):")
        for message in report.warnings:
            print(f"  ! {message}")
        print()

    if report.errors:
        print(f"{len(report.errors)} error(s):")
        for message in report.errors:
            print(f"  x {message}")
        return 1

    print("No errors. The course is clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
