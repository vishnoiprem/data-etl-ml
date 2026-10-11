"""
Iceberg table compactor.

Rewrites small Parquet files into larger ones, keeping the manifest
tidy. Real impl: PyIceberg + Spark; this is the policy layer.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


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
    # group by partition
    by_part: dict[tuple, list[FileStat]] = {}
    for f in files:
        by_part.setdefault(f.partition, []).append(f)

    for part, fs in by_part.items():
        # only files below target
        small = sorted([f for f in fs if f.size_bytes < policy.target_file_size_bytes], key=lambda f: f.size_bytes)
        # greedy bin-packing
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


if __name__ == "__main__":
    files = [
        FileStat("a.parquet", 16_000_000,  ("p", "2024-01-01")),
        FileStat("b.parquet",  8_000_000,  ("p", "2024-01-01")),
        FileStat("c.parquet", 32_000_000,  ("p", "2024-01-01")),
        FileStat("d.parquet", 12_000_000,  ("p", "2024-01-01")),
        FileStat("e.parquet", 24_000_000,  ("p", "2024-01-01")),
    ]
    tasks = plan_compaction(files, CompactionPolicy())
    print(f"{len(tasks)} rewrite tasks; est {estimate_runtime_minutes(tasks)} min")
