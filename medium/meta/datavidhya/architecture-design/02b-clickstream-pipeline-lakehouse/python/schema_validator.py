"""
Schema validator for incoming events.

Two modes:
  - STRICT: hard reject if any required field missing or wrong type
  - LENIENT: tag known events; quarantine unknown event_names

In production this is replaced by the Avro/JSON-Schema generated from
the schema registry. Here we use jsonschema for portability.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple

import jsonschema


# --------------------------------------------------------------------- #
# JSON Schema (matches sdk_payload.ClickstreamEvent)
# --------------------------------------------------------------------- #

EVENT_JSON_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "ClickstreamEvent",
    "type": "object",
    "required": ["event_id", "user_id", "event_ts", "event_name"],
    "properties": {
        "event_id":    {"type": "string", "minLength": 4, "maxLength": 64},
        "user_id":     {"type": "string", "minLength": 1, "maxLength": 64},
        "event_ts":    {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"},
        "event_name":  {"type": "string", "minLength": 1, "maxLength": 64},
        "session_id":  {"type": ["string", "null"]},
        "platform":    {"type": ["string", "null"], "enum": ["web", "ios", "android", "server", None]},
        "properties":  {"type": "object", "additionalProperties": {"type": "string"}},
        "context":     {"type": "object", "additionalProperties": {"type": "string"}},
    },
    "additionalProperties": True,
}


@dataclass
class ValidationResult:
    valid: int = 0
    invalid: int = 0
    quarantined: int = 0     # structurally OK but unknown event_name

    def __str__(self):
        return f"valid={self.valid}, invalid={self.invalid}, quarantined={self.quarantined}"


def validate_events(
    events: Iterable[dict],
    known_event_names: set[str] | None = None,
) -> Tuple[list[dict], list[dict], list[dict]]:
    """
    Returns (valid, invalid, quarantined).
    """
    valid, invalid, quarantined = [], [], []
    for ev in events:
        try:
            jsonschema.validate(ev, EVENT_JSON_SCHEMA)
            if known_event_names and ev.get("event_name") not in known_event_names:
                quarantined.append(ev)
            else:
                valid.append(ev)
        except jsonschema.ValidationError:
            invalid.append(ev)
    return valid, invalid, quarantined


# --------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------- #

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="sample_data/events.jsonl")
    args = p.parse_args()

    from sdk_payload import KNOWN_EVENT_NAMES
    events = [json.loads(l) for l in Path(args.input).read_text().splitlines() if l.strip()]
    valid, invalid, quarantined = validate_events(events, KNOWN_EVENT_NAMES)
    print(ValidationResult(
        valid=len(valid),
        invalid=len(invalid),
        quarantined=len(quarantined),
    ))
    if invalid[:3]:
        print("Sample invalid events:")
        for ev in invalid[:3]:
            print(" ", ev)
