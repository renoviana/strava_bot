import logging
from infrastructure.mongo.strava_group import StravaGroup

logger = logging.getLogger(__name__)
from domain.services.medal_service import MedalService
from shared.rank import create_rank
from shared.user import get_user


def handle_medal_command(group_id: int) -> str:
    group_repo = StravaGroup()
    group = group_repo.get_group(group_id)


    service = MedalService(group)
    medal_result = service.calculate()

    logger.info("Calculando medalhas para grupo %s", group_id)
    if not medal_result:
        return "Nenhuma medalha conquistada"

    
    emoji_dict = {
        1: "🥇",
        2: "🥈",
        3: "🥉",
        "points": "| ",
    }

    medalhas_list = []
    for user_name, medal_data in medal_result.items():
        user = get_user(group.membros, user_name=user_name)

        if not user:
            continue
        
        medalhas_str = ""
        for medalha, count in medal_data.items():
            emoji = emoji_dict.get(medalha)
            if emoji:
                medalhas_str += f"{emoji}{count} "
        medalhas_str += "pts"
        medalhas_list.append((user["id"], medalhas_str))

    return create_rank(
        "Ranking de Medalhas",
        medalhas_list,
        group
    )