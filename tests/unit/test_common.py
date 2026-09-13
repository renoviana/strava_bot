from datetime import datetime
from unittest.mock import patch

from application.common import periodo_ano, periodo_mes


def test_periodo_mes():
    p = periodo_mes(datetime(2026, 9, 12, 21, 0))
    assert (p.inicio, p.fim) == (datetime(2026, 9, 1), datetime(2026, 10, 1))
    assert p.titulo == "Setembro/2026"
    assert p.referencia == "este mês"
    assert p.dias_decorridos == 12


def test_periodo_mes_dezembro_vira_o_ano():
    p = periodo_mes(datetime(2026, 12, 31))
    assert p.fim == datetime(2027, 1, 1)
    assert p.titulo == "Dezembro/2026"


def test_periodo_ano():
    p = periodo_ano(datetime(2026, 9, 12))
    assert (p.inicio, p.fim) == (datetime(2026, 1, 1), datetime(2027, 1, 1))
    assert p.titulo == "2026"
    assert p.referencia == "este ano"
    assert p.dias_decorridos == 255


@patch("application.common.agora_brasilia", return_value=datetime(2026, 1, 31, 23, 0))
def test_padrao_usa_horario_de_brasilia(_agora):
    assert periodo_mes().titulo == "Janeiro/2026"
    assert periodo_ano().titulo == "2026"
