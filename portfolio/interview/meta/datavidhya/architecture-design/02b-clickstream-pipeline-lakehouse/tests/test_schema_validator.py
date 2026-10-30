"""Tests for schema validator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

import pytest
from schema_validator import validate_events
from sdk_payload import KNOWN_EVENT_NAMES


def test_valid_event():
    ev = {
        "event_id":   "abc-123",
        "user_id":    "hashed-user-id",
        "event_ts":   "2026-09-26T10:00:00Z",
        "event_name": "page_view",
        "properties": {"page": "/home"},
    }
    valid, invalid, quarantined = validate_events([ev], KNOWN_EVENT_NAMES)
    assert len(valid) == 1
    assert len(invalid) == 0
    assert len(quarantined) == 0


def test_missing_required_field():
    ev = {"event_id": "abc-123", "user_id": "u1", "event_ts": "2026-09-26T10:00:00Z"}
    valid, invalid, _ = validate_events([ev], KNOWN_EVENT_NAMES)
    assert len(invalid) == 1


def test_invalid_timestamp():
    ev = {
        "event_id":   "abc-123",
        "user_id":    "u1",
        "event_ts":   "not-a-date",
        "event_name": "click",
    }
    valid, invalid, _ = validate_events([ev], KNOWN_EVENT_NAMES)
    assert len(invalid) == 1


def test_unknown_event_name_quarantined():
    ev = {
        "event_id":   "abc-123",
        "user_id":    "u1",
        "event_ts":   "2026-09-26T10:00:00Z",
        "event_name": "experimental_future_event",
    }
    valid, invalid, quarantined = validate_events([ev], KNOWN_EVENT_NAMES)
    assert len(quarantined) == 1
    assert len(valid) == 0


def test_unknown_event_name_accepted_when_no_blocklist():
    ev = {
        "event_id":   "abc-123",
        "user_id":    "u1",
        "event_ts":   "2026-09-26T10:00:00Z",
        "event_name": "experimental_future_event",
    }
    valid, invalid, quarantined = validate_events([ev])   # no blocklist
    assert len(valid) == 1
    assert len(quarantined) == 0
