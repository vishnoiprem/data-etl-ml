# Schema-Evolution Safe Writes

## Problem
Write data to a table whose schema may change over time, without breaking
readers.

## How to Think
1. **Add columns** nullable by default.
2. **Widen types** (int -> bigint); never narrow.
3. **Rename** = dangerous (dual-write alias, drain readers, drop).
4. **Drop** = dangerous (drain readers first).
5. **Use schema registry** (Confluent / Glue) for enforcement.
6. **Block** incompatible changes in CI.

## How to Remember
- **"Widen types, never narrow."**
- **"Add nullable freely; remove carefully."**

## Schema Rules
| Change | Allowed? |
|---|---|
| Add nullable column | Yes |
| Add non-nullable column | Risky (needs backfill) |
| Remove column | Dangerous - drain readers first |
| Widen type (int -> bigint) | Yes |
| Narrow type | Bad (overflow risk) |
| Rename | Dangerous - dual-write, then drain |

## Code (Safe Write Pattern)
```python
def safe_write(df, target_table):
    expected = spark.catalog.listColumns(target_table)
    expected_map = {c.name: c.dataType for c in expected}

    for field in df.schema:
        if field.name not in expected_map and not field.nullable:
            raise ValueError(f"New non-nullable column {field.name}")

    for col_name, col_type in expected_map.items():
        if col_name not in df.schema.names:
            raise ValueError(f"Drop of existing column {col_name}")

    for field in df.schema:
        if field.name in expected_map and not can_widen(field.dataType, expected_map[field.name]):
            raise ValueError(f"Narrowing change on {field.name}")

    df.write.mode("append").saveAsTable(target_table)
```

## Common Mistakes
- Dropping columns without draining readers.
- Narrowing types silently.
- Adding non-nullable columns without backfill.

## AI Use Cases
- Auto-detect schema drift in real-time.
- Auto-generate backward-compat migration code.
- LLM-based schema diff summarisation.
