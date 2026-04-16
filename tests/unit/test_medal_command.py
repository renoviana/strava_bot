from unittest.mock import patch, MagicMock
from application.commands.medal import handle_medal_command
from tests.unit.conftest import make_group


@patch("application.commands.medal.StravaGroup")
def test_medal_no_medals(mock_group_repo):
    mock_group_repo.return_value.get_group.return_value = make_group(medalhas={})

    with patch("application.commands.medal.MedalService") as mock_service:
        mock_service.return_value.calculate.return_value = {}
        result = handle_medal_command(123)

    assert result == "Nenhuma medalha conquistada"


@patch("application.commands.medal.StravaGroup")
def test_medal_formats_correctly(mock_group_repo):
    group = make_group(
        membros={"Joao": {"athlete_id": 1, "access_token": "t", "refresh_token": "r", "last_activity_date": None}},
        medalhas={"2025-01": {"Run": {"Joao": 1}}}
    )
    mock_group_repo.return_value.get_group.return_value = group

    with patch("application.commands.medal.MedalService") as mock_service:
        mock_service.return_value.calculate.return_value = {
            "Joao": {1: 2, 2: 1, 3: 0, "points": 8}
        }
        with patch("application.commands.medal.create_rank") as mock_create_rank:
            mock_create_rank.return_value = "rank_result"
            result = handle_medal_command(123)

    assert result == "rank_result"
    mock_create_rank.assert_called_once()
    rank_data = mock_create_rank.call_args[0][1]
    assert len(rank_data) == 1
    assert rank_data[0][0] == 1


@patch("application.commands.medal.StravaGroup")
def test_medal_skips_unknown_members(mock_group_repo):
    group = make_group(membros={}, medalhas={})
    mock_group_repo.return_value.get_group.return_value = group

    with patch("application.commands.medal.MedalService") as mock_service:
        mock_service.return_value.calculate.return_value = {
            "GhostUser": {1: 1, 2: 0, 3: 0, "points": 3}
        }
        with patch("application.commands.medal.create_rank") as mock_create_rank:
            mock_create_rank.return_value = "rank_result"
            handle_medal_command(123)

    rank_data = mock_create_rank.call_args[0][1]
    assert rank_data == []
