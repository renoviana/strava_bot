from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from service import StravaApiProvider


class StravaDataEngine:
    provider: StravaApiProvider
    membros = {}
    metas = {}
    ignored_activities = []

    def __init__(self, group_id, provider: StravaApiProvider, db_manager) -> None:
        self.db_manager = db_manager(group_id)
        self.group_id = group_id
        self.strava_entity = self.db_manager.get_strava_group()
        self.provider = provider(self.strava_entity.membros, self.db_manager)
        self.membros = self.strava_entity.membros
        self.metas = self.strava_entity.metas
        self.ignored_activities = self.strava_entity.ignored_activities
        self.medalhas = self.strava_entity.medalhas or {}
        self.list_activities = []
        self.last_run = None
        self.cache_last_activity = None
        self.cache_first_day = None
        self.cache_last_day = None

    def get_users_medal_dict(self, sport_type):
        """
        Retorna mensagem de vitoria
        Args:
            sport_type (str): tipo de esporte
            user_name (str): nome do usuário
        """

        user_medal_dict = {}
        for month_dict in self.medalhas.values():
            sport_dict = month_dict.get(sport_type, {})
            for user, user_position in sport_dict.items():
                if user not in user_medal_dict:
                    user_medal_dict[user] = {user_position: 1}
                    continue

                if user_position not in user_medal_dict[user]:
                    user_medal_dict[user][user_position] = 1
                    continue

                user_medal_dict[user][user_position] += 1

        return user_medal_dict

    def last_db_activity_list(self, api_activity_list, db_activity_list):
        """
        Retorna o index da ultima atividade
        Args:
            api_activity_list (list): lista de atividades da api
            db_activity_list (list): lista de atividades do banco de dados
        """
        if not db_activity_list:
            return None

        for index, data in enumerate(api_activity_list):
            if db_activity_list[0].get("id") == data["id"]:
                return index

        return None

    def list_activity(self, user_name, first_day=None, last_day=None):
        """
        Retorna lista de atividades do mês e filtra de acordo com o sport_list
        Args:
            user_name (str): usuario
            sport_list (list): lista de esportes
            first_day (datetime): data de inicio
            last_day (datetime): data de fim
        """
        activity_list = []

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

        db_activity_list = self.list_db_activity(
            first_day, last_day, self.membros.get(user_name, {}).get("athlete_id")
        )
        api_activity_list = self.provider.list_activity(
            user_name, after=first_day.timestamp(), before=last_day.timestamp()
        )

        last_index_db = self.last_db_activity_list(api_activity_list, db_activity_list)
        if last_index_db is not None:
            api_activity_list = api_activity_list[:last_index_db]

        activity_list += api_activity_list
        page = 2
        while api_activity_list and len(api_activity_list) % 100 == 0:
            api_activity_list = self.provider.list_activity(
                user_name,
                after=first_day.timestamp(),
                before=last_day.timestamp(),
                page=page,
            )

            last_index_db = self.last_db_activity_list(
                api_activity_list, db_activity_list
            )
            if last_index_db is not None:
                activity_list += api_activity_list[:last_index_db]
                break

            activity_list += api_activity_list
            page += 1

        self.db_manager.process_activities(activity_list)
        return activity_list + list(db_activity_list)

    def list_db_activity(self, first_day, last_day, user_id):
        """
        Lista atividades do banco de dados de acordo com o usuário
        Args:
            first_day (datetime): data de inicio
            last_day (datetime): data de fim
            user_id (int): id do usuário
        """
        db_activity_list = self.db_manager.list_strava_activities(
            user_id, first_day, last_day
        )
        activity_list = []
        for i in db_activity_list:
            data_dict = i.to_mongo().to_dict()
            data_dict["type"] = data_dict["activity_type"]
            data_dict["id"] = data_dict["activity_id"]
            data_dict["map"] = data_dict["activity_map"]
            del data_dict["activity_type"]
            del data_dict["activity_id"]
            del data_dict["activity_map"]
            activity_list.append(data_dict)
        return activity_list

    def list_activity_by_sport_type(self, user, first_day=None, last_day=None):
        """
        Lista atividades por tipo de esporte
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
                activity["start_date_local"] = datetime.strptime(
                    activity["start_date_local"], "%Y-%m-%dT%H:%M:%SZ"
                )

            activity_sport_type = activity["sport_type"]

            if (
                activity_sport_type == "WeightTraining"
                and activity["moving_time"] > 7200
            ):
                activity["moving_time"] = 7200

            gym_dict = self.apply_gym_rules(gym_dict, activity)

            if activity_sport_type not in activity_dict:
                activity_dict[activity_sport_type] = []

            activity_dict[activity_sport_type].append(activity)

        return activity_dict

    def apply_gym_rules(self, gym_dict, activity):
        """
        Aplica regras para atividades de musculação
        Args:
            gym_dict (dict): dicionario de atividades
            activity (dict): atividade
        """
        if activity["type"] != "WeightTraining":
            return gym_dict

        date_activity = activity["start_date_local"].replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        moving_time_ride = activity["moving_time"]

        if date_activity not in gym_dict:
            gym_dict[date_activity] = activity
            return gym_dict

        old_moving_time_ride = gym_dict[date_activity]["moving_time"]
        if old_moving_time_ride < moving_time_ride:
            gym_dict[date_activity] = activity
        return gym_dict

    def calculate_group_stats(
        self, ignore_stats_ids=None, first_day=None, last_day=None
    ):
        """
        Calcula estatísticas de atividades para cada usuário do grupo.
        Esta função gera um resumo
        das atividades de cada usuário, incluindo totais de distância,
        tempo em movimento, pontos e os valores máximos para
        distância, velocidade, velocidade média, ganho de elevação e
        tempo em movimento, juntamente com o ID da atividade
        correspondente a cada máximo.
        Args:
            ignore_stats_ids (list): lista de ids de atividades ignoradas
            first_day (datetime): data de inicio
            last_day (datetime): data de fim.
            include_activity_dict (bool): incluir dicionario de atividades no retorno. Default: False
            min_distance (int): distancia minima para considerar atividade
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
            last_day = first_day + relativedelta(months=+1)

        if not ignore_stats_ids:
            ignore_stats_ids = []

        if self.has_activities_cached(first_day, last_day):
            return self.cache_last_activity

        group_members_dict = {}

        for user in self.membros:
            activity_dict = self.list_activity_by_sport_type(
                user, first_day=first_day, last_day=last_day
            )

            if not activity_dict:
                continue

            user_dict = {"sport_stats_dict": {}, "total_points": 0, "activity_dict": {}}
            for sport_name, activity_list in activity_dict.items():
                if sport_name not in user_dict:
                    user_dict["sport_stats_dict"][sport_name] = {
                        "total_distance": 0,
                        "total_user_points": 0,
                        "total_moving_time": 0,
                        "max_distance": {"activity_id": None, "value": 0},
                        "max_velocity": {"activity_id": None, "value": 0},
                        "max_average_speed": {"activity_id": None, "value": 0},
                        "max_elevation_gain": {"activity_id": None, "value": 0},
                        "max_moving_time": {"activity_id": None, "value": 0},
                    }

                for activity in activity_list:
                    max_speed_ride_km = round(activity["max_speed"] * 3.6, 2)
                    max_average_speed_ride_km = round(
                        activity["average_speed"] * 3.6, 2
                    )
                    total_elevation_gain_ride = round(
                        activity["total_elevation_gain"], 2
                    )
                    distance_km = round(activity["distance"] / 1000, 2)
                    moving_time_ride = activity["moving_time"]

                    if self.ignore_activity_rules(activity):
                        continue

                    ignore_stats = (
                        str(activity.get("id", activity.get("activity_id")))
                        in ignore_stats_ids
                    )

                    if (
                        distance_km
                        > user_dict["sport_stats_dict"][sport_name]["max_distance"][
                            "value"
                        ]
                        and not ignore_stats
                    ):
                        user_dict["sport_stats_dict"][sport_name]["max_distance"][
                            "value"
                        ] = round(distance_km, 2)
                        user_dict["sport_stats_dict"][sport_name]["max_distance"][
                            "activity_id"
                        ] = activity.get("id")

                    if (
                        max_speed_ride_km
                        > user_dict["sport_stats_dict"][sport_name]["max_velocity"][
                            "value"
                        ]
                        and not ignore_stats
                    ):
                        user_dict["sport_stats_dict"][sport_name]["max_velocity"][
                            "value"
                        ] = round(max_speed_ride_km, 2)
                        user_dict["sport_stats_dict"][sport_name]["max_velocity"][
                            "activity_id"
                        ] = activity.get("id")

                    if (
                        max_average_speed_ride_km
                        > user_dict["sport_stats_dict"][sport_name][
                            "max_average_speed"
                        ]["value"]
                        and not ignore_stats
                    ):
                        user_dict["sport_stats_dict"][sport_name]["max_average_speed"][
                            "value"
                        ] = round(max_average_speed_ride_km, 2)
                        user_dict["sport_stats_dict"][sport_name]["max_average_speed"][
                            "activity_id"
                        ] = activity.get("id")

                    if (
                        total_elevation_gain_ride
                        > user_dict["sport_stats_dict"][sport_name][
                            "max_elevation_gain"
                        ]["value"]
                        and not ignore_stats
                    ):
                        user_dict["sport_stats_dict"][sport_name]["max_elevation_gain"][
                            "value"
                        ] = round(total_elevation_gain_ride, 2)
                        user_dict["sport_stats_dict"][sport_name]["max_elevation_gain"][
                            "activity_id"
                        ] = activity.get("id")

                    if (
                        moving_time_ride
                        > user_dict["sport_stats_dict"][sport_name]["max_moving_time"][
                            "value"
                        ]
                        and not ignore_stats
                    ):
                        user_dict["sport_stats_dict"][sport_name]["max_moving_time"][
                            "value"
                        ] = moving_time_ride
                        user_dict["sport_stats_dict"][sport_name]["max_moving_time"][
                            "activity_id"
                        ] = activity.get("id")

                    user_dict["sport_stats_dict"][sport_name]["total_user_points"] = (
                        round(
                            self.calc_point_rank(
                                user_dict["sport_stats_dict"][sport_name][
                                    "total_user_points"
                                ],
                                total_elevation_gain_ride,
                                distance_km,
                                sport_name,
                            ),
                            2,
                        )
                    )
                    user_dict["total_points"] = round(
                        user_dict["total_points"]
                        + user_dict["sport_stats_dict"][sport_name][
                            "total_user_points"
                        ],
                        2,
                    )
                    user_dict["sport_stats_dict"][sport_name]["total_distance"] = round(
                        user_dict["sport_stats_dict"][sport_name]["total_distance"]
                        + distance_km,
                        2,
                    )
                    user_dict["sport_stats_dict"][sport_name]["total_moving_time"] = (
                        round(
                            user_dict["sport_stats_dict"][sport_name][
                                "total_moving_time"
                            ]
                            + moving_time_ride
                        )
                    )

                user_dict["activity_dict"] = activity_dict

            group_members_dict[user] = user_dict

        self.cache_last_activity = group_members_dict
        self.cache_first_day = first_day
        self.cache_last_day = last_day
        self.last_run = datetime.now()
        return group_members_dict

    def has_activities_cached(self, first_day, last_day):
        """
        Verifica se as atividades estão em cache
        Args:
            first_day (datetime): data de inicio
            last_day (datetime): data de fim
        """
        return (
            self.last_run
            and datetime.now() - timedelta(minutes=2) < self.last_run
            and self.cache_last_day == last_day
            and self.cache_first_day == first_day
        )

    def ignore_activity_rules(self, activity, min_distance=None):
        """
        Ignora atividades com menos de 5 minutos, mais de 400 km ou atividades manuais que não sejam de natação ou musculação
        Args:
            activity (dict): atividade
        """
        ignore_min_distance = False
        if min_distance:
            ignore_min_distance = activity["distance"] < int(min_distance)
        total_distance_and_moving_time_zero = (
            activity.get("total_distance") == 0
            and activity.get("total_moving_time") == 0
        )
        total_moving_time_less_than_5 = activity.get("moving_time") < 300
        distance_greater_than_400 = round(activity.get("distance") / 1000, 2) > 400
        return (
            total_distance_and_moving_time_zero
            or total_moving_time_less_than_5
            or distance_greater_than_400
            or ignore_min_distance
        )

    def list_points(self, first_day=None, last_day=None):
        """
        Retorna lista de pontos dos usuários
        """
        distance_list = []
        ignore_stats_ids = self.ignored_activities or []
        group_members_dict = self.calculate_group_stats(
            ignore_stats_ids=ignore_stats_ids, first_day=first_day, last_day=last_day
        )
        for user, activity_dict in group_members_dict.items():
            if activity_dict["total_points"] == 0:
                continue

            distance_list.append({"user": user, "point": activity_dict["total_points"]})

        sort_distance_list = sorted(
            distance_list, key=lambda k: k["point"], reverse=True
        )

        return list(
            map(
                lambda x: f"{x[0]+1}º - {x[1].get('user').title()} - {x[1].get('point')} {'ponto' if x[1].get('point') == 1 else 'pontos'}",
                enumerate(sort_distance_list),
            )
        )

    def get_stats(self, first_day=None, last_day=None):
        """
        Retorna estatísticas do grupo
        Args:
            first_day (datetime): data de inicio
            last_day (datetime): data de fim
        """
        max_metrics = {
            "max_distance": {},
            "max_velocity": {},
            "max_average_speed": {},
            "max_elevation_gain": {},
            "max_moving_time": {},
        }
        group_members_dict = self.calculate_group_stats(
            ignore_stats_ids=self.ignored_activities,
            first_day=first_day,
            last_day=last_day,
        )
        for user_name, activity_dict in group_members_dict.items():
            ride_dict = activity_dict["sport_stats_dict"].get("Ride")
            if not ride_dict:
                continue

            for metric, _ in max_metrics.items():
                current_value = ride_dict[metric]["value"]
                if (
                    not max_metrics[metric]
                    or current_value > max_metrics[metric]["value"]
                ):
                    max_metrics[metric] = {
                        "user": user_name,
                        "value": current_value,
                        "activity_id": ride_dict[metric]["activity_id"],
                    }

        return max_metrics

    def list_type_activities(self, first_day=None, last_day=None):
        """
        Retorna lista de distancias dos usuários
        """
        all_types = []
        group_members_dict = self.calculate_group_stats(
            first_day=first_day, last_day=last_day
        )
        for activity_list in group_members_dict.values():
            all_types += list(activity_list["sport_stats_dict"].keys())

        all_types = list(set(all_types))
        return sorted(all_types)

    def get_sport_rank(
        self, sport_type, year_rank=False, first_day=None, last_day=None
    ):
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
                year=datetime.now().year + 1,
            )
        ignore_stats_ids = self.ignored_activities
        distance_list = []
        group_members_dict = self.calculate_group_stats(
            ignore_stats_ids=ignore_stats_ids, first_day=first_day, last_day=last_day
        )
        for user_name, activity_dict in group_members_dict.items():
            json_data = activity_dict["sport_stats_dict"].get(sport_type)

            if not json_data:
                continue

            json_data["user"] = user_name
            json_data["user_id"] = self.membros.get(user_name).get("athlete_id")
            distance_list.append(json_data)

        return distance_list

    def get_ranking_str(self, sport_type, year_rank=False):
        """
        Calcula o rank dos usuários
        Args:
            sport_type (str): tipo de esporte
            year_rank (bool): ranking do ano
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

        medal_dict = {
            1: "🥇",
            2: "🥈",
            3: "🥉",
        }

        emoji = emoji_dict.get(sport_type, sport_type)
        today_str = datetime.now().strftime("%B")

        if year_rank:
            today_str = datetime.now().year

        user_medal_dict = self.get_users_medal_dict(sport_type)
        metas = self.metas.get(sport_type.lower())
        msg_template = f"Ranking {today_str} {emoji}:\n"
        rank_params, rank_unit = self.get_rank_params_and_unit(sport_type)
        distance_list = self.get_sport_rank(
            sport_type, year_rank, first_day=None, last_day=None
        )
        sort_distance_list = sorted(
            distance_list, key=lambda k: k[rank_params], reverse=True
        )

        position = 1
        position_value = sort_distance_list[0].get(rank_params)
        rank_msg_list = []
        for distance_user in sort_distance_list:
            emoji = ""
            medal_str = ""
            activity_value = distance_user.get(rank_params)
            user_name = distance_user.get("user").title()
            user_id = distance_user.get("user_id")

            if distance_user.get(rank_params) <= 0:
                continue

            if activity_value != position_value:
                position = position + 1
                position_value = activity_value

            if metas and activity_value >= metas:
                emoji = "✅"

            if rank_params == "total_moving_time":
                activity_value = f"{int(activity_value // 3600):02}:{int((activity_value % 3600) // 60):02}:{int(activity_value % 60):02}"

            user_medal = dict(sorted(user_medal_dict.get(user_name, {}).items()))
            for medal_position, count in user_medal.items():
                medal_str += f"{medal_dict[medal_position]}{count}"

            user_link = (
                f'<a href="https://www.strava.com/athletes/{user_id}">{user_name}</a>'
            )
            rank_msg_list.append(
                f"{position}º - {user_link}{medal_str} - {activity_value}{rank_unit} {emoji}"
            )

        msg = "\n".join(rank_msg_list)
        msg = msg_template + msg

        if not year_rank and metas:
            msg += f"\n\n⚠️ Meta individual do mês: {metas}{rank_unit}"

        return msg

    def get_rank_params_and_unit(self, sport_type):
        """
        Retorna os parametros de rank e unidade
        Args:
            sport_type (str): tipo de esporte
        """
        sport_rank_by_time_list = [
            "workout",
            "weighttraining",
            "velomobile",
            "standuppaddling",
            "yoga",
            "stairstepper",
        ]
        rank_params = "total_distance"
        rank_unit = "km"

        if sport_type.lower() in sport_rank_by_time_list:
            rank_params = "total_moving_time"
            rank_unit = ""
        return rank_params, rank_unit

    def remove_strava_user(self, user_name):
        """
        Remove usuário do strava
        Args:
            user_name (str): nome do usuário
            user_name_admin (str): nome do admin
        """
        user_name = user_name.split(" - ")[0]
        membros = self.db_manager.remove_strava_user(user_name)
        self.membros = membros

    def save_group_meta(self, tipo_meta, km):
        """
        Salva meta do grupo
        Args:
            tipo_meta (str): tipo de meta
            km (int): km
        """
        metas = self.db_manager.update_meta(tipo_meta, km)
        self.metas = metas

    def calc_point_rank(
        self, total_user_points, total_elevation_gain_ride_m, distance_km, sport_type
    ):
        """
        Calcula o rank de pontos
        Args:
            total_user_points (int): total de pontos
            total_elevation_gain_ride_m (int): total de elevação
            distance_km (int): distancia
        """
        if distance_km >= 1 and sport_type == "Swim":
            total_user_points += 1
            return total_user_points

        if distance_km > 2 and sport_type in ["Run", "Walk", "Hike"]:
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
        self.ignored_activities = self.db_manager.add_ignore_activity(activity_id)

    def get_medalhas_rank(self):
        """
        Retorna o ranking geral de medalhas
        """
        from collections import defaultdict

        medals = defaultdict(lambda: {"🥇": 0, "🥈": 0, "🥉": 0, "pontos": 0})

        for _, sports in self.medalhas.items():
            for _, rankings in sports.items():
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
        sorted_medals = sorted(
            medals.items(),
            key=lambda x: (-x[1]["pontos"], -x[1]["🥇"], -x[1]["🥈"], -x[1]["🥉"]),
        )

        # Exibir os resultados no formato desejado
        msg_list = []
        rank = 1
        pontos = sorted_medals[0][1]["pontos"]
        for rank, (person, counts) in enumerate(sorted_medals, 1):
            if counts["pontos"] < pontos:
                rank = rank + 1
                pontos = counts["pontos"]
            msg_list.append(
                f"{rank}º - {person} 🥇{counts['🥇']} 🥈{counts['🥈']} 🥉{counts['🥉']} | {counts['pontos']} pts"
            )

        return "\n".join(msg_list)

    def get_frequency(self, first_day=None, last_day=None, month_days=None, title=""):
        """
        Retorna a frequência de atividades dos usuários
        Args:
            first_day (datetime): data de inicio
            last_day (datetime): data de fim
            month_days (int): quantidade de dias no mês
            title (str): titulo
        """
        if not month_days:
            title = "Quantidade de dias com atividades no mês:"
            month_days = datetime.now().day

        date_dict = {}
        for membro in self.membros:
            activity = self.list_activity(
                membro, first_day=first_day, last_day=last_day
            )
            if membro not in date_dict:
                date_dict[membro] = {}

            for a in activity:
                start_date_local = a["start_date_local"]
                if isinstance(start_date_local, str):
                    start_date_local = datetime.strptime(
                        start_date_local, "%Y-%m-%dT%H:%M:%SZ"
                    )
                date = start_date_local.strftime("%Y-%m-%d")
                date_dict[membro][date] = True
                pass

            if len(date_dict[membro]) == 0:
                del date_dict[membro]
                continue

            date_dict[membro] = len(date_dict[membro])

        if not date_dict:
            return

        # Order by value
        date_dict = dict(
            sorted(date_dict.items(), key=lambda item: item[1], reverse=True)
        )
        msg_list = [title]
        rank_position = 1
        current_value = list(date_dict.values())[0]
        for name, valor in date_dict.items():
            if valor != current_value:
                rank_position = rank_position + 1
                current_value = valor
            msg_list.append(f"{rank_position}º - {name.title()} - {valor}/{month_days}")
        return "\n".join(msg_list)

    def get_medalhas_var(self):
        """
        Retorna o ranking de medalhas por esporte e mês
        """
        from collections import defaultdict

        medals = defaultdict(
            lambda: {
                "🥇": 0,
                "🥈": 0,
                "🥉": 0,
                "detalhes": defaultdict(lambda: {"🥇": [], "🥈": [], "🥉": []}),
            }
        )

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

        sorted_medals = sorted(
            medals.items(), key=lambda x: (-x[1]["🥇"], -x[1]["🥈"], -x[1]["🥉"])
        )
        msg_list = []

        for rank, (person, counts) in enumerate(sorted_medals, 1):
            msg_list.append(
                f"\n{rank}º - {person} 🥇{counts['🥇']} 🥈{counts['🥈']} 🥉{counts['🥉']}"
            )
            for sport, detalhes in counts["detalhes"].items():
                msg_list.append(f"{sport} -")
                for medalha, meses in detalhes.items():
                    if meses:
                        msg_list.append(f"{medalha} - {', '.join(meses)}")

        return "\n".join(msg_list)

    def get_segments_rank(self, segment_id):
        """
        Retorna o ranking de um segmento
        Args:
            segment_id (int): id do segmento
        """
        lista_membros = []
        for membro_name in self.membros:
            segment_data = self.provider.get_segment(membro_name, segment_id)

            if "errors" in segment_data:
                raise Exception(f"Erro ao buscar segmento: {segment_data['message']}")

            athlete_has_segment = segment_data.get("athlete_segment_stats")
            if not athlete_has_segment["pr_elapsed_time"]:
                continue

            pr_elapsed_time = athlete_has_segment["pr_elapsed_time"]
            pr_elapsed_time = f"{pr_elapsed_time // 60}:{pr_elapsed_time % 60:02}"
            pr_date = datetime.strptime(
                athlete_has_segment["pr_date"], "%Y-%m-%d"
            ).strftime("%d/%m/%Y")
            lista_membros.append(
                {
                    "membro_name": membro_name,
                    "pr_elapsed_time": pr_elapsed_time,
                    "pr_date": pr_date,
                    "str": f"<a href='https://www.strava.com/activities/{athlete_has_segment['pr_activity_id']}'>{membro_name} - {pr_elapsed_time} {pr_date}</a>",
                }
            )
        lista_membros = sorted(lista_membros, key=lambda x: x["pr_elapsed_time"])

        if not lista_membros:
            return "Nenhum membro tem o segmento"

        msg = [
            f"<a href='https://www.strava.com/segments/{segment_id}'>{segment_data['name']} - {round(segment_data['distance'] / 1000, 2)}km</a>"
        ]
        return "\n".join(
            msg
            + [
                f"{membro[0]} - {membro[1]['str']}"
                for membro in enumerate(lista_membros, 1)
            ]
        )

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
        group_members_dict = self.calculate_group_stats(
            ignore_stats_ids=ignore_stats_ids
        )
        all_segments = {}

        for name, token in group_members:
            activities = self._get_user_activities(
                name, group_members_dict, min_distance, ignore_stats_ids
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
        activity_list = user_data.get(name, {}).get("activity_dict", {}).get("Ride", [])
        filtered_activities = []

        for activity in activity_list:
            if activity["distance"] < int(min_distance):
                continue
            activity_id = activity["id"]
            if str(activity_id) in ignore_stats_ids:
                continue
            activity["id"] = activity_id
            filtered_activities.append(activity)

        return filtered_activities

    def _process_activity_segments(
        self, activity, user_name, token, min_distance, all_segments
    ):
        """
        Processes an activity to collect segment efforts.

        Args:
            activity (dict): The activity data.
            user_name (str): The user's name.
            token (dict): The user's token.
            min_distance (int): The minimum distance.
            all_segments (dict): Dictionary to collect all segment efforts.
        """
        activity_data = self.provider.get_activity(user_name, activity["id"])
        segment_efforts = activity_data.get("segment_efforts", [])

        for segment_effort in segment_efforts:
            if segment_effort["distance"] < int(min_distance):
                continue

            if segment_effort["segment"]["id"] in [18536734, 683759]:
                continue

            segment_effort.update(
                {
                    "user": user_name,
                    "access_token": token["access_token"],
                    "refresh_token": token["refresh_token"],
                    "atividade_id": activity["id"],
                }
            )
            segment_id = segment_effort["segment"]["id"]

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
        filtered_segments = {k: v for k, v in all_segments.items() if len(v) > 2}

        for segment_list in filtered_segments.values():
            for segment in segment_list:
                try:
                    segment_data = self.provider.get_segment_effort(
                        segment["user"], segment["id"]
                    )
                except Exception as e:
                    continue

                activity_id = segment_data["segment"]["id"]
                segment_data.update(
                    {"user": segment["user"], "atividade_id": segment["atividade_id"]}
                )
                athlete_ids[segment["athlete"]["id"]] = True

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
                segments[0]["name"],
                " - ",
                str(round(segments[0]["distance"] / 1000, 2)),
                "km",
                " - ",
                str(segments[0]["segment"]["id"]),
            ]

            str_list.append(f"{''.join(data)}")
            segments = sorted(segments, key=lambda x: x["moving_time"])
            athelete_list = []
            for segment in segments:
                segment_athlete = segment["user"]
                start_date_local = segment["start_date_local"]
                segment["start_date_local"] = datetime.strptime(
                    start_date_local, "%Y-%m-%dT%H:%M:%SZ"
                )

                if segment_athlete in athelete_list:
                    continue

                athelete_list.append(segment_athlete)
                segment_min = f"{int(segment['moving_time'] // 3600):02}:{int((segment['moving_time'] % 3600) // 60):02}:{int(segment['moving_time'] % 60):02}"
                msg_str = f"- <a href=\"https://www.strava.com/activities/{segment['activity']['id']}/segments/{segment['id']}\">{segment_athlete} - {segment_min}</a>"
                str_list.append(msg_str)
            str_list.append("")

        return "\n".join(str_list)

    def reset_rank(self):
        """
        Reseta o rank
        """
        self.db_manager.remove_activities({"group_id": self.group_id})
        self.get_sport_rank("Ride", year_rank=True)
