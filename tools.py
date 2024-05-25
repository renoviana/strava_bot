from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
)

from secure import (
    BSB_PEDAL_BOT_TOKEN,
)

def return_has_result(result: dict, message: Message, telegram_bot) -> None:
    """
    Retorna resultado da mensagem
    Args:
        result (dict): Resultado da mensagem
        message (Message): Mensagem recebida
        telegram_bot (telebot.TeleBot): Bot do telegram
    """
    if not result:
        return None

    is_pedal_bot = telegram_bot.token == BSB_PEDAL_BOT_TOKEN
    if isinstance(result, dict):
        texto_result = result.get("texto", "")
        message_id = message.chat.id
        has_markup = "markup" in result

        if "photo" in result:
            photo = result.get("photo", "")
            caption = texto_result if "texto" in result else None

            if has_markup:
                return telegram_bot.send_photo(
                    message_id,
                    photo,
                    caption=caption,
                    reply_markup=result.get("markup", ""),
                )

            return telegram_bot.send_photo(
                message_id,
                photo,
                caption=caption,
            )

        if "video" in result:
            return telegram_bot.send_video(message_id, result.get("video", ""))

        if "function" in result:
            function_data = result.get("function_data")

            if function_data:
                telegram_bot.register_next_step_handler(
                    message,
                    lambda m: result.get("function", "")(m, function_data),
                )
            else:
                telegram_bot.register_next_step_handler(
                    message, result.get("function", "")
                )

            return telegram_bot.reply_to(message, texto_result, parse_mode="HTML", disable_web_page_preview=is_pedal_bot)

        if has_markup:
            markup_data = result.get("markup", "")
            return telegram_bot.reply_to(
                message, texto_result, reply_markup=markup_data, parse_mode="HTML", disable_web_page_preview=is_pedal_bot
            )

        if "texto" in result:
            return telegram_bot.reply_to(message, texto_result, parse_mode = 'HTML', disable_web_page_preview=is_pedal_bot)

    if isinstance(result, list):
        for item in result:
            return_has_result(item, message, telegram_bot)
        return
    
    array_result = [result]

    if len(result) > 4000:
        array_result = [result[i : i + 4000] for i in range(0, len(result), 4000)]

    reply_id_list = []
    for item in array_result:
        reply_id_list.append(telegram_bot.reply_to(message, item, parse_mode = "HTML", disable_web_page_preview=is_pedal_bot))
    
    return reply_id_list[0] if len(reply_id_list) == 1 else reply_id_list








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

    if len(item) == 1:
        item = item[0]

    if delete_option and edit_option:
        markup.row_width = 3
        markup.add(
            add_text_option_markup(item["nome"], callback_data=item["callback"]),
            add_edit_option_markup(edit_data, item["nome"]),
            add_del_option_markup(delete_data, item["callback"] or item["nome"]),
        )
        return markup

    if delete_option:
        markup.row_width = 2
        markup.add(
            add_text_option_markup(item["nome"], callback_data=item["callback"]),
            add_del_option_markup(delete_data, item["callback"] or item["nome"]),
        )
        return markup

    if edit_option:
        markup.row_width = 2
        markup.add(
            add_text_option_markup(item["nome"], callback_data=item["callback"]),
            add_edit_option_markup(edit_data, item["nome"]),
        )
        return markup

    return None


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


def start_bot(bot_run, tipo: str) -> None:
    """
    Inicia bot
    Args:
        bot_run (Bot): Bot
        tipo (str): Tipo de bot
    """
    while True:
        try:
            bot_run.polling(none_stop=True)
        except Exception as exc:
            bot_run.stop_polling()
