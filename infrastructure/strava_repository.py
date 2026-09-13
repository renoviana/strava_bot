"""
Repositório do bot sobre os models e CRUDs do `assistant_model`.

Regra 3 do CLAUDE.md: nada de esquema local para dado que já existe no
ecossistema. A cópia local dos models (sem o índice único e sem `db_alias`)
foi removida; o acesso passa todo pelo `assistant_model.crud.strava`.
"""
from datetime import datetime
from typing import List, Optional

from assistant_model.crud import strava as crud


class StravaRepository:
    """Acesso a grupos e atividades do desafio."""

    def get_group(self, group_id: int):
        return crud.get_strava_group(group_id)

    def list_activities(
        self, group_id: int, start: datetime, end: datetime, athlete_ids: Optional[List[int]] = None
    ) -> list:
        return list(crud.list_strava_activities(group_id, start, end, athlete_ids=athlete_ids))

    def list_sports(self, group_id: int, start: datetime, end: datetime) -> List[str]:
        return sorted(crud.list_strava_sports(group_id, start, end))

    def remove_member(self, group_id: int, athlete_id: int) -> Optional[str]:
        return crud.remove_strava_member(group_id, athlete_id)
