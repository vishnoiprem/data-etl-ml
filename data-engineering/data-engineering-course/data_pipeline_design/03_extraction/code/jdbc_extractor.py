"""JDBC-style SQL extractor with watermark and keyset patterns.

This module implements two extraction patterns from a SQL source
using a ``QueryRunner`` (so tests can run against SQLite):

  * ``JDBCExtractor`` — incremental extraction with a high-water
    mark. Tracks the last-seen ``updated_at`` and queries
    ``WHERE updated_at > :last_watermark``.
  * ``KeysetExtractor`` — incremental extraction by primary key.
    Tracks the last-seen ``id`` and queries
    ``WHERE id > :last_id``.

Both extractors use a pluggable ``watermark_store`` (a dict in
tests, a real database in production) so the watermark survives
restarts.

Author: Prem Vishnoi <pvishnoi@avilx.com>
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence

from common import QueryRunner


@dataclass
class ExtractionResult:
    rows: List[Dict[str, Any]]
    new_watermark: Any
    truncated: bool


class JDBCExtractor:
    """Incremental SQL extractor using an ``updated_at`` watermark.

    Parameters
    ----------
    runner:
        A ``QueryRunner`` connected to the source database.
    table:
        Source table name.
    columns:
        Columns to select. Defaults to all (``SELECT *``).
    watermark_column:
        The column to use as the watermark (must be a timestamp).
    watermark_store:
        A dict-like object that persists the watermark across
        restarts. Keys: ``table`` names. Values: the latest
        watermark.
    page_size:
        Max rows per query (drives pagination within a single
        run).
    statement_timeout_ms:
        Optional per-statement timeout. SQLite doesn't enforce
        this, but real JDBC drivers do.
    """

    def __init__(
        self,
        runner: QueryRunner,
        table: str,
        columns: Optional[Sequence[str]] = None,
        watermark_column: str = "updated_at",
        watermark_store: Optional[Dict[str, Any]] = None,
        page_size: int = 10_000,
        statement_timeout_ms: Optional[int] = None,
    ) -> None:
        self.runner = runner
        self.table = table
        self.columns = list(columns) if columns else ["*"]
        self.watermark_column = watermark_column
        self.watermark_store = watermark_store if watermark_store is not None else {}
        self.page_size = page_size
        self.statement_timeout_ms = statement_timeout_ms

    def _initial_watermark(self) -> Any:
        """The watermark to start from. Defaults to 'epoch'."""
        if self.watermark_column not in ("updated_at",):
            return self.watermark_store.get(self.table, "1970-01-01 00:00:00")
        return self.watermark_store.get(self.table, "1970-01-01 00:00:00")

    def extract(self) -> ExtractionResult:
        """Extract rows updated after the current watermark."""
        last = self._initial_watermark()
        col_list = ", ".join(self.columns) if self.columns != ["*"] else "*"
        sql = (
            f"SELECT {col_list} FROM {self.table} "
            f"WHERE {self.watermark_column} > ? "
            f"ORDER BY {self.watermark_column} "
            f"LIMIT ?"
        )
        rows = self.runner.query_all(sql, (last, self.page_size))
        if not rows:
            return ExtractionResult(rows=[], new_watermark=last, truncated=False)
        new_wm = rows[-1][self.watermark_column]
        return ExtractionResult(
            rows=rows, new_watermark=new_wm, truncated=len(rows) == self.page_size
        )

    def commit(self, new_watermark: Any) -> None:
        """Persist the new watermark. Call only after the load succeeds."""
        self.watermark_store[self.table] = new_watermark


class KeysetExtractor:
    """Incremental SQL extractor by primary key.

    Faster than the watermark pattern for append-only data with
    a monotonic primary key. No clock-skew issues.
    """

    def __init__(
        self,
        runner: QueryRunner,
        table: str,
        pk: str = "id",
        watermark_store: Optional[Dict[str, Any]] = None,
        page_size: int = 10_000,
    ) -> None:
        self.runner = runner
        self.table = table
        self.pk = pk
        self.watermark_store = (
            watermark_store if watermark_store is not None else {}
        )
        self.page_size = page_size

    def _initial_id(self) -> Any:
        return self.watermark_store.get(self.table, 0)

    def extract(self) -> ExtractionResult:
        last = self._initial_id()
        sql = (
            f"SELECT * FROM {self.table} "
            f"WHERE {self.pk} > ? "
            f"ORDER BY {self.pk} "
            f"LIMIT ?"
        )
        rows = self.runner.query_all(sql, (last, self.page_size))
        if not rows:
            return ExtractionResult(rows=[], new_watermark=last, truncated=False)
        new_id = rows[-1][self.pk]
        return ExtractionResult(
            rows=rows, new_watermark=new_id, truncated=len(rows) == self.page_size
        )

    def commit(self, new_id: Any) -> None:
        self.watermark_store[self.table] = new_id


# ---- a tiny "build a pipeline" helper --------------------------------


def make_incremental_pipeline(
    runner: QueryRunner,
    sink: Any,
    table: str,
    watermark_column: str = "updated_at",
    watermark_store: Optional[Dict[str, Any]] = None,
):
    """Build a ``common.Pipeline`` that extract → load incrementally.

    The transform is a no-op (the extract already returns the
    right shape). The load writes rows to ``sink`` and commits
    the new watermark only after a successful write.
    """
    from common import Pipeline

    extractor = JDBCExtractor(
        runner=runner,
        table=table,
        watermark_column=watermark_column,
        watermark_store=watermark_store,
    )

    def _load(rows: List[Dict[str, Any]]) -> int:
        sink.write(rows)
        if rows:
            extractor.commit(rows[-1][watermark_column])
        return len(rows)

    return Pipeline(
        name=f"incremental.{table}",
        extract=extractor.extract,
        transform=lambda r: r,
        load=_load,
        retries=3,
    )
