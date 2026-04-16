import pytest
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta
from requests import HTTPError
from application.sync_activities import sync_all_activities


def _mock_group(last_sync=None, membros=None):
    group = MagicMock()
    group.last_sync = last_sync
    group.membros = membros or {
        "user1": {"access_token": "tok1", "refresh_token": "ref1", "last_activity_date": None},
        "user2": {"access_token": "tok2", "refresh_token": "ref2", "last_activity_date": None},
    }
    return group


@patch("application.sync_activities.StravaClient")
@patch("application.sync_activities.StravaActivity")
@patch("application.sync_activities.StravaGroup")
def test_sync_saves_all_activities(mock_group_repo, mock_activity_repo, mock_strava_client):
    mock_group_repo.return_value.get_group.return_value = _mock_group()
    mock_strava_client.return_value.fetch_activities.side_effect = [
        [{"id": "a1", "start_date_local": "2025-01-01T12:00:00Z"}],
        [{"id": "b1", "start_date_local": "2025-01-02T12:00:00Z"}],
    ]

    sync_all_activities(group_id=123)

    assert mock_activity_repo.return_value.save_activity.call_count == 2


@patch("application.sync_activities.StravaClient")
@patch("application.sync_activities.StravaActivity")
@patch("application.sync_activities.StravaGroup")
def test_sync_skips_when_group_not_found(mock_group_repo, mock_activity_repo, mock_strava_client):
    mock_group_repo.return_value.get_group.return_value = None

    sync_all_activities(group_id=999)

    mock_strava_client.return_value.fetch_activities.assert_not_called()


@patch("application.sync_activities.StravaClient")
@patch("application.sync_activities.StravaActivity")
@patch("application.sync_activities.StravaGroup")
def test_sync_skips_when_synced_recently(mock_group_repo, mock_activity_repo, mock_strava_client):
    recent_sync = datetime.now() - timedelta(seconds=30)
    mock_group_repo.return_value.get_group.return_value = _mock_group(last_sync=recent_sync)

    sync_all_activities(group_id=123)

    mock_strava_client.return_value.fetch_activities.assert_not_called()


@patch("application.sync_activities.StravaClient")
@patch("application.sync_activities.StravaActivity")
@patch("application.sync_activities.StravaGroup")
def test_sync_refreshes_token_on_401(mock_group_repo, mock_activity_repo, mock_strava_client):
    mock_group_repo.return_value.get_group.return_value = _mock_group(membros={
        "user1": {"access_token": "expired_tok", "refresh_token": "ref1", "last_activity_date": None}
    })

    http_401 = HTTPError(response=MagicMock(status_code=401))
    mock_strava_client.return_value.fetch_activities.side_effect = [
        http_401,
        [{"id": "a1", "start_date_local": "2025-01-01T12:00:00Z"}],
    ]
    mock_strava_client.return_value.refresh_access_token.return_value = {
        "access_token": "new_tok",
        "refresh_token": "new_ref",
    }

    sync_all_activities(group_id=123)

    mock_strava_client.return_value.refresh_access_token.assert_called_once_with("ref1")
    assert mock_activity_repo.return_value.save_activity.call_count == 1


@patch("application.sync_activities.StravaClient")
@patch("application.sync_activities.StravaActivity")
@patch("application.sync_activities.StravaGroup")
def test_sync_raises_on_non_401_error(mock_group_repo, mock_activity_repo, mock_strava_client):
    mock_group_repo.return_value.get_group.return_value = _mock_group(membros={
        "user1": {"access_token": "tok", "refresh_token": "ref", "last_activity_date": None}
    })
    http_500 = HTTPError(response=MagicMock(status_code=500))
    mock_strava_client.return_value.fetch_activities.side_effect = http_500

    with pytest.raises(HTTPError):
        sync_all_activities(group_id=123)


@patch("application.sync_activities.StravaClient")
@patch("application.sync_activities.StravaActivity")
@patch("application.sync_activities.StravaGroup")
def test_sync_updates_last_activity_date(mock_group_repo, mock_activity_repo, mock_strava_client):
    group = _mock_group(membros={
        "user1": {"access_token": "tok1", "refresh_token": "ref1", "last_activity_date": None}
    })
    mock_group_repo.return_value.get_group.return_value = group
    mock_strava_client.return_value.fetch_activities.return_value = [
        {"id": "a1", "start_date_local": "2025-01-03T12:00:00Z"},
        {"id": "a2", "start_date_local": "2025-01-05T12:00:00Z"},
    ]

    sync_all_activities(group_id=123)

    assert group.membros["user1"]["last_activity_date"] == "2025-01-05T12:00:00Z"


@patch("application.sync_activities.StravaClient")
@patch("application.sync_activities.StravaActivity")
@patch("application.sync_activities.StravaGroup")
def test_sync_skips_member_with_no_activities(mock_group_repo, mock_activity_repo, mock_strava_client):
    group = _mock_group(membros={
        "user1": {"access_token": "tok1", "refresh_token": "ref1", "last_activity_date": None}
    })
    mock_group_repo.return_value.get_group.return_value = group
    mock_strava_client.return_value.fetch_activities.return_value = []

    sync_all_activities(group_id=123)

    mock_activity_repo.return_value.save_activity.assert_not_called()
    group.save.assert_called_once()
