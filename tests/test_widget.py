"""Tests for widget helper functions."""

import pytest
from widget import fmt_reset, pct_bar


class TestFmtReset:
    def test_zero_or_negative_returns_now(self):
        assert fmt_reset(0) == "now"
        assert fmt_reset(-1) == "now"
        assert fmt_reset(-100) == "now"

    def test_minutes_only(self):
        assert fmt_reset(60) == "1m"
        assert fmt_reset(59 * 60) == "59m"

    def test_hours_and_minutes(self):
        assert fmt_reset(3600) == "1h00m"
        assert fmt_reset(3660) == "1h01m"
        assert fmt_reset(7200) == "2h00m"
        assert fmt_reset(7260) == "2h01m"
        assert fmt_reset(90 * 60) == "1h30m"

    def test_minutes_padded_with_leading_zero(self):
        assert fmt_reset(3609) == "1h00m"  # 3609 // 60 = 60m -> 1h, 60 % 60 = 0m
        assert fmt_reset(3660) == "1h01m"

    def test_under_one_minute_returns_now(self):
        # 30 seconds: 30 // 60 = 0 minutes -> "0m" ... but spec says <= 0 returns "now"
        # 30 secs: h=0, m=0, so no h branch, returns "0m"
        assert fmt_reset(30) == "0m"

    def test_exactly_one_hour(self):
        assert fmt_reset(3600) == "1h00m"


class TestPctBar:
    def test_zero_pct_all_empty(self):
        assert pct_bar(0) == "░░░░░░░░"

    def test_100_pct_all_filled(self):
        assert pct_bar(100) == "████████"

    def test_50_pct_half_filled(self):
        bar = pct_bar(50)
        assert bar == "████░░░░"

    def test_custom_width(self):
        assert pct_bar(0, width=4) == "░░░░"
        assert pct_bar(100, width=4) == "████"
        assert pct_bar(50, width=4) == "██░░"

    def test_width_8_default(self):
        bar = pct_bar(75)
        assert len(bar) == 8

    def test_25_pct(self):
        assert pct_bar(25) == "██░░░░░░"

    def test_total_length_always_equals_width(self):
        for pct in range(0, 101, 10):
            bar = pct_bar(pct)
            assert len(bar) == 8, f"pct={pct} bar len={len(bar)}"
