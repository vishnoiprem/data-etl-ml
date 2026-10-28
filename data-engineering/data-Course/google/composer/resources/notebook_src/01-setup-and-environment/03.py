import json
from pathlib import Path

# Find every notebook in the course and confirm none of them import airflow.
NOTEBOOK_DIR = Path.cwd()
if not (NOTEBOOK_DIR / "notebooks").exists():
    NOTEBOOK_DIR = Path.cwd().parent

notebook_paths = sorted((NOTEBOOK_DIR / "notebooks").glob("*.ipynb"))
print(f"found {len(notebook_paths)} notebooks in {NOTEBOOK_DIR / 'notebooks'}\n")

offenders = []
for path in notebook_paths:
    nb = json.loads(path.read_text(encoding="utf-8"))
    for index, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith(("import airflow", "from airflow")):
                offenders.append((path.name, index, stripped))

if offenders:
    print("AIRFLOW IMPORTS FOUND (these would break the course premise):")
    for name, index, line in offenders:
        print(f"  {name} cell {index}: {line}")
else:
    print("PASS: no notebook imports airflow. The course premise holds.")
