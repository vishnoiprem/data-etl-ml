import os

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    TimestampType,
    IntegerType,
    ArrayType,
    MapType,
)

from main.base import PySparkJobInterface


class PySparkJob(PySparkJobInterface):

    def init_spark_session(self) -> SparkSession:
        return (
            SparkSession.builder
            .appName("RepoSphere CDC Merge")
            .master("local[*]")
            .config("spark.sql.session.timeZone", "UTC")
            .getOrCreate()
        )

    # =========================================================
    # Helpers
    # =========================================================

    def _empty_curated_df(self) -> DataFrame:
        schema = StructType([
            StructField("event_id", StringType(), True),
            StructField("event_type", StringType(), True),
            StructField("created_ts", TimestampType(), True),
            StructField("ingested_ts", TimestampType(), True),
            StructField("repo_id", StringType(), True),
            StructField("repo_name", StringType(), True),
            StructField("actor_login", StringType(), True),
        ])

        return self.spark.createDataFrame([], schema)

    def _nested_exists(
        self,
        df: DataFrame,
        parent: str,
        child: str
    ) -> bool:

        if parent not in df.columns:
            return False

        parent_field = next(
            field
            for field in df.schema.fields
            if field.name == parent
        )

        if not isinstance(parent_field.dataType, StructType):
            return False

        return child in parent_field.dataType.fieldNames()

    def _repo_id(self, df: DataFrame):
        if self._nested_exists(df, "repo", "id"):
            return F.col("repo.id").cast("string")

        return F.lit(None).cast("string")

    def _repo_name(self, df: DataFrame):
        if self._nested_exists(df, "repo", "name"):
            return F.col("repo.name").cast("string")

        return F.lit(None).cast("string")

    def _actor_login(self, df: DataFrame):
        if self._nested_exists(df, "actor", "login"):
            return F.col("actor.login").cast("string")

        return F.lit(None).cast("string")

    def _event_id(self, df: DataFrame):
        if "event_id" in df.columns:
            return F.col("event_id").cast("string")

        return F.lit(None).cast("string")

    def _event_type(self, df: DataFrame):
        if "event_type" in df.columns:
            return F.col("event_type").cast("string")

        return F.lit(None).cast("string")

    def _created_ts(self, df: DataFrame):
        if "created_at" in df.columns:
            return F.to_timestamp(F.col("created_at"))

        return F.lit(None).cast("timestamp")

    def _ingested_ts(self, df: DataFrame):
        if "ingested_at" in df.columns:
            return F.to_timestamp(F.col("ingested_at"))

        return F.lit(None).cast("timestamp")

    def _flatten_events(self, df: DataFrame) -> DataFrame:

        core_input_columns = {
            "event_id",
            "event_type",
            "created_at",
            "ingested_at",
            "repo",
            "actor",
        }

        extra_columns = []

        # Preserve optional top-level scalar fields
        for field in df.schema.fields:
            if field.name in core_input_columns:
                continue

            if isinstance(
                field.dataType,
                (StructType, ArrayType, MapType)
            ):
                continue

            extra_columns.append(
                F.col(f"`{field.name}`")
            )

        return df.select(
            self._event_id(df).alias("event_id"),
            self._event_type(df).alias("event_type"),
            self._created_ts(df).alias("created_ts"),
            self._ingested_ts(df).alias("ingested_ts"),
            self._repo_id(df).alias("repo_id"),
            self._repo_name(df).alias("repo_name"),
            self._actor_login(df).alias("actor_login"),
            *extra_columns
        )

    def _well_formed_events(
        self,
        events_df: DataFrame
    ) -> DataFrame:

        return (
            events_df
            .withColumn(
                "_check_event_id",
                self._event_id(events_df)
            )
            .withColumn(
                "_check_repo_id",
                self._repo_id(events_df)
            )
            .withColumn(
                "_check_created_ts",
                self._created_ts(events_df)
            )
            .filter(
                F.col("_check_event_id").isNotNull()
                & (F.trim(F.col("_check_event_id")) != "")
                & F.col("_check_repo_id").isNotNull()
                & F.col("_check_created_ts").isNotNull()
            )
        )

    # =========================================================
    # 1. Read Events
    # =========================================================

    def read_events_batch(
        self,
        input_path: str
    ) -> DataFrame:

        return (
            self.spark.read
            .option("multiLine", "false")
            .json(input_path)
        )

    # =========================================================
    # 2. Read Curated
    # =========================================================

    def read_curated_if_exists(
        self,
        curated_path: str
    ) -> DataFrame:

        if not os.path.isdir(curated_path):
            return self._empty_curated_df()

        has_file = any(
            os.path.isfile(
                os.path.join(curated_path, name)
            )
            for name in os.listdir(curated_path)
        )

        if not has_file:
            return self._empty_curated_df()

        return self.spark.read.parquet(curated_path)

    # =========================================================
    # 3. Quarantine
    # =========================================================

    def quarantine_events(
        self,
        events_df: DataFrame
    ) -> DataFrame:

        checked = (
            events_df
            .withColumn(
                "_check_event_id",
                self._event_id(events_df)
            )
            .withColumn(
                "_check_repo_id",
                self._repo_id(events_df)
            )
            .withColumn(
                "_check_created_ts",
                self._created_ts(events_df)
            )
        )

        return (
            checked
            .withColumn(
                "quarantine_reason",

                F.when(
                    F.col("_check_event_id").isNull()
                    | (
                        F.trim(
                            F.col("_check_event_id")
                        ) == ""
                    ),
                    F.lit("missing_event_id")
                )
                .when(
                    F.col("_check_repo_id").isNull(),
                    F.lit("missing_repo_id")
                )
                .when(
                    F.col("_check_created_ts").isNull(),
                    F.lit("invalid_created_at")
                )
            )
            .filter(
                F.col("quarantine_reason").isNotNull()
            )
            .drop(
                "_check_event_id",
                "_check_repo_id",
                "_check_created_ts"
            )
        )

    # =========================================================
    # 4. Late Arrivals
    # =========================================================

    def extract_late_arrivals(
        self,
        events_df: DataFrame,
        run_date: str
    ) -> DataFrame:

        valid_df = self._well_formed_events(events_df)

        cutoff = (
            F.date_sub(
                F.to_date(F.lit(run_date)),
                7
            )
            .cast("timestamp")
        )

        late_df = (
            valid_df
            .filter(
                F.col("_check_created_ts") < cutoff
            )
            .drop(
                "_check_event_id",
                "_check_repo_id",
                "_check_created_ts"
            )
        )

        return self._flatten_events(late_df)

    # =========================================================
    # 5. Fresh Events
    # =========================================================

    def extract_fresh_events(
        self,
        events_df: DataFrame,
        run_date: str
    ) -> DataFrame:

        valid_df = self._well_formed_events(events_df)

        cutoff = (
            F.date_sub(
                F.to_date(F.lit(run_date)),
                7
            )
            .cast("timestamp")
        )

        fresh_df = (
            valid_df
            .filter(
                F.col("_check_created_ts") >= cutoff
            )
            .drop(
                "_check_event_id",
                "_check_repo_id",
                "_check_created_ts"
            )
        )

        return self._flatten_events(fresh_df)

    # =========================================================
    # 6. Merge Into Curated
    # =========================================================

    def merge_into_curated(
        self,
        curated_df: DataFrame,
        fresh_events_df: DataFrame
    ) -> DataFrame:

        combined_df = curated_df.unionByName(
            fresh_events_df,
            allowMissingColumns=True
        )

        window_spec = (
            Window
            .partitionBy("event_id")
            .orderBy(
                F.col("ingested_ts").desc_nulls_last()
            )
        )

        return (
            combined_df
            .withColumn(
                "_rn",
                F.row_number().over(window_spec)
            )
            .filter(
                F.col("_rn") == 1
            )
            .drop("_rn")
        )

    # =========================================================
    # 7. Archive Superseded Versions
    # =========================================================

    def extract_archived_versions(
        self,
        curated_df: DataFrame,
        fresh_events_df: DataFrame
    ) -> DataFrame:

        fresh_latest = (
            fresh_events_df
            .groupBy("event_id")
            .agg(
                F.max("ingested_ts")
                .alias("_fresh_max_ts")
            )
        )

        return (
            curated_df.alias("old")
            .join(
                fresh_latest.alias("new"),
                F.col("old.event_id")
                == F.col("new.event_id"),
                "inner"
            )
            .filter(
                F.col("new._fresh_max_ts")
                > F.col("old.ingested_ts")
            )
            .select("old.*")
        )

    # =========================================================
    # 8. Drift Metrics
    # =========================================================

    def compute_drift_metrics(
        self,
        curated_before: DataFrame,
        curated_after: DataFrame,
        quarantine_df: DataFrame,
        late_arrivals_df: DataFrame,
        fresh_events_df: DataFrame,
        run_date: str,
    ) -> DataFrame:

        # -----------------------------------------
        # Quarantine + Late Counts
        # -----------------------------------------

        rows_quarantined = quarantine_df.count()
        rows_late = late_arrivals_df.count()

        # -----------------------------------------
        # Inserted Event IDs
        # -----------------------------------------

        before_ids = (
            curated_before
            .select("event_id")
            .distinct()
        )

        fresh_ids = (
            fresh_events_df
            .select("event_id")
            .distinct()
        )

        rows_inserted = (
            fresh_ids
            .join(
                before_ids,
                on="event_id",
                how="left_anti"
            )
            .count()
        )

        # -----------------------------------------
        # Updated Event IDs
        # -----------------------------------------

        before_max = (
            curated_before
            .groupBy("event_id")
            .agg(
                F.max("ingested_ts")
                .alias("_old_ts")
            )
        )

        fresh_max = (
            fresh_events_df
            .groupBy("event_id")
            .agg(
                F.max("ingested_ts")
                .alias("_new_ts")
            )
        )

        rows_updated = (
            before_max
            .join(
                fresh_max,
                on="event_id",
                how="inner"
            )
            .filter(
                F.col("_new_ts") > F.col("_old_ts")
            )
            .select("event_id")
            .distinct()
            .count()
        )

        # -----------------------------------------
        # Schema Drift
        # -----------------------------------------

        new_fields_added = sorted(
            list(
                set(curated_after.columns)
                - set(curated_before.columns)
            )
        )

        # -----------------------------------------
        # Explicit Metrics Schema
        # -----------------------------------------

        metrics_schema = StructType([
            StructField(
                "run_date",
                StringType(),
                False
            ),
            StructField(
                "rows_quarantined",
                IntegerType(),
                False
            ),
            StructField(
                "rows_late",
                IntegerType(),
                False
            ),
            StructField(
                "rows_inserted",
                IntegerType(),
                False
            ),
            StructField(
                "rows_updated",
                IntegerType(),
                False
            ),
            StructField(
                "new_fields_added",
                ArrayType(StringType()),
                False
            ),
        ])

        metrics_df = self.spark.createDataFrame(
            [
                (
                    run_date,
                    int(rows_quarantined),
                    int(rows_late),
                    int(rows_inserted),
                    int(rows_updated),
                    new_fields_added,
                )
            ],
            schema=metrics_schema
        )

        return metrics_df.withColumn(
            "run_date",
            F.to_date("run_date")
        )