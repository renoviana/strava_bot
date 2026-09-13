from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from application.sync_activities import sync_all_activities
from assistant_util.strava import agora_utc


def _repo(last_sync=None, existe=True):
    repo = MagicMock()
    repo.get_group.return_value = SimpleNamespace(last_sync=last_sync) if existe else None
    return repo


@patch("application.sync_activities.sync_group")
def test_grupo_inexistente(mock_sync):
    assert sync_all_activities(123, repo=_repo(existe=False)) is None
    mock_sync.assert_not_called()


@patch("application.sync_activities.sync_group")
def test_pula_se_sincronizou_ha_menos_de_1_minuto(mock_sync):
    assert sync_all_activities(123, repo=_repo(agora_utc() - timedelta(seconds=30))) is None
    mock_sync.assert_not_called()


@patch("application.sync_activities.sync_group", return_value="resultado")
def test_force_ignora_o_intervalo(mock_sync):
    client = MagicMock()
    since = datetime(2026, 9, 1)

    result = sync_all_activities(123, since=since, force=True, repo=_repo(agora_utc()), client=client)

    assert result == "resultado"
    mock_sync.assert_called_once_with(123, client, since=since, origem="strava_bot")


@patch("application.sync_activities.sync_group")
def test_sincroniza_quando_passou_o_intervalo(mock_sync):
    sync_all_activities(123, repo=_repo(agora_utc() - timedelta(minutes=5)), client=MagicMock())
    mock_sync.assert_called_once()


@patch("application.sync_activities.sync_group")
def test_sincroniza_sem_last_sync(mock_sync):
    sync_all_activities(123, repo=_repo(None), client=MagicMock())
    mock_sync.assert_called_once()
