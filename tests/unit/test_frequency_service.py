from datetime import datetime
from domain.services.frequency_service import FrequencyService
from tests.unit.conftest import MockActivity


def test_frequency_counts_unique_days():
    activities = [
        MockActivity(1, datetime(2025, 8, 1)),
        MockActivity(1, datetime(2025, 8, 1)),
        MockActivity(1, datetime(2025, 8, 2)),
        MockActivity(2, datetime(2025, 8, 1)),
    ]
    result = FrequencyService(activities).calculate()
    assert result[0] == (1, 2)
    assert result[1] == (2, 1)


def test_frequency_sorted_descending():
    activities = [
        MockActivity(2, datetime(2025, 8, 1)),
        MockActivity(1, datetime(2025, 8, 1)),
        MockActivity(1, datetime(2025, 8, 2)),
        MockActivity(1, datetime(2025, 8, 3)),
    ]
    result = FrequencyService(activities).calculate()
    assert result[0][0] == 1
    assert result[0][1] == 3


def test_frequency_accepts_datetime_object():
    activities = [
        MockActivity(1, datetime(2025, 8, 1, 10, 30)),
    ]
    result = FrequencyService(activities).calculate()
    assert result == [(1, 1)]


def test_frequency_accepts_iso_string():
    activities = [
        MockActivity(1, "2025-08-01T10:30:00"),
    ]
    result = FrequencyService(activities).calculate()
    assert result == [(1, 1)]


def test_frequency_empty_activities():
    result = FrequencyService([]).calculate()
    assert result == []


def test_frequency_multiple_activities_same_day_count_as_one():
    activities = [MockActivity(1, datetime(2025, 8, 1)) for _ in range(5)]
    result = FrequencyService(activities).calculate()
    assert result == [(1, 1)]
