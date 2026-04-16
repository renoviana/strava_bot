from datetime import datetime, timedelta
from domain.services.streak_service import StreakService
from tests.unit.conftest import MockActivity


def _iso(delta_days: int = 0) -> str:
    return (datetime.now() - timedelta(days=delta_days)).replace(
        hour=10, minute=0, second=0, microsecond=0
    ).isoformat()


def test_streak_consecutive_days():
    activities = [
        MockActivity(1, _iso(0)),
        MockActivity(1, _iso(1)),
        MockActivity(1, _iso(2)),
    ]
    result = StreakService(activities).calculate()
    assert result == [(1, 3)]


def test_streak_gap_breaks_streak():
    activities = [
        MockActivity(1, _iso(0)),
        MockActivity(1, _iso(2)),
    ]
    result = StreakService(activities).calculate()
    assert result == [(1, 1)]


def test_streak_no_activity_today_excluded():
    activities = [
        MockActivity(1, _iso(1)),
        MockActivity(1, _iso(2)),
    ]
    result = StreakService(activities).calculate()
    assert result == []


def test_streak_sorted_descending():
    activities = [
        MockActivity(1, _iso(0)),
        MockActivity(2, _iso(0)),
        MockActivity(2, _iso(1)),
        MockActivity(2, _iso(2)),
    ]
    result = StreakService(activities).calculate()
    assert result[0] == (2, 3)
    assert result[1] == (1, 1)


def test_streak_multiple_activities_same_day_count_as_one():
    activities = [MockActivity(1, _iso(0)) for _ in range(3)]
    result = StreakService(activities).calculate()
    assert result == [(1, 1)]


def test_streak_empty_activities():
    result = StreakService([]).calculate()
    assert result == []
