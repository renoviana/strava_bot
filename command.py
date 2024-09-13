from datetime import datetime, timedelta
from secure import STRAVA_CLIENT_ID, STRAVA_REDIRECT_URI
from tools import get_markup
from rest import StravaGroup

def send_ranking_msg_command(message):
    """
    Send ride rank
    Args:
        message (Message): telegram message
    """

    return StravaGroup(str(message.chat.id)).get_ranking_str('Ride')

def send_ranking_ano_msg_command(message):
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
    all_type = StravaGroup(str(message.chat.id)).list_type_activities(first_day=first_day, last_day=last_day)

    if not all_type:
        return "Nenhum atividade encontrada nesse mês"

    return {
        "texto": "Selecione o tipo de esporte",
        "markup": get_markup(all_type, "syear_"),
    }

def get_ranking_year_msg(callback):
    """
    Send year sport rank
    """
    sport = callback.data.replace("syear_", "")
    return StravaGroup(str(callback.message.chat.id)).get_ranking_str(sport,year_rank=True)

def send_point_msg_command(message):
    """
    Send score ride rank
    Args:
        message (Message): telegram message
    """
    pontos_msg = (
        "\n".join(StravaGroup(str(message.chat.id)).get_point_str())
        + "\n\nComo funciona: \n1 ponto - Caminhada/corrida acima de 2km\n1 ponto - Pedal acima de 10km\n+1 ponto - Pedal acima de 350m de elevação\n+1 ponto - Pedal acima de 50km"
    )
    return pontos_msg


def send_stats_command(message):
    """
    Send ride stats
    Args:
        message (Message): telegram message
    """
    return StravaGroup(str(message.chat.id)).get_stats_str()

def admin_command(message):
    """
    Send admin menu
    Args:
        message (Message): telegram message
    """
    dict_user = StravaGroup(str(message.chat.id)).membros
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

def del_strava_user_callback(call):
    """
    Remove strava user
    """
    user_name = call.data.replace("del_strava_", "")
    group_id = str(call.message.chat.id)
    user_name_admin = call.from_user.first_name or call.from_user.username
    return StravaGroup(str(group_id)).remove_strava_user(user_name, user_name_admin)


def get_link_command(message):
    """
    Send strava link
    """
    group_id = str(message.chat.id)
    return f"https://www.strava.com/oauth/authorize?client_id={STRAVA_CLIENT_ID}&redirect_uri={STRAVA_REDIRECT_URI.format(group_id)}"


def metas_command(_):
    """
    Send goals menu
    """
    return {
        "texto": "Selecione o tipo de meta",
        "markup": get_markup(
            [
                ("Bicicleta", "meta_ride"),
                ("Corrida/Caminhada", "meta_run"),
            ],
            delete_option=True,
            delete_data="meta",
        ),
    }


def custom_meta_command(message):
    """
    Send goal question
    """
    tipo_meta = message.data.replace("meta_", "")
    return {
        "function": add_meta_callback,
        "texto": "Digite o valor da meta em km",
        "function_data": {
            "tipo_meta": tipo_meta,
        },
    }


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

    StravaGroup(str(message.chat.id)).save_group_meta(tipo_meta, int(meta_km))

    return "Meta adicionada com sucesso"


def del_meta_command(message):
    """
    Remove goal
    Args:
        message (Message): telegram message
    """
    tipo_meta = message.data.replace("del_meta_meta_", "")
    StravaGroup(str(message.chat.id)).save_group_meta(tipo_meta, None)
    return f"Meta {tipo_meta.title()} removida com sucesso"


def ignore_ativities_status_callback(message):
    """
    Send ignored activitys
    Args:
        message (Message): telegram message
    """
    message_text = message.text
    atividade_link = message_text.replace("/ignore ", "")
    atividade_id = atividade_link.split("/")[-1]
    return StravaGroup(str(message.chat.id)).add_ignore_activity(atividade_id)


def get_menu_sports_msg(message):
    """
    Send sport menu
    Args:
        message (Message): telegram message
    """
    all_type = StravaGroup(str(message.chat.id)).list_type_activities()

    if not all_type:
        return "Nenhum atividade encontrada nesse mês"

    return {
        "texto": "Selecione o tipo de esporte",
        "markup": get_markup(all_type, "strava_"),
    }

def get_sports_msg(callback):
    """
    Retorna ranking do esporte
    """
    sport_type = callback.data.replace("strava_", "")
    return StravaGroup(str(callback.message.chat.id)).get_ranking_str(sport_type)

def get_segments(message):
    """
    Send strava segments
    Args:
        message (Message): telegram message
    """
    return StravaGroup(str(message.chat.id)).get_segments_str()

def get_medalhas(message):
    """
    Send medal rank
    Args:
        message (Message): telegram message
    """
    return StravaGroup(str(message.chat.id)).get_medalhas_rank()

def get_ticket_message(message):
    texto = message.text.replace("/ticket ", "")
    from_user= message.from_user
    first_name = from_user.first_name or from_user.username
    data_future = datetime.now() + timedelta(hours=48).strftime("%d/%m/%Y %H:%M")
    return f"Oi {first_name}!\nParabéns, você foi sorteado para desenvolver o ticket  '{texto}'.\n\nVocê tem 48hrs a partir desse momento para desenvolver o ticket, caso não consiga basta fazer uma pequena colaboração de 5g do 🇨🇴.\nSeu tempo termina: {data_future}"
