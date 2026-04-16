from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from application.commands.streak import handle_streak_command
from tests.unit.conftest import MockActivity, make_group

TODAY = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)


@patch("application.commands.streak.sync_all_activities")
@patch("application.commands.streak.StravaActivity")
@patch("application.commands.streak.StravaGroup")
def test_streak_no_activity_today(mock_group_repo, mock_activity_repo, mock_sync):
    mock_group_repo.return_value.get_group.return_value = make_group()
    mock_activity_repo.return_value.get_activities.return_value = []

    result = handle_streak_command(123)

    assert result == "Ninguem fez atividade hoje"


@patch("application.commands.streak.create_rank")
@patch("application.commands.streak.StreakService")
@patch("application.commands.streak.sync_all_activities")
@patch("application.commands.streak.StravaActivity")
@patch("application.commands.streak.StravaGroup")
def test_streak_calls_streak_service_with_active_members(
    mock_group_repo, mock_activity_repo, mock_sync, mock_streak_service, mock_create_rank
):
    group = make_group()
    mock_group_repo.return_value.get_group.return_value = group

    today_activity = MagicMock()
    today_activity.__getitem__ = lambda self, k: {"athlete": {"id": 1}}[k]
    mock_activity_repo.return_value.get_activities.side_effect = [
        [today_activity],
        [MockActivity(1, TODAY)],
    ]
    mock_streak_service.return_value.calculate.return_value = [(1, 5)]
    mock_create_rank.return_value = "streak_rank"

    result = handle_streak_command(123)

    assert result == "streak_rank"
    mock_streak_service.assert_called_once()
