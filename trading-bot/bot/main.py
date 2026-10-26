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
import threading

from broker.state import State
from broker.interface import AlpacaPaperBroker
from bot.signal_watcher import SignalWatcher
from bot.poller import SignalPoller
from bot.telegram_bot import run_telegram_bot


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
log = logging.getLogger("main")


def main():
    state = State(os.environ.get("TRADING_BOT_DB", "trades.db"))
    broker = AlpacaPaperBroker()
    notional = float(os.environ.get("TRADING_BOT_NOTIONAL", "200.0"))
    max_pct = float(os.environ.get("TRADING_BOT_MAX_POS_PCT", "0.20"))
    watcher = SignalWatcher(state, broker,
                            notional_per_trade=notional,
                            max_position_pct=max_pct)
    poller = SignalPoller(state, watcher, poll_interval=5.0)

    # Run the poller in a background thread
    t = threading.Thread(target=poller.run_forever, daemon=True, name="poller")
    t.start()
    log.info("poller started in background")

    # Run the Telegram bot in the main asyncio loop
    asyncio.run(run_telegram_bot(state, broker, watcher))


if __name__ == "__main__":
    main()
