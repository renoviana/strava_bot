from typing import Optional

def get_user(membros:dict, user_id:Optional[int] = None, user_name:Optional[str] = None) -> dict:
    if user_id:
        user = list(filter(lambda x: x[1]['athlete_id'] == user_id, membros.items()))
    elif user_name:
        user = list(filter(lambda x: x[0] == user_name, membros.items()))
    else:
        return {}
    
    if not user:
        return {}

    return {
      "id": user[0][1]['athlete_id'],
      "name": user[0][0]
    }