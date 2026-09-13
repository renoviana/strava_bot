from datetime import date, datetime, timedelta

from domain.services.streak_service import StreakService
from tests.unit.conftest import MockActivity

HOJE = date(2026, 9, 12)


def _iso(delta_days: int = 0) -> str:
    return (datetime(2026, 9, 12, 10, 0) - timedelta(days=delta_days)).isoformat()


def test_streak_consecutive_days():
    activities = [MockActivity(1, _iso(0)), MockActivity(1, _iso(1)), MockActivity(1, _iso(2))]
    assert StreakService(activities, HOJE).calculate() == [(1, 3)]


def test_streak_gap_breaks_streak():
    activities = [MockActivity(1, _iso(0)), MockActivity(1, _iso(2))]
    assert StreakService(activities, HOJE).calculate() == [(1, 1)]


def test_streak_no_activity_today_excluded():
    activities = [MockActivity(1, _iso(1)), MockActivity(1, _iso(2))]
    assert StreakService(activities, HOJE).calculate() == []


def test_streak_sorted_descending():
    activities = [
        MockActivity(1, _iso(0)),
        MockActivity(2, _iso(0)),
        MockActivity(2, _iso(1)),
        MockActivity(2, _iso(2)),
    ]
    assert StreakService(activities, HOJE).calculate() == [(2, 3), (1, 1)]


def test_streak_multiple_activities_same_day_count_as_one():
    activities = [MockActivity(1, _iso(0)) for _ in range(3)]
    assert StreakService(activities, HOJE).calculate() == [(1, 1)]


def test_streak_accepts_datetime():
    activities = [MockActivity(1, datetime(2026, 9, 12, 6, 0)), MockActivity(1, datetime(2026, 9, 11, 23, 0))]
    assert StreakService(activities, HOJE).calculate() == [(1, 2)]


def test_streak_usa_o_today_injetado():
    activities = [MockActivity(1, _iso(1))]
    assert StreakService(activities, HOJE - timedelta(days=1)).calculate() == [(1, 1)]


def test_streak_empty_activities():
    assert StreakService([], HOJE).calculate() == []
