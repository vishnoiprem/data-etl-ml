**1.**

```python
def check_no_double_count(destination, source, tolerance=0.01):
    for region, expected in source.items():
        actual = destination.get(region)
        if actual is None:
            return False
        if abs(actual["revenue_eur"] - expected["revenue_eur"]) > tolerance:
            return False
    return True
```

After two `truncate` runs the table equals the source and the check returns `True`; after two `append` runs the revenue is doubled and the check returns `False`.

**2.** `dedup_key("ORD-1", "20260115")` is `"20260115:ORD-1"` and `dedup_key("ORD-1", "20260116")` is `"20260116:ORD-1"` — two distinct keys, so `dedup_rows` keeps both rows. Three rows in partition `20260115` collapse to one. The partition belongs in the key because an order id is only unique *within a day*; the same id appearing on two days is a different business fact, and keying on the id alone would silently discard one day's revenue.

**3.** Three typical breakages:

- *A task reading "today's" file* (`orders_{today}.csv`) reads the wrong day's data and writes it into the backfilled partition. Fix: derive the source path from the logical date or the data interval.
- *A whole-table truncate instead of a partition-scoped one* wipes the freshly loaded current-day partition. Fix: use the partition decorator `partition_for_date(logical_date)` with `WRITE_TRUNCATE`.
- *Row identity based on load time* means the backfilled rows get fresh keys and are appended alongside the originals, doubling the partition. Fix: content-derived `dedup_key(order_id, partition)` plus a merge/upsert or a partition-scoped truncate.
