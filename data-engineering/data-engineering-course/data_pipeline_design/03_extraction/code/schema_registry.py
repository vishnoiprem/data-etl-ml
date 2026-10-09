"""Tiny schema registry with backward-compatibility checks.

This is a teaching implementation of the four kinds of schema
change a production pipeline must handle:

  1. Add a column  — backward compatible (old readers ignore).
  2. Remove a column — NOT backward compatible.
  3. Rename a column — NOT backward compatible.
  4. Type change — depends on the direction (widening is OK,
     narrowing is NOT).

The registry stores the latest schema per topic. ``check_compatibility``
rejects non-backward-compatible changes. ``check_contract`` validates
a sample row against the latest schema.

Author: Prem Vishnoi <prem.vishnoi.example.com>
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# Type widening rules: (old, new) → True if backward compatible.
_TYPE_WIDEN = {
    ("int", "float"): True,
    ("int", "str"): True,
    ("float", "str"): True,
    ("int", "int"): True,
    ("float", "float"): True,
    ("str", "str"): True,
    ("bool", "int"): True,
    ("bool", "str"): True,
}


_TYPE_NARROW = {
    ("float", "int"): True,
    ("str", "int"): True,
    ("str", "float"): True,
}


_TYPE_RANK = {"bool": 0, "int": 1, "float": 2, "str": 3}


def _py_type(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    return "str"


def _type_widening_compatible(old: str, new: str) -> bool:
    """True if a value of type ``old`` can be losslessly widened to ``new``."""
    if old == new:
        return True
    if (old, new) in _TYPE_WIDEN:
        return True
    return False


def _type_narrowing_compatible(old: str, new: str) -> bool:
    """True if a value of type ``new`` can be safely narrowed to ``old``.

    This is what backward compatibility *for the writer* requires:
    an old writer (sending old) must be able to land in a new
    destination (expecting new). The destination must accept the
    old value.
    """
    if old == new:
        return True
    if (old, new) in _TYPE_NARROW:
        return True
    if (old, "int") in _TYPE_NARROW and (old, new) in _TYPE_NARROW:
        return True
    return False


class IncompatibleSchemaError(Exception):
    """Raised when a schema change is not backward compatible."""


@dataclass
class SchemaVersion:
    name: str
    version: int
    fields: Dict[str, str]  # field name -> python type name


@dataclass
class SchemaRegistry:
    """A tiny in-memory schema registry.

    Stores the latest schema per topic. Enforces backward
    compatibility on every :meth:`register` call.

    Example::

        reg = SchemaRegistry()
        reg.register("users", {"id": "int", "name": "str"})
        reg.register("users", {"id": "int", "name": "str", "email": "str"})
        # OK: added a column (backward compatible).
        reg.register("users", {"id": "int", "name": "str", "email": "int"})
        # IncompatibleSchemaError: email type narrowed from str to int.
    """

    _schemas: Dict[str, List[SchemaVersion]] = field(default_factory=dict)

    def versions(self, name: str) -> List[SchemaVersion]:
        return list(self._schemas.get(name, []))

    def latest(self, name: str) -> Optional[SchemaVersion]:
        versions = self._schemas.get(name, [])
        return versions[-1] if versions else None

    def register(self, name: str, fields: Dict[str, str]) -> SchemaVersion:
        """Register a new schema. Raises if not backward compatible."""
        existing = self.latest(name)
        if existing is not None:
            self._check_compatibility(existing, fields, name)
        version = (
            existing.version + 1 if existing else 1
        )
        sv = SchemaVersion(name=name, version=version, fields=dict(fields))
        self._schemas.setdefault(name, []).append(sv)
        return sv

    def _check_compatibility(
        self,
        old: SchemaVersion,
        new_fields: Dict[str, str],
        name: str,
    ) -> None:
        # 1. Removed columns are not backward compatible.
        for col, old_type in old.fields.items():
            if col not in new_fields:
                raise IncompatibleSchemaError(
                    f"{name}: removed column {col!r} (not backward compatible)"
                )

        # 2. New columns are OK (backward compatible).
        # 3. Renames look like remove+add. We can't detect renames
        #    without a name-preserving diff; treat remove+add as
        #    incompatible. A real registry would use a field id
        #    (Avro does this).
        for col, new_type in new_fields.items():
            if col in old.fields:
                old_type = old.fields[col]
                if not _type_widening_compatible(old_type, new_type):
                    raise IncompatibleSchemaError(
                        f"{name}: column {col!r} changed type "
                        f"from {old_type} to {new_type} "
                        f"(not backward compatible)"
                    )

    def check_contract(
        self, name: str, sample: Dict[str, Any]
    ) -> List[str]:
        """Validate a sample row against the latest schema.

        Returns a list of error messages. Empty list = contract OK.
        """
        latest = self.latest(name)
        errors: List[str] = []
        if latest is None:
            return [f"no schema registered for {name!r}"]
        for col, expected in latest.fields.items():
            if col not in sample:
                errors.append(f"missing column {col!r}")
                continue
            actual = _py_type(sample[col])
            if not _type_widening_compatible(actual, expected):
                errors.append(
                    f"column {col!r}: expected {expected}, got {actual}"
                )
        return errors
