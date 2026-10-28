```python
# Exercise 1
def audit_environment():
    import importlib.util
    return {
        "python_3_9_plus": sys.version_info >= (3, 9),
        "jinja2": importlib.util.find_spec("jinja2") is not None,
        "pandas": importlib.util.find_spec("pandas") is not None,
        "sample_data": (COURSE_ROOT / "sample_data" / "orders.csv").exists(),
        "local_runner": "local_runner" in sys.modules,
    }

print(audit_environment())
```

```python
# Exercise 2
for item in rejected_m:
    print(f"{item['reason']:<26} detail={item['detail']!r:<14} raw={item['raw'][:60]!r}")
```

The reason codes (`missing_order_id`, `bad_timestamp`, `unknown_region`,
`unknown_currency`, `wrong_field_count`, ...) form a small closed set, so
they are safe as metric labels and safe to alert on. The raw payload is
arbitrary user data — high cardinality, possibly containing PII, and it ends
up in logs and in the dead-letter table. One is a dimension; the other is
a measure.

```python
# Exercise 3
print(len(lines) - 1 - len(accepted))       # 3755 not accepted
print(sum(status_counts.values()))          # 5000 parseable
print(validity_counts["valid"])             # 4705 valid
```

Of the 5000 rows: 295 are not parseable or valid (rejected), 4705 are valid,
and of those 4705 only the 1245 with `status == "complete"` are
revenue-bearing. The remaining 3460 valid rows are `active`, `cancelled` or
`refunded`.

If the pipeline selected only `complete` rows, an order that arrives as
`active` would be dropped on that day's run and — because the raw file is
replaced daily — would never be picked up again. It would be lost
permanently. This is why the course separates *acceptance* from *revenue*:
a correct pipeline keeps the row and computes revenue from it, so yesterday's
`active` order becomes today's revenue when it completes.
