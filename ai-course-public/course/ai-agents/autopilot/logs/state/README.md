# `state/` — watchdog state files

This directory is the **scratch space** for `run_autopilot.sh`'s crash-recovery
state.  Each iteration writes two small files here:

| File | Purpose |
|---|---|
| `restart_count` | Number of consecutive restarts in the current 10-min window.  When this hits `MAX_RESTARTS` (default 5), the watchdog gives up and exits. |
| `last_start_ts` | The unix-epoch timestamp of the most recent iteration start.  Used to detect a stale crash loop. |

The state files are intentionally tiny and human-readable so a developer can
`cat restart_count` from another shell to see how many restarts the watchdog
has already done.

This directory is normally **empty** at rest: each iteration cleans up the
state files when the run completes successfully.  Files appear here **only
when the watchdog is mid-crash-loop** (between a failed iter and the next
restart attempt).

If you see non-empty contents and the autopilot is not running, it's safe
to `rm restart_count last_start_ts` to clear stale state before relaunching.
