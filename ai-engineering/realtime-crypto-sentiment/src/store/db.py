"""SQLAlchemy engine + schema bootstrap + CRUD helpers.

Author: Prem Vishnoi <pvishnoi@avilx.com>

Compatible with both Postgres (TimescaleDB hypertables) and SQLite
(used by the integration test). The schema.sql file is Postgres-only
and is not applied under SQLite; the integration test uses the
`ensure_sqlite_schema()` helper below.
"""
from __future__ import annotations

import json
import pathlib
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterable, List, Optional

from loguru import logger
from sqlalchemy import (
    Column, DateTime, Float, Integer, String, Text, BigInteger, create_engine,
    text, Index,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert, JSONB
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config import settings

HERE = pathlib.Path(__file__).resolve().parent

# ── Engine / Session ────────────────────────────────────────────────────

def _make_engine(url: Optional[str] = None):
    url = url or settings.database_url
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=10)


_engine = None
_SessionLocal = None


def get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        _engine = _make_engine()
        _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine


def override_engine(url: str):
    """Test hook: swap in a different engine (e.g. sqlite:///:memory:)."""
    global _engine, _SessionLocal
    _engine = _make_engine(url)
    _SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine


@contextmanager
def session_scope():
    s = get_engine().connect()
    try:
        yield s
    finally:
        s.close()


# ── ORM (for SQLite integration tests; PG uses raw SQL via schema.sql) ─

Base = declarative_base()


class Tweet(Base):
    __tablename__ = "tweets"
    ts = Column(DateTime, primary_key=True)
    tweet_id = Column(BigInteger, primary_key=True)
    symbol = Column(String, nullable=False, index=True)
    text = Column(Text, nullable=False)
    author = Column(String, nullable=False)
    likes = Column(Integer, default=0)
    retweets = Column(Integer, default=0)
    followers = Column(Integer, default=0)
    url = Column(Text, nullable=False)
    source_adapter = Column(String, nullable=False)
    sentiment_score = Column(Float, nullable=True)
    raw_json = Column(Text, nullable=True)  # JSON-stringified for sqlite


class Price(Base):
    __tablename__ = "prices"
    ts = Column(DateTime, primary_key=True)
    symbol = Column(String, primary_key=True)
    price_usd = Column(Float, nullable=False)
    volume_usd = Column(Float, default=0.0)


class Signal(Base):
    __tablename__ = "signals"
    ts = Column(DateTime, primary_key=True)
    symbol = Column(String, primary_key=True)
    action = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    sentiment_zscore = Column(Float, nullable=False)
    momentum_zscore = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)


class Position(Base):
    __tablename__ = "positions"
    ts = Column(DateTime, primary_key=True)
    symbol = Column(String, primary_key=True)
    qty = Column(Float, nullable=False)
    avg_price = Column(Float, nullable=False)
    realized_pnl = Column(Float, default=0.0)


class PaperTrade(Base):
    __tablename__ = "paper_trades"
    ts = Column(DateTime, primary_key=True)
    symbol = Column(String, primary_key=True)
    side = Column(String, nullable=False)
    qty = Column(Float, nullable=False)
    price_usd = Column(Float, nullable=False)
    fee_usd = Column(Float, nullable=False)
    cash_after = Column(Float, nullable=False)
    reason = Column(Text, nullable=True)


# ── Schema bootstrap ────────────────────────────────────────────────────

# Resolve once: src/store/ → project root
PROJECT_ROOT = HERE.resolve().parents[1]
VIEWS_SQL_PATH = PROJECT_ROOT / "db" / "02_views.sql"


def init_schema() -> None:
    """Apply TimescaleDB schema + continuous aggregates + views.

    Safe to call repeatedly (uses IF NOT EXISTS / OR REPLACE).
    Raises on any read/exec error so the pipeline can fail-fast at boot.
    """
    engine = get_engine()
    if engine.dialect.name == "postgresql":
        schema_sql = (HERE / "schema.sql").read_text()
        if not VIEWS_SQL_PATH.exists():
            raise FileNotFoundError(
                f"expected views SQL at {VIEWS_SQL_PATH}; did you forget to git pull?"
            )
        views_sql = VIEWS_SQL_PATH.read_text()
        aggregates_sql = (HERE / "aggregates.sql").read_text()
        with engine.begin() as conn:
            conn.execute(text(schema_sql))
            conn.execute(text(views_sql))
            conn.execute(text(aggregates_sql))
        logger.info("TimescaleDB schema applied (hypertables + views + aggregates)")
    else:
        Base.metadata.create_all(engine)
        logger.info("SQLite schema applied (test mode)")


def ensure_sqlite_schema() -> None:
    """For tests: force the SQLite schema on the current engine."""
    Base.metadata.create_all(get_engine())


# ── CRUD helpers ────────────────────────────────────────────────────────

def upsert_tweet(t: dict) -> bool:
    """Insert a tweet, no-op on duplicate (tweet_id, ts).

    Returns True if a new row was inserted, False on conflict.
    """
    engine = get_engine()
    raw = t.get("raw_json")
    if raw is not None and not isinstance(raw, str):
        raw = json.dumps(raw, default=str)
    row = {
        "ts": t["ts"],
        "tweet_id": t["tweet_id"],
        "symbol": t["symbol"],
        "text": t["text"],
        "author": t["author"],
        "likes": int(t.get("likes", 0)),
        "retweets": int(t.get("retweets", 0)),
        "followers": int(t.get("followers", 0)),
        "url": t["url"],
        "source_adapter": t["source_adapter"],
        "sentiment_score": t.get("sentiment_score"),
        "raw_json": raw,
    }
    with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            stmt = pg_insert(Tweet.__table__).values(**row)
            stmt = stmt.on_conflict_do_nothing(index_elements=["tweet_id", "ts"])
            result = conn.execute(stmt)
            return result.rowcount > 0
        else:
            existing = conn.execute(
                text("SELECT 1 FROM tweets WHERE tweet_id=:id AND ts=:ts"),
                {"id": row["tweet_id"], "ts": row["ts"]},
            ).fetchone()
            if existing:
                return False
            conn.execute(Tweet.__table__.insert().values(**row))
            return True


def bulk_upsert_tweets(tweets: Iterable[dict]) -> int:
    """Insert many tweets. Returns count of newly inserted rows."""
    return sum(1 for t in tweets if upsert_tweet(t))


def update_tweet_sentiment(tweet_id: int, ts, score: float) -> int:
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text(
                "UPDATE tweets SET sentiment_score=:s "
                "WHERE tweet_id=:id AND ts=:ts"
            ),
            {"s": score, "id": tweet_id, "ts": ts},
        )
        return result.rowcount


def fetch_unscored_tweets(limit: int = 256) -> List[dict]:
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT ts, tweet_id, text, symbol FROM tweets "
                "WHERE sentiment_score IS NULL "
                "ORDER BY ts ASC LIMIT :lim"
            ),
            {"lim": limit},
        ).fetchall()
    return [dict(r._mapping) for r in rows]


def upsert_price(p: dict) -> None:
    """Idempotent insert (ts, symbol). On conflict, update price+volume."""
    engine = get_engine()
    row = {
        "ts": p["ts"],
        "symbol": p["symbol"],
        "price_usd": p["price_usd"],
        "volume_usd": float(p.get("volume_usd", 0.0)),
    }
    with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            stmt = pg_insert(Price.__table__).values(**row)
            stmt = stmt.on_conflict_do_update(
                index_elements=["ts", "symbol"],
                set_={"price_usd": stmt.excluded.price_usd, "volume_usd": stmt.excluded.volume_usd},
            )
            conn.execute(stmt)
        else:
            conn.execute(
                text(
                    "INSERT OR REPLACE INTO prices (ts, symbol, price_usd, volume_usd) "
                    "VALUES (:ts, :symbol, :price_usd, :volume_usd)"
                ),
                row,
            )


def bulk_upsert_prices(prices: Iterable[dict]) -> int:
    n = 0
    for p in prices:
        upsert_price(p)
        n += 1
    return n


def latest_price(symbol: str) -> Optional[dict]:
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT ts, symbol, price_usd, volume_usd FROM prices "
                "WHERE symbol=:s ORDER BY ts DESC LIMIT 1"
            ),
            {"s": symbol},
        ).fetchone()
    return dict(row._mapping) if row else None


def insert_signal(s: dict) -> None:
    engine = get_engine()
    row = {
        "ts": s["ts"],
        "symbol": s["symbol"],
        "action": s["action"],
        "score": s["score"],
        "sentiment_zscore": s["sentiment_zscore"],
        "momentum_zscore": s["momentum_zscore"],
        "reason": s["reason"],
    }
    with engine.begin() as conn:
        conn.execute(Signal.__table__.insert().values(**row))


def fetch_recent_signals(symbol: str, hours: int = 24, limit: int = 200) -> List[dict]:
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT ts, symbol, action, score, sentiment_zscore, momentum_zscore, reason "
                "FROM signals "
                "WHERE symbol=:s AND ts > NOW() - (:h || ' hours')::INTERVAL "
                "ORDER BY ts DESC LIMIT :lim"
                if engine.dialect.name == "postgresql"
                else
                "SELECT ts, symbol, action, score, sentiment_zscore, momentum_zscore, reason "
                "FROM signals "
                "WHERE symbol=:s AND ts > datetime('now', :h) "
                "ORDER BY ts DESC LIMIT :lim"
            ),
            {"s": symbol, "h": f"-{hours} hours", "lim": limit},
        ).fetchall()
    return [dict(r._mapping) for r in rows]


def fetch_recent_tweets(symbol: str, minutes: int = 5) -> List[dict]:
    engine = get_engine()
    with engine.connect() as conn:
        if engine.dialect.name == "postgresql":
            rows = conn.execute(
                text(
                    "SELECT ts, tweet_id, text, author, sentiment_score "
                    "FROM tweets "
                    "WHERE symbol=:s AND ts > NOW() - (:m || ' minutes')::INTERVAL "
                    "ORDER BY ts ASC"
                ),
                {"s": symbol, "m": str(minutes)},
            ).fetchall()
        else:
            rows = conn.execute(
                text(
                    "SELECT ts, tweet_id, text, author, sentiment_score FROM tweets "
                    "WHERE symbol=:s AND ts > datetime('now', :m) ORDER BY ts ASC"
                ),
                {"s": symbol, "m": f"-{minutes} minutes"},
            ).fetchall()
    return [dict(r._mapping) for r in rows]


def recent_price_returns(symbol: str, minutes: int = 5) -> List[float]:
    """Return the per-minute price-returns for the last `minutes`.

    Returns: list of (price_now - price_then) / price_then for each minute.
    """
    engine = get_engine()
    with engine.connect() as conn:
        if engine.dialect.name == "postgresql":
            rows = conn.execute(
                text(
                    "SELECT bucket, close FROM prices_1m "
                    "WHERE symbol=:s AND bucket > NOW() - (:m || ' minutes')::INTERVAL "
                    "ORDER BY bucket ASC"
                ),
                {"s": symbol, "m": str(minutes + 1)},
            ).fetchall()
        else:
            rows = conn.execute(
                text(
                    "SELECT ts AS bucket, price_usd AS close FROM prices "
                    "WHERE symbol=:s AND ts > datetime('now', :m) ORDER BY ts ASC"
                ),
                {"s": symbol, "m": f"-{minutes + 1} minutes"},
            ).fetchall()
    closes = [float(r._mapping["close"]) for r in rows]
    if len(closes) < 2:
        return []
    return [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))]


def sentiment_buckets(symbol: str, minutes: int = 5, hours: int = 24) -> List[dict]:
    """Return list of {bucket, avg_sentiment, n} aggregated to `minutes`-wide buckets.

    Used by signal generation so the z-score compares a current 5-min mean
    against a history of *bucket means*, not against the noisy per-tweet
    distribution.
    """
    engine = get_engine()
    total_minutes = hours * 60
    with engine.connect() as conn:
        if engine.dialect.name == "postgresql":
            rows = conn.execute(
                text(
                    f"SELECT time_bucket('{minutes} minutes', ts) AS bucket, "
                    f"AVG(sentiment_score) AS avg_sent, COUNT(*) AS n "
                    f"FROM tweets "
                    f"WHERE symbol=:s AND sentiment_score IS NOT NULL "
                    f"AND ts > NOW() - (:m || ' minutes')::INTERVAL "
                    f"GROUP BY bucket ORDER BY bucket ASC"
                ),
                {"s": symbol, "m": str(total_minutes)},
            ).fetchall()
        else:
            # SQLite: use strftime to round down to the nearest 5-min boundary.
            # 5-minute boundaries: 00, 05, 10, ..., 55. Divide by 300 seconds and floor.
            seconds = minutes * 60
            rows = conn.execute(
                text(
                    "SELECT CAST((strftime('%s', ts) / :sec) * :sec AS INTEGER) AS bucket, "
                    "AVG(sentiment_score) AS avg_sent, COUNT(*) AS n "
                    "FROM tweets "
                    "WHERE symbol=:s AND sentiment_score IS NOT NULL "
                    "AND ts > datetime('now', :m) "
                    "GROUP BY bucket ORDER BY bucket ASC"
                ),
                {"s": symbol, "m": f"-{total_minutes} minutes", "sec": seconds},
            ).fetchall()
    return [dict(r._mapping) for r in rows]


def insert_paper_trade(t: dict) -> None:
    engine = get_engine()
    row = {
        "ts": t["ts"],
        "symbol": t["symbol"],
        "side": t["side"],
        "qty": t["qty"],
        "price_usd": t["price_usd"],
        "fee_usd": t["fee_usd"],
        "cash_after": t["cash_after"],
        "reason": t.get("reason"),
    }
    with engine.begin() as conn:
        conn.execute(PaperTrade.__table__.insert().values(**row))


def fetch_paper_trades(limit: int = 200) -> List[dict]:
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT ts, symbol, side, qty, price_usd, fee_usd, cash_after, reason "
                "FROM paper_trades ORDER BY ts DESC LIMIT :lim"
            ),
            {"lim": limit},
        ).fetchall()
    return [dict(r._mapping) for r in rows]


def upsert_position(p: dict) -> None:
    """Record a position snapshot (overwrite by symbol)."""
    engine = get_engine()
    row = {
        "ts": p["ts"],
        "symbol": p["symbol"],
        "qty": p["qty"],
        "avg_price": p["avg_price"],
        "realized_pnl": float(p.get("realized_pnl", 0.0)),
    }
    with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            stmt = pg_insert(Position.__table__).values(**row)
            stmt = stmt.on_conflict_do_update(
                index_elements=["ts", "symbol"],
                set_={
                    "qty": stmt.excluded.qty,
                    "avg_price": stmt.excluded.avg_price,
                    "realized_pnl": stmt.excluded.realized_pnl,
                },
            )
            conn.execute(stmt)
        else:
            conn.execute(
                text(
                    "INSERT OR REPLACE INTO positions (ts, symbol, qty, avg_price, realized_pnl) "
                    "VALUES (:ts, :symbol, :qty, :avg_price, :realized_pnl)"
                ),
                row,
            )


def all_open_positions() -> List[dict]:
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT DISTINCT ON (symbol) ts, symbol, qty, avg_price, realized_pnl "
                "FROM positions WHERE qty > 0 ORDER BY symbol, ts DESC"
                if engine.dialect.name == "postgresql"
                else
                "SELECT ts, symbol, qty, avg_price, realized_pnl FROM positions "
                "WHERE qty > 0 AND ts IN (SELECT MAX(ts) FROM positions GROUP BY symbol) "
                "ORDER BY symbol"
            )
        ).fetchall()
    return [dict(r._mapping) for r in rows]
