import inspect
from abc import abstractmethod
import queue
import threading
import time
import requests
import telebot


class TelegramBot:
    """
    Classe para criar um bot do telegram
    """

    callback_dict = {}
    command_dict = {}

    def __init__(self, bot_token, command_class, use_queue=True, health_check_url=None):
        self.bot = telebot.TeleBot(bot_token)
        self.use_queue = use_queue
        self.create_queue()
        self.start_handler()
        self.get_methods_and_decorators(command_class)
        self.health_check_url = health_check_url

    def create_queue(self):
        """
        Cria as filas de comandos
        """
        if not self.use_queue:
            return

        queue_dict = {
            "callback_queue": self.callback_query,
            "command_queue": self.commands_handler,
            "group_command_queue": self.group_commands_handler,
        }

        for queue_name, queue_function in queue_dict.items():
            setattr(self, queue_name, queue.Queue())
            consumer_thread = threading.Thread(
                target=self.queue_consumer,
                args=(getattr(self, queue_name), queue_function),
            )
            consumer_thread.daemon = True
            consumer_thread.start()

    def queue_consumer(self, fila, function):
        """
        Função para consumir as filas
        Args:
            fila (Queue): Fila de comandos
            function (function): Função a ser executada
        """
        while True:
            mensagem = fila.get()
            function(mensagem)
            fila.task_done()

    def is_group_message(self, message):
        """
        Verifica se é mensagem de grupo
        Args:
            message (Message): Mensagem recebida
        """
        return hasattr(message, "chat") and message.chat.type in ["group", "supergroup"]

    def start_handler(self):
        """
        Inicia os handlers do bot
        """
        self.bot.message_handler(func=lambda x: x.json.get("new_chat_member"))(
            self.new_chat_member
        )

        if self.use_queue:
            self.bot.callback_query_handler(func=lambda _: True)(
                lambda call: self.process_queue(call, getattr(self, "callback_queue"))
            )
            self.bot.message_handler(func=lambda x: not self.is_group_message(x))(
                lambda message: self.process_queue(
                    message, getattr(self, "command_queue")
                )
            )
            self.bot.message_handler(func=self.is_group_message)(
                lambda message: self.process_queue(
                    message, getattr(self, "group_command_queue")
                )
            )
            return

        self.bot.callback_query_handler(func=lambda _: True)(self.callback_query)
        self.bot.message_handler(func=self.is_group_message)(
            self.group_commands_handler
        )
        self.bot.message_handler(func=lambda x: not self.is_group_message(x))(
            self.commands_handler
        )

    def process_queue(self, call, command_queue) -> None:
        """
        Handler para responder os callbacks:
        Quando um usuário clica em algum botão no bot
        Args:
            call (CallbackQuery): Objeto de callback do bot
            current (str): Comando atual
            command_queue (Queue): Fila de comandos
            function (function): Função a ser executada
        """
        try:
            command_queue.put(call)
        except Exception:
            pass

    def get_methods_and_decorators(self, command_class):
        """
        Função para pegar os métodos e decoradores de uma classe
        Args:
            command_class (class): Classe de comandos
        """
        for name, member in inspect.getmembers(command_class):
            if inspect.isfunction(member) or inspect.ismethod(member):
                if hasattr(member, "telegram_callback_command"):
                    command_param = getattr(member, "telegram_callback_command")
                    for command in command_param:
                        self.callback_dict[command] = name

                if hasattr(member, "telegram_command"):
                    command_param = getattr(member, "telegram_command")
                    for command in command_param:
                        self.command_dict[command] = name

    @abstractmethod
    def commands_handler(self, message):
        """
        Handler para escutar comandos
        """

    @abstractmethod
    def callback_query(self, call):
        """
        Handler para escutar os callbacks
        """

    @abstractmethod
    def group_commands_handler(self, message):
        """
        Handler para escutar comandos de grupo
        """

    @abstractmethod
    def new_chat_member(self, message):
        """
        Handler para novos usuários
        """

    def health_check(self):
        """
        Função para realizar o health check do bot
        """
        while True:
            requests.get(self.health_check_url, timeout=40)
            time.sleep(300)

    def run(self):
        """
        Função para rodar o bot
        """
        if self.health_check_url:
            health_check_thread = threading.Thread(target=self.health_check)
            health_check_thread.daemon = True
            health_check_thread.start()


        while True:
            try:
                self.bot.polling(none_stop=True)
            except Exception:
                self.bot.stop_polling()
