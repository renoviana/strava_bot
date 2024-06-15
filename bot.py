import telebot
from mongoengine import connect
from model import add_strava_group
from command import (
    get_link_command,
    admin_command,
    custom_meta_command,
    del_meta_command,
    del_strava_user_callback,
    get_menu_sports_msg,
    get_segments,
    get_sports_msg,
    send_point_msg_command,
    send_ranking_ano_msg_command,
    send_ranking_msg_command,
    send_stats_command,
    metas_command,
    ignore_ativities_status_callback,)
from tools import is_group_message, return_has_result
from secure import TELEGRAM_BOT_TOKEN, MONGO_URI, TELEGRAM_BOT_ID

connect(host=MONGO_URI)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

grupo_commands = {
    "rank": send_ranking_msg_command,
    'year':send_ranking_ano_msg_command,
    "score": send_point_msg_command,
    "stats": send_stats_command,
    "admin": admin_command,
    "link": get_link_command,
    "metas": metas_command,
    "ignore": ignore_ativities_status_callback,
    "sports": get_menu_sports_msg,
    "segments": get_segments,
}

query_commands = {
    "del_meta": del_meta_command,
    "del_strava": del_strava_user_callback,
    "meta_": custom_meta_command,
    "strava_": get_sports_msg,
}

grupo_commands_admin = ["admin", "metas"]



@bot.message_handler(content_types=[
    "new_chat_members"
])
def new_chat_handler(message):
    """
    Handler para novos usuários e também a entrada do bot no grupo
    """
    new_user = message.json.get("new_chat_member")
    link = get_link_command(message)

    if new_user.get('id') == TELEGRAM_BOT_ID:
        bot.reply_to(
            message,
            "Strava Bot configurado com sucesso!\nAcesse o menu para ver os comandos disponiveis."
        )
        bot.reply_to(
            message,
            f"Para começar a usar, autorize seu strava nesse link"\
            f"\n{link}"
        )
        add_strava_group(message.chat.id)
        return "Grupo adicionado com sucesso!"

    if new_user.get("is_bot"):
        return

    bot.reply_to(message, f"Bem vindo ao grupo {new_user.get('first_name')}!\n\n Autorize seu strava nesse link para participar \n{link}")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call) -> None:
    """
    Handler para responder os callbacks:
    Quando um usuário clica em algum botão no bot
    """
    
    try:
        command_list = list(
            filter(lambda command: command[0] in call.data, query_commands.items())
        )

        if not command_list:
            return

        _, command_function = command_list[0]
        resultado = command_function(call)
        return_has_result(resultado, call.message, bot)
        try:
            bot.answer_callback_query(call.id)
        except Exception as exc:
            pass
    except Exception as exc:
        return_has_result(
            "Erro ao executar o comando, tente novamente.", call.message, bot
        )

    


@bot.message_handler(func=is_group_message)
def handle_group_message(message) -> None:
    """
    Handler para escutar comandos de grupo
    """
    try:
        command = message.text[1:].split(" ")[0]
        bot_member = bot.get_chat_member(message.chat.id, bot.get_me().id)
        is_bot_admin = bot_member.status in ["administrator", "creator"]

        command = command.replace("@bsbpedalbot", "")

        if command not in grupo_commands:
            return

        result = grupo_commands[command](message)
        data = return_has_result(result, message, bot)
    except Exception as exc:
        return_has_result(
            "Erro ao executar o comando, tente novamente.", message, bot
        )
        return

    if is_bot_admin and data:
        bot.pin_chat_message(message.chat.id, data.message_id)

@bot.message_handler(func=lambda x: not is_group_message(x))
def commands_handler(message) -> None:
    """
    Handler que escuta todos os comandos cadastrados na lista
    """
    return bot.reply_to(
        message,
        "Bem vindo ao Strava Bot!"\
        "\nEsse bot foi desenvolvido para funcionar apenas em grupos do telegram"\
        ", para utiliza-lo crie um grupo e me adicione. :)")

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as exc:
        bot.stop_polling()