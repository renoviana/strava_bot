import logging
from datetime import date, datetime, time, timedelta
from typing import Optional

from application.common import GRUPO_NAO_CADASTRADO
from application.sync_activities import sync_all_activities
from assistant_util.strava import agora_brasilia
from domain.services.streak_service import StreakService
from infrastructure.strava_repository import StravaRepository
from shared.rank import create_rank

logger = logging.getLogger(__name__)

#: Até quantos dias para trás a sequência é contada.
JANELA_DIAS = 365


def handle_streak_command(group_id: int, repo=None, sync=None, hoje: Optional[date] = None) -> str:
    """
    Sequência de dias seguidos com atividade, de hoje para trás, de quem treinou hoje.
    """
    repo = repo or StravaRepository()
    group = repo.get_group(group_id)
    if not group:
        return GRUPO_NAO_CADASTRADO

    (sync or sync_all_activities)(group_id)

    hoje = hoje or agora_brasilia().date()
    inicio_hoje = datetime.combine(hoje, time.min)
    amanha = inicio_hoje + timedelta(days=1)

    ativos_hoje = sorted({act.athlete.id for act in repo.list_activities(group_id, inicio_hoje, amanha)})
    if not ativos_hoje:
        logger.info("Nenhuma atividade hoje para grupo %s", group_id)
        return "Ninguém fez atividade hoje"

    # A janela vai até amanhã: o dia de hoje precisa estar nos dados, é dele
    # que a contagem parte.
    activity_list = repo.list_activities(
        group_id, inicio_hoje - timedelta(days=JANELA_DIAS), amanha, athlete_ids=ativos_hoje
    )

    logger.info("Calculando streak para %d membros ativos no grupo %s", len(ativos_hoje), group_id)
    streak_result = StreakService(activity_list, today=hoje).calculate()
    return create_rank("Sequência de dias ativos", streak_result, group)
