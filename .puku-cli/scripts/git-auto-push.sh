#!/bin/bash
# git-auto-push.sh — background agent that pushes un-pushed commits.
#
# Triggers:
#   * When /Users/pvishnoi/PycharmProjects/data-etl-ml/.puku-cli/state/git-push-now
#     exists (set by .git/hooks/post-commit).
#   * Every 600 seconds (10 min) as a safety net.
#
# Usage:  bash /Users/pvishnoi/PycharmProjects/data-etl-ml/.puku-cli/scripts/git-auto-push.sh
# Stop:   kill $(cat /Users/pvishnoi/PycharmProjects/data-etl-ml/.puku-cli/state/git-auto-push.pid)
# Logs:   /Users/pvishnoi/PycharmProjects/data-etl-ml/.puku-cli/state/git-auto-push.log

set -u

PROJECT="/Users/pvishnoi/PycharmProjects/data-etl-ml"
STATE_DIR="$PROJECT/.puku-cli/state"
FLAG="$STATE_DIR/git-push-now"
LOG="$STATE_DIR/git-auto-push.log"
PIDFILE="$STATE_DIR/git-auto-push.pid"
REPO="$PROJECT"

mkdir -p "$STATE_DIR"
echo $$ > "$PIDFILE"

ts() { date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(ts)] $*" >> "$LOG"; }

push_repo() {
    local label="$1"
    (
        cd "$REPO" || { log "$label: cannot cd to $REPO"; return 1; }
        if git rev-parse --abbrev-ref HEAD >/dev/null 2>&1; then
            local ahead
            ahead=$(git rev-list --count origin/master..HEAD 2>/dev/null || echo 0)
            if [ "${ahead:-0}" -eq 0 ]; then
                log "$label: nothing to push (HEAD is up-to-date with origin/master)"
                return 0
            fi
            log "$label: pushing $ahead commit(s) to origin/master"
            if git push origin master >> "$LOG" 2>&1; then
                log "$label: push OK ($ahead commit(s))"
            else
                log "$label: push FAILED (exit $?)"
            fi
        fi
    )
}

log "=== git-auto-push started (pid $$) ==="

while true; do
    if [ -f "$FLAG" ]; then
        rm -f "$FLAG"
        push_repo "post-commit"
    else
        push_repo "timer"
    fi
    sleep 600
done
