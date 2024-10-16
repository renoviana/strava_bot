import queue
import time
import requests
import telebot
import threading
from mongoengine import connect
from model import add_strava_group
from command import StravaCommands
from tools import is_group_message, send_reply_return
from secure import HEALTH_CHECK_URL, TELEGRAM_BOT_TOKEN, MONGO_URI, TELEGRAM_BOT_ID

connect(host=MONGO_URI)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

strava_dict = {}
CALLBACK_QUEUE = queue.Queue()
CURRENT_CALLBACK = None

grupo_commands = {
    "rank": 'get_menu_sports_msg',
    'year':'send_ranking_ano_msg_command',
    "score": 'send_point_msg_command',
    "yscore": 'send_year_point_msg_command',
    "stats": 'send_stats_command',
    "ystats": 'send_year_stats_command',
    "admin": 'admin_command',
    "link": 'get_link_command',
    "metas": 'metas_command',
    "ignore": 'ignore_ativities_status_callback',
    "sports": 'get_menu_sports_msg',
    "segments": 'get_segments',
    "medalhas": 'get_medalhas',
    "medalhasvar": 'get_medalhas_var',
    "ticket": 'get_ticket_message',
    'frequency': 'get_frequency_message',
    'yfrequency': 'get_year_frequency_message'
}

query_commands = {
    "del_meta": 'del_meta_command',
    "del_strava": 'del_strava_user_callback',
    "meta_": 'custom_meta_command',
    "strava_": 'get_sports_msg',
    "syear_": 'get_ranking_year_msg',
}

grupo_commands_admin = ["admin", "metas"]



@bot.message_handler(content_types=[
    "new_chat_members"
])
def new_chat_handler(message):
    """
    Handler para novos usuários e também a entrada do bot no grupo
    """
    if message.chat.id not in strava_dict:
        strava_dict[message.chat.id] = StravaCommands(message.chat.id)

    strava_command = strava_dict[message.chat.id]
    new_user = message.json.get("new_chat_member")
    link = strava_command.get_link_command(message)

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

def callback_process(call):
    try:
        if call.message.chat.id not in strava_dict:
            strava_dict[call.message.chat.id] = StravaCommands(call.message.chat.id)
        strava_command = strava_dict[call.message.chat.id]
        command_list = list(
            filter(lambda command: command[0] in call.data, query_commands.items())
        )

        if not command_list:
            return

        _, command_function_name = command_list[0]
        resultado = strava_command.__getattribute__(command_function_name)(call)
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



def loop_callback():
    global CALLBACK_QUEUE
    while not CALLBACK_QUEUE.empty():
        call = CALLBACK_QUEUE.get()
        callback_process(call)
        CALLBACK_QUEUE.task_done()

@bot.callback_query_handler(func=lambda _: True)
def callback_query(call) -> None:
    """
    Handler para responder os callbacks:
    Quando um usuário clica em algum botão no bot
    """
    global CURRENT_CALLBACK, CALLBACK_QUEUE
    print(call.data)
    if CURRENT_CALLBACK:
        return CALLBACK_QUEUE.put(call)
    
    CURRENT_CALLBACK = call
    try:
        callback_process(call)
        loop_callback()
    except:
        pass
    
    CURRENT_CALLBACK = None

@bot.message_handler(func=is_group_message)
def handle_group_message(message) -> None:
    """
    Handler para escutar comandos de grupo
    """
    try:
        if message.chat.id not in strava_dict:
            strava_dict[message.chat.id] = StravaCommands(message.chat.id)

        strava_command = strava_dict[message.chat.id]
        command = message.text[1:].split(" ")[0]
        bot_member = bot.get_chat_member(message.chat.id, bot.get_me().id)
        is_bot_admin = bot_member.status in ["administrator", "creator"]

        command = command.replace("@bsbpedalbot", "")

        if command not in grupo_commands:
            return
        result = strava_command.__getattribute__(grupo_commands[command])(message)
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