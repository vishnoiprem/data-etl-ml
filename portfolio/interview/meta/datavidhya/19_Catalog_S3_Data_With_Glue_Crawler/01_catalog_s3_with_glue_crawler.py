"""
Q19: Catalog S3 Data with a Glue Crawler   [AWS | Glue, S3, Crawlers, Athena]

Offline driver: replay the 7 lab stages against a moto-mocked Glue + S3
+ Athena. No AWS, no Glue, no S3 -- just the catalog and a Python dict.

How to Think:
- The Glue Data Catalog is metadata, not data. It holds a list of tables,
  each with a name, a schema, a file format, and an S3 location pointer.
  When Athena runs ``SELECT * FROM catalog_db.orders``, it asks Glue for
  the table definition, then reads the S3 files directly using the
  format + SerDe Glue recorded.
- A crawler doesn't actually read the data files into Glue. It samples
  them, infers the schema (column names + types), and writes a table
  definition into the catalog. The bytes in S3 are untouched.
- Crawler type inference is best-effort. Glue looks at a sample of values
  per column and picks the broadest type. A single "N/A" in a date column
  falls back to string -- exactly the trap this lab is built around.

The trap:
- The seed CSV has one row (1009) with ``order_date = "N/A"``. After the
  crawler runs, ``order_date`` is inferred as ``string``, not ``date``.
  The fix is a Glue ``UpdateTable`` call that rewrites the column type --
  the S3 file is never re-read.
- One table per folder of homogeneous files. ``raw/orders/`` becomes
  table ``orders``; ``raw/customers/`` becomes table ``customers``. The
  crawler will NOT merge them even if the schemas happen to overlap.
- A crawler's IAM role is what authorizes it to read S3 and write Glue.
  In the lab the role is pre-provisioned with the right permissions.

AWS note:
- Real Glue crawlers cost money per object crawled. Each S3 file is one
  billable "object" the first time the crawler sees it. For a 12-row CSV
  this is sub-cent; for a million-object bucket it adds up fast.
- The Glue Data Catalog itself is free for the first million objects;
  above that it's per-object per-month. Production data lakes budget
  for this.
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from moto import mock_aws  # noqa: E402

from catalog import Catalog  # noqa: E402


def expect(title: str, got, expected) -> None:
    if got != expected:
        print(f"[FAIL] {title}")
        print(f"   expected: {expected}")
        print(f"   got:      {got}")
        raise AssertionError(title)
    print(f"[PASS] {title}")


def _columns_by_name(cat: Catalog, table: str) -> dict:
    """Helper: Glue column list as a {Name: Type} dict for fast assertions."""
    return {c["Name"]: c["Type"] for c in cat.get_columns(table)}


def main() -> None:
    bucket = "glue-crawler-catalog-bucket-test"
    db     = "catalog_db_test"
    role   = "arn:aws:iam::123456789012:role/GlueCrawlerLabRole-test"

    cat = Catalog(bucket=bucket, database=db, role_arn=role)

    print("\n=== Q19 Catalog S3 Data with a Glue Crawler ===\n")

    with mock_aws():
        cat.setUp()

        # ------ stage 1: lab pre-provisions a bucket; we upload the seeds.
        orders_url = cat.upload("raw/orders",
                                 os.path.join(_HERE, "sample_data", "orders",
                                              "orders.csv"))
        cust_url   = cat.upload("raw/customers",
                                 os.path.join(_HERE, "sample_data", "customers",
                                              "customers.json"))
        expect("Q19 stage 1 orders CSV is at s3://.../raw/orders/orders.csv",
               orders_url, f"s3://{bucket}/raw/orders/orders.csv")
        expect("Q19 stage 1 customers JSON is at s3://.../raw/customers/customers.json",
               cust_url,   f"s3://{bucket}/raw/customers/customers.json")

        # ------ stage 2: create the crawler pointed at both prefixes.
        crawler = cat.create_crawler(
            name="orders-and-customers-crawler",
            s3_paths=[f"s3://{bucket}/raw/orders/",
                       f"s3://{bucket}/raw/customers/"],
        )
        expect("Q19 stage 2 crawler target has both S3 prefixes",
               sorted(t["Path"] for t in crawler["Targets"]["S3Targets"]),
               sorted([f"s3://{bucket}/raw/orders/",
                       f"s3://{bucket}/raw/customers/"]))
        expect("Q19 stage 2 crawler points at the catalog_db_xxx database",
               crawler["DatabaseName"], db)
        expect("Q19 stage 2 crawler uses the lab-provided IAM role",
               crawler["Role"], role)

        # ------ stage 3: start the crawler; it walks S3 and registers tables.
        cat.start_crawler("orders-and-customers-crawler")
        cat.infer_catalog_from_crawl("orders-and-customers-crawler")

        expect("Q19 stage 3 crawler registered TWO tables (one per folder)",
               cat.list_tables(), ["customers", "orders"])
        expect("Q19 stage 3 orders table points at the right S3 location",
               cat.get_location("orders"),
               f"s3://{bucket}/raw/orders/")
        expect("Q19 stage 3 customers table points at the right S3 location",
               cat.get_location("customers"),
               f"s3://{bucket}/raw/customers/")

        # ------ stage 4: review the inferred schemas (and find the trap).
        orders_cols = _columns_by_name(cat, "orders")
        cust_cols   = _columns_by_name(cat, "customers")
        expect("Q19 stage 4 orders table has six columns",
               sorted(orders_cols), sorted(["order_id", "customer_id", "amount",
                                            "currency", "order_date", "status"]))
        expect("Q19 stage 4 customers table has five columns",
               sorted(cust_cols), sorted(["customer_id", "name", "tier",
                                          "country", "signup_date"]))
        expect("Q19 stage 4 order_id inferred as bigint (clean numeric column)",
               orders_cols["order_id"], "bigint")
        expect("Q19 stage 4 amount inferred as double (clean numeric column)",
               orders_cols["amount"], "double")
        expect("Q19 stage 4 currency inferred as string",
               orders_cols["currency"], "string")
        # The trap: order_date has a single 'N/A' row 1009. Crawler falls back.
        expect("Q19 stage 4 TRAP -- order_date inferred as STRING "
               "(N/A in row 1009 poisons the column)",
               orders_cols["order_date"], "string")
        expect("Q19 stage 4 customers.customer_id inferred as bigint",
               cust_cols["customer_id"], "bigint")
        expect("Q19 stage 4 customers.signup_date inferred as date "
               "(no contamination)",
               cust_cols["signup_date"], "date")

        # ------ stage 5: fix the schema WITHOUT touching the S3 file.
        cat.update_column_type("orders", "order_date", "date")
        fixed_cols = _columns_by_name(cat, "orders")
        expect("Q19 stage 5 order_date is now 'date' (caller patched the schema)",
               fixed_cols["order_date"], "date")
        expect("Q19 stage 5 the S3 location of the orders table is unchanged",
               cat.get_location("orders"),
               f"s3://{bucket}/raw/orders/")
        # Sanity: original row 1009 still has 'N/A' in S3 (caller didn't rewrite).
        body = cat.s3.get_object(Bucket=bucket, Key="raw/orders/orders.csv")["Body"].read().decode("utf-8")
        expect("Q19 stage 5 the S3 file STILL contains 'N/A' "
               "(schema edit doesn't touch data)",
               "N/A" in body, True)

        # ------ stage 6: query both tables via Athena-style joins.
        # The driver doesn't run an actual SQL engine; it loads each table's
        # S3 file, joins them by customer_id, and aggregates.
        import csv as _csv
        import io as _io
        import json as _json

        orders = list(_csv.DictReader(_io.StringIO(body)))
        cust_body = cat.s3.get_object(Bucket=bucket, Key="raw/customers/customers.json")["Body"].read().decode("utf-8")
        customers = _json.loads(cust_body)

        by_id = {int(c["customer_id"]): c for c in customers}
        joined = [{"name": by_id[int(o["customer_id"])]["name"],
                    "tier": by_id[int(o["customer_id"])]["tier"],
                    "amount": float(o["amount"]),
                    "currency": o["currency"]}
                   for o in orders if int(o["customer_id"]) in by_id]

        per_customer = {}
        for r in joined:
            cid = next(k for k, v in by_id.items() if v["name"] == r["name"])
            per_customer.setdefault(r["name"], 0.0)
            per_customer[r["name"]] += r["amount"]

        expect("Q19 stage 6 join produced 12 rows (every order matches a customer)",
               len(joined), 12)
        expect("Q19 stage 6 Alice Johnson (id=42) has 3 orders totalling 354.75",
               round(per_customer["Alice Johnson"], 2), 354.75)
        # The "trap" customer: 1009 had N/A date -- still in the join because
        # the join is on customer_id, not order_date.
        expect("Q19 stage 6 every joined row has a tier (gold/silver/...)",
               all(r["tier"] in {"gold", "silver", "platinum", "bronze"}
                   for r in joined), True)

        # ------ stage 7: drop the catalog tables (data in S3 is preserved).
        cat.drop_table("orders")
        cat.drop_table("customers")
        expect("Q19 stage 7 catalog tables dropped",
               cat.list_tables(), [])
        # S3 objects survive -- external tables don't own their data.
        keys_left = [o["Key"] for o in
                     cat.s3.list_objects_v2(Bucket=bucket)["Contents"]]
        expect("Q19 stage 7 S3 objects survive the DROP TABLE",
               sorted(keys_left),
               sorted(["raw/orders/orders.csv",
                       "raw/customers/customers.json"]))

    print("\n=== All Q19 stages pass ===\n")


if __name__ == "__main__":
    main()
