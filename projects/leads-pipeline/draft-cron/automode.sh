#!/bin/bash
# Daily automode — runs auto.py, then re-runs firehose to replenish leads
# Schedule: every day at 9am Vietnam time (cron: 0 9 * * *)

set -e
cd "$(dirname "$0")"

echo "=== AUTO MODE $(date) ==="
echo ""
echo "1. Running email + URL apply..."
python3 auto.py
echo ""
echo "2. Status:"
python3 -c "
import json
leads = json.load(open('leads.json'))
total = len(leads)
sent = sum(1 for l in leads if l['status'] != 'pending')
print(f'   {sent}/{total} leads processed')
"
echo ""
echo "=== DONE ==="
