"""Unit tests for analytics period-bound logic (no database required)."""

from datetime import date

import pytest

from app.services.analytics import _period_bounds


class TestPeriodBounds:
    def test_daily(self) -> None:
        start, end = _period_bounds("daily", date(2026, 9, 4))
        assert start == date(2026, 9, 4)
        assert end == date(2026, 9, 4)

    def test_weekly_starts_monday(self) -> None:
        # 2026-09-04 is a Friday.
        start, end = _period_bounds("weekly", date(2026, 9, 4))
        assert start == date(2026, 8, 31)  # Monday
        assert end == date(2026, 9, 6)  # Sunday
        assert start.weekday() == 0

    def test_monthly(self) -> None:
        start, end = _period_bounds("monthly", date(2026, 9, 15))
        assert start == date(2026, 9, 1)
        assert end == date(2026, 9, 30)

    def test_monthly_february_leap(self) -> None:
        start, end = _period_bounds("monthly", date(2024, 2, 10))
        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)  # 2024 is a leap year

    def test_annual(self) -> None:
        start, end = _period_bounds("annual", date(2026, 6, 15))
        assert start == date(2026, 1, 1)
        assert end == date(2026, 12, 31)

    def test_unknown_period_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown period"):
            _period_bounds("fortnightly", date(2026, 9, 4))
