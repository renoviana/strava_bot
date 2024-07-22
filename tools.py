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
        return None
    try:
        if isinstance(message_return, list):
            return list(map(lambda item: send_reply_return(item, message, telegram_bot, save_log, disable_web_page_preview), message_return))

        if isinstance(message_return, str):
            if len(message_return) > 4000:
                return list(map(lambda i: send_reply_return(message_return[i : i + 4000], message, telegram_bot, save_log, disable_web_page_preview), range(0, len(message_return), 4000)))
            return telegram_bot.reply_to(message, message_return, reply_markup=reply_markup, parse_mode = "HTML", disable_web_page_preview=disable_web_page_preview)

        if isinstance(message_return, dict):
            texto_result = message_return.get("texto", "")
            reply_markup = message_return.get("markup", None)
            message_id = message.chat.id

            if "photo" in message_return:
                    return telegram_bot.send_photo(
                        message_id,
                        message_return.get("photo", ""),
                        caption=texto_result,
                        reply_markup=reply_markup
                    )

            if "video" in message_return:
                return telegram_bot.send_video(message_id, message_return.get("video", ""))

            if "function" in message_return:
                if message_return.get("function_data"):
                    telegram_bot.register_next_step_handler(
                        message,
                        lambda m: message_return.get("function", "")(m, message_return.get("function_data")),
                    )
                else:
                    telegram_bot.register_next_step_handler(
                        message, message_return.get("function", "")
                    )
                return send_reply_return(texto_result, message, telegram_bot, save_log, disable_web_page_preview, reply_markup=reply_markup)

            if "texto" in message_return:
                return send_reply_return(texto_result, message, telegram_bot, save_log, disable_web_page_preview, reply_markup=reply_markup)
    except ApiTelegramException as exc:
        handler_parse_error(exc, telegram_bot, message, message_return, disable_web_page_preview)

def add_edit_option_markup(query, name):
    """
    Adiciona botão de edição
    Args:
        query (str): Query
        name (str): Nome
    """
    return InlineKeyboardButton("✏️", callback_data=f"edit_{query}_{name}")


def add_del_option_markup(query, name):
    """
    Adiciona botão de exclusão
    Args:
        query (str): Query
        name (str): Nome
    """
    return InlineKeyboardButton("❌", callback_data=f"del_{query}_{name}")


def add_text_option_markup(text, callback_data):
    """
    Adiciona botão de texto
    Args:
        text (str): Texto
        callback_data (str): Callback data
    """
    return InlineKeyboardButton(text, callback_data=callback_data)


def add_opts_markup(delete_option, delete_data, addopts, markup):
    """
    Adiciona opções de adição e exclusão
    Args:
        delete_option (bool): Excluir opção
        delete_data (str): Dados de exclusão
        addopts (bool): Adicionar opção
        markup (InlineKeyboardMarkup): Markup
    """
    if addopts:
        markup.add(
            add_text_option_markup("Adicionar", callback_data=f"add_{delete_data}"),
        )

        if not delete_option:
            markup.add(
                add_text_option_markup("Excluir", callback_data=f"del_{delete_data}"),
            )
    return markup


def add_more_options_markup(prefix, more_option, markup):
    """
    Adiciona opções de mais
    Args:
        prefix (str): Prefixo
        more_option (str): Mais opção
        markup (InlineKeyboardMarkup): Markup
    """

    if more_option:
        obj = format_markup(more_option, prefix)
        for item in obj:
            markup.add(
                add_text_option_markup(item["nome"], callback_data=item["callback"]),
            )
    return markup


def format_markup(array: list, prefix: str) -> list:
    """
    Formata markup
    Args:
        array (list): Array
        prefix (str): Prefixo
    """
    array_data = []

    if isinstance(array, dict):
        array = array.items()

    for item_index in array:
        data_key = data_value = item_index

        if isinstance(item_index, tuple):
            data_key, data_value = item_index

        call_back = data_value

        if prefix:
            call_back = prefix + data_value

        array_data.append({"nome": data_key, "callback": call_back.replace("ç", "c")})
    return array_data


def split_array(arr, x):
    """
    Divide array
    Args:
        arr (list): Array
        x (int): Quantidade de itens
    """
    result = []
    for i in range(0, len(arr), x):
        result.append(arr[i : i + x])
    return result


def get_markup_edit_delete(
    delete_option, delete_data, edit_option, edit_data, item, markup
):
    """
    Retorna markup de edição e exclusão
    Args:
        delete_option (bool): Excluir opção
        delete_data (str): Dados de exclusão
        edit_option (bool): Editar opção
        edit_data (str): Dados de edição
        item (list): Item
        markup (InlineKeyboardMarkup): Markup
    """
    markup.row_width = 2
    if len(item) == 1:
        item = item[0]

    if delete_option and edit_option:
        markup.row_width = 3

    elements = [add_text_option_markup(item["nome"], callback_data=item["callback"])]

    if edit_option:
        elements.append(add_edit_option_markup(edit_data, item["nome"]))

    if delete_option:
        elements.append(add_del_option_markup(delete_data, item["callback"] or item["nome"]))

    markup.add(*elements)
    return markup if elements else None

def get_markup(
    array: list = None,
    prefix: str = None,
    delete_option: bool = False,
    delete_data: str = None,
    addopts: bool = False,
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
        addopts (bool): Adicionar opção
        edit_option (bool): Editar opção
        edit_data (str): Dados de edição
        more_option (str): Mais opção
        row_width (int): Largura da linha
    """
    if not array:
        array = {}
    obj = format_markup(array, prefix)
    markup = InlineKeyboardMarkup()
    markup.row_width = row_width

    obj = split_array(obj, row_width)
    for item in obj:
        if delete_option or edit_option:
            markup = get_markup_edit_delete(
                delete_option, delete_data, edit_option, edit_data, item, markup
            )
            continue

        markup_list = list(
            map(
                lambda button: add_text_option_markup(
                    button["nome"], callback_data=button["callback"]
                ),
                item,
            )
        )
        markup.add(*markup_list)

    markup = add_opts_markup(delete_option, delete_data, addopts, markup)
    markup = add_more_options_markup(prefix, more_option, markup)
    return markup


def is_group_message(message):
    """
    Verifica se é mensagem de grupo
    Args:
        message (Message): Mensagem recebida
    """
    return hasattr(message,'chat') and message.chat.type in ["group", "supergroup"]


