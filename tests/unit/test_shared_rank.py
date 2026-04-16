from unittest.mock import MagicMock
from shared.rank import create_rank, get_user_link, get_medalhas
from tests.unit.conftest import make_group

MEMBROS = {
    "Joao": {"athlete_id": 1, "access_token": "t", "refresh_token": "r", "last_activity_date": None},
    "Maria": {"athlete_id": 2, "access_token": "t", "refresh_token": "r", "last_activity_date": None},
    "Pedro": {"athlete_id": 3, "access_token": "t", "refresh_token": "r", "last_activity_date": None},
}


def _group_with_medalhas(medalhas):
    group = MagicMock()
    group.membros = MEMBROS
    group.medalhas = medalhas
    return group


def test_create_rank_basic():
    group = _group_with_medalhas({})
    result = create_rank("Titulo", [(1, "10.0km"), (2, "8.0km")], group)
    assert "Titulo" in result
    assert "1º" in result
    assert "2º" in result
    assert "10.0km" in result


def test_create_rank_tie_same_position():
    group = _group_with_medalhas({})
    result = create_rank("Titulo", [(1, "10km"), (2, "10km")], group)
    assert result.count("1º") == 2
    assert "2º" not in result


def test_create_rank_increments_position_after_tie():
    group = _group_with_medalhas({})
    result = create_rank("Titulo", [(1, "10km"), (2, "10km"), (3, "5km")], group)
    assert result.count("1º") == 2
    assert "2º" in result


def test_get_user_link_contains_athlete_id():
    link = get_user_link(1, MEMBROS)
    assert "strava.com/athletes/1" in link
    assert "Joao" in link


def test_get_medalhas_no_sport_type():
    group = _group_with_medalhas({"2025-01": {"Run": {"Joao": 1}}})
    result = get_medalhas(1, group, sport_type=None)
    assert result == ""


def test_get_medalhas_with_medals():
    medalhas = {
        "2025-01": {"Run": {"Joao": 1}},
        "2025-02": {"Run": {"Joao": 2}},
    }
    group = _group_with_medalhas(medalhas)
    result = get_medalhas(1, group, sport_type="Run")
    assert "🥇1" in result
    assert "🥈1" in result


def test_get_medalhas_no_medals_for_user():
    medalhas = {"2025-01": {"Run": {"Maria": 1}}}
    group = _group_with_medalhas(medalhas)
    result = get_medalhas(1, group, sport_type="Run")
    assert result == ""
