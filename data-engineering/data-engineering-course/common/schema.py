"""SQL DDL helpers — small enough to read in one sitting.

These helpers build ``CREATE TABLE IF NOT EXISTS`` / ``DROP TABLE`` /
``CREATE INDEX`` statements for SQLite. They are deliberately tiny —
just enough to script a demo database and write deterministic
exercises against it.

In production you'd use Alembic, Flyway, or a real migration tool.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence


@dataclass
class Column:
    """A single SQL column definition.

    >>> Column("id", "INTEGER", primary_key=True).to_sql_fragment()
    '"id" INTEGER PRIMARY KEY'
    >>> Column("email", "TEXT", nullable=False, default="''").to_sql_fragment()
    '"email" TEXT NOT NULL DEFAULT \'\''
    """

    name: str
    dtype: str
    nullable: bool = True
    primary_key: bool = False
    default: Optional[str] = None
    references: Optional[str] = None  # e.g. "users(id)"

    def to_sql_fragment(self) -> str:
        parts: List[str] = [f'"{self.name}"', self.dtype]
        if self.primary_key:
            parts.append("PRIMARY KEY")
        if not self.nullable:
            parts.append("NOT NULL")
        if self.default is not None:
            parts.append(f"DEFAULT {self.default}")
        if self.references:
            parts.append(f"REFERENCES {self.references}")
        return " ".join(parts)


@dataclass
class Table:
    """A SQL table — name plus columns plus optional foreign keys.

    >>> t = Table("users", [Column("id", "INTEGER", primary_key=True),
    ...                     Column("email", "TEXT", nullable=False)])
    >>> print(t.to_ddl())
    CREATE TABLE IF NOT EXISTS "users" (
        "id" INTEGER PRIMARY KEY,
        "email" TEXT NOT NULL
    )
    """

    name: str
    columns: List[Column] = field(default_factory=list)
    foreign_keys: List[str] = field(default_factory=list)

    def to_ddl(self) -> str:
        col_lines = [f"    {c.to_sql_fragment()}" for c in self.columns]
        col_lines.extend(f"    FOREIGN KEY ({fk})" for fk in self.foreign_keys)
        body = ",\n".join(col_lines) if col_lines else ""
        return f'CREATE TABLE IF NOT EXISTS "{self.name}" (\n{body}\n)'

    def qualified(self, prefix: str = "main") -> str:
        """Return ``prefix.name`` for use in joins."""
        return f'"{prefix}"."{self.name}"'


def create_table_sqlite(t: Table) -> str:
    """Generate a ``CREATE TABLE IF NOT EXISTS`` statement."""
    return t.to_ddl()


def drop_table_sqlite(table_name: str, if_exists: bool = True) -> str:
    """Generate a ``DROP TABLE`` statement."""
    guard = "IF EXISTS " if if_exists else ""
    return f'DROP TABLE {guard}"{table_name}"'


def create_index_sqlite(
    t: Table, columns: Sequence[str], unique: bool = False
) -> str:
    """Generate a ``CREATE INDEX IF NOT EXISTS`` statement."""
    if not columns:
        raise ValueError("create_index_sqlite requires at least one column")
    cols = ", ".join(f'"{c}"' for c in columns)
    kind = "UNIQUE INDEX" if unique else "INDEX"
    idx_name = f"idx_{t.name}_{'_'.join(columns)}"
    return (
        f'CREATE {kind} IF NOT EXISTS "{idx_name}" '
        f'ON "{t.name}" ({cols})'
    )


def add_foreign_keys(table: Table, fk_specs: Sequence[str]) -> Table:
    """Append foreign-key constraints to a Table, return the same table.

    Each spec is rendered verbatim into a ``FOREIGN KEY (...)`` clause
    by :meth:`Table.to_ddl`, so pass full clauses like ``"user_id"
    REFERENCES users(id)``.
    """
    table.foreign_keys.extend(fk_specs)
    return table
