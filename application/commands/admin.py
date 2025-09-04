from infrastructure.mongo.strava_group import StravaGroup

def handle_admin_command(group_id: int) -> list:
    group_repo = StravaGroup()
    group = group_repo.get_group(group_id)
    return list(map(lambda membro: (membro, group.membros.get(membro).get("athlete_id")), group.membros.keys()))