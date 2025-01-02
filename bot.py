import time
import queue
import threading
import requests
import telebot
from mongoengine import connect
from db import DbManager
from command import StravaCommands, command_dict, callback_dict
from engine import StravaDataEngine
from service import StravaApiProvider
from tools import is_group_message, send_reply_return
from secure import TELEGRAM_BOT_TOKEN, MONGO_URI, TELEGRAM_BOT_ID, HEALTH_CHECK_URL

connect(host=MONGO_URI)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
strava_dict = {}
CALLBACK_QUEUE = queue.Queue()
CURRENT_CALLBACK = None

def get_strava_command_group(group_id) -> StravaCommands:
    """
    Função para retornar a instância de StravaCommands
    Args:
        group_id (int): Id do grupo
    """
    if group_id not in strava_dict:
            strava_dict[group_id] = StravaCommands(StravaDataEngine(group_id, StravaApiProvider, DbManager))
    return strava_dict[group_id]

@bot.message_handler(content_types=["new_chat_members"])
def new_chat_handler(message):
    """
    Handler para novos usuários e também a entrada do bot no grupo
    """
    strava_command_group = get_strava_command_group(message.chat.id)
    new_user = message.json.get("new_chat_member")
    link = strava_command_group.get_link_command(message)

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
        DbManager(message.chat.id).add_strava_group()
        return "Grupo adicionado com sucesso!"

    if new_user.get("is_bot"):
        return

    bot.reply_to(message, f"Bem vindo ao grupo {new_user.get('first_name')}!\n\n Autorize seu strava nesse link para participar \n{link}")

def callback_process(call):
    try:
        strava_command_group = get_strava_command_group(call.message.chat.id)
        command_list = list(
            filter(lambda command: command[0] in call.data, callback_dict.items())
        )

        if not callback_dict:
            return

        _, command_function_name = command_list[0]
        resultado = strava_command_group.__getattribute__(command_function_name)(call)
        send_reply_return(resultado, call.message, bot, disable_web_page_preview=True)
        try:
            bot.answer_callback_query(call.id)
        except Exception as exc:
            pass
    except Exception as exc:
        if exc.args:
            send_reply_return(
                exc.args[0], call.message, bot, disable_web_page_preview=True
            )
            return

        send_reply_return(
            "Erro ao executar o comando, tente novamente.", call.message, bot, disable_web_page_preview=True
        )

@bot.callback_query_handler(func=lambda _: True)
def callback_query(call) -> None:
    """
    Handler para responder os callbacks:
    Quando um usuário clica em algum botão no bot
    """
    global CURRENT_CALLBACK, CALLBACK_QUEUE
    if CURRENT_CALLBACK:
        return CALLBACK_QUEUE.put(call)
    
    CURRENT_CALLBACK = call
    try:
        callback_process(call)
        while not CALLBACK_QUEUE.empty():
            call = CALLBACK_QUEUE.get()
            callback_process(call)
            CALLBACK_QUEUE.task_done()
    except:
        pass
    
    CURRENT_CALLBACK = None

@bot.message_handler(func=is_group_message)
def handle_group_message(message) -> None:
    """
    Handler para escutar comandos de grupo
    """
    try:
        strava_command_group = get_strava_command_group(message.chat.id)
        command = message.text[1:].split(" ")[0].replace("@bsbpedalbot", "")
        bot_member = bot.get_chat_member(message.chat.id, bot.get_me().id)
        is_bot_admin = bot_member.status in ["administrator", "creator"]

        if command not in command_dict:
            return

        result = getattr(strava_command_group, command_dict[command])(message)
        data = send_reply_return(result, message, bot, disable_web_page_preview=True)
    except Exception as exc:
        if exc.args:
            send_reply_return(
                exc.args[0], message, bot, disable_web_page_preview=True
            )
            return

        send_reply_return(
            "Erro ao executar o comando, tente novamente.", message, bot, disable_web_page_preview=True
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

def health_check():
    while True:
        requests.get(HEALTH_CHECK_URL)
        time.sleep(300)
    

health_check_thread = threading.Thread(target=health_check)
health_check_thread.daemon = True
health_check_thread.start()
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as exc:
        bot.stop_polling()