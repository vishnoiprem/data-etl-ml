import abc
from pyspark.sql import SparkSession, DataFrame


class PySparkJobInterface(abc.ABC):
    def __init__(self):
        self.spark = self.init_spark_session()

    @abc.abstractmethod
    def init_spark_session(self) -> SparkSession:
        pass

    @abc.abstractmethod
    def read_events_batch(self, input_path: str) -> DataFrame:
        pass

    @abc.abstractmethod
    def read_curated_if_exists(self, curated_path: str) -> DataFrame:
        pass

    @abc.abstractmethod
    def quarantine_events(self, events_df: DataFrame) -> DataFrame:
        pass

    @abc.abstractmethod
    def extract_late_arrivals(self, events_df: DataFrame, run_date: str) -> DataFrame:
        pass

    @abc.abstractmethod
    def extract_fresh_events(self, events_df: DataFrame, run_date: str) -> DataFrame:
        pass

    @abc.abstractmethod
    def merge_into_curated(self, curated_df: DataFrame, fresh_events_df: DataFrame) -> DataFrame:
        pass

    @abc.abstractmethod
    def extract_archived_versions(self, curated_df: DataFrame, fresh_events_df: DataFrame) -> DataFrame:
        pass

    @abc.abstractmethod
    def compute_drift_metrics(
        self,
        curated_before: DataFrame,
        curated_after: DataFrame,
        quarantine_df: DataFrame,
        late_arrivals_df: DataFrame,
        fresh_events_df: DataFrame,
        run_date: str,
    ) -> DataFrame:
        pass

    def stop(self):
        self.spark.stop()
