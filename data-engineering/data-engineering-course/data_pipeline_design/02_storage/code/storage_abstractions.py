"""Storage abstractions: Source, Sink, BatchSink, StreamSink.

These are the smallest useful vocabulary for talking about the
left and right edges of a pipeline. The classes in this file are
the substrate every other module in this track builds on:

  * ``CsvSource``  — reads a CSV file
  * ``SqliteSink`` — writes to a SQLite table
  * ``MemorySink`` — accumulates rows in a Python list (testing)
  * ``BatchSink``  — decorates any Sink to flush on a threshold

The Pipeline class in ``common.pipeline`` accepts any callable for
extract and load, so a Source's ``read()`` and a Sink's ``write()``
slot in directly::

    Pipeline("csv_to_sqlite", CsvSource(path).read, transform, sink.write)

The classes here are intentionally tiny — they exist to anchor
the vocabulary, not to be a production storage layer. Real
sources are Kafka, Postgres CDC, REST APIs; real sinks are
Delta, Snowflake, BigQuery. The lesson is that every one of
those can be modeled as ``read() -> Iterator[dict]`` or
``write(rows: list[dict]) -> None``.

Author: Prem Vishnoi <prem.vishnoi@example.com>
"""

from __future__ import annotations

import csv
import sqlite3
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional, Sequence, Union


# ---- abstract bases ----------------------------------------------------


class Source(ABC):
    """A pipeline source. ``read()`` returns an iterator of dicts.

    Every concrete source in this track implements ``read()`` the
    same way: yield a dict per row, with stable string keys.
    """

    @abstractmethod
    def read(self) -> Iterator[Dict[str, Any]]:
        """Yield rows one at a time."""
        raise NotImplementedError

    def to_list(self) -> List[Dict[str, Any]]:
        """Eager materialization — useful for tests and small sources."""
        return list(self.read())


class Sink(ABC):
    """A pipeline sink. ``write(rows)`` accepts a batch of dicts."""

    @abstractmethod
    def write(self, rows: Sequence[Dict[str, Any]]) -> None:
        """Write a batch of rows. May be called multiple times."""
        raise NotImplementedError


class StreamSink(Sink):
    """A sink that accepts rows one at a time.

    The default ``write`` is just a list.append; subclasses that
    care about per-row latency (e.g. Kafka) override ``write_one``.
    """

    def write(self, rows: Sequence[Dict[str, Any]]) -> None:
        for row in rows:
            self.write_one(row)

    @abstractmethod
    def write_one(self, row: Dict[str, Any]) -> None:
        raise NotImplementedError


# ---- concrete sources --------------------------------------------------


class CsvSource(Source):
    """Read rows from a CSV file.

    The header row provides the keys. Values are returned as
    strings; downstream transforms are responsible for typing.
    """

    def __init__(self, path: str) -> None:
        self.path = path

    def read(self) -> Iterator[Dict[str, str]]:
        with open(self.path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield dict(row)


class InMemorySource(Source):
    """A source backed by a list of dicts — useful for tests."""

    def __init__(self, rows: Sequence[Dict[str, Any]]) -> None:
        self._rows = list(rows)

    def read(self) -> Iterator[Dict[str, Any]]:
        for row in self._rows:
            yield dict(row)


# ---- concrete sinks ----------------------------------------------------


class MemorySink(Sink):
    """A sink that accumulates rows in a list.

    Tests use this to assert what was written without a database.
    The accumulated list is exposed via ``.rows``.
    """

    def __init__(self) -> None:
        self.rows: List[Dict[str, Any]] = []

    def write(self, rows: Sequence[Dict[str, Any]]) -> None:
        self.rows.extend(dict(r) for r in rows)

    def __len__(self) -> int:
        return len(self.rows)


class SqliteSink(Sink):
    """A sink that writes rows to a SQLite table.

    The first call to ``write`` ensures the table exists with the
    correct schema. Subsequent calls ``INSERT`` rows in batched
    transactions. Column types are inferred from the first row.
    """

    def __init__(
        self,
        conn: sqlite3.Connection,
        table: str,
        *,
        pk: Optional[str] = None,
        replace_on_pk: bool = False,
    ) -> None:
        self.conn = conn
        self.table = table
        self.pk = pk
        self.replace_on_pk = replace_on_pk
        self._schema_ready = False
        self._columns: List[str] = []

    def _ensure_schema(self, sample: Dict[str, Any]) -> None:
        if self._schema_ready:
            return
        # Pick a stable column order: the sample's key order, then
        # any subsequent keys we haven't seen yet.
        self._columns = list(sample.keys())
        col_defs: List[str] = []
        for col in self._columns:
            value = sample[col]
            if isinstance(value, bool):
                col_defs.append(f'"{col}" INTEGER')
            elif isinstance(value, int):
                col_defs.append(f'"{col}" INTEGER')
            elif isinstance(value, float):
                col_defs.append(f'"{col}" REAL')
            else:
                col_defs.append(f'"{col}" TEXT')
        if self.pk:
            col_defs.append(f'PRIMARY KEY ("{self.pk}")')
        ddl = (
            f'CREATE TABLE IF NOT EXISTS "{self.table}" '
            f'({", ".join(col_defs)})'
        )
        self.conn.execute(ddl)
        self.conn.commit()
        self._schema_ready = True

    def write(self, rows: Sequence[Dict[str, Any]]) -> None:
        if not rows:
            return
        self._ensure_schema(rows[0])
        # Allow new columns in subsequent batches (a real pipeline
        # would validate via a schema registry; we keep the door
        # open by adding columns on demand).
        for row in rows:
            for col in row.keys():
                if col not in self._columns:
                    self._columns.append(col)
                    self.conn.execute(
                        f'ALTER TABLE "{self.table}" ADD COLUMN "{col}" TEXT'
                    )
        placeholders = ", ".join("?" for _ in self._columns)
        cols = ", ".join(f'"{c}"' for c in self._columns)
        sql = f'INSERT INTO "{self.table}" ({cols}) VALUES ({placeholders})'
        params = [tuple(self._coerce(row.get(c)) for c in self._columns) for row in rows]
        if self.replace_on_pk and self.pk:
            sql = (
                f'INSERT OR REPLACE INTO "{self.table}" ({cols}) '
                f'VALUES ({placeholders})'
            )
        self.conn.executemany(sql, params)
        self.conn.commit()

    @staticmethod
    def _coerce(v: Any) -> Any:
        # sqlite3 binds None, int, float, str, bytes natively; bools
        # become ints naturally.
        if isinstance(v, bool):
            return int(v)
        return v


class BatchSink(Sink):
    """A sink that buffers rows and flushes on a size threshold.

    Wraps any underlying :class:`Sink` and calls ``write`` on the
    inner sink only when the buffer reaches ``batch_size`` rows.
    Always flushes on :meth:`close`.
    """

    def __init__(self, inner: Sink, batch_size: int = 100) -> None:
        if batch_size < 1:
            raise ValueError("batch_size must be >= 1")
        self.inner = inner
        self.batch_size = batch_size
        self._buffer: List[Dict[str, Any]] = []
        self.flush_count = 0
        self.row_count = 0

    def write(self, rows: Sequence[Dict[str, Any]]) -> None:
        for row in rows:
            self._buffer.append(dict(row))
            self.row_count += 1
            if len(self._buffer) >= self.batch_size:
                self._flush()

    def _flush(self) -> None:
        if not self._buffer:
            return
        self.inner.write(self._buffer)
        self._buffer.clear()
        self.flush_count += 1

    def close(self) -> None:
        """Flush the buffer. Call this at the end of every pipeline."""
        self._flush()


# ---- a tiny convenience: a stream sink that batches in memory --------


class BatchingStreamSink(StreamSink):
    """A StreamSink that buffers and flushes periodically.

    Used in the streaming-loading lesson (M05) to demonstrate that
    a stream of events can be batched into warehouse-friendly
    chunks without losing the per-row ordering.
    """

    def __init__(self, batch_size: int = 50) -> None:
        self.batch_size = batch_size
        self._buffer: List[Dict[str, Any]] = []
        self.flushed: List[List[Dict[str, Any]]] = []

    def write_one(self, row: Dict[str, Any]) -> None:
        self._buffer.append(dict(row))
        if len(self._buffer) >= self.batch_size:
            self._flush()

    def _flush(self) -> None:
        if not self._buffer:
            return
        self.flushed.append(self._buffer)
        self._buffer = []

    def flush(self) -> None:
        self._flush()


# ---- pipeline-ready helper --------------------------------------------


def pipeline_pair(
    source: Source, sink: Sink
) -> "tuple[Source, Sink]":
    """Return ``(source, sink)`` for use as a Pipeline's endpoints.

    Tiny ergonomic helper so the call site reads cleanly::

        Pipeline("copy", source.read, lambda r: r, sink.write).run()
    """
    return source, sink
