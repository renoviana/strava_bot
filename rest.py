from datetime import datetime
import requests
from model import add_strava_group, get_strava_group
from secure import (
    PEDAL_TELEGRAM_GROUP_ID,
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

    def get_strava_api(
        self,
        url,
        params,
        user,):
        """
        Retorna dados de atividades em formato json
        Args:
            after_date (str): Data de inicio
            before_date (str): Data de fim
            user (str): usuario
            access_token (str): access token
            refresh_token (str): refresh token
            page (int): pagina
            per_page (int): quantidade de atividades por pagina
        """
        access_token, refresh_token = self.get_user_access_and_refresh_token(user)
        params["access_token"] = access_token

        response = requests.get(url, params=params)
        
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
        self.membros[athlete_name] = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "athlete_id": athlete_id,
        }
        self.update_entity()

    def update_user_token(self, user, refresh_token):
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
        user_at = self.membros[user].get("access_token")
        user_rt = self.membros[user].get("refresh_token")
        return user_at, user_rt
    
    def list_month_activity(
        self,
        user=None,
        sport_list=None,
        first_day=None,
        last_day=None,):
        """
        Retorna lista de atividades do mês e filtra de acordo com o sport_list
        Args:
            access_token (str): access token
            refresh_token (str): refresh token
            user (str): usuario
            sport_list (list): tipo de esporte
            first_day (datetime): data de inicio
            last_day (datetime): data de fim
        """

        token = self.membros[user]

        # if last_activity_date and not last_day and sport_list and (len(sport_list) == 0 or "Ride" in sport_list):
        #     first_day = datetime.fromtimestamp(last_activity_date)

        # if last_activity_date and sport_list and "Ride" in sport_list and first_day.month != datetime.now().month and not last_day:
        #     activity_list = []
        #     first_day = None

        # if  sport_list and "Ride" not in sport_list:
        #     activity_list = []

        if not first_day:
            first_day = datetime.now().replace(
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

        if not last_day:
            final_month = datetime.now().month + 1
            year = datetime.now().year

            if datetime.now().month == 12:
                final_month = 1
                year = datetime.now().year + 1


            last_day = datetime.now().replace(
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
                month=final_month,
                year=year
            )

        new_activity_list = self.get_athlete_data(
            after_date=first_day,
            before_date=last_day,
            user=user,
        )

        page = 1
        while len(new_activity_list) % 100 == 0 and len(new_activity_list) != 0:
            page += 1
            new_activity_list += self.get_athlete_data(
                token['access_token'],
                token['refresh_token'],
                user=user,
                after_date=first_day,
                before_date=last_day,
                page=page,
            )
        

        # if new_activity_list and is_month:
        #     self.membros[user]["activity_list"] = activity_list
        #     start_date = activity_list[0]["start_date"]
        #     start_date = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ").timestamp()
        #     self.membros[user]["last_activity_date"] = start_date
        #     self.save()

        if not sport_list:
            return new_activity_list, len(new_activity_list) > 0

        return list(filter(lambda x: x["type"] in sport_list, new_activity_list)), len(new_activity_list) > 0
    
    def get_athlete_data(
        self,
        after_date=None,
        before_date=None,
        user=None,
        page=1,
        per_page=100):
        """
        Retorna dados ded atividades em formato json
        Args:
            after_date (str): Data de inicio
            before_date (str): Data de fim
            user (str): usuario
            access_token (str): access token
            refresh_token (str): refresh token
            page (int): pagina
            per_page (int): quantidade de atividades por pagina
        """
        url = "https://www.strava.com/api/v3/athlete/activities"
        access_token, refresh_token = self.get_user_access_and_refresh_token(user)
        params = {"access_token": access_token, "page": page, "per_page": per_page}

        if after_date:
            params["after"] = after_date.timestamp()

        if before_date:
            params["before"] = before_date.timestamp()

        response = self.get_strava_api(url, params, user)
        return response.json()
    
    def update_entity(self):
        self.strava_entity.metas = self.metas
        self.strava_entity.membros = self.membros
        self.strava_entity.ignored_activities = self.ignored_activities
        self.strava_entity.save()

    def get_distance_and_points(
    self, sport_type=None, user=None, ignore_stats_ids=None, ignore_cache=False, first_day=None, last_day=None):
        """
        Calcula a distancia total e os pontos do usuário
        Args:
            sport_type (str): tipo de esporte
            user (str): usuario
            ignore_stats_ids (list): lista de ids de atividades ignoradas
            ignore_cache (bool): ignora cache
            first_day (datetime): data de inicio
            last_day (datetime): data de fim
        """


        if not sport_type:
            sport_type = "Ride"

        sport_list = [sport_type]
        
        ride_list, has_new_ride = self.list_month_activity(
            user=user,
            sport_list=sport_list,
            first_day=first_day,
            last_day=last_day,
        )
        
        if not has_new_ride and "Ride" in sport_list and self.membros[user].get("stats", {}).get(sport_type) and not ignore_cache:
            return self.membros[user].get("stats").get(sport_type)

        result_dict = {
            "total_distance": 0,
            "total_user_points": 0,
            "total_moving_time": 0,
            "max_distance": {"activity_id":None, "value":0},
            "max_velocity": {"activity_id":None, "value":0},
            "max_average_speed": {"activity_id":None, "value":0},
            "max_elevation_gain": {"activity_id":None, "value":0},
            "max_moving_time": {"activity_id":None, "value":0},
        }

        for ride in ride_list:
            max_speed_ride_km = round(ride["max_speed"] * 3.6, 2)
            max_average_speed_ride_km = round(ride["average_speed"] * 3.6, 2)
            total_elevation_gain_ride = ride["total_elevation_gain"]
            distance_km = ride["distance"] / 1000
            moving_time_ride = ride["moving_time"] / 60

            if moving_time_ride < 5:
                continue

            manual_ride = ride["manual"]
            ignore_stats = str(ride.get('id')) in ignore_stats_ids

            if distance_km > 400:
                continue

            if manual_ride:
                continue

            if distance_km > result_dict["max_distance"]['value'] and not ignore_stats:
                result_dict["max_distance"]['value'] = distance_km
                result_dict["max_distance"]['activity_id'] = ride.get('id')

            if max_speed_ride_km > result_dict["max_velocity"]['value'] and not ignore_stats and max_speed_ride_km < 80:
                result_dict["max_velocity"]['value'] = max_speed_ride_km
                result_dict["max_velocity"]['activity_id'] = ride.get('id')

            # Ignora atividades manuais no calculo de velocidade média maxima
            if (
                max_average_speed_ride_km > result_dict["max_average_speed"]['value']
                and not ignore_stats
            ):
                result_dict["max_average_speed"]['value'] = max_average_speed_ride_km
                result_dict["max_average_speed"]['activity_id'] = ride.get('id')

            if total_elevation_gain_ride > result_dict["max_elevation_gain"]['value']  and not ignore_stats:
                result_dict["max_elevation_gain"]['value'] = total_elevation_gain_ride
                result_dict["max_elevation_gain"]['activity_id'] = ride.get('id')

            if moving_time_ride > result_dict["max_moving_time"]['value'] and not ignore_stats:
                result_dict["max_moving_time"]['value'] = moving_time_ride
                result_dict["max_moving_time"]['activity_id'] = ride.get('id')

            result_dict["total_user_points"] = self.calc_point_rank(
                result_dict["total_user_points"], total_elevation_gain_ride, distance_km
            )
            result_dict["total_distance"] += distance_km
            result_dict["total_moving_time"] += moving_time_ride

        return result_dict

    def list_distance_user(self, only_desafio=False, sport_type=None, first_day=None, last_day=None, sort_by='total_distance'):
        """
        Retorna lista de distancias dos usuários
        Args:
            group_id (str): id do grupo
            only_desafio (bool): apenas desafio
            sport_type (str): tipo de esporte
        """
        ignore_stats_ids = self.ignored_activities
        distance_list = []
        for user, strava in self.membros.items():
            if only_desafio and strava.get("beta"):
                continue

            json_data = self.get_distance_and_points(
                sport_type,
                user=user,
                ignore_stats_ids=ignore_stats_ids,
                ignore_cache=last_day is not None,
                first_day=first_day,
                last_day=last_day,
            )

            total_distance = round(json_data["total_distance"], 2)
            total_user_points = round(json_data["total_user_points"], 2)
            total_moving_time = round(json_data.get("total_moving_time",0), 2)
            max_distance = round(json_data["max_distance"]['value'], 2)
            max_velocity = round(json_data["max_velocity"]['value'], 2)
            max_average_speed = round(json_data["max_average_speed"]['value'], 2)
            max_elevation_gain = round(json_data["max_elevation_gain"]['value'], 2)
            max_moving_time = round(json_data["max_moving_time"]['value'], 2)
            distance_list.append(
                {
                    "user": user,
                    "user_id": strava["athlete_id"],
                    "total_distance": total_distance,
                    "total_user_points": total_user_points,
                    "total_moving_time": total_moving_time,
                    "max_distance": max_distance,
                    "max_velocity": max_velocity,
                    "max_average_speed": max_average_speed,
                    "max_elevation_gain": max_elevation_gain,
                    "max_moving_time": max_moving_time,

                })
            
            # if "stats" not in self.membros[user]:
            #     self.membros[user]["stats"] = {}

            # if not last_day:
            #     self.membros[user]["stats"][sport_type] = {
            #         "user": user,
            #         "user_id": strava["athlete_id"],
            #         "total_distance": total_distance,
            #         "total_user_points": total_user_points,
            #         "total_moving_time": total_moving_time,
            #         "max_distance": json_data["max_distance"],
            #         "max_velocity": json_data["max_velocity"],
            #         "max_average_speed": json_data["max_average_speed"],
            #         "max_elevation_gain": json_data["max_elevation_gain"],
            #         "max_moving_time": json_data["max_moving_time"],

            #     }


        sort_distance_list = sorted(
            distance_list, key=lambda k: k[sort_by], reverse=True
        )

        return sort_distance_list
    
    def get_point_str(self):
        """
        Retorna lista de pontos dos usuários
        Args:
            group_id (str): id do grupo
        """
        distance_list = []
        ignore_stats_ids = self.ignored_activities or []
        for user, strava in self.membros.items():
            distance = self.get_distance_and_points(
                user=user,
                ignore_stats_ids=ignore_stats_ids
            )
            total_user_points = distance["total_user_points"]

            if total_user_points == 0:
                continue

            distance_list.append({"user": user, "point": total_user_points})
        sort_distance_list = sorted(distance_list, key=lambda k: k["point"], reverse=True)

        return list(
            map(
                lambda x: f"{x[0]+1}º - {x[1].get('user').capitalize()} - {x[1].get('point')} {'ponto' if x[1].get('point') == 1 else 'pontos'}",
                enumerate(sort_distance_list),
            )
        )

    def get_stats_str(self):
        """
        Retorna lista de pontos dos usuários
        Args:
            group_id (str): id do grupo
        """
        ignore_stats_ids = self.ignored_activities
        max_distance_geral = {"user": '', "value": 0, "activity_id": None}
        max_velocity_geral = {"user": '', "value": 0, "activity_id": None}
        max_average_spee_gerald = {"user": '', "value": 0, "activity_id": None}
        max_elevation_gain_geral = {"user": '', "value": 0, "activity_id": None}
        max_moving_time_geral = {"user": '', "value": 0, "activity_id": None}
        for user, strava in self.membros.items():
            distance = self.get_distance_and_points(
                user=user,
                ignore_stats_ids=ignore_stats_ids
            )


            if distance["max_distance"]["value"] > max_distance_geral["value"]:
                max_distance_geral["user"] = user
                max_distance_geral["value"] = distance["max_distance"]["value"]
                max_distance_geral["activity_id"] = distance["max_distance"]["activity_id"]
            if distance["max_velocity"]["value"] > max_velocity_geral["value"]:
                max_velocity_geral["user"] = user
                max_velocity_geral["value"] = distance["max_velocity"]["value"]
                max_velocity_geral["activity_id"] = distance["max_velocity"]["activity_id"]
            if distance["max_average_speed"]["value"] > max_average_spee_gerald["value"]:
                max_average_spee_gerald["user"] = user
                max_average_spee_gerald["value"] = distance["max_average_speed"]["value"]
                max_average_spee_gerald["activity_id"] = distance["max_average_speed"]["activity_id"]
            if distance["max_elevation_gain"]["value"] > max_elevation_gain_geral["value"]:
                max_elevation_gain_geral["user"] = user
                max_elevation_gain_geral["value"] = distance["max_elevation_gain"]["value"]
                max_elevation_gain_geral["activity_id"] = distance["max_elevation_gain"]["activity_id"]
            if distance["max_moving_time"]["value"] > max_moving_time_geral["value"]:
                max_moving_time_geral["user"] = user
                max_moving_time_geral["value"] = distance["max_moving_time"]["value"]
                max_moving_time_geral["activity_id"] = distance["max_moving_time"]["activity_id"]

        
        msg_texto = "🚲💨  Estatísticas do mês 🚲💨\n"
        msg_texto += f"Maior distância: <a href=\"https://www.strava.com/activities/{max_distance_geral['activity_id']}\">{round(max_distance_geral['value'],2)}km - {max_distance_geral['user'].capitalize()}</a>\n"
        msg_texto += f"Maior velocidade: <a href=\"https://www.strava.com/activities/{max_velocity_geral['activity_id']}\">{round(max_velocity_geral['value'],2)}km/h - {max_velocity_geral['user'].capitalize()}</a>\n"
        msg_texto += f"Maior velocidade média: <a href=\"https://www.strava.com/activities/{max_average_spee_gerald['activity_id']}\">{round(max_average_spee_gerald['value'],2)}km/h - {max_average_spee_gerald['user'].capitalize()}</a>\n"
        msg_texto += f"Maior ganho de elevação: <a href=\"https://www.strava.com/activities/{max_elevation_gain_geral['activity_id']}\">{round(max_elevation_gain_geral['value'],2)}m - {max_elevation_gain_geral['user'].capitalize()}</a>\n"
        msg_texto += f"Maior tempo de movimento: <a href=\"https://www.strava.com/activities/{max_moving_time_geral['activity_id']}\">{round(max_moving_time_geral['value'],2)}min - {max_moving_time_geral['user'].capitalize()}</a>\n"
        return msg_texto

    def list_type_activities(self):
        """
        Retorna lista de distancias dos usuários
        Args:
            group_id (str): id do grupo
            only_desafio (bool): apenas desafio
            sport_type (str): tipo de esporte
        """
        all_types = []
        for user, strava in self.membros.items():
            ride_list, has_new_ride = self.list_month_activity(
                user
            )
            all_types += list(map(lambda x: x["type"], ride_list))
        all_types = list(set(all_types))
        return all_types

    def rank_format(self, object_data, sport_type, rank_unit="km", rank_params='total_distance'):
        """
        Formata o rank
        Args:
            object_data (tuple): tupla com index e dados
            group_id (str): id do grupo
            sport_type (str): tipo de esporte
        """
        strava_month_distance = (
            self.metas.get(sport_type)
        )
        
        index_data, data = object_data
        rank_data = data.get(rank_params)
        emoji = ""

        if strava_month_distance and rank_data >= strava_month_distance:
            emoji = "✅"
        user_id = data.get("user_id")
        user_name = data.get('user').title()

        if user_id:
            user_name = f"<a href=\"https://www.strava.com/athletes/{user_id}\">{data.get('user').title()}</a>"

        return f"{index_data+1}º - {user_name} - {rank_data}{rank_unit} {emoji}"

    def get_ranking_str(self, sport_type , year_rank=False, first_day=None, last_day=None):
        """
        Envia mensagem com o ranking do pedal
        Args:
            grupo_id (str): id do grupo
        """
        only_desafio = self.group_id == str(PEDAL_TELEGRAM_GROUP_ID)

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

        msg_template = f"Ranking {today_str} {emoji}:\n"
        sport_rank_by_time_list = ['workout', 'weighttraining']
        rank_params = 'total_distance'
        rank_unit="km"

        if sport_type.lower() in sport_rank_by_time_list:
                rank_params = 'total_moving_time'
                rank_unit = "min"
        
        distance_list = self.list_distance_user(only_desafio, sport_type, first_day=first_day, last_day=last_day, sort_by=rank_params)
        rank_msg_list = list(
            map(
                lambda i: self.rank_format(i, sport_type.lower(), rank_unit=rank_unit, rank_params=rank_params),
                filter( lambda i: i[1].get(rank_params) > 0, enumerate(distance_list)),
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
            group_id (str): id do grupo
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
            group_id (str): id do grupo
            tipo_meta (str): tipo de meta
            km (int): km da meta
        """
        if km:
            km = int(km)
        self.metas[tipo_meta] = km
        self.update_entity()

    def calc_point_rank(self, total_user_points, total_elevation_gain_ride_m, distance_km):
        """
        Calcula o rank de pontos
        Args:
            total_user_points (int): total de pontos
            total_elevation_gain_ride (int): total de elevação
            distance_km (int): distancia em km
        """
        if distance_km > 5:
            total_user_points += 1

        if distance_km > 50:
            total_user_points += 1

        if total_elevation_gain_ride_m > 350:
            total_user_points += 1
        return total_user_points

    def add_ignore_activity(self, activity_id):
        ignore_stats_ids = self.ignored_activities or []
        ignore_stats_ids.append(str(activity_id))
        self.ignored_activities = ignore_stats_ids
        self.update_entity()
        return "Atividade ignorada com sucesso!"

    def get_segments_str(self, min_distance=6000):
        ignore_stats_ids = self.ignored_activities
        grupo_members = list(self.membros.items())
        all_segments = []
        for nome,token in grupo_members:

            data, has_new_ride = self.list_month_activity(
                nome
            )

            activity_list = data

            for atividade in activity_list:
                if atividade['distance'] < min_distance:
                    continue

                atividade_id = atividade['id']
                
                if str(atividade_id) in ignore_stats_ids:
                    continue


                atividade_data = self.get_strava_api(f"https://www.strava.com/api/v3/activities/{atividade_id}", {}, nome).json()
                segment_afforts = atividade_data['segment_efforts']
                for segment in segment_afforts:
                    if segment['distance'] < min_distance:
                        continue

                    segment['user'] = nome
                    segment['access_token'] = token['access_token']
                    segment['refresh_token'] = token['refresh_token']
                    segment['atividade_id'] = atividade_id

                    all_segments.append(segment)

            pass

        segment_dict = {}
        athelete_id = {

        }
        for segment in all_segments:
            segment_data = self.get_strava_api(f"https://www.strava.com/api/v3/segment_efforts/{segment['id']}", {}, segment['user']).json()
            atividade_id = segment_data['segment']['id']
            segment_data['user'] = segment['user']
            segment_data['atividade_id'] = segment['atividade_id']
            athelete_id[segment['athlete']['id']] = True
            
            if atividade_id not in segment_dict:
                segment_dict[atividade_id] = []

            segment_dict[atividade_id].append(segment_data)

        str_list = []
        for atividade_id, segments in segment_dict.items():
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
                segment_id = segment['id']
                url = f"<a href=\"https://www.strava.com/activities/{str(segment['atividade_id'])}/segments/{str(segment_id)}\">{segment_min}min - {segment_date}</a>"
                str_list.append('- '+segment_athlete+"\n"+url)
            str_list.append("")

        return "\n".join(str_list)
