from types import SimpleNamespace
from unittest.mock import patch

import pytest

from adapters.telegram import telegram_bot as tb

GRUPO = SimpleNamespace(id=-100, type="supergroup")
USUARIO = SimpleNamespace(id=7, first_name="Ana", username="ana")


def _msg(text, chat=GRUPO):
    return SimpleNamespace(text=text, chat=chat, from_user=USUARIO)


def _call(data, chat=GRUPO):
    return SimpleNamespace(id="cb1", data=data, message=SimpleNamespace(chat=chat), from_user=USUARIO)


@pytest.fixture
def api():
    with patch.object(tb.bot, "send_message") as send, \
            patch.object(tb.bot, "answer_callback_query") as answer, \
            patch.object(tb.bot, "get_chat_member") as member:
        member.return_value = SimpleNamespace(status="member")
        yield SimpleNamespace(send=send, answer=answer, member=member)


def _botoes(send):
    return [b.callback_data for linha in send.call_args.kwargs["reply_markup"].keyboard for b in linha]


@patch.object(tb, "handle_rank_menu", return_value=("Selecione o tipo de esporte:", ["Ride", "Run"]))
def test_rank_com_mencao_ao_bot(mock_menu, api):
    tb.rank_command_handler(_msg("/rank@strava_bot"))

    mock_menu.assert_called_once_with(-100, anual=False)
    assert _botoes(api.send) == ["rank_Ride", "rank_Run"]


@patch.object(tb, "handle_rank_menu", return_value=("Selecione o tipo de esporte:", ["Ride"]))
def test_yrank(mock_menu, api):
    tb.rank_command_handler(_msg("/yrank@strava_bot"))

    mock_menu.assert_called_once_with(-100, anual=True)
    assert _botoes(api.send) == ["yrank_Ride"]


@patch.object(tb, "handle_rank_menu", return_value=("Nenhuma atividade registrada este mês.", []))
def test_rank_sem_esportes_nao_manda_teclado_vazio(mock_menu, api):
    tb.rank_command_handler(_msg("/rank"))

    assert api.send.call_args.args == (-100, "Nenhuma atividade registrada este mês.")
    assert "reply_markup" not in api.send.call_args.kwargs


@patch.object(tb, "handle_rank_year_command", return_value="ranking")
def test_callback_yrank_responde_e_fecha_o_callback(mock_year, api):
    tb.rank_year_callback_handler(_call("yrank_MountainBikeRide"))

    mock_year.assert_called_once_with(-100, "MountainBikeRide")
    api.answer.assert_called_once_with("cb1")


@patch.object(tb, "handle_rank_month_command", return_value="ranking")
def test_callback_rank(mock_month, api):
    tb.rank_month_callback_handler(_call("rank_Ride"))
    mock_month.assert_called_once_with(-100, "Ride")


@patch.object(tb, "tratar_error")
@patch.object(tb, "handle_streak_command", side_effect=RuntimeError("mongo fora"))
def test_excecao_no_handler_nao_derruba_o_bot(mock_streak, mock_erro, api):
    tb.streak_command_handler(_msg("/streak"))

    mock_erro.assert_called_once()
    assert mock_erro.call_args.args[1] == "strava_bot"
    api.send.assert_called_once_with(-100, tb.MSG_ERRO)


@patch.object(tb, "tratar_error")
@patch.object(tb, "handle_rank_month_command", side_effect=RuntimeError("x"))
def test_excecao_em_callback_ainda_fecha_o_callback(mock_month, mock_erro, api):
    tb.rank_month_callback_handler(_call("rank_Ride"))
    api.answer.assert_called_once_with("cb1")


@patch.object(tb, "handle_admin_command")
def test_admin_exige_administrador(mock_admin, api):
    tb.admin_command_handler(_msg("/admin"))

    mock_admin.assert_not_called()
    assert api.send.call_args.args == (-100, tb.MSG_SEM_PERMISSAO)


@patch.object(tb, "handle_admin_command", return_value=[("Joao", 1)])
def test_admin_para_administrador(mock_admin, api):
    api.member.return_value = SimpleNamespace(status="creator")

    tb.admin_command_handler(_msg("/admin"))

    assert _botoes(api.send) == ["admin_1"]


@patch.object(tb, "handle_admin_command", return_value=None)
def test_admin_grupo_nao_cadastrado(mock_admin, api):
    api.member.return_value = SimpleNamespace(status="administrator")
    tb.admin_command_handler(_msg("/admin"))
    assert api.send.call_args.args == (-100, tb.GRUPO_NAO_CADASTRADO)


@patch.object(tb, "handle_admin_callback")
def test_admin_callback_exige_administrador(mock_callback, api):
    tb.admin_callback_handler(_call("admin_1"))
    mock_callback.assert_not_called()


@patch.object(tb, "handle_admin_callback", return_value="ok")
def test_admin_callback_administrador(mock_callback, api):
    api.member.return_value = SimpleNamespace(status="administrator")
    tb.admin_callback_handler(_call("admin_42"))
    mock_callback.assert_called_once_with(-100, 42, "Ana")


@patch.object(tb, "handle_reset_command", return_value="ok")
def test_reset_exige_administrador(mock_reset, api):
    tb.reset_command_handler(_msg("/reset"))
    mock_reset.assert_not_called()


@patch.object(tb, "handle_reset_command", return_value="ok")
def test_chat_privado_dispensa_checagem(mock_reset, api):
    tb.reset_command_handler(_msg("/reset", chat=SimpleNamespace(id=7, type="private")))

    mock_reset.assert_called_once_with(7)
    api.member.assert_not_called()
