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
    start = datetime.now() - timedelta(days=30)
    end = datetime.now()
    streak_service = StreakService(activity_repo.get_activities(group_id, start, end))
    streak_result = streak_service.calculate()

    return create_rank("Sequencia de dias ativos", streak_result, group)
