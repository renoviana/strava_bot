from datetime import datetime
from unittest.mock import MagicMock, patch

from application.commands.frequency import (
    handle_frequency_command,
    handle_month_frequency_command,
    handle_year_frequency_command,
)
from application.common import GRUPO_NAO_CADASTRADO, periodo_ano, periodo_mes
from tests.unit.conftest import MockActivity, make_group


def _repo(group=None, activities=()):
    repo = MagicMock()
    repo.get_group.return_value = group
    repo.list_activities.return_value = list(activities)
    return repo


def test_grupo_nao_cadastrado():
    result = handle_frequency_command(123, periodo_mes(datetime(2026, 9, 12)), repo=_repo(None), sync=MagicMock())
    assert result == GRUPO_NAO_CADASTRADO


def test_mensal_dias_sobre_dia_do_mes():
    repo = _repo(make_group(), [
        MockActivity(1, datetime(2026, 9, 1)),
        MockActivity(1, datetime(2026, 9, 2)),
        MockActivity(2, datetime(2026, 9, 1)),
    ])

    result = handle_frequency_command(123, periodo_mes(datetime(2026, 9, 12)), repo=repo, sync=MagicMock())

    linhas = result.splitlines()
    assert linhas[0] == "Ranking de Frequência - Setembro/2026"
    assert linhas[1].endswith("2/12")
    assert linhas[2].endswith("1/12")


def test_anual_dias_sobre_dia_do_ano():
    repo = _repo(make_group(), [MockActivity(1, datetime(2026, 9, 1))])
    result = handle_frequency_command(123, periodo_ano(datetime(2026, 9, 12)), repo=repo, sync=MagicMock())
    assert result.splitlines()[0] == "Ranking de Frequência - 2026"
    assert result.splitlines()[1].endswith("1/255")


def test_anual_sem_atividades_fala_do_ano():
    result = handle_frequency_command(123, periodo_ano(datetime(2026, 9, 12)), repo=_repo(make_group()),
                                      sync=MagicMock())
    assert result == "Nenhuma atividade registrada este ano."


@patch("application.commands.frequency.handle_frequency_command", return_value="ok")
@patch("application.common.agora_brasilia", return_value=datetime(2026, 9, 12))
def test_atalhos(_agora, mock_handle):
    handle_month_frequency_command(1)
    assert mock_handle.call_args.args[1].titulo == "Setembro/2026"
    handle_year_frequency_command(1)
    assert mock_handle.call_args.args[1].titulo == "2026"
