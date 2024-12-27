import requests

from secure import STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET

class StravaService:
    url = 'https://www.strava.com/api/v3'

    def __init__(self, membros, db_manager):
        self.membros = membros
        self.db_manager = db_manager

    def get_params(self, **kwargs):
        self.params = {}

        for key, value in kwargs.items():
            self.params[key] = value

        return self.params
    
    def refresh_access_token(self, user):
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
            "refresh_token": self.membros[user]["refresh_token"],
            "grant_type": "refresh_token",
        }
        new_token = requests.post(url, params=params, timeout=40).json()
        self.membros[user]["access_token"] = new_token["access_token"]
        self.membros[user]["refresh_token"] = new_token["refresh_token"]
        self.db_manager.update_membro(user, self.membros[user])
        return new_token["access_token"], new_token["refresh_token"]
    
    def make_request(self, user_name, url, params):
        params['access_token'] = self.membros[user_name]["access_token"]
        response = requests.get(url, params=params)
        
        
        if response.status_code == 429:
            raise Exception("Erro ao acessar o strava muitas requisições, tente novamente mais tarde")

        if response.status_code == 401:
            new_access_token = self.refresh_access_token(user_name)
            params['access_token'] = new_access_token[0]
            return self.make_request(user_name, url, params)
        
        if response.status_code != 200:
            raise Exception(f"Erro na requisição: {response.status_code} - {response.text}")
        
        return response.json()

    def list_activity(self, user_name, page=1, per_page=100, before=None, after=None):
        return self.make_request(user_name, f'{self.url}/athlete/activities', params=self.get_params(page=page, per_page=per_page, before=before, after=after))

    def get_activity(self,user_name, activity_id):
        return self.make_request(user_name, f'{self.url}/activities/{activity_id}')

    def get_segment(self,user_name, segment_id):
        return self.make_request(user_name, f'{self.url}/segments/{segment_id}')

    def get_segment_effort(self, user_name, segment_effort_id):
        return self.make_request(user_name, f'{self.url}/segment_efforts/{segment_effort_id}')
