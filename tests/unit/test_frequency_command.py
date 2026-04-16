from unittest.mock import patch
from datetime import datetime
from application.commands.frequency import (
    handle_frequency_command,
    handle_month_frequency_command,
    handle_year_frequency_command,
)
from tests.unit.conftest import MockActivity, make_group


@patch("application.commands.frequency.sync_all_activities")
@patch("application.commands.frequency.StravaActivity")
def test_handle_frequency_command_returns_sorted_list(mock_activity_repo, mock_sync):
    mock_activity_repo.return_value.get_activities.return_value = [
        MockActivity(1, datetime(2025, 8, 1)),
        MockActivity(1, datetime(2025, 8, 2)),
        MockActivity(2, datetime(2025, 8, 1)),
    ]

    result = handle_frequency_command(123, datetime(2025, 8, 1), datetime(2025, 9, 1))

    assert result[0] == (1, 2)
    assert result[1] == (2, 1)


@patch("application.commands.frequency.create_rank")
@patch("application.commands.frequency.sync_all_activities")
@patch("application.commands.frequency.StravaActivity")
@patch("application.commands.frequency.StravaGroup")
def test_handle_month_frequency_formats_days_over_current_day(
    mock_group_repo, mock_activity_repo, mock_sync, mock_create_rank
):
    mock_group_repo.return_value.get_group.return_value = make_group()
    mock_activity_repo.return_value.get_activities.return_value = [
        MockActivity(1, datetime(2025, 8, 1)),
    ]
    mock_create_rank.return_value = "formatted"

    handle_month_frequency_command(123)

    call_args = mock_create_rank.call_args[0]
    rank_data = call_args[1]
    now = datetime.now()
    assert rank_data[0][1].endswith(f"/{now.day}")


@patch("application.commands.frequency.sync_all_activities")
@patch("application.commands.frequency.StravaActivity")
@patch("application.commands.frequency.StravaGroup")
def test_handle_month_frequency_no_activities(mock_group_repo, mock_activity_repo, mock_sync):
    mock_group_repo.return_value.get_group.return_value = make_group()
    mock_activity_repo.return_value.get_activities.return_value = []

    result = handle_month_frequency_command(123)

    assert result == "Nenhuma atividade registrada este mês."


@patch("application.commands.frequency.create_rank")
@patch("application.commands.frequency.sync_all_activities")
@patch("application.commands.frequency.StravaActivity")
@patch("application.commands.frequency.StravaGroup")
def test_handle_year_frequency_formats_days_over_year_day(
    mock_group_repo, mock_activity_repo, mock_sync, mock_create_rank
):
    mock_group_repo.return_value.get_group.return_value = make_group()
    mock_activity_repo.return_value.get_activities.return_value = [
        MockActivity(1, datetime(2025, 8, 1)),
    ]
    mock_create_rank.return_value = "formatted"

    handle_year_frequency_command(123)

    call_args = mock_create_rank.call_args[0]
    rank_data = call_args[1]
    now = datetime.now()
    assert rank_data[0][1].endswith(f"/{now.timetuple().tm_yday}")
