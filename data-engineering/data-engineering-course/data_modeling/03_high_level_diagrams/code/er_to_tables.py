"""ER-to-table translation rules.

This module codifies the mechanical translation from an entity-
relationship diagram to a set of relational tables. The rules are
the standard ones taught in any database course, but the helper
functions here are useful for *narrating* the translation during a
data modeling interview.

The rules, in order:

1.  Each entity becomes a table.
2.  Each 1-to-many relationship is encoded as a foreign key on the
    "many" side.
3.  Each many-to-many relationship is encoded as a bridge (junction)
    table with two foreign keys.
4.  Each multi-valued attribute becomes its own table.
5.  Each derived attribute is *not* stored (it's a query, not a
    column).

Author: Prem Vishnoi <prem.vishnoi@example.com>
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Entity:
    """An entity from the ER diagram.

    >>> e = Entity(name="User", attributes=["id", "name", "email"])
    >>> "id" in e.attributes
    True
    """

    name: str
    attributes: List[str] = field(default_factory=list)


@dataclass
class Relationship:
    """A relationship between two entities.

    Cardinality is one of: "1:N", "N:1", "1:1", "N:M".
    """

    name: str
    left: str
    right: str
    cardinality: str
    attributes: List[str] = field(default_factory=list)


@dataclass
class TranslatedTable:
    """The output of a translation: a single table spec."""

    name: str
    columns: List[str]
    primary_key: List[str]
    foreign_keys: List[str] = field(default_factory=list)


# ---- the rules, codified as helpers ---------------------------------------


def entity_to_table(e: Entity) -> TranslatedTable:
    """Rule 1: each entity becomes a table.

    The primary key is the entity's ``id`` attribute by convention.
    """
    pk = ["id"] if "id" in e.attributes else [e.attributes[0]]
    return TranslatedTable(
        name=e.name.lower() + "s",  # naive pluralization
        columns=list(e.attributes),
        primary_key=pk,
    )


def relationship_to_fk(
    rel: Relationship,
    left_table: str,
    right_table: str,
) -> Optional[TranslatedTable]:
    """Rule 2 & 3: encode the relationship as a FK or bridge table.

    - "1:N" / "N:1" → foreign key on the "many" side.
    - "N:M"       → bridge (junction) table.
    - "1:1"       → foreign key on either side; we'll pick ``right``.
    """
    if rel.cardinality in ("1:N", "N:1"):
        # The "many" side is whichever name is "second" in the
        # cardinality spec. We rely on the caller to pass the
        # relationship in the correct order. The convention we use
        # is "left:1, right:N", i.e. left is the "one" side.
        fk_col = f"{left_table[:-1]}_id"  # naive singularization
        return TranslatedTable(
            name=right_table,
            columns=[fk_col],
            primary_key=[],
            foreign_keys=[
                f"FOREIGN KEY ({fk_col}) REFERENCES {left_table}(id)"
            ],
        )
    if rel.cardinality == "1:1":
        fk_col = f"{left_table[:-1]}_id"
        return TranslatedTable(
            name=right_table,
            columns=[fk_col],
            primary_key=[],
            foreign_keys=[
                f"UNIQUE FOREIGN KEY ({fk_col}) REFERENCES {left_table}(id)"
            ],
        )
    if rel.cardinality == "N:M":
        # Bridge table.
        l_id = f"{left_table[:-1]}_id"
        r_id = f"{right_table[:-1]}_id"
        return TranslatedTable(
            name=f"{left_table}_{right_table}",
            columns=[l_id, r_id] + rel.attributes,
            primary_key=[l_id, r_id],
            foreign_keys=[
                f"FOREIGN KEY ({l_id}) REFERENCES {left_table}(id)",
                f"FOREIGN KEY ({r_id}) REFERENCES {right_table}(id)",
            ],
        )
    raise ValueError(f"unknown cardinality {rel.cardinality!r}")


def translate_er(
    entities: List[Entity],
    relationships: List[Relationship],
) -> Dict[str, TranslatedTable]:
    """Translate a full ER diagram to a set of relational tables.

    >>> entities = [
    ...     Entity("User", ["id", "name", "email"]),
    ...     Entity("Workout", ["id", "user_id", "duration_min"]),
    ...     Entity("Exercise", ["id", "name"]),
    ... ]
    >>> rels = [
    ...     Relationship("does", "User", "Workout", "1:N"),
    ...     Relationship("includes", "Workout", "Exercise", "N:M"),
    ... ]
    >>> out = translate_er(entities, rels)
    >>> "users" in out and "workouts" in out and "exercises" in out
    True
    >>> "workout_exercises" in out  # the bridge table
    True
    """
    tables: Dict[str, TranslatedTable] = {}
    for e in entities:
        t = entity_to_table(e)
        tables[t.name] = t

    for rel in relationships:
        lt = rel.left.lower() + "s"
        rt = rel.right.lower() + "s"
        if rel.cardinality in ("1:N", "N:1", "1:1"):
            t = relationship_to_fk(rel, lt, rt)
            if t is not None and t.name in tables:
                tables[t.name].columns.extend(t.columns)
                tables[t.name].foreign_keys.extend(t.foreign_keys)
        else:
            t = relationship_to_fk(rel, lt, rt)
            if t is not None:
                tables[t.name] = t
    return tables


# ---- rule 4: multi-valued attributes -------------------------------------


def split_multivalued(
    entity: Entity, attribute: str
) -> TranslatedTable:
    """Rule 4: a multi-valued attribute becomes its own table.

    E.g., ``User(phone_numbers)`` → ``user_phones(user_id, phone_number)``.
    """
    if attribute not in entity.attributes:
        raise ValueError(
            f"{attribute!r} is not an attribute of {entity.name!r}"
        )
    return TranslatedTable(
        name=f"{entity.name.lower()}_"
             f"{attribute.lower().rstrip('s')}",
        columns=[
            f"{entity.name.lower()}_id",
            attribute.lower().rstrip("s"),
        ],
        primary_key=[
            f"{entity.name.lower()}_id",
            attribute.lower().rstrip("s"),
        ],
        foreign_keys=[
            f"FOREIGN KEY ({entity.name.lower()}_id) "
            f"REFERENCES {entity.name.lower()}s(id)"
        ],
    )


# ---- rule 5: derived attributes ------------------------------------------


def derived_attribute_note(attr: str) -> str:
    """Rule 5: derived attributes are queries, not columns.

    The interviewer will sometimes ask "should we store
    ``lifetime_revenue`` on the customer?" The right answer is
    usually *no* — it's a derived attribute, computed at query
    time from the fact table.
    """
    return (
        f"{attr!r} is a *derived* attribute — compute it at query "
        f"time as a SUM/COUNT over the fact table rather than "
        f"storing it. Storing it creates a synchronization problem "
        f"(it goes stale whenever the underlying events change)."
    )
