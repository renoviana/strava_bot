from datetime import datetime

from application.sync_activities import sync_all_activities
from domain.services.rank_service import RankService
from infrastructure.mongo.strava_activity import StravaActivity
from infrastructure.mongo.strava_group import StravaGroup
from shared.rank import create_rank

def handle_rank_command(group_id: int, sport_type: str, start: datetime, end: datetime) -> str:
    now = datetime.now()
    activity_repo = StravaActivity()
    group_repo = StravaGroup()
    group = group_repo.get_group(group_id)

    sync_all_activities(group_id)
    activities = activity_repo.get_activities(group_id, start, end)
    service = RankService(activities)
    rank_result = service.calculate(sport_type)

    if not rank_result:
        return "Nenhuma atividade registrada este mês."

    return create_rank(
        f"Ranking de {sport_type} - {now.strftime('%B')}",
        [(user_id, convert_rank(rank, service.get_rank_type())) for user_id, rank in rank_result],
        group,
        sport_type=sport_type
    )


def convert_rank_to_km(rank: int) -> str:
    return f"{rank / 1000:.2f}km"

def convert_rank_to_hour_minute_seconds(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours}:{minutes}:{seconds}"

def convert_rank(rank: int, rank_params: str) -> str     :
    if rank_params == "moving_time":
        return convert_rank_to_hour_minute_seconds(rank)
    return convert_rank_to_km(rank)

def handle_rank_year_command(group_id: int, sport_type: str) -> str:
    now = datetime.now()
    start = datetime(now.year, 1, 1)
    end = datetime(now.year + 1, 1, 1)
    return handle_rank_command(group_id, sport_type, start, end)

def handle_rank_month_command(group_id: int, sport_type: str) -> str:
    now = datetime.now()
    start = datetime(now.year, now.month, 1)
    if now.month == 12:
        end = datetime(now.year + 1, 1, 1)
    else:
        end = datetime(now.year, now.month + 1, 1)
    return handle_rank_command(group_id, sport_type, start, end)

def handle_rank_menu(group_id: int, start: datetime, end: datetime) -> list:
    sync_all_activities(group_id)
    activity_repo = StravaActivity()
    return activity_repo.list_sports(group_id, start, end)