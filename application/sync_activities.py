import logging
from datetime import datetime, timedelta

from requests import HTTPError
from adapters.strava_client import StravaClient
from infrastructure.mongo.strava_activity import StravaActivity
from infrastructure.mongo.strava_group import StravaGroup

logger = logging.getLogger(__name__)


def sync_all_activities(group_id: int):
    group_repo = StravaGroup()
    activity_repo = StravaActivity()
    strava_client = StravaClient()
    group = group_repo.get_group(group_id)

    if not group:
        logger.warning("Grupo %s não encontrado, sync ignorado", group_id)
        return

    if group.last_sync and group.last_sync > datetime.now() - timedelta(minutes=1):
        logger.debug("Grupo %s sincronizado há menos de 1 minuto, ignorando", group_id)
        return

    logger.info("Iniciando sync do grupo %s (%d membros)", group_id, len(group.membros))

    for member_name, member_data in group.membros.items():
        after = member_data.get("last_activity_date")

        if not after:
            after = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0) - timedelta(days=1)

        try:
            activities = strava_client.fetch_activities(member_data["access_token"], after)
        except HTTPError as e:
            if e.response.status_code != 401:
                logger.error("Erro HTTP %s ao buscar atividades de %s", e.response.status_code, member_name)
                raise e
            logger.warning("Token expirado para %s, renovando...", member_name)
            response = strava_client.refresh_access_token(member_data["refresh_token"])
            member_data["access_token"] = response["access_token"]
            member_data["refresh_token"] = response["refresh_token"]
            group.membros[member_name] = member_data
            activities = strava_client.fetch_activities(member_data["access_token"], after)

        logger.info("Membro %s: %d atividades encontradas", member_name, len(activities))

        for activity in activities:
            activity_repo.save_activity(group_id, activity)

        if not activities:
            continue
        last_activity = activities[-1]
        member_data["last_activity_date"] = last_activity["start_date_local"]
        group.membros[member_name] = member_data
        group.last_sync = datetime.now()

    logger.info("Sync do grupo %s concluído", group_id)
    group.save()