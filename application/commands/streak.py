from datetime import datetime, timedelta

from application.sync_activities import sync_all_activities
from domain.services.streak_service import StreakService
from infrastructure.mongo.strava_activity import StravaActivity
from infrastructure.mongo.strava_group import StravaGroup
from shared.rank import create_rank

def handle_streak_command(group_id: int) -> str:
    activity_repo = StravaActivity()
    group_repo = StravaGroup()
    group = group_repo.get_group(group_id)
    sync_all_activities(group_id)

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    last_60_days = today - timedelta(days=60)

    today_activity_list = activity_repo.get_activities(group_id, today, tomorrow)
    today_athlete_id_list = list(set(map(lambda x: x["athlete"]["id"], today_activity_list)))

    if not today_athlete_id_list:
        return "Ninguem fez atividade hoje"

    activity_list = activity_repo.get_activities(
        group_id,
        last_60_days,
        today,
        member_id_list=today_athlete_id_list
    )

    streak_service = StreakService(activity_list)
    streak_result = streak_service.calculate()

    return create_rank("Sequencia de dias ativos", streak_result, group)
