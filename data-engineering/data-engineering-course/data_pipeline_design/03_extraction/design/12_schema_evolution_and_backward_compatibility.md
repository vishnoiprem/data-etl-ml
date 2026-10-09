# 12 — Schema Evolution and Backward Compatibility

> **Lesson 12 of 30 — Extraction**

The silent killer of pipelines. The source adds a column, removes
a column, changes a type. The downstream pipeline breaks at 3 AM.
This lesson is how to detect, prevent, and survive schema changes.

---

## 1. Why schema evolution matters

Every pipeline is a contract between the source and the
destination. The source promises to send rows of a certain shape;
the destination promises to accept them. When the source breaks
the contract, the pipeline breaks.

Real-world examples:

- Stripe adds a `radar_options` field to `Charge`. The downstream
  table has no such column. The CDC connector fails.
- A product team renames `is_premium` to `is_pro`. The downstream
  `WHERE is_premium = true` returns nothing.
- A type changes from `INT` to `BIGINT`. The downstream Parquet
  schema rejects the write.

The senior move: every production pipeline has a *schema contract*
that both sides agree to, and a *contract test* that runs in CI.

---

## 2. The four kinds of schema change

Not all schema changes are equal. The compatibility matrix:

| Change | Backward compatible? | Forward compatible? |
|---|---|---|
| Add a column (nullable) | ✅ Yes (old readers ignore) | ✅ Yes (new readers see null) |
| Add a column (with default) | ⚠️ Depends (old readers may not handle) | ✅ Yes |
| Remove a column | ❌ No (old readers expect it) | ✅ Yes (new readers ignore) |
| Rename a column | ❌ No | ❌ No |
| Change type (widening, e.g. INT → BIGINT) | ✅ Usually | ✅ Usually |
| Change type (narrowing, e.g. STRING → INT) | ❌ No | ❌ No |
| Change semantics (e.g. `status` values) | ❌ No (unless documented) | ❌ No |

**Backward compatible:** an old reader can still process new data.
**Forward compatible:** a new reader can still process old data.

The senior move: only make backward-compatible changes without
coordinating with downstream. Anything else requires a versioned
rollout.

---

## 3. The schema registry

The senior pattern is a *schema registry*: a central service that
stores every schema version and enforces compatibility on every
change. The most common is the Confluent Schema Registry (for
Avro / Protobuf / JSON Schema on Kafka).

```
Source producer  ──►  Schema Registry: "I want to register v2 of
                       users, must be backward compatible with v1"
                                       │
                                       └─► Compatible: ✅ Register v2
                                       └─► Incompatible: ❌ Reject
```

The schema registry is the *gatekeeper*. Producers can't push
incompatible schemas. Consumers can request any version they
support. The pipeline is *self-describing*: every event carries
its schema id, so the consumer can look up the right schema.

---

## 4. The contract test

Even with a schema registry, you need a *contract test* that
verifies the pipeline can actually process the data. The pattern:

```python
def test_users_schema_contract():
    expected = {
        "id": int,
        "name": str,
        "email": str,
        "country": str,
        "updated_at": str,  # ISO 8601
    }
    sample = {"id": 1, "name": "Alice", "email": "a@b.com",
              "country": "US", "updated_at": "2024-01-01T00:00:00Z"}
    for key, typ in expected.items():
        assert key in sample, f"missing column {key}"
        assert isinstance(sample[key], typ), f"wrong type for {key}"
```

The contract test runs:

- In CI on every commit (catches new source changes before deploy).
- In production on a small sample (catches the case where the
  source added a column without telling the schema registry).
- On every pipeline run (cheap; takes 100 ms).

The senior move: the contract test is *the* mechanism that
prevents the 3 AM page.

---

## 5. The dbt source freshness pattern

dbt has a built-in `source freshness` check that runs on every
build:

```yaml
sources:
  - name: raw
    schema: public
    tables:
      - name: users
        loaded_at_field: updated_at
        freshness:
          warn_after: { count: 6, period: hour }
          error_after: { count: 24, period: hour }
```

If the source hasn't been updated in 6 hours, dbt warns. If 24
hours, dbt errors and the pipeline stops. The senior move: every
production source has a freshness SLA, and the pipeline enforces
it.

---

## 6. The "drop and recreate" anti-pattern

The junior pattern: when a schema change breaks the pipeline,
drop the destination table and recreate it. This is *catastrophic*
in production:

- All downstream queries break.
- All historical data is lost.
- The pipeline has to re-extract everything (hours, days).

The senior pattern: *additive* changes only. Add a new column,
backfill the data, deprecate the old column. The destination
schema is *append-only*; nothing is ever removed without a
versioned migration.

---

## 7. The migration pattern

When you need to make a *non-backward-compatible* change, the
senior pattern is a versioned migration:

```
v1: id INT, name TEXT, is_premium BOOLEAN
v2: id INT, name TEXT, is_pro BOOLEAN  -- new
v3: id INT, name TEXT, is_pro BOOLEAN  -- drop is_premium (after backfill)
```

The pipeline writes to *both* columns during the transition. Once
the downstream consumers have migrated to `is_pro`, the old
column is dropped. The whole process takes weeks, not hours.

The senior move: every non-backward-compatible change is a
*project*, not a deploy. It has phases, owners, and a rollback
plan.

---

## 8. The Avro / Protobuf advantage

Row formats like Avro and Protobuf have schema *embedded* in the
data:

```
Avro file: schema + rows, schema is required to read
Parquet file: schema + rows, schema is in the file footer
JSON / CSV: no schema, free-for-all
```

The senior move: use Avro or Protobuf for CDC events, Parquet
for warehouse tables, JSON only for the "raw bronze" layer where
schema flexibility is the point.

---

## 9. Code: the schema registry

The `code/schema_registry.py` module implements a tiny schema
registry:

```python
from data_pipeline_design.03_extraction.code.schema_registry import SchemaRegistry

reg = SchemaRegistry()
reg.register("users", {"id": int, "name": str})
reg.check_compatibility("users", {"id": int, "name": str, "email": str})
# raises: IncompatibleSchemaError (removed column 'email' from existing
# would break backward compat, but here we're *adding*, so it's fine)
```

The test in `tests/test_extraction.py` exercises the four
compatibility cases (add, remove, rename, type change).

---

## 10. The interview answer

> "Every pipeline I build has a schema registry at the source and
> a contract test in CI. The contract test verifies the expected
> columns and types. The schema registry enforces backward
> compatibility on every change. For CDC events I use Avro so the
> schema travels with the data. The migration pattern for breaking
> changes is additive: add the new column, backfill, deprecate
> the old. No drops in production."

That single paragraph covers: registry, contract test, format
choice, migration pattern. Senior answer in 30 seconds.

---

## Try it

Look at the most recent pipeline you've worked on. Does it have a
schema registry? A contract test? A freshness check? If any of
the three is missing, the pipeline is one source-side change away
from a 3 AM page.
