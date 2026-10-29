# monitor.py
"""Live dashboard for user analytics from Redis."""

import json
import logging
import signal
import sys
import time
from typing import Optional

import redis
from redis.exceptions import RedisError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DashboardMonitor:
    """Monitors and displays live user analytics from Redis."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        refresh_interval: float = 2.0,
        key_pattern: str = "user_analytics:*",
    ):
        self.refresh_interval = refresh_interval
        self.key_pattern = key_pattern
        self._running = False

        self._pool = redis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
            max_connections=10,
        )
        self._client = redis.Redis(connection_pool=self._pool)

    def _shutdown(self, signum: int, frame) -> None:
        """Handle shutdown signals gracefully."""
        logger.info("Shutdown signal received, stopping monitor...")
        self._running = False

    def _fetch_analytics(self) -> list[dict]:
        """Fetch all user analytics from Redis."""
        results = []
        try:
            for key in self._client.scan_iter(match=self.key_pattern, count=100):
                data = self._client.get(key)
                if data:
                    try:
                        user_id = key.split(":")[-1]
                        parsed = json.loads(data)
                        parsed["user_id"] = user_id
                        results.append(parsed)
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning("Failed to parse data for key %s: %s", key, e)
        except RedisError as e:
            logger.error("Redis error while fetching analytics: %s", e)
        return results

    def _display(self, analytics: list[dict]) -> None:
        """Display analytics in a formatted dashboard."""
        if not analytics:
            print("\n=== LIVE USER ANALYTICS ===")
            print("No data available")
            return

        print("\n=== LIVE USER ANALYTICS ===")
        print(f"{'User ID':<20} {'Orders':>10} {'Revenue':>15}")
        print("-" * 48)
        for item in analytics:
            user_id = item.get("user_id", "unknown")
            orders = item.get("total_orders", 0)
            revenue = item.get("total_revenue", 0.0)
            print(f"{user_id:<20} {orders:>10} ${revenue:>14.2f}")

    def run(self) -> None:
        """Run the dashboard monitor until interrupted."""
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

        self._running = True
        logger.info("Starting dashboard monitor (press Ctrl+C to stop)")

        while self._running:
            try:
                analytics = self._fetch_analytics()
                self._display(analytics)
                time.sleep(self.refresh_interval)
            except Exception as e:
                logger.exception("Unexpected error in monitor loop: %s", e)
                time.sleep(self.refresh_interval)

        self._cleanup()

    def _cleanup(self) -> None:
        """Clean up resources."""
        try:
            self._client.close()
            self._pool.disconnect()
            logger.info("Monitor stopped cleanly")
        except Exception as e:
            logger.error("Error during cleanup: %s", e)


def main() -> None:
    """Entry point for the dashboard monitor."""
    monitor = DashboardMonitor()
    monitor.run()


if __name__ == "__main__":
    main()