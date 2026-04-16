from unittest.mock import MagicMock
from domain.services.medal_service import MedalService


def _make_group(medalhas):
    group = MagicMock()
    group.medalhas = medalhas
    return group


def test_medal_counts_and_points():
    group = _make_group({
        "2025-01": {
            "Run": {"Joao": 1, "Maria": 2, "Pedro": 3}
        }
    })
    result = MedalService(group).calculate()
    assert result["Joao"][1] == 1
    assert result["Joao"]["points"] == 3
    assert result["Maria"][2] == 1
    assert result["Maria"]["points"] == 2
    assert result["Pedro"][3] == 1
    assert result["Pedro"]["points"] == 1


def test_medal_sorted_by_points_descending():
    group = _make_group({
        "2025-01": {"Run": {"Joao": 1}},
        "2025-02": {"Run": {"Joao": 1, "Maria": 2}},
    })
    result = MedalService(group).calculate()
    keys = list(result.keys())
    assert keys[0] == "Joao"
    assert keys[1] == "Maria"


def test_medal_accumulates_across_months():
    group = _make_group({
        "2025-01": {"Run": {"Joao": 1}},
        "2025-02": {"Run": {"Joao": 1}},
        "2025-03": {"Run": {"Joao": 1}},
    })
    result = MedalService(group).calculate()
    assert result["Joao"][1] == 3
    assert result["Joao"]["points"] == 9


def test_medal_accumulates_across_sports():
    group = _make_group({
        "2025-01": {
            "Run": {"Joao": 1},
            "Ride": {"Joao": 2},
        }
    })
    result = MedalService(group).calculate()
    assert result["Joao"][1] == 1
    assert result["Joao"][2] == 1
    assert result["Joao"]["points"] == 5


def test_medal_empty_medalhas():
    group = _make_group({})
    result = MedalService(group).calculate()
    assert result == {}


def test_medal_only_user_in_result():
    group = _make_group({
        "2025-01": {"Run": {"Joao": 1}}
    })
    result = MedalService(group).calculate()
    assert list(result.keys()) == ["Joao"]
