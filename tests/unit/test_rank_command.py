from datetime import datetime
from unittest.mock import MagicMock, patch

from application.commands.rank import (
    convert_rank,
    convert_rank_to_hour_minute_seconds,
    convert_rank_to_km,
    handle_rank_command,
    handle_rank_menu,
    handle_rank_month_command,
    handle_rank_year_command,
)
from application.common import GRUPO_NAO_CADASTRADO, periodo_ano, periodo_mes
from tests.unit.conftest import MockActivity, make_group

ANO = periodo_ano(datetime(2026, 9, 12))
MES = periodo_mes(datetime(2026, 9, 12))


def _repo(group=None, activities=(), sports=()):
    repo = MagicMock()
    repo.get_group.return_value = group
    repo.list_activities.return_value = list(activities)
    repo.list_sports.return_value = list(sports)
    return repo


def test_convert_rank_to_km():
    assert convert_rank_to_km(1000) == "1.00km"
    assert convert_rank_to_km(5500) == "5.50km"
    assert convert_rank_to_km(0) == "0.00km"


def test_convert_rank_to_hour_minute_seconds():
    assert convert_rank_to_hour_minute_seconds(3661) == "01:01:01"
    assert convert_rank_to_hour_minute_seconds(3600) == "01:00:00"
    assert convert_rank_to_hour_minute_seconds(60) == "00:01:00"
    assert convert_rank_to_hour_minute_seconds(0) == "00:00:00"
    assert convert_rank_to_hour_minute_seconds(40 * 3600) == "40:00:00"


def test_convert_rank_dispatch():
    assert convert_rank(10000, "distance") == "10.00km"
    assert convert_rank(3600, "moving_time") == "01:00:00"


def test_rank_grupo_nao_cadastrado():
    sync = MagicMock()
    assert handle_rank_command(123, "Run", MES, repo=_repo(None), sync=sync) == GRUPO_NAO_CADASTRADO
    sync.assert_not_called()


def test_rank_sem_atividades_anual_fala_do_ano():
    result = handle_rank_command(123, "Run", ANO, repo=_repo(make_group()), sync=MagicMock())
    assert result == "Nenhuma atividade de Run registrada este ano."


def test_rank_anual_tem_o_ano_no_titulo_e_nao_o_mes():
    repo = _repo(make_group(), [MockActivity(1, "2026-03-01T10:00:00", sport_type="Run", distance=10000)])
    sync = MagicMock()

    result = handle_rank_command(123, "Run", ANO, repo=repo, sync=sync)

    assert result.splitlines()[0] == "Ranking de Run - 2026"
    assert "Setembro" not in result
    assert "10.00km" in result
    sync.assert_called_once_with(123)
    repo.list_activities.assert_called_once_with(123, datetime(2026, 1, 1), datetime(2027, 1, 1))


def test_rank_mensal_titulo():
    repo = _repo(make_group(), [MockActivity(1, "2026-09-01T10:00:00", sport_type="Run", distance=10000)])
    result = handle_rank_command(123, "Run", MES, repo=repo, sync=MagicMock())
    assert result.splitlines()[0] == "Ranking de Run - Setembro/2026"


def test_rank_por_tempo_para_esporte_sem_distancia():
    repo = _repo(make_group(), [MockActivity(1, "2026-09-01T10:00:00", sport_type="Soccer", moving_time=5400)])
    result = handle_rank_command(123, "Soccer", MES, repo=repo, sync=MagicMock())
    assert "01:30:00" in result


@patch("application.commands.rank.handle_rank_command", return_value="ok")
@patch("application.common.agora_brasilia", return_value=datetime(2026, 9, 12, 22, 0))
def test_month_e_year_passam_o_periodo(_agora, mock_handle):
    handle_rank_month_command(123, "Run")
    assert mock_handle.call_args.args[2].titulo == "Setembro/2026"

    handle_rank_year_command(123, "Run")
    assert mock_handle.call_args.args[2].titulo == "2026"


def test_menu_grupo_nao_cadastrado():
    assert handle_rank_menu(123, repo=_repo(None), sync=MagicMock()) == (GRUPO_NAO_CADASTRADO, [])


@patch("application.common.agora_brasilia", return_value=datetime(2026, 9, 12))
def test_menu_sem_atividades(_agora):
    texto, esportes = handle_rank_menu(123, anual=True, repo=_repo(make_group()), sync=MagicMock())
    assert esportes == []
    assert texto == "Nenhuma atividade registrada este ano."


@patch("application.common.agora_brasilia", return_value=datetime(2026, 9, 12))
def test_menu_com_esportes(_agora):
    repo = _repo(make_group(), sports=["Ride", "Run"])
    texto, esportes = handle_rank_menu(123, repo=repo, sync=MagicMock())
    assert esportes == ["Ride", "Run"]
    assert texto == "Selecione o tipo de esporte:"
    repo.list_sports.assert_called_once_with(123, datetime(2026, 9, 1), datetime(2026, 10, 1))
