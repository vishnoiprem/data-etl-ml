from datetime import datetime, timedelta, timezone

from pipeline_logic import partition_for_date

# A simple exponential-backoff retry simulator.
def simulate_retries(attempts_allowed, failures, delay_base=timedelta(minutes=5), max_delay=timedelta(hours=1)):
    """Simulate a retry policy with exponential backoff.

    Args:
        attempts_allowed: Total attempts (1 means no retries).
        failures: How many attempts fail before one succeeds.
        delay_base: The first retry delay.
        max_delay: The cap on the retry delay.

    Returns:
        A dict describing the outcome.
    """
    attempt = 0
    waits = []
    while attempt < attempts_allowed:
        attempt += 1
        if attempt > failures:
            break
        delay = min(delay_base * (2 ** (attempt - 1)), max_delay)
        waits.append(delay)
    return {
        "attempts_used": attempt,
        "succeeded": attempt > failures,
        "waits": waits,
        "total_wait": sum(waits, timedelta()),
    }


for failures in (0, 1, 2, 3):
    result = simulate_retries(attempts_allowed=3, failures=failures)
    print(
        f"{failures} transient failure(s): attempts={result['attempts_used']} "
        f"succeeded={result['succeeded']} total_wait={result['total_wait']}"
    )

print()
print("With retries=2 (3 attempts) and backoff from 5 minutes:")
print("  worst-case wait before the final attempt:", simulate_retries(3, 2)["total_wait"])
print("  a permanent failure costs the full budget every time")
print("  -> validate before you write, so permanent errors fail fast.")
