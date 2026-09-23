"""
Problem 06: Schema-evolution safe writes.

Meta flavor: Upstream schemas change. Show how to write safely
(backward + forward compatible).

How to Think:
- Add columns nullable by default.
- Don't change column types (cast + dual-write).
- Use schema registry (Confluent / Glue).
- Block writes on incompatible change in CI.

How to Remember:
- "Widen types, never narrow."
- "Add nullable columns freely; remove carefully."

AI Use Cases:
- Auto-detect schema drift in real-time.
- Auto-generate backward-compat migration code.
- LLM-based schema diff summarisation.
"""
SCHEMA_RULES = {
    "add_column":      "OK if nullable or default value.",
    "remove_column":   "DANGEROUS - drain readers first.",
    "widen_type":      "OK (int -> bigint, float -> double).",
    "narrow_type":     "BAD (bigint -> int can overflow).",
    "rename_column":   "DANGEROUS - alias both, drain readers, then drop.",
}

def safe_write(df, target_table):
    """Compare df.schema to target_table schema; reject if incompatible."""
    expected = spark.catalog.listColumns(target_table)
    expected_map = {c.name: c.dataType for c in expected}

    for field in df.schema:
        if field.name not in expected_map:
            # New column - must be nullable OR have default
            if not field.nullable:
                raise ValueError(f"New non-nullable column {field.name}")

    for col_name, col_type in expected_map.items():
        if col_name not in df.schema.names:
            # Dropped column - warn loudly
            raise ValueError(f"Drop of existing column {col_name}")

    # Widening check
    for field in df.schema:
        if field.name in expected_map and not can_widen(field.dataType, expected_map[field.name]):
            raise ValueError(f"Narrowing change on {field.name}")

    df.write.mode("append").saveAsTable(target_table)
