# trading-bot

Auto-buy on signal, manual-sell from Telegram. Half-automated trading bot
that sits on top of your existing `realtime-stock-pipeline` (Kafka → Flink
→ TimescaleDB) and turns BUY signals into Alpaca paper-trading orders.

> **Disclaimer** — Educational project only. **Not financial advice.**
> No guarantee of accuracy, completeness, or profitability. Markets can
> lose money. Do your own research. The smoke test uses a fake broker
> with no real money.

## Architecture

```
TimescaleDB  ───►  SignalPoller  ───►  SignalWatcher  ───►  Broker
   (signals           (every 5s)         (size + decide)      (Alpaca paper)
    table)                                                      │
                                                                ▼
                                                          trades.db (SQLite)
                                                          └─ signals, decisions, trades
                                                                ▲
                                                                │
                                                         Telegram bot
                                                         (/status, /sell, /panic)
```

## What it does

1. **Polls TimescaleDB** every 5s for new BUY signals written by your
   Flink pipeline (the `realtime-stock-pipeline`).
2. **Sizes each buy** to a fixed notional (default $200) capped at 20%
   of available cash per position.
3. **Submits a market buy** to Alpaca paper via the official API.
4. **Records** every signal → decision → fill in a local SQLite ledger
   so we never re-buy the same signal even across restarts.
5. **Sends a Telegram alert** when a buy fills (you set this up in
   `telegram_bot.py`).
6. **Manual sell** via Telegram: `/sell TICKER N` or `/panic`.

## What it does NOT do

- It does NOT short sell.
- It does NOT place sell orders automatically. Exits are your call.
- It does NOT trade options, futures, or crypto. US equities only.
- It does NOT claim to make money. The signal quality is whatever your
  Flink pipeline produces.

## Quick start

### 1. Install

```bash
cd trading-bot
pip install -r requirements.txt
```

### 2. Get Alpaca paper credentials

Sign up at https://alpaca.markets (free), open a paper account, generate
an API key. Set:

```bash
export ALPACA_API_KEY=...
export ALPACA_SECRET_KEY=...
```

### 3. Get a Telegram bot token

1. Talk to @BotFather on Telegram.
2. `/newbot`, follow the prompts.
3. Copy the token, send any message to your new bot, then visit
   `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your chat id.

```bash
export TELEGRAM_BOT_TOKEN=...
export TELEGRAM_CHAT_ID=...
```

### 4. Make sure the stock pipeline is running

```bash
cd ../realtime-stock-pipeline
docker compose up -d
```

Wait for Flink to write some signals to TimescaleDB.

### 5. Run the bot

```bash
make run
```

You'll see the poller start logging every 5s. When a BUY signal arrives,
the bot places a market order and sends a Telegram message like:

```
🟢 BUY AAPL 2 @ $178.43
   signal conf=0.82 reason=momentum+vol
   notional: $356.86
```

### 6. Sell manually

In your Telegram chat with the bot:

```
/status
/sell AAPL 1
/panic
```

## Files

- `broker/state.py` — SQLite ledger (signals, decisions, trades)
- `broker/sizer.py` — position-sizing rules
- `broker/interface.py` — Broker protocol + FakeBroker + AlpacaPaperBroker
- `bot/signal_watcher.py` — the auto-buy loop (idempotent)
- `bot/poller.py` — TimescaleDB polling loop
- `bot/telegram_bot.py` — Telegram command handlers
- `bot/smoke.py` — meaningful workload (200 signals, 4 scenarios, asserts)

## Smoke test

```bash
make smoke
```

Feeds 200 synthetic BUY/WATCH signals through the watcher, then
asserts: every signal has a decision, every BUY filled, every WATCH
was skipped, replay is idempotent, manual sell works, ledger balances.

## Configuration (env vars)

| Var | Default | Purpose |
|-----|---------|---------|
| `ALPACA_API_KEY` | (required) | Alpaca paper API key |
| `ALPACA_SECRET_KEY` | (required) | Alpaca paper secret |
| `TELEGRAM_BOT_TOKEN` | (required) | Telegram bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | (required) | Your personal chat id |
| `TIMESCALEDB_DSN` | `host=localhost port=5432 dbname=stocks user=stocks password=stocks` | TimescaleDB connection string |
| `TRADING_BOT_NOTIONAL` | `200.0` | Dollar size per trade |
| `TRADING_BOT_MAX_POS_PCT` | `0.20` | Max % of cash in one position |

## Tuning

Edit `notional_per_trade` and `max_position_pct` in `bot/signal_watcher.py`,
or set the env vars above.

## License

MIT. No warranty. Not financial advice.
