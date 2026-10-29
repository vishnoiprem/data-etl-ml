"""Data generator for simulating live order streams into PostgreSQL."""

import logging
import random
import signal
import sys
import time
from dataclasses import dataclass
from typing import Optional

import psycopg2
from faker import Faker
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

fake = Faker()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeneratorConfig:
    """Configuration for the data generator."""
    host: str = "localhost"
    port: int = 5432
    database: str = "postgres"
    user: str = "postgres"
    password: str = "postgres"
    min_pool_size: int = 1
    max_pool_size: int = 5
    user_count: int = 10
    min_amount: float = 10.0
    max_amount: float = 500.0
    min_interval: float = 0.1
    max_interval: float = 0.5
    batch_size: int = 1


class OrderDataGenerator:
    """Generates synthetic order data and inserts into PostgreSQL."""

    def __init__(self, config: Optional[GeneratorConfig] = None):
        self.config = config or GeneratorConfig()
        self._pool: Optional[pool.ThreadedConnectionPool] = None
        self._running = False

    def _create_pool(self) -> pool.ThreadedConnectionPool:
        """Create a connection pool for PostgreSQL."""
        return pool.ThreadedConnectionPool(
            minconn=self.config.min_pool_size,
            maxconn=self.config.max_pool_size,
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=self.config.user,
            password=self.config.password,
        )

    def _shutdown(self, signum: int, frame) -> None:
        """Handle shutdown signals gracefully."""
        logger.info("Shutdown signal received, stopping generator...")
        self._running = False

    def _get_connection(self):
        """Get a connection from the pool."""
        if self._pool is None:
            self._pool = self._create_pool()
        return self._pool.getconn()

    def _return_connection(self, conn) -> None:
        """Return a connection to the pool."""
        if self._pool and conn:
            self._pool.putconn(conn)

    def _generate_order(self) -> tuple[str, float]:
        """Generate a single order."""
        user_id = f"user_{random.randint(1, self.config.user_count)}"
        amount = round(random.uniform(self.config.min_amount, self.config.max_amount), 2)
        return user_id, amount

    def _insert_batch(self, orders: list[tuple[str, float]]) -> int:
        """Insert a batch of orders.

        Args:
            orders: List of (user_id, amount) tuples

        Returns:
            Number of successfully inserted orders
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.executemany(
                    "INSERT INTO orders (user_id, amount) VALUES (%s, %s)",
                    orders
                )
                conn.commit()
                return len(orders)
        except psycopg2.Error as e:
            logger.error("Database error during batch insert: %s", e)
            if conn:
                conn.rollback()
            return 0
        except Exception as e:
            logger.exception("Unexpected error during batch insert: %s", e)
            if conn:
                conn.rollback()
            return 0
        finally:
            self._return_connection(conn)

    def run(self) -> None:
        """Run the data generator until interrupted."""
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

        self._running = True
        logger.info("Starting order data generator (press Ctrl+C to stop)")

        while self._running:
            try:
                batch = [
                    self._generate_order()
                    for _ in range(self.config.batch_size)
                ]
                inserted = self._insert_batch(batch)
                if inserted:
                    for user_id, amount in batch:
                        logger.info("Inserted: %s, $%.2f", user_id, amount)

                sleep_time = random.uniform(self.config.min_interval, self.config.max_interval)
                time.sleep(sleep_time)

            except Exception as e:
                logger.exception("Error in generator loop: %s", e)
                time.sleep(1.0)  # Back off on error

        self._cleanup()

    def _cleanup(self) -> None:
        """Clean up resources."""
        if self._pool:
            self._pool.closeall()
            logger.info("Connection pool closed")
        logger.info("Generator stopped cleanly")


def main() -> None:
    """Entry point for the data generator."""
    config = GeneratorConfig()
    generator = OrderDataGenerator(config)
    generator.run()


if __name__ == "__main__":
    main()