import html
import logging
from typing import List, Optional, Tuple

from application.common import GRUPO_NAO_CADASTRADO, periodo_mes
from application.sync_activities import sync_all_activities
from infrastructure.strava_repository import StravaRepository

logger = logging.getLogger(__name__)


def handle_admin_command(group_id: int, repo=None) -> Optional[List[Tuple[str, int]]]:
    """
    Membros do grupo como (nome, athlete_id).

    Returns:
        list | None: None se o grupo não está cadastrado
    """
    repo = repo or StravaRepository()
    group = repo.get_group(group_id)
    if not group:
        return None
    return [(nome, dados["athlete_id"]) for nome, dados in (group.membros or {}).items() if dados.get("athlete_id")]


def handle_admin_callback(group_id: int, member_id: int, autor_remocao: str, repo=None) -> str:
    """
    Remove um membro do grupo (membro, medalhas e atividades).
    Args:
        group_id (int): O ID do grupo.
        member_id (int): O athlete_id do membro a ser removido.
        autor_remocao (str): O nome do usuário que está removendo o membro.
    """
    repo = repo or StravaRepository()
    member_name = repo.remove_member(group_id, member_id)

    if not member_name:
        logger.warning("Membro com athlete_id %s não encontrado no grupo %s", member_id, group_id)
        return "Membro não encontrado."

    logger.info("Membro %s (athlete_id=%s) removido do grupo %s por %s", member_name, member_id, group_id, autor_remocao)
    return f"{html.escape(member_name)} removido com sucesso por {html.escape(autor_remocao or '')}."


def handle_reset_command(group_id: int, repo=None, sync=None) -> str:
    """
    Re-sincroniza as atividades do mês inteiro, ignorando o intervalo mínimo.

    Substitui o reset antigo, que voltava o cursor de cada membro para o dia 1
    (o sync não usa mais cursor).
    """
    repo = repo or StravaRepository()
    if not repo.get_group(group_id):
        return GRUPO_NAO_CADASTRADO

    result = (sync or sync_all_activities)(group_id, since=periodo_mes().inicio, force=True)
    if result and result.falhas:
        falhas = ", ".join(html.escape(nome) for nome in result.falhas)
        return f"Atividades do mês re-sincronizadas. Não consegui sincronizar: {falhas}."
    return "Atividades do mês re-sincronizadas."
