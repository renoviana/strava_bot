from unittest.mock import patch, MagicMock
from datetime import datetime
from application.commands.rank import (
    convert_rank_to_km,
    convert_rank_to_hour_minute_seconds,
    convert_rank,
    handle_rank_command,
    handle_rank_month_command,
    handle_rank_year_command,
)
from tests.unit.conftest import MockActivity, make_group


def test_convert_rank_to_km():
    assert convert_rank_to_km(1000) == "1.00km"
    assert convert_rank_to_km(5500) == "5.50km"
    assert convert_rank_to_km(0) == "0.00km"


def test_convert_rank_to_hour_minute_seconds():
    assert convert_rank_to_hour_minute_seconds(3661) == "1:1:1"
    assert convert_rank_to_hour_minute_seconds(3600) == "1:0:0"
    assert convert_rank_to_hour_minute_seconds(60) == "0:1:0"
    assert convert_rank_to_hour_minute_seconds(0) == "0:0:0"


def test_convert_rank_dispatches_distance():
    assert convert_rank(10000, "distance") == "10.00km"


def test_convert_rank_dispatches_time():
    assert convert_rank(3600, "moving_time") == "1:0:0"


@patch("application.commands.rank.sync_all_activities")
@patch("application.commands.rank.StravaActivity")
@patch("application.commands.rank.StravaGroup")
def test_handle_rank_command_no_activities(mock_group_repo, mock_activity_repo, mock_sync):
    mock_group_repo.return_value.get_group.return_value = make_group()
    mock_activity_repo.return_value.get_activities.return_value = []

    result = handle_rank_command(123, "Run", datetime(2025, 8, 1), datetime(2025, 9, 1))

    assert result == "Nenhuma atividade registrada este mês."


@patch("application.commands.rank.create_rank")
@patch("application.commands.rank.sync_all_activities")
@patch("application.commands.rank.StravaActivity")
@patch("application.commands.rank.StravaGroup")
def test_handle_rank_command_with_activities(mock_group_repo, mock_activity_repo, mock_sync, mock_create_rank):
    group = make_group()
    mock_group_repo.return_value.get_group.return_value = group
    mock_activity_repo.return_value.get_activities.return_value = [
        MockActivity(1, "2025-08-01T10:00:00", sport_type="Run", distance=10000),
    ]
    mock_create_rank.return_value = "formatted_rank"

    result = handle_rank_command(123, "Run", datetime(2025, 8, 1), datetime(2025, 9, 1))

    assert result == "formatted_rank"
    mock_create_rank.assert_called_once()


@patch("application.commands.rank.handle_rank_command")
def test_handle_rank_month_command_calls_with_correct_dates(mock_handle):
    mock_handle.return_value = "ok"
    now = datetime.now()

    handle_rank_month_command(123, "Run")

    args = mock_handle.call_args[0]
    assert args[0] == 123
    assert args[1] == "Run"
    assert args[2] == datetime(now.year, now.month, 1)


@patch("application.commands.rank.handle_rank_command")
def test_handle_rank_year_command_calls_with_correct_dates(mock_handle):
    mock_handle.return_value = "ok"
    now = datetime.now()

    handle_rank_year_command(123, "Run")

    args = mock_handle.call_args[0]
    assert args[2] == datetime(now.year, 1, 1)
