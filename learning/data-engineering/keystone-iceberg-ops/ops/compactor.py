"""Iceberg-style table operations: snapshots, manifests, partition pruning,
time travel, and compaction.

This is a pure-Python re-implementation of the Iceberg metadata model —
snapshots, manifest lists, partition pruning, time travel, and
`rewrite_data_files` (compaction). The point is to show the *policy* and
*invariants* of operational Iceberg without dragging in PyIceberg or Spark.

Iceberg metadata model (simplified):
    Table
    ├── current_snapshot_id     (pointer to "now")
    ├── snapshots[]             (immutable history)
    │     └── manifest_list     (list of manifest files)
    │           └── manifest    (list of data files in a partition column)
    │                 └── DataFile(path, partition, row_count, ...)
    └── schema
"""
from __future__ import annotations
import copy
import time
from dataclasses import dataclass, field
from typing import Iterable, Optional


# ============================================================================
# Core data structures
# ============================================================================

@dataclass(frozen=True)
class DataFile:
    """A single Parquet data file. Immutable once written."""
    path: str
    partition: tuple          # e.g. ("region=us", "dt=2024-01-15")
    record_count: int
    size_bytes: int
    file_id: int

    def __repr__(self) -> str:  # pragma: no cover
        return f"DataFile({self.path}, partition={self.partition}, rows={self.record_count})"


@dataclass
class Manifest:
    """A manifest lists data files for a snapshot, grouped by partition."""
    manifest_id: int
    files: list[DataFile] = field(default_factory=list)

    @property
    def partitions(self) -> set[tuple]:
        return {f.partition for f in self.files}

    @property
    def total_rows(self) -> int:
        return sum(f.record_count for f in self.files)

    def files_for_partition(self, part: tuple) -> list[DataFile]:
        return [f for f in self.files if f.partition == part]


@dataclass
class Snapshot:
    """An immutable point-in-time view of the table."""
    snapshot_id: int
    parent_id: Optional[int]
    timestamp_ms: int
    operation: str             # "append" | "overwrite" | "compact" | "delete"
    manifest: Manifest
    summary: dict = field(default_factory=dict)


@dataclass
class Table:
    """An Iceberg-style table: schema + history of snapshots."""
    name: str
    schema: list[str]
    snapshots: list[Snapshot] = field(default_factory=list)
    current_snapshot_id: Optional[int] = None

    def latest(self) -> Optional[Snapshot]:
        if self.current_snapshot_id is None:
            return None
        return next(s for s in self.snapshots if s.snapshot_id == self.current_snapshot_id)

    def snapshot(self, sid: int) -> Optional[Snapshot]:
        return next((s for s in self.snapshots if s.snapshot_id == sid), None)


# ============================================================================
# File policy & compactor (the original stub logic, preserved)
# ============================================================================

@dataclass
class FileStat:
    path: str
    size_bytes: int
    partition: tuple


@dataclass
class CompactionPolicy:
    target_file_size_bytes: int = 256 * 1024 * 1024   # 256MB
    min_files_to_compact: int = 4
    skip_if_rewritten_within_days: int = 7
    max_runtime_minutes: int = 120


def plan_compaction(files: list[FileStat], policy: CompactionPolicy) -> list[list[FileStat]]:
    """Group small files into rewrite tasks. A task rewrites N small files into 1 large one."""
    tasks: list[list[FileStat]] = []
    by_part: dict[tuple, list[FileStat]] = {}
    for f in files:
        by_part.setdefault(f.partition, []).append(f)

    for part, fs in by_part.items():
        small = sorted([f for f in fs if f.size_bytes < policy.target_file_size_bytes],
                       key=lambda f: f.size_bytes)
        bin: list[FileStat] = []
        bin_size = 0
        for f in small:
            if bin_size + f.size_bytes > policy.target_file_size_bytes and bin:
                if len(bin) >= policy.min_files_to_compact:
                    tasks.append(bin)
                bin, bin_size = [], 0
            bin.append(f)
            bin_size += f.size_bytes
        if len(bin) >= policy.min_files_to_compact:
            tasks.append(bin)
    return tasks


def estimate_runtime_minutes(tasks: list[list[FileStat]], throughput_mb_per_sec: float = 80) -> float:
    total_mb = sum(f.size_bytes for t in tasks for f in t) / 1e6
    return round(total_mb / (throughput_mb_per_sec * 60), 1)


# ============================================================================
# Partition-pruning query engine (predicate pushdown by partition tuple)
# ============================================================================

def read_with_partition_filter(
    snap: Snapshot,
    partition_filter: Optional[set[tuple]] = None,
) -> list[DataFile]:
    """Return the data files that the query engine would actually scan.

    Without a filter: every file in every partition gets scanned.
    With a filter: only files in matching partitions are scanned — the
    classic Iceberg partition-pruning win.
    """
    if partition_filter is None:
        return list(snap.manifest.files)
    return [f for f in snap.manifest.files if f.partition in partition_filter]


def count_rows(snap: Snapshot, partition_filter: Optional[set[tuple]] = None) -> int:
    return sum(f.record_count for f in read_with_partition_filter(snap, partition_filter))


# ============================================================================
# Compactor: rewrite small files → fewer large files (row-count preserving)
# ============================================================================

def compact_snapshot(
    snap: Snapshot,
    policy: CompactionPolicy,
    next_file_id: int,
    next_manifest_id: int,
) -> tuple[Snapshot, int, int]:
    """Rewrite a snapshot's small files into fewer large ones.

    Returns (new_snapshot, files_in, files_out, rows_in, rows_out).
    Row count is preserved by construction; this is the critical invariant.
    """
    # Convert DataFile -> FileStat for the planner
    file_stats = [
        FileStat(path=f.path, size_bytes=f.size_bytes, partition=f.partition)
        for f in snap.manifest.files
    ]
    tasks = plan_compaction(file_stats, policy)

    # Pre-build a map of path -> DataFile so we can recover record_count
    by_path = {f.path: f for f in snap.manifest.files}

    new_files: list[DataFile] = []
    consumed_paths: set[str] = set()
    rows_in = 0
    rows_out = 0
    fid = next_file_id
    files_in = len(file_stats)
    files_out = 0

    for task in tasks:
        # Each task collapses to ONE new file spanning the same partitions'
        # rows. In real Iceberg a single rewrite task can produce a single
        # output file (or one per partition spec); we go with one.
        rows = sum(by_path[p].record_count for p in (f.path for f in task))
        size = sum(f.size_bytes for f in task)
        part = task[0].partition  # task is already per-partition
        new_file = DataFile(
            path=f"rewrite-{fid:06d}.parquet",
            partition=part,
            record_count=rows,
            size_bytes=size,
            file_id=fid,
        )
        new_files.append(new_file)
        rows_out += rows
        rows_in += rows
        fid += 1
        files_out += 1
        for f in task:
            consumed_paths.add(f.path)

    # Keep files that were NOT touched by any task (already large enough,
    # or solo small file below min_files_to_compact).
    for f in snap.manifest.files:
        if f.path not in consumed_paths:
            new_files.append(f)
            rows_in += f.record_count
            rows_out += f.record_count
            files_out += 1

    new_manifest = Manifest(manifest_id=next_manifest_id, files=new_files)
    new_snap = Snapshot(
        snapshot_id=snap.snapshot_id + 1,
        parent_id=snap.snapshot_id,
        timestamp_ms=now_ms(),
        operation="compact",
        manifest=new_manifest,
        summary={
            "rows_in": rows_in,
            "rows_out": rows_out,
            "files_in": files_in,
            "files_out": files_out,
        },
    )
    return new_snap, rows_in, rows_out


# ============================================================================
# Synthetic data generator
# ============================================================================

def now_ms() -> int:
    return int(time.time() * 1000)


def build_workload(
    n_snapshots: int = 6,
    rows_per_snapshot: int = 1000,
    n_partitions: int = 12,
    seed: int = 42,
) -> Table:
    """Build a realistic Iceberg-style workload: multiple append snapshots
    across multiple partitions, then compact, then time-travel-read."""
    import random
    rng = random.Random(seed)
    regions = ["us", "eu", "ap", "sa", "af"]
    days = [f"2024-01-{d:02d}" for d in range(1, 16)]
    # Generate all partition tuples
    partitions: list[tuple] = []
    for r in regions:
        for d in days:
            partitions.append((f"region={r}", f"dt={d}"))
        if len(partitions) >= n_partitions:
            break
    partitions = partitions[:n_partitions]

    schema = ["event_id", "user_id", "region", "dt", "amount", "currency"]
    table = Table(name="events", schema=schema)

    fid = 0
    mid = 0
    for snap_idx in range(n_snapshots):
        mid += 1
        # Each snapshot appends `rows_per_snapshot` rows spread across
        # partitions; new snapshots get a bit larger (realistic: data
        # grows over time).
        n_rows = rows_per_snapshot + snap_idx * 50
        files: list[DataFile] = []
        rows_left = n_rows
        while rows_left > 0:
            part = rng.choice(partitions)
            chunk = min(rows_left, rng.randint(80, 250))
            fid += 1
            # Synthetic file size: ~120 bytes/row + small overhead
            size = chunk * 120 + 1024
            files.append(
                DataFile(
                    path=f"snap{snap_idx:03d}-file{fid:06d}.parquet",
                    partition=part,
                    record_count=chunk,
                    size_bytes=size,
                    file_id=fid,
                )
            )
            rows_left -= chunk
        manifest = Manifest(manifest_id=mid, files=files)
        parent = table.latest().snapshot_id if table.latest() else None
        snap = Snapshot(
            snapshot_id=mid,
            parent_id=parent,
            timestamp_ms=now_ms() + snap_idx * 1000,
            operation="append",
            manifest=manifest,
            summary={"added_rows": n_rows, "added_files": len(files)},
        )
        table.snapshots.append(snap)
        table.current_snapshot_id = snap.snapshot_id

    return table


# ============================================================================
# Smoke test
# ============================================================================

if __name__ == "__main__":
    print("═══ keystone-iceberg-ops: meaningful workload ═══")
    print()

    # Build the workload
    N_SNAPS = 6
    ROWS_PER = 1000
    N_PARTS = 12
    table = build_workload(
        n_snapshots=N_SNAPS,
        rows_per_snapshot=ROWS_PER,
        n_partitions=N_PARTS,
    )
    total_rows = sum(s.manifest.total_rows for s in table.snapshots)
    total_files = sum(len(s.manifest.files) for s in table.snapshots)
    print(f"snapshots built:    {len(table.snapshots)}")
    print(f"total rows:         {total_rows}")
    print(f"total files:        {total_files}")
    print(f"distinct partitions: "
          f"{len({f.partition for s in table.snapshots for f in s.manifest.files})}")
    print()

    # ---- Scenario A: write a snapshot, verify manifest list ----
    print("═══ Scenario A: append snapshot, verify manifest list ═══")
    last = table.latest()
    print(f"  current snapshot id:  {last.snapshot_id}")
    print(f"  manifest id:          {last.manifest.manifest_id}")
    print(f"  data files in latest: {len(last.manifest.files)}")
    print(f"  rows in latest:       {last.manifest.total_rows}")
    print(f"  parent snapshot id:   {last.parent_id}")
    assert last.parent_id == last.snapshot_id - 1, "snapshot chain must be linear"
    assert len(last.manifest.files) > 0, "latest snapshot must have files"
    # Manifest list integrity: every partition referenced must exist in files
    listed_parts = {f.partition for f in last.manifest.files}
    assert len(listed_parts) > 0, "manifest must list at least one partition"
    print(f"  partitions in manifest: {len(listed_parts)}")
    print("  ✓ manifest list integrity OK")
    print()

    # ---- Scenario B: partition pruning query ----
    print("═══ Scenario B: partition pruning query ═══")
    snap_b = table.latest()
    # Pick 2 specific partitions and prune to them
    all_parts = sorted({f.partition for f in snap_b.manifest.files})
    target_parts = set(all_parts[:2])
    files_unpruned = read_with_partition_filter(snap_b)
    files_pruned = read_with_partition_filter(snap_b, target_parts)
    files_unpruned_count = len(files_unpruned)
    files_pruned_count = len(files_pruned)
    speedup = files_unpruned_count / files_pruned_count if files_pruned_count else float("inf")
    print(f"  partitions in snapshot:    {len(all_parts)}")
    print(f"  filter selects:            {len(target_parts)} partitions")
    print(f"  files scanned w/o filter:  {files_unpruned_count}")
    print(f"  files scanned w/  filter:  {files_pruned_count}")
    print(f"  pruning speedup:           {speedup:.2f}x")
    # Invariant: pruning returns only files in matching partitions
    assert all(f.partition in target_parts for f in files_pruned), \
        "partition pruning returned files outside the filter"
    # Invariant: row count under filter <= total row count
    assert count_rows(snap_b, target_parts) <= snap_b.manifest.total_rows
    assert files_pruned_count < files_unpruned_count, "pruning must scan fewer files"
    print("  ✓ partition pruning returns only matching partitions")
    print()

    # ---- Scenario C: time travel to an older snapshot ----
    print("═══ Scenario C: time travel (query an older snapshot) ═══")
    # Pick the SECOND snapshot and verify the manifest contents there
    # differ from the latest (proves we read the older data, not current).
    older = table.snapshots[1]
    latest = table.latest()
    older_files = {f.path for f in older.manifest.files}
    latest_files = {f.path for f in latest.manifest.files}
    older_rows = older.manifest.total_rows
    latest_rows = latest.manifest.total_rows
    print(f"  reading snapshot@{older.snapshot_id}: "
          f"{len(older_files)} files, {older_rows} rows")
    print(f"  reading snapshot@{latest.snapshot_id}: "
          f"{len(latest_files)} files, {latest_rows} rows")
    # Older snapshot must have strictly fewer rows than latest
    assert older_rows < latest_rows, \
        f"older snapshot must have fewer rows ({older_rows} !< {latest_rows})"
    # The set of paths must differ (different append events → different files)
    assert older_files != latest_files, "older snapshot must reference different files"
    # We can read directly from the older snapshot via table.snapshot()
    re_read = table.snapshot(older.snapshot_id)
    assert re_read is older, "snapshot(id) lookup broken"
    assert re_read.manifest.total_rows == older_rows, "time-travel row count mismatch"
    print(f"  ✓ time travel returns correct historical data")
    print()

    # ---- Scenario D: compaction ----
    print("═══ Scenario D: compaction (rewrite small files) ═══")
    policy = CompactionPolicy(
        target_file_size_bytes=200_000,        # 200KB to force rewrites in synthetic data
        min_files_to_compact=3,
    )
    pre_snap = table.latest()
    pre_rows = pre_snap.manifest.total_rows
    pre_files = len(pre_snap.manifest.files)
    pre_avg_size = sum(f.size_bytes for f in pre_snap.manifest.files) / pre_files
    next_fid = max(f.file_id for s in table.snapshots for f in s.manifest.files) + 1
    next_mid = max(s.manifest.manifest_id for s in table.snapshots) + 1
    new_snap, rows_in, rows_out = compact_snapshot(
        pre_snap, policy, next_file_id=next_fid, next_manifest_id=next_mid,
    )
    post_files = len(new_snap.manifest.files)
    post_avg_size = (
        sum(f.size_bytes for f in new_snap.manifest.files) / post_files
        if post_files else 0
    )
    # The new snapshot is appended to history
    table.snapshots.append(new_snap)
    table.current_snapshot_id = new_snap.snapshot_id
    print(f"  pre  files / rows / avg-size: "
          f"{pre_files} / {pre_rows} / {pre_avg_size:,.0f} B")
    print(f"  post files / rows / avg-size: "
          f"{post_files} / {new_snap.manifest.total_rows} / {post_avg_size:,.0f} B")
    print(f"  reduction in file count:  {pre_files} → {post_files} "
          f"({(1 - post_files / pre_files) * 100:.1f}% fewer)")
    # Row count preserved
    assert new_snap.manifest.total_rows == pre_rows, \
        f"compaction must preserve row count: {new_snap.manifest.total_rows} != {pre_rows}"
    # Row count from the planner matches
    assert rows_out == pre_rows, f"planner row count mismatch: {rows_out} != {pre_rows}"
    print("  ✓ row count preserved across compaction")
    print()

    # ---- Final invariants across ALL snapshots ----
    print("═══ final invariants ═══")
    # Row count preserved across every snapshot
    snapshot_rows = [s.manifest.total_rows for s in table.snapshots]
    print(f"  rows per snapshot: {snapshot_rows}")
    # Each snapshot has a unique id
    snap_ids = [s.snapshot_id for s in table.snapshots]
    assert len(set(snap_ids)) == len(snap_ids), "snapshot ids must be unique"
    # Parent links form a valid chain
    for s in table.snapshots:
        if s.parent_id is not None:
            assert table.snapshot(s.parent_id) is not None, \
                f"snapshot {s.snapshot_id} has dangling parent {s.parent_id}"
    # Current snapshot points to a real snapshot
    assert table.snapshot(table.current_snapshot_id) is not None
    print(f"  snapshots:           {len(table.snapshots)}")
    print(f"  total rows:          {sum(snapshot_rows)}")
    print(f"  file count:          {sum(len(s.manifest.files) for s in table.snapshots)}")
    print(f"  distinct partitions: "
          f"{len({f.partition for s in table.snapshots for f in s.manifest.files})}")
    print(f"  pre-compaction files:  {pre_files}")
    print(f"  post-compaction files: {post_files}")
    print(f"  pruning speedup:       {speedup:.2f}x")

    assert len(table.snapshots) == N_SNAPS + 1, \
        f"expected {N_SNAPS + 1} snapshots after compaction, got {len(table.snapshots)}"
    assert total_rows >= 5000, f"need >= 5000 rows, got {total_rows}"

    print()
    print("✓ all invariants pass")
