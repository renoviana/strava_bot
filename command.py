from datetime import datetime, timedelta
from secure import STRAVA_CLIENT_ID, STRAVA_REDIRECT_URI
from tools import get_markup
from rest import StravaGroup
class StravaCommands:
    strava_group = None

    def __init__(self, group_id):
        self.strava_group = StravaGroup(str(group_id))

    def send_ranking_ano_msg_command(self, _):
        """
        Send ride year rank
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
            year=datetime.now().year + 1
        )
        all_type = self.strava_group.list_type_activities(first_day=first_day, last_day=last_day)
        all_type = list(filter(lambda x: x != "activity_dict", all_type))

        if not all_type:
            return "Nenhum atividade encontrada nesse mês"

        return {
            "texto": "Selecione o tipo de esporte",
            "markup": get_markup(all_type, "syear_"),
        }

    def get_ranking_year_msg(self, callback):
        """
        Send year sport rank
        """
        sport = callback.data.replace("syear_", "")
        return self.strava_group.get_ranking_str(sport,year_rank=True)

    def send_point_msg_command(self, _):
        """
        Send score ride rank
        Args:
            message (Message): telegram message
        """
        pontos_msg = (
            "Score Mensal:\n"
            + "\n".join(self.strava_group.get_point_str())
            + "\n\nComo funciona: \n1 ponto - Ride/Run/Swim/Hike acima de 2km\n1 ponto - Pedal acima de 10km\n+1 ponto - Pedal acima de 350m de elevação\n+1 ponto - Pedal acima de 50km"
        )
        return pontos_msg

    def send_year_point_msg_command(self, _):
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
            year=datetime.now().year + 1
        )
        pontos_msg = (
            "Score Anual:\n"
            + "\n".join(self.strava_group.get_point_str(first_day, last_day))
            + "\n\nComo funciona: \n1 ponto - Ride/Run/Swim/Hike acima de 2km\n1 ponto - Pedal acima de 10km\n+1 ponto - Pedal acima de 350m de elevação\n+1 ponto - Pedal acima de 50km"
        )
        return pontos_msg

    def send_stats_command(self, _):
        """
        Send ride stats
        Args:
            message (Message): telegram message
        """
        return self.strava_group.get_stats_str()
    
    def send_year_stats_command(self, _):
        """
        Send ride stats
        Args:
            message (Message): telegram message
        """
        return self.strava_group.get_stats_str(year_stats=True)

    def admin_command(self, _):
        """
        Send admin menu
        Args:
            message (Message): telegram message
        """
        dict_user = self.strava_group.membros
        lista_user = list(dict_user.keys())

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

    def del_strava_user_callback(self, call):
        """
        Remove strava user
        """
        user_name = call.data.replace("del_strava_", "")
        user_name_admin = call.from_user.first_name or call.from_user.username
        return self.strava_group.remove_strava_user(user_name, user_name_admin)

    def get_link_command(self, message):
        """
        Send strava link
        """
        group_id = str(message.chat.id)
        return f"https://www.strava.com/oauth/authorize?client_id={STRAVA_CLIENT_ID}&redirect_uri={STRAVA_REDIRECT_URI.format(group_id)}"

    def metas_command(self, _):
        """
        Send goals menu
        """
        dict_meta = self.strava_group.metas.keys()
        return {
            "texto": "Selecione o tipo de meta",
            "markup": get_markup(
                list(map(lambda x: (x.title(), f"meta_{x}"), dict_meta)),
                delete_option=True,
                delete_data="meta",
            ),
        }

    def custom_meta_command(self, message):
        """
        Send goal question
        """
        tipo_meta = message.data.replace("meta_", "")
        return {
            "function": self.add_meta_callback,
            "texto": "Digite o valor da meta em km",
            "function_data": {
                "tipo_meta": tipo_meta,
            },
        }

    def add_meta_callback(self, message, data):
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

        self.strava_group.save_group_meta(tipo_meta, int(meta_km))

        return "Meta adicionada com sucesso"

    def del_meta_command(self, message):
        """
        Remove goal
        Args:
            message (Message): telegram message
        """
        tipo_meta = message.data.replace("del_meta_meta_", "")
        self.strava_group.save_group_meta(tipo_meta, None)
        return f"Meta {tipo_meta.title()} removida com sucesso"

    def ignore_ativities_status_callback(self, message):
        """
        Send ignored activitys
        Args:
            message (Message): telegram message
        """
        message_text = message.text
        atividade_link = message_text.replace("/ignore ", "")
        atividade_id = atividade_link.split("/")[-1]
        return self.strava_group.add_ignore_activity(atividade_id)

    def get_menu_sports_msg(self, _):
        """
        Send sport menu
        Args:
            message (Message): telegram message
        """
        all_type = self.strava_group.list_type_activities()
        all_type = list(filter(lambda x: x != "activity_dict", all_type))

        if not all_type:
            return "Nenhum atividade encontrada nesse mês"

        return {
            "texto": "Selecione o tipo de esporte",
            "markup": get_markup(all_type, "strava_"),
        }

    def get_sports_msg(self, callback):
        """
        Retorna ranking do esporte
        """
        sport_type = callback.data.replace("strava_", "")
        return self.strava_group.get_ranking_str(sport_type)

    def get_segments(self, message):
        """
        Send strava segments
        Args:
            message (Message): telegram message
        """
        max_distance = None
        distance = message.text.split(" ")
        if len(distance) > 1:
            max_distance = distance[1]
        return self.strava_group.get_segments_str(max_distance)

    def get_medalhas(self, _):
        """
        Send medal rank
        Args:
            message (Message): telegram message
        """
        return self.strava_group.get_medalhas_rank()

    def get_ticket_message(self, message):
        texto = message.text.replace("/ticket ", "")
        from_user= message.from_user
        first_name = from_user.first_name or from_user.username
        data_future = (datetime.now() + timedelta(hours=48)).strftime("%d/%m/%Y %H:%M")
        return f"Oi {first_name}!\nParabéns, você foi sorteado para desenvolver o ticket  '{texto}'.\n\nVocê tem 48hrs a partir desse momento para desenvolver o ticket, caso não consiga basta fazer uma pequena colaboração de 5g do 🇨🇴.\nSeu tempo termina: {data_future}"
