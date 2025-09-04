from infrastructure.mongo.strava_group import StravaGroup
from infrastructure.mongo.strava_activity import StravaActivity

def handle_admin_command(group_id: int) -> list:
    """
    Retorna a lista de membros do grupo com seus respectivos IDs de atleta.
    Args:
        group_id (int): O ID do grupo.
    """
    group_repo = StravaGroup()
    group = group_repo.get_group(group_id)
    return list(map(lambda membro: (membro, group.membros.get(membro).get("athlete_id")), group.membros.keys()))

def handle_admin_callback(group_id:int, member_id:int, autor_remocao:str) -> str:
    """
    Remove um membro do grupo.
    Args:
        group_id (int): O ID do grupo.
        member_id (int): O ID do membro a ser removido.
        autor_remocao (str): O nome do usuário que está removendo o membro.
    """
    group_repo = StravaGroup()
    activity_repo = StravaActivity()
    group = group_repo.get_group(group_id)
    membro_removido = list(filter(lambda x: x[1].get("athlete_id") == member_id, group.membros.items()))

    if not membro_removido:
        return "Membronão encontrado."

    member_name = membro_removido[0][0]
    del group.membros[membro_removido[0][0]]
    for month, sport_dict in group.medalhas.items():
        for sport_name, sport_data in sport_dict.items():
            if member_name in sport_data:
                del group.medalhas[month][sport_name][member_name]
    group.save()
    activity_repo.remove_activity_member(group_id, member_id)
    return f"{member_name} removido com sucesso por {autor_remocao}."