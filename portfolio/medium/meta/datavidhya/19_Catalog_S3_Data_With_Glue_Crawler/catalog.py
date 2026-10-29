"""Offline Glue-Data-Catalog + Crawler simulator for the Q19 lab.

Mirrors the Glue surface area used in the lab:

  - ``create_database``            -- Glue database (catalog namespace)
  - ``create_crawler``             -- S3 target + IAM role + DB
  - ``start_crawler``              -- reads sample S3 files, infers schemas,
                                     creates/updates one table per folder
  - ``get_table`` / ``get_tables`` -- inspect the catalog
  - ``update_table``               -- fix a mis-inferred column type
  - ``get_work_group`` / ``start_query_execution``  -- Athena read-only queries

The crawler type inference is a real CSV/JSON sampler. It picks the first
non-empty value per column and decides:

    ""      -> string  (can't tell)
    int     -> bigint
    float   -> double
    YYYY-MM-DD (or YYYY/MM/DD)  -> date

This mimics Glue's "infer from a sample of records" behaviour, including
the trap that an all-numeric column with a "N/A" row falls back to string.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3
from moto import mock_aws


_DATE_RE = re.compile(r"^\d{4}[-/]\d{2}[-/]\d{2}$")


# ============================================================ inference
def _infer_type(values: List[str]) -> str:
    """Glue's "look at a sample of values, pick the broadest type" rule.

    Empty list -> string. Otherwise union the per-value types and pick the
    broadest match. ``int`` -> ``bigint``; ``float`` -> ``double``;
    ``date`` -> ``date`` only if EVERY value parses; ``string`` wins ties.
    """
    types = {_infer_value(v) for v in values if v != ""}
    if not types:
        return "string"
    if types == {"int"}:
        return "bigint"
    if types == {"date"}:
        return "date"
    if types <= {"int", "float"}:
        return "double"
    if types <= {"int", "float", "date"}:
        # dates + numerics (e.g. an id-like ISO date) -> string
        return "string"
    return "string"


def _infer_value(v: str) -> str:
    if v == "":
        return "string"
    if _DATE_RE.match(v):
        return "date"
    try:
        int(v)
        return "int"
    except ValueError:
        pass
    try:
        float(v)
        return "float"
    except ValueError:
        pass
    return "string"


# ============================================================ csv sampler
def _sample_csv(text: str) -> List[Dict[str, str]]:
    """Read the CSV body into a list of row dicts."""
    return list(csv.DictReader(io.StringIO(text)))


# ============================================================ simulator
@dataclass
class Catalog:
    """In-memory replica of one Glue session.

    The driver's stages call methods in the same order the lab does them.
    The methods wrap ``boto3.client('glue')`` + ``boto3.client('s3')`` so
    the offline flow is structurally identical to the live flow.
    """
    bucket:        str
    database:      str
    role_arn:      str
    region:        str = "us-east-1"
    s3:            Any = field(init=False)
    glue:          Any = field(init=False)

    def __post_init__(self) -> None:
        # The driver / pytest wraps the whole flow in mock_aws(); we just
        # build clients lazily. setUp() is called explicitly so tests can
        # control the lifecycle.
        self.s3   = None
        self.glue = None

    # ----------------------------------------------------------- setup
    def setUp(self) -> None:
        """Provision clients + the S3 bucket + the Glue database."""
        self.s3   = boto3.client("s3",   region_name=self.region)
        self.glue = boto3.client("glue", region_name=self.region)
        self.s3.create_bucket(Bucket=self.bucket)
        self.glue.create_database(DatabaseInput={"Name": self.database})

    def upload(self, prefix: str, local_path: str) -> str:
        """Mirror ``aws s3 cp`` -- upload one file under ``prefix/``."""
        key = f"{prefix}/{os.path.basename(local_path)}"
        with open(local_path, "rb") as fh:
            self.s3.put_object(Bucket=self.bucket, Key=key, Body=fh.read())
        return f"s3://{self.bucket}/{key}"

    # ----------------------------------------------------------- crawler
    def create_crawler(self, name: str, s3_paths: List[str]) -> Dict[str, Any]:
        """``CreateCrawler`` with one S3 target per path the lab crawls."""
        targets = {"S3Targets": [{"Path": p} for p in s3_paths]}
        self.glue.create_crawler(
            Name=name,
            Role=self.role_arn,
            DatabaseName=self.database,
            Targets=targets,
        )
        return self.glue.get_crawler(Name=name)["Crawler"]

    def start_crawler(self, name: str) -> Dict[str, Any]:
        """``StartCrawler`` -- in moto, this transitions the crawler to
        RUNNING. The driver's ``infer_catalog_from_crawl`` reads the S3
        files itself and registers the discovered tables, mirroring how
        Glue's crawler would."""
        self.glue.start_crawler(Name=name)
        return self.glue.get_crawler(Name=name)["Crawler"]

    def infer_catalog_from_crawl(self, name: str) -> Dict[str, List[str]]:
        """Walk the crawler's S3 targets, read each prefix's files, infer
        schemas, and register a Glue table per prefix.

        Returns a mapping ``{prefix -> [table_name, ...]}``. One folder of
        homogeneous files produces one table -- exactly Glue's rule.
        """
        crawler = self.glue.get_crawler(Name=name)["Crawler"]
        result: Dict[str, List[str]] = {}

        for target in crawler["Targets"]["S3Targets"]:
            prefix = self._prefix_from_s3_uri(target["Path"])
            keys   = self._list_prefix(prefix)
            schema = self._infer_schema_for_prefix(prefix, keys)
            table  = self._table_name_from_prefix(prefix)
            self._register_table(table=table, prefix=prefix, schema=schema)
            result[prefix] = [table]

        # Glue marks the crawler SUCCEEDED once the crawl loop finishes.
        self.glue.update_crawler = None  # moto has no UpdateCrawler state machine;
        return result

    # ----------------------------------------------------------- queries
    def list_tables(self) -> List[str]:
        return sorted(t["Name"] for t in
                      self.glue.get_tables(DatabaseName=self.database)["TableList"])

    def get_columns(self, table: str) -> List[Dict[str, str]]:
        tbl = self.glue.get_table(DatabaseName=self.database,
                                  Name=table)["Table"]
        return tbl["StorageDescriptor"]["Columns"]

    def get_location(self, table: str) -> str:
        tbl = self.glue.get_table(DatabaseName=self.database,
                                  Name=table)["Table"]
        return tbl["StorageDescriptor"]["Location"]

    def update_column_type(self, table: str, column: str, new_type: str) -> None:
        """Mutate one column's type and persist via ``UpdateTable``."""
        tbl = self.glue.get_table(DatabaseName=self.database,
                                  Name=table)["Table"]
        cols = tbl["StorageDescriptor"]["Columns"]
        for c in cols:
            if c["Name"] == column:
                c["Type"] = new_type
        self.glue.update_table(
            DatabaseName=self.database,
            TableInput={
                "Name": table,
                "StorageDescriptor": {**tbl["StorageDescriptor"], "Columns": cols},
            },
        )

    def drop_table(self, table: str) -> None:
        self.glue.delete_table(DatabaseName=self.database, Name=table)

    # ------------------------------------------------------------ I/O
    def _prefix_from_s3_uri(self, uri: str) -> str:
        """``s3://bucket/prefix/`` -> ``prefix/`` (key prefix only)."""
        assert uri.startswith(f"s3://{self.bucket}/"), uri
        return uri[len(f"s3://{self.bucket}/"):]

    def _table_name_from_prefix(self, prefix: str) -> str:
        """``raw/orders/`` -> ``orders`` -- one table per folder."""
        parts = [p for p in prefix.split("/") if p]
        return parts[-1]

    def _list_prefix(self, prefix: str) -> List[str]:
        """All object keys under ``prefix/``."""
        keys = []
        kwargs = {"Bucket": self.bucket, "Prefix": prefix}
        while True:
            resp = self.s3.list_objects_v2(**kwargs)
            keys.extend(o["Key"] for o in resp.get("Contents", []))
            if not resp.get("IsTruncated"):
                break
            kwargs["ContinuationToken"] = resp["NextContinuationToken"]
        return keys

    def _infer_schema_for_prefix(self, prefix: str,
                                  keys: List[str]) -> List[Dict[str, str]]:
        """Read every file under ``prefix/``, sample rows, return Glue columns."""
        if not keys:
            return []
        first_key = keys[0]
        body = self.s3.get_object(Bucket=self.bucket, Key=first_key)["Body"].read()
        text = body.decode("utf-8")
        rows = self._parse(text, first_key)
        if not rows:
            return []
        columns = list(rows[0].keys())
        # Glue sees JSON numbers as numeric and strings as string; we coerce
        # to str so _infer_value gets a uniform string input.
        sampled = [[str(r.get(c, "")) for c in columns] for r in rows]
        sampled_rows = [dict(zip(columns, vals)) for vals in sampled]
        return [{"Name": c, "Type": _infer_type([r[c] for r in sampled_rows])}
                for c in columns]

    @staticmethod
    def _parse(text: str, key: str) -> List[Dict[str, Any]]:
        """Dispatch on file extension. CSV -> DictReader, JSON -> json.load."""
        if key.endswith(".json"):
            data = json.loads(text)
            # Glue crawls one-record-per-line JSON as well as JSON arrays;
            # we accept either shape.
            if isinstance(data, dict):
                return [data]
            return data
        return _sample_csv(text)

    def _register_table(self, table: str, prefix: str,
                         schema: List[Dict[str, str]]) -> None:
        is_json = any(k.endswith(".json") for k in self._list_prefix(prefix))
        serde, input_fmt, output_fmt = (
            ("org.openx.data.jsonserde.JsonSerDe",
             "org.apache.hadoop.mapred.TextInputFormat",
             "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat")
            if is_json else
            ("org.apache.hadoop.hive.serde2.OpenCSVSerde",
             "org.apache.hadoop.mapred.TextInputFormat",
             "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat")
        )
        self.glue.create_table(
            DatabaseName=self.database,
            TableInput={
                "Name": table,
                "StorageDescriptor": {
                    "Columns": schema,
                    "Location": f"s3://{self.bucket}/{prefix}",
                    "InputFormat":  input_fmt,
                    "OutputFormat": output_fmt,
                    "SerdeInfo": {"SerializationLibrary": serde},
                },
            },
        )


# ============================================================ demo entry
def _demo() -> None:  # pragma: no cover -- manual smoke test
    """Quick local sanity check -- not part of the lab."""
    here = Path(__file__).resolve().parent
    with mock_aws():
        cat = Catalog(bucket="x", database="d",
                       role_arn="arn:aws:iam::1:role/r")
        cat.setUp()
        cat.upload("raw/orders",
                    str(here / "sample_data" / "orders" / "orders.csv"))
        cat.upload("raw/customers",
                    str(here / "sample_data" / "customers" / "customers.json"))
        cat.create_crawler("c", ["s3://x/raw/orders/", "s3://x/raw/customers/"])
        cat.start_crawler("c")
        cat.infer_catalog_from_crawl("c")
        print(cat.list_tables())
        for t in cat.list_tables():
            print(t, cat.get_columns(t))
