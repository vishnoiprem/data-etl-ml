"""SQLAlchemy engine + schema bootstrap + CRUD helpers.

Author: Prem Vishnoi <pvishnoi@avilx.com>

Compatible with both Postgres (TimescaleDB hypertables) and SQLite
(used by the integration test). The schema.sql file is Postgres-only
and is not applied under SQLite; the integration test uses the
`ensure_sqlite_schema()` helper below.

Currency note: there is no real money in this system. The paper-
trading broker uses synthetic "unit prices" derived from tweet
engagement, so all monetary fields are unitless (price, fee, cash)
rather than USD.
"""
from __future__ import annotations

import json
import pathlib
from collections.abc import Iterable
from contextlib import contextmanager

from loguru import logger
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import declarative_base, sessionmaker

from src.config import settings

HERE = pathlib.Path(__file__).resolve().parent

# ── Engine / Session ────────────────────────────────────────────────────

def _make_engine(url: str | None = None):
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


class Signal(Base):
    __tablename__ = "signals"
    ts = Column(DateTime, primary_key=True)
    symbol = Column(String, primary_key=True)
    action = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    sentiment_zscore = Column(Float, nullable=False)
    momentum_zscore = Column(Float, nullable=False)  # always 0; kept for back-compat
    reason = Column(Text, nullable=False)


class Position(Base):
    __tablename__ = "positions"
    ts = Column(DateTime, primary_key=True)
    symbol = Column(String, primary_key=True)
    qty = Column(Float, nullable=False)
    avg_price = Column(Float, nullable=False)  # synthetic unit price
    realized_pnl = Column(Float, default=0.0)


class PaperTrade(Base):
    __tablename__ = "paper_trades"
    ts = Column(DateTime, primary_key=True)
    symbol = Column(String, primary_key=True)
    side = Column(String, nullable=False)
    qty = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    fee = Column(Float, nullable=False)
    cash_after = Column(Float, nullable=False)
    reason = Column(Text, nullable=True)


class TrendingTag(Base):
    __tablename__ = "trending_tags"
    ts = Column(DateTime, primary_key=True)
    bucket = Column(DateTime, primary_key=True)
    tag = Column(String, primary_key=True)
    tag_kind = Column(String, nullable=False)
    count = Column(Integer, default=0)
    avg_sentiment = Column(Float, nullable=True)
    sample_text = Column(Text, nullable=True)
    sample_url = Column(Text, nullable=True)


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
        "ts": _to_naive_utc(t["ts"]),
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
            # SQLite: SELECT-then-INSERT can race; the WHERE ts=:ts check
            # also has a string-mismatch problem when Python round-trips
            # microsecond-precision datetimes. Catch IntegrityError on the
            # INSERT as the source of truth for the dedup decision.
            try:
                conn.execute(Tweet.__table__.insert().values(**row))
                return True
            except IntegrityError:
                return False


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
            {"s": score, "id": tweet_id, "ts": _to_naive_utc(ts)},
        )
        if result.rowcount > 0:
            return result.rowcount
        # Fallback: SQLite string-compare on the WHERE ts=:ts clause can
        # silently miss the row even though it exists (microsecond
        # formatting mismatch). Re-match by tweet_id and verify the ts
        # is within 1 second of the requested ts — that's tight enough
        # to avoid clobbering a different tweet with the same id.
        if engine.dialect.name == "postgresql":
            return 0
        result = conn.execute(
            text(
                "UPDATE tweets SET sentiment_score=:s "
                "WHERE tweet_id=:id AND ABS(strftime('%s', ts) - strftime('%s', :ts)) < 1"
            ),
            {"s": score, "id": tweet_id, "ts": ts},
        )
        return result.rowcount


def fetch_unscored_tweets(limit: int = 256) -> list[dict]:
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


def _to_naive_utc(ts):
    """Coerce a tz-aware datetime to a naive UTC datetime.

    SQLAlchemy's SQLite DateTime type rejects tz-aware datetimes on
    insert. Postgres tolerates either, so we normalize at the
    store-boundary so the same code path works on both backends.

    Accepts:
      - datetime (tz-aware or naive)
      - pandas.Timestamp
      - ISO-8601 string (e.g. from a raw SQL roundtrip via SQLite)
    """
    if ts is None:
        return None
    # pandas.Timestamp
    if hasattr(ts, "to_pydatetime"):
        ts = ts.to_pydatetime()
    # String (SQLite SELECT returns datetimes as text)
    elif isinstance(ts, str):
        from datetime import datetime as _dt
        try:
            ts = _dt.fromisoformat(ts)
        except ValueError:
            # Some drivers emit "YYYY-MM-DD HH:MM:SS.ffffff" (no T).
            ts = _dt.strptime(ts.split(".")[0], "%Y-%m-%d %H:%M:%S")
    if ts.tzinfo is not None:
        from datetime import UTC
        ts = ts.astimezone(UTC).replace(tzinfo=None)
    return ts


def insert_signal(s: dict) -> None:
    engine = get_engine()
    row = {
        "ts": _to_naive_utc(s["ts"]),
        "symbol": s["symbol"],
        "action": s["action"],
        "score": s["score"],
        "sentiment_zscore": s["sentiment_zscore"],
        # momentum_zscore is kept in the schema (back-compat) but always 0
        # now that prices are gone.
        "momentum_zscore": s.get("momentum_zscore", 0.0),
        "reason": s["reason"],
    }
    with engine.begin() as conn:
        conn.execute(Signal.__table__.insert().values(**row))


def fetch_recent_signals(symbol: str, hours: int = 24, limit: int = 200) -> list[dict]:
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


def fetch_recent_tweets(symbol: str, minutes: int = 5) -> list[dict]:
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


def sentiment_buckets(symbol: str, minutes: int = 5, hours: int = 24) -> list[dict]:
    """Return list of {bucket, avg_sentiment, n} aggregated to `minutes`-wide buckets.

    Used by signal generation so the z-score compares a current 5-min mean
    against a history of *bucket means*, not against the noisy per-tweet
    distribution.

    NOTE: `minutes` is intentionally interpolated into the Postgres
    `time_bucket(...)` string because the function requires a literal
    interval. Callers must pass an int (this is enforced at the type
    level by the function signature; no user input is ever passed here).
    """
    engine = get_engine()
    total_minutes = hours * 60
    if engine.dialect.name == "postgresql":
        # Defensive: hard-cap to keep a typo from producing a giant query.
        # Postgres time_bucket accepts integer minutes up to ~35791394
        # (about 68 years); 1 day = 1440 is the realistic ceiling.
        if not (1 <= int(minutes) <= 1440 * 30):
            raise ValueError(f"minutes out of safe range: {minutes!r}")
    with engine.connect() as conn:
        if engine.dialect.name == "postgresql":
            rows = conn.execute(
                text(
                    "SELECT time_bucket(:bucket_width, ts) AS bucket, "
                    "AVG(sentiment_score) AS avg_sent, COUNT(*) AS n "
                    "FROM tweets "
                    "WHERE symbol=:s AND sentiment_score IS NOT NULL "
                    "AND ts > NOW() - (:m || ' minutes')::INTERVAL "
                    "GROUP BY bucket ORDER BY bucket ASC"
                ),
                {"bucket_width": f"{minutes} minutes", "s": symbol,
                 "m": str(total_minutes)},
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


def _validate_bucket_minutes(minutes: int) -> int:
    """Sanity-check a `minutes` bucket width before we interpolate it
    into the `time_bucket(:w, ts)` SQL. Bounds:
      - >= 1: a 0-width bucket is meaningless
      - <= 1440*30 (≈30 days): anything larger is a typo
    """
    minutes = int(minutes)
    if not 1 <= minutes <= 1440 * 30:
        raise ValueError(f"bucket minutes out of safe range [1, {1440*30}]: {minutes!r}")
    return minutes


def global_sentiment_buckets(minutes: int, hours: int) -> list[dict]:
    """Cross-tag sentiment aggregation: one row per `minutes`-wide bucket,
    averaged across ALL symbols. Used by the 'Live' tab to chart the
    macro hourly / daily sentiment trend.

    Returns: list of {bucket, avg_sent, n, pos_n, neg_n}.

    Note: we deliberately do NOT use the `tweets_1h` / `tweets_1d`
    continuous aggregates here, because the pre-aggregates don't
    track the positive/negative breakdown this function returns.
    The per-symbol helper `per_symbol_buckets` does use the
    pre-aggregates for the same reason `time_bucket(:w, ts)` is
    fine when no pos/neg split is needed.
    """
    minutes = _validate_bucket_minutes(minutes)
    engine = get_engine()
    total_minutes = hours * 60
    with engine.connect() as conn:
        if engine.dialect.name == "postgresql":
            rows = conn.execute(
                text(
                    "SELECT time_bucket(:bucket_width, ts) AS bucket, "
                    "AVG(sentiment_score) AS avg_sent, COUNT(*) AS n, "
                    "SUM(CASE WHEN sentiment_score > 0 THEN 1 ELSE 0 END) AS pos_n, "
                    "SUM(CASE WHEN sentiment_score < 0 THEN 1 ELSE 0 END) AS neg_n "
                    "FROM tweets "
                    "WHERE sentiment_score IS NOT NULL "
                    "AND ts > NOW() - (:m || ' minutes')::INTERVAL "
                    "GROUP BY bucket ORDER BY bucket ASC"
                ),
                {"bucket_width": f"{minutes} minutes",
                 "m": str(total_minutes)},
            ).fetchall()
        else:
            seconds = minutes * 60
            rows = conn.execute(
                text(
                    "SELECT CAST((strftime('%s', ts) / :sec) * :sec AS INTEGER) AS bucket, "
                    "AVG(sentiment_score) AS avg_sent, COUNT(*) AS n, "
                    "SUM(CASE WHEN sentiment_score > 0 THEN 1 ELSE 0 END) AS pos_n, "
                    "SUM(CASE WHEN sentiment_score < 0 THEN 1 ELSE 0 END) AS neg_n "
                    "FROM tweets "
                    "WHERE sentiment_score IS NOT NULL "
                    "AND ts > datetime('now', :m) "
                    "GROUP BY bucket ORDER BY bucket ASC"
                ),
                {"m": f"-{total_minutes} minutes", "sec": seconds},
            ).fetchall()
    return [dict(r._mapping) for r in rows]


def per_symbol_buckets(minutes: int, hours: int) -> list[dict]:
    """Cross-tag bucketed sentiment, but broken out per symbol so the
    'Live' tab can show per-tag hourly/daily lines on one chart.

    Returns: list of {bucket, symbol, avg_sent, n}.

    On Postgres, when the requested width matches a pre-aggregated
    continuous aggregate (60min → tweets_1h, 1day → tweets_1d) we
    read from the aggregate table instead of scanning `tweets` —
    these tables are kept up to date by a 15-min/1-hour refresh
    policy and are dramatically faster on a 90-day-retention
    hypertable. Other widths (5 min, 15 min, etc.) still scan
    `tweets` directly.
    """
    minutes = _validate_bucket_minutes(minutes)
    engine = get_engine()
    total_minutes = hours * 60
    with engine.connect() as conn:
        if engine.dialect.name == "postgresql":
            # Fast-path: read from the pre-aggregated continuous
            # aggregate when the requested bucket width is exactly 1h
            # or 1d. The aggregates only carry avg_sentiment + counts
            # (no pos/neg breakdown) which is fine for per-symbol
            # line charts.
            agg_table = _agg_table_for_minutes(minutes)
            if agg_table is not None:
                rows = conn.execute(
                    text(
                        f"SELECT bucket, symbol, avg_sentiment AS avg_sent, "
                        f"tweet_count AS n "
                        f"FROM {agg_table} "
                        f"WHERE bucket > NOW() - (:m || ' minutes')::INTERVAL "
                        f"ORDER BY bucket ASC"
                    ),
                    {"m": str(total_minutes)},
                ).fetchall()
            else:
                rows = conn.execute(
                    text(
                        "SELECT time_bucket(:bucket_width, ts) AS bucket, "
                        "symbol, AVG(sentiment_score) AS avg_sent, COUNT(*) AS n "
                        "FROM tweets "
                        "WHERE sentiment_score IS NOT NULL "
                        "AND ts > NOW() - (:m || ' minutes')::INTERVAL "
                        "GROUP BY bucket, symbol ORDER BY bucket ASC"
                    ),
                    {"bucket_width": f"{minutes} minutes",
                     "m": str(total_minutes)},
                ).fetchall()
        else:
            seconds = minutes * 60
            rows = conn.execute(
                text(
                    "SELECT CAST((strftime('%s', ts) / :sec) * :sec AS INTEGER) AS bucket, "
                    "symbol, AVG(sentiment_score) AS avg_sent, COUNT(*) AS n "
                    "FROM tweets "
                    "WHERE sentiment_score IS NOT NULL "
                    "AND ts > datetime('now', :m) "
                    "GROUP BY bucket, symbol ORDER BY bucket ASC"
                ),
                {"m": f"-{total_minutes} minutes", "sec": seconds},
            ).fetchall()
    return [dict(r._mapping) for r in rows]


def _agg_table_for_minutes(minutes: int) -> str | None:
    """Map a bucket width in minutes to a TimescaleDB continuous
    aggregate table that pre-computes that exact width. Returns None
    when no pre-aggregate matches (callers should fall back to a
    live `time_bucket` scan).

    The aggregates are created in `src/store/aggregates.sql`:
        tweets_1h  → 60-min buckets, refreshed every 15 min
        tweets_1d  → 1-day buckets, refreshed every 1 hour
    """
    if minutes == 60:
        return "tweets_1h"
    if minutes == 60 * 24:
        return "tweets_1d"
    return None


def daily_topic_aggregates(days: int, limit: int = 10) -> list[dict]:
    """Top-N topics (i.e. tracked `symbol`s) aggregated per day for the
    last `days` days. Each row is one (day, symbol) pair with metrics
    suitable for the '📡 Live' tab's 'Top topics by day' panel:

        day, symbol, tweet_count, unique_authors, total_likes,
        total_retweets, total_reach, avg_sentiment, pos_count,
        neg_count, velocity

    `velocity` = (today's tweet_count) - (yesterday's tweet_count) for
    the same symbol. Positive = trending up, negative = cooling.

    `total_reach` = SUM(followers) — proxy for "how many eyeballs saw
    this topic today" (real impressions are unavailable without the
    X.com API).
    """
    engine = get_engine()
    with engine.connect() as conn:
        if engine.dialect.name == "postgresql":
            rows = conn.execute(
                text(
                    "SELECT DATE_TRUNC('day', ts) AS day, "
                    "symbol, COUNT(*) AS tweet_count, "
                    "COUNT(DISTINCT author) AS unique_authors, "
                    "COALESCE(SUM(likes), 0) AS total_likes, "
                    "COALESCE(SUM(retweets), 0) AS total_retweets, "
                    "COALESCE(SUM(followers), 0) AS total_reach, "
                    "AVG(sentiment_score) AS avg_sentiment, "
                    "SUM(CASE WHEN sentiment_score > 0 THEN 1 ELSE 0 END) AS pos_count, "
                    "SUM(CASE WHEN sentiment_score < 0 THEN 1 ELSE 0 END) AS neg_count "
                    "FROM tweets "
                    "WHERE ts > NOW() - (:d || ' days')::INTERVAL "
                    "GROUP BY day, symbol "
                    "ORDER BY day DESC, tweet_count DESC"
                ),
                {"d": str(days)},
            ).fetchall()
        else:
            # SQLite: epoch-day = strftime('%s', ts) / 86400
            rows = conn.execute(
                text(
                    "SELECT CAST(strftime('%s', ts) / 86400 AS INTEGER) AS day, "
                    "symbol, COUNT(*) AS tweet_count, "
                    "COUNT(DISTINCT author) AS unique_authors, "
                    "COALESCE(SUM(likes), 0) AS total_likes, "
                    "COALESCE(SUM(retweets), 0) AS total_retweets, "
                    "COALESCE(SUM(followers), 0) AS total_reach, "
                    "AVG(sentiment_score) AS avg_sentiment, "
                    "SUM(CASE WHEN sentiment_score > 0 THEN 1 ELSE 0 END) AS pos_count, "
                    "SUM(CASE WHEN sentiment_score < 0 THEN 1 ELSE 0 END) AS neg_count "
                    "FROM tweets "
                    "WHERE ts > datetime('now', :d) "
                    "GROUP BY day, symbol "
                    "ORDER BY day DESC, tweet_count DESC"
                ),
                {"d": f"-{days} days"},
            ).fetchall()
    # Compute velocity in Python (cheaper than another SQL pass).
    # `day` is an integer day-number, so (day, symbol) -> (day-1, symbol)
    # is exactly "yesterday's bucket for the same topic" — no need to
    # worry about month/year rollovers (epoch days are monotonic).
    by_day_symbol: dict[tuple[int, str], dict] = {
        (r._mapping["day"], r._mapping["symbol"]): dict(r._mapping) for r in rows
    }
    for k, row in by_day_symbol.items():
        prev = by_day_symbol.get((k[0] - 1, k[1]))
        row["velocity"] = (row["tweet_count"] - prev["tweet_count"]) if prev else row["tweet_count"]
    # Return the top-N per day (only for the most recent day for "today's top"
    # view; caller can iterate to see all days)
    out = list(by_day_symbol.values())
    out.sort(key=lambda r: (r["day"], r["tweet_count"]), reverse=True)
    return out[: max(limit, 1)]


def insert_paper_trade(t: dict) -> None:
    engine = get_engine()
    row = {
        "ts": _to_naive_utc(t["ts"]),
        "symbol": t["symbol"],
        "side": t["side"],
        "qty": t["qty"],
        "price": t["price"],
        "fee": t["fee"],
        "cash_after": t["cash_after"],
        "reason": t.get("reason"),
    }
    with engine.begin() as conn:
        conn.execute(PaperTrade.__table__.insert().values(**row))


def fetch_paper_trades(limit: int = 200) -> list[dict]:
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT ts, symbol, side, qty, price, fee, cash_after, reason "
                "FROM paper_trades ORDER BY ts DESC LIMIT :lim"
            ),
            {"lim": limit},
        ).fetchall()
    return [dict(r._mapping) for r in rows]


def upsert_position(p: dict) -> None:
    """Record a position snapshot (overwrite by symbol)."""
    engine = get_engine()
    row = {
        "ts": _to_naive_utc(p["ts"]),
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


def all_open_positions() -> list[dict]:
    """Return the latest position snapshot per symbol, filtered to
    `qty > 0` (i.e. currently-open positions only).

    Bug history: the previous version did `WHERE qty > 0 AND ts = MAX(ts)
    GROUP BY symbol`, which returned the latest snapshot with `qty > 0`
    rather than the latest snapshot. A position that was opened then
    closed (qty: 10 → 0) would still show as open because the latest
    `qty > 0` row is the opening fill.
    """
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT ts, symbol, qty, avg_price, realized_pnl FROM ("
                "  SELECT ts, symbol, qty, avg_price, realized_pnl, "
                "         ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY ts DESC) AS rn "
                "  FROM positions"
                ") latest WHERE rn = 1 AND qty > 0 ORDER BY symbol"
                if engine.dialect.name == "postgresql"
                else
                "SELECT ts, symbol, qty, avg_price, realized_pnl FROM positions p1 "
                "WHERE ts = (SELECT MAX(ts) FROM positions p2 WHERE p2.symbol = p1.symbol) "
                "AND qty > 0 ORDER BY symbol"
            )
        ).fetchall()
    return [dict(r._mapping) for r in rows]


# ── trending_tags CRUD ──────────────────────────────────────────────────


def upsert_trending_tag(row: dict) -> None:
    """Insert or update a (bucket, tag) row. count/avg_sentiment/sample
    fields are taken from the latest scrape; we keep the most recent
    sample_text/sample_url so the dashboard can render a representative
    tweet.
    """
    engine = get_engine()
    payload = {
        "ts": row["ts"],
        "bucket": row["bucket"],
        "tag": row["tag"],
        "tag_kind": row["tag_kind"],
        "count": int(row.get("count", 0)),
        "avg_sentiment": row.get("avg_sentiment"),
        "sample_text": row.get("sample_text"),
        "sample_url": row.get("sample_url"),
    }
    with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            stmt = pg_insert(TrendingTag.__table__).values(**payload)
            stmt = stmt.on_conflict_do_update(
                index_elements=["bucket", "tag"],
                set_={
                    "ts": stmt.excluded.ts,
                    "count": stmt.excluded.count,
                    "avg_sentiment": stmt.excluded.avg_sentiment,
                    "sample_text": stmt.excluded.sample_text,
                    "sample_url": stmt.excluded.sample_url,
                },
            )
            conn.execute(stmt)
        else:
            conn.execute(
                text(
                    "INSERT OR REPLACE INTO trending_tags "
                    "(ts, bucket, tag, tag_kind, count, avg_sentiment, sample_text, sample_url) "
                    "VALUES (:ts, :bucket, :tag, :tag_kind, :count, :avg_sentiment, :sample_text, :sample_url)"
                ),
                payload,
            )


def bulk_upsert_trending_tags(rows: Iterable[dict]) -> int:
    """Insert/update many trending tag rows. Returns count processed."""
    n = 0
    for r in rows:
        upsert_trending_tag(r)
        n += 1
    return n


def fetch_trending_tags(minutes: int = 5, limit: int = 50) -> list[dict]:
    """Return the top-N (by count) tags seen in the last `minutes`."""
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                # Aggregate per-tag over the window.
                "SELECT tag, tag_kind, SUM(count) AS total_count, "
                "AVG(avg_sentiment) AS avg_sent, "
                "(SELECT sample_url FROM trending_tags t2 "
                " WHERE t2.tag = t1.tag AND t2.bucket > datetime('now', :m) "
                " ORDER BY t2.bucket DESC LIMIT 1) AS sample_url, "
                "(SELECT sample_text FROM trending_tags t2 "
                " WHERE t2.tag = t1.tag AND t2.bucket > datetime('now', :m) "
                " ORDER BY t2.bucket DESC LIMIT 1) AS sample_text "
                "FROM trending_tags t1 "
                "WHERE bucket > datetime('now', :m) "
                "GROUP BY tag, tag_kind "
                "ORDER BY total_count DESC LIMIT :lim"
                if engine.dialect.name == "sqlite"
                else
                "SELECT tag, tag_kind, SUM(count) AS total_count, "
                "AVG(avg_sentiment) AS avg_sent, "
                # Postgres supports DISTINCT ON to grab the latest sample.
                "(SELECT sample_url FROM trending_tags t2 "
                " WHERE t2.tag = t1.tag AND t2.bucket > NOW() - (:m || ' minutes')::INTERVAL "
                " ORDER BY t2.bucket DESC LIMIT 1) AS sample_url, "
                "(SELECT sample_text FROM trending_tags t2 "
                " WHERE t2.tag = t1.tag AND t2.bucket > NOW() - (:m || ' minutes')::INTERVAL "
                " ORDER BY t2.bucket DESC LIMIT 1) AS sample_text "
                "FROM trending_tags t1 "
                "WHERE bucket > NOW() - (:m || ' minutes')::INTERVAL "
                "GROUP BY tag, tag_kind "
                "ORDER BY total_count DESC LIMIT :lim"
            ),
            # SQLite `datetime('now', '-5 minutes')` requires the modifier as
            # a single string with a unit. Pass `-N minutes` (with the unit
            # baked in) so both dialects can substitute it verbatim.
            {"m": f"-{minutes} minutes" if engine.dialect.name == "sqlite" else str(minutes),
             "lim": limit},
        ).fetchall()
    return [dict(r._mapping) for r in rows]