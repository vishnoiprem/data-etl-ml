"""Signal UDF -- computes a buy / watch / hold signal from rolling features.

The math (per the design plan):

    intraday_return_5m = (price - close_5m_ago) / close_5m_ago
    range_pct          = (day_high - day_low) / day_low
    hours_remaining    = market_close - now   (US market closes 16:00 ET)
    expected_move_pct  = range_pct * sqrt(hours_remaining / 6.5)

BUY iff all of:
    1. price <= day_low * 1.01                          # near day low
    2. momentum_5m > 0                                  # upward momentum
    3. expected_move_pct >= 0.04                        # enough room
    4. composite confidence >= 0.6

WATCH: conditions 1 & 2 met but expected move or time insufficient.
HOLD:  anything else.

The UDF is registered as `TSignalUDF` for SQL access from
``flink/jobs/04_signals.sql``. The cluster ships this file via
``python.files`` (mounted at /opt/flink/udf/signal_udf.py) and the
sql-client startup script imports it before running the SQL.
"""
from pyflink.table import DataTypes
from pyflink.table.udf import udf
import math


@udf(
    result_type=DataTypes.ROW([
        DataTypes.FIELD("action",           DataTypes.STRING()),
        DataTypes.FIELD("target_price",     DataTypes.DOUBLE()),
        DataTypes.FIELD("expected_move_pct", DataTypes.DOUBLE()),
        DataTypes.FIELD("confidence",       DataTypes.DOUBLE()),
        DataTypes.FIELD("reasons",          DataTypes.STRING()),
    ])
)
def compute_signal(price, day_high, day_low, prev_close,
                   momentum_5m, vol_15m, hhmm):
    """Return a ROW<action, target_price, expected_move_pct, confidence, reasons>.

    Parameters mirror the call site in 04_signals.sql:
        price, day_high, day_low, prev_close, momentum_5m, vol_15m, hhmm
    """
    try:
        # Null-safe defaults -- Flink may pass None on first tick of a window.
        price        = float(price        or 0)
        day_high     = float(day_high     or price)
        day_low      = float(day_low      or price)
        prev_close   = float(prev_close   or price)
        momentum_5m  = float(momentum_5m  or 0.0)
        vol_15m      = float(vol_15m      or 0.0)

        if price <= 0 or day_low <= 0:
            return ("HOLD", 0.0, 0.0, 0.0, "invalid_price")

        # 4% upside target relative to current price.
        target_price = price * 1.04

        # Intraday range as a fraction of the day's low.
        range_pct = (day_high - day_low) / day_low

        # Decode HHMM (int, e.g. 1415 for 14:15) into hours remaining in the
        # US trading session (closes 16:00 ET). We treat the UDF clock as the
        # local market time -- in production this should be wired from a
        # properly zoned wallclock source rather than CURRENT_TIMESTAMP on the
        # job manager.
        hhmm_int = int(hhmm or 0)
        hour     = hhmm_int // 100
        minute   = hhmm_int % 100
        now_minutes    = hour * 60 + minute
        close_minutes  = 16 * 60   # 16:00 ET
        hours_remaining = max(0.0, (close_minutes - now_minutes) / 60.0)

        # Expected move scales with sqrt of remaining session fraction.
        expected_move_pct = (
            range_pct * math.sqrt(hours_remaining / 6.5)
            if hours_remaining > 0 else 0.0
        )

        # Boolean conditions.
        cond_near_low   = price <= day_low * 1.01
        cond_momentum   = momentum_5m > 0
        cond_vol_enough = expected_move_pct >= 0.04
        cond_have_time  = hours_remaining >= 0.5  # at least 30 min left

        # Composite confidence:
        #   0.30 weight on "near day low"
        #   0.30 weight on "momentum" -- capped at 2% return -> full credit
        #   0.25 weight on expected move -- capped at 6% -> full credit
        #   0.15 weight on time-remaining -- 30+ min -> full credit
        conf  = 0.30 * (1.0 if cond_near_low else 0.0)
        if momentum_5m > 0:
            conf += 0.30 * min(1.0, momentum_5m / 0.02)
        conf += 0.25 * min(1.0, expected_move_pct / 0.06)
        conf += 0.15 * (1.0 if cond_have_time else hours_remaining / 0.5)

        if cond_near_low and cond_momentum and cond_vol_enough and conf >= 0.6:
            action  = "BUY"
            reasons = "near_day_low;positive_momentum;vol_above_4pct_target"
        elif cond_near_low and cond_momentum:
            action  = "WATCH"
            reasons = "near_low_and_momentum;low_vol_or_insufficient_time"
        else:
            action  = "HOLD"
            reasons = "no_signal"

        return (action, target_price, expected_move_pct, float(conf), reasons)
    except Exception as e:
        # Never let the UDF crash the streaming job -- degrade to HOLD.
        return ("HOLD", 0.0, 0.0, 0.0, f"error: {e}")


# Register under the SQL name TSignalUDF. The sql-client startup script
# imports this module and calls add_python_function; renaming the attribute
# here is what the runtime looks up.
compute_signal.name = "TSignalUDF"
