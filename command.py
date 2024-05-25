from model import get_strava_group
from tools import get_markup
from rest import (
    add_ignore_activity,
    get_point_str,
    get_ranking_str,
    get_stats_str,
    list_type_activities,
    remove_strava_user,
    save_group_meta,
    get_segments_str,
)






def send_ranking_msg_command(message):
    """
    Envia ranking do pedal do strava
    Args:
        message (Message): mensagem do telegram
    """
    return get_ranking_str(str(message.chat.id), 'Ride')

def send_ranking_ano_msg_command(message):
    """
    Envia ranking do pedal do strava
    Args:
        message (Message): mensagem do telegram
    """
    return get_ranking_str(str(message.chat.id), 'Ride',year_rank=True)

def send_run_msg_command(message):
    """
    Envia ranking da corrida do strava
    Args:
        message (Message): mensagem do telegram
    """
    return get_ranking_str(str(message.chat.id),'Run')

def send_run_ano_msg_command(message):
    """
    Envia ranking da corrida do strava
    Args:
        message (Message): mensagem do telegram
    """
    return get_ranking_str(str(message.chat.id),'Run', year_rank=True)

def send_point_msg_command(message):
    """
    Envia pontos do strava
    Args:
        message (Message): mensagem do telegram
    """
    group_id = str(message.chat.id)
    pontos_msg = (
        "\n".join(get_point_str(group_id))
        + "\n\nComo funciona: \n1 ponto - Pedal a cima de 5km\n+1 ponto - Pedal a cima de 350m de elevação\n+1 ponto - Pedal a cima de 50km"
    )
    return pontos_msg


def send_stats_command(message):
    """
    Envia o status geral do strava
    Args:
        message (Message): mensagem do telegram
    """
    group_id = str(message.chat.id)
    return get_stats_str(group_id)

def admin_command(message):
    """
    Retorna o menu de admin do strava
    Args:
        message (Message): mensagem do telegram
    """
    dict_user = get_strava_group(str(message.chat.id)).membros
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
    Deleta usuário do strava
    """
    user_name = call.data.replace("del_strava_", "")
    group_id = str(call.message.chat.id)
    user_name_admin = call.from_user.first_name or call.from_user.username
    return remove_strava_user(user_name, group_id, user_name_admin)


def get_link_command(message):
    """
    Retorna link
    """
    group_id = str(message.chat.id)
    return f"https://www.strava.com/oauth/authorize?client_id=36564&redirect_uri=http://www.renoviana.com.br/api/strava/{group_id}&response_type=code&scope=activity:read_all,profile:read_all,read_all"


def metas_command(message):
    """
    Retorna metas
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
    Retorna perguntando o valor da meta
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
    Adiciona meta
    Args:
        message (Message): mensagem do telegram
        data (dict): dados da função
    """
    meta_km = message.text
    tipo_meta = data.get("tipo_meta")

    if not meta_km.isnumeric():
        return "Valor invalido, informe apenas numeros"

    save_group_meta(message.chat.id, tipo_meta, int(meta_km))

    return "Meta adicionada com sucesso"


def del_meta_command(message):
    """
    Deleta meta
    Args:
        message (Message): mensagem do telegram
    """
    tipo_meta = message.data.replace("del_meta_meta_", "")
    save_group_meta(message.json.get("message").get("chat").get("id"), tipo_meta, None)
    return f"Meta {tipo_meta.title()} removida com sucesso"


def ignore_ativities_status_callback(message):
    message_text = message.text
    atividade_link = message_text.replace("/ignore ", "")
    atividade_id = atividade_link.split("/")[-1]
    return add_ignore_activity(message.chat.id, atividade_id)


def get_menu_sports_msg(message):
    all_type = list_type_activities(message.chat.id)

    if not all_type:
        return "Nenhum atividade encontrada nesse mês"

    return {
        "texto": "Selecione o tipo de esporte",
        "markup": get_markup(all_type, f"strava_"),
    }

def get_sports_msg(callback):
    sport_type = callback.data.replace("strava_", "")
    return get_ranking_str(str(callback.message.chat.id), sport_type)

def get_segments(message):
    group_id = str(message.chat.id)
    return get_segments_str(group_id)