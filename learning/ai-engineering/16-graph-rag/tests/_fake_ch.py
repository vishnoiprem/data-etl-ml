"""Tiny in-memory shim that mimics the surface of clickhouse_connect
that we use in api/app/main.py and api/app/auth.py.

Lets us test the full auth + data flow without a running ClickHouse.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any


class FakeCHClient:
    def __init__(self) -> None:
        self._tables: dict[str, list[dict[str, Any]]] = {}

    def query(self, sql: str, parameters: dict | None = None) -> "FakeResult":
        sql_l = sql.lower().strip()
        # Apply parameter substitution (we use {name:Type} syntax)
        if parameters:
            for k, v in parameters.items():
                sql = sql.replace("{" + k + ":String}", f"'{v}'")
                sql = sql.replace("{" + k + ":Int}", str(v))
                sql_l = sql.lower()

        # SHOW TABLES
        if "show tables" in sql_l:
            return FakeResult(
                ["name"],
                [(t,) for t in self._tables.keys()],
            )

        # CREATE TABLE — accept
        if "create table" in sql_l:
            return FakeResult([], [])

        # SELECT count() AS n FROM graph_rag.users
        if "count() as n" in sql_l and "users" in sql_l:
            return FakeResult(["n"], [(len(self._tables.get("users", [])),)])

        # SELECT ... FROM graph_rag.users FINAL WHERE username = '<x>'
        if "from graph_rag.users" in sql_l:
            users = self._tables.get("users", [])
            # simple param substitution for username = 'X'
            import re

            m = re.search(r"username\s*=\s*'([^']+)'", sql)
            if m:
                target = m.group(1)
                users = [u for u in users if u.get("username") == target]
            return FakeResult(
                ["username", "password_hash", "display_name", "role"],
                [
                    (
                        u.get("username"),
                        u.get("password_hash", ""),
                        u.get("display_name", ""),
                        u.get("role", "user"),
                    )
                    for u in users
                ],
            )

        # Generic SELECT  -> return everything
        if sql_l.startswith("select") or sql_l.startswith("with"):
            return FakeResult([], [])

        return FakeResult([], [])

    def query_df(self, sql: str) -> list[dict[str, Any]]:
        result = self.query(sql)
        return [dict(zip(result.column_names, row)) for row in result.result_rows]

    def insert(self, table: str, data: list[dict[str, Any]]) -> None:
        # ReplacingMergeTree semantics: replace existing rows with same key
        self._tables.setdefault(table, [])
        for row in data:
            self._tables[table].append(row)

    def insert_dicts(self, table: str, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        self.insert(table, rows)


class FakeResult:
    def __init__(self, column_names: list[str], result_rows: list[tuple]) -> None:
        self.column_names = column_names
        self.result_rows = result_rows
