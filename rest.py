from datetime import datetime, timedelta
import requests
from model import add_strava_group, get_strava_group
from secure import (
    STRAVA_CLIENT_ID,
    STRAVA_CLIENT_SECRET,
)

class StravaGroup:
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
        self.cache_data = self.strava_entity.cache_data or []
        self.cache_data = sorted(self.cache_data, key=lambda x: datetime.strptime(x['start_date_local'], '%Y-%m-%dT%H:%M:%SZ'), reverse=True)
        self.list_activities = []

    def get_victory_str(self, sport_type,  user_name):
        """
        Retorna mensagem de vitoria
        Args:
            user_name (str): nome do usuário
        """
        victory_dict = self.medalhas.get(sport_type, {}).get(user_name.lower(), {})
        lider = victory_dict.get("lider")
        segundo = victory_dict.get("segundo")
        terceiro = victory_dict.get("terceiro")

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

    def add_user(self, athlete_name, access_token, refresh_token, athlete_id):
        """
        Adiciona usuário
        Args:
            athlete_name (str): nome do atleta
            access_token (str): access token
            refresh_token (str): refresh token
            athlete_id (str): id do atleta
        """
        self.membros[athlete_name] = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "athlete_id": athlete_id,
        }
        self.update_entity()

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

        new_activity_list = self.get_athlete_data(
            user,
            after_date=first_day,
            before_date=last_day,
        )

        if self.cache_data and new_activity_list:
            last_activity_id = None
            user_activity_list = list(filter(lambda x: x['athlete']['id'] == self.membros[user].get('athlete_id') and datetime.strptime(x['start_date_local'], '%Y-%m-%dT%H:%M:%SZ') >= first_day and datetime.strptime(x['start_date_local'], '%Y-%m-%dT%H:%M:%SZ') <= last_day, self.cache_data))
            if user_activity_list:
                last_activity_id = user_activity_list[0]['id']
                
                if new_activity_list:
                    last_index = len(new_activity_list)
                    if last_activity_id:
                        for index, activity in enumerate(new_activity_list):
                            if activity['id'] == last_activity_id:
                                last_index = index
                                break
                        new_activity_list = new_activity_list[:last_index]

                    if new_activity_list:
                        self.cache_data = new_activity_list + self.cache_data
                        self.update_entity()
                return list(
                        filter(
                            lambda x: datetime.strptime(x['start_date_local'], '%Y-%m-%dT%H:%M:%SZ') >= first_day and datetime.strptime(x['start_date_local'], '%Y-%m-%dT%H:%M:%SZ') <= last_day,
                            new_activity_list + user_activity_list
                        )
                    )

        page = 1
        while len(new_activity_list) % 100 == 0 and len(new_activity_list) != 0:
            page += 1
            new_activity_list += self.get_athlete_data(
                user,
                after_date=first_day,
                before_date=last_day,
                page=page,
            )

            if self.cache_data and new_activity_list:
                last_activity_id = None
                user_activity_list = list(filter(lambda x: x['athlete']['id'] == self.membros[user].get('athlete_id'), self.cache_data))
                if user_activity_list:
                    last_activity_id = user_activity_list[0]['id']

                    if new_activity_list:
                        last_index = len(new_activity_list)
                        if last_activity_id:
                            for index, activity in enumerate(new_activity_list):
                                if activity['id'] == last_activity_id:
                                    last_index = index
                                    break
                            new_activity_list = new_activity_list[:last_index]

                        if new_activity_list:
                            self.cache_data = new_activity_list + self.cache_data
                            self.update_entity()
                    return list(
                            filter(
                                lambda x: datetime.strptime(x['start_date_local'], '%Y-%m-%dT%H:%M:%SZ') >= first_day and datetime.strptime(x['start_date_local'], '%Y-%m-%dT%H:%M:%SZ') <= last_day,
                                new_activity_list + user_activity_list
                            )
                        )



        self.list_activities += new_activity_list
        return new_activity_list

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
        return response.json()

    def remove_cache_data_duplicates(self):
        """
        Remove duplicatas do cache
        """
        self.cache_data = list({v['id']:v for v in self.cache_data}.values())

    def update_entity(self):
        """
        Atualiza entidade do strava
        """
        self.strava_entity.metas = self.metas
        self.strava_entity.membros = self.membros
        self.strava_entity.ignored_activities = self.ignored_activities
        self.strava_entity.medalhas = self.medalhas
        self.remove_cache_data_duplicates()
        self.strava_entity.cache_data = self.cache_data
        self.strava_entity.cache_data = sorted(self.cache_data, key=lambda x: datetime.strptime(x['start_date_local'], '%Y-%m-%dT%H:%M:%SZ'), reverse=True)
        self.strava_entity.save()

    def get_distance_and_points(
    self, user, sport_list=None, ignore_stats_ids=None, first_day=None, last_day=None):
        """
        Calcula a distancia total e os pontos do usuário
        Args:
            user (str): usuario
            sport_list (str): tipo de esporte
            ignore_stats_ids (list): lista de ids de atividades ignoradas
            ignore_cache (bool): ignorar cache
            first_day (datetime): data de inicio
            last_day (datetime): data de fim
        """


        if not sport_list:
            sport_list = ["Ride"]

        activity_list = self.list_activity(
            user,
            first_day=first_day,
            last_day=last_day,
        )

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


        for activity in activity_list:
            activity_type = activity["type"]

            if activity_type == 'Workout':
                activity_type = 'WeightTraining'

            if activity_type not in result_dict:
                result_dict[activity_type] = default_dict.copy()

            max_speed_ride_km = round(activity["max_speed"] * 3.6, 2)
            max_average_speed_ride_km = round(activity["average_speed"] * 3.6, 2)
            total_elevation_gain_ride = round(activity["total_elevation_gain"], 2)
            distance_km = round(activity["distance"] / 1000, 2)
            moving_time_ride = round(activity["moving_time"] / 60, 2)

            if moving_time_ride < 5:
                continue

            manual_ride = activity["manual"]
            ignore_stats = str(activity.get('id')) in ignore_stats_ids

            if distance_km > 400:
                continue

            if manual_ride and activity_type not in ["WeightTraining", "Swim"]:
                continue

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
                result_dict[activity_type]["max_moving_time"]['value'] = round(moving_time_ride, 2)
                result_dict[activity_type]["max_moving_time"]['activity_id'] = activity.get('id')

            result_dict[activity_type]["total_user_points"] = round(self.calc_point_rank(
                result_dict[activity_type]["total_user_points"], total_elevation_gain_ride, distance_km, activity_type
            ), 2)
            result_dict[activity_type]["total_distance"] = round(result_dict[activity_type]["total_distance"] + distance_km, 2)
            result_dict[activity_type]["total_moving_time"] = round(result_dict[activity_type]["total_moving_time"] + moving_time_ride, 2)

        return result_dict

    def get_point_str(self):
        """
        Retorna lista de pontos dos usuários
        """
        distance_list = []
        ignore_stats_ids = self.ignored_activities or []
        for user in self.membros.keys():
            distance = self.get_distance_and_points(
                user,
                ignore_stats_ids=ignore_stats_ids
            )
            total_points = distance.get("Ride", {}).get("total_user_points", 0) + distance.get("Run", {}).get("total_user_points", 0) + distance.get("Walk", {}).get("total_user_points", 0)

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

    def get_stats_str(self):
        """
        Retorna lista de pontos dos usuários
        """
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

        for user in self.membros.keys():
            distance = self.get_distance_and_points(
                user,
                ignore_stats_ids=ignore_stats_ids
            )
            distance = distance.get("Ride")

            if not distance:
                continue

            for metric in max_metrics:
                self.update_max_metrics(metric, user, distance, max_metrics)

        msg_texto = "🚲💨  Estatísticas do mês 🚲💨\n"
        msg_texto += f"Maior distância: <a href=\"https://www.strava.com/activities/{max_distance_geral['activity_id']}\">{round(max_distance_geral['value'],2)}km - {max_distance_geral['user'].title()}</a>\n"
        msg_texto += f"Maior velocidade: <a href=\"https://www.strava.com/activities/{max_velocity_geral['activity_id']}\">{round(max_velocity_geral['value'],2)}km/h - {max_velocity_geral['user'].title()}</a>\n"
        msg_texto += f"Maior velocidade média: <a href=\"https://www.strava.com/activities/{max_average_speed_geral['activity_id']}\">{round(max_average_speed_geral['value'],2)}km/h - {max_average_speed_geral['user'].title()}</a>\n"
        msg_texto += f"Maior ganho de elevação: <a href=\"https://www.strava.com/activities/{max_elevation_gain_geral['activity_id']}\">{round(max_elevation_gain_geral['value'],2)}m - {max_elevation_gain_geral['user'].title()}</a>\n"
        msg_texto += f"Maior tempo de movimento: <a href=\"https://www.strava.com/activities/{max_moving_time_geral['activity_id']}\">{round(max_moving_time_geral['value'],2)}min - {max_moving_time_geral['user'].title()}</a>\n"
        return msg_texto

    def list_type_activities(self, first_day=None, last_day=None):
        """
        Retorna lista de distancias dos usuários
        """
        all_types = []
        for user in self.membros.keys():
            activity_list = self.list_activity(
                user,
                first_day=first_day,
                last_day=last_day,
            )
            activity_list = list(filter(lambda x: not x["manual"] or x['type'] == "WeightTraining", activity_list))
            all_types += list(map(lambda x: x["type"], activity_list))
        all_types = list(set(all_types))

        all_types = list(filter(lambda x: x not in ['Workout'], all_types))
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
            user_id = user.get("user_id")
            user_name = user.get('user').title()

            if user_id:
                user_name = f"<a href=\"https://www.strava.com/athletes/{user_id}\">{user_name}{self.get_victory_str(sport_type, user_name)}</a>"

            rank_list.append(f"{index_data+1}º - {user_name}{self.get_victory_str(sport_type ,user_name)} - {rank_data}{rank_unit} {emoji}")
        return "\n".join(rank_list)

    def get_rank(self, sport_type, year_rank=False, first_day=None, last_day=None):
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

        for user, strava in self.membros.items():
            json_data = self.get_distance_and_points(
                user,
                ignore_stats_ids=ignore_stats_ids,
                first_day=first_day,
                last_day=last_day,
            )

            if not json_data.get(sport_type):
                continue

            json_data = json_data[sport_type]

            json_data['user'] = user
            json_data['user_id'] = strava["athlete_id"]
            distance_list.append(json_data)
        return distance_list


    def get_ranking_str(self, sport_type , year_rank=False, first_day=None, last_day=None):
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
            "Workout": "🏋️",
        }

        emoji = emoji_dict.get(sport_type, sport_type)
        today_str = datetime.now().strftime("%B")

        if year_rank:
            today_str = datetime.now().year

        msg_template = f"Ranking {today_str} {emoji}:\n"
        sport_rank_by_time_list = ['workout', 'weighttraining']
        rank_params = 'total_distance'
        rank_unit="km"
        
        if sport_type.lower() in sport_rank_by_time_list:
            rank_params = 'total_moving_time'
            rank_unit = "min"

        if self.list_activities:
            self.cache_data += self.list_activities
            self.update_entity()

        distance_list = self.get_rank(sport_type, year_rank, first_day=None, last_day=None)
        sort_distance_list = sorted(
            distance_list, key=lambda k: k[rank_params], reverse=True
        )
        distance_list = sort_distance_list

        ranking_dict = {}

        for data in distance_list:
            if data.get(rank_params) < 0:
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
                lambda i: self.rank_format(i[0],ranking_dict[i[1]], sport_type.lower(), rank_unit=rank_unit, rank_params=rank_params),
                enumerate(sort_distance_list),
            )
        )
        msg = "\n".join(rank_msg_list)
        msg = msg_template + msg

        if not year_rank:
            strava_month_distance = self.metas.get(sport_type.lower())
            if strava_month_distance:
                msg += f"\n\n⚠️ Meta individual do mês: {strava_month_distance}km"

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
        self.update_entity()

    def calc_point_rank(self, total_user_points, total_elevation_gain_ride_m, distance_km, sport_type):
        """
        Calcula o rank de pontos
        Args:
            total_user_points (int): total de pontos
            total_elevation_gain_ride_m (int): total de elevação
            distance_km (int): distancia
        """

        if distance_km > 2 and sport_type in ['Run', 'Walk']:
            total_user_points += 1
            return total_user_points

        if distance_km > 10:
            total_user_points += 1

        if distance_km > 50:
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

    def get_segments(self, min_distance=9000):
        """
        Retorna segmentos
        Args:
            min_distance (int): distancia minima
        """
        ignore_stats_ids = self.ignored_activities
        grupo_members = list(self.membros.items())
        all_segments = {}
        for nome,token in grupo_members:

            activity_list = self.list_activity(
                nome,
            )
            activity_list = list(filter(lambda x: x["type"] in ['Ride'], activity_list))

            for atividade in activity_list:
                if atividade['distance'] < min_distance:
                    continue

                atividade_id = atividade['id']

                if str(atividade_id) in ignore_stats_ids:
                    continue


                atividade_data = self.get_strava_api(f"https://www.strava.com/api/v3/activities/{atividade_id}", {}, nome).json()
                segment_afforts = atividade_data['segment_efforts']
                for segment_effort in segment_afforts:
                    if segment_effort['distance'] < min_distance:
                        continue

                    segment_effort['user'] = nome
                    segment_effort['access_token'] = token['access_token']
                    segment_effort['refresh_token'] = token['refresh_token']
                    segment_effort['atividade_id'] = atividade_id
                    if segment_effort['segment']['id'] not in all_segments:
                        all_segments[segment_effort['segment']['id']] = []

                    all_segments[segment_effort['segment']['id']].append(segment_effort)


        segment_dict = {}
        athelete_id = {

        }

        # segment with min 2 athletes
        all_segments = list(filter(lambda x: len(x[1]) > 2, all_segments.items()))
        for _, segment_list in all_segments:
            for segment in segment_list:
                segment_data = self.get_strava_api(f"https://www.strava.com/api/v3/segment_efforts/{segment['id']}", {}, segment['user']).json()
                atividade_id = segment_data['segment']['id']
                segment_data['user'] = segment['user']
                segment_data['atividade_id'] = segment['atividade_id']
                athelete_id[segment['athlete']['id']] = True

                if atividade_id not in segment_dict:
                    segment_dict[atividade_id] = []

                segment_dict[atividade_id].append(segment_data)

        return segment_dict

    def get_segments_str(self, min_distance=9000):
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
                "km - ID: ",
                f"{str(segments[0]['segment']['id'])}"
            ]

            str_list.append(f"<a href=\"https://www.strava.com/segments/{str(segments[0]['segment']['id'])}\">{''.join(data)}</a>")
            segments = sorted(segments, key=lambda x: x['moving_time'])
            athelete_list = []
            for segment in segments:
                moving_time = segment['moving_time']
                segment_athlete = segment['user']
                start_date_local = segment['start_date_local']
                segment['start_date_local'] = datetime.strptime(start_date_local, '%Y-%m-%dT%H:%M:%SZ')

                if segment_athlete in athelete_list:
                    continue

                athelete_list.append(segment_athlete)
                segment_min = str(round(moving_time/60, 2))
                segment_date = segment['start_date_local'].strftime('%d/%m/%Y %H:%M:%S')
                url = f"{segment_min}min - {segment_date}"
                str_list.append('- '+segment_athlete+"\n"+url)
            str_list.append("")

        return "\n".join(str_list)
    
    def get_medalhas_rank(self):
        """
        Retorna o ranking geral de medalhas
        """
        medalhas = self.medalhas
        user_dict = {}
        for sport in medalhas:
            for user in medalhas[sport]:
                if user not in user_dict:
                    user_dict[user] = {
                        'lider': 0,
                        'segundo': 0,
                        'terceiro': 0,
                        'pontos_total': 0,
                    }
                user_dict[user]['lider'] += medalhas[sport][user]['lider']
                user_dict[user]['segundo'] += medalhas[sport][user]['segundo']
                user_dict[user]['terceiro'] += medalhas[sport][user]['terceiro']
                user_dict[user]['pontos_total'] += medalhas[sport][user]['lider'] * 3 + medalhas[sport][user]['segundo'] * 2 + medalhas[sport][user]['terceiro']

        rank = sorted(user_dict.items(), key=lambda x: x[1]['pontos_total'], reverse=True)
        msg_list = []
        for index, i in enumerate(rank):
            name, medalhas = i
            msg_list.append(f"{index+1}º - {name.title()} 🥇{medalhas['lider']} 🥈{medalhas['segundo']} 🥉{medalhas['terceiro']}")
        return "\n".join(msg_list)
