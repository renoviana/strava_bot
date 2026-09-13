import logging

from application.common import GRUPO_NAO_CADASTRADO
from domain.services.medal_service import MedalService
from infrastructure.strava_repository import StravaRepository
from shared.rank import create_rank
from shared.user import get_user

logger = logging.getLogger(__name__)

EMOJI = {1: "🥇", 2: "🥈", 3: "🥉"}


def handle_medal_command(group_id: int, repo=None) -> str:
    """
    Placar acumulado de medalhas dos membros atuais.
    """
    repo = repo or StravaRepository()
    group = repo.get_group(group_id)
    if not group:
        return GRUPO_NAO_CADASTRADO

    logger.info("Calculando medalhas para grupo %s", group_id)
    medal_result = MedalService(group.medalhas or {}, group.membros or {}).calculate()
    if not medal_result:
        return "Nenhuma medalha conquistada"

    medalhas_list = []
    for athlete_id, medal_data in medal_result.items():
        if not get_user(group.membros, user_id=athlete_id):
            continue
        medalhas = " ".join(f"{EMOJI[posicao]}{medal_data[posicao]}" for posicao in (1, 2, 3))
        medalhas_list.append((athlete_id, f"{medalhas} | {medal_data['points']}pts"))

    return create_rank("Ranking de Medalhas", medalhas_list, group)
