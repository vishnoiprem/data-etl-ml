"""Validate the interview bank: counts, cross-references, link targets, anatomy,
and every `Check yourself` block.

Run from the `interview/` directory:

    python3 _verify_bank.py
"""

import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
COURSE = HERE.parent

REQUIRED = [
    "**Answer.**",
    "**Mechanism.**",
    "**Trade-off.**",
    "**In practice.**",
    "**Check yourself.**",
]

TOPICS = [
    "01-platform-fundamentals.md",
    "02-storage-and-databases.md",
    "03-analytics-and-cost.md",
    "04-streaming-and-ingestion.md",
    "05-processing-and-orchestration.md",
    "06-governance-security-and-ml.md",
    "07-query-optimization.md",
]

# The numbers quoted in README.md's file table.
EXPECTED_COUNTS = {
    "01-platform-fundamentals.md": 14,
    "02-storage-and-databases.md": 14,
    "03-analytics-and-cost.md": 19,
    "04-streaming-and-ingestion.md": 14,
    "05-processing-and-orchestration.md": 16,
    "06-governance-security-and-ml.md": 14,
    "07-query-optimization.md": 20,
    "top-40.md": 46,
}


def count_questions(text: str) -> int:
    return len(re.findall(r"^### Q\d+\.", text, flags=re.M))


def main() -> int:
    failures = 0

    print("== question counts ==")
    actual = {}
    for name in EXPECTED_COUNTS:
        path = HERE / name
        if not path.exists():
            print(f"  {name}: MISSING")
            failures += 1
            continue
        n = count_questions(path.read_text())
        actual[name] = n
        expected = EXPECTED_COUNTS[name]
        status = "ok" if n == expected else "MISMATCH"
        if n != expected:
            failures += 1
        print(f"  {name}: {n} (expected {expected}) {status}")

    total = sum(actual.values())
    print(f"  total: {total}")

    print("\n== README table consistency ==")
    readme = (HERE / "README.md").read_text()
    for name, n in EXPECTED_COUNTS.items():
        row = re.search(rf"\| \[`{re.escape(name)}`\]\([^)]+\) \| (\d+) \|", readme)
        if not row:
            print(f"  {name}: no README row")
            failures += 1
            continue
        stated = int(row.group(1))
        if stated != n:
            print(f"  {name}: README says {stated}, file has {n}")
            failures += 1
        else:
            print(f"  {name}: {stated} ok")

    total_row = re.search(r"\| \*\*Total\*\* \| \*\*(\d+)\*\*", readme)
    if total_row:
        stated_total = int(total_row.group(1))
        if stated_total != total:
            print(f"  Total: README says {stated_total}, files total {total}")
            failures += 1
        else:
            print(f"  Total: {stated_total} ok")

    print("\n== required sections per question ==")
    for name in TOPICS:
        text = (HERE / name).read_text()
        parts = re.split(r"^### Q(\d+)\.", text, flags=re.M)
        for i in range(1, len(parts), 2):
            qn, body = parts[i], parts[i + 1]
            missing = [r for r in REQUIRED if r not in body]
            if missing:
                print(f"  {name} Q{qn}: missing {missing}")
                failures += 1
        print(f"  {name}: checked")

    print("\n== cross-references (topic file + question number) ==")
    for name in TOPICS:
        text = (HERE / name).read_text()
        for label, target in re.findall(
            r"\[(\d\d-[a-z-]+\.md) Q(\d+)\]\(\1\)", text
        ):
            target_path = HERE / target
            if not target_path.exists():
                print(f"  {name}: missing file {target}")
                failures += 1
                continue
            n = count_questions(target_path.read_text())
            if int(target) > n:
                print(f"  {name}: {target} Q{target} does not exist (file has {n})")
                failures += 1
    print("  checked")

    print("\n== markdown link targets ==")
    for path in sorted(HERE.glob("*.md")):
        text = path.read_text()
        for link in re.findall(r"\]\(([^)#][^)]*)\)", text):
            if link.startswith("http"):
                continue
            target = (HERE / link).resolve()
            if not target.exists():
                print(f"  {path.name}: broken link -> {link}")
                failures += 1
    print("  checked")

    print("\n== no placeholder markers ==")
    for path in sorted(HERE.glob("*.md")):
        text = path.read_text()
        for marker in ("TODO", "FIXME", "XXX"):
            if marker in text:
                print(f"  {path.name}: contains {marker}")
                failures += 1
    print("  checked")

    print("\n== `Check yourself` blocks execute ==")
    failures += run_check_yourself()

    print(f"\nfailures: {failures}")
    return 1 if failures else 0


# A `Check yourself` block: the python fence that follows the header.
CHECK_BLOCK = re.compile(r"\*\*Check yourself\.\*\*[^\n]*\n```python\n(.*?)```", re.S)

# A `Check yourself` block that also quotes its expected output.
OUTPUT_BLOCK = re.compile(
    r"```python\n(.*?)```\n\nExpected output:\n\n```text\n(.*?)```",
    re.S,
)


def run_check_yourself() -> int:
    """Execute every `Check yourself` block against the course's own modules.

    Blocks that quote an `Expected output:` are diffed against it; the rest
    are only required to run without raising.
    """
    tmp = pathlib.Path(tempfile.mkdtemp())
    shutil.copytree(COURSE / "resources", tmp / "resources", dirs_exist_ok=True)
    (tmp / "project").mkdir(exist_ok=True)
    shutil.copytree(
        COURSE / "project" / "core", tmp / "project" / "core", dirs_exist_ok=True
    )
    subprocess.run(
        [
            sys.executable,
            str(tmp / "resources" / "sample_data.py"),
            "--output-dir",
            str(tmp / "sample_data"),
        ],
        capture_output=True,
        text=True,
        cwd=tmp,
    )

    failures = 0
    total = 0
    for path in sorted(p for p in HERE.glob("*.md") if p.name[0].isdigit()):
        text = path.read_text()
        parts = re.split(r"^### Q(\d+)\.", text, flags=re.M)
        for i in range(1, len(parts), 2):
            number, body = parts[i], parts[i + 1]
            expected = dict(
                (code.strip(), out.strip()) for code, out in OUTPUT_BLOCK.findall(body)
            )
            for code in CHECK_BLOCK.findall(body):
                total += 1
                script = tmp / "block.py"
                script.write_text(code)
                result = subprocess.run(
                    [sys.executable, str(script)],
                    capture_output=True,
                    text=True,
                    cwd=tmp,
                )
                if result.returncode != 0:
                    failures += 1
                    print(f"  {path.name} Q{number}: ERROR")
                    print(result.stderr.strip()[-600:])
                    continue
                want = expected.get(code.strip())
                if want is not None and result.stdout.strip() != want:
                    failures += 1
                    print(f"  {path.name} Q{number}: MISMATCH")
                    print(f"    expected: {want[:300]!r}")
                    print(f"    actual:   {result.stdout.strip()[:300]!r}")
    print(f"  blocks executed: {total}   failures: {failures}")
    return failures


if __name__ == "__main__":
    sys.exit(main())
