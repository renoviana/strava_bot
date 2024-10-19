from datetime import datetime, timedelta
import random
import requests
from model import StravaActivity, add_strava_group, get_strava_group, list_strava_activities
from secure import (
    STRAVA_CLIENT_ID,
    STRAVA_CLIENT_SECRET,
)
from dateutil.relativedelta import relativedelta

class StravaGroup:
    last_run = None
    cache_last_activity = None
    cache_first_day = None
    cache_last_day = None
    membros = {}
    metas = {}
    ignored_activities = []

    def __init__(self, group_id=None) -> None:
        self.strava_entity = get_strava_group(group_id)
        self.group_id = self.strava_entity.telegram_group_id
        if not self.strava_entity:
            add_strava_group(self.group_id)
            self.strava_entity = get_strava_group(self.group_id)

        self.metas = self.strava_entity.metas
        self.membros = self.strava_entity.membros
        self.ignored_activities = self.strava_entity.ignored_activities
        self.medalhas = self.strava_entity.medalhas or {}
        self.list_activities = []

    def get_victory_str(self, sport_type,  user_name):
        """
        Retorna mensagem de vitoria
        Args:
            sport_type (str): tipo de esporte
            user_name (str): nome do usuário
        """
        medalhas = {
            1:0,
            2:0,
            3:0,
        }
        for data in self.medalhas.values():
            sport_medalhas = data.get(sport_type.title())
            if not sport_medalhas:
                continue
            victory_dict = sport_medalhas.get(user_name, None)
            if victory_dict:
                medalhas[victory_dict] += 1
        lider, segundo, terceiro = list(medalhas.values())
        msg = ""

        if lider:
            msg += f"🥇{lider}"

        if segundo:
            msg += f"🥈{segundo}"

        if terceiro:
            msg += f"🥉{terceiro}"

        return msg

    def get_strava_api(
        self,
        url,
        params,
        user):
        """
        Retorna dados de atividades em formato json
        Args:
            'url' (str): url da api
            'params' (dict): parametros
            'user' (str): usuario
        """
        access_token, refresh_token = self.get_user_access_and_refresh_token(user)
        params["access_token"] = access_token
        response = requests.get(url, params=params, timeout=40)

        if response.status_code == 429:
            raise Exception("Erro ao acessar o strava muitas requisições, tente novamente mais tarde")

        if response.status_code == 401:
            access_token, refresh_token = self.update_user_token(user, refresh_token)
            return self.get_strava_api(
                url,
                params,
                user,
            )

        return response

    def update_user_token(self, user, refresh_token):
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
        new_token = requests.post(url, params=params, timeout=40).json()
        self.membros[user]["access_token"] = new_token["access_token"]
        self.membros[user]["refresh_token"] = new_token["refresh_token"]
        self.update_entity()
        return new_token["access_token"], new_token["refresh_token"]

    def last_id_in_list(self, lista, last_id):
        for index, data in enumerate(lista):
            if last_id == data['id']:
                return index
        
        return None

    def get_user_access_and_refresh_token(self, user):
        """
        Retorna access token e refresh token do usuário
        Args:
            user (str): usuario
        """
        user_at = self.membros[user].get("access_token")
        user_rt = self.membros[user].get("refresh_token")
        return user_at, user_rt

    def list_activity(
        self,
        user,
        first_day=None,
        last_day=None,):
        """
        Retorna lista de atividades do mês e filtra de acordo com o sport_list
        Args:
            user (str): usuario
            sport_list (list): lista de esportes
            first_day (datetime): data de inicio
            last_day (datetime): data de fim
        """

        if not first_day:
            first_day = datetime.now().replace(
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

        if not last_day:
            last_day = datetime.now() + timedelta(minutes=1)
        
        query = {
            "athlete.id":  self.membros[user].get('athlete_id'),
            "start_date_local": {
                "$gte": first_day,
                "$lt": last_day,
            }
        }

        new_data = list_strava_activities(self.group_id, query)
        activity_id = None
        if new_data:
            activity_id = new_data[0]['id']
        lista_geral = []
        new_activity_list = self.get_athlete_data(
            user,
            after_date=first_day,
            before_date=last_day,
        )
        lista_geral += new_activity_list

        if activity_id:
            index_data = self.last_id_in_list(new_activity_list, activity_id)
            if index_data is not None:
                new_activity_list = new_activity_list[:index_data]
                self.process_activities(new_activity_list)
                return new_activity_list + list(new_data)

        page = 1
        while len(new_activity_list) % 100 == 0 and len(new_activity_list) != 0:
            page += 1
            new_activity_list = self.get_athlete_data(
                user,
                after_date=first_day,
                before_date=last_day,
                page=page,
            )
            
            index_data = self.last_id_in_list(new_activity_list, activity_id)
            if index_data is not None:
                new_activity_list = new_activity_list[:index_data]
                lista_geral += new_activity_list
                self.process_activities(lista_geral)
                return new_activity_list + list(new_data)
            else:
                lista_geral += new_activity_list
        self.process_activities(lista_geral)
        return lista_geral

    def process_activities(self, new_activity_list):
        mongo_lista = []
        for activity in new_activity_list:
            activity_dict = activity.copy()
            activity_dict['group_id'] = self.group_id
            activity_dict['activity_type'] = activity_dict['type']
            activity_dict['activity_id'] = activity_dict['id']
            activity_dict['activity_map'] = activity_dict['map']
            del activity_dict['type']
            del activity_dict['id']
            del activity_dict['map']
            mongo_lista.append(StravaActivity(**activity_dict))
        if mongo_lista:
            StravaActivity.objects.insert(mongo_lista)

    def get_athlete_data(
        self,
        user,
        after_date=None,
        before_date=None,
        page=1,
        per_page=100):
        """
        Retorna dados ded atividades em formato json
        Args:
            after_date (datetime): data de inicio
            before_date (datetime): data de fim
            user (str): usuario
            page (int): pagina
            per_page (int): itens por pagina
        """
        url = "https://www.strava.com/api/v3/athlete/activities"
        access_token, _ = self.get_user_access_and_refresh_token(user)
        params = {"access_token": access_token, "page": page, "per_page": per_page}

        if after_date:
            params["after"] = after_date.timestamp()

        if before_date:
            params["before"] = before_date.timestamp()

        response = self.get_strava_api(url, params, user)
        if response.status_code > 500:
            raise Exception("Erro ao acessar a API do Strava, tente novamente mais tarde")
        return response.json()

    def update_entity(self):
        """
        Atualiza entidade do strava
        """
        self.strava_entity.metas = self.metas
        self.strava_entity.membros = self.membros
        self.strava_entity.ignored_activities = self.ignored_activities
        self.strava_entity.medalhas = self.medalhas
        self.strava_entity.save()
    
    def get_activity_list_by_type(
        self, user, first_day=None, last_day=None):
        """
        Calcula a distancia total e os pontos do usuário
        Args:
            user (str): usuario
            first_day (datetime): data de inicio
            last_day (datetime): data de fim
        """

        activity_list = self.list_activity(
            user,
            first_day=first_day,
            last_day=last_day,
        )

        activity_dict = {}
        gym_dict = {}
        for activity in activity_list:
            if isinstance(activity["start_date_local"], str):
                activity["start_date_local"] = datetime.strptime(activity["start_date_local"], '%Y-%m-%dT%H:%M:%SZ')

            activity_type = activity["sport_type"]

            # if activity_type == 'WeightTraining' and activity["moving_time"] > 7200:
            #     activity["moving_time"] = 7200
                
            gym_dict = self.update_gym_dict(gym_dict, activity)

            if activity_type not in activity_dict:
                activity_dict[activity_type] = []

            activity_dict[activity_type].append(activity)

        # if  gym_dict:
        #     activity_dict["WeightTraining"] = list(gym_dict.values())
        return activity_dict

    def update_gym_dict(self, gym_dict, activity):
        """
        Atualiza dicionario de atividades
        Args:
            gym_dict (dict): dicionario de atividades
            activity (dict): atividade
        """
        if activity["type"] != 'WeightTraining':
            return gym_dict
    
        date_activity = activity['start_date_local'].replace(hour=0, minute=0, second=0, microsecond=0)
        moving_time_ride = activity["moving_time"]

        if date_activity not in gym_dict:
            gym_dict[date_activity] = activity
            return gym_dict

        old_moving_time_ride = gym_dict[date_activity]["moving_time"]
        if old_moving_time_ride < moving_time_ride:
            gym_dict[date_activity] = activity
        return gym_dict

    def get_all_user_data(self, ignore_stats_ids=None, first_day=None, last_day=None):
        if not first_day:
            first_day = datetime.now().replace(
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

        if not last_day:
            last_day = first_day + relativedelta(months=+1)

        if self.last_run and datetime.now() - timedelta(minutes=1) < self.last_run and self.cache_last_day == last_day and self.cache_first_day == first_day:
            return self.cache_last_activity

        user_dict = {}
        for user in self.membros:
            json_data, activity_dict = self.get_distance_and_points(
                user,
                ignore_stats_ids=ignore_stats_ids,
                first_day=first_day,
                last_day=last_day,
            )
            json_data_new = {}
            for activity_name, activity_data in json_data.items():
                if activity_data.get("total_distance") == 0 and activity_data.get("total_moving_time") == 0:
                    continue
                json_data_new[activity_name] = activity_data

            json_data_new["activity_dict"] = activity_dict
            user_dict[user] = json_data_new
        self.cache_last_activity = user_dict
        self.cache_first_day = first_day
        self.cache_last_day = last_day
        self.last_run = datetime.now()
        return user_dict

    def ignore_activity_rules(self, activity):
        """
        Ignora atividades com menos de 5 minutos, mais de 400 km ou atividades manuais que não sejam de natação ou musculação
        Args:
            activity (dict): atividade
        """
        return activity["moving_time"] < 300 or round(activity["distance"] / 1000, 2) > 400 or (activity["manual"] and activity["type"] not in ["WeightTraining", "Swim", "Workout"])

    def get_distance_and_points(
    self, user, ignore_stats_ids=None, first_day=None, last_day=None):
        """
        Calcula a distancia total e os pontos do usuário
        Args:
            user (str): usuario
            ignore_stats_ids (list): lista de ids de atividades ignoradas
            ignore_cache (bool): ignorar cache
            first_day (datetime): data de inicio
            last_day (datetime): data de fim
        """

        if not ignore_stats_ids:
            ignore_stats_ids = []

        activity_dict = self.get_activity_list_by_type(user, first_day=first_day, last_day=last_day)

        default_dict = {
            "total_distance": 0,
            "total_user_points": 0,
            "total_moving_time": 0,
            "max_distance": {"activity_id":None, "value":0},
            "max_velocity": {"activity_id":None, "value":0},
            "max_average_speed": {"activity_id":None, "value":0},
            "max_elevation_gain": {"activity_id":None, "value":0},
            "max_moving_time": {"activity_id":None, "value":0},
        }
        result_dict = {}


        for activity_type, activity_list in activity_dict.items():
            if activity_type not in result_dict:
                result_dict[activity_type] = default_dict.copy()

            for activity in activity_list:
                max_speed_ride_km = round(activity["max_speed"] * 3.6, 2)
                max_average_speed_ride_km = round(activity["average_speed"] * 3.6, 2)
                total_elevation_gain_ride = round(activity["total_elevation_gain"], 2)
                distance_km = round(activity["distance"] / 1000, 2)
                moving_time_ride = activity["moving_time"]

                if self.ignore_activity_rules(activity):
                    continue

                ignore_stats = str(activity.get('id', activity.get('activity_id'))) in ignore_stats_ids
                if distance_km > result_dict[activity_type]["max_distance"]['value'] and not ignore_stats:
                    result_dict[activity_type]["max_distance"]['value'] = round(distance_km, 2)
                    result_dict[activity_type]["max_distance"]['activity_id'] = activity.get('id')

                if max_speed_ride_km > result_dict[activity_type]["max_velocity"]['value'] and not ignore_stats and max_speed_ride_km < 80:
                    result_dict[activity_type]["max_velocity"]['value'] = round(max_speed_ride_km, 2)
                    result_dict[activity_type]["max_velocity"]['activity_id'] = activity.get('id')

                if (
                    max_average_speed_ride_km > result_dict[activity_type]["max_average_speed"]['value']
                    and not ignore_stats
                ):
                    result_dict[activity_type]["max_average_speed"]['value'] = round(max_average_speed_ride_km, 2)
                    result_dict[activity_type]["max_average_speed"]['activity_id'] = activity.get('id')

                if total_elevation_gain_ride > result_dict[activity_type]["max_elevation_gain"]['value']  and not ignore_stats:
                    result_dict[activity_type]["max_elevation_gain"]['value'] = round(total_elevation_gain_ride, 2)
                    result_dict[activity_type]["max_elevation_gain"]['activity_id'] = activity.get('id')

                if moving_time_ride > result_dict[activity_type]["max_moving_time"]['value'] and not ignore_stats:
                    result_dict[activity_type]["max_moving_time"]['value'] = moving_time_ride
                    result_dict[activity_type]["max_moving_time"]['activity_id'] = activity.get('id')

                result_dict[activity_type]["total_user_points"] = round(self.calc_point_rank(
                    result_dict[activity_type]["total_user_points"], total_elevation_gain_ride, distance_km, activity_type
                ), 2)
                result_dict[activity_type]["total_distance"] = round(result_dict[activity_type]["total_distance"] + distance_km, 2)
                result_dict[activity_type]["total_moving_time"] = round(result_dict[activity_type]["total_moving_time"] + moving_time_ride)

        return result_dict, activity_dict

    def format_seconds_to_mm_ss(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    def get_point_str(self, first_day=None, last_day=None):
        """
        Retorna lista de pontos dos usuários
        """
        distance_list = []
        ignore_stats_ids = self.ignored_activities or []
        user_data = self.get_all_user_data(ignore_stats_ids=ignore_stats_ids, first_day=first_day, last_day=last_day)
        for user in self.membros.keys():
            distance = user_data.get(user)
            total_points = 0
            for category in distance:
                total_points += distance[category].get("total_user_points", 0)
 
            if total_points == 0:
                continue

            distance_list.append({"user": user, "point": total_points})
        sort_distance_list = sorted(distance_list, key=lambda k: k["point"], reverse=True)

        return list(
            map(
                lambda x: f"{x[0]+1}º - {x[1].get('user').title()} - {x[1].get('point')} {'ponto' if x[1].get('point') == 1 else 'pontos'}",
                enumerate(sort_distance_list),
            )
        )

    def update_max_metrics(self, metric, user, distance, max_metrics):
        """
        Atualiza metricas4
        Args:
            metric (str): metrica
            user (str): usuario
            distance (dict): distancia
            max_metrics (dict): metricas
        """
        if distance[metric]["value"] > max_metrics[metric]["value"]:
            max_metrics[metric]["user"] = user
            max_metrics[metric]["value"] = distance[metric]["value"]
            max_metrics[metric]["activity_id"] = distance[metric]["activity_id"]

    def get_stats_str(self, year_stats=False):
        """
        Retorna lista de pontos dos usuários
        """
        first_day, last_day = None, None
        date_str = "mês"
        if year_stats:
            first_day = datetime.now().replace(
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
                month=1,
            )
            last_day = datetime.now().replace(
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
                month=1,
                year=datetime.now().year + 1
            )
            date_str = "ano"
        ignore_stats_ids = self.ignored_activities
        max_distance_geral = {"user": '', "value": 0, "activity_id": None}
        max_velocity_geral = {"user": '', "value": 0, "activity_id": None}
        max_average_speed_geral = {"user": '', "value": 0, "activity_id": None}
        max_elevation_gain_geral = {"user": '', "value": 0, "activity_id": None}
        max_moving_time_geral = {"user": '', "value": 0, "activity_id": None}
        max_metrics = {
            "max_distance": max_distance_geral,
            "max_velocity": max_velocity_geral,
            "max_average_speed": max_average_speed_geral,
            "max_elevation_gain": max_elevation_gain_geral,
            "max_moving_time": max_moving_time_geral
        }
        user_data = self.get_all_user_data(ignore_stats_ids=ignore_stats_ids, first_day=first_day, last_day=last_day)

        for user in self.membros.keys():
            distance = user_data.get(user)
            distance = distance.get("Ride")

            if not distance:
                continue

            for metric in max_metrics:
                self.update_max_metrics(metric, user, distance, max_metrics)

        msg_texto = f"🚲💨  Estatísticas do {date_str} 🚲💨\n"
        msg_texto += f"Maior distância: <a href=\"https://www.strava.com/activities/{max_distance_geral['activity_id']}\">{round(max_distance_geral['value'],2)}km - {max_distance_geral['user'].title()}</a>\n"
        msg_texto += f"Maior velocidade: <a href=\"https://www.strava.com/activities/{max_velocity_geral['activity_id']}\">{round(max_velocity_geral['value'],2)}km/h - {max_velocity_geral['user'].title()}</a>\n"
        msg_texto += f"Maior velocidade média: <a href=\"https://www.strava.com/activities/{max_average_speed_geral['activity_id']}\">{round(max_average_speed_geral['value'],2)}km/h - {max_average_speed_geral['user'].title()}</a>\n"
        msg_texto += f"Maior ganho de elevação: <a href=\"https://www.strava.com/activities/{max_elevation_gain_geral['activity_id']}\">{round(max_elevation_gain_geral['value'],2)}m - {max_elevation_gain_geral['user'].title()}</a>\n"
        msg_texto += f"Maior tempo de movimento: <a href=\"https://www.strava.com/activities/{max_moving_time_geral['activity_id']}\">{self.format_seconds_to_mm_ss(max_moving_time_geral['value'])} - {max_moving_time_geral['user'].title()}</a>\n"
        return msg_texto

    def list_type_activities(self, first_day=None, last_day=None):
        """
        Retorna lista de distancias dos usuários
        """
        all_types = []
        user_dict = self.get_all_user_data(first_day=first_day, last_day=last_day)
        for user in self.membros.keys():
            user_data = user_dict.get(user)
            all_types += list(user_data.keys())
        all_types = list(set(all_types))
        return sorted(all_types)

    def rank_format(self,index_data, data, sport_type, rank_unit="km", rank_params='total_distance'):
        """
        Formata o rank
        Args:
            index_data (int): index
            data (list): lista de dados
            sport_type (str): tipo de esporte
            rank_unit (str): unidade de medida
            rank_params (str): parametro de rank
        """
        strava_month_distance = (
            self.metas.get(sport_type)
        )

        rank_list = []
        for user in data:
            rank_data = user.get(rank_params)
            emoji = ""

            if strava_month_distance and rank_data >= strava_month_distance:
                emoji = "✅"

            if rank_params == 'total_moving_time':
                rank_data = self.format_seconds_to_mm_ss(rank_data)
                rank_unit = ""

            user_id = user.get("user_id")
            user_name = user.get('user').title()
            user_link = user_name

            if user_id:
                user_link = f"<a href=\"https://www.strava.com/athletes/{user_id}\">{user_name}</a>"

            rank_list.append(f"{index_data+1}º - {user_link}{self.get_victory_str(sport_type ,user_name)} - {rank_data}{rank_unit} {emoji}")
        return "\n".join(rank_list)

    def get_sport_rank(self, sport_type, year_rank=False, first_day=None, last_day=None):
        """
        Retorna lista de distancias dos usuários
        Args:
            sport_type (str): tipo de esporte
            year_rank (bool): ranking do ano
            first_day (datetime): data de inicio
            last_day (datetime): data de fim
        """
        if year_rank:
            first_day = datetime.now().replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
            month=1,
            )
            last_day = datetime.now().replace(
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
                month=1,
                year=datetime.now().year + 1
            )
        ignore_stats_ids = self.ignored_activities
        distance_list = []
        user_dict = self.get_all_user_data(ignore_stats_ids=ignore_stats_ids, first_day=first_day, last_day=last_day)
        for user, strava in self.membros.items():
            json_data = user_dict.get(user)

            if not json_data.get(sport_type):
                continue

            json_data = json_data[sport_type]

            json_data['user'] = user
            json_data['user_id'] = strava["athlete_id"]
            distance_list.append(json_data)
        
        return distance_list

    def get_ranking_str(self, sport_type , year_rank=False):
        """
        Envia mensagem com o ranking
        Args:
            sport_type (str): tipo de esporte
            year_rank (bool): ranking do ano
            first_day (datetime): data de inicio
            last_day (datetime): data de fim
        """
        emoji_dict = {
            "Ride": "🚲",
            "Run": "🏃",
            "WeightTraining": "🏋️",
            "Swim": "🏊",
            "Hike": "🥾",
            "Walk": "🚶",
            "Workout": "⚡︎",
        }

        emoji = emoji_dict.get(sport_type, sport_type)
        today_str = datetime.now().strftime("%B")

        if year_rank:
            today_str = datetime.now().year

        msg_template = f"Ranking {today_str} {emoji}:\n"
        sport_rank_by_time_list = ['workout', 'weighttraining']
        rank_params = 'total_distance'
        rank_unit="km"
        metas = self.metas.get(sport_type.lower())
        if sport_type.lower() in sport_rank_by_time_list:
            rank_params = 'total_moving_time'
            rank_unit = "min"
            if self.metas.get(sport_type.lower()):
                metas = self.metas.get(sport_type.lower()) / 60

        distance_list = self.get_sport_rank(sport_type, year_rank, first_day=None, last_day=None)
        sort_distance_list = sorted(
            distance_list, key=lambda k: k[rank_params], reverse=True
        )
        distance_list = sort_distance_list

        ranking_dict = {}

        for data in distance_list:
            if data.get(rank_params) <= 0:
                continue
    
            params = data.get(rank_params)
            if params not in ranking_dict:
                ranking_dict[params] = []
            
            ranking_dict[params].append(data)

        sort_distance_list = sorted(
            ranking_dict, reverse=True
        )
        

        rank_msg_list = list(
            map(
                lambda i : self.rank_format(i[0], ranking_dict[i[1]], sport_type.lower(), rank_unit=rank_unit, rank_params=rank_params),
                enumerate(sort_distance_list),
            )
        )
        msg = "\n".join(rank_msg_list)
        msg = msg_template + msg

        if not year_rank and self.metas.get(sport_type.lower()):
            msg += f"\n\n⚠️ Meta individual do mês: {metas}{rank_unit}"

        return msg

    def remove_strava_user(self, user_name, user_name_admin):
        """
        Remove usuário do strava
        Args:
            user_name (str): nome do usuário
            user_name_admin (str): nome do admin
        """
        new_grupo_dict = {}
        for user_name_db, strava_data in self.membros.items():
            if user_name_db == user_name:
                continue
            new_grupo_dict[user_name_db] = strava_data
        
        athlete_id = self.membros[user_name].get('athlete_id')
        query = {
            "athlete.id":  athlete_id,
            "group_id": self.group_id,
        }
        StravaActivity.objects(__raw__=query).delete()
        self.membros = new_grupo_dict
        self.update_entity()
        return f"Usuário {user_name} removido com sucesso pelo {user_name_admin}!"

    def save_group_meta(self, tipo_meta, km):
        """
        Salva meta do grupo
        Args:
            tipo_meta (str): tipo de meta
            km (int): km
        """
        if km:
            km = int(km)
            self.metas[tipo_meta] = km
        else:
            del self.metas[tipo_meta]
        self.update_entity()

    def calc_point_rank(self, total_user_points, total_elevation_gain_ride_m, distance_km, sport_type):
        """
        Calcula o rank de pontos
        Args:
            total_user_points (int): total de pontos
            total_elevation_gain_ride_m (int): total de elevação
            distance_km (int): distancia
        """

        if distance_km > 2 and sport_type in ['Run', 'Walk', 'Hike', 'Swim']:
            total_user_points += 1
            return total_user_points

        if distance_km > 10:
            total_user_points += 1

        if distance_km > 50:
            total_user_points += 1

        if distance_km > 100:
            total_user_points += 1

        if total_elevation_gain_ride_m > 350:
            total_user_points += 1
        return total_user_points

    def add_ignore_activity(self, activity_id):
        """
        Ignora atividade
        Args:
            activity_id (str): id da atividade
        """
        ignore_stats_ids = self.ignored_activities or []
        ignore_stats_ids.append(str(activity_id))
        self.ignored_activities = ignore_stats_ids
        self.update_entity()
        return "Atividade ignorada com sucesso!"

    def get_segments(self, min_distance=None):
        """
        Retrieves segments based on a minimum distance.

        Args:
            min_distance (int): The minimum distance for segments.

        Returns:
            dict: A dictionary containing segment data.
        """
        if not min_distance:
            min_distance = 6000

        ignore_stats_ids = self.ignored_activities
        group_members = list(self.membros.items())
        user_data = self.get_all_user_data(ignore_stats_ids=ignore_stats_ids)
        all_segments = {}

        for name, token in group_members:
            activities = self._get_user_activities(
                name, user_data, min_distance, ignore_stats_ids
            )

            for activity in activities:
                self._process_activity_segments(
                    activity, name, token, min_distance, all_segments
                )

        segment_dict = self._collect_segment_data(all_segments)
        return segment_dict

    def _get_user_activities(self, name, user_data, min_distance, ignore_stats_ids):
        """
        Retrieves activities for a user that meet the minimum distance criteria.

        Args:
            name (str): The user's name.
            user_data (dict): The user data.
            min_distance (int): The minimum distance.
            ignore_stats_ids (set): Set of activity IDs to ignore.

        Returns:
            list: A list of filtered activities.
        """
        activity_list = user_data.get(name, {}).get('activity_dict', {}).get('Ride', [])
        filtered_activities = []

        for activity in activity_list:
            if activity['distance'] < int(min_distance):
                continue
            activity_id = activity['id']
            if str(activity_id) in ignore_stats_ids:
                continue
            activity['id'] = activity_id
            filtered_activities.append(activity)

        return filtered_activities

    def _process_activity_segments(self, activity, name, token, min_distance, all_segments):
        """
        Processes an activity to collect segment efforts.

        Args:
            activity (dict): The activity data.
            name (str): The user's name.
            token (dict): The user's token.
            min_distance (int): The minimum distance.
            all_segments (dict): Dictionary to collect all segment efforts.
        """
        activity_id = activity['id']
        activity_data = self.get_strava_api(
            f"https://www.strava.com/api/v3/activities/{activity_id}", {}, name
        ).json()
        segment_efforts = activity_data.get('segment_efforts', [])

        for segment_effort in segment_efforts:
            if segment_effort['distance'] < int(min_distance):
                continue

            if segment_effort['segment']['id'] in [18536734, 683759]:
                continue

            segment_effort.update({
                'user': name,
                'access_token': token['access_token'],
                'refresh_token': token['refresh_token'],
                'atividade_id': activity_id
            })
            segment_id = segment_effort['segment']['id']

            all_segments.setdefault(segment_id, []).append(segment_effort)

    def _collect_segment_data(self, all_segments):
        """
        Collects segment data from segment efforts.

        Args:
            all_segments (dict): Dictionary containing all segment efforts.

        Returns:
            dict: A dictionary containing segment data.
        """
        segment_dict = {}
        athlete_ids = {}
        filtered_segments = {
            k: v for k, v in all_segments.items() if len(v) > 2
        }

        for segment_list in filtered_segments.values():
            for segment in segment_list:
                segment_data = self.get_strava_api(
                    f"https://www.strava.com/api/v3/segment_efforts/{segment['id']}",
                    {},
                    segment['user']
                ).json()

                activity_id = segment_data['segment']['id']
                segment_data.update({
                    'user': segment['user'],
                    'atividade_id': segment['atividade_id']
                })
                athlete_ids[segment['athlete']['id']] = True

                segment_dict.setdefault(activity_id, []).append(segment_data)

        return segment_dict

    def get_segments_str(self, min_distance):
        """
        Retorna segmentos em formato de string
        Args:
            min_distance (int): distancia minima
        """
        str_list = ["Segmentos do mês:"]
        segment_dict = self.get_segments(min_distance)
        for segments in segment_dict.values():
            if len(segments) < 2:
                continue

            data = [
                segments[0]['name'],
                " - ",
                str(round(segments[0]['distance']/1000, 2)),
                "km"
            ]

            str_list.append(f"{''.join(data)}")
            segments = sorted(segments, key=lambda x: x['moving_time'])
            athelete_list = []
            for segment in segments:
                segment_athlete = segment['user']
                start_date_local = segment['start_date_local']
                segment['start_date_local'] = datetime.strptime(start_date_local, '%Y-%m-%dT%H:%M:%SZ')

                if segment_athlete in athelete_list:
                    continue

                athelete_list.append(segment_athlete)
                segment_min = self.format_seconds_to_mm_ss(segment['moving_time'])
                msg_str = f"- <a href=\"https://www.strava.com/activities/{segment['activity']['id']}/segments/{segment['id']}\">{segment_athlete} - {segment_min}</a>"
                str_list.append(msg_str)
            str_list.append("")

        return "\n".join(str_list)
    
    def get_medalhas_rank(self):
        """
        Retorna o ranking geral de medalhas
        """
        from collections import defaultdict
        medals = defaultdict(lambda: {"🥇": 0, "🥈": 0, "🥉": 0, "pontos": 0})

        for month, sports in self.medalhas.items():
            for sport, rankings in sports.items():
                for person, position in rankings.items():
                    if position == 1:
                        medals[person]["🥇"] += 1
                        medals[person]["pontos"] += 3
                    elif position == 2:
                        medals[person]["🥈"] += 1
                        medals[person]["pontos"] += 2
                    elif position == 3:
                        medals[person]["🥉"] += 1
                        medals[person]["pontos"] += 1

        # Ordenar por pontos, e em caso de empate, ordenar por medalhas de ouro, prata, e bronze
        sorted_medals = sorted(medals.items(), key=lambda x: (-x[1]["pontos"], -x[1]["🥇"], -x[1]["🥈"], -x[1]["🥉"]))

        # Exibir os resultados no formato desejado
        msg_list = []
        rank = 1
        pontos = sorted_medals[0][1]['pontos']
        for rank, (person, counts) in enumerate(sorted_medals, 1):
            if counts['pontos'] < pontos:
                rank = rank + 1
                pontos = counts['pontos']
            msg_list.append(f"{rank}º - {person} 🥇{counts['🥇']} 🥈{counts['🥈']} 🥉{counts['🥉']} | {counts['pontos']} pts")

        return "\n".join(msg_list)


    def get_frequency(self, first_day=None, last_day=None, month_days=None, title=""):
        if not month_days:
            title = "Quantidade de dias com atividades no mês:"
            month_days = datetime.now().day

        date_dict = {}
        for membro in self.membros:
            activity = self.list_activity(membro, first_day=first_day, last_day=last_day)
            if membro not in date_dict:
                date_dict[membro] = {}

            for a in activity:
                start_date_local = a['start_date_local']
                if isinstance(start_date_local, str):
                    start_date_local = datetime.strptime(start_date_local, '%Y-%m-%dT%H:%M:%SZ')
                date = start_date_local.strftime('%Y-%m-%d')
                date_dict[membro][date] = True
                pass

            if len(date_dict[membro]) == 0:
                del date_dict[membro]
                continue

            date_dict[membro] = len(date_dict[membro])
        # Order by value
        date_dict = dict(sorted(date_dict.items(), key=lambda item: item[1], reverse=True))
        msg_list = [title]
        rank_position = 1
        current_value = list(date_dict.values())[0]
        for name, valor in date_dict.items():
            if valor != current_value:
                rank_position = rank_position + 1
                current_value = valor
            msg_list.append(f"{rank_position}º - {name.title()} - {valor}/{month_days}")
        return "\n".join(msg_list)

        
    def update_medalhas(self, first_day, last_day):
        """
        Atualiza medalhas
        """
        medalhas = self.medalhas
        novas_medalhas_str = "Vencedores do mês:\n"
        index_dict = {
            0: {
                'emoji': '🥇',
                'key': 'lider'
            },
            1: {
                'emoji': '🥈',
                'key': 'segundo'
            },
            2: {
                'emoji': '🥉',
                'key': 'terceiro'
            }
        }
        rank_dict = {}
        medalhas_dict = {}
        for membro, data  in self.membros.items():
            created_at = data.get('created_at')
            if created_at > last_day:
                continue
            activity = self.get_activity_list_by_type(membro, first_day=first_day, last_day=last_day)
            sport_dict = {}
            for sport_type in activity:
                if sport_type not in rank_dict:
                    rank_dict[sport_type] = []

                lista = activity[sport_type]
                rank_parms = 'distance'
                if sport_type in ['WeightTraining', 'Workout']:
                    rank_parms = 'moving_time'
                soma = sum([i[rank_parms] for i in lista])

                if sport_type == 'Walk' and soma < 45000:
                    continue
                sport_dict[sport_type] = soma
                rank_dict[sport_type].append({
                    'total': soma,
                    'user': membro
                })
        
        for sport in rank_dict:
            user_lista = rank_dict[sport]
            user_lista = sorted(user_lista, key=lambda x: x['total'], reverse=True)

            if len(user_lista) == 1:
                continue
            
            if  len(user_lista) > 1 and len(user_lista) < 3:
                user_lista = user_lista[:1]

            if len(user_lista) > 3:
                user_lista = user_lista[:3]

            medalhas_dict[sport] = {}

            for index, user_data in enumerate(user_lista):
                user = user_data.get('user')
                total = user_data.get('total')
                if user not in medalhas_dict[sport]:
                    medalhas_dict[sport][user] = []
                medalhas_dict[sport][user] = index+1
        return medalhas_dict
        # for sport in self.list_type_activities(first_day=first_day, last_day=last_day).items():
        #     sport_name, users = sport
        #     rank =  self.get_rank(sport_name, use_cache=True, user_list=users)
        #     sport_name = sport_name.lower()
        #     sport_rank_by_time_list = ['workout', 'weighttraining']
        #     rank_params = 'km'
        #     if sport_name in sport_rank_by_time_list:
        #         rank_params = 'min'

        #     if len(rank) == 1:
        #         continue

        #     medalhas_dict = {}
        #     for user_data in rank:
        #         total = user_data.get('total_distance')
        #         if not total:
        #             total = user_data.get('total_moving_time')

        #         if sport_name == 'walk' and total < 50:
        #             continue

        #         user_name = user_data.get('user').lower()
                
        #         if total not in medalhas_dict:
        #             medalhas_dict[total] = []
        #         medalhas_dict[total].append(user_name)

        #     if not medalhas_dict:
        #         continue

        #     novas_medalhas_str += f"\n{sport_name.capitalize()}:\n"
        #     medalhas_dict = sorted(medalhas_dict.items(), key=lambda x: x[0], reverse=True)
        #     for index, medal in enumerate(medalhas_dict):
        #         total, users = medal
        #         user = random.choice(users)
        #         only_gold_medal = int(index) > 0 and len(medalhas_dict) < 4

        #         if index > 2 or only_gold_medal:
        #             break

        #         if user not in medalhas[sport_name]:
        #             medalhas[sport_name][user] = {
        #                 'lider': 0,
        #                 'segundo': 0,
        #                 'terceiro': 0
        #             }
        #         medalhas[sport_name][user][index_dict[index]['key']] += 1
        #         novas_medalhas_str += f"{index_dict[index]['emoji']} {user.title()} - {total}{rank_params}\n"

        self.medalhas = medalhas
        # self.update_entity()
        return medalhas
    

    def get_medalhas_var(self):
        from collections import defaultdict

        # Dicionário para armazenar as contagens de medalhas e os detalhes dos meses
        medals = defaultdict(lambda: {
            "🥇": 0, "🥈": 0, "🥉": 0, "detalhes": defaultdict(lambda: {"🥇": [], "🥈": [], "🥉": []})
        })

        # Iterar sobre os meses e esportes
        for month, sports in self.medalhas.items():
            month = month.replace("_", "/")
            for sport, rankings in sports.items():
                for person, position in rankings.items():
                    if position == 1:
                        medals[person]["🥇"] += 1
                        medals[person]["detalhes"][sport]["🥇"].append(month)
                    elif position == 2:
                        medals[person]["🥈"] += 1
                        medals[person]["detalhes"][sport]["🥈"].append(month)
                    elif position == 3:
                        medals[person]["🥉"] += 1
                        medals[person]["detalhes"][sport]["🥉"].append(month)

        # Ordenar as pessoas pelo número de medalhas de ouro, depois prata, depois bronze
        sorted_medals = sorted(medals.items(), key=lambda x: (-x[1]["🥇"], -x[1]["🥈"], -x[1]["🥉"]))
        msg_list = []
        # Exibir os resultados no formato desejado
        for rank, (person, counts) in enumerate(sorted_medals, 1):
            msg_list.append(f"{rank}º - {person} 🥇{counts['🥇']} 🥈{counts['🥈']} 🥉{counts['🥉']}")
            for sport, detalhes in counts['detalhes'].items():
                msg_list.append(f"{sport} -")
                for medalha, meses in detalhes.items():
                    if meses:
                        msg_list.append(f"{medalha} - {', '.join(meses)}")

        return "\n".join(msg_list)