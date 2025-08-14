from typing import Optional


def create_rank(title:str, rank_data:list, group, sport_type:Optional[str] = None):
    rank_position = 0
    value = 0
    lines = [title]
    for (user_id, data) in rank_data:
        if data != value:
            value = data
            rank_position += 1
        lines.append(f"{rank_position}º - {get_user_link(user_id, group.membros)}{get_medalhas(user_id, group, sport_type)} - {data}")

    return "\n".join(lines)

def get_user_link(user_id:int, membros:dict):
    user = list(filter(lambda x: x[1]['athlete_id'] == user_id, membros.items()))
    return f"<a href='https://www.strava.com/athletes/{user[0][1]['athlete_id']}'>{user[0][0]}</a>"

def get_medalhas(user_id:int, group, sport_type:Optional[str] = None):
    user = list(filter(lambda x: x[1]['athlete_id'] == user_id, group.membros.items()))
    user_name = user[0][0]
   
    if not sport_type:
        return ""
    
    emoji_dict = {
        1: "🥇",
        2: "🥈",
        3: "🥉"
    }

    medalha_dict = {
        1: 0,
        2: 0,
        3: 0
    }
    
    for medalha in group.medalhas.values():
        if not medalha.get(sport_type):
            continue

        sport_type_medalhas = medalha.get(sport_type)

        if sport_type_medalhas.get(user_name):
            medalha_dict[sport_type_medalhas.get(user_name)] += 1

    medalhas_str = ""
    for medalha, count in medalha_dict.items():
        if count == 0:
            continue
        medalhas_str += f"{emoji_dict.get(medalha, '')}{count} "
    return medalhas_str.strip()
