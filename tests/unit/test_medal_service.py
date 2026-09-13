from domain.services.medal_service import MedalService

MEMBROS = {"Joao": {"athlete_id": 1}, "Maria": {"athlete_id": 2}, "Pedro": {"athlete_id": 3}}


def _calc(medalhas, membros=MEMBROS):
    return MedalService(medalhas, membros).calculate()


def test_medal_counts_and_points():
    result = _calc({"8_2026": {"Run": {"1": 1, "2": 2, "3": 3}}})
    assert result[1] == {1: 1, 2: 0, 3: 0, "points": 3}
    assert result[2] == {1: 0, 2: 1, 3: 0, "points": 2}
    assert result[3] == {1: 0, 2: 0, 3: 1, "points": 1}


def test_medal_legado_por_nome_vira_athlete_id():
    result = _calc({"1_2025": {"Run": {"Joao": 1}}, "8_2026": {"Run": {"1": 1}}})
    assert result == {1: {1: 2, 2: 0, 3: 0, "points": 6}}


def test_medal_nome_de_ex_membro_fica_de_fora():
    assert _calc({"1_2025": {"Run": {"Ex Membro": 1}}}) == {}


def test_medal_chave_int():
    assert _calc({"1_2025": {"Run": {1: 1}}})[1]["points"] == 3


def test_medal_posicao_invalida_e_ignorada():
    result = _calc({"1_2025": {"Run": {"1": 4, "2": "x", "3": None, "Joao": "2"}}})
    assert result == {1: {1: 0, 2: 1, 3: 0, "points": 2}}


def test_medal_sorted_by_points_descending():
    result = _calc({"1_2025": {"Run": {"1": 1}}, "2_2025": {"Run": {"1": 1, "2": 2}}})
    assert list(result) == [1, 2]


def test_medal_accumulates_across_sports():
    result = _calc({"1_2025": {"Run": {"1": 1}, "Ride": {"1": 2}}})
    assert result[1] == {1: 1, 2: 1, 3: 0, "points": 5}


def test_medal_empty_medalhas():
    assert _calc({}) == {}
