from unittest.mock import MagicMock

from shared.rank import create_rank, get_medalhas, get_user_link

MEMBROS = {
    "Joao": {"athlete_id": 1, "access_token": "t", "refresh_token": "r"},
    "Maria": {"athlete_id": 2, "access_token": "t", "refresh_token": "r"},
    "Pedro & <Filho>": {"athlete_id": 3, "access_token": "t", "refresh_token": "r"},
}


def _group_with_medalhas(medalhas):
    group = MagicMock()
    group.membros = MEMBROS
    group.medalhas = medalhas
    return group


def test_create_rank_basic():
    result = create_rank("Titulo", [(1, "10.0km"), (2, "8.0km")], _group_with_medalhas({}))
    assert "Titulo" in result
    assert "1º" in result
    assert "2º" in result
    assert "10.0km" in result


def test_create_rank_tie_same_position():
    result = create_rank("Titulo", [(1, "10km"), (2, "10km")], _group_with_medalhas({}))
    assert result.count("1º") == 2
    assert "2º" not in result


def test_create_rank_increments_position_after_tie():
    result = create_rank("Titulo", [(1, "10km"), (2, "10km"), (3, "5km")], _group_with_medalhas({}))
    assert result.count("1º") == 2
    assert "2º" in result


def test_create_rank_primeiro_valor_zero_nao_vira_0o():
    result = create_rank("Titulo", [(1, 0)], _group_with_medalhas({}))
    assert result.splitlines()[1].startswith("1º")


def test_get_user_link_contains_athlete_id():
    link = get_user_link(1, MEMBROS)
    assert "strava.com/athletes/1" in link
    assert "Joao" in link


def test_get_user_link_escapa_o_nome():
    assert ">Pedro &amp; &lt;Filho&gt;</a>" in get_user_link(3, MEMBROS)


def test_get_user_link_membro_ausente_nao_quebra():
    assert get_user_link(999, MEMBROS) == "Atleta 999"


def test_get_medalhas_no_sport_type():
    assert get_medalhas(1, _group_with_medalhas({"1_2025": {"Run": {"Joao": 1}}}), sport_type=None) == ""


def test_get_medalhas_por_nome_legado_e_por_id():
    group = _group_with_medalhas({
        "1_2025": {"Run": {"Joao": 1}},
        "2_2025": {"Run": {"1": 2}},
        "3_2025": {"Run": {"1": 1}},
    })
    assert get_medalhas(1, group, sport_type="Run") == "🥇2🥈1"


def test_get_medalhas_no_medals_for_user():
    assert get_medalhas(1, _group_with_medalhas({"1_2025": {"Run": {"Maria": 1}}}), sport_type="Run") == ""
