import functools
import logging

import mongoengine
import telebot
from telebot.util import extract_command, quick_markup

from application.commands.streak import handle_streak_command
from application.commands.frequency import (
    handle_month_frequency_command,
    handle_year_frequency_command,
)
from application.commands.rank import (
    handle_rank_month_command,
    handle_rank_year_command,
    handle_rank_menu,
)
from application.commands.medal import handle_medal_command
from application.commands.admin import (
    handle_admin_callback,
    handle_admin_command,
    handle_reset_command,
)
from application.common import GRUPO_NAO_CADASTRADO
from assistant_util.error_handler import tratar_error
from config import MONGO_URI, REDIRECT_URI, STRAVA_CLIENT_ID, TELEGRAM_TOKEN

logger = logging.getLogger(__name__)

# Mesmo alias dos models do assistant_model (e do Error do tratar_error).
mongoengine.connect(host=MONGO_URI, alias="assistant-db")
bot = telebot.TeleBot(TELEGRAM_TOKEN)

MSG_ERRO = "Não consegui processar o comando agora. Tente de novo em instantes."
MSG_SEM_PERMISSAO = "Só administradores do grupo podem usar este comando."
ADMIN_STATUS = ("creator", "administrator")


def _is_callback(update) -> bool:
    return hasattr(update, "data") and getattr(update, "message", None) is not None


def _chat_id(update) -> int:
    return update.message.chat.id if _is_callback(update) else update.chat.id


def _responder(chat_id: int, texto: str, **kwargs):
    bot.send_message(chat_id, texto, parse_mode="HTML", disable_web_page_preview=True, **kwargs)


def seguro(handler):
    """
    Captura a exceção do handler: registra no `tratar_error` e avisa o chat.

    Sem isso, uma exceção num handler parava o polling e derrubava o bot. Em
    callback, sempre responde o callback_query (senão o botão fica carregando).
    """
    @functools.wraps(handler)
    def wrapper(update):
        try:
            return handler(update)
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Erro no handler %s", handler.__name__)
            tratar_error(exc, "strava_bot", job_tag=handler.__name__)
            try:
                bot.send_message(_chat_id(update), MSG_ERRO)
            except Exception:  # pylint: disable=broad-except
                logger.exception("Falha ao avisar o chat sobre o erro")
        finally:
            if _is_callback(update):
                try:
                    bot.answer_callback_query(update.id)
                except Exception:  # pylint: disable=broad-except
                    logger.debug("Falha ao responder o callback", exc_info=True)
    return wrapper


def _is_admin(chat, user) -> bool:
    """Admin do grupo no Telegram (em chat privado, o próprio usuário)."""
    if chat.type == "private":
        return True
    return bot.get_chat_member(chat.id, user.id).status in ADMIN_STATUS


@bot.message_handler(commands=['admin'])
@seguro
def admin_command_handler(message):
    group_id = message.chat.id
    if not _is_admin(message.chat, message.from_user):
        return _responder(group_id, MSG_SEM_PERMISSAO)

    member_list = handle_admin_command(group_id)
    if member_list is None:
        return _responder(group_id, GRUPO_NAO_CADASTRADO)
    if not member_list:
        return _responder(group_id, "Nenhum membro cadastrado.")

    markup_dict = {nome: {'callback_data': f'admin_{athlete_id}'} for nome, athlete_id in member_list}
    markup = quick_markup(markup_dict, row_width=2)
    return bot.send_message(group_id, "Selecione um membro pra remover:", reply_markup=markup)


@bot.message_handler(commands=['frequency'])
@seguro
def frequency_command_handler(message):
    _responder(message.chat.id, handle_month_frequency_command(message.chat.id))


@bot.message_handler(commands=['yfrequency'])
@seguro
def year_frequency_command_handler(message):
    _responder(message.chat.id, handle_year_frequency_command(message.chat.id))


@bot.message_handler(commands=['medalhas'])
@seguro
def medal_command_handler(message):
    _responder(message.chat.id, handle_medal_command(message.chat.id))


@bot.message_handler(commands=['rank', 'yrank'])
@seguro
def rank_command_handler(message):
    group_id = message.chat.id
    # extract_command tira o "@nome_do_bot" que o Telegram acrescenta em grupo.
    prefixo = "yrank" if extract_command(message.text) == "yrank" else "rank"
    texto, esportes = handle_rank_menu(group_id, anual=prefixo == "yrank")
    if not esportes:
        return _responder(group_id, texto)

    markup = quick_markup({x: {'callback_data': f'{prefixo}_{x}'} for x in esportes}, row_width=1)
    return bot.send_message(group_id, texto, reply_markup=markup)


@bot.message_handler(commands=['streak'])
@seguro
def streak_command_handler(message):
    _responder(message.chat.id, handle_streak_command(message.chat.id))


@bot.message_handler(commands=['link'])
@seguro
def link_command_handler(message):
    group_id = message.chat.id
    redirect_uri = REDIRECT_URI.format(group_id)
    bot.send_message(
        group_id,
        f"https://www.strava.com/oauth/authorize?client_id={STRAVA_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}&response_type=code&scope=activity:read",
    )


@bot.message_handler(commands=['reset'])
@seguro
def reset_command_handler(message):
    group_id = message.chat.id
    if not _is_admin(message.chat, message.from_user):
        return _responder(group_id, MSG_SEM_PERMISSAO)
    return _responder(group_id, handle_reset_command(group_id))


@bot.callback_query_handler(func=lambda call: call.data.startswith('rank_'))
@seguro
def rank_month_callback_handler(call):
    group_id = call.message.chat.id
    sport_type = call.data.split('_', 1)[1]
    _responder(group_id, handle_rank_month_command(group_id, sport_type))


@bot.callback_query_handler(func=lambda call: call.data.startswith('yrank_'))
@seguro
def rank_year_callback_handler(call):
    group_id = call.message.chat.id
    sport_type = call.data.split('_', 1)[1]
    _responder(group_id, handle_rank_year_command(group_id, sport_type))


@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
@seguro
def admin_callback_handler(call):
    chat = call.message.chat
    if not _is_admin(chat, call.from_user):
        return _responder(chat.id, MSG_SEM_PERMISSAO)

    member_id = int(call.data.split('_', 1)[1])
    user_name_admin = call.from_user.first_name or call.from_user.username
    return _responder(chat.id, handle_admin_callback(chat.id, member_id, user_name_admin))


def start_bot():
    # infinity_polling reconecta sozinho em erro de rede/API; bot.polling()
    # parava na primeira exceção.
    bot.infinity_polling(timeout=20, long_polling_timeout=20)
