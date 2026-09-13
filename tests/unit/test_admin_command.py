from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from application.commands.admin import (
    handle_admin_callback,
    handle_admin_command,
    handle_reset_command,
)
from application.common import GRUPO_NAO_CADASTRADO
from tests.unit.conftest import make_group


def _repo(group=None, removido=None):
    repo = MagicMock()
    repo.get_group.return_value = group
    repo.remove_member.return_value = removido
    return repo


def test_admin_command_returns_member_list():
    result = handle_admin_command(123, repo=_repo(make_group()))
    assert ("Joao", 1) in result
    assert ("Maria", 2) in result


def test_admin_command_ignora_membro_sem_athlete_id():
    group = make_group(membros={"Joao": {"athlete_id": 1}, "Quebrado": {}})
    assert handle_admin_command(123, repo=_repo(group)) == [("Joao", 1)]


def test_admin_command_grupo_nao_cadastrado():
    assert handle_admin_command(123, repo=_repo(None)) is None


def test_admin_callback_removes_member():
    repo = _repo(removido="Joao")

    result = handle_admin_callback(123, member_id=1, autor_remocao="Admin", repo=repo)

    repo.remove_member.assert_called_once_with(123, 1)
    assert result == "Joao removido com sucesso por Admin."


def test_admin_callback_escapa_html():
    result = handle_admin_callback(123, 1, "<b>Ana</b>", repo=_repo(removido="João & Maria"))
    assert result == "João &amp; Maria removido com sucesso por &lt;b&gt;Ana&lt;/b&gt;."


def test_admin_callback_member_not_found():
    assert handle_admin_callback(123, member_id=999, autor_remocao="Admin", repo=_repo()) == "Membro não encontrado."


@patch("application.common.agora_brasilia", return_value=datetime(2026, 9, 12, 22, 0))
def test_reset_resincroniza_o_mes(_agora):
    sync = MagicMock(return_value=SimpleNamespace(falhas=[]))

    result = handle_reset_command(123, repo=_repo(make_group()), sync=sync)

    sync.assert_called_once_with(123, since=datetime(2026, 9, 1), force=True)
    assert result == "Atividades do mês re-sincronizadas."


def test_reset_avisa_quem_falhou():
    sync = MagicMock(return_value=SimpleNamespace(falhas=["Joao"]))
    result = handle_reset_command(123, repo=_repo(make_group()), sync=sync)
    assert "Não consegui sincronizar: Joao" in result


def test_reset_grupo_nao_cadastrado():
    sync = MagicMock()
    assert handle_reset_command(123, repo=_repo(None), sync=sync) == GRUPO_NAO_CADASTRADO
    sync.assert_not_called()
