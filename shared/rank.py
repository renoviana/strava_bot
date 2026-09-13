import html
from typing import Optional

from shared.user import get_user

EMOJI = {1: "🥇", 2: "🥈", 3: "🥉"}

# Sentinela: com `0` como valor inicial, um primeiro colocado com valor 0 saía "0º".
_SEM_VALOR = object()


def create_rank(title: str, rank_data: list, group, sport_type: Optional[str] = None) -> str:
    """
    Monta o ranking em HTML do Telegram. Empate divide a posição.
    """
    rank_position = 0
    value = _SEM_VALOR
    lines = [html.escape(title)]
    for (user_id, data) in rank_data:
        if data != value:
            value = data
            rank_position += 1
        lines.append(
            f"{rank_position}º - {get_user_link(user_id, group.membros)}"
            f"{get_medalhas(user_id, group, sport_type)} - {html.escape(str(data))}"
        )

    return "\n".join(lines)


def get_user_link(user_id: int, membros: dict) -> str:
    """Link para o perfil do Strava; o nome é escapado (a mensagem vai em HTML)."""
    user = get_user(membros, user_id=user_id)
    if not user:
        return f"Atleta {user_id}"
    return f"<a href='https://www.strava.com/athletes/{user['id']}'>{html.escape(user['name'])}</a>"


def get_medalhas(user_id: int, group, sport_type: Optional[str] = None) -> str:
    """
    Medalhas do atleta no esporte, ex.: "🥇2🥉1".

    Aceita medalha chaveada por athlete_id (atual) ou pelo nome (legado).
    """
    if not sport_type:
        return ""

    user_name = get_user(group.membros, user_id=user_id).get("name")
    medalha_dict = {1: 0, 2: 0, 3: 0}

    for esportes in (group.medalhas or {}).values():
        posicoes = esportes.get(sport_type) or {}
        posicao = posicoes.get(str(user_id))
        if posicao is None and user_name:
            posicao = posicoes.get(user_name)
        try:
            posicao = int(posicao)
        except (TypeError, ValueError):
            continue
        if posicao in medalha_dict:
            medalha_dict[posicao] += 1

    return "".join(f"{EMOJI[posicao]}{count}" for posicao, count in medalha_dict.items() if count)
