"""
Problem 07: State checkpoint (save progress, resume on failure)
Meta flavor: "A nightly job iterates 2000 ad accounts. After account #1234 it
crashes. Re-running from scratch would burn 12 hours again. With a
checkpoint file we resume from #1235 in seconds."

How to Think:
- Define a checkpoint = the smallest unit of work that is safe to redo. Here:
  "last successfully processed account_id".
- Persist it to durable storage (local file, S3, Redis) after every successful
  unit.
- On startup, load the checkpoint; if present, skip ahead to the next item.
- Combine with atomic writes: each unit's output must be idempotent so that
  re-running a unit on restart does not double-write.

How to Remember:
- Checkpoint = progress marker, not a transactional undo log.

AI Use Cases
- Long-running Meta Ads data pulls (Insights sync, creative sync).
- Crawling large link/URL graphs.
"""
from __future__ import annotations
from pathlib import Path
import json
from typing import Callable, Iterable


def run_with_checkpoint(items: Iterable[str], process: Callable[[str], None],
                        checkpoint_path: Path,
                        resume_marker: str = "__RESUME__") -> list[str]:
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    start_from = 0
    if checkpoint_path.exists():
        start_from = int(checkpoint_path.read_text().strip() or "0")

    processed: list[str] = []
    for idx, item in enumerate(items):
        if idx < start_from:
            continue
        process(item)
        processed.append(item)
        # atomic checkpoint write
        tmp = checkpoint_path.with_suffix(".tmp")
        tmp.write_text(str(idx + 1))
        tmp.replace(checkpoint_path)
    return processed


if __name__ == "__main__":
    import shutil
    cp = Path("/tmp/_etl_demo_checkpoint.txt")
    if cp.exists():
        cp.unlink()

    def work(acc: str) -> None:
        print(" processed", acc)

    items = [f"acc_{i}" for i in range(5)]
    # First run -- process all, simulate crash after 2 by truncating items.
    # Here we just call once; second call below resumes (no-op since all done).
    run_with_checkpoint(items, work, cp)
    print("checkpoint:", cp.read_text())

    # Simulate resume: same checkpoint file present, fresh items list.
    run_with_checkpoint(items, work, cp)
    # If we had crashed at idx=2, the file would say "2"; on resume we'd skip
    # acc_0, acc_1, acc_2 and process acc_3, acc_4 only.
