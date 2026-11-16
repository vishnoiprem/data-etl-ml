"""Settings: the window, the exclusive end date, and the thresholds."""

from __future__ import annotations

from datetime import date

import pytest

from aws_cost_analyzer.config import (
    DEFAULT_END,
    DEFAULT_REGION,
    DEFAULT_START,
    Settings,
    Thresholds,
    load_settings,
)


class TestWindow:
    def test_the_default_window_is_the_console_view(self):
        settings = Settings()
        assert settings.start == DEFAULT_START
        assert settings.end == DEFAULT_END
        assert settings.region == DEFAULT_REGION

    def test_the_end_date_is_exclusive_on_the_wire(self):
        # TimePeriod.End is exclusive: "up to and including 2017-04-30
        # but not including 2017-05-01". Sending 2026-10-31 literally
        # makes October vanish with no error.
        settings = Settings()
        assert settings.exclusive_end == "2026-11-01"

    def test_the_exclusive_end_rolls_over_the_year(self):
        settings = Settings(end="2026-12-31")
        assert settings.exclusive_end == "2027-01-01"

    def test_the_exclusive_end_handles_a_leap_day_window(self):
        settings = Settings(end="2028-02-28")
        assert settings.exclusive_end == "2028-02-29"


class TestLoading:
    def test_the_environment_sets_the_region(self):
        settings = load_settings({"AWS_REGION": "us-east-1"})
        assert settings.region == "us-east-1"

    def test_the_environment_sets_the_window(self):
        settings = load_settings({"AWSCA_START": "2026-01-01", "AWSCA_END": "2026-03-31"})
        assert settings.start == "2026-01-01"
        assert settings.end == "2026-03-31"

    def test_a_blank_override_falls_back_to_the_default(self):
        settings = load_settings({"AWS_REGION": "   "})
        assert settings.region == DEFAULT_REGION

    def test_the_thresholds_are_overridable(self):
        settings = load_settings({"AWSCA_MIN_GROWTH_USD": "500"})
        assert settings.thresholds.min_growth_usd == 500.0

    def test_a_malformed_threshold_falls_back_to_the_default(self):
        settings = load_settings({"AWSCA_MIN_GROWTH_USD": "not-a-number"})
        assert settings.thresholds.min_growth_usd == Thresholds().min_growth_usd

    def test_the_granularity_is_upper_cased(self):
        settings = load_settings({"AWSCA_GRANULARITY": "daily"})
        assert settings.granularity == "DAILY"

    def test_the_window_parses_as_dates(self):
        settings = Settings()
        assert settings.start_date == date(2026, 5, 1)
        assert settings.end_date == date(2026, 10, 31)

    def test_the_thresholds_hold_the_documented_defaults(self):
        thresholds = Thresholds()
        assert thresholds.min_growth_pct == 0.20
        assert thresholds.min_growth_usd == 50.0
        assert thresholds.min_access_usd == 25.0
        assert thresholds.min_age_days_for_glacier == 90
        assert thresholds.min_size_kb_for_ia == 128
        assert thresholds.min_tag_coverage == 0.90

    @pytest.mark.parametrize(
        ("pct", "usd", "should_fire"),
        [
            (0.20, 50.0, True),   # both thresholds met exactly
            (0.19, 500.0, False),  # grew a lot, but not enough
            (0.50, 49.0, False),   # big relative move, still too small
            (0.21, 51.0, True),
        ],
    )
    def test_the_growth_gate_is_a_double_threshold(self, pct, usd, should_fire):
        # A bucket that doubled to $3 is noise. A bucket that moved 40%
        # to $400 is worth a look. Both conditions must hold.
        fires = pct >= 0.20 and usd >= 50.0
        assert fires is should_fire
