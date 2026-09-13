import logging
from typing import List, Tuple

from application.common import GRUPO_NAO_CADASTRADO, Periodo, periodo_ano, periodo_mes
from application.sync_activities import sync_all_activities
from assistant_util.strava import rank_metric
from domain.services.rank_service import RankService
from infrastructure.strava_repository import StravaRepository
from shared.rank import create_rank

logger = logging.getLogger(__name__)


def convert_rank_to_km(rank: float) -> str:
    return f"{rank / 1000:.2f}km"


def convert_rank_to_hour_minute_seconds(seconds: int) -> str:
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def convert_rank(rank: float, metric: str) -> str:
    if metric == "moving_time":
        return convert_rank_to_hour_minute_seconds(rank)
    return convert_rank_to_km(rank)


def handle_rank_command(group_id: int, sport_type: str, periodo: Periodo, repo=None, sync=None) -> str:
    """
    Ranking de um esporte no período.

    Args:
        group_id (int): grupo do Telegram
        sport_type (str): esporte do Strava
        periodo (Periodo): mês ou ano de referência (o título vem dele)
    """
    repo = repo or StravaRepository()
    group = repo.get_group(group_id)
    if not group:
        return GRUPO_NAO_CADASTRADO

    (sync or sync_all_activities)(group_id)
    activities = repo.list_activities(group_id, periodo.inicio, periodo.fim)
    metric = rank_metric(sport_type)
    logger.info("Calculando rank de %s para grupo %s (%d atividades)", sport_type, group_id, len(activities))
    rank_result = RankService(activities).calculate(sport_type, metric)

    if not rank_result:
        return f"Nenhuma atividade de {sport_type} registrada {periodo.referencia}."

    return create_rank(
        f"Ranking de {sport_type} - {periodo.titulo}",
        [(user_id, convert_rank(valor, metric)) for user_id, valor in rank_result],
        group,
        sport_type=sport_type,
    )


def handle_rank_month_command(group_id: int, sport_type: str) -> str:
    return handle_rank_command(group_id, sport_type, periodo_mes())


def handle_rank_year_command(group_id: int, sport_type: str) -> str:
    return handle_rank_command(group_id, sport_type, periodo_ano())


def handle_rank_menu(group_id: int, anual: bool = False, repo=None, sync=None) -> Tuple[str, List[str]]:
    """
    Texto e esportes do menu de ranking.

    Returns:
        (str, list[str]): a mensagem e os esportes com atividade no período;
        lista vazia quando não há o que escolher (a mensagem explica o motivo)
    """
    repo = repo or StravaRepository()
    if not repo.get_group(group_id):
        return GRUPO_NAO_CADASTRADO, []

    (sync or sync_all_activities)(group_id)
    periodo = periodo_ano() if anual else periodo_mes()
    esportes = repo.list_sports(group_id, periodo.inicio, periodo.fim)
    if not esportes:
        return f"Nenhuma atividade registrada {periodo.referencia}.", []
    return "Selecione o tipo de esporte:", esportes
