"""Tests for notification pipeline."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

import pytest

from multi_channel_dedup import NotificationRecord, dedup
from attribution_engine import NotificationSent, AppOpen, attribute_many, ATTRIBUTION_WINDOW_S
from fatigue_scorer import UserFatigueFeatures, score_user, score_many
from ab_test_router import assign_variant, NotificationVariant


# --------------------------------------------------------------------- #
# Multi-channel dedup
# --------------------------------------------------------------------- #

def test_dedup_keeps_earliest_engagement_across_channels():
    recs = [
        NotificationRecord("n1", "g1", "u1", "push",  100.0,
                            delivered_ts=101.0, opened_ts=110.0),
        NotificationRecord("n2", "g1", "u1", "email", 100.5,
                            delivered_ts=102.0, opened_ts=105.0),  # earlier open
    ]
    facts = dedup(recs)
    f = facts["g1"]
    assert f.opened_ts == 105.0     # earliest across channels
    assert f.channels_sent == ["email", "push"]
    assert f.is_engaged


def test_dedup_unengaged_notification():
    recs = [NotificationRecord("n1", "g1", "u1", "push", 100.0, delivered_ts=101.0)]
    f = dedup(recs)["g1"]
    assert f.opened_ts is None
    assert not f.is_engaged


# --------------------------------------------------------------------- #
# Attribution
# --------------------------------------------------------------------- #

def test_attribution_within_window():
    n = [NotificationSent("n1", "u1", 1000.0, "push")]
    o = [AppOpen("u1", 1100.0, "s1")]    # +100s, well within 30 min
    out = attribute_many(n, o)
    assert len(out) == 1
    assert out[0].notification_id == "n1"


def test_attribution_outside_window():
    n = [NotificationSent("n1", "u1", 1000.0, "push")]
    o = [AppOpen("u1", 1000.0 + ATTRIBUTION_WINDOW_S + 100, "s1")]
    out = attribute_many(n, o)
    assert out == []


def test_attribution_picks_most_recent_qualifying():
    n = [
        NotificationSent("n1", "u1", 1000.0, "push"),
        NotificationSent("n2", "u1", 1100.0, "email"),
    ]
    o = [AppOpen("u1", 1120.0, "s1")]    # 120s after n1, 20s after n2
    out = attribute_many(n, o)
    assert len(out) == 1
    assert out[0].notification_id == "n2"     # closest one


def test_attribution_separate_users():
    n = [NotificationSent("n1", "u1", 1000.0, "push")]
    o = [AppOpen("u2", 1100.0, "s1")]     # different user
    out = attribute_many(n, o)
    assert out == []


# --------------------------------------------------------------------- #
# Fatigue
# --------------------------------------------------------------------- #

def test_healthy_user_no_action():
    f = UserFatigueFeatures("u1", notifs_sent_24h=3, notifs_sent_7d=10,
                            open_rate_7d=0.45, dismiss_rate_7d=0.05,
                            unsubscribe_count_30d=0)
    s = score_user(f)
    assert s.tier == "healthy"
    assert not s.should_drop_marketing


def test_critical_user_drops_marketing():
    f = UserFatigueFeatures("u1", notifs_sent_24h=25, notifs_sent_7d=70,
                            open_rate_7d=0.05, dismiss_rate_7d=0.50,
                            unsubscribe_count_30d=3)
    s = score_user(f)
    assert s.tier == "critical"
    assert s.should_drop_marketing


def test_warn_user_partial_action():
    f = UserFatigueFeatures("u1", notifs_sent_24h=12, notifs_sent_7d=35,
                            open_rate_7d=0.10, dismiss_rate_7d=0.20,
                            unsubscribe_count_30d=0)
    s = score_user(f)
    assert s.tier == "warn"
    assert s.should_drop_marketing


# --------------------------------------------------------------------- #
# A/B test router
# --------------------------------------------------------------------- #

def test_variant_assignment_deterministic():
    variants = [
        NotificationVariant("exp_x", "control", "t1", "push", 10, 5),
        NotificationVariant("exp_x", "v1",      "t2", "push", 10, 5),
    ]
    a1 = assign_variant("user_42", "exp_x", variants)
    a2 = assign_variant("user_42", "exp_x", variants)
    assert a1.variant_id == a2.variant_id


def test_variant_assignment_distribution():
    variants = [
        NotificationVariant("exp_x", "control", "t1", "push", 10, 5),
        NotificationVariant("exp_x", "v1",      "t2", "push", 10, 5),
    ]
    counts = {"control": 0, "v1": 0, None: 0}
    for i in range(10_000):
        v = assign_variant(f"u_{i}", "exp_x", variants)
        counts[v.variant_id if v else None] += 1
    # ~80% in experiment (~20% None), ~50/50 split within
    assert 3_500 <= counts["control"] <= 4_500     # ~40% of 10k
    assert 0.18 < counts[None] / 10_000 < 0.22
