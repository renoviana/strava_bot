import inspect
from abc import abstractmethod
import queue
import threading
import time
import requests
import telebot


class TelegramBot:
    callback_dict = {}
    command_dict = {}
    callback_queue = queue.Queue()
    current_callback = None
    command_queue = queue.Queue()
    current_command = None
    group_command_queue = queue.Queue()
    current_group_command = None

    def __init__(self, bot_token, command_class, use_queue=False, health_check_url=None):
        self.bot = telebot.TeleBot(bot_token)
        self.use_queue = use_queue
        self.start_handler()
        self.get_methods_and_decorators(command_class)
        self.health_check_url = health_check_url

    def is_group_message(self, message):
        """
        Verifica se é mensagem de grupo
        Args:
            message (Message): Mensagem recebida
        """
        return hasattr(message,'chat') and message.chat.type in ["group", "supergroup"]

    def start_handler(self):
        """
        Inicia os handlers do bot
        """
        self.bot.message_handler(func=lambda x: x.json.get("new_chat_member"))(self.new_chat_member)
        if self.use_queue:
            self.bot.callback_query_handler(func=lambda _: True)(lambda call: self.process_queue(call, self.current_callback, self.callback_queue, self.callback_query))
            self.bot.message_handler(func=lambda x: not self.is_group_message(x))(lambda message: self.process_queue(message, self.current_command, self.command_queue, self.commands_handler))
            self.bot.message_handler(func=self.is_group_message)(lambda message: self.process_queue(message, self.current_group_command, self.group_command_queue, self.group_commands_handler))
        else:
            self.bot.callback_query_handler(func=lambda _: True)(self.callback_query)
            self.bot.message_handler(func=self.is_group_message)(self.group_commands_handler)
            self.bot.message_handler(func=lambda x: not self.is_group_message(x))(self.commands_handler)

    def process_queue(self, call, current, command_queue, function) -> None:
        """
        Handler para responder os callbacks:
        Quando um usuário clica em algum botão no bot
        Args:
            call (CallbackQuery): Objeto de callback do bot
            current (str): Comando atual
            command_queue (Queue): Fila de comandos
            function (function): Função a ser executada
        """
        if current:
            return command_queue.put(call)

        current = call
        try:
            function(call)
            while not command_queue.empty():
                call = command_queue.get()
                function(call)
                command_queue.task_done()
        except:
            pass

        current = None

    def get_methods_and_decorators(self, command_class):
        """
        Função para pegar os métodos e decoradores de uma classe
        Args:
            command_class (class): Classe de comandos
        """
        for name, member in inspect.getmembers(command_class):
            if inspect.isfunction(member) or inspect.ismethod(member):
                if hasattr(member, 'telegram_callback_command'):
                    command_param = getattr(member, 'telegram_callback_command')
                    self.callback_dict[command_param] = name

                if hasattr(member, 'telegram_command'):
                    command_param = getattr(member, 'telegram_command')
                    self.command_dict[command_param] = name

    @abstractmethod
    def commands_handler(self):
        """
        Handler para escutar comandos
        """

    @abstractmethod
    def callback_query(self):
        """
        Handler para escutar os callbacks
        """

    @abstractmethod
    def group_commands_handler(self):
        """
        Handler para escutar comandos de grupo
        """

    @abstractmethod
    def new_chat_member(self):
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
            except Exception as exc:
                self.bot.stop_polling()
