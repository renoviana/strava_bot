from datetime import datetime, timedelta
import functools
from secure import STRAVA_CLIENT_ID, STRAVA_REDIRECT_URI, TICKET_MESSAGE
from tools import get_markup
from rest import StravaDataEngine

command_dict = {}
callback_dict = {}

def TelegramCommand(command: str):
        def decorator(func):
            command_dict[command] = func.__name__
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator

def TelegramCallback(command: str):
    def decorator(func):
        callback_dict[command] = func.__name__
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

class StravaCommands:
    strava_engine: StravaDataEngine = None
    def __init__(self, strava_engine: StravaDataEngine):
        self.strava_engine = strava_engine

    @TelegramCommand("year")
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
        all_type = self.strava_engine.list_type_activities(first_day=first_day, last_day=last_day)
        all_type = list(filter(lambda x: x != "activity_dict", all_type))

        if not all_type:
            return "Nenhum atividade encontrada nesse mês"

        return {
            "texto": "Selecione o tipo de esporte",
            "markup": get_markup(all_type, "syear_"),
        }

    @TelegramCommand("score")
    def send_point_msg_command(self, _):
        """
        Send score ride rank
        Args:
            message (Message): telegram message
        """

        array_msg = [
            "Como funciona: ",
            "1 ponto - Run/Swim/Hike acima de 2km",
            "1 ponto - Pedal acima de 10km",
            "+1 ponto - Pedal acima de 350m de elevação",
            "+1 ponto - Pedal acima de 50km",
            "+1 ponto - Pedal acima de 100km",
        ]
        array_msg = '\n'.join(array_msg)
        points_str = '\n'.join(self.strava_engine.get_point_str())
        pontos_msg = f"Score Mensal:\n{points_str}\n\n{array_msg}"
        return pontos_msg

    @TelegramCommand("yscore")
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
            + "\n".join(self.strava_engine.get_point_str(first_day, last_day))
            + "\n\nComo funciona: \n1 ponto - Ride/Run/Swim/Hike acima de 2km\n1 ponto - Pedal acima de 10km\n+1 ponto - Pedal acima de 350m de elevação\n+1 ponto - Pedal acima de 50km"
        )
        return pontos_msg

    @TelegramCommand("stats")
    def send_stats_command(self, _):
        """
        Send ride stats
        Args:
            message (Message): telegram message
        """
        return self.strava_engine.get_stats_str()
    
    @TelegramCommand("ystats")
    def send_year_stats_command(self, _):
        """
        Send ride stats
        Args:
            message (Message): telegram message
        """
        return self.strava_engine.get_stats_str(year_stats=True)

    @TelegramCommand("admin")
    def admin_command(self, _):
        """
        Send admin menu
        Args:
            message (Message): telegram message
        """
        dict_user = self.strava_engine.membros
        lista_user = []
        for membro, data in dict_user.items():
            data = data.get('created_at')
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
    def get_link_command(self, message):
        """
        Send strava link
        """
        group_id = str(message.chat.id)
        return f"https://www.strava.com/oauth/authorize?client_id={STRAVA_CLIENT_ID}&redirect_uri={STRAVA_REDIRECT_URI.format(group_id)}"

    @TelegramCommand("metas")
    def metas_command(self, _):
        """
        Send goals menu
        """
        dict_meta = self.strava_engine.metas.keys()
        return {
            "texto": "Selecione o tipo de meta",
            "markup": get_markup(
                list(map(lambda x: (x.title(), f"meta_{x}"), dict_meta)),
                delete_option=True,
                delete_data="meta",
            ),
        }

    @TelegramCommand("rank")
    @TelegramCommand("sport")
    def get_menu_sports_command(self, _):
        """
        Send sport menu
        Args:
            message (Message): telegram message
        """
        all_type = self.strava_engine.list_type_activities()
        all_type = list(filter(lambda x: x != "activity_dict", all_type))

        if not all_type:
            return "Nenhum atividade encontrada nesse mês"

        return {
            "texto": "Selecione o tipo de esporte",
            "markup": get_markup(all_type, "strava_"),
        }

    @TelegramCommand("segments")
    def get_segments_command(self, message):
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

    @TelegramCommand("medalhas")
    def get_medalhas_command(self, _):
        """
        Send medal rank
        Args:
            message (Message): telegram message
        """
        return self.strava_engine.get_medalhas_rank()
    
    @TelegramCommand("medalhasvar")
    def get_medalhas_var_command(self, _):
        """
        Send medal rank
        Args:
            message (Message): telegram message
        """
        return self.strava_engine.get_medalhas_var()

    @TelegramCommand("ticket")
    def get_ticket_command(self, message):
        texto = message.text.replace("/ticket ", "")
        from_user= message.from_user
        first_name = from_user.first_name or from_user.username
        data_future = (datetime.now() + timedelta(hours=48)).strftime("%d/%m/%Y %H:%M")
        return f"Oi {first_name}!\nParabéns, você foi sorteado para desenvolver o ticket  '{texto}'.\n\n{TICKET_MESSAGE}\nSeu tempo termina: {data_future}"

    @TelegramCommand("frequency")
    def get_frequency_command(self, _):
        """
        Send month rank
        Args:
            message (Message): telegram message
        """
        return self.strava_engine.get_frequency()
    
    @TelegramCommand("yfrequency")
    def get_year_frequency_command(self, _):
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
            year=datetime.now().year + 1
        )
        data = datetime.now().timetuple().tm_yday
        return self.strava_engine.get_frequency(first_day, last_day, data, "Quantidade de dias com atividades no ano:")
    
    @TelegramCommand("segment")
    def get_segment_rank_command(self, message):
        """
        Send segment rank
        Args:
            message (Message): telegram message
        """
        segment_id = message.text.replace("/segment ", "")
        return self.strava_engine.get_segments_rank(int(segment_id))
    
    @TelegramCommand("ignore")
    def ignore_ativities_status_command(self, message):
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
    
    @TelegramCallback("syear_")
    def get_ranking_year_callback(self, callback):
        """
        Send year sport rank
        Args:
            callback (Callback): telegram callback
        """
        sport = callback.data.replace("syear_", "")
        return self.strava_engine.get_ranking_str(sport,year_rank=True)

    @TelegramCallback("del_strava")
    def del_strava_user_callback(self, callback):
        """
        Remove strava user
        Args:
            callback (Callback): telegram callback
        """
        user_name = callback.data.replace("del_strava_", "")
        user_name_admin = callback.from_user.first_name or callback.from_user.username
        self.strava_engine.remove_strava_user(user_name, user_name_admin)
        return f"Usuário {user_name} removido com sucesso pelo {user_name_admin}!"

    @TelegramCallback("meta_")
    def custom_meta_callback(self, callback):
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
    def del_meta_callback(self, callback):
        """
        Remove goal
        Args:
            callback (Callback): telegram callback
        """
        tipo_meta = callback.data.replace("del_meta_meta_", "")
        self.strava_engine.save_group_meta(tipo_meta, None)
        return f"Meta {tipo_meta.title()} removida com sucesso"

    @TelegramCallback("strava_")
    def get_sports_msg_callback(self, callback):
        """
        Retorna ranking do esporte
        Args:
            callback (Callback): telegram callback
        """
        sport_type = callback.data.replace("strava_", "")
        return self.strava_engine.get_ranking_str(sport_type)