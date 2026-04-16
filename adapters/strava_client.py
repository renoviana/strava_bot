import logging
import requests
from datetime import datetime

from config import STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET

logger = logging.getLogger(__name__)


class StravaClient:
    BASE_URL = "https://www.strava.com/api/v3"

    def fetch_activities(self, access_token: str, after: datetime) -> list[dict]:
        """
        Busca atividades do Strava com base no access_token fornecido.
        :param access_token: Token de acesso do usuário Strava
        :param after: Data a partir da qual buscar atividades
        :param per_page: Número de atividades por página (max 200)
        :return: Lista de atividades
        """
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        after_timestamp = int(after.timestamp())

        url = f"{self.BASE_URL}/athlete/activities"
        params = {
            "after": after_timestamp,
            "per_page": 50,
            "page": 1
        }

        logger.info("Buscando atividades do Strava após %s", after)
        response = requests.get(url, headers=headers, params=params, timeout=40)
        response.raise_for_status()
        data = response.json()
        logger.info("Recebidas %d atividades do Strava", len(data))
        return data
  
    def refresh_access_token(self, refresh_token):
        """
        Atualiza token do usuário
        Args:
            user (str): usuario
            refresh_token (str): refresh token
        """
        url = "https://www.strava.com/oauth/token"
        params = {
            "client_id": STRAVA_CLIENT_ID,
            "client_secret": STRAVA_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        logger.info("Renovando access token do Strava")
        response = requests.post(url, params=params, timeout=40)
        response.raise_for_status()
        logger.info("Token renovado com sucesso")
        return response.json()
        