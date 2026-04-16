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
    result = RankService(_make_activities()).calculate("Run")
    assert result[0] == (2, 20000)
    assert result[1] == (1, 15000)


def test_rank_excludes_other_sports():
    result = RankService(_make_activities()).calculate("Run")
    ids = [r[0] for r in result]
    assert 3 not in ids


def test_rank_sorted_descending():
    result = RankService(_make_activities()).calculate("Run")
    values = [r[1] for r in result]
    assert values == sorted(values, reverse=True)


def test_rank_empty_activities():
    result = RankService([]).calculate("Run")
    assert result == []


def test_rank_no_matching_sport():
    activities = [MockActivity(1, "2025-08-01T10:00:00", sport_type="Swim", distance=1000)]
    result = RankService(activities).calculate("Run")
    assert result == []


def test_rank_by_time_for_yoga():
    activities = [
        MockActivity(1, "2025-08-01T10:00:00", sport_type="yoga", moving_time=3600),
        MockActivity(2, "2025-08-01T10:00:00", sport_type="yoga", moving_time=1800),
    ]
    service = RankService(activities)
    result = service.calculate("yoga")
    assert service.rank_params == "moving_time"
    assert result[0] == (1, 3600)


def test_rank_type_distance_for_run():
    service = RankService([])
    service.sport_type = "Run"
    assert service.get_rank_type() == "distance"


def test_rank_type_time_for_weighttraining():
    service = RankService([])
    service.sport_type = "weighttraining"
    assert service.get_rank_type() == "moving_time"


def test_list_sports():
    activities = _make_activities()
    sports = RankService(activities).list_sports()
    assert set(sports) == {"Run", "Ride"}
