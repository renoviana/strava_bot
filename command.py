from datetime import datetime, timedelta
from secure import STRAVA_CLIENT_ID, STRAVA_REDIRECT_URI, TICKET_MESSAGE, ADMIN_ID
from tools import TelegramCommand, TelegramCallback, get_markup
from engine import StravaDataEngine


class StravaCommands:
    strava_engine: StravaDataEngine = None

    def __init__(self, strava_engine: StravaDataEngine):
        self.strava_engine = strava_engine

    @TelegramCommand("year")
    def year_rank_command(self, _):
        """
        Send menu year rank
        Args:
            _ (Message): telegram message
        """
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
        year_activities_list = self.strava_engine.list_type_activities(
            first_day=first_day, last_day=last_day
        )

        if not year_activities_list:
            return "Nenhuma atividade encontrada"

        return {
            "texto": "Selecione o esporte",
            "markup": get_markup(year_activities_list, "syear_"),
        }

    @TelegramCommand("score")
    def score_command(self, _):
        """
        Send score ride rank
        Args:
            message (Message): telegram message
        """

        rules_list = [
            "Como funciona: ",
            "1 ponto - Run/Swim/Hike acima de 2km",
            "1 ponto - Pedal acima de 10km",
            "+1 ponto - Pedal acima de 350m de elevação",
            "+1 ponto - Pedal acima de 50km",
            "+1 ponto - Pedal acima de 100km",
        ]

        point_list = self.strava_engine.list_points()

        if not point_list:
            return "Nenhuma atividade encontrada nesse mês"

        rules_str = "\n".join(rules_list)
        points_str = "\n".join(point_list)
        pontos_msg = f"Score Mensal:\n{points_str}\n\n{rules_str}"
        return pontos_msg

    @TelegramCommand("yscore")
    def year_score_command(self, _):
        """
        Send score ride rank
        Args:
            message (Message): telegram message
        """
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
        rules_list = [
            "Como funciona: ",
            "1 ponto - Run/Swim/Hike acima de 2km",
            "1 ponto - Pedal acima de 10km",
            "+1 ponto - Pedal acima de 350m de elevação",
            "+1 ponto - Pedal acima de 50km",
            "+1 ponto - Pedal acima de 100km",
        ]

        point_list = self.strava_engine.list_points(
            first_day=first_day, last_day=last_day
        )

        if not point_list:
            return "Nenhuma atividade encontrada nesse ano"

        rules_str = "\n".join(rules_list)
        points_str = "\n".join(point_list)
        pontos_msg = f"Score Anual:\n{points_str}\n\n{rules_str}"
        return pontos_msg

    @TelegramCommand("stats")
    @TelegramCommand("ystats")
    def stats_command(self, message):
        """
        Send ride stats
        Args:
            message (Message): telegram message
        """
        first_day, last_day = None, None
        date_str = "mês"

        if message.text == "/ystats@bsbpedalbot":
            first_day = datetime.now().replace(
                day=1, hour=0, minute=0, second=0, microsecond=0, month=1
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
            date_str = "ano"

        max_metrics = self.strava_engine.get_stats(first_day, last_day)

        if not max_metrics["max_distance"]:
            return "Não há atividades para gerar estatísticas"

        msg_texto = f"🚲💨  Estatísticas do {date_str} 🚲💨\n"
        msg_texto += f"Maior distância: <a href=\"https://www.strava.com/activities/{max_metrics['max_distance']['activity_id']}\">{round(max_metrics['max_distance']['value'],2)}km - {max_metrics['max_distance']['user'].title()}</a>\n"
        msg_texto += f"Maior velocidade: <a href=\"https://www.strava.com/activities/{max_metrics['max_velocity']['activity_id']}\">{round(max_metrics['max_velocity']['value'],2)}km/h - {max_metrics['max_velocity']['user'].title()}</a>\n"
        msg_texto += f"Maior velocidade média: <a href=\"https://www.strava.com/activities/{max_metrics['max_average_speed']['activity_id']}\">{round(max_metrics['max_average_speed']['value'],2)}km/h - {max_metrics['max_average_speed']['user'].title()}</a>\n"
        msg_texto += f"Maior ganho de elevação: <a href=\"https://www.strava.com/activities/{max_metrics['max_elevation_gain']['activity_id']}\">{round(max_metrics['max_elevation_gain']['value'],2)}m - {max_metrics['max_elevation_gain']['user'].title()}</a>\n"
        msg_texto += f"Maior tempo de movimento: <a href=\"https://www.strava.com/activities/{max_metrics['max_moving_time']['activity_id']}\">{int(max_metrics['max_moving_time']['value'] // 3600):02}:{int((max_metrics['max_moving_time']['value'] % 3600) // 60):02}:{int(max_metrics['max_moving_time']['value'] % 60):02} - {max_metrics['max_moving_time']['user'].title()}</a>\n"
        return msg_texto

    @TelegramCommand("admin")
    def admin_command(self, _):
        """
        Send admin menu
        Args:
            message (Message): telegram message
        """
        self.strava_engine.load_strava_entity()
        dict_user = self.strava_engine.membros
        lista_user = []
        for membro, data in dict_user.items():
            data = data.get("created_at")
            data_str = data.strftime("%d/%m/%Y %H:%M")
            lista_user.append(f"{membro} - {data_str}")

        if len(lista_user) == 0:
            return "Nenhum usuário cadastrado"

        return {
            "texto": "Usuários cadastradas:",
            "markup": get_markup(
                lista_user,
                delete_option=True,
                delete_data="strava",
            ),
        }

    @TelegramCommand("link")
    def link_command(self, message):
        """
        Send strava link
        """
        group_id = str(message.chat.id)
        return f"https://www.strava.com/oauth/authorize?client_id={STRAVA_CLIENT_ID}&redirect_uri={STRAVA_REDIRECT_URI.format(group_id)}"

    @TelegramCommand("metas")
    def group_goals_command(self, _):
        """
        Send goals menu
        """
        goals_dict = self.strava_engine.metas.keys()
        return {
            "texto": "Selecione a meta",
            "markup": get_markup(
                list(map(lambda x: (x.title(), f"meta_{x}"), goals_dict)),
                delete_option=True,
                delete_data="meta",
            ),
        }

    @TelegramCommand("rank")
    @TelegramCommand("sports")
    def list_sport_command(self, _):
        """
        Send sport menu
        Args:
            message (Message): telegram message
        """
        all_type = self.strava_engine.list_type_activities()

        if not all_type:
            return "Nenhum atividade encontrada nesse mês"

        return {
            "texto": "Selecione o tipo de esporte",
            "markup": get_markup(all_type, "strava_"),
        }

    @TelegramCommand("medalhas")
    def group_medals_command(self, _):
        """
        Send medal rank
        Args:
            message (Message): telegram message
        """
        return self.strava_engine.get_medalhas_rank()

    @TelegramCommand("medalhasvar")
    def group_medals_var_command(self, _):
        """
        Send medal rank
        Args:
            message (Message): telegram message
        """
        return self.strava_engine.get_medalhas_var()

    @TelegramCommand("ticket")
    def ticket_command(self, message):
        """
        Send ticket message
        Args:
            message (Message): telegram message
        """
        texto = message.text.replace("/ticket ", "")
        from_user = message.from_user
        first_name = from_user.first_name or from_user.username
        data_future = (datetime.now() + timedelta(hours=48)).strftime("%d/%m/%Y %H:%M")
        return f"Oi {first_name}!\nParabéns, você foi sorteado para desenvolver o ticket  '{texto}'.\n\n{TICKET_MESSAGE}\nSeu tempo termina: {data_future}"

    @TelegramCommand("frequency")
    def frequency_command(self, _):
        """
        Send month rank
        Args:
            message (Message): telegram message
        """
        frequency = self.strava_engine.get_frequency()

        if not frequency:
            return "Nenhuma atividade encontrada nesse mês"

        return frequency

    @TelegramCommand("yfrequency")
    def year_frequency_command(self, _):
        """
        Send year rank
        Args:
            message (Message): telegram message
        """
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
        data = datetime.now().timetuple().tm_yday

        frequency = self.strava_engine.get_frequency(
            first_day, last_day, data, "Quantidade de dias com atividades no ano:"
        )

        if not frequency:
            return "Nenhuma atividade encontrada nesse ano"

        return frequency

    @TelegramCommand("segment")
    def segment_command(self, message):
        """
        Send segment rank
        Args:
            message (Message): telegram message
        """
        segment_id = message.text.split(" ")

        if len(segment_id) < 2 or segment_id[1] == "":
            return "Informe o ID do segmento"

        return self.strava_engine.get_segments_rank(int(segment_id))

    @TelegramCommand("ignore")
    def ignore_ativities_command(self, message):
        """
        Send ignored activitys
        Args:
            message (Message): telegram message
        """
        message_text = message.text
        atividade_link = message_text.replace("/ignore ", "")
        atividade_id = atividade_link.split("/")[-1]
        self.strava_engine.add_ignore_activity(atividade_id)
        return "Atividade ignorada com sucesso!"

    @TelegramCallback("strava_")
    @TelegramCallback("syear_")
    def rank_callback(self, callback):
        """
        Send rank
        Args:
            callback (Callback): telegram callback
        """
        year_rank = "syear" in callback.data
        sport_name = callback.data.replace("syear_", "").replace("strava_", "")
        return self.strava_engine.get_ranking_str(sport_name, year_rank=year_rank)

    @TelegramCallback("del_strava")
    def delete_user_callback(self, callback):
        """
        Remove strava user
        Args:
            callback (Callback): telegram callback
        """
        user_name = callback.data.replace("del_strava_", "")
        user_name_admin = callback.from_user.first_name or callback.from_user.username
        self.strava_engine.remove_strava_user(user_name)
        return f"Usuário {user_name} removido com sucesso pelo {user_name_admin}!"

    @TelegramCallback("meta_")
    def update_meta_callback(self, callback):
        """
        Send goal question
        Args:
            callback (Callback): telegram callback
        """

        def add_meta_callback(message, data):
            """
            Add sport goal
            Args:
                message (Message): telegram message
                data (dict): dados da função
            """
            meta_km = message.text
            tipo_meta = data.get("tipo_meta")

            if not meta_km.isnumeric():
                return "Valor invalido, informe apenas numeros"

            self.strava_engine.save_group_meta(tipo_meta, int(meta_km))

            return "Meta adicionada com sucesso"

        tipo_meta = callback.data.replace("meta_", "")
        return {
            "function": add_meta_callback,
            "texto": "Digite o valor da meta em km",
            "function_data": {
                "tipo_meta": tipo_meta,
            },
        }

    @TelegramCallback("del_meta")
    def delete_meta_callback(self, callback):
        """
        Remove goal
        Args:
            callback (Callback): telegram callback
        """
        tipo_meta = callback.data.replace("del_meta_meta_", "")
        self.strava_engine.save_group_meta(tipo_meta, None)
        return f"Meta {tipo_meta.title()} removida com sucesso"

    @TelegramCommand("segments")
    def segments_command(self, message):
        """
        Send strava segments
        Args:
            message (Message): telegram message
        """
        max_distance = None
        distance = message.text.split(" ")
        if len(distance) > 1:
            max_distance = distance[1]
        return self.strava_engine.get_segments_str(max_distance)

    @TelegramCommand("resetar")
    def resetar_rank(self, user):
        """
        Resetar rank
        Args:
            message (Message): telegram message
        """
        if user.from_user.id != ADMIN_ID:
            return "Você não tem permissão para executar esse comando"

        self.strava_engine.reset_rank()
        return "Dados resetados com sucesso"
