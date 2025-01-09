import functools
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telebot.apihelper import ApiTelegramException



def handler_parse_error(exc, telegram_bot, message, texto_result, disable_web_page_preview):
    """
    Error 
    """
    if "parse entities" in exc.description:
        return telegram_bot.reply_to(message, texto_result, disable_web_page_preview=disable_web_page_preview)
def send_reply_return(message_return, message, telegram_bot, save_log=True, disable_web_page_preview=False, reply_markup=None) -> None:
    """
    Retorna resultado da mensagem
    Args:
        message_return (any): Resultado da mensagem
        message (Message): Mensagem recebida
        telegram_bot (telebot.TeleBot): Bot do telegram
        save_log (bool, optional): Salvar log. Defaults to True.
    """
    if not message_return:
        return

    try:
        if isinstance(message_return, list):
            return [
                send_reply_return(
                    item, message, telegram_bot, save_log, disable_web_page_preview
                )
                for item in message_return
            ]

        if isinstance(message_return, str):
            if len(message_return) > 4000:
                return [
                    send_reply_return(
                        message_return[i:i + 4000],
                        message,
                        telegram_bot,
                        save_log,
                        disable_web_page_preview,
                        reply_markup,
                    )
                    for i in range(0, len(message_return), 4000)
                ]
            return telegram_bot.send_message(
                message.chat.id,
                message_return,
                reply_markup=reply_markup,
                parse_mode="HTML",
                disable_web_page_preview=disable_web_page_preview,
            )

        if isinstance(message_return, dict):
            texto_result = message_return.get("texto", "")
            reply_markup = message_return.get("markup", reply_markup)
            message_id = message.chat.id

            if "photo" in message_return:
                return telegram_bot.send_photo(
                    message_id,
                    message_return.get("photo", ""),
                    caption=texto_result,
                    reply_markup=reply_markup,
                )

            if "video" in message_return:
                return telegram_bot.send_video(
                    message_id, message_return.get("video", "")
                )

            if "function" in message_return:
                function = message_return.get("function", "")
                function_data = message_return.get("function_data")
                if function_data:
                    telegram_bot.register_next_step_handler(
                        message, lambda m: function(m, function_data)
                    )
                else:
                    telegram_bot.register_next_step_handler(message, function)
                return send_reply_return(
                    texto_result,
                    message,
                    telegram_bot,
                    save_log,
                    disable_web_page_preview,
                    reply_markup=reply_markup,
                )

            if texto_result:
                return send_reply_return(
                    texto_result,
                    message,
                    telegram_bot,
                    save_log,
                    disable_web_page_preview,
                    reply_markup=reply_markup,
                )

    except ApiTelegramException as exc:
        handler_parse_error(
            exc, telegram_bot, message, message_return, disable_web_page_preview
        )

def get_markup(
    array: list = None,
    prefix: str = None,
    delete_option: bool = False,
    delete_data: str = None,
    edit_option=False,
    edit_data=None,
    more_option=None,
    row_width=1,
) -> InlineKeyboardMarkup:
    """
    Retorna markup
    Args:
        array (list): Array
        prefix (str): Prefixo
        delete_option (bool): Excluir opção
        delete_data (str): Dados de exclusão
        edit_option (bool): Editar opção
        edit_data (str): Dados de edição
        more_option (str): Mais opção
        row_width (int): Largura da linha
    """
    array = array or {}
    obj = []

    array = array.items() if isinstance(array, dict) else array

    for item_index in array:
        data_key, data_value = item_index if isinstance(item_index, tuple) else (item_index, item_index)
        call_back = (prefix + data_value if prefix else data_value).replace("ç", "c")
        obj.append({"nome": data_key, "callback": call_back})

    markup = InlineKeyboardMarkup(row_width=row_width)
    rows = [obj[i:i + row_width] for i in range(0, len(obj), row_width)]

    for row in rows:
        if delete_option or edit_option:
            markup.row_width = 2 + int(delete_option) + int(edit_option)
            elements = [InlineKeyboardButton(item["nome"], callback_data=item["callback"]) for item in row]

            if edit_option:
                elements.append(InlineKeyboardButton("✏️", callback_data=f"edit_{edit_data}_{row[0]['nome']}"))

            if delete_option:
                elements.append(InlineKeyboardButton("❌", callback_data=f"del_{delete_data}_{row[0]['callback']}"))

            markup.add(*elements)
        else:
            markup.add(*[InlineKeyboardButton(item["nome"], callback_data=item["callback"]) for item in row])

    if more_option:
        for item in more_option:
            markup.add(InlineKeyboardButton(item[0], callback_data=item[1]))

    return markup

def TelegramCommand(command: str):
    """
    Decorator para comandos do telegram
    """
    def decorator(func):
        if not hasattr(func, 'telegram_command'):
            func.telegram_command = [command]
        else:
            func.telegram_command.append(command)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

def TelegramCallback(command: str):
    """
    Decorator para callbacks do telegram
    """
    def decorator(func):
        if not hasattr(func,'telegram_callback_command'):
            func.telegram_callback_command = [command]
        else:
            func.telegram_callback_command.append(command)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator
