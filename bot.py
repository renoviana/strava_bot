from abc import abstractmethod
import time
import inspect
import queue
import threading
import requests
import telebot
from mongoengine import connect
from db import DbManager
from command import StravaCommands
from engine import StravaDataEngine
from service import StravaApiProvider
from telegram_bot import TelegramBot
from tools import send_reply_return
from secure import TELEGRAM_BOT_TOKEN, MONGO_URI, TELEGRAM_BOT_ID, HEALTH_CHECK_URL


connect(host=MONGO_URI)

class StravaBot(TelegramBot):
    strava_dict = {}

    def __init__(self, telegram_bot_token):
        super().__init__(telegram_bot_token, StravaCommands, use_queue=True, health_check_url=HEALTH_CHECK_URL)

    def get_strava_command_group(self, group_id) -> StravaCommands:
        """
        Função para retornar a instância de StravaCommands
        Args:
            group_id (int): Id do grupo
        """
        if group_id not in self.strava_dict:
            self.strava_dict[group_id] = StravaCommands(StravaDataEngine(group_id, StravaApiProvider, DbManager))
        return self.strava_dict[group_id]
 
    def new_chat_member(self, message):
        """
        Handler para novos usuários e também a entrada do bot no grupo
        """
        strava_command_group = self.get_strava_command_group(message.chat.id)
        new_user = message.json.get("new_chat_member")
        link = strava_command_group.link_command(message)

        if new_user.get('id') == TELEGRAM_BOT_ID:
            self.bot.reply_to(
                message,
                "Strava Bot configurado com sucesso!\nAcesse o menu para ver os comandos disponiveis."
            )
            self.bot.reply_to(
                message,
                f"Para começar a usar, autorize seu strava nesse link"\
                f"\n{link}"
            )
            DbManager(message.chat.id).add_strava_group()
            return "Grupo adicionado com sucesso!"

        if new_user.get("is_bot"):
            return

        self.bot.reply_to(message, f"Bem vindo ao grupo {new_user.get('first_name')}!\n\n Autorize seu strava nesse link para participar \n{link}")

    def callback_query(self, call):
        """
        Executa o callback do bot
        Args:
            call (CallbackQuery): Objeto de callback do bot
        """
        try:
            strava_command_group = self.get_strava_command_group(call.message.chat.id)
            command_list = list(
                filter(lambda command: command[0] in call.data, self.callback_dict.items())
            )

            if not self.callback_dict:
                return

            _, command_function_name = command_list[0]
            resultado = getattr(strava_command_group, command_function_name)(call)
            send_reply_return(resultado, call.message, self.bot, disable_web_page_preview=True)
            try:
                self.bot.answer_callback_query(call.id)
            except Exception as exc:
                pass
        except Exception as exc:
            if exc.args:
                send_reply_return(
                    exc.args[0], call.message, self.bot, disable_web_page_preview=True
                )
                return

            send_reply_return(
                "Erro ao executar o comando, tente novamente.", call.message, self.bot, disable_web_page_preview=True
            )

    def group_commands_handler(self, message) -> None:
        """
        Handler para escutar comandos de grupo
        """
        try:
            strava_command_group = self.get_strava_command_group(message.chat.id)
            command = message.text[1:].split(" ")[0].replace("@bsbpedalbot", "")
            bot_member = self.bot.get_chat_member(message.chat.id, self.bot.get_me().id)
            is_bot_admin = bot_member.status in ["administrator", "creator"]

            if command not in self.command_dict:
                return

            result = getattr(strava_command_group, self.command_dict[command])(message)
            data = send_reply_return(result, message, self.bot, disable_web_page_preview=True)
        except Exception as exc:
            if exc.args:
                send_reply_return(
                    exc.args[0], message, self.bot, disable_web_page_preview=True
                )
                return

            send_reply_return(
                "Erro ao executar o comando, tente novamente.", message, self.bot, disable_web_page_preview=True
            )
            return

        if is_bot_admin and data:
            self.bot.pin_chat_message(message.chat.id, data.message_id)

    def commands_handler(self, message) -> None:
        """
        Handler que escuta todos os comandos cadastrados na lista
        """
        return self.bot.reply_to(
            message,
            "Bem vindo ao Strava Bot!"\
            "\nEsse bot foi desenvolvido para funcionar apenas em grupos do telegram"\
            ", para utiliza-lo crie um grupo e me adicione. :)")


if __name__ == "__main__":
    StravaBot(TELEGRAM_BOT_TOKEN).run()