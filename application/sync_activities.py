"""
Caso de uso de sync do bot: limite de frequência + o sync compartilhado.

O sync em si (janela de 7 dias, paginação, upsert, token) é o
`assistant_util.strava.sync_group`, o mesmo usado pelo strava_schedule.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from assistant_util.strava import StravaClient, SyncResult, agora_utc, sync_group
from config import STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET
from infrastructure.strava_repository import StravaRepository

logger = logging.getLogger(__name__)

#: Intervalo mínimo entre syncs do mesmo grupo disparados por comando.
INTERVALO_MINIMO = timedelta(minutes=1)


def sync_all_activities(
    group_id: int,
    since: Optional[datetime] = None,
    force: bool = False,
    repo: Optional[StravaRepository] = None,
    client: Optional[StravaClient] = None,
) -> Optional[SyncResult]:
    """
    Sincroniza o grupo, respeitando o intervalo mínimo entre syncs.

    Args:
        group_id (int): grupo do Telegram
        since (datetime | None): rebusca desde esta data (Brasília), além da janela padrão
        force (bool): ignora o intervalo mínimo
        repo, client: dependências (injetáveis nos testes)

    Returns:
        SyncResult | None: None se o grupo não existe ou o sync foi pulado
    """
    repo = repo or StravaRepository()
    group = repo.get_group(group_id)
    if not group:
        logger.warning("Grupo %s não encontrado, sync ignorado", group_id)
        return None

    if not force and group.last_sync and group.last_sync > agora_utc() - INTERVALO_MINIMO:
        logger.debug("Grupo %s sincronizado há menos de 1 minuto, ignorando", group_id)
        return None

    client = client or StravaClient(STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET)
    return sync_group(group_id, client, since=since, origem="strava_bot")
