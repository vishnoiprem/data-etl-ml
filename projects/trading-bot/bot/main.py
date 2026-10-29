"""Live bot entry point.

Wires the SignalPoller (background thread) and the Telegram bot
(asyncio event loop) together. Run with `make run` or directly:

    python -m bot.main

Requires env:
  ALPACA_API_KEY, ALPACA_SECRET_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
"""
from __future__ import annotations
import asyncio
import logging
import os
import signal
import sys
import threading
import time
from contextlib import suppress
from typing import Optional

from broker.state import State
from broker.interface import AlpacaPaperBroker, FakeBroker
from bot.signal_watcher import SignalWatcher
from bot.poller import SignalPoller
from bot.telegram_bot import run_telegram_bot


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
log = logging.getLogger("main")


class TradingBot:
    """Main trading bot orchestrator."""

    def __init__(self):
        self._poller_thread: Optional[threading.Thread] = None
        self._telegram_task: Optional[asyncio.Task] = None
        self._shutdown_event = threading.Event()
        self._state: Optional[State] = None
        self._broker = None
        self._watcher: Optional[SignalWatcher] = None
        self._poller: Optional[SignalPoller] = None

    def _setup_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._shutdown)

    def _shutdown(self, signum: int, frame) -> None:
        """Handle shutdown signals."""
        log.info("Shutdown signal received (%s), stopping bot...", signal.Signals(signum).name)
        self._shutdown_event.set()

    def _initialize_components(self) -> None:
        """Initialize all bot components."""
        # Database
        db_path = os.environ.get("TRADING_BOT_DB", "trades.db")
        self._state = State(db_path)

        # Broker
        use_fake = os.environ.get("TRADING_BOT_USE_FAKE_BROKER", "false").lower() == "true"
        if use_fake:
            self._broker = FakeBroker()
            log.info("Using FakeBroker")
        else:
            self._broker = AlpacaPaperBroker()
            log.info("Using AlpacaPaperBroker")

        # Signal watcher
        notional = float(os.environ.get("TRADING_BOT_NOTIONAL", "200.0"))
        max_pct = float(os.environ.get("TRADING_BOT_MAX_POS_PCT", "0.20"))
        self._watcher = SignalWatcher(self._state, self._broker,
                                      notional_per_trade=notional,
                                      max_position_pct=max_pct)

        # Signal poller
        poll_interval = float(os.environ.get("TRADING_BOT_POLL_INTERVAL", "5.0"))
        self._poller = SignalPoller(self._state, self._watcher, poll_interval=poll_interval)

    def _start_poller(self) -> None:
        """Start the signal poller in a background thread."""
        if self._poller is None:
            raise RuntimeError("Poller not initialized")

        self._poller_thread = threading.Thread(
            target=self._run_poller,
            daemon=True,
            name="signal-poller"
        )
        self._poller_thread.start()
        log.info("Signal poller started in background thread")

    def _run_poller(self) -> None:
        """Run poller loop with shutdown awareness."""
        while not self._shutdown_event.is_set():
            try:
                n = self._poller.tick() if self._poller else 0
                if n:
                    log.info("Processed %d new signals", n)
            except Exception:
                log.exception("Polling cycle failed")
            # Sleep with periodic shutdown checks
            for _ in range(int(self._poller.poll_interval * 10) if self._poller else 50):
                if self._shutdown_event.is_set():
                    break
                time.sleep(0.1)

    async def _start_telegram(self) -> None:
        """Start the Telegram bot."""
        if self._state is None or self._broker is None or self._watcher is None:
            raise RuntimeError("Components not initialized")

        self._telegram_task = asyncio.create_task(
            run_telegram_bot(self._state, self._broker, self._watcher)
        )
        log.info("Telegram bot started")

        try:
            await self._telegram_task
        except asyncio.CancelledError:
            log.info("Telegram bot cancelled")
            raise
        except Exception:
            log.exception("Telegram bot crashed")
            raise

    async def run(self) -> None:
        """Main async entry point."""
        self._setup_signal_handlers()
        self._initialize_components()
        self._start_poller()

        try:
            await self._start_telegram()
        finally:
            await self._cleanup()

    async def _cleanup(self) -> None:
        """Clean up all resources."""
        log.info("Cleaning up...")

        # Cancel telegram task
        if self._telegram_task and not self._telegram_task.done():
            self._telegram_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._telegram_task

        # Wait for poller thread
        if self._poller_thread and self._poller_thread.is_alive():
            log.info("Waiting for poller thread to finish...")
            self._poller_thread.join(timeout=5.0)

        # Close state
        if self._state:
            try:
                self._state.close()
                log.info("State database closed")
            except Exception:
                log.exception("Error closing state")

        log.info("Bot shutdown complete")


def main() -> None:
    """Entry point for the trading bot."""
    bot = TradingBot()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        log.info("Interrupted by user")
    except Exception:
        log.exception("Bot crashed")
        sys.exit(1)


if __name__ == "__main__":
    main()
