"""
Peças compartilhadas pelos comandos: período de referência e mensagens.

O período é calculado aqui, e não no adapter, e sempre no horário de
Brasília: o container roda em UTC, e `datetime.now()` cru virava o dia e o
mês 3h antes.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from assistant_util.strava import agora_brasilia

GRUPO_NAO_CADASTRADO = "Grupo não cadastrado. Use /link para conectar o Strava."

#: Nomes fixos: `strftime('%B')` depende do locale e saía em inglês no container.
MESES = (
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
)


@dataclass(frozen=True)
class Periodo:
    """Janela [inicio, fim) de um ranking, em hora local (Brasília)."""

    inicio: datetime
    fim: datetime
    titulo: str  # "Setembro/2026" ou "2026"
    referencia: str  # "este mês" ou "este ano"
    dias_decorridos: int  # denominador da frequência


def periodo_mes(ref: Optional[datetime] = None) -> Periodo:
    """Mês corrente (ou o mês de `ref`)."""
    ref = ref or agora_brasilia()
    inicio = datetime(ref.year, ref.month, 1)
    fim = datetime(ref.year + 1, 1, 1) if ref.month == 12 else datetime(ref.year, ref.month + 1, 1)
    return Periodo(inicio, fim, f"{MESES[ref.month - 1]}/{ref.year}", "este mês", ref.day)


def periodo_ano(ref: Optional[datetime] = None) -> Periodo:
    """Ano corrente (ou o ano de `ref`)."""
    ref = ref or agora_brasilia()
    return Periodo(
        datetime(ref.year, 1, 1),
        datetime(ref.year + 1, 1, 1),
        str(ref.year),
        "este ano",
        ref.timetuple().tm_yday,
    )
