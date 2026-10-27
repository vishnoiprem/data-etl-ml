# 7.2 — Python: Create a Dataset

> **Section 7 · Python Client Library · Lecture 7.2 · 5:28**

## 🎯 What you will learn

- The `Dataset` object and all its options
- Create, update, list, and delete datasets from Python
- The idempotent pattern that makes pipeline setup safe
- Labels, descriptions, and lifecycle configuration

---

## 🧠 Concept

The `Dataset` object maps directly to a BigQuery dataset. Every SQL `CREATE SCHEMA` option has a
Python equivalent.

### The full option set

| Python attribute | SQL equivalent |
|------------------|----------------|
| `dataset_id` | The dataset name |
| `project` | The project |
| `location` | `OPTIONS(location = ...)` |
| `description` | `OPTIONS(description = ...)` |
| `labels` | `OPTIONS(labels = ...)` |
| `default_table_expiration_ms` | `OPTIONS(default_table_expiration_days = ...)` |
| `default_partition_expiration_ms` | `OPTIONS(default_partition_expiration_days = ...)` |
| `max_time_travel_hours` | Time travel window |
| `is_case_insensitive` | `OPTIONS(is_case_insensitive = ...)` |
| `default_collation` | `OPTIONS(default_collation = ...)` |
| `access_entries` | IAM bindings |

---

## 🛠️ Hands-On

### 1. Create a dataset

```python
from google.cloud import bigquery

client = bigquery.Client(project="YOUR_PROJECT_ID")

dataset = bigquery.Dataset(
    f"YOUR_PROJECT_ID.curated",
    location="US",
    description="Curated, conformed analytics models",
    labels={
        "env": "prod",
        "tier": "curated",
        "owner": "data-eng",
    },
    default_table_expiration_ms=365 * 24 * 60 * 60 * 1000,      # 365 days
    default_partition_expiration_ms=730 * 24 * 60 * 60 * 1000,   # 730 days
)

dataset = client.create_dataset(dataset, exists_ok=True)
print(f"Created {dataset.full_dataset_id}")
```

💡 **`exists_ok=True` makes creation idempotent.** This is the pattern you want in setup scripts —
it succeeds whether or not the dataset exists.

### 2. Create a layer of datasets in one go

```python
from google.cloud import bigquery

client = bigquery.Client(project="YOUR_PROJECT_ID")

DATASETS = {
    "raw": {
        "description": "Immutable raw landing zone. Never update, never delete manually.",
        "default_partition_expiration_days": 180,
        "labels": {"tier": "raw", "env": "prod", "owner": "data-eng"},
    },
    "curated": {
        "description": "Curated, conformed, queryable models",
        "default_table_expiration_days": 365,
        "default_partition_expiration_days": 730,
        "labels": {"tier": "curated", "env": "prod", "owner": "data-eng"},
    },
    "mart": {
        "description": "BI serving layer",
        "labels": {"tier": "gold", "env": "prod", "owner": "analytics-eng"},
    },
    "scratch": {
        "description": "Experiments. Auto-expires in 7 days.",
        "default_table_expiration_days": 7,
        "labels": {"tier": "scratch", "env": "dev"},
    },
}

for dataset_id, config in DATASETS.items():
    kwargs = {
        "location": "US",
        "description": config["description"],
        "labels": config.get("labels", {}),
    }
    if "default_table_expiration_days" in config:
        kwargs["default_table_expiration_ms"] = (
            config["default_table_expiration_days"] * 24 * 60 * 60 * 1000
        )
    if "default_partition_expiration_days" in config:
        kwargs["default_partition_expiration_ms"] = (
            config["default_partition_expiration_days"] * 24 * 60 * 60 * 1000
        )

    dataset = bigquery.Dataset(f"YOUR_PROJECT_ID.{dataset_id}", **kwargs)
    dataset = client.create_dataset(dataset, exists_ok=True)
    print(f"✓ {dataset.full_dataset_id}")
```

### 3. Update a dataset

```python
dataset = client.get_dataset("YOUR_PROJECT_ID.curated")

dataset.description = "Curated models (updated)"
dataset.labels = {**dataset.labels, "reviewed": "2026-10"}
dataset.default_table_expiration_ms = 180 * 24 * 60 * 60 * 1000

dataset = client.update_dataset(dataset, update_mode="update_fields")
print(f"Updated {dataset.full_dataset_id}")
```

⚠️ **`update_mode` matters:**
- `"update_fields"` (default) — only changes the fields you set
- `"update_full"` — replaces everything not set to `None` with defaults

### 4. List datasets with their metadata

```python
for dataset in client.list_datasets(project="YOUR_PROJECT_ID"):
    labels = dataset.labels or {}
    print(
        f"{dataset.dataset_id:12} | {dataset.location:6} | "
        f"tables={len(list(client.list_tables(dataset))):3} | "
        f"owner={labels.get('owner', '-'):15} | tier={labels.get('tier', '-')}"
    )
```

### 5. Check existence before acting

```python
def dataset_exists(client: bigquery.Client, dataset_id: str) -> bool:
    try:
        client.get_dataset(dataset_id)
        return True
    except NotFound:
        return False


if dataset_exists(client, "YOUR_PROJECT_ID.curated"):
    print("Exists")
else:
    print("Not found")
```

### 6. Delete a dataset

```python
from google.cloud.exceptions import NotFound

# Delete without deleting contents — fails if the dataset is not empty
try:
    client.delete_dataset("YOUR_PROJECT_ID.scratch", delete_contents=False)
    print("Deleted (was empty)")
except NotFound:
    print("Already gone")
except Exception as exc:
    print(f"Could not delete: {exc}")
```

```python
# Delete with contents — DANGEROUS
# client.delete_dataset("YOUR_PROJECT_ID.scratch", delete_contents=True)
```

💡 **Always protect destructive operations with an explicit flag in production code.** Make
`delete_contents=True` impossible to trigger accidentally — require a separate `force=True`.

### 7. Set IAM access on a dataset

```python
dataset = client.get_dataset("YOUR_PROJECT_ID.curated")

entry = bigquery.AccessEntry(
    role="READER",
    entity_type="user",
    entity_id="analyst@yourcompany.com",
)
dataset.access_entries = [entry]
dataset = client.update_dataset(dataset, update_mode="update_fields")
```

---

## 💡 Production Notes

- **Use `exists_ok=True` everywhere.** Setup scripts should be re-runnable.
- **Set `location` explicitly.** It is immutable, and the default is `US`.
- **Set `default_table_expiration_ms` on every non-gold dataset.** It is the cheapest cost control
  in the platform.
- **Labels are the only reliable cost-attribution mechanism.** Set them at creation.
- **Never call `delete_dataset(delete_contents=True)` without a guard.** It deletes every table.
- **Remember that `update_mode="update_full"` resets unset fields.** Use `"update_fields"` unless
  you specifically want a full replacement.

---

## 🔑 Key Takeaways

- `bigquery.Dataset` maps 1:1 to a BigQuery dataset and all its options.
- **`exists_ok=True` is the idempotency key** for setup scripts.
- `location` is immutable — choose it carefully.
- `default_table_expiration_ms` and `default_partition_expiration_days` are the automatic cost
  controls.
- `update_mode="update_fields"` vs `"update_full"` — know which you want.
- Guard `delete_contents=True` behind an explicit force flag.

---

## 📚 Practice Exercises

1. **Environment provisioner.** Write a script that provisions a full environment: datasets,
   labels, expirations, and service accounts. It must be safe to re-run.

2. **Dataset audit.** Write a report generator that lists every dataset in a project with its
   location, labels, expirations, table count, and total size. Flag datasets missing labels or
   expirations.

3. **Migration tool.** Write a script that copies a dataset to a new project with labels and
   expirations preserved, and verifies row counts match.

4. **Cost projection.** Given a dataset's current size and expiration settings, project its
   storage cost in 6 months. Include the effect of growing daily.

5. **Guard pattern.** Write a `safe_delete_dataset` function that refuses to delete a non-empty
   dataset, requires a confirmation string, and logs the action.

---

## 📖 Further Reading

- `Dataset` reference — https://cloud.google.com/python/docs/reference/bigquery/latest/bigquery.dataset.Dataset
- Creating datasets — https://cloud.google.com/bigquery/docs/dataset-options
- Python client samples — https://cloud.google.com/bigquery/docs/samples-python
