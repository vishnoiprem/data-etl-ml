from pyspark.sql import SparkSession, DataFrame
from main.base import PySparkJobInterface


class PySparkJob(PySparkJobInterface):

    def init_spark_session(self) -> SparkSession:
        return (
            SparkSession.builder
            .appName("RepoSphere CDC Merge")
            .master("local[*]")
            .getOrCreate()
        )

    def read_events_batch(self, input_path: str) -> DataFrame:
        # Write your code here
        return (
            self.spark.read
            .option("multiLine", "false")
            .json(input_path)
        )

    def read_curated_if_exists(self, curated_path: str) -> DataFrame:
        # Write your code here
        import os

        if not os.path.isdir(curated_path):
            return self._empty_curated_df()

        has_file = any(
            os.path.isfile(os.path.join(curated_path, name))
            for name in os.listdir(curated_path)
        )

        if not has_file:
            return self._empty_curated_df()

        return self.spark.read.parquet(curated_path)

    def quarantine_events(self, events_df: DataFrame) -> DataFrame:
        # Write your code here
        pass

    def extract_late_arrivals(self, events_df: DataFrame, run_date: str) -> DataFrame:
        # Write your code here
        pass

    def extract_fresh_events(self, events_df: DataFrame, run_date: str) -> DataFrame:
        # Write your code here
        pass

    def merge_into_curated(self, curated_df: DataFrame, fresh_events_df: DataFrame) -> DataFrame:
        # Write your code here
        pass

    def extract_archived_versions(self, curated_df: DataFrame, fresh_events_df: DataFrame) -> DataFrame:
        # Write your code here
        pass

    def compute_drift_metrics(
            self,
            curated_before: DataFrame,
            curated_after: DataFrame,
            quarantine_df: DataFrame,
            late_arrivals_df: DataFrame,
            fresh_events_df: DataFrame,
            run_date: str,
    ) -> DataFrame:
        # Write your code here
        pass
