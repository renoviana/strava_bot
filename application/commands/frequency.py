from datetime import datetime

from application.sync_activities import sync_all_activities
from domain.services.frequency_service import FrequencyService
from infrastructure.mongo.strava_activity import StravaActivity
from infrastructure.mongo.strava_group import StravaGroup
from shared.rank import create_rank

def handle_frequency_command(group_id: int, start:datetime, end:datetime) -> list:
    activity_repo = StravaActivity()
    sync_all_activities(group_id)
    activities = activity_repo.get_activities(group_id, start, end)
    service = FrequencyService(activities)
    return service.calculate()

def handle_year_frequency_command(group_id: int) -> str:
    group_repo = StravaGroup()
    group = group_repo.get_group(group_id)
    now = datetime.now()
    start = datetime(now.year, 1, 1)
    end = datetime(now.year + 1, 1, 1)
    freq_result = handle_frequency_command(group_id, start, end)
    freq_result_rank = []

    for (user_id, days) in freq_result:
        freq_result_rank.append((user_id, f"{days}/{now.timetuple().tm_yday}"))
    if not freq_result_rank:
        return "Nenhuma atividade registrada este mês."

    return create_rank(f"Ranking de Frequência - {now.year}", freq_result_rank, group)

def handle_month_frequency_command(group_id: int) -> str:
    group_repo = StravaGroup()
    group = group_repo.get_group(group_id)
    now = datetime.now()
    start = datetime(now.year, now.month, 1)
    if now.month == 12:
        end = datetime(now.year + 1, 1, 1)
    else:
        end = datetime(now.year, now.month + 1, 1)
    freq_result = handle_frequency_command(group_id, start, end)
    freq_result_rank = []

    for (user_id, days) in freq_result:
        freq_result_rank.append((user_id, f"{days}/{now.day}"))
    if not freq_result_rank:
        return "Nenhuma atividade registrada este mês."

    return create_rank(f"Ranking de Frequência - {now.strftime('%B')}", freq_result_rank, group)