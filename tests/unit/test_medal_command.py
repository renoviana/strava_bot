from unittest.mock import MagicMock

from application.commands.medal import handle_medal_command
from application.common import GRUPO_NAO_CADASTRADO
from tests.unit.conftest import make_group


def _repo(group):
    repo = MagicMock()
    repo.get_group.return_value = group
    return repo


def test_grupo_nao_cadastrado():
    assert handle_medal_command(123, repo=_repo(None)) == GRUPO_NAO_CADASTRADO


def test_sem_medalhas():
    assert handle_medal_command(123, repo=_repo(make_group(medalhas={}))) == "Nenhuma medalha conquistada"


def test_formata_e_aceita_chave_por_id_e_por_nome():
    group = make_group(medalhas={
        "7_2026": {"Ride": {"Joao": 1, "Maria": 2}},  # legado: por nome
        "8_2026": {"Ride": {"1": 1}, "Run": {"2": 1}},  # atual: por athlete_id
    })

    result = handle_medal_command(123, repo=_repo(group))

    linhas = result.splitlines()
    assert linhas[0] == "Ranking de Medalhas"
    assert "Joao" in linhas[1] and linhas[1].endswith("🥇2 🥈0 🥉0 | 6pts")
    assert "Maria" in linhas[2] and linhas[2].endswith("🥇1 🥈1 🥉0 | 5pts")


def test_ex_membro_fica_de_fora():
    group = make_group(medalhas={"8_2026": {"Ride": {"999": 1, "Ex Membro": 1, "1": 2}}})

    result = handle_medal_command(123, repo=_repo(group))

    assert len(result.splitlines()) == 2
    assert "Joao" in result
