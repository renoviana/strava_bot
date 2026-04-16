from unittest.mock import patch, MagicMock
from datetime import datetime
from application.commands.admin import (
    handle_admin_command,
    handle_admin_callback,
    handle_reset_command,
)
from tests.unit.conftest import make_group


@patch("application.commands.admin.StravaGroup")
def test_admin_command_returns_member_list(mock_group_repo):
    group = make_group()
    mock_group_repo.return_value.get_group.return_value = group

    result = handle_admin_command(123)

    assert ("Joao", 1) in result
    assert ("Maria", 2) in result


@patch("application.commands.admin.StravaActivity")
@patch("application.commands.admin.StravaGroup")
def test_admin_callback_removes_member(mock_group_repo, mock_activity_repo):
    group = make_group(
        membros={"Joao": {"athlete_id": 1, "access_token": "t", "refresh_token": "r", "last_activity_date": None}},
        medalhas={"2025-01": {"Run": {"Joao": 1}}}
    )
    mock_group_repo.return_value.get_group.return_value = group

    result = handle_admin_callback(123, member_id=1, autor_remocao="Admin")

    assert "Joao" not in group.membros
    assert "Joao" not in group.medalhas["2025-01"]["Run"]
    assert "removido com sucesso" in result
    mock_activity_repo.return_value.remove_activity_member.assert_called_once_with(123, 1)
    group.save.assert_called_once()


@patch("application.commands.admin.StravaActivity")
@patch("application.commands.admin.StravaGroup")
def test_admin_callback_member_not_found(mock_group_repo, mock_activity_repo):
    group = make_group()
    mock_group_repo.return_value.get_group.return_value = group

    result = handle_admin_callback(123, member_id=999, autor_remocao="Admin")

    assert "não encontrado" in result.lower() or "nao encontrado" in result.lower()
    mock_activity_repo.return_value.remove_activity_member.assert_not_called()


@patch("application.commands.admin.StravaGroup")
def test_reset_command_sets_first_of_month(mock_group_repo):
    group = make_group()
    mock_group_repo.return_value.get_group.return_value = group

    result = handle_reset_command(123)

    now = datetime.now()
    for member_data in group.membros.values():
        reset_date = member_data["last_activity_date"]
        assert reset_date.day == 1
        assert reset_date.month == now.month
        assert reset_date.year == now.year

    assert "sucesso" in result.lower()
    group.save.assert_called_once()
