from datetime import datetime
from unittest.mock import MagicMock


class MockActivity:
    """Simula um documento StravaActivity suportando acesso por atributo e por chave."""

    def __init__(self, athlete_id, start_date_local, sport_type="Run", distance=0.0, moving_time=0):
        self.athlete = MagicMock()
        self.athlete.id = athlete_id
        self.sport_type = sport_type
        self.distance = distance
        self.moving_time = moving_time
        self._data = {
            "start_date_local": start_date_local,
            "sport_type": sport_type,
            "athlete": {"id": athlete_id},
        }

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)


def make_group(membros=None, medalhas=None):
    group = MagicMock()
    group.membros = membros or {
        "Joao": {"athlete_id": 1, "access_token": "tok1", "refresh_token": "ref1", "last_activity_date": None},
        "Maria": {"athlete_id": 2, "access_token": "tok2", "refresh_token": "ref2", "last_activity_date": None},
    }
    group.medalhas = medalhas or {}
    group.last_sync = None
    return group
