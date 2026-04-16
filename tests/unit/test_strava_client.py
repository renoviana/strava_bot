import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from requests import HTTPError
from adapters.strava_client import StravaClient


def _mock_response(json_data, status_code=200, raise_for_status=None):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    if raise_for_status:
        mock.raise_for_status.side_effect = raise_for_status
    else:
        mock.raise_for_status.return_value = None
    return mock


@patch("adapters.strava_client.requests.get")
def test_fetch_activities_success(mock_get):
    mock_get.return_value = _mock_response([{"id": 1, "name": "Morning Run"}])

    client = StravaClient()
    result = client.fetch_activities("valid_token", datetime(2025, 8, 1))

    assert result == [{"id": 1, "name": "Morning Run"}]
    mock_get.assert_called_once()
    call_kwargs = mock_get.call_args
    assert call_kwargs[1]["headers"]["Authorization"] == "Bearer valid_token"


@patch("adapters.strava_client.requests.get")
def test_fetch_activities_passes_after_timestamp(mock_get):
    mock_get.return_value = _mock_response([])
    after = datetime(2025, 8, 1, 12, 0, 0)

    StravaClient().fetch_activities("token", after)

    params = mock_get.call_args[1]["params"]
    assert params["after"] == int(after.timestamp())
    assert params["per_page"] == 50


@patch("adapters.strava_client.requests.get")
def test_fetch_activities_raises_on_http_error(mock_get):
    mock_get.return_value = _mock_response(
        {}, status_code=401, raise_for_status=HTTPError(response=MagicMock(status_code=401))
    )

    with pytest.raises(HTTPError):
        StravaClient().fetch_activities("bad_token", datetime(2025, 8, 1))


@patch("adapters.strava_client.requests.post")
def test_refresh_access_token_success(mock_post):
    mock_post.return_value = _mock_response({
        "access_token": "new_access",
        "refresh_token": "new_refresh",
    })

    result = StravaClient().refresh_access_token("old_refresh")

    assert result["access_token"] == "new_access"
    assert result["refresh_token"] == "new_refresh"
    mock_post.assert_called_once()
    params = mock_post.call_args[1]["params"]
    assert params["grant_type"] == "refresh_token"
    assert params["refresh_token"] == "old_refresh"


@patch("adapters.strava_client.requests.post")
def test_refresh_access_token_raises_on_error(mock_post):
    mock_post.return_value = _mock_response(
        {}, status_code=400, raise_for_status=HTTPError(response=MagicMock(status_code=400))
    )

    with pytest.raises(HTTPError):
        StravaClient().refresh_access_token("bad_refresh")
