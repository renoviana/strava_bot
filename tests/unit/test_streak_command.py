from datetime import date, datetime, timedelta
from unittest.mock import MagicMock

from application.commands.streak import JANELA_DIAS, handle_streak_command
from application.common import GRUPO_NAO_CADASTRADO
from tests.unit.conftest import MockActivity, make_group

HOJE = date(2026, 9, 12)


def _repo_com(activities, group=None):
    """Repo que filtra de verdade por período e atletas, como o banco."""
    def list_activities(group_id, start, end, athlete_ids=None):
        return [
            a for a in activities
            if start <= a["start_date_local"] < end and (not athlete_ids or a.athlete.id in athlete_ids)
        ]

    repo = MagicMock()
    repo.get_group.return_value = group or make_group()
    repo.list_activities.side_effect = list_activities
    return repo


def _act(athlete_id, dias_atras):
    return MockActivity(athlete_id, datetime(2026, 9, 12, 8, 0) - timedelta(days=dias_atras))


def test_grupo_nao_cadastrado():
    repo = MagicMock()
    repo.get_group.return_value = None
    assert handle_streak_command(123, repo=repo, sync=MagicMock(), hoje=HOJE) == GRUPO_NAO_CADASTRADO


def test_ninguem_treinou_hoje():
    repo = _repo_com([_act(1, 1)])
    assert handle_streak_command(123, repo=repo, sync=MagicMock(), hoje=HOJE) == "Ninguém fez atividade hoje"


def test_regressao_streak_conta_o_dia_de_hoje():
    # Bug antigo: a busca terminava em "hoje" (exclusivo), o dia de hoje nunca
    # entrava nos dados e todo mundo ficava com streak 0 -> ranking vazio.
    repo = _repo_com([_act(1, 0), _act(1, 1), _act(1, 2), _act(2, 0), _act(3, 1)])

    result = handle_streak_command(123, repo=repo, sync=MagicMock(), hoje=HOJE)

    linhas = result.splitlines()
    assert linhas[0] == "Sequência de dias ativos"
    assert linhas[1].startswith("1º") and "Joao" in linhas[1] and linhas[1].endswith(" - 3")
    assert linhas[2].startswith("2º") and "Maria" in linhas[2] and linhas[2].endswith(" - 1")
    assert len(linhas) == 3  # o atleta 3 não treinou hoje


def test_janela_vai_ate_amanha_e_filtra_quem_treinou_hoje():
    repo = _repo_com([_act(1, 0)])

    handle_streak_command(123, repo=repo, sync=MagicMock(), hoje=HOJE)

    args = repo.list_activities.call_args_list[1]
    assert args.args[1] == datetime(2026, 9, 12) - timedelta(days=JANELA_DIAS)
    assert args.args[2] == datetime(2026, 9, 13)
    assert args.kwargs["athlete_ids"] == [1]
