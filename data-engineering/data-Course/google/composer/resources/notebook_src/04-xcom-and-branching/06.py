from pathlib import Path
import sys

COURSE_ROOT = Path.cwd()
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent
if not (COURSE_ROOT / "project").exists():
    COURSE_ROOT = Path.cwd().parent.parent
sys.path.insert(0, str(COURSE_ROOT / "project" / "core"))
sys.path.insert(0, str(COURSE_ROOT / "project"))

print("COURSE_ROOT =", COURSE_ROOT)
print("project/ present:", (COURSE_ROOT / "project").exists())
print("core/ present:", (COURSE_ROOT / "project" / "core").exists())

class MetadataDB:
    """A minimal model of the table XCom values live in."""

    def __init__(self):
        self.rows = []          # (dag_id, task_id, run_id, key, value, size)
        self.read_count = 0

    def insert(self, dag_id, task_id, run_id, key, value):
        size = len(str(value).encode("utf-8"))
        self.rows.append((dag_id, task_id, run_id, key, value, size))
        return size

    def select(self, dag_id, task_id, run_id, key):
        self.read_count += 1
        for row in self.rows:
            if (
                row[0] == dag_id
                and row[1] == task_id
                and row[2] == run_id
                and row[3] == key
            ):
                return row[4]
        return None

    def total_bytes(self):
        return sum(row[5] for row in self.rows)


db = MetadataDB()
run_id = "scheduled__2026-01-15T00:00:00+00:00"

# One control value.
db.insert("etl_to_gcs", "transform", run_id, "return_value", {"accepted_count": 1245})
# One reference.
db.insert(
    "etl_to_gcs", "transform", run_id, "gcs_path",
    "gs://bucket/orders/2026-01-15/orders.jsonl",
)
# One BAD push: the whole dataset.
db.insert(
    "etl_to_gcs", "transform", run_id, "rows",
    [{"order_id": f"o{n}"} for n in range(1245)],
)

print(f"rows in xcom table : {len(db.rows)}")
print(f"total bytes stored : {db.total_bytes():,}")
print()
for row in db.rows:
    print(f"  key={row[3]:<15} size={row[5]:>9,} bytes")
print()
print("The 'rows' key dominates. And it was ONE push.")
print()
print("Each pull is a SELECT - a database round trip:")
before = db.read_count
for _ in range(5):
    db.select("etl_to_gcs", "transform", run_id, "return_value")
print(f"  5 pulls -> {db.read_count - before} reads against the metadata DB")
print()
print("In a DAG with 100 tasks each pulling one XCom value, that is 100")
print("queries against the same database the scheduler uses. On a loaded")
print("Composer environment, that is measurable latency.")
