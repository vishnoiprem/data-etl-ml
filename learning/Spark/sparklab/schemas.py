"""Explicit schemas for every fixture used in the labs.

Why this module exists
-----------------------
``inferSchema=True`` is the single most common mistake in self-taught Spark
code. It costs an extra pass over the data, and — worse — it makes the
schema *data-dependent*. A column that is an integer in today's file and
contains a stray ``"N/A"`` tomorrow changes type, which changes the plan,
which changes the output. In production that is an incident.

Every read in this repo passes one of these schemas instead.
"""

from __future__ import annotations

from pyspark.sql.types import (
    DoubleType,
    LongType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

__all__ = [
    "EVENTS_SCHEMA",
    "SALES_SCHEMA",
    "TRANSACTIONS_SCHEMA",
    "WIRE_SCHEMA",
]

#: ``sales.csv`` — the aggregate/salting fixture.
SALES_SCHEMA = StructType(
    [
        StructField("timestamp", TimestampType(), True),
        StructField("region", StringType(), True),
        StructField("sales_amount", DoubleType(), True),
        StructField("product", StringType(), True),
    ]
)

#: ``skewed_events.csv`` — one hot key plus a long tail.
EVENTS_SCHEMA = StructType(
    [
        StructField("user_id", LongType(), True),
        StructField("event_type", StringType(), True),
        StructField("event_time", TimestampType(), True),
    ]
)

#: ``transactions.csv`` — the aggregation fixture.
TRANSACTIONS_SCHEMA = StructType(
    [
        StructField("transaction_id", StringType(), True),
        StructField("customer_id", StringType(), True),
        StructField("amount", DoubleType(), True),
        StructField("txn_date", StringType(), True),
    ]
)

#: Cross-border wires — used by the windowing and broadcasting labs.
WIRE_SCHEMA = StructType(
    [
        StructField("wire_id", StringType(), True),
        StructField("sender_customer_id", StringType(), True),
        StructField("sender_country", StringType(), True),
        StructField("receiver_customer_id", StringType(), True),
        StructField("receiver_country", StringType(), True),
        StructField("amount_usd", DoubleType(), True),
        StructField("value_date", StringType(), True),
    ]
)
