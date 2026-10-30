"""Smoke tests for end-to-end clickstream pipeline (offline)."""

import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from sdk_payload import generate_sample
from schema_validator import validate_events
from bot_filter import filter_events


def test_pipeline_end_to_end_offline():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "events.jsonl"
        generate_sample(n=200, bot_pct=0.30, out=str(out))

        events = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
        valid, invalid, _ = validate_events(events)
        res = filter_events(valid)

        # 25-30% of generated events should be flagged as bots
        bot_pct = res.stats["bot"] / max(res.stats["bot"] + res.stats["human"], 1)
        assert 0.15 <= bot_pct <= 0.50, f"unexpected bot pct: {bot_pct:.2%}"
