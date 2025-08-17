import pytest
from unittest.mock import patch, MagicMock
from application.sync_activities import sync_all_activities


@patch("application.sync_activities.StravaClient")
@patch("application.sync_activities.StravaActivity")
@patch("application.sync_activities.StravaGroup")
def test_sync_all_activities(mock_group_repo, mock_activity_repo, mock_strava_client):
    mock_group_repo.return_value.get_group.return_value = MagicMock(
        membros={
            "user1": {
                "access_token": "token1",
                "refresh_token": "refresh1",
                "last_activity_date": None
            },
            "user2": {
                "access_token": "token2",
                "refresh_token": "refresh2",
                "last_activity_date": None
            }
        }
    )

    mock_strava_client.return_value.fetch_activities.side_effect = [
        [{"id": "a1", "start_date_local":"2025-01-01T12:00:00Z"}, {"id": "a2", "start_date_local":"2025-01-01T12:00:00Z"}],
        [{"id": "b1", "start_date_local":"2025-01-01T12:00:00Z"}]
    ]

    mock_activity_repo.return_value.save_activity = MagicMock()

    sync_all_activities(group_id=123)
    assert mock_activity_repo.return_value.save_activity.call_count == 3
    mock_activity_repo.return_value.save_activity.assert_any_call(123, {"id": "a1", "start_date_local":"2025-01-01T12:00:00Z"})
    mock_activity_repo.return_value.save_activity.assert_any_call(123, {"id": "a2", "start_date_local":"2025-01-01T12:00:00Z"})
    mock_activity_repo.return_value.save_activity.assert_any_call(123, {"id": "b1", "start_date_local":"2025-01-01T12:00:00Z"})
