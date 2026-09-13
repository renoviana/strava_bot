from domain.services.rank_service import RankService
from tests.unit.conftest import MockActivity


def _make_activities():
    return [
        MockActivity(1, "2025-08-01T10:00:00", sport_type="Run", distance=10000),
        MockActivity(1, "2025-08-02T10:00:00", sport_type="Run", distance=5000),
        MockActivity(2, "2025-08-01T10:00:00", sport_type="Run", distance=20000),
        MockActivity(3, "2025-08-01T10:00:00", sport_type="Ride", distance=50000),
    ]


def test_rank_sums_distance_by_sport():
    result = RankService(_make_activities()).calculate("Run", "distance")
    assert result == [(2, 20000), (1, 15000)]


def test_rank_excludes_other_sports():
    ids = [r[0] for r in RankService(_make_activities()).calculate("Run", "distance")]
    assert 3 not in ids


def test_rank_empty_activities():
    assert RankService([]).calculate("Run", "distance") == []


def test_rank_no_matching_sport():
    activities = [MockActivity(1, "2025-08-01T10:00:00", sport_type="Swim", distance=1000)]
    assert RankService(activities).calculate("Run", "distance") == []


def test_rank_by_moving_time():
    activities = [
        MockActivity(1, "2025-08-01T10:00:00", sport_type="Yoga", moving_time=3600),
        MockActivity(2, "2025-08-01T10:00:00", sport_type="Yoga", moving_time=1800),
    ]
    assert RankService(activities).calculate("Yoga", "moving_time") == [(1, 3600), (2, 1800)]


def test_rank_metric_nula_conta_como_zero():
    activities = [
        MockActivity(1, "2025-08-01T10:00:00", sport_type="Run", distance=None),
        MockActivity(1, "2025-08-02T10:00:00", sport_type="Run", distance=3000),
    ]
    assert RankService(activities).calculate("Run", "distance") == [(1, 3000)]
