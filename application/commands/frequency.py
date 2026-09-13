import logging

from application.common import GRUPO_NAO_CADASTRADO, Periodo, periodo_ano, periodo_mes
from application.sync_activities import sync_all_activities
from domain.services.frequency_service import FrequencyService
from infrastructure.strava_repository import StravaRepository
from shared.rank import create_rank

logger = logging.getLogger(__name__)


def handle_frequency_command(group_id: int, periodo: Periodo, repo=None, sync=None) -> str:
    """
    Ranking de dias com atividade no período ("dias ativos/dias decorridos").
    """
    repo = repo or StravaRepository()
    group = repo.get_group(group_id)
    if not group:
        return GRUPO_NAO_CADASTRADO

    (sync or sync_all_activities)(group_id)
    activities = repo.list_activities(group_id, periodo.inicio, periodo.fim)
    logger.info("Calculando frequência para grupo %s (%d atividades)", group_id, len(activities))
    freq_result = FrequencyService(activities).calculate()

    if not freq_result:
        return f"Nenhuma atividade registrada {periodo.referencia}."

    freq_result_rank = [(user_id, f"{days}/{periodo.dias_decorridos}") for user_id, days in freq_result]
    return create_rank(f"Ranking de Frequência - {periodo.titulo}", freq_result_rank, group)


def handle_month_frequency_command(group_id: int) -> str:
    return handle_frequency_command(group_id, periodo_mes())


def handle_year_frequency_command(group_id: int) -> str:
    return handle_frequency_command(group_id, periodo_ano())
