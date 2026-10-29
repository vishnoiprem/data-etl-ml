"""Event time window processing with Apache Flink Table API.

This module demonstrates session and sliding window aggregations
for event stream processing.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from pyflink.table import EnvironmentSettings, TableEnvironment, Table
from pyflink.table.expressions import col

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WindowConfig:
    """Configuration for window processing."""
    session_gap_minutes: int = 5
    sliding_size_minutes: int = 10
    sliding_slide_minutes: int = 5


class EventWindowProcessor:
    """Processes event streams with session and sliding windows."""

    def __init__(self, config: Optional[WindowConfig] = None):
        self.config = config or WindowConfig()
        self._table_env: Optional[TableEnvironment] = None

    def _create_table_env(self) -> TableEnvironment:
        """Create and configure the Flink TableEnvironment."""
        env_settings = EnvironmentSettings.in_streaming_mode()
        table_env = TableEnvironment.create(env_settings)
        # Enable checkpointing for fault tolerance
        table_env.get_config().get_configuration().set_string(
            "execution.checkpointing.interval", "60s"
        )
        return table_env

    def create_source_table(self, table_env: TableEnvironment, data: list[tuple]) -> Table:
        """Create source table from event data.

        Args:
            table_env: Flink TableEnvironment
            data: List of (event_time, user_id, event_type) tuples

        Returns:
            Source table with proper timestamp type
        """
        schema = ["event_time", "user_id", "event_type"]
        source_table = table_env.from_elements(data, schema)

        # Convert string timestamp to TIMESTAMP(3)
        source_table = source_table.with_columns(
            col("event_time").cast("TIMESTAMP(3)").alias("event_time")
        )

        table_env.create_temporary_view("events", source_table)
        logger.info("Created source table with %d events", len(data))
        return source_table

    def session_window_query(self) -> str:
        """Generate session window aggregation query."""
        gap = self.config.session_gap_minutes
        return f"""
        SELECT
            SESSION_START(event_time, INTERVAL '{gap}' MINUTE) AS window_start,
            SESSION_END(event_time, INTERVAL '{gap}' MINUTE) AS window_end,
            user_id,
            COUNT(event_type) AS event_count
        FROM events
        GROUP BY
            SESSION(event_time, INTERVAL '{gap}' MINUTE),
            user_id
        """

    def sliding_window_query(self) -> str:
        """Generate sliding window aggregation query."""
        size = self.config.sliding_size_minutes
        slide = self.config.sliding_slide_minutes
        return f"""
        SELECT
            HOP_START(event_time, INTERVAL '{slide}' MINUTE, INTERVAL '{size}' MINUTE) AS window_start,
            HOP_END(event_time, INTERVAL '{slide}' MINUTE, INTERVAL '{size}' MINUTE) AS window_end,
            user_id,
            COUNT(event_type) AS event_count
        FROM events
        GROUP BY
            HOP(event_time, INTERVAL '{slide}' MINUTE, INTERVAL '{size}' MINUTE),
            user_id
        """

    def execute_query(self, table_env: TableEnvironment, query: str) -> Table:
        """Execute a SQL query and return the result table."""
        try:
            result = table_env.sql_query(query)
            logger.debug("Executed query successfully")
            return result
        except Exception as e:
            logger.error("Query execution failed: %s", e)
            raise

    def process(self, data: list[tuple]) -> dict[str, Table]:
        """Process events with both session and sliding windows.

        Args:
            data: List of (event_time, user_id, event_type) tuples

        Returns:
            Dictionary with 'session' and 'sliding' result tables
        """
        self._table_env = self._create_table_env()
        self.create_source_table(self._table_env, data)

        results = {}

        # Session window
        session_query = self.session_window_query()
        results["session"] = self.execute_query(self._table_env, session_query)

        # Sliding window
        sliding_query = self.sliding_window_query()
        results["sliding"] = self.execute_query(self._table_env, sliding_query)

        return results

    def print_results(self, results: dict[str, Table], limit: int = 100) -> None:
        """Print results with optional row limit."""
        for name, table in results.items():
            try:
                df = table.to_pandas()
                if len(df) > limit:
                    logger.warning(
                        "Result for %s has %d rows, showing first %d",
                        name, len(df), limit
                    )
                    df = df.head(limit)
                print(f"\n=== {name.upper()} WINDOW RESULTS ===")
                print(df.to_string(index=False))
            except Exception as e:
                logger.error("Failed to convert %s results to pandas: %s", name, e)


def create_sample_data() -> list[tuple]:
    """Create sample event data for demonstration."""
    return [
        ("2023-08-16 10:00:00", "user1", "click"),
        ("2023-08-16 10:02:00", "user1", "view"),
        ("2023-08-16 10:07:00", "user1", "purchase"),
        ("2023-08-16 10:10:00", "user2", "click"),
        ("2023-08-16 10:20:00", "user2", "view"),
        ("2023-08-16 10:25:00", "user2", "purchase"),
    ]


def main() -> None:
    """Main entry point for event window processing demo."""
    config = WindowConfig(session_gap_minutes=5, sliding_size_minutes=10, sliding_slide_minutes=5)
    processor = EventWindowProcessor(config)

    data = create_sample_data()
    results = processor.process(data)
    processor.print_results(results)


if __name__ == "__main__":
    main()
