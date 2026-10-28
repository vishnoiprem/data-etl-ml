"""Print the stdout of an executed notebook."""
import sys
import nbformat

nb = nbformat.read(sys.argv[1], as_version=4)
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 1500
for i, cell in enumerate(nb.cells):
    if cell.cell_type != "code":
        continue
    for output in cell.get("outputs", []):
        text = output.get("text") or ""
        if text:
            print(f"--- cell {i} ---")
            print(text[:limit])
